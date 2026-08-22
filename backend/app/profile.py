from __future__ import annotations

from datetime import datetime, timezone

from .database import connection, transaction
from .history import list_history
from .models import ProfileResponse, ProfileStats, ProfileUpdateRequest, ProfileUser


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_profile() -> None:
    now = _now_iso()
    with connection() as conn:
        row = conn.execute('SELECT id FROM profiles WHERE id = 1').fetchone()
        if not row:
            conn.execute(
                'INSERT INTO profiles(id, display_name, handle, bio, created_at, updated_at) VALUES(1, ?, ?, ?, ?, ?)',
                ('Yerel Kullanıcı', '@yerel', 'N-KÖPRÜ yerel çalışma profili', now, now),
            )
            conn.commit()


def _user() -> ProfileUser:
    _ensure_profile()
    with connection() as conn:
        row = conn.execute('SELECT * FROM profiles WHERE id = 1').fetchone()
    return ProfileUser(
        display_name=row['display_name'],
        handle=row['handle'],
        bio=row['bio'],
        created_at=row['created_at'],
        updated_at=row['updated_at'],
    )


def _stats() -> ProfileStats:
    with connection() as conn:
        analysis_count = int(conn.execute('SELECT COUNT(*) AS c FROM analysis_history').fetchone()['c'])
        unique_discussions = int(conn.execute('SELECT COUNT(DISTINCT post_id) AS c FROM analysis_history').fetchone()['c'])
        bridge_count = int(conn.execute(
            "SELECT COUNT(*) AS c FROM bookmarks WHERE kind = 'bridge'"
        ).fetchone()['c'])
        bookmark_count = int(conn.execute('SELECT COUNT(*) AS c FROM bookmarks').fetchone()['c'])
        list_count = int(conn.execute('SELECT COUNT(*) AS c FROM topic_lists').fetchone()['c'])
        list_item_count = int(conn.execute('SELECT COUNT(*) AS c FROM topic_list_entries').fetchone()['c'])
        notification_count = int(conn.execute('SELECT COUNT(*) AS c FROM notifications WHERE deleted = 0').fetchone()['c'])
        message_count = int(conn.execute('SELECT COUNT(*) AS c FROM messages WHERE is_mine = 1').fetchone()['c'])
        last = conn.execute('SELECT analyzed_at FROM analysis_history ORDER BY id DESC LIMIT 1').fetchone()
    return ProfileStats(
        analysis_count=analysis_count,
        unique_discussions=unique_discussions,
        saved_bridge_count=bridge_count,
        bookmark_count=bookmark_count,
        list_count=list_count,
        list_item_count=list_item_count,
        notification_count=notification_count,
        sent_message_count=message_count,
        last_analyzed_at=str(last['analyzed_at']) if last else None,
    )


def get_profile() -> ProfileResponse:
    return ProfileResponse(user=_user(), stats=_stats(), recent_analyses=list_history(limit=8))


def update_profile(req: ProfileUpdateRequest) -> ProfileResponse:
    _ensure_profile()
    display_name = ' '.join(req.display_name.strip().split())
    handle = req.handle.strip()
    bio = ' '.join(req.bio.strip().split())
    if not display_name:
        raise ValueError('Görünen ad boş olamaz')
    if not handle:
        handle = '@yerel'
    if not handle.startswith('@'):
        handle = '@' + handle
    now = _now_iso()
    with transaction(immediate=True) as conn:
        conn.execute(
            'UPDATE profiles SET display_name = ?, handle = ?, bio = ?, updated_at = ? WHERE id = 1',
            (display_name, handle[:80], bio[:500], now),
        )
    return get_profile()


def reset_profile_for_tests() -> None:
    with transaction(immediate=True) as conn:
        conn.execute('DELETE FROM profiles')
