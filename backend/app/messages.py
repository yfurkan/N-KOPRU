from __future__ import annotations

import json
from datetime import datetime, timezone

from .database import connection, meta_get, meta_set, transaction
from .models import ConversationDetail, ConversationSummary, MessageAttachment, MessageItem


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
    return f'{hours // 24} gün'


def _seed() -> None:
    with transaction(immediate=True) as conn:
        if meta_get(conn, 'messages_seeded') == '1':
            return
        now = _now_iso()
        conn.executemany(
            '''INSERT OR IGNORE INTO conversations(id, title, subtitle, badge, unread_count, last_message, last_time)
               VALUES(?, ?, ?, ?, ?, ?, ?)''',
            [
                (1, 'N-KÖPRÜ Sistem', 'Analiz ve kaynak uyarıları', 'Sistem', 1,
                 'Köprü kartını paylaşmadan önce kaynak uyarılarını kontrol et.', 'Şimdi'),
                (2, 'Ekip görüşmesi', 'Ekip içi çalışma alanı', 'Ekip', 0,
                 'Köprü kartını burada ekip içinde tartışabilirsin.', '3 dk'),
            ],
        )
        if not conn.execute('SELECT 1 FROM messages LIMIT 1').fetchone():
            conn.executemany(
                '''INSERT INTO messages(conversation_id, author, text, created_at, is_mine, attachment_json)
                   VALUES(?, ?, ?, ?, ?, NULL)''',
                [
                    (1, 'N-KÖPRÜ Sistem', 'Analiz sonuçlarını paylaşmadan önce özellikle doğrulanabilir iddiaların kaynak durumunu kontrol et.', now, 0),
                    (2, 'Ayşe', 'Son tartışmadaki ortak zemini ekipçe değerlendirelim. Köprü kartını buraya bırakabilirsin.', now, 0),
                ],
            )
        meta_set(conn, 'messages_seeded', '1')


def _conversation_from_row(row) -> ConversationSummary:
    return ConversationSummary(
        id=int(row['id']),
        title=row['title'],
        subtitle=row['subtitle'],
        badge=row['badge'],
        unread_count=int(row['unread_count']),
        last_message=row['last_message'],
        last_time=row['last_time'],
    )


def _message_from_row(row) -> MessageItem:
    attachment = None
    raw = row['attachment_json']
    if raw:
        try:
            attachment = MessageAttachment.model_validate(json.loads(raw))
        except Exception:
            attachment = None
    return MessageItem(
        id=int(row['id']),
        conversation_id=int(row['conversation_id']),
        author=row['author'],
        text=row['text'],
        created_at=row['created_at'],
        relative_time=_relative_time(row['created_at']),
        is_mine=bool(row['is_mine']),
        attachment=attachment,
    )


def list_conversations() -> list[ConversationSummary]:
    _seed()
    with connection() as conn:
        rows = conn.execute('SELECT * FROM conversations ORDER BY id').fetchall()
    return [_conversation_from_row(row) for row in rows]


def get_conversation(conversation_id: int, mark_read: bool = True) -> ConversationDetail | None:
    _seed()
    with transaction(immediate=mark_read) as conn:
        row = conn.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,)).fetchone()
        if not row:
            return None
        if mark_read and int(row['unread_count']):
            conn.execute('UPDATE conversations SET unread_count = 0 WHERE id = ?', (conversation_id,))
            row = conn.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,)).fetchone()
        messages = conn.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY id', (conversation_id,)).fetchall()
        return ConversationDetail(
            conversation=_conversation_from_row(row),
            messages=[_message_from_row(item) for item in messages],
        )


def send_message(conversation_id: int, text: str) -> MessageItem | None:
    clean = ' '.join(text.split())
    if not clean:
        return None
    _seed()
    now = _now_iso()
    with transaction(immediate=True) as conn:
        if not conn.execute('SELECT 1 FROM conversations WHERE id = ?', (conversation_id,)).fetchone():
            return None
        cursor = conn.execute(
            '''INSERT INTO messages(conversation_id, author, text, created_at, is_mine, attachment_json)
               VALUES(?, 'Sen', ?, ?, 1, NULL)''',
            (conversation_id, clean, now),
        )
        conn.execute(
            'UPDATE conversations SET last_message = ?, last_time = ?, unread_count = 0 WHERE id = ?',
            (clean, 'Şimdi', conversation_id),
        )
        row = conn.execute('SELECT * FROM messages WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return _message_from_row(row)


def share_bridge(
    conversation_id: int,
    *,
    post_id: int,
    title: str,
    summary: str,
    common_acceptance: str,
    main_divergence: str,
    missing_information: str,
    bridge_question: str,
) -> MessageItem | None:
    _seed()
    attachment = MessageAttachment(
        kind='bridge', title=title, post_id=post_id, tab_index=7,
        summary=summary, common_acceptance=common_acceptance,
        main_divergence=main_divergence, missing_information=missing_information,
        bridge_question=bridge_question,
    )
    now = _now_iso()
    with transaction(immediate=True) as conn:
        if not conn.execute('SELECT 1 FROM conversations WHERE id = ?', (conversation_id,)).fetchone():
            return None
        cursor = conn.execute(
            '''INSERT INTO messages(conversation_id, author, text, created_at, is_mine, attachment_json)
               VALUES(?, 'Sen', ?, ?, 1, ?)''',
            (conversation_id, 'N-KÖPRÜ Köprü kartını paylaştı.', now, json.dumps(attachment.model_dump(), ensure_ascii=False)),
        )
        conn.execute(
            'UPDATE conversations SET last_message = ?, last_time = ?, unread_count = 0 WHERE id = ?',
            (f'Köprü kartı: {title}', 'Şimdi', conversation_id),
        )
        row = conn.execute('SELECT * FROM messages WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return _message_from_row(row)


def reset_messages_for_tests() -> None:
    with transaction(immediate=True) as conn:
        conn.execute('DELETE FROM messages')
        conn.execute('DELETE FROM conversations')
        conn.execute("DELETE FROM app_meta WHERE key = 'messages_seeded'")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'messages'")
    _seed()


_seed()
