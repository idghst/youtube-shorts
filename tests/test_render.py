from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shorts.render import write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_full_width_black_bar_and_centered_ink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("금리 오르면 이자만", path, width=1080)
            img = Image.open(path).convert("RGBA")
        self.assertEqual(img.size[0], 1080)
        left = img.getpixel((0, img.size[1] // 2))
        right = img.getpixel((1079, img.size[1] // 2))
        self.assertLessEqual(left[0] + left[1] + left[2], 20)
        self.assertEqual(left[3], 255)
        self.assertLessEqual(right[0] + right[1] + right[2], 20)
        bbox = img.getbbox()
        self.assertIsNotNone(bbox)
        ink = img.crop(bbox)
        bright = [
            (x, y)
            for y in range(ink.size[1])
            for x in range(ink.size[0])
            if sum(ink.getpixel((x, y))[:3]) > 400
        ]
        self.assertTrue(bright)
        xs = [p[0] for p in bright]
        ys = [p[1] for p in bright]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        self.assertAlmostEqual(cx, ink.size[0] / 2, delta=40)
        self.assertAlmostEqual(cy, ink.size[1] / 2, delta=18)

    def test_short_caption_stays_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("이자만 더 붙어요", path, width=1080)
            img = Image.open(path).convert("RGBA")
        self.assertLess(img.size[1], 160)


if __name__ == "__main__":
    unittest.main()
