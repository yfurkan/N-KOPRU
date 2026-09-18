from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'data' / 'nkopru.db'


def db_path() -> Path:
    raw = os.getenv('N_KOPRU_DB_PATH', '').strip()
    path = Path(raw).expanduser() if raw else _DEFAULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    conn.execute('PRAGMA synchronous = NORMAL')
    return conn


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def transaction(immediate: bool = False) -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        conn.execute('BEGIN IMMEDIATE' if immediate else 'BEGIN')
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_schema() -> None:
    with connection() as conn:
        conn.executescript(
            '''
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                post_id INTEGER,
                tab_index INTEGER,
                badge TEXT NOT NULL DEFAULT 'Bilgi',
                priority TEXT NOT NULL DEFAULT 'normal',
                signature_key TEXT NOT NULL UNIQUE,
                deleted INTEGER NOT NULL DEFAULT 0,
                deleted_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_active_created
                ON notifications(deleted, created_at DESC);

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                subtitle TEXT NOT NULL,
                badge TEXT NOT NULL DEFAULT 'Ekip',
                unread_count INTEGER NOT NULL DEFAULT 0,
                last_message TEXT NOT NULL DEFAULT '',
                last_time TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_mine INTEGER NOT NULL DEFAULT 0,
                attachment_json TEXT,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id, id);

            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                post_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                tab_index INTEGER,
                comment_id INTEGER,
                created_at TEXT NOT NULL,
                identity_key TEXT NOT NULL UNIQUE
            );
            CREATE INDEX IF NOT EXISTS idx_bookmarks_created ON bookmarks(created_at DESC);

            CREATE TABLE IF NOT EXISTS topic_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS topic_list_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                post_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                tab_index INTEGER,
                comment_id INTEGER,
                created_at TEXT NOT NULL,
                identity_key TEXT NOT NULL,
                FOREIGN KEY(list_id) REFERENCES topic_lists(id) ON DELETE CASCADE,
                UNIQUE(list_id, identity_key)
            );
            CREATE INDEX IF NOT EXISTS idx_list_entries_list ON topic_list_entries(list_id, id DESC);

            CREATE TABLE IF NOT EXISTS custom_posts (
                post_id INTEGER PRIMARY KEY,
                post_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                post_json TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                analyzed_at TEXT NOT NULL,
                comment_count INTEGER NOT NULL DEFAULT 0,
                viewpoint_count INTEGER NOT NULL DEFAULT 0,
                claim_count INTEGER NOT NULL DEFAULT 0,
                question_count INTEGER NOT NULL DEFAULT 0,
                engine_mode TEXT NOT NULL DEFAULT '',
                changed_count INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_analysis_history_post
                ON analysis_history(post_id, id DESC);
            CREATE INDEX IF NOT EXISTS idx_analysis_history_recent
                ON analysis_history(id DESC);

            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                display_name TEXT NOT NULL,
                handle TEXT NOT NULL,
                bio TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pilot_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_code TEXT NOT NULL UNIQUE,
                assignment TEXT NOT NULL,
                practice INTEGER NOT NULL DEFAULT 1,
                consented_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_pilot_sessions_completed
                ON pilot_sessions(practice, completed_at);

            CREATE TABLE IF NOT EXISTS pilot_phase_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                phase_index INTEGER NOT NULL,
                variant TEXT NOT NULL,
                scenario_key TEXT NOT NULL,
                selected_answer INTEGER NOT NULL,
                correct INTEGER NOT NULL,
                duration_ms INTEGER NOT NULL,
                clarity_rating INTEGER NOT NULL,
                confidence_rating INTEGER NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES pilot_sessions(id) ON DELETE CASCADE,
                UNIQUE(session_id, phase_index)
            );
            CREATE INDEX IF NOT EXISTS idx_pilot_results_variant
                ON pilot_phase_results(variant, completed_at);
            '''
        )
        conn.commit()


def meta_get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute('SELECT value FROM app_meta WHERE key = ?', (key,)).fetchone()
    return str(row['value']) if row else None


def meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        'INSERT INTO app_meta(key, value) VALUES(?, ?) '
        'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
        (key, value),
    )


def reset_database_for_tests() -> None:
    """Test yardımcıları için tüm kalıcı uygulama tablolarını sıfırlar."""
    initialize_schema()
    with transaction(immediate=True) as conn:
        for table in (
            'messages', 'conversations', 'notifications', 'bookmarks',
            'topic_list_entries', 'topic_lists', 'analysis_history',
            'custom_posts', 'profiles', 'pilot_phase_results',
            'pilot_sessions', 'app_meta',
        ):
            conn.execute(f'DELETE FROM {table}')
        conn.execute(
            "DELETE FROM sqlite_sequence WHERE name IN "
            "('notifications','messages','bookmarks','topic_lists','topic_list_entries',"
            "'analysis_history','pilot_sessions','pilot_phase_results')"
        )


initialize_schema()
