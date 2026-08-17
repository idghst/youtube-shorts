from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from shorts.config import DEFAULT_CHANNEL, OUT_DIR, channel_dir, ensure_dirs, youtube_channel_id
from shorts.models import Headline, slugify
from shorts.store import mark_used, recent_titles, try_claim, used_hashes

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


def claimed_hashes(channel: str, out_dir: Path | None = None, cfg: dict | None = None) -> set:
    hashes = used_hashes(channel, cfg=cfg)
    root = channel_dir(channel) if channel else (out_dir or OUT_DIR)
    if not root.is_dir():
        return hashes
    for path in root.glob("*/headline.json"):
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

# 돈이웃 시청층(시니어) 핵심. 점수가 금융 키워드·최신·매체보다 앞선다.
_SENIOR_CORE = (
    "연금", "은퇴", "노후", "고령", "시니어", "정년", "노령",
    "국민연금", "기초연금", "퇴직연금", "개인연금", "주택연금",
    "건강보험", "건보료", "의료비", "간병", "요양",
    "상속", "증여", "역모기지",
    "pension", "retirement", "annuity", "medicare", "medicaid",
    "social security", "nursing",
)

# 시니어가 자주 보는 재테크. 코어보다 낮게 가산.
_SENIOR_NEAR = (
    "예금", "적금", "예적금", "배당", "부동산", "전세", "종부세", "재산세",
    "irp", "공시가격", "공시지가",
    "dividend", "deposit",
)


def _blob(headline: Headline) -> str:
    return ("%s %s" % (headline.title, headline.summary)).lower()


def _count_hints(blob: str, keys: tuple) -> int:
    return sum(1 for key in keys if key in blob)


def _finance_score(headline: Headline) -> int:
    return _count_hints(_blob(headline), _HINTS)


def _senior_score(headline: Headline) -> int:
    blob = _blob(headline)
    return _count_hints(blob, _SENIOR_CORE) * 3 + _count_hints(blob, _SENIOR_NEAR)


def _preferred_sources(now: datetime | None = None) -> tuple:
    hour = (now or datetime.now()).hour
    return ("hankyung", "mk") if hour < 12 else ("reuters", "cnbc")


def _source_boost(headline: Headline, prefer: tuple) -> int:
    return 1 if any(headline.source.startswith(p) for p in prefer) else 0


_TOPIC_STOP = frozenset(
    "것 수 등 및 더 덜 첫 오늘 앞으로 단독 한경 매경 프리미엄 today 전망 보도 소식 것".split()
)


def topic_tokens(title: str) -> set:
    parts = re.findall(r"[가-힣A-Za-z0-9]+", (title or "").lower())
    return {p for p in parts if len(p) >= 2 and p not in _TOPIC_STOP}


def topic_overlap(a: str, b: str) -> int:
    return len(topic_tokens(a) & topic_tokens(b))


def recent_topics(channel: str, cfg: dict | None = None, out_dir: Path | None = None) -> list:
    titles = list(recent_titles(channel))
    root = Path(out_dir) / channel if out_dir else channel_dir(channel)
    if root.is_dir():
        for path in sorted(root.glob("*/headline.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            title = str(data.get("title") or "").strip()
            if title:
                titles.append(title)
    seen = set()
    out = []
    for title in titles:
        if title not in seen:
            seen.add(title)
            out.append(title)
    return out


def _too_similar(headline: Headline, used_titles: list) -> bool:
    return any(topic_overlap(headline.title, title) >= 3 for title in used_titles)


def choose_headline(
    unused: list,
    now: datetime | None = None,
    used_titles: list | None = None,
) -> Headline:
    """미사용 헤드라인 중 시니어 관심 → 금융 키워드 → 이전 주제와 안 겹침 → 시간대 매체 → 최신 순."""
    if not unused:
        raise SystemExit("쓸 헤드라인 없음 (RSS 실패이거나 전부 사용함)")
    prefer = _preferred_sources(now)
    used = [t for t in (used_titles or []) if t]
    fresh = [h for h in unused if not _too_similar(h, used)] if used else unused
    pool_src = fresh or unused
    senior_hits = [h for h in pool_src if _senior_score(h) > 0]
    finance_hits = [h for h in pool_src if _finance_score(h) > 0]
    pool = senior_hits or finance_hits or pool_src

    def sort_key(item: Headline):
        overlap = max((topic_overlap(item.title, t) for t in used), default=0)
        return (
            _senior_score(item),
            _finance_score(item),
            -overlap,
            _source_boost(item, prefer),
            _parse_date(item.published),
        )

    chosen = max(pool, key=sort_key)
    log.info(
        "선정 점수 senior=%d finance=%d overlap=%d [%s] %s",
        _senior_score(chosen),
        _finance_score(chosen),
        max((topic_overlap(chosen.title, t) for t in used), default=0),
        chosen.source,
        chosen.title,
    )
    return chosen


def pick_headline(cfg: dict, channel: str = DEFAULT_CHANNEL, now: datetime | None = None) -> Headline:
    feeds = cfg.get("rss") or []
    claimed = claimed_hashes(channel, cfg=cfg)
    unused = [h for h in collect(feeds) if h.hash not in claimed]
    return choose_headline(unused, now=now, used_titles=recent_topics(channel, cfg=cfg))


def pick_job(cfg: dict, channel: str = DEFAULT_CHANNEL, now: datetime | None = None) -> Path:
    """이전 주제를 보고 미사용 헤드라인을 고른 뒤 채널별로 Supabase에 선점한다."""
    feeds = cfg.get("rss") or []
    claimed = claimed_hashes(channel, cfg=cfg)
    used = recent_topics(channel, cfg=cfg)
    unused = [h for h in collect(feeds) if h.hash not in claimed]
    yt_id = youtube_channel_id(cfg, channel)
    while unused:
        headline = choose_headline(unused, now=now, used_titles=used)
        job = write_job(headline, channel, used_titles=used)
        if not try_claim(
            headline,
            channel=channel,
            job_path=str(job),
            youtube_channel_id=yt_id,
            cfg=cfg,
        ):
            log.info("다른 런이 이미 선점/업로드: [%s] %s", headline.source, headline.title)
            shutil.rmtree(job, ignore_errors=True)
            unused = [item for item in unused if item.hash != headline.hash]
            continue
        mark_used(
            headline,
            status="picked",
            channel=channel,
            job_path=str(job),
            youtube_channel_id=yt_id,
            cfg=cfg,
        )
        log.info("선점 [%s] %s", headline.source, headline.title)
        return job
    raise SystemExit("쓸 헤드라인 없음 (RSS 실패이거나 이 채널에 이미 올린 것)")


def write_job(
    headline: Headline,
    channel: str = DEFAULT_CHANNEL,
    used_titles: list | None = None,
) -> Path:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    job = channel_dir(channel) / ("%s-%s" % (stamp, slugify(headline.title)))
    job.mkdir(parents=True, exist_ok=True)
    (job / "headline.json").write_text(
        json.dumps(headline.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (job / "used-topics.json").write_text(
        json.dumps({"channel": channel, "titles": list(used_titles or [])}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return job
