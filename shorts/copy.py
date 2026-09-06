from __future__ import annotations

import re

from shorts.models import ANATOMY_LOCK

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
CHANNEL_TAG_WORDS = frozenset({"돈이웃", "쇼츠", "shorts", "Shorts"})
REQUIRED_TAGS = ()
FORMAL_END = ("입니다", "습니다", "나왔습니다", "것입니다")
_HOOK_END = ("요", "다", "죠", "네요", "예요", "이에요")
_STAKE = (
    "내 ",
    "내가",
    "나의",
    "우리",
    "월급",
    "이자",
    "대출",
    "연금",
    "건보",
    "내돈",
    "전세",
    "월세",
    "부모",
    "아버지",
    "아빠",
    "엄마",
    "증여",
    "한도",
    "통장",
)
_HOUSE_TITLE = (
    "부모",
    "아버지",
    "아빠",
    "엄마",
    "전세",
    "월세",
    "증여",
    "차용",
    "무이자",
    "한도",
    "건보",
    "연금",
    "월급",
    "이자",
    "보증",
    "통장",
    "이체",
    "합산",
    "내 ",
    "우리",
)
_TITLE_OPINION = ("말지", "살지 말", "팔면", "어디 맡")
_YOUTH_COHORT = re.compile(r"2030(?!년)|(?<![가-힣A-Za-z])mz(?![가-힣A-Za-z])|엠지|청년층", re.I)
_INDEX_RETURN = ("코스피", "코스닥", "나스닥", "다우", "닛케이", "따라가")
_PRICE_NEWS = ("전셋값", "집값", "시세", "2년 새")
_PRICE_STAKE = ("한도", "세금", "이체", "월세", "무이자", "합산", "증여", "종부세")
_RATE_ONLY = re.compile(r"연\s*\d+(?:\.\d+)?\s*%")
_RATE_PRODUCT = ("적금", "예금", "주담대", "신용대출")
_RATE_STAKE = ("세금", "이체", "월세", "증여", "무이자", "합산", "종부세")
_WORKPLACE = ("육아휴직",)
_LIMIT_RESULT = (
    "세금",
    "소멸",
    "사라",
    "합산",
    "이체",
    "증여",
    "무이자",
    "종부세",
    "월세",
    "꺼내",
    "인출",
    "동결",
)
_LIMIT_COMPARE = re.compile(r"\d+(?:\.\d+)?\s*만(?:\s*원)?.{0,12}\d+(?:\.\d+)?\s*만")
_PENSION_DOUBLE = re.compile(r"두\s*배|2배|200\s*%")
_MIDPAY = ("중도금", "분양", "입주")
_MIDPAY_STAKE = ("전세", "월세", "통장", "꺼내", "인출", "증여", "차용")
_JEONSE_YIELD_VERB = ("맡기면", "맡기고", "예치", "묶어", "묶이면", "넣으면")
_JEONSE_YIELD_STAKE = ("부모", "한도", "꺼내", "인출", "증여", "무이자", "차용")
_FAMILY_PENSION = ("가족", "유족", "분할연금", "분할 연금", "가급", "부양", "배우자")
_NPS_ADDON = ("국민연금", "노령연금", "기초연금", "가급")
_NPS_AMOUNT = re.compile(r"(?:연|월)\s*\d+(?:\.\d+)?\s*만")
_PENSION_STAKE = (
    "한도",
    "통장",
    "꺼내",
    "인출",
    "세금",
    "합산",
    "건보",
    "피부양자",
    "소멸",
    "이체",
    "증여",
    "무이자",
)
_MONEY_EOK = re.compile(r"\d+(?:\.\d+)?\s*억(?:\s*\d+(?:\.\d+)?\s*만)?")
_MONEY_MAN_WON = re.compile(r"\d+(?:\.\d+)?\s*만\s*원")
_MONEY_WON = re.compile(r"\d+(?:\.\d+)?\s*원")
_MONEY_PCT = re.compile(r"\d+(?:\.\d+)?\s*%")
_MONTH_INTEREST = re.compile(r"(?:한\s*달|월)\s*\d+(?:\.\d+)?\s*만")
_YEAR_MAN = re.compile(r"연\s*\d+(?:\.\d+)?\s*만")
_NATION_JO = re.compile(r"\d+(?:\.\d+)?\s*조")
_MAN_AMOUNT = re.compile(r"(\d+(?:\.\d+)?)\s*만")
_TAX_RATE_WORD = ("세금", "세율", "양도세", "증여세", "종부세", "소득세", "퇴직소득세")
_NOT_MONEY_MAN = re.compile(r"\d+(?:\.\d+)?\s*만\s*(?:명|가구|채|세대|건)")
_PCT_STAKE = ("세금", "한도", "건보", "증여", "이체", "통장", "연금")
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
_TITLE_NUM = re.compile(r"\d+(?:\.\d+)?")
_STORY_MOOD = (
    "걸어가요",
    "걸어요",
    "올려다봐요",
    "불빛만",
    "창밖",
    "골목을",
    "벤치에",
    "산책을",
    "바라봐요",
    "들고 걸어",
    "하루를",
    "마을을 걸",
    "골목을 걸",
    "창을 봐요",
    "창가에",
    "내려가요",
    "서 있어요",
    "뛰어가요",
)
_MESSAGE = (
    "깎",
    "삭감",
    "인상",
    "인하",
    "줄어",
    "늘어",
    "늘었",
    "늘어요",
    "더 늘",
    "뛰",
    "오르",
    "올랐",
    "더 내",
    "더 붙",
    "못 ",
    "날아",
    "없어",
    "부족",
    "부담",
    "위험",
    "폭탄",
    "고갈",
    "체납",
    "연체",
    "빚",
    "월급",
    "이자",
    "대출",
    "연금",
    "전세",
    "건보",
    "내 ",
)


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


def _norm_hashtag(tag: str) -> str:
    raw = (tag or "").strip()
    if raw.lower() == "#shorts":
        return "#shorts"
    return raw


def topic_words(script) -> list:
    out = []

    def add(raw: str) -> None:
        word = str(raw or "").strip().lstrip("#")
        if not word or word in CHANNEL_TAG_WORDS or word in out:
            return
        out.append(word)

    for raw in getattr(script, "tags", None) or []:
        add(raw)
    for raw in parse_hashtags(getattr(script, "hashtags", "") or ""):
        add(_norm_hashtag(raw))
    return out


def studio_hashtags(script) -> str:
    words = []
    for raw in parse_hashtags(getattr(script, "hashtags", "") or ""):
        word = _norm_hashtag(raw).lstrip("#")
        if word and word not in CHANNEL_TAG_WORDS and word not in words:
            words.append(word)
    if len(words) < 5:
        for word in topic_words(script):
            if word not in words:
                words.append(word)
            if len(words) >= 5:
                break
    return " ".join("#" + w for w in words[:9])


def studio_tags(script) -> list:
    return topic_words(script)[:20]


def missing_required_hashtags(text: str) -> list:
    found = []
    for raw in parse_hashtags(text):
        word = _norm_hashtag(raw).lstrip("#")
        if word and word not in CHANNEL_TAG_WORDS and word not in found:
            found.append(word)
    if len(found) < 3:
        return ["주제"]
    return []


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


def title_has_money(title: str) -> bool:
    """제목에 억, 만 원, 원, 또는 세금·한도 %가 있어야 한다. 만 명·연 N%·세율 %·조만으로는 안 된다."""
    text = title or ""
    if _NOT_MONEY_MAN.search(text):
        text = _NOT_MONEY_MAN.sub(" ", text)
    if _MONEY_EOK.search(text) or _MONEY_MAN_WON.search(text) or _MONEY_WON.search(text):
        return True
    if _MONEY_PCT.search(text) and any(word in text for word in _PCT_STAKE):
        return True
    return False


def title_is_opinion(title: str) -> bool:
    return any(phrase in (title or "") for phrase in _TITLE_OPINION)


def title_is_youth(title: str) -> bool:
    return bool(_YOUTH_COHORT.search(title or ""))


def title_is_index(title: str) -> bool:
    """코스피 56%처럼 지수 수익률. 세금·한도 %가 아니다."""
    return any(word in (title or "") for word in _INDEX_RETURN)


def title_is_price_news(title: str) -> bool:
    """전셋값 2년 새 7800만처럼 시세 뉴스. 한도·세금·월세 결과가 없으면 실패다."""
    text = title or ""
    if not any(word in text for word in _PRICE_NEWS):
        return False
    if any(word in text for word in _PRICE_STAKE):
        return False
    return True


def title_is_rate_promo(title: str) -> bool:
    """적금 연 12%·적금 10% vs 예금 3.3%처럼 금리 상품. 연이 없어도 %면 같다. 세금·월세 결과가 아니면 실패다."""
    text = title or ""
    if not (_RATE_ONLY.search(text) or _MONEY_PCT.search(text)):
        return False
    if not any(word in text for word in _RATE_PRODUCT):
        return False
    if any(word in text for word in _RATE_STAKE):
        return False
    return True


def title_is_workplace(title: str) -> bool:
    """육아휴직급여 0원처럼 직장 복지. 통장·한도·월세가 아니다."""
    return any(word in (title or "") for word in _WORKPLACE)


def title_is_bare_limit(title: str) -> bool:
    """통장 한도 월 50만처럼 한도만 있고 세금·소멸·합산·비교·인출 제한이 없다."""
    text = title or ""
    if "한도" not in text:
        return False
    if any(word in text for word in _LIMIT_RESULT):
        return False
    if _LIMIT_COMPARE.search(text):
        return False
    return True


def title_is_pension_double(title: str) -> bool:
    """국민연금 200%·두 배처럼 조회는 와도 이탈이 큰 훅."""
    text = title or ""
    if "연금" not in text:
        return False
    return bool(_PENSION_DOUBLE.search(text))


def title_is_bare_mortgage(title: str) -> bool:
    """주담대 2억 다 갚아처럼 원금만 있고 이자 만 원이 없다."""
    text = title or ""
    if not any(word in text for word in ("주담대", "주택담보")):
        return False
    if "이자" in text and (
        _MONEY_MAN_WON.search(text) or re.search(r"\d+(?:\.\d+)?\s*만", text)
    ):
        return False
    return True


def title_is_month_interest(title: str) -> bool:
    """3억 주담대 이자 한 달 200만처럼 월 원리금. 억 + 연 만 원이 아니다."""
    text = title or ""
    if not any(word in text for word in ("주담대", "주택담보")):
        return False
    if "이자" not in text:
        return False
    if not _MONTH_INTEREST.search(text):
        return False
    if _YEAR_MAN.search(text):
        return False
    return True


def title_is_midpay(title: str) -> bool:
    """중도금 무이자처럼 분양·입주 상품. 전세·통장·못 꺼내가 아니다."""
    text = title or ""
    if not any(word in text for word in _MIDPAY):
        return False
    if any(word in text for word in _MIDPAY_STAKE):
        return False
    return True


def title_is_tax_rate(title: str) -> bool:
    """IRP 16.5% 세금처럼 세율 비교. 억/만 원 세금이 아니다."""
    text = title or ""
    if not _MONEY_PCT.search(text):
        return False
    if not any(word in text for word in _TAX_RATE_WORD):
        return False
    if _MONEY_EOK.search(text) or _MONEY_MAN_WON.search(text):
        return False
    return True


def title_is_nation_jo(title: str) -> bool:
    """퇴직연금 500조처럼 국가 통계. 억/만 원 한도가 아니다."""
    return bool(_NATION_JO.search(title or ""))


def title_is_health_depend(title: str) -> bool:
    """건보 피부양자 탈락처럼 자격. 통장·한도·못 꺼내·억/만 원 세금이 아니다."""
    text = title or ""
    depend = "피부양자" in text
    drop = "건보" in text and "탈락" in text
    if not (depend or drop):
        return False
    if any(word in text for word in ("통장", "한도", "꺼내", "인출")):
        return False
    if "세금" in text and (_MONEY_EOK.search(text) or _MONEY_MAN_WON.search(text)):
        return False
    return True


_ACCOUNT_CRIME = ("범죄", "대포", "사기")


def title_is_account_crime(title: str) -> bool:
    """통장 넘기면 범죄처럼 대포·사기. 세금·한도·못 꺼내가 아니다."""
    text = title or ""
    if "통장" not in text:
        return False
    if not any(word in text for word in _ACCOUNT_CRIME):
        return False
    if any(word in text for word in ("세금", "한도", "꺼내", "인출", "소멸", "합산")):
        return False
    return True


def title_is_tiny_rent(title: str) -> bool:
    """전세 3만·월세 5만처럼 가구 수/10만 미만. 74만→53만 월세 비교가 아니다."""
    text = title or ""
    if not any(word in text for word in ("전세", "월세")):
        return False
    if _MONEY_EOK.search(text):
        return False
    mans = [float(n) for n in _MAN_AMOUNT.findall(text)]
    if not mans:
        return False
    return all(n < 10 for n in mans)


def title_is_jeonse_yield(title: str) -> bool:
    """전세금 2억 맡기면 월 73만처럼 운용 수익 환산. 월세 비교·부모 한도가 아니다."""
    text = title or ""
    if "전세" not in text:
        return False
    if not any(word in text for word in _JEONSE_YIELD_VERB):
        return False
    if not re.search(r"월(?:세)?\s*\d+", text):
        return False
    if _LIMIT_COMPARE.search(text):
        return False
    if any(word in text for word in _JEONSE_YIELD_STAKE):
        return False
    return True


def title_is_family_pension(title: str) -> bool:
    """국민연금 가족 연 70만·가급·배우자처럼 가족·유족 급여. 한도·통장·세금이 아니다."""
    text = title or ""
    if "연금" not in text and "가급" not in text:
        return False
    family = any(word in text for word in _FAMILY_PENSION)
    addon = any(word in text for word in _NPS_ADDON) and bool(_NPS_AMOUNT.search(text))
    if not (family or addon):
        return False
    if any(word in text for word in _PENSION_STAKE):
        return False
    return True


def title_is_account_rate(title: str) -> bool:
    """통장 이율·이체 %·전세 통장 연%처럼 %만 있고 억·이자 만 원·못 꺼내가 없다."""
    text = title or ""
    rate_word = any(word in text for word in ("이율", "금리", "세율", "잔이자", "이체"))
    tax_pct = bool(re.search(r"세\s*\d+(?:\.\d+)?\s*%", text))
    year_pct_on_account = bool(_RATE_ONLY.search(text)) and any(
        word in text for word in ("통장", "전세", "예금")
    )
    yoy_pct_on_account = bool(
        re.search(r"(?:1년|작년|전년).{0,8}\d+(?:\.\d+)?\s*%", text)
    ) and any(word in text for word in ("통장", "이체", "예금"))
    if not (rate_word or tax_pct or year_pct_on_account or yoy_pct_on_account):
        return False
    if not _MONEY_PCT.search(text):
        return False
    if _MONEY_EOK.search(text) or _MONEY_MAN_WON.search(text):
        return False
    if "이자" in text and (
        _MONEY_MAN_WON.search(text) or re.search(r"\d+(?:\.\d+)?\s*만", text)
    ):
        return False
    if any(word in text for word in ("꺼내", "인출", "소멸", "합산")):
        return False
    return True


def title_numbers(title: str) -> list:
    return _TITLE_NUM.findall(title or "")


def has_message(text: str) -> bool:
    blob = text or ""
    if _DIGIT.search(blob):
        return True
    return any(token in blob for token in _MESSAGE)


def story_mood(text: str) -> str:
    blob = text or ""
    for phrase in _STORY_MOOD:
        if phrase in blob:
            return phrase
    return ""


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


_YOUNG_FACE = (
    "child",
    "teen",
    "20s",
    "30s",
    "young woman",
    "young man",
    "youthful",
    "little girl",
    "little boy",
)
_SENIOR_FACE = (
    "60s",
    "70s",
    "80s",
    "late-60",
    "late 60",
    "elderly",
    "silver-haired",
    "silver hair",
    "white-haired",
)
_AGE_DRIFT = (
    "becomes younger",
    "becomes older",
    "de-age",
    "deaged",
    "younger version",
    "older version",
    "ages into",
    "suddenly young",
    "suddenly old",
)


def style_anchor(script) -> str:
    style = getattr(script, "style", None)
    return (getattr(style, "anchor", None) or "").strip()


def style_face(script) -> str:
    style = getattr(script, "style", None)
    return (getattr(style, "face", None) or "").strip()


def style_wardrobe(script) -> str:
    style = getattr(script, "style", None)
    return (getattr(style, "wardrobe", None) or "").strip()


def _scene_prompts(scene) -> list:
    prompts = [b.image_prompt for b in (getattr(scene, "beats", None) or []) if getattr(b, "image_prompt", "")]
    if prompts:
        return prompts
    if getattr(scene, "image_prompt", ""):
        return [scene.image_prompt]
    return []


def age_band(text: str) -> str:
    blob = (text or "").lower()
    young = any(mark in blob for mark in _YOUNG_FACE)
    senior = any(mark in blob for mark in _SENIOR_FACE)
    if young and senior:
        return "mixed"
    if young:
        return "young"
    if senior:
        return "senior"
    return ""


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
    if not title_has_money(title):
        errors.append("제목에 억·만 원·세금% 금액이 없음")
    if title_is_opinion(title):
        errors.append("제목이 팔지말지 의견. 한도·세금 결과로")
    if title_is_youth(title):
        errors.append("제목이 2030·MZ 타깃. 시니어 한도로")
    if title_is_index(title):
        errors.append("제목이 코스피·지수 수익률. 한도·세금 결과로")
    if title_is_price_news(title):
        errors.append("제목이 전셋값·시세 뉴스. 한도·세금·월세 결과로")
    if title_is_rate_promo(title):
        errors.append("제목이 적금·대출 연%. 한도·세금·월세 결과로")
    if title_is_workplace(title):
        errors.append("제목이 육아휴직 직장복지. 통장·한도·월세로")
    if title_is_bare_limit(title):
        errors.append("제목이 한도만. 세금·소멸·합산·비교·인출 결과로")
    if title_is_pension_double(title):
        errors.append("제목이 연금 두 배. 한도·세금·이자 만 원으로")
    if title_is_bare_mortgage(title):
        errors.append("제목이 주담대 원금만. 억 원금 + 이자 만 원으로")
    if title_is_month_interest(title):
        errors.append("제목이 주담대 한 달 이자. 억 원금 + 연 만 원으로")
    if title_is_account_rate(title):
        errors.append("제목이 통장 이율·이체 %·전세 연%. 억 + 못 꺼내·이자 만 원으로")
    if title_is_midpay(title):
        errors.append("제목이 중도금·분양 상품. 전세 무이자·주담대 이자 만 원으로")
    if title_is_family_pension(title):
        errors.append("제목이 국민연금 가족·유족·가급. 한도·통장·세금·못 꺼내로")
    if title_is_jeonse_yield(title):
        errors.append("제목이 전세금 맡기면 월 환산. 월세 비교·부모 한도로")
    if title_is_tax_rate(title):
        errors.append("제목이 세금 세율 %. 억/만 원 세금으로")
    if title_is_nation_jo(title):
        errors.append("제목이 국가 조 단위. 억/만 원 한도로")
    if title_is_health_depend(title):
        errors.append("제목이 건보 피부양자 탈락. 통장·한도·못 꺼내·억/만 원 세금으로")
    if title_is_tiny_rent(title):
        errors.append("제목이 전세·월세 10만 미만·가구 수. 74만→53만 월세 비교로")
    if title_is_account_crime(title):
        errors.append("제목이 통장 범죄·대포. 세금·한도·못 꺼내로")
    banned = _hit_banned(title)
    if banned:
        errors.append("제목 금지어: %s" % banned)
    topics = topic_words(script)
    if topics and not any(word in title for word in topics):
        errors.append("제목에 주제가 안 보임")
    if not any(word in title for word in _HOUSE_TITLE):
        errors.append("제목에 내 돈 상황(전세·부모·아버지·통장·이자·한도)이 없음")

    body = description_body(script.description)
    if len(body) < 40:
        errors.append("설명 본문이 짧음")
    if body.splitlines()[0].strip() == title if body else False:
        errors.append("설명 첫 줄이 제목 복붙")
    banned = _hit_banned(body)
    if banned:
        errors.append("설명 금지어: %s" % banned)
    sents = [p for p in re.split(r"[.!?。]\s*", body) if p.strip()]
    if len(sents) < 2:
        errors.append("설명은 완결 문장 2개 이상")
    formal_desc = sum(1 for line in sents if _ending(line) == "formal")
    if formal_desc >= 2:
        errors.append("설명에 습니다/입니다가 너무 많음")
    lead = body[:200]
    hits = [word for word in topics if word in lead]
    if topics and len(hits) < min(2, len(topics)):
        errors.append("설명 앞 200자에 주제 키워드 필요")

    tags = parse_hashtags(script.hashtags)
    if any(_norm_hashtag(t).lstrip("#") in CHANNEL_TAG_WORDS for t in tags):
        errors.append("채널·쇼츠 해시태그 금지")
    if not (5 <= len(tags) <= 9):
        errors.append("해시태그는 주제만 5~9개")
    topic = [t for t in tags if t.lstrip("#") not in GENERIC_TAGS]
    if len(topic) < 2:
        errors.append("주제 해시태그 2개 이상")
    raw_tags = [str(t).strip().lstrip("#") for t in (script.tags or []) if str(t).strip()]
    if any(t in CHANNEL_TAG_WORDS for t in raw_tags):
        errors.append("태그에 채널·쇼츠 금지")
    if len(raw_tags) < 10:
        errors.append("태그는 10개 이상")

    captions = _captions(script)
    if not captions:
        errors.append("captions 필요")
    anchor = style_anchor(script)
    face = style_face(script)
    wardrobe = style_wardrobe(script)
    if len(anchor) < 24:
        errors.append("style.anchor 필요")
    if len(face) < 24:
        errors.append("style.face 필요")
    if len(wardrobe) < 16:
        errors.append("style.wardrobe 필요")
    bands = set()
    if age_band(face) == "mixed":
        errors.append("style.face 나이가 섞여 있음")
    elif age_band(face):
        bands.add(age_band(face))
    for i, scene in enumerate(script.scenes, 1):
        caps = [c for c in (scene.captions or []) if str(c).strip()]
        if len(caps) < 2:
            errors.append("scenes[%d] captions 2개 이상" % i)
        blob = " ".join([scene.text] + caps)
        banned = _hit_banned(blob)
        if banned:
            errors.append("scenes[%d] 금지어: %s" % (i, banned))
        prompts = _scene_prompts(scene)
        if not prompts:
            errors.append("scenes[%d] beats 필요" % i)
        for prompt in prompts:
            if _hit_photo(prompt):
                errors.append("scenes[%d] 실사 프롬프트 금지" % i)
            if _hit_manga(prompt):
                errors.append("scenes[%d] 망가/만화체 금지" % i)
            if prompt and not _has_style_need(prompt):
                errors.append("scenes[%d] 장편 애니 화풍 단어 필요" % i)
            if anchor and anchor not in prompt:
                errors.append("scenes[%d] 프롬프트에 style.anchor 없음" % i)
            if face and face not in prompt:
                errors.append("scenes[%d] 프롬프트에 style.face 없음" % i)
            if wardrobe and wardrobe not in prompt:
                errors.append("scenes[%d] 프롬프트에 style.wardrobe 없음" % i)
            if ANATOMY_LOCK not in prompt:
                errors.append("scenes[%d] 해부 고정 없음" % i)
            if any(mark in prompt.lower() for mark in _AGE_DRIFT):
                errors.append("scenes[%d] 얼굴 나이 변경 금지" % i)
            band = age_band(prompt)
            if band == "mixed":
                errors.append("scenes[%d] 얼굴 나이가 한 장면에서 섞임" % i)
            elif band:
                bands.add(band)
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
        title_nums = title_numbers(title)
        if title_nums and not any(num in captions[0] for num in title_nums):
            errors.append("첫 자막에 제목 숫자가 없음")
        if not has_personal_stake(captions[0]):
            errors.append("첫 자막에 내 돈(전세·부모·아버지·통장·한도)이 없음")
        if _ending(captions[0]) == "formal":
            errors.append("첫 자막을 습니다로 끝내지 말 것")
        formal_n = sum(1 for c in captions if _ending(c) == "formal")
        if formal_n > 1:
            errors.append("습니다/입니다 자막이 %d개. 1개 이하" % formal_n)
        last = script.scenes[-1]
        stake_blob = " ".join([last.text] + [c for c in (last.captions or []) if str(c).strip()])
        if not has_personal_stake(stake_blob):
            errors.append("마지막 장면은 내 돈(월급·이자·대출·연금)으로 끝내라")
        if len(bands) > 1:
            errors.append("얼굴 나이가 장면마다 다름. style.face로 고정하라")
        for cap in captions:
            mood = story_mood(cap)
            if mood:
                errors.append("자막이 스토리 정서: %s" % cap)
        for num in title_numbers(title):
            if num not in "".join(captions):
                errors.append("제목 숫자 %s가 자막에 없음" % num)
        scored = sum(1 for cap in captions if has_message(cap))
        need = max(4, (len(captions) + 1) // 2)
        if scored < need:
            errors.append("자막이 분위기만 있고 사실·공포가 부족")
        for i, scene in enumerate(script.scenes, 1):
            caps = [c for c in (scene.captions or []) if str(c).strip()]
            if caps and not any(has_message(c) for c in caps):
                errors.append("scenes[%d] 자막에 숫자·위험·내 돈이 없음" % i)

    if errors:
        raise ValueError("script.json 카피: " + "; ".join(errors))
