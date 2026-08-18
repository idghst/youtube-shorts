from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from shorts.models import Scene, Script, Style, scene_media_path
from shorts.render import fit_vf, write_caption_png
from shorts.run import missing_agent_assets

ANCHOR = (
    "the same silver-haired Korean woman in a cream cardigan, "
    "painterly animated film, luminous dusk sky"
)
FACE = (
    "same late-60s Korean woman, silver bob to the jaw, "
    "soft eye wrinkles, round cheeks, do not change age"
)


def _script() -> Script:
    prompt = ANCHOR + ". " + FACE + ". Soft theatrical animation, luminous sky. Vertical 9:16."
    return Script(
        title="가계빚 2000조, 이자만 3조 더?",
        description="영끌이랑 빚투로 가계빚이 처음 2000조를 넘겼어요. 늘어난 빚의 열 중 여덟이 주택담보대출이고, 금리가 오르면 이자만 3조가 더 붙는다는 얘기예요.",
        tags=["가계빚", "주담대"],
        hashtags="#가계빚 #주담대 #영끌 #금리인상 #돈이웃 #쇼츠 #shorts",
        style=Style(anchor=ANCHOR, face=FACE, mood="dusk town"),
        scenes=[
            Scene("가계빚이 2000조를 넘겼어요", prompt, 7, ["이자가 더 붙는다고요?", "가계빚이 2000조예요"]),
            Scene("영끌과 빚투가 밀어 올렸어요", prompt, 8, ["영끌이랑 빚투가 밀었어요", "늘분의 열 중 여덟이 주담대"]),
            Scene("한도를 넓히면 더 늘어요", prompt, 8, ["한도를 넓히면 더 늘어요", "연체는 10년 만에 최고예요"]),
            Scene("내 이자부터 흔들려요", prompt, 7, ["빚이 월급보다 먼저 컸어요", "내 이자부터 흔들려요"]),
        ],
    )


class FitFilterTests(unittest.TestCase):
    def test_fit_does_not_zoom_or_letterbox(self):
        vf = fit_vf(1080, 1920)
        self.assertEqual(vf, "scale=1080:1920")
        self.assertNotIn("zoompan", vf)
        self.assertNotIn("increase", vf)
        self.assertNotIn("crop", vf)
        self.assertNotIn("pad", vf)


class CaptionTests(unittest.TestCase):
    def test_caption_has_no_black_bar(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("가계빚 2000조요", path, width=1080)
            from PIL import Image

            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            self.assertEqual(img.getpixel((0, 0))[3], 0)
            self.assertEqual(img.getpixel((1079, 0))[3], 0)
            self.assertEqual(img.getpixel((0, img.size[1] - 1))[3], 0)


class MediaPathTests(unittest.TestCase):
    def test_prefers_mp4_over_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "scene-01.png").write_bytes(b"png")
            (job / "scene-01.mp4").write_bytes(b"mp4")
            self.assertEqual(scene_media_path(job, 1).name, "scene-01.mp4")

    def test_png_alone_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "scene-02.png").write_bytes(b"png")
            self.assertIsNone(scene_media_path(job, 2))

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
        self.assertTrue(any("scene-01.mp4" in g for g in gaps))

    def test_png_is_not_enough(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(
                json.dumps(_script().to_json(), ensure_ascii=False),
                encoding="utf-8",
            )
            for i in range(1, 5):
                (job / ("scene-%02d.png" % i)).write_bytes(b"x")
            gaps = missing_agent_assets(job)
        self.assertTrue(any("scene-01.mp4" in g for g in gaps))

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
