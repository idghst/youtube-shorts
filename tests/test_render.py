from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from shorts.models import ANATOMY_LOCK, Beat, Scene, Script, Style, beat_media_path, scene_media_path
from shorts.render import caption_at, fit_vf, write_caption_png
from shorts.run import missing_agent_assets

ANCHOR = (
    "the same silver-haired Korean woman in a cream cardigan, "
    "painterly animated film, luminous dusk sky"
)
FACE = (
    "same late-60s Korean woman, silver bob to the jaw, "
    "soft eye wrinkles, round cheeks, do not change age"
)
WARDROBE = "same cream cardigan over ivory blouse every beat"


def _prompt() -> str:
    return (
        "%s. %s. %s. %s. Soft theatrical animation, luminous sky. Vertical 9:16."
        % (ANCHOR, FACE, WARDROBE, ANATOMY_LOCK)
    )


def _beats(n: int) -> list:
    return [Beat(image_prompt=_prompt()) for _ in range(n)]


def _script() -> Script:
    return Script(
        title="전세금 부모에게 빌리면, 무이자 2억?",
        description="전세금을 부모에게 빌리면 무이자 한도가 있어요. 차용증 없이 통장만 옮기면 증여세가 붙고, 한도는 2억까지예요.",
        tags=["전세금", "부모", "무이자", "증여세", "차용증", "한도", "전세", "가족이체", "통장", "증여"],
        hashtags="#전세금 #부모 #무이자 #증여세 #차용증",
        style=Style(anchor=ANCHOR, face=FACE, wardrobe=WARDROBE, mood="dusk town"),
        scenes=[
            Scene("전세금을 부모에게 빌리면 한도가 있어요", duration=12, captions=["무이자 2억까지라고요?", "전세금을 부모에게 빌리면"], beats=_beats(4)),
            Scene("차용증 없이 옮기면 증여세가 붙어요", duration=9, captions=["차용증이 없으면 증여세예요", "한도를 넘기면 더 붙어요"], beats=_beats(3)),
            Scene("무이자로 빌려도 한도는 2억이에요", duration=9, captions=["무이자여도 한도는 2억", "그냥 옮기면 세금이에요"], beats=_beats(3)),
            Scene("통장만 옮기면 내 돈이 줄어요", duration=9, captions=["통장만 옮기면 세금이에요", "한도가 바로 깎여요"], beats=_beats(3)),
            Scene("내 전세금부터 한도를 봐야 해요", duration=9, captions=["내 전세금 한도부터", "2억을 넘기면 흔들려요"], beats=_beats(3)),
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
            write_caption_png("전세금 2억이요", path, width=1080)
            from PIL import Image

            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            self.assertEqual(img.getpixel((0, 0))[3], 0)
            self.assertEqual(img.getpixel((1079, 0))[3], 0)
            self.assertEqual(img.getpixel((0, img.size[1] - 1))[3], 0)

    def test_caption_follows_scene_time(self):
        scene = _script().scenes[0]
        self.assertEqual(caption_at(scene, 1.5), "무이자 2억까지라고요?")
        self.assertEqual(caption_at(scene, 7.5), "전세금을 부모에게 빌리면")


class MediaPathTests(unittest.TestCase):
    def test_uses_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "scene-01.png").write_bytes(b"png")
            self.assertEqual(scene_media_path(job, 1).name, "scene-01.png")

    def test_uses_beat_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "beat-03.png").write_bytes(b"png")
            self.assertEqual(beat_media_path(job, 3).name, "beat-03.png")

    def test_mp4_alone_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "beat-02.mp4").write_bytes(b"mp4")
            self.assertIsNone(beat_media_path(job, 2))

    def test_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(beat_media_path(Path(tmp), 1))


class MissingAssetsTests(unittest.TestCase):
    def test_missing_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(
                json.dumps(_script().to_json(), ensure_ascii=False),
                encoding="utf-8",
            )
            gaps = missing_agent_assets(job)
        self.assertTrue(any("beat-01.png" in g for g in gaps))
        self.assertTrue(any("beat-16.png" in g for g in gaps))

    def test_png_is_enough(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(
                json.dumps(_script().to_json(), ensure_ascii=False),
                encoding="utf-8",
            )
            for i in range(1, 17):
                (job / ("beat-%02d.png" % i)).write_bytes(b"x")
            (job / "thumb.png").write_bytes(b"x")
            self.assertEqual(missing_agent_assets(job), [])

    def test_missing_thumb(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(
                json.dumps(_script().to_json(), ensure_ascii=False),
                encoding="utf-8",
            )
            for i in range(1, 17):
                (job / ("beat-%02d.png" % i)).write_bytes(b"x")
            gaps = missing_agent_assets(job)
        self.assertTrue(any("thumb.png" in g for g in gaps))

    def test_missing_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            gaps = missing_agent_assets(Path(tmp))
        self.assertTrue(any("script.json" in g for g in gaps))


if __name__ == "__main__":
    unittest.main()
