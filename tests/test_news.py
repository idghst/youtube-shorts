from __future__ import annotations

import unittest
from datetime import datetime

from shorts.models import Headline
from shorts.news import (
    _finance_score,
    _house_score,
    _senior_score,
    _same_hook,
    _weak_news_penalty,
    choose_headline,
    headline_hash,
    topic_overlap,
)


def _h(title: str, source: str = "hankyung_finance", summary: str = "", published: str = "") -> Headline:
    return Headline(
        source=source,
        title=title,
        summary=summary,
        link="",
        published=published,
        hash=headline_hash(title),
    )


class SeniorScoreTests(unittest.TestCase):
    def test_pension_outranks_nasdaq(self):
        pension = _h("국민연금 개혁안, 보험료율 인상 검토")
        nasdaq = _h("나스닥 급등, 반도체 실적 호조")
        self.assertGreater(_senior_score(pension), 0)
        self.assertEqual(_senior_score(nasdaq), 0)
        self.assertGreater(_finance_score(nasdaq), 0)

    def test_core_beats_near_topic(self):
        core = _h("은퇴 후 국민연금만으로 노후 될까")
        near = _h("전세 보증금 반환 소송 늘었다")
        self.assertGreater(_senior_score(core), _senior_score(near))


class ChooseHeadlineTests(unittest.TestCase):
    def test_senior_beats_newer_finance(self):
        nasdaq = _h(
            "나스닥 급등 반도체 실적",
            source="reuters_business",
            published="Mon, 17 Aug 2026 10:00:00 +0000",
        )
        pension = _h(
            "기초연금 지급액 인상 논의",
            source="hankyung_economy",
            published="Mon, 17 Aug 2026 01:00:00 +0000",
        )
        chosen = choose_headline([nasdaq, pension], now=datetime(2026, 8, 17, 15))
        self.assertEqual(chosen.title, pension.title)

    def test_more_senior_keywords_win(self):
        weak = _h("전세 시장 한파", published="Mon, 17 Aug 2026 12:00:00 +0000")
        strong = _h(
            "은퇴 앞둔 직장인, 퇴직연금·IRP 점검",
            published="Mon, 17 Aug 2026 08:00:00 +0000",
        )
        chosen = choose_headline([weak, strong], now=datetime(2026, 8, 17, 9))
        self.assertEqual(chosen.title, strong.title)

    def test_no_senior_falls_back_to_finance_and_morning_source(self):
        reuters = _h(
            "한은 기준금리 동결, 물가 안정세",
            source="reuters_business",
            published="Mon, 17 Aug 2026 10:00:00 +0000",
        )
        hankyung = _h(
            "한은 기준금리 동결과 물가",
            source="hankyung_finance",
            published="Mon, 17 Aug 2026 09:00:00 +0000",
        )
        self.assertEqual(_finance_score(reuters), _finance_score(hankyung))
        chosen = choose_headline([reuters, hankyung], now=datetime(2026, 8, 17, 9))
        self.assertEqual(chosen.source, "hankyung_finance")

    def test_afternoon_prefers_english_source_when_scores_tie(self):
        reuters = _h(
            "연준 금리 동결, 물가 둔화 흐름",
            source="reuters_business",
            published="Mon, 17 Aug 2026 10:00:00 +0000",
        )
        hankyung = _h(
            "연준 금리 동결, 물가 둔화 국면",
            source="hankyung_finance",
            published="Mon, 17 Aug 2026 10:00:00 +0000",
        )
        self.assertEqual(_finance_score(reuters), _finance_score(hankyung))
        chosen = choose_headline([hankyung, reuters], now=datetime(2026, 8, 17, 15))
        self.assertEqual(chosen.source, "reuters_business")

    def test_empty_unused_exits(self):
        with self.assertRaises(SystemExit):
            choose_headline([])

    def test_skips_similar_used_topic(self):
        used = ["영끌 빚투에 가계빚 사상 첫 2000조 기준금리"]
        similar = _h("영끌 빚투 가계빚 2000조 기준금리 인상")
        other = _h("기초연금 지급액 인상 논의")
        self.assertGreaterEqual(topic_overlap(similar.title, used[0]), 3)
        chosen = choose_headline([similar, other], now=datetime(2026, 8, 17, 9), used_titles=used)
        self.assertEqual(chosen.title, other.title)

    def test_household_stake_beats_plain_jeonse(self):
        plain = _h("전세 시장 한파", published="Mon, 17 Aug 2026 12:00:00 +0000")
        house = _h(
            "부모에게 전세금 빌리면 증여세·무이자 한도",
            published="Mon, 17 Aug 2026 08:00:00 +0000",
        )
        self.assertGreater(_house_score(house), _house_score(plain))
        chosen = choose_headline([plain, house], now=datetime(2026, 8, 17, 9))
        self.assertEqual(chosen.title, house.title)

    def test_viral_number_beats_same_senior_topic(self):
        plain = _h("국민연금 개혁안 논의")
        punch = _h("국민연금 보험료 9% 인상 검토")
        chosen = choose_headline([plain, punch], now=datetime(2026, 8, 17, 9))
        self.assertEqual(chosen.title, punch.title)

    def test_house_limit_beats_senior_national_stat(self):
        nation = _h("퇴직연금 적립금 500조, 30%가 20년째 방치")
        house = _h("예금 보호 1억, 같은 은행은 통장 합산")
        self.assertGreater(_house_score(house), _house_score(nation))
        self.assertGreater(_weak_news_penalty(nation), 0)
        chosen = choose_headline([nation, house], now=datetime(2026, 8, 17, 9))
        self.assertEqual(chosen.title, house.title)

    def test_place_youth_news_loses_to_parent_jeonse(self):
        place = _h("전세난에 지친 2030, 은평으로 몰리나")
        house = _h("부모에게 전세금 빌리면 증여세·무이자 한도")
        self.assertGreater(_weak_news_penalty(place), 0)
        chosen = choose_headline([place, house], now=datetime(2026, 8, 17, 9))
        self.assertEqual(chosen.title, house.title)

    def test_skips_same_isa_limit_amount(self):
        used = ["ISA 남은 한도 2000만 원, 내년에 사라지나"]
        remake = _h("ISA 통장 한도, 이제 연 2000만 원?")
        other = _h("예금 보호 1억, 같은 은행은 통장 합산")
        self.assertTrue(_same_hook(remake.title, used[0]))
        chosen = choose_headline([remake, other], now=datetime(2026, 8, 17, 9), used_titles=used)
        self.assertEqual(chosen.title, other.title)

    def test_same_digits_different_unit_is_not_remake(self):
        self.assertFalse(
            _same_hook(
                "전세금 부모에게 빌리면, 무이자 2억?",
                "전세금 미반환, 2만 원 차이면",
            )
        )

    def test_skips_same_limit_amount(self):
        used = ["ISA 남은 한도 2000만 원, 내년에 사라지나"]
        remake = _h("주부 신용대출, 한도 2000만 원?")
        other = _h("예금 보호 1억, 같은 은행은 통장 합산")
        self.assertTrue(_same_hook(remake.title, used[0]))
        chosen = choose_headline([remake, other], now=datetime(2026, 8, 21, 3), used_titles=used)
        self.assertEqual(chosen.title, other.title)

    def test_rate_promo_headline_loses_to_wolse_cash(self):
        promo = _h("국민은행 연 12% 역대급 적금, 선착순 월 30만 한도")
        house = _h("전세금 HUG에 맡기고 집주인은 월세 받는다")
        self.assertGreater(_weak_news_penalty(promo), 0)
        chosen = choose_headline([promo, house], now=datetime(2026, 8, 21, 9))
        self.assertEqual(chosen.title, house.title)

    def test_workplace_benefit_loses_to_parent_jeonse(self):
        work = _h("육아휴직급여 안들어왔어요, 회사 확인서 빠지면 0원")
        house = _h("부모에게 전세금 빌리면 증여세·무이자 한도")
        self.assertGreater(_weak_news_penalty(work), 0)
        chosen = choose_headline([work, house], now=datetime(2026, 8, 21, 21))
        self.assertEqual(chosen.title, house.title)

    def test_rate_only_headline_is_penalized(self):
        rate = _h("변동 주담대 이자, 연 6%로 상승")
        tax = _h("가족이체 2억, 증여세 10%")
        self.assertGreater(_weak_news_penalty(rate), 0)
        self.assertEqual(_weak_news_penalty(tax), 0)

    def test_index_return_headline_loses_to_jeonse_wolse(self):
        index = _h("코스피 56% 올랐는데 내 연금은 왜, 디폴트옵션")
        house = _h("전세금 HUG에 맡기고 집주인은 월세 받는다")
        self.assertGreater(_weak_news_penalty(index), 0)
        self.assertGreater(_house_score(house), _house_score(index))
        chosen = choose_headline([index, house], now=datetime(2026, 8, 20, 12))
        self.assertEqual(chosen.title, house.title)

    def test_jeonse_price_news_loses_to_wolse_cash(self):
        price = _h("집주인 전화올까…세입자 덮친 실거주, 전셋값 2년 새 7800만")
        house = _h("전세금 HUG에 맡기고 집주인은 월세 받는다")
        self.assertGreater(_weak_news_penalty(price), 0)
        chosen = choose_headline([price, house], now=datetime(2026, 8, 20, 9))
        self.assertEqual(chosen.title, house.title)

    def test_skips_same_wolse_amount(self):
        used = ["내 전세 월세, 74만 원이 53만?"]
        remake = _h("전세금 맡기면 월세 74만 원이 집주인 통장")
        other = _h("예금 보호 1억, 같은 은행은 통장 합산")
        self.assertTrue(_same_hook(remake.title, used[0]))
        chosen = choose_headline([remake, other], now=datetime(2026, 8, 20, 21), used_titles=used)
        self.assertEqual(chosen.title, other.title)

    def test_skips_near_wolse_amount(self):
        used = ["내 전세 월세, 74만 원이 53만?"]
        remake = _h("전세금 2억 맡기면, 월세 73만 원이 집주인")
        other = _h("예금 보호 1억, 같은 은행은 통장 합산")
        self.assertTrue(_same_hook(remake.title, used[0]))
        chosen = choose_headline([remake, other], now=datetime(2026, 8, 22, 21), used_titles=used)
        self.assertEqual(chosen.title, other.title)

    def test_interest_cash_beats_bare_limit(self):
        bare = _h("내 통장 한도, 월 50만 원 입금")
        cash = _h("5억 주담대 이자, 연 140만 원")
        self.assertGreater(_weak_news_penalty(bare), 0)
        self.assertEqual(_house_score(bare), 0)
        self.assertGreater(_house_score(cash), 0)
        chosen = choose_headline([bare, cash], now=datetime(2026, 8, 22, 9))
        self.assertEqual(chosen.title, cash.title)

    def test_pension_double_loses_to_interest_cash(self):
        pension = _h("국민연금 1개월 내고 2배, 연금액 200%")
        cash = _h("5억 주담대 이자, 연 140만 원")
        self.assertGreater(_weak_news_penalty(pension), 0)
        self.assertEqual(_house_score(pension), 0)
        chosen = choose_headline([pension, cash], now=datetime(2026, 8, 22, 15))
        self.assertEqual(chosen.title, cash.title)

    def test_rate_promo_does_not_get_house_from_interest_word(self):
        rate = _h("변동 주담대 이자, 연 6%로 상승")
        cash = _h("5억 주담대 이자, 연 140만 원")
        self.assertEqual(_house_score(rate), 0)
        self.assertGreater(_house_score(cash), _house_score(rate))
        chosen = choose_headline([rate, cash], now=datetime(2026, 8, 22, 12))
        self.assertEqual(chosen.title, cash.title)

    def test_skips_same_account_eok(self):
        used = ["아버지 통장 4억, 지금 못 꺼내?"]
        remake = _h("엄마 통장 4억, 상속이면 바로 인출")
        other = _h("예금 보호 1억, 같은 은행은 통장 합산")
        self.assertTrue(_same_hook(remake.title, used[0]))
        chosen = choose_headline([remake, other], now=datetime(2026, 8, 23, 21), used_titles=used)
        self.assertEqual(chosen.title, other.title)

    def test_father_withdraw_beats_bare_limit(self):
        bare = _h("내 통장 한도, 월 50만 원 입금")
        father = _h("아버지 명의 예금 4억, 상속 막히면 바로 못 꺼내")
        self.assertGreater(_weak_news_penalty(bare), 0)
        self.assertEqual(_house_score(bare), 0)
        self.assertGreater(_house_score(father), 0)
        chosen = choose_headline([bare, father], now=datetime(2026, 8, 23, 9))
        self.assertEqual(chosen.title, father.title)

    def test_bare_mortgage_payoff_loses_to_interest_cash(self):
        payoff = _h("다주택 주담대 만기 연장 막히면 원금 2억 일시상환")
        cash = _h("5억 주담대 이자, 연 140만 원")
        self.assertGreater(_weak_news_penalty(payoff), 0)
        self.assertEqual(_house_score(payoff), 0)
        self.assertGreater(_house_score(cash), 0)
        chosen = choose_headline([payoff, cash], now=datetime(2026, 8, 24, 21))
        self.assertEqual(chosen.title, cash.title)

    def test_father_word_gives_house_score(self):
        father = _h("돌아가신 아버지 예금, 인출이 막혔다")
        pension = _h("국민연금 개혁안, 보험료율 인상 검토")
        self.assertGreater(_house_score(father), 0)
        self.assertGreater(_house_score(father), _house_score(pension))
        chosen = choose_headline([pension, father], now=datetime(2026, 8, 23, 15))
        self.assertEqual(chosen.title, father.title)

    def test_account_rate_loses_to_father_withdraw(self):
        rate = _h("내 통장 이율, 1년 세 30% 원천징수")
        father = _h("아버지 명의 예금 4억, 상속 막히면 바로 못 꺼내")
        self.assertGreater(_weak_news_penalty(rate), 0)
        self.assertEqual(_house_score(rate), 0)
        self.assertGreater(_house_score(father), 0)
        chosen = choose_headline([rate, father], now=datetime(2026, 8, 25, 21))
        self.assertEqual(chosen.title, father.title)

    def test_transfer_pct_loses_to_father_withdraw(self):
        transfer = _h("내 통장 이체, 1년 새 30% 늘었다")
        father = _h("아버지 명의 예금 4억, 상속 막히면 바로 못 꺼내")
        self.assertGreater(_weak_news_penalty(transfer), 0)
        self.assertEqual(_house_score(transfer), 0)
        self.assertGreater(_house_score(father), 0)
        chosen = choose_headline([transfer, father], now=datetime(2026, 8, 29, 21))
        self.assertEqual(chosen.title, father.title)

    def test_jeonse_account_year_rate_loses_to_withdraw(self):
        locked = _h("전세 보증금 안심신탁 통장, 묶이면 연 4.5% 이자")
        father = _h("아버지 명의 예금 4억, 상속 막히면 바로 못 꺼내")
        self.assertGreater(_weak_news_penalty(locked), 0)
        self.assertEqual(_house_score(locked), 0)
        self.assertGreater(_house_score(father), 0)
        chosen = choose_headline([locked, father], now=datetime(2026, 8, 27, 21))
        self.assertEqual(chosen.title, father.title)

    def test_family_pension_loses_to_withdraw(self):
        family = _h("국민연금 가족 급여, 연 70만 원 유족")
        father = _h("아버지 명의 예금 4억, 상속 막히면 바로 못 꺼내")
        self.assertGreater(_weak_news_penalty(family), 0)
        self.assertEqual(_house_score(family), 0)
        self.assertGreater(_house_score(father), 0)
        chosen = choose_headline([family, father], now=datetime(2026, 8, 28, 21))
        self.assertEqual(chosen.title, father.title)

    def test_nps_addon_loses_to_withdraw(self):
        addon = _h("노령연금 가급액, 배우자 연 70만 원")
        bare = _h("내 국민연금, 연 70만 원 더 붙나")
        father = _h("아버지 명의 예금 4억, 상속 막히면 바로 못 꺼내")
        self.assertGreater(_weak_news_penalty(addon), 0)
        self.assertGreater(_weak_news_penalty(bare), 0)
        self.assertEqual(_house_score(addon), 0)
        self.assertEqual(_house_score(bare), 0)
        self.assertGreater(_house_score(father), 0)
        chosen = choose_headline([addon, bare, father], now=datetime(2026, 8, 30, 21))
        self.assertEqual(chosen.title, father.title)

    def test_jeonse_yield_loses_to_wolse_compare(self):
        parked = _h("전세금 2억 맡기면, 월 73만 원 이자")
        compare = _h("전세 월세 74만 원이 53만으로 깎인다")
        hug = _h("전세금 HUG에 맡기고 집주인은 월세 받는다")
        self.assertGreater(_weak_news_penalty(parked), 0)
        self.assertEqual(_house_score(parked), 0)
        self.assertGreater(_house_score(compare), 0)
        self.assertGreater(_house_score(hug), 0)
        chosen = choose_headline([parked, compare], now=datetime(2026, 8, 22, 9))
        self.assertEqual(chosen.title, compare.title)

    def test_tax_rate_loses_to_eok_tax(self):
        rate = _h("IRP 해지하면 16.5% 세금, 연금은 3.3%")
        cash = _h("자녀 통장 5000만 원, 그냥 옮기면 증여세")
        self.assertGreater(_weak_news_penalty(rate), 0)
        self.assertEqual(_house_score(rate), 0)
        self.assertGreater(_house_score(cash), 0)
        chosen = choose_headline([rate, cash], now=datetime(2026, 8, 15, 9))
        self.assertEqual(chosen.title, cash.title)

    def test_nation_jo_loses_to_deposit_eok(self):
        nation = _h("퇴직연금 적립금 500조, 30%가 20년째 방치")
        house = _h("예금 보호 1억, 같은 은행은 통장 합산")
        self.assertGreater(_weak_news_penalty(nation), 0)
        self.assertEqual(_house_score(nation), 0)
        chosen = choose_headline([nation, house], now=datetime(2026, 8, 16, 9))
        self.assertEqual(chosen.title, house.title)

    def test_tiny_rent_loses_to_wolse_compare(self):
        tiny = _h("전세 3만 원 줄고, 월세 5만 원이 늘면")
        compare = _h("전세 월세 74만 원이 53만으로 깎인다")
        self.assertGreater(_weak_news_penalty(tiny), 0)
        self.assertEqual(_house_score(tiny), 0)
        self.assertGreater(_house_score(compare), 0)
        chosen = choose_headline([tiny, compare], now=datetime(2026, 8, 18, 9))
        self.assertEqual(chosen.title, compare.title)

    def test_rate_compare_without_year_loses_to_isa_limit(self):
        compare = _h("적금 10%? 시중은행 예금은 3.3%, 내 통장")
        isa = _h("ISA 남은 한도 2000만 원, 내년에 사라지나")
        self.assertGreater(_weak_news_penalty(compare), 0)
        self.assertEqual(_house_score(compare), 0)
        self.assertGreater(_house_score(isa), 0)
        chosen = choose_headline([compare, isa], now=datetime(2026, 8, 20, 9))
        self.assertEqual(chosen.title, isa.title)

    def test_account_crime_loses_to_tax_transfer(self):
        crime = _h("자녀 통장 5000만 원, 넘기면 범죄자")
        tax = _h("자녀 통장 5000만 원, 그냥 옮기면 증여세")
        self.assertGreater(_weak_news_penalty(crime), 0)
        self.assertEqual(_house_score(crime), 0)
        self.assertGreater(_house_score(tax), 0)
        chosen = choose_headline([crime, tax], now=datetime(2026, 8, 21, 9))
        self.assertEqual(chosen.title, tax.title)

    def test_health_depend_loses_to_isa_limit(self):
        depend = _h("연금 합쳐 2000만 원 넘으면 건보 피부양자 탈락")
        isa = _h("ISA 남은 한도 2000만 원, 내년에 사라지나")
        self.assertGreater(_weak_news_penalty(depend), 0)
        self.assertEqual(_house_score(depend), 0)
        self.assertGreater(_house_score(isa), 0)
        chosen = choose_headline([depend, isa], now=datetime(2026, 8, 17, 9))
        self.assertEqual(chosen.title, isa.title)

    def test_month_interest_loses_to_year_cash(self):
        monthly = _h("3억 주담대 이자, 한 달 200만 원 원리금")
        yearly = _h("5억 주담대 이자, 연 140만 원")
        self.assertGreater(_weak_news_penalty(monthly), 0)
        self.assertEqual(_house_score(monthly), 0)
        self.assertGreater(_house_score(yearly), 0)
        chosen = choose_headline([monthly, yearly], now=datetime(2026, 8, 19, 21))
        self.assertEqual(chosen.title, yearly.title)

    def test_midpay_promo_loses_to_interest_cash(self):
        midpay = _h("6억 중도금 무이자, 이자 2250만 원 분양")
        cash = _h("5억 주담대 이자, 연 140만 원")
        self.assertGreater(_weak_news_penalty(midpay), 0)
        self.assertEqual(_house_score(midpay), 0)
        self.assertGreater(_house_score(cash), 0)
        chosen = choose_headline([midpay, cash], now=datetime(2026, 8, 26, 21))
        self.assertEqual(chosen.title, cash.title)


if __name__ == "__main__":
    unittest.main()
