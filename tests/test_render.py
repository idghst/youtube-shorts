from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_sits_at_lower_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_bar_is_full_width_black_with_centered_ink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("가계빚 2000조요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((img.size[0] - 1, img.size[1] // 2))
            self.assertLessEqual(left[0], 8)
            self.assertLessEqual(left[1], 8)
            self.assertLessEqual(left[2], 8)
            self.assertGreaterEqual(left[3], 250)
            self.assertEqual(left[:3], right[:3])

            ink = [
                (x, y)
                for y in range(img.size[1])
                for x in range(img.size[0])
                if img.getpixel((x, y))[0] > 200 or img.getpixel((x, y))[1] > 180
            ]
            self.assertTrue(ink)
            ys = [y for _x, y in ink]
            xs = [x for x, _y in ink]
            mid_y = (min(ys) + max(ys)) / 2
            mid_x = (min(xs) + max(xs)) / 2
            self.assertAlmostEqual(mid_y, img.size[1] / 2, delta=12)
            self.assertAlmostEqual(mid_x, img.size[0] / 2, delta=40)


if __name__ == "__main__":
    unittest.main()
