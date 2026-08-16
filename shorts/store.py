from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from shorts.config import DB_PATH, ensure_dirs


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS used_headlines (
            hash TEXT PRIMARY KEY,
            title TEXT,
            source TEXT,
            used_at TEXT,
            video_path TEXT,
            video_id TEXT,
            status TEXT
        )
        """
    )
    return conn


def used_hashes(path: Path = DB_PATH) -> set:
    conn = connect(path)
    try:
        rows = conn.execute("SELECT hash FROM used_headlines").fetchall()
    finally:
        conn.close()
    return {row[0] for row in rows}


def mark_used(
    headline,
    status: str,
    video_path: str = "",
    video_id: str = "",
    path: Path = DB_PATH,
) -> None:
    conn = connect(path)
    try:
        conn.execute(
            """
            INSERT INTO used_headlines (hash, title, source, used_at, video_path, video_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hash) DO UPDATE SET
                status=excluded.status,
                video_path=excluded.video_path,
                video_id=excluded.video_id,
                used_at=excluded.used_at
            """,
            (
                headline.hash,
                headline.title,
                headline.source,
                datetime.now().isoformat(timespec="seconds"),
                video_path,
                video_id,
                status,
            ),
        )
        conn.commit()
    finally:
        conn.close()
