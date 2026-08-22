from __future__ import annotations

from datetime import datetime, timezone

from .database import connection, transaction
from .models import BookmarkCreateRequest, BookmarkItem

_ALLOWED_KINDS = {'discussion', 'claim', 'bridge'}


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


def _identity(kind: str, post_id: int, text: str, comment_id: int | None) -> str:
    if kind == 'discussion':
        return f'discussion:{post_id}'
    if kind == 'claim':
        return f'claim:{post_id}:{comment_id if comment_id is not None else "none"}'
    return f'bridge:{post_id}:{text.strip().casefold()}'


def _from_row(row) -> BookmarkItem:
    return BookmarkItem(
        id=int(row['id']),
        kind=row['kind'],
        post_id=int(row['post_id']),
        title=row['title'],
        text=row['text'],
        tab_index=row['tab_index'],
        comment_id=row['comment_id'],
        created_at=row['created_at'],
        relative_time=_relative_time(row['created_at']),
    )


def list_bookmarks(kind: str | None = None) -> list[BookmarkItem]:
    if kind not in (None, 'all', *_ALLOWED_KINDS):
        raise ValueError('Geçersiz yer imi filtresi')
    with connection() as conn:
        if kind and kind != 'all':
            rows = conn.execute('SELECT * FROM bookmarks WHERE kind = ? ORDER BY id DESC', (kind,)).fetchall()
        else:
            rows = conn.execute('SELECT * FROM bookmarks ORDER BY id DESC').fetchall()
    return [_from_row(row) for row in rows]


def create_bookmark(req: BookmarkCreateRequest) -> tuple[BookmarkItem, bool]:
    if req.kind not in _ALLOWED_KINDS:
        raise ValueError('Geçersiz yer imi türü')
    title = req.title.strip()
    text = req.text.strip()
    identity = _identity(req.kind, req.post_id, text, req.comment_id)
    with transaction(immediate=True) as conn:
        existing = conn.execute('SELECT * FROM bookmarks WHERE identity_key = ?', (identity,)).fetchone()
        if existing:
            return _from_row(existing), False
        cursor = conn.execute(
            '''INSERT INTO bookmarks(kind, post_id, title, text, tab_index, comment_id, created_at, identity_key)
               VALUES(?, ?, ?, ?, ?, ?, ?, ?)''',
            (req.kind, req.post_id, title, text, req.tab_index, req.comment_id, _now_iso(), identity),
        )
        row = conn.execute('SELECT * FROM bookmarks WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return _from_row(row), True


def delete_bookmark(bookmark_id: int) -> BookmarkItem | None:
    with transaction(immediate=True) as conn:
        row = conn.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,)).fetchone()
        if not row:
            return None
        conn.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
        return _from_row(row)


def get_bookmark(bookmark_id: int) -> BookmarkItem | None:
    with connection() as conn:
        row = conn.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,)).fetchone()
    return _from_row(row) if row else None


def count_bookmarks() -> int:
    with connection() as conn:
        return int(conn.execute('SELECT COUNT(*) AS c FROM bookmarks').fetchone()['c'])


def reset_bookmarks() -> None:
    with transaction(immediate=True) as conn:
        conn.execute('DELETE FROM bookmarks')
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'bookmarks'")
