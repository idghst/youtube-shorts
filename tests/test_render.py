from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import write_caption_png


class CaptionPngTests(unittest.TestCase):
    def test_full_width_black_bar_centers_ink(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("금리 오르면 이자만", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            self.assertGreater(img.size[1], 40)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertEqual(left[:3], (0, 0, 0))
            self.assertEqual(right[:3], (0, 0, 0))
            ink = img.getbbox()
            self.assertIsNotNone(ink)
            ink_cx = (ink[0] + ink[2]) / 2
            ink_cy = (ink[1] + ink[3]) / 2
            self.assertLess(abs(ink_cx - 540), 40)
            self.assertLess(abs(ink_cy - img.size[1] / 2), 12)
