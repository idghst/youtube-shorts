from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from shorts.render import (
    CAPTION_OVERLAY,
    write_caption_png,
    wrap_caption_lines,
    _caption_font,
    _line_width,
)


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_is_full_width_at_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_wrap_keeps_short_line(self):
        font = _caption_font(76)
        probe = Image.new("RGBA", (1080, 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(probe)
        lines = wrap_caption_lines("빚이 월급보다 먼저 컸어요", draw, font, 1008)
        self.assertEqual(lines, ["빚이 월급보다 먼저 컸어요"])
        self.assertLessEqual(_line_width(draw, lines[0], font)[0], 1008)

    def test_full_width_black_bar_centers_ink(self):
        font = _caption_font(76)
        self.assertIsNotNone(font)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("금리 오르면 이자만", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLessEqual(left[0], 20)
            self.assertLessEqual(left[1], 20)
            self.assertLessEqual(left[2], 20)
            self.assertGreaterEqual(left[3], 250)
            self.assertEqual(left[:3], right[:3])
            pixels = list(img.get_flattened_data()) if hasattr(img, "get_flattened_data") else list(img.getdata())
            ys = [
                i // img.size[0]
                for i, px in enumerate(pixels)
                if px[3] > 20 and px[0] > 200
            ]
            self.assertTrue(ys)
            mid = (min(ys) + max(ys)) / 2
            self.assertLess(abs(mid - img.size[1] / 2), img.size[1] * 0.18)


if __name__ == "__main__":
    unittest.main()
