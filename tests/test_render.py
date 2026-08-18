from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_is_two_thirds_full_width(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_bar_is_full_width_black_with_centered_ink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("정기예금 열 중 여섯이", path, width=1080)
            img = Image.open(path).convert("RGBA")
            try:
                self.assertEqual(img.size[0], 1080)
                left = img.getpixel((0, img.size[1] // 2))
                right = img.getpixel((1079, img.size[1] // 2))
                self.assertEqual(left[:3], (0, 0, 0))
                self.assertEqual(right[:3], (0, 0, 0))
                pixels = list(img.getdata())
                alpha = [p[3] for p in pixels if p[3] > 20 and p[:3] != (0, 0, 0)]
                self.assertTrue(alpha)
                ys = []
                for y in range(img.size[1]):
                    for x in range(img.size[0]):
                        r, g, b, a = img.getpixel((x, y))
                        if a > 20 and (r, g, b) != (0, 0, 0):
                            ys.append(y)
                            break
                self.assertTrue(ys)
                mid = (min(ys) + max(ys)) / 2
                self.assertLess(abs(mid - img.size[1] / 2), 12)
            finally:
                img.close()

    def test_short_caption_stays_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("서울로 더 몰렸어요", path, width=1080)
            with Image.open(path) as img:
                self.assertLess(img.size[1], 180)


if __name__ == "__main__":
    unittest.main()
