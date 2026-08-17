from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shorts.render import write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_full_width_black_bar_centers_ink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("가계빚 2000조요", path, width=1080)
            from PIL import Image

            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            px = img.load()
            self.assertEqual(px[0, img.size[1] // 2][:3], (0, 0, 0))
            self.assertEqual(px[1079, img.size[1] // 2][:3], (0, 0, 0))
            ink = [xy for xy in [(x, y) for y in range(img.size[1]) for x in range(img.size[0])] if px[xy][0] > 200]
            self.assertTrue(ink)
            xs = [x for x, _y in ink]
            ys = [y for _x, y in ink]
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            self.assertAlmostEqual(cx, 540, delta=40)
            self.assertAlmostEqual(cy, img.size[1] / 2, delta=8)


if __name__ == "__main__":
    unittest.main()
