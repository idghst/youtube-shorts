from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from shorts.render import (
    CAPTION_OVERLAY,
    write_caption_png,
    wrap_caption_lines,
)


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_centers_bar_at_lower_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_wrap_keeps_short_line(self):
        font = ImageFont.load_default()
        draw = ImageDraw.Draw(Image.new("RGBA", (200, 20), (0, 0, 0, 0)))
        self.assertEqual(wrap_caption_lines("집값은 왜 더 뛰어요?", draw, font, 2000), ["집값은 왜 더 뛰어요?"])

    def test_wrap_only_when_wider_than_max(self):
        font = ImageFont.load_default()
        draw = ImageDraw.Draw(Image.new("RGBA", (40, 20), (0, 0, 0, 0)))
        lines = wrap_caption_lines("가나다라마바사아자차카타파하", draw, font, 20)
        self.assertGreaterEqual(len(lines), 2)
        self.assertLessEqual(len(lines), 2)

    def test_caption_png_is_full_width_black_with_centered_ink(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cap.png"
            write_caption_png("집값은 왜 더 뛰어요?", dest, width=1080)
            img = Image.open(dest).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            corners = [img.getpixel((0, 0)), img.getpixel((1079, 0)), img.getpixel((0, img.size[1] - 1))]
            self.assertTrue(all(px[0] < 20 and px[1] < 20 and px[2] < 20 and px[3] > 200 for px in corners))
            ys = []
            xs = []
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = img.getpixel((x, y))
                    if a > 200 and (r > 200 or g > 180):
                        ys.append(y)
                        xs.append(x)
            self.assertTrue(ys)
            mid_y = (min(ys) + max(ys)) / 2
            mid_x = (min(xs) + max(xs)) / 2
            self.assertAlmostEqual(mid_y, img.size[1] / 2, delta=18)
            self.assertAlmostEqual(mid_x, 540, delta=40)


if __name__ == "__main__":
    unittest.main()
