from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from shorts.copy import validate_script
from shorts.models import Beat, Scene, Script, Style, beat_image_path, load_script
from shorts.render import required_beat_files, write_caption_png
from shorts.run import missing_agent_assets


def _beat_script() -> Script:
    limb = "exactly two hands and two feet, no extra limbs"
    style = Style(
        anchor="the same silver-haired Korean woman in a cream cardigan, painterly animated film, luminous dusk sky",
        face="same late-60s Korean woman, silver bob to the jaw, soft eye wrinkles, round cheeks, do not change age",
        wardrobe="same cream cardigan over ivory blouse every beat",
        mood="quiet hillside village, late summer dusk",
    )
    scenes = []
    for i in range(5):
        beats = [
            Beat(image_prompt="%s. %s. %s. %s. She looks at a paper. Soft theatrical animation. Vertical 9:16." % (style.anchor, style.face, style.wardrobe, limb))
            for _ in range(4)
        ]
        scenes.append(
            Scene(
                text="장면 %d 텍스트예요" % (i + 1),
                image_prompt=beats[0].image_prompt,
                duration=12,
                captions=["훅인가요" if i == 0 else "숫자 하나예요", "내 돈과 닿아요"],
                beats=beats,
            )
        )
    return Script(
        title="집값 올라도 이자는 그대로?",
        description="은행 이자가 월급을 먼저 가져가면 남는 돈이 줄어들어요. 한 달 통장만 보면 체감이 바로 나요.",
        tags=["주담대", "금리", "이자"],
        hashtags="#주담대 #금리 #이자 #돈이웃 #쇼츠 #shorts",
        scenes=scenes,
        style=style,
    )


class BeatPathTests(unittest.TestCase):
    def test_beat_image_path_uses_global_index(self):
        self.assertEqual(beat_image_path(Path("/tmp/job"), 1).name, "beat-01.png")
        self.assertEqual(beat_image_path(Path("/tmp/job"), 20).name, "beat-20.png")


class BeatScriptTests(unittest.TestCase):
    def test_load_script_keeps_beats_and_style(self):
        script = _beat_script()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(script.to_json(), ensure_ascii=False), encoding="utf-8")
            loaded = load_script(path)
        self.assertEqual(len(loaded.scenes[0].beats), 4)
        self.assertGreaterEqual(len(loaded.style.anchor), 24)
        self.assertEqual(required_beat_files(loaded), ["beat-%02d.png" % i for i in range(1, 21)])

    def test_rejects_wrong_beat_count(self):
        script = _beat_script()
        script.scenes[0].beats = script.scenes[0].beats[:3]
        with self.assertRaises(ValueError) as ctx:
            validate_script(script)
        self.assertIn("beat", str(ctx.exception).lower())

    def test_rejects_duration_not_multiple_of_three(self):
        script = _beat_script()
        script.scenes[0].duration = 11
        script.scenes[0].beats = script.scenes[0].beats[:3] + script.scenes[0].beats[:1]
        # 11 is not /3; even if we keep 4 beats it should fail
        script.scenes[0].beats = script.scenes[0].beats[:4]
        with self.assertRaises(ValueError):
            validate_script(script)

    def test_missing_assets_lists_beat_files(self):
        script = _beat_script()
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "script.json").write_text(json.dumps(script.to_json(), ensure_ascii=False), encoding="utf-8")
            gaps = missing_agent_assets(job)
        self.assertIn("beat-01.png", " ".join(gaps))
        self.assertIn("beat-20.png", " ".join(gaps))
        self.assertNotIn("scene-01.png", " ".join(gaps))


class CaptionNoBoxTests(unittest.TestCase):
    def test_caption_png_has_no_solid_black_bar(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("이자만 더 붙어요", path, width=1080)
            from PIL import Image

            img = Image.open(path).convert("RGBA")
            blacks = 0
            total = img.width * img.height
            for px in img.getdata():
                if px[3] > 200 and px[0] < 20 and px[1] < 20 and px[2] < 20:
                    blacks += 1
            self.assertLess(blacks / total, 0.12, "자막 검정 박스가 너무 넓음")


if __name__ == "__main__":
    unittest.main()
