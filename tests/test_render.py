from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_sits_at_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_bar_is_full_width_black_and_centered(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("등기부부터 봐야 해요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            self.assertGreaterEqual(img.size[1], 100)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLessEqual(sum(left[:3]), 20)
            self.assertEqual(left[3], 255)
            self.assertLessEqual(sum(right[:3]), 20)
            alpha = img.split()[-1]
            ink = [p for p in img.getdata() if p[0] > 200 and p[3] > 200]
            self.assertTrue(ink)
            box = None
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = img.getpixel((x, y))
                    if r > 200 and a > 200:
                        if box is None:
                            box = [x, y, x, y]
                        else:
                            box[0] = min(box[0], x)
                            box[1] = min(box[1], y)
                            box[2] = max(box[2], x)
                            box[3] = max(box[3], y)
            self.assertIsNotNone(box)
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2
            self.assertAlmostEqual(cx, 540, delta=40)
            self.assertAlmostEqual(cy, img.size[1] / 2, delta=18)
            self.assertIsNotNone(alpha.getbbox())


if __name__ == "__main__":
    unittest.main()
