import os
import sqlite3
import threading
from datetime import datetime


class PlayHistoryDB:
    def __init__(self, db_path):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self._db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=OFF")
        except Exception:
            pass
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    title TEXT DEFAULT '',
                    media_type TEXT DEFAULT 'unknown',
                    play_start TEXT,
                    play_end TEXT,
                    resume_time REAL DEFAULT 0.0,
                    total_time REAL DEFAULT 0.0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_play_history_start
                ON play_history(play_start DESC)
            """)
            conn.commit()
            conn.close()

    def add_play_start(self, file_path, title="", media_type="unknown", max_entries=100):
        now = datetime.now().isoformat()
        with self._lock:
            conn = self._get_conn()
            existing = conn.execute("SELECT id FROM play_history WHERE file_path=?", (file_path,)).fetchone()
            if existing:
                conn.execute("""
                    UPDATE play_history SET title=?, media_type=?, play_start=?, play_end=NULL, resume_time=0, total_time=0
                    WHERE file_path=?
                """, (title, media_type, now, file_path))
            else:
                conn.execute("""
                    INSERT INTO play_history (file_path, title, media_type, play_start)
                    VALUES (?, ?, ?, ?)
                """, (file_path, title, media_type, now))
            self._cleanup(conn, max_entries)
            conn.commit()
            conn.close()

    @staticmethod
    def _cleanup(conn, max_entries):
        conn.execute("""
            DELETE FROM play_history WHERE id NOT IN (
                SELECT id FROM play_history ORDER BY play_start DESC LIMIT ?
            )
        """, (max_entries,))

    def get_history(self, limit=100):
        with self._lock:
            conn = self._get_conn()
            cursor = conn.execute("""
                SELECT * FROM play_history
                ORDER BY play_start DESC
                LIMIT ?
            """, (limit,))
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows

    def clear_history(self):
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM play_history")
            conn.commit()
            conn.close()

    def update_play_stop(self, file_path, resume_time, total_time):
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                UPDATE play_history SET resume_time=?, total_time=?, play_end=?
                WHERE file_path=?
            """, (resume_time, total_time, datetime.now().isoformat(), file_path))
            conn.commit()
            conn.close()

    def delete_entry(self, entry_id):
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM play_history WHERE id=?", (entry_id,))
            conn.commit()
            conn.close()


