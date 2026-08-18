from __future__ import annotations

import unittest

from shorts.models import Scene, Script
from shorts.upload import description_with_disclaimer, studio_meta


class DescriptionTests(unittest.TestCase):
    def test_body_hashtags_disclaimer(self):
        script = Script(
            title="가계빚 2000조, 이자만 3조 더?",
            description="영끌이랑 빚투로 가계빚이 처음 2000조를 넘겼어요.\n\n#가계빚 #쇼츠",
            hashtags="#가계빚 #주담대 #돈이웃 #쇼츠 #shorts",
            scenes=[Scene("a", "p", 10, ["a", "b"])],
        )
        out = description_with_disclaimer(script, "본 영상은 정보 제공 목적입니다.")
        self.assertTrue(out.startswith("영끌이랑 빚투로"))
        self.assertIn("#가계빚 #주담대 #돈이웃 #쇼츠 #shorts", out)
        self.assertIn("정보 제공 목적", out)
        self.assertNotIn("#Shorts", out.split("\n")[0])

    def test_studio_meta_lists_hashtag_chips_and_skips_channel_tags(self):
        script = Script(
            title="송파 로또 청약, 11억? #Shorts",
            description="송파 로또 청약에 한 가구를 두고 9만명이 몰렸어요.",
            hashtags="#로또청약 #송파청약 #청약 #시세차익 #무순위청약 #돈이웃 #쇼츠 #shorts",
            tags=["송파", "로또청약", "청약", "11억", "시세차익", "쇼츠", "돈이웃"],
            scenes=[Scene("a", "p", 10, ["a", "b"])],
        )
        meta = studio_meta(script, "본 영상은 정보 제공 목적입니다.")
        self.assertEqual(meta["title"], "송파 로또 청약, 11억?")
        self.assertIn("#로또청약 #송파청약", meta["hashtags"])
        self.assertIn("로또청약", meta["hashtag_chips"])
        self.assertIn("shorts", meta["hashtag_chips"])
        self.assertGreaterEqual(len(meta["hashtag_chips"]), 5)
        self.assertIn("송파", meta["tags"])
        self.assertNotIn("쇼츠", meta["tags"])
        self.assertNotIn("돈이웃", meta["tags"])
        self.assertIn("정보 제공 목적", meta["description"])
        self.assertGreaterEqual(meta["description"].count("#"), 3)


if __name__ == "__main__":
    unittest.main()
