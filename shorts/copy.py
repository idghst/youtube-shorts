from __future__ import annotations

import re

BANNED = (
    "알아보겠습니다",
    "살펴보겠습니다",
    "살펴볼 시점",
    "다시 한번 살펴",
    "다시 한번 정리",
    "다시 볼 시점",
    "핵심을 정리",
    "많은 분들이",
    "오늘 알아볼",
    "함께 알아",
    "함께 살펴",
    "알아보도록",
    "라는 표현입니다",
    "헤드라인에",
    "매수나 매도 신호",
    "목표가는 나오지",
    "목표가도 나오지",
    "정보 제공이 목적",
    "결론적으로",
    "정리하면",
    "첫째",
    "둘째",
    "셋째",
    "마지막으로",
)

GENERIC_TAGS = frozenset({"재테크", "경제", "쇼츠", "shorts", "돈이웃", "Shorts"})
REQUIRED_TAGS = ("#돈이웃", "#쇼츠", "#shorts")
FORMAL_END = ("입니다", "습니다", "나왔습니다", "것입니다")
_HOOK_END = ("요", "다", "죠", "네요", "예요", "이에요")
_STAKE = ("내 ", "내가", "나의", "우리", "월급", "이자", "대출", "연금", "건보", "내돈")
_PHOTO_MARK = (
    "photorealistic",
    "photoreal",
    "photograph",
    "cinematic photo",
    "cinematic still",
    "smartphone photo",
    "documentary still",
    "shot on 35mm",
    "worried korean senior",
)
_MANGA_MARK = (
    "manga",
    "manhwa",
    "chibi",
    "screentone",
    "speed lines",
    "comic panel",
)
_STYLE_NEED = (
    "painterly",
    "animated film",
    "theatrical animation",
    "luminous",
)
_PUNCT = " \t.!?…,~"
_HASH_LINE = re.compile(r"^(?:#\S+\s*)+$")
_DIGIT = re.compile(r"\d")


def description_body(text: str) -> str:
    lines = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            if lines and lines[-1]:
                lines.append("")
            continue
        if _HASH_LINE.match(line):
            continue
        if any(mark in line for mark in ("정보 제공이 목적", "투자 권유가 아니", "투자 손실에 대한 책임")):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def studio_title(title: str) -> str:
    cleaned = re.sub(r"\s*#\S+", "", title or "").strip()
    return cleaned[:100]


def parse_hashtags(text: str) -> list:
    return [p for p in (text or "").split() if p.startswith("#") and len(p) > 1]


def _strip_end(text: str) -> str:
    return (text or "").rstrip(_PUNCT)


def _ending(text: str) -> str:
    s = _strip_end(text)
    if s.endswith(FORMAL_END):
        return "formal"
    if s.endswith("다"):
        return "da"
    return "ok"


def is_hook(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    if s.endswith("?") or s.endswith("…") or s.endswith("..."):
        return True
    return not _strip_end(s).endswith(_HOOK_END)


def has_number_or_question(text: str) -> bool:
    s = text or ""
    return "?" in s or bool(_DIGIT.search(s))


def has_personal_stake(text: str) -> bool:
    return any(word in (text or "") for word in _STAKE)


def _hit_photo(text: str) -> bool:
    blob = (text or "").lower()
    return any(mark in blob for mark in _PHOTO_MARK)


def _hit_manga(text: str) -> bool:
    blob = (text or "").lower()
    return any(mark in blob for mark in _MANGA_MARK)


def _has_style_need(text: str) -> bool:
    blob = (text or "").lower()
    return any(mark in blob for mark in _STYLE_NEED)


def style_anchor(script) -> str:
    style = getattr(script, "style", None)
    return (getattr(style, "anchor", None) or "").strip()


def _hit_banned(text: str) -> str:
    for phrase in BANNED:
        if phrase in (text or ""):
            return phrase
    return ""


def _captions(script) -> list:
    out = []
    for scene in script.scenes:
        out.extend(c for c in (scene.captions or []) if str(c).strip())
    return out


def validate_script(script) -> None:
    errors = []
    title = (script.title or "").strip()
    if "#" in title:
        errors.append("제목에 해시태그 금지")
    if not (12 <= len(title) <= 42):
        errors.append("제목은 12~42자")
    if "입니다" in title or "습니다" in title or title.endswith("나왔습니다"):
        errors.append("제목에 입니다/습니다 금지")
    if not has_number_or_question(title):
        errors.append("제목에 숫자 또는 물음표 필요")
    banned = _hit_banned(title)
    if banned:
        errors.append("제목 금지어: %s" % banned)

    body = description_body(script.description)
    if len(body) < 24:
        errors.append("설명 본문이 짧음")
    if body.splitlines()[0].strip() == title if body else False:
        errors.append("설명 첫 줄이 제목 복붙")
    banned = _hit_banned(body)
    if banned:
        errors.append("설명 금지어: %s" % banned)
    formal_desc = sum(1 for line in re.split(r"[.!?。]\s*", body) if _ending(line) == "formal")
    if formal_desc >= 2:
        errors.append("설명에 습니다/입니다가 너무 많음")

    tags = parse_hashtags(script.hashtags)
    if not (5 <= len(tags) <= 10):
        errors.append("해시태그는 5~10개")
    missing = [t for t in REQUIRED_TAGS if t not in tags]
    if missing:
        errors.append("해시태그 필수: %s" % " ".join(missing))
    topic = [t for t in tags if t.lstrip("#") not in GENERIC_TAGS]
    if len(topic) < 2:
        errors.append("주제 해시태그 2개 이상")

    captions = _captions(script)
    if not captions:
        errors.append("captions 필요")
    anchor = style_anchor(script)
    if len(anchor) < 24:
        errors.append("style.anchor 필요")
    for i, scene in enumerate(script.scenes, 1):
        caps = [c for c in (scene.captions or []) if str(c).strip()]
        if len(caps) < 2:
            errors.append("scenes[%d] captions 2개 이상" % i)
        blob = " ".join([scene.text] + caps)
        banned = _hit_banned(blob)
        if banned:
            errors.append("scenes[%d] 금지어: %s" % (i, banned))
        prompt = scene.image_prompt or ""
        if _hit_photo(prompt):
            errors.append("scenes[%d] 실사 프롬프트 금지" % i)
        if _hit_manga(prompt):
            errors.append("scenes[%d] 망가/만화체 금지" % i)
        if prompt and not _has_style_need(prompt):
            errors.append("scenes[%d] 장편 애니 화풍 단어 필요" % i)
        if anchor and anchor not in prompt:
            errors.append("scenes[%d] 프롬프트에 style.anchor 없음" % i)
        for cap in caps:
            if len(cap) > 28:
                errors.append("자막이 김: %s" % cap[:20])
            if _ending(cap) == "da":
                errors.append("자막 ~다 체 금지: %s" % cap)

    if captions:
        if captions[0] == title:
            errors.append("첫 자막이 제목 복붙")
        if not is_hook(captions[0]):
            errors.append("첫 자막은 훅(질문·덜 끝난 말)")
        if _ending(captions[0]) == "formal":
            errors.append("첫 자막을 습니다로 끝내지 말 것")
        formal_n = sum(1 for c in captions if _ending(c) == "formal")
        if formal_n > 1:
            errors.append("습니다/입니다 자막이 %d개. 1개 이하" % formal_n)
        last = script.scenes[-1]
        stake_blob = " ".join([last.text] + [c for c in (last.captions or []) if str(c).strip()])
        if not has_personal_stake(stake_blob):
            errors.append("마지막 장면은 내 돈(월급·이자·대출·연금)으로 끝내라")

    if errors:
        raise ValueError("script.json 카피: " + "; ".join(errors))
