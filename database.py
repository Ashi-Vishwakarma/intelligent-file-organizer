"""
database.py
SQLite-backed history and report storage for the Intelligent File Organizer.
Each run is stored as a session; individual file moves are stored as records.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path


DEFAULT_DB = os.path.join(
    os.path.dirname(__file__), "..", "organizer_history.db"
)


class OrganizerDB:
    """Thin wrapper around an SQLite database for organizing history."""

    CREATE_SESSIONS = """
    CREATE TABLE IF NOT EXISTS sessions (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        source_dir    TEXT    NOT NULL,
        output_dir    TEXT    NOT NULL,
        dry_run       INTEGER NOT NULL DEFAULT 0,
        total_scanned INTEGER NOT NULL DEFAULT 0,
        moved         INTEGER NOT NULL DEFAULT 0,
        duplicates    INTEGER NOT NULL DEFAULT 0,
        errors        INTEGER NOT NULL DEFAULT 0,
        created_at    TEXT    NOT NULL
    );
    """

    CREATE_RECORDS = """
    CREATE TABLE IF NOT EXISTS file_records (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id   INTEGER NOT NULL REFERENCES sessions(id),
        source_path  TEXT    NOT NULL,
        dest_path    TEXT    NOT NULL,
        category     TEXT    NOT NULL,
        is_duplicate INTEGER NOT NULL DEFAULT 0,
        created_at   TEXT    NOT NULL
    );
    """

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self._conn:
            self._conn.execute(self.CREATE_SESSIONS)
            self._conn.execute(self.CREATE_RECORDS)

    # ── Write ──────────────────────────────────────────────────────────────────

    def save_report(self, report: dict) -> int:
        """Persist a full organizer report; return the new session id."""
        stats = report["stats"]
        now   = datetime.now().isoformat()

        with self._conn as conn:
            cur = conn.execute(
                """
                INSERT INTO sessions
                    (source_dir, output_dir, dry_run,
                     total_scanned, moved, duplicates, errors, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report["source_directory"],
                    report["output_directory"],
                    int(report["dry_run"]),
                    stats["total_scanned"],
                    stats["moved"],
                    stats["duplicates_found"],
                    stats["errors"],
                    now,
                ),
            )
            session_id = cur.lastrowid

            # Moved files
            for rec in report["moved_files"]:
                conn.execute(
                    """
                    INSERT INTO file_records
                        (session_id, source_path, dest_path, category,
                         is_duplicate, created_at)
                    VALUES (?, ?, ?, ?, 0, ?)
                    """,
                    (session_id, rec["source"], rec["destination"],
                     rec["category"], now),
                )

            # Duplicate files
            for rec in report["duplicate_files"]:
                conn.execute(
                    """
                    INSERT INTO file_records
                        (session_id, source_path, dest_path, category,
                         is_duplicate, created_at)
                    VALUES (?, ?, ?, 'Duplicates', 1, ?)
                    """,
                    (session_id, rec["duplicate"], rec["original"], now),
                )

        return session_id

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_sessions(self, limit: int = 20) -> list[dict]:
        """Return the most recent *limit* sessions."""
        rows = self._conn.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_session_records(self, session_id: int) -> list[dict]:
        """Return all file records for a given session."""
        rows = self._conn.execute(
            "SELECT * FROM file_records WHERE session_id = ?", (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_statistics(self) -> dict:
        """Return aggregate statistics across all sessions."""
        row = self._conn.execute(
            """
            SELECT
                COUNT(*)          AS total_sessions,
                SUM(moved)        AS total_moved,
                SUM(duplicates)   AS total_duplicates,
                SUM(errors)       AS total_errors,
                MIN(created_at)   AS first_run,
                MAX(created_at)   AS last_run
            FROM sessions
            WHERE dry_run = 0
            """
        ).fetchone()
        return dict(row) if row else {}

    def close(self):
        self._conn.close()
