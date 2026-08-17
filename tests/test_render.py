from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_is_two_thirds_full_width(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_bar_is_full_width_black_and_text_centered(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("전세가 줄고 월세가 늘어요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLessEqual(left[0], 20)
            self.assertLessEqual(left[1], 20)
            self.assertLessEqual(left[2], 20)
            self.assertGreaterEqual(left[3], 200)
            self.assertLessEqual(right[0], 20)
            self.assertLessEqual(right[1], 20)
            self.assertLessEqual(right[2], 20)
            pixels = img.load()
            ink = []
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = pixels[x, y]
                    if a > 200 and (r + g + b) > 400:
                        ink.append((x, y))
            self.assertTrue(ink)
            cx = sum(p[0] for p in ink) / len(ink)
            cy = sum(p[1] for p in ink) / len(ink)
            self.assertAlmostEqual(cx, img.size[0] / 2, delta=80)
            self.assertAlmostEqual(cy, img.size[1] / 2, delta=18)


if __name__ == "__main__":
    unittest.main()
