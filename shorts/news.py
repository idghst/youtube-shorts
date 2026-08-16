from __future__ import annotations

import hashlib
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from shorts.config import DEFAULT_CHANNEL, OUT_DIR, channel_dir, ensure_dirs
from shorts.models import Headline, slugify
from shorts.store import used_hashes

log = logging.getLogger("shorts")
UA = "Mozilla/5.0 (compatible; shorts/0.1; +local)"
_TAG = re.compile(r"<[^>]+>")
_NS = re.compile(r"^\{.+\}")


def _local(tag: str) -> str:
    return _NS.sub("", tag)


def _text(el) -> str:
    if el is None:
        return ""
    return _TAG.sub(" ", "".join(el.itertext())).replace("&nbsp;", " ")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def headline_hash(title: str) -> str:
    return hashlib.sha256(" ".join(title.lower().split()).encode("utf-8")).hexdigest()


def _parse_date(raw: str) -> datetime:
    raw = (raw or "").strip()
    if not raw:
        return datetime.min
    try:
        return parsedate_to_datetime(raw).replace(tzinfo=None)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def _child(el, *names):
    want = set(names)
    for child in list(el):
        if _local(child.tag) in want:
            return child
    return None


def _link(el) -> str:
    link_el = _child(el, "link")
    if link_el is None:
        return ""
    href = (link_el.get("href") or "").strip()
    if href:
        return href
    return _clean(_text(link_el))


def parse_feed(xml_text: str, source: str) -> list:
    root = ET.fromstring(xml_text)
    items = []
    for el in root.iter():
        if _local(el.tag) not in {"item", "entry"}:
            continue
        title = _clean(_text(_child(el, "title")))
        if not title:
            continue
        summary = _clean(_text(_child(el, "description", "summary", "content")))
        published = _clean(
            _text(_child(el, "pubDate", "published", "updated", "date"))
        )
        items.append(
            Headline(
                source=source,
                title=title,
                summary=summary,
                link=_link(el),
                published=published,
                hash=headline_hash(title),
            )
        )
    return items


def fetch_feed(name: str, url: str, timeout: int = 20) -> list:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    text = raw.decode("utf-8", errors="replace")
    return parse_feed(text, name)


def claimed_hashes(out_dir: Path = OUT_DIR) -> set:
    hashes = used_hashes()
    if not out_dir.is_dir():
        return hashes
    for path in out_dir.glob("*/*/headline.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        digest = data.get("hash")
        if digest:
            hashes.add(digest)
    return hashes


def collect(feeds: list) -> list:
    found = []
    seen = set()
    for feed in feeds:
        name = feed.get("name") or "rss"
        url = feed.get("url") or ""
        if not url:
            continue
        try:
            items = fetch_feed(name, url)
        except (URLError, OSError, ET.ParseError) as exc:
            log.warning("RSS 실패 %s: %s", name, exc)
            continue
        log.info("RSS %s %d건", name, len(items))
        for item in items:
            if item.hash in seen:
                continue
            seen.add(item.hash)
            found.append(item)
    found.sort(key=lambda h: _parse_date(h.published), reverse=True)
    return found


_HINTS = (
    "금리", "연준", "fed", "fomc", "증시", "코스피", "코스닥", "나스닥", "다우",
    "환율", "달러", "물가", "cpi", "관세", "유가", "채권", "국채", "실적",
    "어닝", "수출", "무역", "한은", "ecb", "주가", "배당", "etf", "비트코인",
    "반도체", "금리인하", "금리인상", "고용", "gdp",
)


def _finance_score(headline: Headline) -> int:
    blob = ("%s %s" % (headline.title, headline.summary)).lower()
    return sum(1 for key in _HINTS if key in blob)


def pick_headline(cfg: dict) -> Headline:
    feeds = cfg.get("rss") or []
    claimed = claimed_hashes()
    unused = [h for h in collect(feeds) if h.hash not in claimed]
    if not unused:
        raise SystemExit("쓸 헤드라인 없음 (RSS 실패이거나 전부 사용함)")
    hour = datetime.now().hour
    prefer = ("hankyung", "mk") if hour < 12 else ("reuters", "cnbc")
    ranked = [h for h in unused if _finance_score(h) > 0] or unused
    for item in ranked:
        if any(item.source.startswith(p) for p in prefer):
            return item
    return ranked[0]


def write_job(headline: Headline, channel: str = DEFAULT_CHANNEL) -> Path:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    job = channel_dir(channel) / ("%s-%s" % (stamp, slugify(headline.title)))
    job.mkdir(parents=True, exist_ok=True)
    (job / "headline.json").write_text(
        json.dumps(headline.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return job
