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
            write_caption_png("가계빚이 더 커졌어요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((img.size[0] - 1, img.size[1] // 2))
            self.assertLessEqual(left[0], 20)
            self.assertLessEqual(left[1], 20)
            self.assertLessEqual(left[2], 20)
            self.assertGreaterEqual(left[3], 200)
            self.assertEqual(left[:3], right[:3])

            alpha = img.split()[-1]
            # 글자(불투명 + 흰/금)만 모아 잉크 박스
            px = img.load()
            xs, ys = [], []
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = px[x, y]
                    if a > 200 and (r > 180 or g > 180):
                        xs.append(x)
                        ys.append(y)
            self.assertTrue(xs)
            ink_cx = (min(xs) + max(xs)) / 2
            ink_cy = (min(ys) + max(ys)) / 2
            self.assertLess(abs(ink_cx - img.size[0] / 2), 40)
            self.assertLess(abs(ink_cy - img.size[1] / 2), 12)
            self.assertGreater(alpha.getpixel((2, 2)), 200)
