from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_full_width_black_bar_centers_text(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("병원비 5137만원 본전", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLessEqual(left[0], 20)
            self.assertLessEqual(left[1], 20)
            self.assertLessEqual(left[2], 20)
            self.assertGreaterEqual(left[3], 200)
            self.assertEqual(left[:3], right[:3])

            alpha = [px[3] for px in img.getdata()]
            content = [
                (i % 1080, i // 1080)
                for i, a in enumerate(alpha)
                if a > 250
            ]
            self.assertTrue(content)
            xs = [x for x, _y in content]
            ys = [y for _x, y in content]
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            self.assertLess(abs(cx - 540), 80)
            self.assertLess(abs(cy - img.size[1] / 2), 18)
