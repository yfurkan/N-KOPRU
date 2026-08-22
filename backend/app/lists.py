from __future__ import annotations

from datetime import datetime, timezone

from .database import connection, meta_get, meta_set, transaction
from .models import TopicList, TopicListCreateRequest, TopicListDetail, TopicListEntry, TopicListEntryCreateRequest

_ALLOWED_KINDS = {'discussion', 'claim', 'bridge'}
_DEFAULTS = [
    ('AI & Eğitim', 'Yapay zekâ, öğrenme, etik ve akademik güvenilirlik tartışmaları.'),
    ('Dijital Etik', 'Mahremiyet, güvenlik, içerik sorumluluğu ve platform davranışları.'),
    ('Gençlik & Sosyal Medya', 'Genç kullanıcı deneyimi, dijital iyi oluş ve çevrim içi etkileşim.'),
]


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


def _normalize_name(value: str) -> str:
    return ' '.join(value.strip().split()).casefold()


def _entry_identity(kind: str, post_id: int, text: str, comment_id: int | None) -> str:
    if kind == 'discussion':
        return f'discussion:{post_id}'
    if kind == 'claim':
        return f'claim:{post_id}:{comment_id if comment_id is not None else "none"}'
    return f'bridge:{post_id}:{text.strip().casefold()}'


def _seed_defaults() -> None:
    with transaction(immediate=True) as conn:
        if meta_get(conn, 'topic_lists_seeded') == '1':
            return
        now = _now_iso()
        for name, description in _DEFAULTS:
            conn.execute(
                'INSERT OR IGNORE INTO topic_lists(name, normalized_name, description, created_at) VALUES(?, ?, ?, ?)',
                (name, _normalize_name(name), description, now),
            )
        meta_set(conn, 'topic_lists_seeded', '1')


def _summary_from_row(conn, row) -> TopicList:
    counts = conn.execute(
        '''SELECT COUNT(*) AS total,
                  SUM(CASE WHEN kind='discussion' THEN 1 ELSE 0 END) AS discussions,
                  SUM(CASE WHEN kind='claim' THEN 1 ELSE 0 END) AS claims,
                  SUM(CASE WHEN kind='bridge' THEN 1 ELSE 0 END) AS bridges
           FROM topic_list_entries WHERE list_id = ?''',
        (row['id'],),
    ).fetchone()
    return TopicList(
        id=int(row['id']),
        name=row['name'],
        description=row['description'],
        created_at=row['created_at'],
        relative_time=_relative_time(row['created_at']),
        item_count=int(counts['total'] or 0),
        discussion_count=int(counts['discussions'] or 0),
        claim_count=int(counts['claims'] or 0),
        bridge_count=int(counts['bridges'] or 0),
    )


def _entry_from_row(row) -> TopicListEntry:
    return TopicListEntry(
        id=int(row['id']),
        list_id=int(row['list_id']),
        kind=row['kind'],
        post_id=int(row['post_id']),
        title=row['title'],
        text=row['text'],
        tab_index=row['tab_index'],
        comment_id=row['comment_id'],
        created_at=row['created_at'],
        relative_time=_relative_time(row['created_at']),
    )


def list_lists() -> list[TopicList]:
    _seed_defaults()
    with connection() as conn:
        rows = conn.execute('SELECT * FROM topic_lists ORDER BY id').fetchall()
        return [_summary_from_row(conn, row) for row in rows]


def count_lists() -> int:
    _seed_defaults()
    with connection() as conn:
        return int(conn.execute('SELECT COUNT(*) AS c FROM topic_lists').fetchone()['c'])


def create_list(req: TopicListCreateRequest) -> tuple[TopicList, bool]:
    _seed_defaults()
    name = ' '.join(req.name.strip().split())
    description = ' '.join(req.description.strip().split())
    if not name:
        raise ValueError('Liste adı boş olamaz')
    normalized = _normalize_name(name)
    with transaction(immediate=True) as conn:
        existing = conn.execute('SELECT * FROM topic_lists WHERE normalized_name = ?', (normalized,)).fetchone()
        if existing:
            return _summary_from_row(conn, existing), False
        cursor = conn.execute(
            'INSERT INTO topic_lists(name, normalized_name, description, created_at) VALUES(?, ?, ?, ?)',
            (name, normalized, description, _now_iso()),
        )
        row = conn.execute('SELECT * FROM topic_lists WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return _summary_from_row(conn, row), True


def get_list(list_id: int) -> TopicListDetail | None:
    _seed_defaults()
    with connection() as conn:
        row = conn.execute('SELECT * FROM topic_lists WHERE id = ?', (list_id,)).fetchone()
        if not row:
            return None
        entries = conn.execute('SELECT * FROM topic_list_entries WHERE list_id = ? ORDER BY id DESC', (list_id,)).fetchall()
        return TopicListDetail(list=_summary_from_row(conn, row), items=[_entry_from_row(item) for item in entries])


def delete_list(list_id: int) -> TopicList | None:
    _seed_defaults()
    with transaction(immediate=True) as conn:
        row = conn.execute('SELECT * FROM topic_lists WHERE id = ?', (list_id,)).fetchone()
        if not row:
            return None
        summary = _summary_from_row(conn, row)
        conn.execute('DELETE FROM topic_lists WHERE id = ?', (list_id,))
        return summary


def add_entry(list_id: int, req: TopicListEntryCreateRequest) -> tuple[TopicListEntry, bool]:
    _seed_defaults()
    if req.kind not in _ALLOWED_KINDS:
        raise ValueError('Geçersiz liste öğesi türü')
    title = req.title.strip()
    text = req.text.strip()
    identity = _entry_identity(req.kind, req.post_id, text, req.comment_id)
    with transaction(immediate=True) as conn:
        if not conn.execute('SELECT 1 FROM topic_lists WHERE id = ?', (list_id,)).fetchone():
            raise KeyError('Liste bulunamadı')
        existing = conn.execute(
            'SELECT * FROM topic_list_entries WHERE list_id = ? AND identity_key = ?',
            (list_id, identity),
        ).fetchone()
        if existing:
            return _entry_from_row(existing), False
        cursor = conn.execute(
            '''INSERT INTO topic_list_entries(list_id, kind, post_id, title, text, tab_index, comment_id, created_at, identity_key)
               VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (list_id, req.kind, req.post_id, title, text, req.tab_index, req.comment_id, _now_iso(), identity),
        )
        row = conn.execute('SELECT * FROM topic_list_entries WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return _entry_from_row(row), True


def delete_entry(list_id: int, entry_id: int) -> TopicListEntry | None:
    _seed_defaults()
    with transaction(immediate=True) as conn:
        if not conn.execute('SELECT 1 FROM topic_lists WHERE id = ?', (list_id,)).fetchone():
            return None
        row = conn.execute(
            'SELECT * FROM topic_list_entries WHERE id = ? AND list_id = ?',
            (entry_id, list_id),
        ).fetchone()
        if not row:
            return None
        conn.execute('DELETE FROM topic_list_entries WHERE id = ?', (entry_id,))
        return _entry_from_row(row)


def reset_lists(seed: bool = True) -> None:
    with transaction(immediate=True) as conn:
        conn.execute('DELETE FROM topic_list_entries')
        conn.execute('DELETE FROM topic_lists')
        conn.execute("DELETE FROM app_meta WHERE key = 'topic_lists_seeded'")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('topic_lists','topic_list_entries')")
    if seed:
        _seed_defaults()


_seed_defaults()
