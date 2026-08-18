from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shorts.render import CAPTION_OVERLAY, write_caption_png


def _bright_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    pixels = img.load()
    w, h = img.size
    left, top, right, bottom = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a > 20 and (r + g + b) > 80:
                found = True
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)
    if not found:
        raise AssertionError("밝은 글자 픽셀이 없음")
    return left, top, right, bottom


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_is_full_width_at_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_bar_is_full_width_black_and_ink_centered(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("가계빚 2000조요", path, width=1080)
            img = Image.open(path).convert("RGBA")
        self.assertEqual(img.size[0], 1080)
        pixels = img.load()
        for x in (0, 1079):
            r, g, b, a = pixels[x, img.size[1] // 2]
            self.assertLessEqual(r + g + b, 30)
            self.assertGreaterEqual(a, 250)
        left, top, right, bottom = _bright_bbox(img)
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        self.assertLess(abs(cx - 540), 40)
        self.assertLess(abs(cy - img.size[1] / 2), 8)

    def test_short_caption_stays_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            short = Path(tmp) / "short.png"
            long = Path(tmp) / "long.png"
            write_caption_png("한도를 넓히면 더 늘어요", short, width=1080)
            write_caption_png("한도를 넓히면 더 늘어요 한도를 넓히면 더 늘어요 한도를 넓히면", long, width=1080)
            with Image.open(short) as short_img, Image.open(long) as long_img:
                short_h = short_img.size[1]
                long_h = long_img.size[1]
        self.assertLess(short_h, long_h)


if __name__ == "__main__":
    unittest.main()
