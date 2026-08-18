from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from shorts.copy import description_body, studio_title, validate_script
from shorts.models import Scene, Script, Style, load_script

ANCHOR = (
    "the same silver-haired Korean woman in a cream cardigan, "
    "painterly animated film, luminous dusk sky"
)
FACE = (
    "same late-60s Korean woman, silver bob to the jaw, "
    "soft eye wrinkles, round cheeks, do not change age"
)


def _prompt(beat: str) -> str:
    return (
        "%s. %s. %s Soft theatrical animation. "
        "Vertical 9:16, empty lower third."
        % (ANCHOR, FACE, beat)
    )


def _ok(**overrides) -> Script:
    scenes = [
        Scene("가계빚이 2000조를 넘겼어요. 이자가 더 문제예요", _prompt("She reads an unmarked envelope by the window."), 7, ["이자가 더 붙는다고요?", "가계빚이 2000조예요"]),
        Scene("영끌과 빚투가 밀어 올렸어요", _prompt("She sits at the table and opens the envelope."), 8, ["영끌이랑 빚투가 밀었어요", "늘분의 열 중 여덟이 주담대"]),
        Scene("한도를 넓히면 더 늘 수 있어요", _prompt("She walks down wet dusk streets holding the letter."), 8, ["한도를 넓히면 더 늘어요", "연체는 10년 만에 최고예요"]),
        Scene("금리가 오르면 이자만 3조가 더 붙어요", _prompt("City lights reflect on puddles as she pauses."), 7, ["금리 오르면 이자만", "3조가 더 붙어요"]),
        Scene("빚이 월급보다 먼저 커지면 흔들려요", _prompt("She looks at the hillside town, hand on her chest."), 6, ["빚이 월급보다 먼저 컸어요", "내 이자부터 흔들려요"]),
    ]
    data = dict(
        title="가계빚 2000조, 이자만 3조 더?",
        description="영끌이랑 빚투로 가계빚이 처음 2000조를 넘겼어요. 늘어난 빚의 열 중 여덟이 주택담보대출이고, 금리가 오르면 이자만 3조가 더 붙는다는 얘기예요.",
        tags=["가계빚", "주담대", "영끌", "금리인상"],
        hashtags="#가계빚 #주담대 #영끌 #금리인상 #돈이웃 #쇼츠 #shorts",
        scenes=scenes,
        style=Style(anchor=ANCHOR, face=FACE, mood="quiet dusk hillside town"),
    )
    data.update(overrides)
    return Script(**data)


class CopyValidateTests(unittest.TestCase):
    def test_ok_script_passes(self):
        validate_script(_ok())

    def test_rejects_formal_title_and_meta(self):
        script = _ok(title="가계빚이 사상 처음으로 2000조를 넘었습니다")
        with self.assertRaises(ValueError) as ctx:
            validate_script(script)
        self.assertIn("입니다", str(ctx.exception))

    def test_rejects_hashtag_in_title(self):
        with self.assertRaises(ValueError):
            validate_script(_ok(title="가계빚 2000조 #Shorts"))

    def test_rejects_copied_first_caption(self):
        scenes = _ok().scenes
        scenes[0].captions = ["가계빚 2000조, 이자만 3조 더?", "이자가 더 문제예요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("첫 자막", str(ctx.exception))

    def test_rejects_banned_meta_caption(self):
        scenes = _ok().scenes
        scenes[2].captions = ["헤드라인에 숫자는 없습니다", "풀가동이라는 표현입니다"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("금지어", str(ctx.exception))

    def test_rejects_too_many_formal_endings(self):
        scenes = _ok().scenes
        for scene in scenes:
            scene.captions = [c.replace("요", "습니다") if c.endswith("요") else c + "입니다" for c in scene.captions]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("습니다", str(ctx.exception))

    def test_rejects_title_without_number_or_question(self):
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(title="가계빚이 또 늘었다는 얘기"))
        self.assertIn("숫자", str(ctx.exception))

    def test_rejects_first_caption_that_is_not_a_hook(self):
        scenes = _ok().scenes
        scenes[0].captions = ["가계빚이 2000조예요", "이자가 더 문제예요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("훅", str(ctx.exception))

    def test_rejects_last_scene_without_personal_stake(self):
        scenes = _ok().scenes
        scenes[-1].text = "부채 규모가 커졌어요"
        scenes[-1].captions = ["부채가 또 늘었어요", "숫자가 커졌어요"]
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("내 돈", str(ctx.exception))

    def test_rejects_photoreal_ai_face_prompt(self):
        scenes = _ok().scenes
        scenes[0].image_prompt = ANCHOR + " " + FACE + " A photorealistic cinematic photo of a worried Korean senior."
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("실사", str(ctx.exception))

    def test_rejects_manga_prompt(self):
        scenes = _ok().scenes
        scenes[0].image_prompt = ANCHOR + " " + FACE + " manga chibi comic panel with speed lines."
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("망가", str(ctx.exception))

    def test_rejects_prompt_without_style_anchor(self):
        scenes = _ok().scenes
        scenes[1].image_prompt = "A painterly animated film of a woman walking at dusk. Luminous sky."
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("anchor", str(ctx.exception))

    def test_load_script_runs_copy_check(self):
        script = _ok()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(script.to_json(), ensure_ascii=False), encoding="utf-8")
            loaded = load_script(path)
            self.assertEqual(loaded.title, script.title)
            self.assertEqual(loaded.style.anchor, ANCHOR)
            self.assertEqual(loaded.style.face, FACE)
            self.assertIn(ANCHOR, loaded.scenes[0].image_prompt)
            self.assertIn(FACE, loaded.scenes[0].image_prompt)

    def test_rejects_missing_image_prompt(self):
        script = _ok()
        payload = script.to_json()
        payload["scenes"][0].pop("image_prompt", None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_script(path)
        self.assertIn("image_prompt", str(ctx.exception))

    def test_rejects_prompt_without_face_lock(self):
        scenes = _ok().scenes
        scenes[2].image_prompt = ANCHOR + ". She walks at dusk. Soft theatrical animation. Luminous sky."
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("face", str(ctx.exception))

    def test_rejects_age_drift_across_scenes(self):
        scenes = _ok().scenes
        scenes[1].image_prompt = (
            ANCHOR + " " + FACE + " A youthful 20s woman walks in the rain. Soft theatrical animation."
        )
        with self.assertRaises(ValueError) as ctx:
            validate_script(_ok(scenes=scenes))
        self.assertIn("얼굴", str(ctx.exception))

    def test_rejects_clip_longer_than_ten(self):
        scenes = _ok().scenes
        scenes[0].duration = 12
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(_ok(scenes=scenes).to_json(), ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_script(path)
        self.assertIn("5~10", str(ctx.exception))

    def test_description_body_strips_hashtags_and_disclaimer(self):
        raw = "본문이에요.\n\n#가계빚 #쇼츠\n정보 제공이 목적이며 투자 권유가 아닙니다."
        self.assertEqual(description_body(raw), "본문이에요.")

    def test_studio_title_strips_hash(self):
        self.assertEqual(studio_title("가계빚 2000조 #Shorts"), "가계빚 2000조")


if __name__ == "__main__":
    unittest.main()
