from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

from .database import connection, meta_get, meta_set, transaction
from .models import AnalysisResult, NotificationItem, Post


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relative_from_iso(value: str) -> str:
    try:
        created = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        seconds = max(0, int((datetime.now(timezone.utc) - created.astimezone(timezone.utc)).total_seconds()))
    except Exception:
        return 'Şimdi'
    if seconds < 60:
        return 'Şimdi'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes} dk'
    hours = minutes // 60
    if hours < 24:
        return f'{hours} sa'
    days = hours // 24
    if days < 7:
        return f'{days} gün'
    return f'{days // 7} hf'


def _normalize(value: str) -> str:
    return re.sub(r'\s+', ' ', (value or '').strip().casefold())


def _legacy_sig(kind: str, post_id: int | None, tab_index: int | None, title: str) -> str:
    return f'{kind}|{post_id}|{tab_index}|{title}'


def _event_sig(kind: str, post_id: int | None, tab_index: int | None, event_key: str) -> str:
    """v1.1.2 stable event identity.

    UI wording may change between versions. Notification identity therefore uses the
    semantic event payload instead of the visible title. A deleted event also stays
    suppressed because signature_key remains UNIQUE for soft-deleted rows.
    """
    payload = _normalize(event_key)
    digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]
    return f'v112|{kind}|{post_id}|{tab_index}|{digest}'


def _dedupe_legacy_v112() -> None:
    """One-time cleanup for automatic analysis notifications created before v1.1.2.

    Older releases emitted one generic notification per analysis family. If wording or
    storage generations changed, equivalent active rows could accumulate. Before the
    new event-level system takes over, keep only the newest active row for each
    (kind, post, destination) family. User-deleted rows are left untouched so undo and
    suppression semantics remain intact.
    """
    with transaction(immediate=True) as conn:
        if meta_get(conn, 'notifications_dedup_v112') == '1':
            return
        automatic_kinds = (
            'analysis_ready', 'viewpoint_change', 'claim_alert',
            'source_request', 'bridge_update', 'common_ground_update',
        )
        placeholders = ','.join('?' for _ in automatic_kinds)
        rows = conn.execute(
            f'''SELECT id, kind, post_id, tab_index, is_read
                FROM notifications
                WHERE deleted = 0 AND kind IN ({placeholders})
                ORDER BY id DESC''',
            automatic_kinds,
        ).fetchall()
        keep_by_family: dict[tuple, int] = {}
        read_seen: dict[tuple, bool] = {}
        duplicate_ids: list[int] = []
        for row in rows:
            family = (row['kind'], row['post_id'], row['tab_index'])
            read_seen[family] = read_seen.get(family, False) or bool(row['is_read'])
            if family in keep_by_family:
                duplicate_ids.append(int(row['id']))
            else:
                keep_by_family[family] = int(row['id'])
        # If the user had already read any equivalent legacy copy, the surviving row
        # remains read; cleanup must not turn an already-seen event back into unread.
        for family, keep_id in keep_by_family.items():
            if read_seen.get(family):
                conn.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (keep_id,))
        if duplicate_ids:
            marks = ','.join('?' for _ in duplicate_ids)
            conn.execute(
                f'UPDATE notifications SET deleted = 1, deleted_at = ? WHERE id IN ({marks})',
                (_now_iso(), *duplicate_ids),
            )
        meta_set(conn, 'notifications_dedup_v112', '1')


def _seed() -> None:
    with transaction(immediate=True) as conn:
        if meta_get(conn, 'notifications_seeded') != '1':
            now = datetime.now(timezone.utc)
            rows = [
                ('viewpoint_change', 'Görüş haritasında yeni ayrım', 'Üniversitelerde yapay zekâ tartışmasında farklı görüş kümeleri görünür durumda.', 1, 2, 'Görüş', 'normal', 3),
                ('source_request', 'Kaynak bekleyen soru var', 'Tartışmada doğrulanabilir bir iddia için kaynak veya araştırma talebi öne çıktı.', 1, 4, 'Kaynak', 'high', 8),
                ('bridge_update', 'Köprü sorusu hazır', 'Ortak zemin ve asıl ayrışma üzerinden tartışmayı ilerletecek Köprü sorusu oluşturuldu.', 1, 7, 'Köprü', 'normal', 14),
            ]
            for kind, title, text, post_id, tab_index, badge, priority, age in rows:
                conn.execute(
                    '''INSERT OR IGNORE INTO notifications(kind, title, text, created_at, is_read, post_id, tab_index, badge, priority, signature_key, deleted)
                       VALUES(?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 0)''',
                    (kind, title, text, (now - timedelta(minutes=age)).isoformat(), post_id, tab_index, badge, priority, _legacy_sig(kind, post_id, tab_index, title)),
                )
            meta_set(conn, 'notifications_seeded', '1')
    _dedupe_legacy_v112()


def _from_row(row) -> NotificationItem:
    return NotificationItem(
        id=int(row['id']), kind=row['kind'], title=row['title'], text=row['text'],
        created_at=row['created_at'], relative_time=_relative_from_iso(row['created_at']),
        is_read=bool(row['is_read']), post_id=row['post_id'], tab_index=row['tab_index'],
        badge=row['badge'], priority=row['priority'],
    )


def notification_counts() -> tuple[int, int, int]:
    _seed()
    with connection() as conn:
        row = conn.execute(
            '''SELECT COUNT(*) AS total,
                      SUM(CASE WHEN is_read = 1 THEN 1 ELSE 0 END) AS read_count,
                      SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) AS unread_count
               FROM notifications WHERE deleted = 0'''
        ).fetchone()
    return int(row['total'] or 0), int(row['read_count'] or 0), int(row['unread_count'] or 0)


def list_notifications(status: str = 'all') -> list[NotificationItem]:
    _seed()
    if status not in {'all', 'unread', 'read'}:
        raise ValueError('Geçersiz bildirim filtresi')
    where = 'deleted = 0'
    params: tuple = ()
    if status == 'unread':
        where += ' AND is_read = 0'
    elif status == 'read':
        where += ' AND is_read = 1'
    with connection() as conn:
        rows = conn.execute(f'SELECT * FROM notifications WHERE {where} ORDER BY created_at DESC, id DESC', params).fetchall()
    return [_from_row(row) for row in rows]


def unread_count() -> int:
    return notification_counts()[2]


def get_notification(notification_id: int) -> NotificationItem | None:
    _seed()
    with connection() as conn:
        row = conn.execute('SELECT * FROM notifications WHERE id = ? AND deleted = 0', (notification_id,)).fetchone()
    return _from_row(row) if row else None


def _set_read_state(notification_id: int, is_read: bool) -> NotificationItem | None:
    _seed()
    with transaction(immediate=True) as conn:
        row = conn.execute('SELECT * FROM notifications WHERE id = ? AND deleted = 0', (notification_id,)).fetchone()
        if not row:
            return None
        conn.execute('UPDATE notifications SET is_read = ? WHERE id = ?', (1 if is_read else 0, notification_id))
        updated = conn.execute('SELECT * FROM notifications WHERE id = ?', (notification_id,)).fetchone()
        return _from_row(updated)


def mark_read(notification_id: int) -> NotificationItem | None:
    return _set_read_state(notification_id, True)


def mark_unread(notification_id: int) -> NotificationItem | None:
    return _set_read_state(notification_id, False)


def mark_all_read() -> int:
    _seed()
    with transaction(immediate=True) as conn:
        row = conn.execute('SELECT COUNT(*) AS c FROM notifications WHERE deleted = 0 AND is_read = 0').fetchone()
        changed = int(row['c'])
        conn.execute('UPDATE notifications SET is_read = 1 WHERE deleted = 0 AND is_read = 0')
        return changed


def delete_notification(notification_id: int) -> NotificationItem | None:
    _seed()
    with transaction(immediate=True) as conn:
        row = conn.execute('SELECT * FROM notifications WHERE id = ? AND deleted = 0', (notification_id,)).fetchone()
        if not row:
            return None
        conn.execute('UPDATE notifications SET deleted = 1, deleted_at = ? WHERE id = ?', (_now_iso(), notification_id))
        return _from_row(row)


def delete_read_notifications() -> list[int]:
    _seed()
    with transaction(immediate=True) as conn:
        rows = conn.execute('SELECT id FROM notifications WHERE deleted = 0 AND is_read = 1 ORDER BY id').fetchall()
        ids = [int(row['id']) for row in rows]
        if ids:
            placeholders = ','.join('?' for _ in ids)
            conn.execute(f'UPDATE notifications SET deleted = 1, deleted_at = ? WHERE id IN ({placeholders})', (_now_iso(), *ids))
        return ids


def restore_notifications(notification_ids: list[int]) -> int:
    wanted = sorted({int(x) for x in notification_ids})
    if not wanted:
        return 0
    _seed()
    with transaction(immediate=True) as conn:
        placeholders = ','.join('?' for _ in wanted)
        row = conn.execute(
            f'SELECT COUNT(*) AS c FROM notifications WHERE deleted = 1 AND id IN ({placeholders})',
            tuple(wanted),
        ).fetchone()
        restored = int(row['c'])
        conn.execute(
            f'UPDATE notifications SET deleted = 0, deleted_at = NULL WHERE deleted = 1 AND id IN ({placeholders})',
            tuple(wanted),
        )
        return restored


def _add_event_once(*, kind: str, title: str, text: str, post_id: int, tab_index: int, badge: str, event_key: str, priority: str = 'normal') -> bool:
    _seed()
    signature = _event_sig(kind, post_id, tab_index, event_key)
    with transaction(immediate=True) as conn:
        cursor = conn.execute(
            '''INSERT OR IGNORE INTO notifications(kind, title, text, created_at, is_read, post_id, tab_index, badge, priority, signature_key, deleted)
               VALUES(?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 0)''',
            (kind, title, text, _now_iso(), post_id, tab_index, badge, priority, signature),
        )
        return cursor.rowcount > 0


def _previous_analysis(post_id: int, history_id: int | None) -> AnalysisResult | None:
    if history_id is None:
        return None
    with connection() as conn:
        row = conn.execute(
            '''SELECT analysis_json FROM analysis_history
               WHERE post_id = ? AND id < ? ORDER BY id DESC LIMIT 1''',
            (post_id, history_id),
        ).fetchone()
    if not row:
        return None
    try:
        return AnalysisResult.model_validate_json(row['analysis_json'])
    except Exception:
        return None


def _claim_identity(item) -> str:
    return f'{int(item.comment_id)}|{_normalize(item.text)}'


def _question_identity(item) -> str:
    # Metin kimliği v1.1.x snapshot'larıyla da karşılaştırılabilir. v1.2.0'da
    # tekrar sorular tek kartta toplandığı için yorum numarası olay kimliği değildir.
    return _normalize(item.text)


def _viewpoint_changes(previous: AnalysisResult, current: AnalysisResult) -> tuple[list[str], list[str]]:
    old = {v.name: int(v.percentage) for v in previous.viewpoints}
    new = {v.name: int(v.percentage) for v in current.viewpoints}
    added = sorted(name for name in new if name not in old)
    shifted: list[str] = []
    for name in sorted(new.keys() & old.keys()):
        delta = new[name] - old[name]
        if abs(delta) >= 5:
            shifted.append(f'{name}:{old[name]}->{new[name]}')
    return added, shifted


def record_analysis(post: Post, analysis: AnalysisResult, *, history_id: int | None = None) -> int:
    """Create notifications only for genuinely new analysis events.

    First snapshot: baseline actionable notifications are created once.
    Later snapshots: no measurable change => zero notifications. Only newly added
    claims/questions, meaningful viewpoint shifts, common-ground changes or a changed
    bridge question can create a notification. Event signatures are content-based so
    repeating the exact same event later still cannot duplicate it.
    """
    previous = _previous_analysis(post.id, history_id)
    created = 0

    if previous is None:
        viewpoint_count = len(analysis.viewpoints)
        claim_count = len(analysis.claims)
        open_questions = [
            item for item in analysis.unanswered_questions
            if item.answer_status in {'Cevapsız', 'Kısmen cevaplandı'}
        ]
        question_count = len(open_questions)
        created += int(_add_event_once(
            kind='analysis_ready', title=f'“{post.text[:42]}” analizi hazır',
            text=f'{analysis.indicators.get("comment_count", len(post.comments))} benzersiz yorumdan {viewpoint_count} görüş kümesi çıkarıldı.',
            post_id=post.id, tab_index=0, badge='Analiz',
            event_key='baseline-analysis',
        ))
        if viewpoint_count > 1:
            created += int(_add_event_once(
                kind='viewpoint_change', title='Görüş haritasında ayrışma görünür',
                text=f'{viewpoint_count} farklı görüş kümesi tespit edildi. Dağılımı ve örnek yorumları inceleyebilirsin.',
                post_id=post.id, tab_index=2, badge='Görüş',
                event_key='baseline-viewpoints|' + '|'.join(sorted(v.name for v in analysis.viewpoints)),
            ))
        if claim_count:
            created += int(_add_event_once(
                kind='claim_alert', title='Doğrulanabilir iddialar bulundu',
                text=f'İddia Radarı {claim_count} doğrulanabilir iddia adayı belirledi. Kaynak durumlarını kontrol et.',
                post_id=post.id, tab_index=3, badge='İddia', priority='high',
                event_key='baseline-claims|' + '|'.join(sorted(_claim_identity(x) for x in analysis.claims)),
            ))
        if question_count:
            created += int(_add_event_once(
                kind='source_request', title='Cevapsız kaynak soruları var',
                text=f'{question_count} soru tartışmada yanıt veya kaynak bekliyor.',
                post_id=post.id, tab_index=4, badge='Kaynak', priority='high',
                event_key='baseline-questions|' + '|'.join(sorted(_question_identity(x) for x in open_questions)),
            ))
        bridge_question = str(analysis.bridge.get('bridge_question', '')).strip()
        if bridge_question:
            created += int(_add_event_once(
                kind='bridge_update', title='Yeni Köprü sorusu hazır', text=bridge_question,
                post_id=post.id, tab_index=7, badge='Köprü',
                event_key='baseline-bridge|' + bridge_question,
            ))
        return created

    # If the history comparator already found no measurable delta, notification layer
    # must stay quiet even when the user explicitly reruns the same analysis.
    if analysis.changes_since_last_visit == ['Önceki analizden bu yana ölçülebilir bir değişiklik tespit edilmedi.']:
        return 0

    added_viewpoints, shifted_viewpoints = _viewpoint_changes(previous, analysis)
    if added_viewpoints or shifted_viewpoints:
        pieces: list[str] = []
        if added_viewpoints:
            pieces.append('Yeni görüş: ' + ', '.join(added_viewpoints[:3]))
        if shifted_viewpoints:
            pieces.append(f'{len(shifted_viewpoints)} görüş kümesinde anlamlı oran değişimi')
        event_key = 'viewpoints|' + '|'.join(added_viewpoints + shifted_viewpoints)
        created += int(_add_event_once(
            kind='viewpoint_change', title='Görüş haritasında yeni değişiklik',
            text='. '.join(pieces) + '.', post_id=post.id, tab_index=2, badge='Görüş',
            event_key=event_key,
        ))

    previous_claims = {_claim_identity(item) for item in previous.claims}
    added_claims = [item for item in analysis.claims if _claim_identity(item) not in previous_claims]
    if added_claims:
        high = sum(1 for item in added_claims if _normalize(item.priority) == 'yüksek')
        text = f'{len(added_claims)} yeni doğrulanabilir iddia adayı bulundu.'
        if high:
            text += f' Bunların {high} tanesi yüksek öncelikli.'
        created += int(_add_event_once(
            kind='claim_alert', title='Yeni doğrulanabilir iddia bulundu', text=text,
            post_id=post.id, tab_index=3, badge='İddia', priority='high' if high else 'normal',
            event_key='claims|' + '|'.join(sorted(_claim_identity(x) for x in added_claims)),
        ))

    previous_questions = {
        _question_identity(item) for item in previous.unanswered_questions
        if item.answer_status in {'Cevapsız', 'Kısmen cevaplandı'}
    }
    added_questions = [
        item for item in analysis.unanswered_questions
        if item.answer_status in {'Cevapsız', 'Kısmen cevaplandı'}
        and _question_identity(item) not in previous_questions
    ]
    if added_questions:
        created += int(_add_event_once(
            kind='source_request', title='Yeni cevapsız kaynak sorusu var',
            text=f'{len(added_questions)} yeni soru veya kaynak talebi yanıt bekliyor.',
            post_id=post.id, tab_index=4, badge='Kaynak', priority='high',
            event_key='questions|' + '|'.join(sorted(_question_identity(x) for x in added_questions)),
        ))

    previous_common = [_normalize(x) for x in previous.common_ground]
    current_common = [_normalize(x) for x in analysis.common_ground]
    if current_common != previous_common:
        created += int(_add_event_once(
            kind='common_ground_update', title='Ortak zeminde değişiklik var',
            text='Karşıt görüşlerin kesiştiği ortak zemin yeni analiz verilerine göre değişti.',
            post_id=post.id, tab_index=1, badge='Ortak Zemin',
            event_key='common-ground|' + '|'.join(current_common),
        ))

    old_bridge = str(previous.bridge.get('bridge_question', '')).strip()
    new_bridge = str(analysis.bridge.get('bridge_question', '')).strip()
    if new_bridge and _normalize(new_bridge) != _normalize(old_bridge):
        created += int(_add_event_once(
            kind='bridge_update', title='Köprü sorusu güncellendi', text=new_bridge,
            post_id=post.id, tab_index=7, badge='Köprü',
            event_key='bridge|' + new_bridge,
        ))

    return created


def reset_for_tests() -> None:
    with transaction(immediate=True) as conn:
        conn.execute('DELETE FROM notifications')
        conn.execute("DELETE FROM app_meta WHERE key IN ('notifications_seeded', 'notifications_dedup_v112')")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'notifications'")
    _seed()


_seed()
