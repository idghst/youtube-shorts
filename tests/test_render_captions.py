from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shorts.render import write_caption_png


class CaptionPngTests(unittest.TestCase):
    def test_full_width_black_bar_centers_ink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("초고령사회가 됐어요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            self.assertGreaterEqual(img.size[1], 80)
            left = [img.getpixel((0, y))[:3] for y in range(img.size[1])]
            right = [img.getpixel((1079, y))[:3] for y in range(img.size[1])]
            self.assertTrue(all(p == (0, 0, 0) for p in left))
            self.assertTrue(all(p == (0, 0, 0) for p in right))
            pixels = img.load()
            xs, ys = [], []
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = pixels[x, y]
                    if a > 20 and (r, g, b) != (0, 0, 0):
                        xs.append(x)
                        ys.append(y)
            self.assertTrue(xs)
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            self.assertLess(abs(cx - 540), 40)
            self.assertLess(abs(cy - img.size[1] / 2), 18)


if __name__ == "__main__":
    unittest.main()
