from __future__ import annotations

import json
from datetime import datetime, timezone

from .database import connection, meta_get, meta_set, transaction
from .models import AnalysisHistoryDetail, AnalysisHistoryItem, AnalysisResult, Comment, Post


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relative_time(value: str) -> str:
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


def allocate_custom_post_id() -> int:
    with transaction(immediate=True) as conn:
        raw = meta_get(conn, 'next_custom_post_id')
        if raw is None:
            row = conn.execute('SELECT MAX(post_id) AS max_id FROM custom_posts').fetchone()
            next_id = max(9001, int(row['max_id'] or 9000) + 1)
        else:
            next_id = max(9001, int(raw))
        meta_set(conn, 'next_custom_post_id', str(next_id + 1))
        return next_id


def save_custom_post(post: Post) -> None:
    with connection() as conn:
        conn.execute(
            'INSERT INTO custom_posts(post_id, post_json, created_at) VALUES(?, ?, ?) '
            'ON CONFLICT(post_id) DO UPDATE SET post_json = excluded.post_json',
            (post.id, post.model_dump_json(), _now_iso()),
        )
        conn.commit()


def get_custom_post(post_id: int) -> Post | None:
    with connection() as conn:
        row = conn.execute('SELECT post_json FROM custom_posts WHERE post_id = ?', (post_id,)).fetchone()
    if not row:
        return None
    try:
        return Post.model_validate_json(row['post_json'])
    except Exception:
        return None


def append_post_comment(base_post: Post, text: str, author: str) -> tuple[Post, Comment]:
    """Bir gönderiye yorumu kayıp güncelleme olmadan kalıcı olarak ekler.

    Demo ve Keşfet gönderilerinin kaynak sabitleri değiştirilmez. İlk yerel yorumda
    gönderinin güncel kopyası ``custom_posts`` tablosuna yazılır; sonraki eklemeler
    aynı SQLite kaydı üzerinden devam eder. ``BEGIN IMMEDIATE`` eş zamanlı iki
    isteğin aynı yorum kimliğini üretmesini veya birbirinin verisini ezmesini önler.
    """
    clean_text = ' '.join(text.strip().split())
    clean_author = ' '.join(author.strip().split()) or 'Yerel Kullanıcı'
    if not clean_text:
        raise ValueError('Yorum metni boş olamaz')

    with transaction(immediate=True) as conn:
        row = conn.execute(
            'SELECT post_json FROM custom_posts WHERE post_id = ?',
            (base_post.id,),
        ).fetchone()
        current = base_post
        if row:
            try:
                current = Post.model_validate_json(row['post_json'])
            except Exception:
                current = base_post

        next_comment_id = max((int(item.id) for item in current.comments), default=0) + 1
        comment = Comment(
            id=next_comment_id,
            author=clean_author[:120],
            text=clean_text[:1200],
            created_at='şimdi',
            likes=0,
        )
        updated = current.model_copy(update={'comments': [*current.comments, comment]})
        conn.execute(
            'INSERT INTO custom_posts(post_id, post_json, created_at) VALUES(?, ?, ?) '
            'ON CONFLICT(post_id) DO UPDATE SET post_json = excluded.post_json',
            (updated.id, updated.model_dump_json(), _now_iso()),
        )
    return updated, comment


def _viewpoint_map(result: AnalysisResult) -> dict[str, int]:
    return {item.name: int(item.percentage) for item in result.viewpoints}


def _question_identity(item) -> str:
    """v1.1.x snapshot'larıyla ortak, görünür metne dayalı soru kimliği."""
    return ' '.join(str(item.text).strip().casefold().split())


def _compute_changes(previous: AnalysisResult | None, current: AnalysisResult) -> list[str]:
    if previous is None:
        return [
            'Bu tartışma için ilk analiz anlık görüntüsü kaydedildi.',
            f'{int(current.indicators.get("comment_count", 0))} benzersiz yorum başlangıç noktası olarak kaydedildi.',
            'Bir sonraki analizde görüş, iddia, soru ve Köprü değişimleri bu kayıtla karşılaştırılacak.',
        ]

    changes: list[str] = []
    old_comments = int(previous.indicators.get('comment_count', 0))
    new_comments = int(current.indicators.get('comment_count', 0))
    delta_comments = new_comments - old_comments
    if delta_comments > 0:
        changes.append(f'{delta_comments} yeni benzersiz yorum analiz kapsamına girdi ({old_comments} → {new_comments}).')
    elif delta_comments < 0:
        changes.append(f'Analiz kapsamındaki benzersiz yorum sayısı {old_comments} → {new_comments} olarak değişti.')

    old_viewpoints = _viewpoint_map(previous)
    new_viewpoints = _viewpoint_map(current)
    added_viewpoints = [name for name in new_viewpoints if name not in old_viewpoints]
    removed_viewpoints = [name for name in old_viewpoints if name not in new_viewpoints]
    if added_viewpoints:
        changes.append('Yeni görüş kümesi görünür oldu: ' + ', '.join(added_viewpoints[:3]) + '.')
    if removed_viewpoints:
        changes.append('Önceki analizde görülen bazı görüş kümeleri artık görünür değil: ' + ', '.join(removed_viewpoints[:3]) + '.')
    for name in new_viewpoints.keys() & old_viewpoints.keys():
        delta = new_viewpoints[name] - old_viewpoints[name]
        if abs(delta) >= 5:
            direction = 'güçlendi' if delta > 0 else 'zayıfladı'
            changes.append(f'“{name}” görüşü %{old_viewpoints[name]} → %{new_viewpoints[name]} ile {direction}.')

    old_claims = {(item.comment_id, item.text.strip().casefold()) for item in previous.claims}
    new_claims = {(item.comment_id, item.text.strip().casefold()) for item in current.claims}
    added_claims = new_claims - old_claims
    if added_claims:
        changes.append(f'{len(added_claims)} yeni doğrulanabilir iddia adayı tespit edildi.')

    old_questions = {_question_identity(item): item for item in previous.unanswered_questions}
    new_questions = {_question_identity(item): item for item in current.unanswered_questions}
    added_questions = [
        item for key, item in new_questions.items()
        if key not in old_questions and item.answer_status in {'Cevapsız', 'Kısmen cevaplandı'}
    ]
    if added_questions:
        changes.append(f'{len(added_questions)} yeni cevapsız soru veya kaynak talebi görünür oldu.')

    resolved_questions = [
        current_item for key, current_item in new_questions.items()
        if key in old_questions
        and old_questions[key].answer_status in {'Cevapsız', 'Kısmen cevaplandı'}
        and current_item.answer_status == 'Cevaplandı'
    ]
    if resolved_questions:
        changes.append(f'{len(resolved_questions)} sorunun tartışma içinde yanıtlandığına ilişkin bağlantı bulundu.')

    partial_questions = [
        current_item for key, current_item in new_questions.items()
        if key in old_questions
        and old_questions[key].answer_status == 'Cevapsız'
        and current_item.answer_status == 'Kısmen cevaplandı'
    ]
    if partial_questions:
        changes.append(f'{len(partial_questions)} soru kısmen yanıtlandı; doğrulama ihtiyacı devam ediyor.')

    if previous.bridge.get('bridge_question', '').strip() != current.bridge.get('bridge_question', '').strip():
        changes.append('Tartışmayı ilerletecek Köprü sorusu yeni analiz verilerine göre güncellendi.')

    if previous.common_ground != current.common_ground:
        changes.append('Ortak zemin özeti önceki anlık görüntüye göre değişti.')

    if not changes:
        changes.append('Önceki analizden bu yana ölçülebilir bir değişiklik tespit edilmedi.')
    return changes[:8]


def _last_analysis_for_post(post_id: int) -> AnalysisResult | None:
    with connection() as conn:
        row = conn.execute(
            'SELECT analysis_json FROM analysis_history WHERE post_id = ? ORDER BY id DESC LIMIT 1',
            (post_id,),
        ).fetchone()
    if not row:
        return None
    try:
        return AnalysisResult.model_validate_json(row['analysis_json'])
    except Exception:
        return None


def record_analysis_snapshot(post: Post, analysis: AnalysisResult) -> tuple[AnalysisResult, int]:
    previous = _last_analysis_for_post(post.id)
    changes = _compute_changes(previous, analysis)
    result = analysis.model_copy(update={'changes_since_last_visit': changes})
    analyzed_at = _now_iso()
    with connection() as conn:
        cursor = conn.execute(
            '''
            INSERT INTO analysis_history(
                post_id, title, post_json, analysis_json, analyzed_at,
                comment_count, viewpoint_count, claim_count, question_count,
                engine_mode, changed_count
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                post.id,
                post.text,
                post.model_dump_json(),
                result.model_dump_json(),
                analyzed_at,
                int(result.indicators.get('comment_count', len(post.comments))),
                len(result.viewpoints),
                len(result.claims),
                len(result.unanswered_questions),
                str(result.engine.get('mode', '')),
                len(changes),
            ),
        )
        conn.commit()
        history_id = int(cursor.lastrowid)
    return result, history_id


def _item_from_row(row) -> AnalysisHistoryItem:
    return AnalysisHistoryItem(
        id=int(row['id']),
        post_id=int(row['post_id']),
        title=str(row['title']),
        analyzed_at=str(row['analyzed_at']),
        relative_time=_relative_time(str(row['analyzed_at'])),
        comment_count=int(row['comment_count']),
        viewpoint_count=int(row['viewpoint_count']),
        claim_count=int(row['claim_count']),
        question_count=int(row['question_count']),
        engine_mode=str(row['engine_mode']),
        changed_count=int(row['changed_count']),
    )


def list_history(limit: int = 30, post_id: int | None = None) -> list[AnalysisHistoryItem]:
    safe_limit = max(1, min(200, int(limit)))
    with connection() as conn:
        if post_id is None:
            rows = conn.execute(
                'SELECT * FROM analysis_history ORDER BY id DESC LIMIT ?',
                (safe_limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM analysis_history WHERE post_id = ? ORDER BY id DESC LIMIT ?',
                (post_id, safe_limit),
            ).fetchall()
    return [_item_from_row(row) for row in rows]


def get_history(history_id: int) -> AnalysisHistoryDetail | None:
    with connection() as conn:
        row = conn.execute('SELECT * FROM analysis_history WHERE id = ?', (history_id,)).fetchone()
    if not row:
        return None
    try:
        post = Post.model_validate_json(row['post_json'])
        analysis = AnalysisResult.model_validate_json(row['analysis_json'])
    except Exception:
        return None
    return AnalysisHistoryDetail(item=_item_from_row(row), post=post, analysis=analysis)


def history_count(post_id: int | None = None) -> int:
    with connection() as conn:
        if post_id is None:
            row = conn.execute('SELECT COUNT(*) AS c FROM analysis_history').fetchone()
        else:
            row = conn.execute('SELECT COUNT(*) AS c FROM analysis_history WHERE post_id = ?', (post_id,)).fetchone()
        return int(row['c'])


def reset_history_for_tests() -> None:
    with transaction(immediate=True) as conn:
        conn.execute('DELETE FROM analysis_history')
        conn.execute('DELETE FROM custom_posts')
        conn.execute("DELETE FROM app_meta WHERE key = 'next_custom_post_id'")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'analysis_history'")
