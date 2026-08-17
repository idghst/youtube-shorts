from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shorts.render import CAPTION_OVERLAY, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_sits_at_lower_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_caption_bar_is_full_width_black_with_centered_ink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("관리비가 매달 20만원이요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            self.assertGreater(img.size[1], 80)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLessEqual(sum(left[:3]), 20)
            self.assertLessEqual(sum(right[:3]), 20)
            def _bright_rows(y0, y1):
                n = 0
                for y in range(y0, y1):
                    for x in range(80, 1000, 4):
                        px = img.getpixel((x, y))
                        if px[0] > 180 and px[1] > 180:
                            n += 1
                return n

            h = img.size[1]
            mid = _bright_rows(h // 4, (h * 3) // 4)
            bottom = _bright_rows((h * 3) // 4, h)
            top = _bright_rows(0, h // 4)
            self.assertGreater(mid, 20, "글자가 바 세로 중앙에 있어야 함")
            self.assertLess(bottom, mid // 2, "글자가 바 하단에 몰리면 안 됨")
            self.assertLess(top, mid, "글자가 바 상단에만 있으면 안 됨")


if __name__ == "__main__":
    unittest.main()
