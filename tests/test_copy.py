from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from shorts.copy import (
    description_body,
    studio_title,
    title_has_money,
    title_is_index,
    title_is_price_news,
    title_is_account_rate,
    title_is_bare_limit,
    title_is_bare_mortgage,
    title_is_family_pension,
    title_is_health_depend,
    title_is_account_crime,
    title_is_insure_product,
    title_is_tax_count,
    title_is_tiny_rent,
    title_is_jeonse_yield,
    title_is_midpay,
    title_is_month_interest,
    title_is_nation_jo,
    title_is_pension_double,
    title_is_rate_promo,
    title_is_tax_rate,
    title_is_workplace,
    validate_script,
)
from shorts.models import ANATOMY_LOCK, Beat, Scene, Script, Style, load_script

ANCHOR = (
    "the same silver-haired Korean woman in a cream cardigan, "
    "painterly animated film, luminous dusk sky"
)
FACE = (
    "same late-60s Korean woman, silver bob to the jaw, "
    "soft eye wrinkles, round cheeks, do not change age"
)
WARDROBE = "same cream cardigan over ivory blouse every beat"


def _prompt(beat: str) -> str:
    return (
        "%s. %s. %s. %s. %s Soft theatrical animation. "
        "Vertical 9:16, empty lower third."
        % (ANCHOR, FACE, WARDROBE, ANATOMY_LOCK, beat)
    )


def _beats(*actions: str) -> list:
    return [Beat(image_prompt=_prompt(a)) for a in actions]


def _scene(text: str, captions: list, *actions: str) -> Scene:
    return Scene(text, duration=3.0 * len(actions), captions=captions, beats=_beats(*actions))


def _ok(**overrides) -> Script:
    scenes = [
        _scene(
            "전세금을 부모에게 빌리면 한도가 있어요",
            ["무이자 2억까지라고요?", "전세금을 부모에게 빌리면"],
            "She reads an unmarked envelope by the window.",
            "She turns the envelope over with both hands.",
            "She looks out the dusk window, envelope at her chest.",
            "She steps back from the window, still holding the letter.",
        ),
        _scene(
            "차용증 없이 옮기면 증여세가 붙어요",
            ["차용증이 없으면 증여세예요", "한도를 넘기면 더 붙어요"],
            "She sits at the wooden table with the envelope.",
            "She opens the envelope with two hands.",
            "She reads the letter under the lamp.",
        ),
        _scene(
            "무이자로 빌려도 한도는 2억이에요",
            ["무이자여도 한도는 2억", "그냥 옮기면 세금이에요"],
            "She puts on the same cream cardigan at the door.",
            "She walks down wet dusk streets holding the letter.",
            "She pauses under a streetlamp, letter in one hand.",
        ),
        _scene(
            "통장만 옮기면 내 돈이 줄어요",
            ["통장만 옮기면 세금이에요", "한도가 바로 깎여요"],
            "She climbs the wet hillside path.",
            "City lights reflect on puddles as she pauses.",
            "She looks down at the town from the hill.",
        ),
        _scene(
            "내 전세금부터 한도를 봐야 해요",
            ["내 전세금 한도부터", "2억을 넘기면 흔들려요"],
            "She looks at the hillside town, one hand on her chest.",
            "Same face, same cardigan, dusk town behind her.",
            "She looks at the letter one last time.",
        ),
    ]
    data = dict(
        title="전세금 부모에게 빌리면, 무이자 2억?",
        description="전세금을 부모에게 빌리면 무이자 한도가 있어요. 차용증 없이 통장만 옮기면 증여세가 붙고, 한도는 2억까지예요.",
        tags=["전세금", "부모", "무이자", "증여세", "차용증", "한도", "전세", "가족이체", "통장", "증여"],
        hashtags="#전세금 #부모 #무이자 #증여세 #차용증",
        scenes=scenes,
        style=Style(anchor=ANCHOR, face=FACE, wardrobe=WARDROBE, mood="quiet dusk hillside town"),
    )
    data.update(overrides)
    return Script(**data)


class CopyValidateTests(unittest.TestCase):
    def test_ok_script_passes(self):
        validate_script(_ok())

    def test_rejects_formal_title_and_meta(self):
        script = _ok(title="전세금을 부모에게 빌리면 무이자 2억입니다")
        with self.assertRaises(ValueError) as ctx:
            validate_script(script)
        self.assertIn("입니다", str(ctx.exception))

    def test_rejects_hashtag_in_title(self):
        with self.assertRaises(ValueError):
            validate_script(_ok(title="전세금 부모 무이자 2억 #Shorts"))

    def test_rejects_copied_first_caption(self):
        scenes = _ok().scenes
        scenes[0].captions = ["전세금 부모에게 빌리면, 무이자 2억?", "한도가 더 문제예요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("첫 자막", str(ctx.exception))

    def test_rejects_banned_meta_caption(self):
        scenes = _ok().scenes
        scenes[2].captions = ["헤드라인에 숫자는 없습니다", "풀가동이라는 표현입니다"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("금지어", str(ctx.exception))

    def test_rejects_too_many_formal_endings(self):
        scenes = _ok().scenes
        for scene in scenes:
            scene.captions = [c.replace("요", "습니다") if c.endswith("요") else c + "입니다" for c in scene.captions]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("습니다", str(ctx.exception))

    def test_rejects_title_without_money_unit(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="전세금 부모에게 빌리면, 은평으로?"))
        self.assertIn("억", str(ctx.exception))

    def test_rejects_year_only_title_number(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="전세금 부모 2030, 은평으로?"))
        self.assertIn("억", str(ctx.exception))

    def test_rejects_opinion_title(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="전세금 부모 2억, 팔지 말지?"))
        self.assertIn("의견", str(ctx.exception))

    def test_rejects_sale_hypothesis_title(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 집 팔면 양도세, 2억이 9억?"))
        self.assertIn("의견", str(ctx.exception))

    def test_rejects_youth_cohort_title(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="전세난에 지친 2030, 은평으로 2억?"))
        self.assertIn("2030", str(ctx.exception))

    def test_rejects_man_myeong_as_money(self):
        self.assertFalse(title_has_money("2030년 국민연금 1000만 명, 내 금액부터"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="국민연금 1000만 명, 내 한도부터"))
        self.assertIn("억", str(ctx.exception))

    def test_rejects_man_without_won(self):
        self.assertFalse(title_has_money("전세 3만 줄고, 월세 5만이 늘면?"))
        self.assertFalse(title_has_money("변동 주담대 이자, 연 6%?"))
        self.assertTrue(title_has_money("전세금 부모에게 빌리면, 무이자 2억?"))
        self.assertTrue(title_has_money("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        self.assertTrue(title_has_money("IRP 깨면 16.5% 세금, 55세 연금은 3.3%"))
        self.assertTrue(title_has_money("전세금 부모에게 빌리면, 무이자는 2억1700만까지"))
        self.assertTrue(title_has_money("내 전세 월세, 74만 원이 53만?"))
        self.assertTrue(title_has_money("3억 주담대 이자, 한 달 200만 원?"))

    def test_rejects_index_return_title(self):
        self.assertTrue(title_is_index("내 퇴직연금, 코스피 56%를 못 따라가요?"))
        self.assertFalse(title_is_index("IRP 깨면 16.5% 세금, 55세 연금은 3.3%"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 퇴직연금, 코스피 56%를 못 따라가요?"))
        self.assertIn("코스피", str(ctx.exception))

    def test_rejects_jeonse_price_news_title(self):
        self.assertTrue(title_is_price_news("내 전셋값, 2년 새 7800만 원?"))
        self.assertFalse(title_is_price_news("내 전세 월세, 74만 원이 53만?"))
        self.assertFalse(title_is_price_news("전세금 부모에게 빌리면, 무이자 2억?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 전셋값, 2년 새 7800만 원?"))
        self.assertIn("시세", str(ctx.exception))

    def test_rejects_rate_promo_title(self):
        self.assertTrue(title_is_rate_promo("적금 한도 월 30만 원, 연 12%?"))
        self.assertTrue(title_is_rate_promo("변동 주담대 이자, 연 6%?"))
        self.assertTrue(title_is_rate_promo("적금 10%? 시중은행 예금은 3.3%"))
        self.assertTrue(title_is_rate_promo("적금 10%? 시중은행 예금은 3.3%, 내 통장"))
        self.assertFalse(title_is_rate_promo("IRP 깨면 16.5% 세금, 55세 연금은 3.3%"))
        self.assertFalse(title_is_rate_promo("내 전세 월세, 74만 원이 53만?"))
        self.assertFalse(title_is_rate_promo("5억 주담대 이자, 연 140만 원?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="적금 한도 월 30만 원, 연 12%?"))
        self.assertIn("연%", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="적금 10%? 시중은행 예금은 3.3%, 내 통장"))
        self.assertIn("적금", str(ctx.exception))

    def test_rejects_workplace_benefit_title(self):
        self.assertTrue(title_is_workplace("내 육아휴직급여, 확인서 없으면 0원?"))
        self.assertFalse(title_is_workplace("전세금 부모에게 빌리면, 무이자 2억?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 육아휴직급여, 확인서 없으면 0원?"))
        self.assertIn("육아", str(ctx.exception))

    def test_rejects_bare_limit_title(self):
        self.assertTrue(title_is_bare_limit("내 통장 한도, 월 50만 원?"))
        self.assertTrue(title_is_bare_limit("주부 신용대출, 한도 2000만 원?"))
        self.assertFalse(title_is_bare_limit("ISA 남은 한도 2000만 원, 내년에 사라지나"))
        self.assertFalse(title_is_bare_limit("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        self.assertFalse(title_is_bare_limit("전세금 부모에게 빌리면, 무이자 2억?"))
        self.assertFalse(title_is_bare_limit("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_bare_limit("아버지 통장 한도, 4억 못 꺼내?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 통장 한도, 월 50만 원?"))
        self.assertIn("한도", str(ctx.exception))

    def test_rejects_bare_mortgage_title(self):
        self.assertTrue(title_is_bare_mortgage("내 주담대 2억, 다음 달 다 갚아?"))
        self.assertTrue(title_is_bare_mortgage("주택담보대출 2억, 만기면 일시상환?"))
        self.assertFalse(title_is_bare_mortgage("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_bare_mortgage("3억 주담대 이자, 한 달 200만 원?"))
        self.assertFalse(title_is_bare_mortgage("전세금 부모에게 빌리면, 무이자 2억?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 주담대 2억, 다음 달 다 갚아?"))
        self.assertIn("주담대", str(ctx.exception))

    def test_rejects_month_interest_title(self):
        self.assertTrue(title_is_month_interest("3억 주담대 이자, 한 달 200만 원?"))
        self.assertTrue(title_is_month_interest("주담대 이자, 월 200만 원?"))
        self.assertTrue(title_is_month_interest("주택담보대출 이자, 한달 180만 원"))
        self.assertFalse(title_is_month_interest("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_month_interest("5억 주담대 이자, 연 140만·한 달 12만?"))
        self.assertFalse(title_is_month_interest("내 전세 월세, 74만 원이 53만?"))
        self.assertFalse(title_is_month_interest("아버지 통장 4억, 지금 못 꺼내?"))
        self.assertFalse(title_is_month_interest("내 주담대 2억, 다음 달 다 갚아?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="3억 주담대 이자, 한 달 200만 원?"))
        self.assertIn("한 달", str(ctx.exception))

    def test_rejects_pension_double_title(self):
        self.assertTrue(title_is_pension_double("국민연금 1개월 내고 2배, 연금액 200%?"))
        self.assertTrue(title_is_pension_double("부모 월 9만 원, 자녀 연금이 두 배?"))
        self.assertFalse(title_is_pension_double("IRP 깨면 16.5% 세금, 55세 연금은 3.3%"))
        self.assertFalse(title_is_pension_double("5억 주담대 이자, 연 140만 원?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="국민연금 1개월 내고 2배, 연금액 200%?"))
        self.assertIn("연금", str(ctx.exception))

    def test_rejects_account_rate_title(self):
        self.assertTrue(title_is_account_rate("내 통장 이율, 1년 세 30%?"))
        self.assertTrue(title_is_account_rate("예금 이율 3%, 내 통장부터"))
        self.assertTrue(title_is_account_rate("내 전세 통장, 묶이면 연 4.5%?"))
        self.assertTrue(title_is_account_rate("전세 보증금 잔이자, 연 3%?"))
        self.assertTrue(title_is_account_rate("내 통장 이체, 1년 새 30%?"))
        self.assertTrue(title_is_account_rate("통장 이체 증가, 작년보다 30%?"))
        self.assertFalse(title_is_account_rate("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_account_rate("아버지 통장 4억, 지금 못 꺼내?"))
        self.assertFalse(title_is_account_rate("IRP 깨면 16.5% 세금, 55세 연금은 3.3%"))
        self.assertFalse(title_is_account_rate("가족이체 2억, 증여세 10%?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 전세 통장, 묶이면 연 4.5%?"))
        self.assertIn("연%", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 통장 이율, 1년 세 30%?"))
        self.assertIn("이율", str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 통장 이체, 1년 새 30%?"))
        self.assertIn("이체", str(ctx.exception))

    def test_rejects_family_pension_title(self):
        self.assertTrue(title_is_family_pension("내 국민연금 가족, 연 70만 원?"))
        self.assertTrue(title_is_family_pension("유족연금 월 80만 원, 바로 받아요?"))
        self.assertTrue(title_is_family_pension("내 노령연금 가급, 연 70만 원?"))
        self.assertTrue(title_is_family_pension("내 국민연금 배우자, 연 70만 원?"))
        self.assertTrue(title_is_family_pension("내 국민연금 부양가족, 연 70만 원?"))
        self.assertTrue(title_is_family_pension("내 국민연금, 연 70만 원?"))
        self.assertTrue(title_is_family_pension("내 기초연금, 월 30만 원?"))
        self.assertFalse(title_is_family_pension("연금 합쳐 2000만 넘으면 건보 피부양자 탈락"))
        self.assertFalse(title_is_family_pension("종부세 14억? 주택연금 가입은 아직 12억"))
        self.assertFalse(title_is_family_pension("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_family_pension("아버지 통장 4억, 지금 못 꺼내?"))
        self.assertFalse(title_is_family_pension("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 노령연금 가급, 연 70만 원?"))
        self.assertIn("가급", str(ctx.exception))

    def test_rejects_health_depend_title(self):
        self.assertTrue(title_is_health_depend("연금 합쳐 2000만 넘으면 건보 피부양자 탈락"))
        self.assertTrue(title_is_health_depend("연금 합쳐 2000만 원 넘으면 건보 피부양자 탈락"))
        self.assertTrue(title_is_health_depend("내 건보 피부양자, 연 2000만 원?"))
        self.assertTrue(title_is_health_depend("건보료 기준 넘으면 탈락, 연 2000만 원?"))
        self.assertFalse(title_is_health_depend("통장 합산 2000만 원, 건보 피부양자 탈락"))
        self.assertFalse(title_is_health_depend("ISA 남은 한도 2000만 원, 내년에 사라지나"))
        self.assertFalse(title_is_health_depend("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        self.assertFalse(title_is_health_depend("종부세 14억? 주택연금 가입은 아직 12억"))
        self.assertFalse(title_is_health_depend("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_health_depend("아버지 통장 4억, 지금 못 꺼내?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="연금 합쳐 2000만 원 넘으면 건보 피부양자 탈락"))
        self.assertIn("피부양자", str(ctx.exception))

    def test_rejects_tiny_rent_title(self):
        self.assertTrue(title_is_tiny_rent("전세 3만 줄고, 월세 5만이 늘면?"))
        self.assertTrue(title_is_tiny_rent("전세 3만 원 줄고, 월세 5만 원이 늘면?"))
        self.assertTrue(title_is_tiny_rent("내 월세, 5만 원?"))
        self.assertFalse(title_is_tiny_rent("내 전세 월세, 74만 원이 53만?"))
        self.assertFalse(title_is_tiny_rent("전세금 부모에게 빌리면, 무이자 2억?"))
        self.assertFalse(title_is_tiny_rent("전세금 2억 맡기면, 월 73만 원?"))
        self.assertFalse(title_is_tiny_rent("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_tiny_rent("아버지 통장 4억, 지금 못 꺼내?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="전세 3만 원 줄고, 월세 5만 원이 늘면?"))
        self.assertIn("10만", str(ctx.exception))

    def test_rejects_account_crime_title(self):
        self.assertTrue(title_is_account_crime("통장 넘겼다가 범죄자가 된다고?"))
        self.assertTrue(title_is_account_crime("자녀 통장 5000만 원, 넘기면 범죄자?"))
        self.assertTrue(title_is_account_crime("내 통장 대포로 쓰면, 5000만 원?"))
        self.assertFalse(title_is_account_crime("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        self.assertFalse(title_is_account_crime("아버지 명의 예금 4억, 상속 막히면 바로 못 꺼내"))
        self.assertFalse(title_is_account_crime("아버지 통장 4억, 지금 못 꺼내?"))
        self.assertFalse(title_is_account_crime("5억 주담대 이자, 연 140만 원?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="자녀 통장 5000만 원, 넘기면 범죄자?"))
        self.assertIn("범죄", str(ctx.exception))

    def test_rejects_insure_product_title(self):
        self.assertTrue(title_is_insure_product("자차 한 번, 보험료가 30%나?"))
        self.assertTrue(title_is_insure_product("내 자차 보험료, 30%면 연 200만 원?"))
        self.assertTrue(title_is_insure_product("자차 보험료 30%, 내 통장 200만 원?"))
        self.assertTrue(title_is_insure_product("실손 보험료 20%, 내 월급부터"))
        self.assertFalse(title_is_insure_product("국민연금 보험료 9% 인상 검토"))
        self.assertFalse(title_is_insure_product("건보료 기준 넘으면 탈락, 연 2000만 원?"))
        self.assertFalse(title_is_insure_product("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        self.assertFalse(title_is_insure_product("아버지 통장 4억, 지금 못 꺼내?"))
        self.assertFalse(title_is_insure_product("5억 주담대 이자, 연 140만 원?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 자차 보험료, 30%면 연 200만 원?"))
        self.assertIn("보험", str(ctx.exception))

    def test_rejects_tax_count_title(self):
        self.assertTrue(title_is_tax_count("집 한 채에 세금이 다섯 개면?"))
        self.assertTrue(title_is_tax_count("내 집 세금이 다섯 개면, 연 200만 원?"))
        self.assertTrue(title_is_tax_count("내 집 세금이 다섯 개면, 14억?"))
        self.assertTrue(title_is_tax_count("집 한 채 세금 5개, 종부세부터"))
        self.assertFalse(title_is_tax_count("종부세 14억? 주택연금 가입은 아직 12억"))
        self.assertFalse(title_is_tax_count("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        self.assertFalse(title_is_tax_count("IRP 깨면 16.5% 세금, 55세 연금은 3.3%"))
        self.assertFalse(title_is_tax_count("아버지 통장 4억, 지금 못 꺼내?"))
        self.assertFalse(title_is_tax_count("5억 주담대 이자, 연 140만 원?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="내 집 세금이 다섯 개면, 연 200만 원?"))
        self.assertIn("개", str(ctx.exception))

    def test_rejects_jeonse_yield_title(self):
        self.assertTrue(title_is_jeonse_yield("전세금 2억 맡기면, 월 73만 원?"))
        self.assertTrue(title_is_jeonse_yield("전세금 3억 맡기고 월 110만 원?"))
        self.assertTrue(title_is_jeonse_yield("전세금 맡기면 월세 80만 원이 집주인 통장"))
        self.assertFalse(title_is_jeonse_yield("내 전세 월세, 74만 원이 53만?"))
        self.assertFalse(title_is_jeonse_yield("전세금 부모에게 빌리면, 무이자 2억?"))
        self.assertFalse(title_is_jeonse_yield("전세금 HUG에 맡기고 집주인은 월세 받는다"))
        self.assertFalse(title_is_jeonse_yield("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_jeonse_yield("아버지 통장 4억, 지금 못 꺼내?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="전세금 2억 맡기면, 월 73만 원?"))
        self.assertIn("맡기면", str(ctx.exception))

    def test_rejects_tax_rate_title(self):
        self.assertTrue(title_is_tax_rate("IRP 깨면 16.5% 세금, 55세 연금은 3.3%"))
        self.assertTrue(title_is_tax_rate("퇴직소득세 16.5%, 연금은 3.3%?"))
        self.assertTrue(title_is_tax_rate("양도세율 6%, 내 집부터"))
        self.assertFalse(title_is_tax_rate("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        self.assertFalse(title_is_tax_rate("가족이체 2억, 증여세 10%?"))
        self.assertFalse(title_is_tax_rate("종부세 14억? 주택연금 가입은 아직 12억"))
        self.assertFalse(title_is_tax_rate("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_tax_rate("아버지 통장 4억, 지금 못 꺼내?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="IRP 깨면 16.5% 세금, 55세 연금은 3.3%"))
        self.assertIn("세율", str(ctx.exception))

    def test_rejects_nation_jo_title(self):
        self.assertTrue(title_is_nation_jo("퇴직연금 500조, 30%가 20년째 였다"))
        self.assertTrue(title_is_nation_jo("잠든 예금 1.9조, 내 통장부터"))
        self.assertTrue(title_is_nation_jo("가계빚 2000조, 또 늘었나?"))
        self.assertFalse(title_is_nation_jo("예금 보호 1억, 같은 은행은 통장 합산"))
        self.assertFalse(title_is_nation_jo("자녀 통장에 5000만 원, 그냥 옮기면 세금"))
        self.assertFalse(title_is_nation_jo("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_nation_jo("아버지 통장 4억, 지금 못 꺼내?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="퇴직연금 500조, 30%가 20년째"))
        self.assertIn("조", str(ctx.exception))

    def test_rejects_midpay_title(self):
        self.assertTrue(title_is_midpay("6억 중도금 무이자, 이자 2250만?"))
        self.assertTrue(title_is_midpay("신축 분양 중도금, 무이자 3년?"))
        self.assertTrue(title_is_midpay("입주 중도금 대출, 이자 2250만?"))
        self.assertFalse(title_is_midpay("전세금 부모에게 빌리면, 무이자 2억?"))
        self.assertFalse(title_is_midpay("5억 주담대 이자, 연 140만 원?"))
        self.assertFalse(title_is_midpay("아버지 통장 4억, 지금 못 꺼내?"))
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="6억 중도금 무이자, 이자 2250만?"))
        self.assertIn("중도금", str(ctx.exception))

    def test_rejects_title_without_topic(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="이거 실화예요? 3억"))
        self.assertIn("주제", str(ctx.exception))

    def test_rejects_channel_hashtags(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(hashtags="#전세금 #부모 #무이자 #증여세 #돈이웃"))
        self.assertIn("채널", str(ctx.exception))

    def test_rejects_too_few_tags(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(tags=["가계빚", "주담대"]))
        self.assertIn("태그", str(ctx.exception))

    def test_rejects_description_without_lead_keywords(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(description="요즘 소식이 많아서 정리해 봤어요. 내 돈부터 먼저 보면 돼요."))
        self.assertIn("200", str(ctx.exception))

    def test_rejects_first_caption_that_is_not_a_hook(self):
        scenes = _ok().scenes
        scenes[0].captions = ["전세금이 2억이에요", "한도가 더 문제예요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("훅", str(ctx.exception))

    def test_rejects_first_caption_without_title_number(self):
        scenes = _ok().scenes
        scenes[0].captions = ["전세금이 더 붙는다고요?", "한도가 커졌어요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("첫 자막", str(ctx.exception))

    def test_rejects_first_caption_without_personal_stake(self):
        scenes = _ok().scenes
        scenes[0].captions = ["2억이 넘었다고요?", "숫자가 커졌어요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("내 돈", str(ctx.exception))

    def test_rejects_title_without_household_stake(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(
                _ok(
                    title="가계빚 2000억, 또 늘었나?",
                    tags=["가계빚", "주담대", "영끌", "금리인상", "연체율", "가계부채", "주택담보대출", "이자부담", "대출한도", "빚투"],
                    hashtags="#가계빚 #주담대 #영끌 #금리인상 #연체율",
                )
            )
        self.assertIn("내 돈", str(ctx.exception))

    def test_rejects_last_scene_without_personal_stake(self):
        scenes = _ok().scenes
        scenes[-1].text = "부채 규모가 커졌어요"
        scenes[-1].captions = ["부채가 또 늘었어요", "숫자가 커졌어요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("내 돈", str(ctx.exception))

    def test_rejects_photoreal_ai_face_prompt(self):
        scenes = _ok().scenes
        scenes[0].beats[0].image_prompt = (
            ANCHOR + " " + FACE + " A photorealistic cinematic photo of a worried Korean senior."
        )
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("실사", str(ctx.exception))

    def test_rejects_manga_prompt(self):
        scenes = _ok().scenes
        scenes[0].beats[0].image_prompt = ANCHOR + " " + FACE + " manga chibi comic panel with speed lines."
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("망가", str(ctx.exception))

    def test_rejects_prompt_without_style_anchor(self):
        scenes = _ok().scenes
        scenes[1].beats[0].image_prompt = "A painterly animated film of a woman walking at dusk. Luminous sky."
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("anchor", str(ctx.exception))

    def test_load_script_runs_copy_check(self):
        script = _ok()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(script.to_json(), ensure_ascii=False), encoding="utf-8")
            loaded = load_script(path)
            self.assertEqual(loaded.title, script.title)
            self.assertEqual(loaded.style.anchor, ANCHOR)
            self.assertEqual(loaded.style.face, FACE)
            self.assertEqual(loaded.style.wardrobe, WARDROBE)
            self.assertEqual(len(loaded.all_beats()), 16)
            self.assertIn(ANCHOR, loaded.scenes[0].beats[0].image_prompt)
            self.assertIn(FACE, loaded.scenes[0].beats[0].image_prompt)
            self.assertIn(ANATOMY_LOCK, loaded.scenes[0].beats[0].image_prompt)

    def test_rejects_missing_beats(self):
        script = _ok()
        payload = script.to_json()
        payload["scenes"][0].pop("beats", None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_script(path)
        self.assertIn("beats", str(ctx.exception))

    def test_rejects_prompt_without_face_lock(self):
        scenes = _ok().scenes
        scenes[2].beats[0].image_prompt = ANCHOR + ". She walks at dusk. Soft theatrical animation. Luminous sky."
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("face", str(ctx.exception))

    def test_rejects_prompt_without_wardrobe_or_anatomy(self):
        scenes = _ok().scenes
        scenes[0].beats[1].image_prompt = ANCHOR + " " + FACE + " Soft theatrical animation. Luminous sky."
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        msg = str(ctx.exception)
        self.assertTrue("wardrobe" in msg or "해부" in msg)

    def test_rejects_age_drift_across_scenes(self):
        scenes = _ok().scenes
        scenes[1].beats[0].image_prompt = (
            ANCHOR + " " + FACE + " A youthful 20s woman walks in the rain. Soft theatrical animation."
        )
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("얼굴", str(ctx.exception))

    def test_rejects_duration_not_multiple_of_three(self):
        scenes = _ok().scenes
        scenes[0].duration = 10
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(_ok(scenes=scenes).to_json(), ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_script(path)
        self.assertIn("3초", str(ctx.exception))

    def test_description_body_strips_hashtags_and_disclaimer(self):
        raw = "본문이에요.\n\n#가계빚 #쇼츠\n정보 제공이 목적이며 투자 권유가 아닙니다."
        self.assertEqual(description_body(raw), "본문이에요.")

    def test_studio_title_strips_hash(self):
        self.assertEqual(studio_title("가계빚 2000조 #Shorts"), "가계빚 2000조")

    def test_rejects_story_mood_caption(self):
        scenes = _ok().scenes
        scenes[3].captions = ["청약통장만 들고 걸어가요", "아파트 불빛만 올려다봐요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("스토리", str(ctx.exception))

    def test_rejects_title_number_missing_from_captions(self):
        scenes = _ok().scenes
        scenes[0].captions = ["전세금이 더 붙는다고요?", "한도가 또 늘었어요"]
        scenes[3].captions = ["통장만 옮기면 세금이에요", "부담이 더 커져요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("제목 숫자", str(ctx.exception))

    def test_rejects_scene_without_fact_or_fear(self):
        scenes = _ok().scenes
        scenes[2].captions = ["골목으로 내려가요", "창가에 잠시 서 있어요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        msg = str(ctx.exception)
        self.assertTrue("스토리" in msg or "사실" in msg or "공포" in msg)


if __name__ == "__main__":
    unittest.main()
