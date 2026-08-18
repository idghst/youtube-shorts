from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from shorts.config import DB_PATH, ensure_dirs, supabase_key, supabase_skip, supabase_url

log = logging.getLogger("shorts")

# tests replace this
rpc_impl = None


def _load_cfg() -> dict:
    try:
        from shorts.config import load_config

        return load_config()
    except SystemExit:
        return {}


def supabase_ready(cfg: dict | None = None) -> bool:
    if supabase_skip():
        return False
    data = cfg if cfg is not None else _load_cfg()
    return bool(supabase_url(data) and supabase_key(data))


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(str(path))
    _ensure_sqlite(conn)
    return conn


def _ensure_sqlite(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(used_headlines)").fetchall()}
    if not cols:
        conn.execute(
            """
            CREATE TABLE used_headlines (
                hash TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT '',
                title TEXT,
                source TEXT,
                used_at TEXT,
                video_path TEXT,
                video_id TEXT,
                status TEXT,
                PRIMARY KEY (channel, hash)
            )
            """
        )
        return
    if "channel" not in cols:
        conn.execute(
            "ALTER TABLE used_headlines ADD COLUMN channel TEXT NOT NULL DEFAULT ''"
        )


def _conflict_target(conn: sqlite3.Connection) -> str:
    pk = [row[1] for row in conn.execute("PRAGMA table_info(used_headlines)") if row[5]]
    if pk == ["hash"]:
        return "hash"
    return "channel, hash"


def _sqlite_titles(channel: str, path: Path) -> list:
    conn = connect(path)
    try:
        rows = conn.execute(
            """
            SELECT title FROM used_headlines
            WHERE title != '' AND (channel = ? OR channel = '')
            ORDER BY used_at DESC
            LIMIT 40
            """,
            (channel,),
        ).fetchall()
    finally:
        conn.close()
    seen = set()
    titles = []
    for (title,) in rows:
        text = (title or "").strip()
        if text and text not in seen:
            seen.add(text)
            titles.append(text)
    return titles


def _remote_titles(channel: str, cfg: dict | None = None) -> list:
    if not supabase_ready(cfg):
        return []
    remote = call_rpc("youtube_recent_titles", {"p_channel_key": channel}, cfg=cfg)
    if remote is None:
        return []
    if not isinstance(remote, list):
        raise SystemExit("youtube_recent_titles 응답이 배열이 아님")
    titles = []
    for item in remote:
        text = str(item or "").strip()
        if text:
            titles.append(text)
    return titles


def recent_titles(channel: str, path: Path = DB_PATH, cfg: dict | None = None) -> list:
    titles = _sqlite_titles(channel, path)
    seen = set(titles)
    for title in _remote_titles(channel, cfg=cfg):
        if title not in seen:
            seen.add(title)
            titles.append(title)
    return titles


def _sqlite_hashes(channel: str, path: Path) -> set:
    conn = connect(path)
    try:
        rows = conn.execute(
            "SELECT hash FROM used_headlines WHERE channel = ? OR channel = ''",
            (channel,),
        ).fetchall()
    finally:
        conn.close()
    return {row[0] for row in rows if row[0]}


def call_rpc(name: str, payload: dict, cfg: dict | None = None):
    if rpc_impl is not None:
        return rpc_impl(name, payload)
    data = cfg if cfg is not None else _load_cfg()
    url = supabase_url(data)
    key = supabase_key(data)
    if not url or not key:
        raise SystemExit("Supabase URL/키 없음. config.yaml supabase 또는 환경변수를 넣어라.")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        "%s/rest/v1/rpc/%s" % (url, name),
        data=body,
        method="POST",
        headers={
            "apikey": key,
            "Authorization": "Bearer %s" % key,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; shorts/0.1; +local)",
        },
    )
    try:
        with urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise SystemExit("Supabase RPC %s 실패 %s: %s" % (name, exc.code, err[:500])) from exc
    except URLError as exc:
        raise SystemExit("Supabase 연결 실패: %s" % exc.reason) from exc
    if not raw:
        return None
    return json.loads(raw)


def claimed_remote_hashes(channel: str, cfg: dict | None = None) -> set:
    if not supabase_ready(cfg):
        log.warning("Supabase 없음. 로컬 shorts.db 만 본다. VM 간 중복 업로드가 날 수 있다.")
        return set()
    remote = call_rpc("youtube_claimed_hashes", {"p_channel_key": channel}, cfg=cfg)
    if remote is None:
        return set()
    if not isinstance(remote, list):
        raise SystemExit("youtube_claimed_hashes 응답이 배열이 아님")
    return {item for item in remote if item}


def used_hashes(channel: str, path: Path = DB_PATH, cfg: dict | None = None) -> set:
    hashes = _sqlite_hashes(channel, path)
    hashes |= claimed_remote_hashes(channel, cfg=cfg)
    return hashes


def try_claim(
    headline,
    *,
    channel: str,
    job_path: str = "",
    youtube_channel_id: str = "",
    cfg: dict | None = None,
) -> bool:
    if not supabase_ready(cfg):
        log.warning("Supabase 없음. 로컬만 선점한다.")
        return True
    claimed = call_rpc(
        "youtube_try_claim",
        {
            "p_channel_key": channel,
            "p_headline_hash": headline.hash,
            "p_title": headline.title,
            "p_source": headline.source or None,
            "p_headline_link": getattr(headline, "link", "") or None,
            "p_job_path": job_path or None,
            "p_youtube_channel_id": youtube_channel_id or None,
        },
        cfg=cfg,
    )
    return bool(claimed)


def mark_used(
    headline,
    status: str,
    *,
    channel: str,
    video_path: str = "",
    video_id: str = "",
    job_path: str = "",
    youtube_channel_id: str = "",
    path: Path = DB_PATH,
    cfg: dict | None = None,
) -> None:
    conn = connect(path)
    try:
        target = _conflict_target(conn)
        conn.execute(
            """
            INSERT INTO used_headlines
                (hash, channel, title, source, used_at, video_path, video_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(%s) DO UPDATE SET
                status=excluded.status,
                video_path=excluded.video_path,
                video_id=excluded.video_id,
                used_at=excluded.used_at,
                channel=excluded.channel
            """
            % target,
            (
                headline.hash,
                channel,
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

    if not supabase_ready(cfg):
        return
    if status == "picked":
        return
    call_rpc(
        "youtube_upsert_upload",
        {
            "p_channel_key": channel,
            "p_headline_hash": headline.hash,
            "p_title": headline.title,
            "p_status": status,
            "p_source": headline.source or None,
            "p_headline_link": getattr(headline, "link", "") or None,
            "p_video_id": video_id or None,
            "p_job_path": job_path or None,
            "p_youtube_channel_id": youtube_channel_id or None,
        },
        cfg=cfg,
    )
