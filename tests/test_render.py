from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_is_two_thirds_full_width(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_bar_is_full_width_black_and_ink_centered(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("이자가 더 문제예요", path, width=1080)
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

        ink = []
        for y in range(img.size[1]):
            for x in range(img.size[0]):
                r, g, b, a = img.getpixel((x, y))
                if r + g + b > 80:
                    ink.append((x, y))
        self.assertTrue(ink)
        xs = [p[0] for p in ink]
        ys = [p[1] for p in ink]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        self.assertLess(abs(cx - img.size[0] / 2), 40)
        self.assertLess(abs(cy - img.size[1] / 2), 18)


if __name__ == "__main__":
    unittest.main()
