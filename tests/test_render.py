from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_sits_at_lower_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_is_full_width_black_bar(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("가계빚 2000조요", path, width=1080)
            img = Image.open(path).convert("RGBA")
        self.assertEqual(img.size[0], 1080)
        self.assertGreaterEqual(img.size[1], 100)
        left = img.getpixel((0, img.size[1] // 2))
        right = img.getpixel((img.size[0] - 1, img.size[1] // 2))
        self.assertLessEqual(left[0], 20)
        self.assertLessEqual(left[1], 20)
        self.assertLessEqual(left[2], 20)
        self.assertGreaterEqual(left[3], 250)
        self.assertEqual(left[:3], right[:3])

    def test_caption_ink_is_vertically_centered(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("이자가 더 문제예요", path, width=1080)
            img = Image.open(path).convert("RGBA")
        bright = []
        for y in range(img.size[1]):
            for x in range(0, img.size[0], 4):
                r, g, b, a = img.getpixel((x, y))
                if a > 200 and (r + g + b) > 400:
                    bright.append(y)
        self.assertTrue(bright)
        mid = sum(bright) / len(bright)
        self.assertLess(abs(mid - img.size[1] / 2), img.size[1] * 0.18)


if __name__ == "__main__":
    unittest.main()
