from __future__ import annotations

import unittest
from datetime import datetime

from shorts.models import Headline
from shorts.news import (
    _blocked_topic,
    _finance_score,
    _senior_score,
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

    def test_skips_blocked_auto_pick_topics(self):
        blocked = _h("알고리즘이 데이터 분석…퇴직연금 맞춤설계")
        other = _h("가업상속공제 문턱 30년, 상속재산분할 실무가 달라진다")
        self.assertTrue(_blocked_topic(blocked.title))
        chosen = choose_headline([blocked, other], now=datetime(2026, 8, 17, 9))
        self.assertEqual(chosen.title, other.title)

    def test_skips_similar_used_topic(self):
        used = ["영끌 빚투에 가계빚 사상 첫 2000조 기준금리"]
        similar = _h("영끌 빚투 가계빚 2000조 기준금리 인상")
        other = _h("기초연금 지급액 인상 논의")
        self.assertGreaterEqual(topic_overlap(similar.title, used[0]), 3)
        chosen = choose_headline([similar, other], now=datetime(2026, 8, 17, 9), used_titles=used)
        self.assertEqual(chosen.title, other.title)


if __name__ == "__main__":
    unittest.main()
