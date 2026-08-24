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
from shorts.copy import (
    title_is_bare_limit,
    title_is_pension_double,
    title_is_rate_promo,
    title_is_workplace,
)
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
    "이자", "주담대",
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


_VIRAL = (
    "깎", "삭감", "인상", "인하", "폭탄", "미납", "체납", "고갈",
    "동결", "지급액", "보험료", "연금액", "폐지", "중단",
    "증여", "차용", "무이자", "한도", "부모",
    "꺼내", "인출",
)
_HOUSE = (
    "부모", "아버지", "아빠", "엄마", "차용", "무이자", "한도", "증여세", "차용증",
    "전세금", "건보료", "지급액", "가족이체",
    "통장", "이체", "예금보호", "isa", "주택연금", "피부양자", "합산",
    "월세", "이자", "꺼내", "인출", "상속예금",
)
_WEAK_PLACE = ("은평", "강남구", "마포", "분당", "노원", "송파", "강북")
_WEAK_YOUTH = ("2030", "mz", "엠지", "청년층")
_MARKET_INDEX = ("코스피", "코스닥", "나스닥", "다우", "닛케이", "따라가")
_PRICE_NEWS = ("전셋값", "집값", "시세", "2년 새")
_PRICE_STAKE = ("한도", "세금", "이체", "월세", "무이자", "합산", "증여", "종부세")
_NATION_JO = re.compile(r"\d+\s*조")
_RATE_ONLY = re.compile(r"연\s*\d+(?:\.\d+)?\s*%")
_HOOK_CORE = (
    "전세금", "예금보호", "증여세", "차용증", "무이자", "피부양자", "가족이체", "종부세",
    "월세", "한도", "이자", "통장",
)
_HOOK_AMOUNT = re.compile(r"(\d+(?:\.\d+)?)\s*(억|만|원)")
_ISA_TOKEN = re.compile(r"(?<![a-z])isa(?![a-z])", re.I)


def _rejected_house(title: str, blob: str) -> bool:
    return (
        title_is_rate_promo(title)
        or title_is_rate_promo(blob)
        or title_is_workplace(title)
        or title_is_workplace(blob)
        or title_is_bare_limit(title)
        or title_is_bare_limit(blob)
        or title_is_pension_double(title)
        or title_is_pension_double(blob)
    )


def _house_score(headline: Headline) -> int:
    blob = _blob(headline)
    title = headline.title or ""
    if _rejected_house(title, blob):
        return 0
    return _count_hints(blob, _HOUSE)


def _weak_news_penalty(headline: Headline) -> int:
    """지역 이전·2030 타깃·국가 조·연 N% 상품·육아휴직·한도만·연금 두 배·지수·전셋값 시세는 조회가 안 남는다. 통장·한도가 있으면 지역·조는 깎지 않는다."""
    blob = _blob(headline)
    title = headline.title or ""
    n = 0
    if _house_score(headline) == 0:
        if any(place in blob for place in _WEAK_PLACE):
            n += 1
        if any(youth in blob for youth in _WEAK_YOUTH):
            n += 1
        if _NATION_JO.search(title):
            n += 1
        if _RATE_ONLY.search(title) and not any(
            word in blob for word in ("세금", "한도", "통장", "이체", "만 원", "만원")
        ):
            n += 1
    if title_is_rate_promo(title) or title_is_rate_promo(blob):
        n += 1
    if title_is_workplace(title) or title_is_workplace(blob):
        n += 1
    if title_is_bare_limit(title) or title_is_bare_limit(blob):
        n += 1
    if title_is_pension_double(title) or title_is_pension_double(blob):
        n += 1
    if any(word in blob for word in _MARKET_INDEX):
        n += 1
    if any(word in title for word in _PRICE_NEWS) and not any(
        word in blob for word in _PRICE_STAKE
    ):
        n += 1
    return n


def _hook_cores(text: str) -> set:
    blob = text or ""
    cores = {key for key in _HOOK_CORE if key in blob}
    if _ISA_TOKEN.search(blob):
        cores.add("isa")
    return cores


def _hook_amounts(text: str) -> set:
    return set(_HOOK_AMOUNT.findall(text or ""))


def _amount_near(left: set, right: set) -> bool:
    """같은 단위면 만은 ±5까지 재탕. 74만과 73만은 같다."""
    for na, ua in left:
        for nb, ub in right:
            if ua != ub:
                continue
            try:
                fa, fb = float(na), float(nb)
            except ValueError:
                continue
            if fa == fb:
                return True
            if ua == "만" and abs(fa - fb) <= 5:
                return True
    return False


def _same_hook(a: str, b: str) -> bool:
    """같은 통장·한도·월세·이자 주제 + 같은(또는 가까운 만) 숫자는 각도만 바꿔도 재탕이다. ISA든 신용대출이든 2000만, 아버지든 엄마든 통장 4억이면 같다."""
    cores = _hook_cores(a) & _hook_cores(b)
    if not cores:
        return False
    return _amount_near(_hook_amounts(a), _hook_amounts(b))


def _viral_score(headline: Headline) -> int:
    blob = _blob(headline)
    n = 1 if re.search(r"\d", headline.title) else 0
    return n + _count_hints(blob, _VIRAL)


def _too_similar(headline: Headline, used_titles: list) -> bool:
    title = headline.title
    return any(
        topic_overlap(title, used) >= 3 or _same_hook(title, used) for used in used_titles
    )


def choose_headline(
    unused: list,
    now: datetime | None = None,
    used_titles: list | None = None,
) -> Headline:
    """미사용 헤드라인 중 통장·한도·이체·월세·이자 만 원·아버지 통장 억+못 꺼내 → 시니어 관심 → 지역/2030/조/연%상품/육아휴직/한도만/연금두배/코스피/시세 감점 → 숫자 훅 → 금융 → 안 겹침 → 매체 → 최신 순."""
    if not unused:
        raise SystemExit("쓸 헤드라인 없음 (RSS 실패이거나 전부 사용함)")
    prefer = _preferred_sources(now)
    used = [t for t in (used_titles or []) if t]
    fresh = [h for h in unused if not _too_similar(h, used)] if used else unused
    pool_src = fresh or unused
    senior_hits = [
        h
        for h in pool_src
        if _senior_score(h) > 0 and not _rejected_house(h.title or "", _blob(h))
    ]
    finance_hits = [h for h in pool_src if _finance_score(h) > 0]
    pool = senior_hits or finance_hits or pool_src

    def sort_key(item: Headline):
        overlap = max((topic_overlap(item.title, t) for t in used), default=0)
        return (
            _house_score(item),
            _senior_score(item),
            -_weak_news_penalty(item),
            _viral_score(item),
            _finance_score(item),
            -overlap,
            _source_boost(item, prefer),
            _parse_date(item.published),
        )

    chosen = max(pool, key=sort_key)
    log.info(
        "선정 점수 house=%d senior=%d weak=%d viral=%d finance=%d overlap=%d [%s] %s",
        _house_score(chosen),
        _senior_score(chosen),
        _weak_news_penalty(chosen),
        _viral_score(chosen),
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
