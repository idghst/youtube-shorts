from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shorts.render import _caption_font, _line_width, _wrap_caption, write_caption_png


class CaptionWrapTests(unittest.TestCase):
    def test_does_not_wrap_when_line_fits(self):
        from PIL import ImageDraw

        font = _caption_font(76)
        probe = Image.new("RGBA", (1080, 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(probe)
        text = "관리비 할인카드, 왜 더 나가요?"
        self.assertLessEqual(_line_width(draw, text, font)[0], 1080 - 72)
        self.assertEqual(_wrap_caption(text, draw, font, 1080 - 72), [text])

    def test_full_width_black_bar_and_centered_ink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("이자가 더 문제예요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertEqual(left[:3], (0, 0, 0))
            self.assertEqual(right[:3], (0, 0, 0))
            ys = []
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = img.getpixel((x, y))
                    if a > 200 and (r > 200 or g > 200):
                        ys.append(y)
                        break
            self.assertTrue(ys)
            mid = (min(ys) + max(ys)) / 2
            self.assertLess(abs(mid - img.size[1] / 2), img.size[1] * 0.18)
