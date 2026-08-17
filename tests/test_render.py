from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_sits_at_lower_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_bar_is_full_width_black_with_centered_ink(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("통장을 넘겨준 사람도", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLessEqual(sum(left[:3]), 20)
            self.assertLessEqual(sum(right[:3]), 20)
            alpha = img.split()[3]
            ink = alpha.point(lambda a: 255 if a > 20 else 0).getbbox()
            self.assertIsNotNone(ink)
            ink_cx = (ink[0] + ink[2]) / 2
            ink_cy = (ink[1] + ink[3]) / 2
            self.assertAlmostEqual(ink_cx, 1080 / 2, delta=40)
            self.assertAlmostEqual(ink_cy, img.size[1] / 2, delta=12)


if __name__ == "__main__":
    unittest.main()
