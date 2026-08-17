from __future__ import annotations

import unittest

from shorts.models import Scene, Script
from shorts.upload import description_with_disclaimer


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


if __name__ == "__main__":
    unittest.main()
