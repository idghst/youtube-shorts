from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_centers_bar_at_lower_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_bar_is_full_width_black_with_centered_ink(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("전세 3만 가구가 줄었어요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            self.assertGreater(img.size[1], 80)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLessEqual(left[0], 20)
            self.assertLessEqual(left[1], 20)
            self.assertLessEqual(left[2], 20)
            self.assertGreaterEqual(left[3], 250)
            self.assertLessEqual(right[0], 20)
            self.assertLessEqual(right[1], 20)
            self.assertLessEqual(right[2], 20)

            opaque = img.split()[3].point(lambda a: 255 if a > 40 else 0)
            ink = Image.new("L", img.size, 0)
            pixels = img.load()
            dest = ink.load()
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = pixels[x, y]
                    if a > 40 and (r > 40 or g > 40 or b > 40):
                        dest[x, y] = 255
            box = ink.getbbox()
            self.assertIsNotNone(box)
            ink_cx = (box[0] + box[2]) / 2
            ink_cy = (box[1] + box[3]) / 2
            self.assertAlmostEqual(ink_cx, img.size[0] / 2, delta=40)
            self.assertAlmostEqual(ink_cy, img.size[1] / 2, delta=18)
            self.assertIsNotNone(opaque.getbbox())


if __name__ == "__main__":
    unittest.main()
