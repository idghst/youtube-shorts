from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from shorts.models import Scene, Script, Style, scene_media_path
from shorts.render import fit_vf
from shorts.run import missing_agent_assets

ANCHOR = (
    "the same silver-haired Korean woman in a cream cardigan, "
    "painterly animated film, luminous dusk sky"
)


def _script() -> Script:
    prompt = ANCHOR + ". Soft theatrical animation, luminous sky. Vertical 9:16."
    return Script(
        title="가계빚 2000조, 이자만 3조 더?",
        description="영끌이랑 빚투로 가계빚이 처음 2000조를 넘겼어요. 늘어난 빚의 열 중 여덟이 주택담보대출이고, 금리가 오르면 이자만 3조가 더 붙는다는 얘기예요.",
        tags=["가계빚", "주담대"],
        hashtags="#가계빚 #주담대 #영끌 #금리인상 #돈이웃 #쇼츠 #shorts",
        style=Style(anchor=ANCHOR, mood="dusk town"),
        scenes=[
            Scene("가계빚이 2000조를 넘겼어요", prompt, 7, ["이자가 더 붙는다고요?", "가계빚이 2000조예요"]),
            Scene("영끌과 빚투가 밀어 올렸어요", prompt, 8, ["영끌이랑 빚투가 밀었어요", "늘분의 열 중 여덟이 주담대"]),
            Scene("한도를 넓히면 더 늘어요", prompt, 8, ["한도를 넓히면 더 늘어요", "연체는 10년 만에 최고예요"]),
            Scene("내 이자부터 흔들려요", prompt, 7, ["빚이 월급보다 먼저 컸어요", "내 이자부터 흔들려요"]),
        ],
    )


class FitFilterTests(unittest.TestCase):
    def test_fit_does_not_zoom(self):
        vf = fit_vf(1080, 1920)
        self.assertNotIn("zoompan", vf)
        self.assertNotIn("zoom", vf.lower())
        self.assertIn("scale=1080:1920", vf)
        self.assertIn("crop=1080:1920", vf)


class MediaPathTests(unittest.TestCase):
    def test_prefers_mp4_over_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "scene-01.png").write_bytes(b"png")
            (job / "scene-01.mp4").write_bytes(b"mp4")
            self.assertEqual(scene_media_path(job, 1).name, "scene-01.mp4")

    def test_falls_back_to_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "scene-02.png").write_bytes(b"png")
            self.assertEqual(scene_media_path(job, 2).name, "scene-02.png")

    def test_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(scene_media_path(Path(tmp), 1))


class MissingAssetsTests(unittest.TestCase):
    def test_missing_clip_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(
                json.dumps(_script().to_json(), ensure_ascii=False),
                encoding="utf-8",
            )
            gaps = missing_agent_assets(job)
        self.assertTrue(any("scene-01" in g for g in gaps))

    def test_png_clips_are_enough(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(
                json.dumps(_script().to_json(), ensure_ascii=False),
                encoding="utf-8",
            )
            for i in range(1, 5):
                (job / ("scene-%02d.png" % i)).write_bytes(b"x")
            self.assertEqual(missing_agent_assets(job), [])

    def test_mp4_clips_are_enough(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(
                json.dumps(_script().to_json(), ensure_ascii=False),
                encoding="utf-8",
            )
            for i in range(1, 5):
                (job / ("scene-%02d.mp4" % i)).write_bytes(b"x")
            self.assertEqual(missing_agent_assets(job), [])

    def test_missing_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            gaps = missing_agent_assets(Path(tmp))
        self.assertTrue(any("script.json" in g for g in gaps))


if __name__ == "__main__":
    unittest.main()
