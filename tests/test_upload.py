from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shorts.copy import studio_hashtags, studio_tags
from shorts.models import Scene, Script
from shorts.run import cmd_meta
from shorts.upload import description_with_disclaimer


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
        self.assertIn("가계빚", data["tags"])
        self.assertNotIn("돈이웃", data["tags"])


if __name__ == "__main__":
    unittest.main()
