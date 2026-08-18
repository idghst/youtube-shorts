from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shorts.copy import studio_hashtags, studio_tags
from shorts.models import Scene, Script
from shorts.run import cmd_meta
from shorts.upload import description_with_disclaimer, studio_meta


def _script(**overrides) -> Script:
    data = dict(
        title="가계빚 2000조, 이자만 3조 더?",
        description="영끌이랑 빚투로 가계빚이 처음 2000조를 넘겼어요.\n\n#가계빚 #쇼츠",
        tags=["가계빚", "주담대", "영끌", "금리인상", "연체율", "가계부채", "주택담보대출", "이자부담", "대출한도", "빚투"],
        hashtags="#가계빚 #주담대 #영끌 #금리인상 #연체율",
        scenes=[Scene("a", "p", 10, ["a", "b"])],
    )
    data.update(overrides)
    return Script(**data)


class DescriptionTests(unittest.TestCase):
    def test_body_hashtags_disclaimer(self):
        out = description_with_disclaimer(_script(), "본 영상은 정보 제공 목적입니다.")
        self.assertTrue(out.startswith("영끌이랑 빚투로"))
        self.assertIn("#가계빚 #주담대 #영끌 #금리인상 #연체율", out)
        self.assertNotIn("#돈이웃", out)
        self.assertNotIn("#쇼츠", out)
        self.assertNotIn("#shorts", out)
        self.assertIn("정보 제공 목적", out)
        self.assertNotIn("#Shorts", out.split("\n")[0])

    def test_empty_hashtags_uses_topic_tags(self):
        out = description_with_disclaimer(_script(hashtags=""), "면책")
        self.assertIn("#가계빚", out)
        self.assertNotIn("#돈이웃", out)
        self.assertNotIn("#shorts", out)

    def test_channel_hashtags_are_stripped(self):
        tags = studio_hashtags(_script(hashtags="#가계빚 #주담대 #영끌 #금리인상 #돈이웃 #쇼츠 #shorts"))
        self.assertIn("#가계빚", tags)
        self.assertNotIn("#돈이웃", tags)
        self.assertNotIn("#쇼츠", tags)
        self.assertNotIn("#shorts", tags)

    def test_studio_tags_skip_channel_words(self):
        tags = studio_tags(_script())
        self.assertIn("가계빚", tags)
        self.assertNotIn("돈이웃", tags)
        self.assertNotIn("쇼츠", tags)
        self.assertGreaterEqual(len(tags), 10)

    def test_studio_meta_lists_hashtag_chips_and_skips_channel_tags(self):
        script = _script(
            title="송파 로또 청약, 11억? #Shorts",
            description="송파 로또 청약에 한 가구를 두고 9만명이 몰렸어요.",
            hashtags="#로또청약 #송파청약 #청약 #시세차익 #무순위청약 #돈이웃 #쇼츠 #shorts",
            tags=["송파", "로또청약", "청약", "11억", "시세차익", "쇼츠", "돈이웃"],
        )
        meta = studio_meta(script, "본 영상은 정보 제공 목적입니다.")
        self.assertEqual(meta["title"], "송파 로또 청약, 11억?")
        self.assertIn("#로또청약", meta["hashtags"])
        self.assertIn("로또청약", meta["hashtag_chips"])
        self.assertNotIn("shorts", meta["hashtag_chips"])
        self.assertGreaterEqual(len(meta["hashtag_chips"]), 5)
        self.assertIn("송파", meta["tags"])
        self.assertNotIn("쇼츠", meta["tags"])
        self.assertNotIn("돈이웃", meta["tags"])
        self.assertIn("정보 제공 목적", meta["description"])
        self.assertGreaterEqual(meta["description"].count("#"), 3)


class MetaCommandTests(unittest.TestCase):
    def test_meta_prints_hashtags_for_studio(self):
        script = _script()
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(json.dumps(script.to_json(), ensure_ascii=False), encoding="utf-8")
            with patch("shorts.run.resolve_job", return_value=job), patch("shorts.run.load_script", return_value=script):
                import io
                import sys

                buf = io.StringIO()
                old = sys.stdout
                sys.stdout = buf
                try:
                    cmd_meta(str(job))
                finally:
                    sys.stdout = old
        data = json.loads(buf.getvalue())
        self.assertIn("#가계빚", data["description"])
        self.assertIn("#가계빚", data["hashtags"])
        self.assertNotIn("#shorts", data["hashtags"])
        self.assertIn("가계빚", data["hashtag_chips"])
        self.assertIn("가계빚", data["tags"])
        self.assertNotIn("돈이웃", data["tags"])


if __name__ == "__main__":
    unittest.main()
