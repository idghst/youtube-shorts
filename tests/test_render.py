from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_sits_at_lower_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_is_full_width_black_bar_with_centered_ink(self):
        from PIL import Image

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("연체가 10년 만에 최고예요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLess(left[0] + left[1] + left[2], 40)
            self.assertGreaterEqual(left[3], 200)
            self.assertLess(right[0] + right[1] + right[2], 40)
            alpha = img.split()[-1]
            ink = alpha.getbbox()
            self.assertIsNotNone(ink)
            ink_cx = (ink[0] + ink[2]) / 2
            ink_cy = (ink[1] + ink[3]) / 2
            self.assertLess(abs(ink_cx - 540), 40)
            self.assertLess(abs(ink_cy - img.size[1] / 2), 18)


if __name__ == "__main__":
    unittest.main()
