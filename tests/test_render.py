from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shorts.render import CAPTION_OVERLAY, wrap_caption, write_caption_png


def _bright_rows(img: Image.Image, threshold: int = 80) -> list[int]:
    rows = []
    pix = img.convert("RGBA").load()
    w, h = img.size
    for y in range(h):
        if any(pix[x, y][0] + pix[x, y][1] + pix[x, y][2] >= threshold * 3 for x in range(w)):
            rows.append(y)
    return rows


class CaptionStyleTests(unittest.TestCase):
    def test_overlay_sits_at_lower_two_thirds(self):
        self.assertEqual(CAPTION_OVERLAY, "overlay=0:H*2/3-h/2")

    def test_short_caption_does_not_wrap(self):
        self.assertEqual(wrap_caption("가계빚 2000조요", width=1080), ["가계빚 2000조요"])

    def test_bar_is_full_width_black(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("가계빚 2000조요", path, width=1080)
            img = Image.open(path).convert("RGBA")
            self.assertEqual(img.size[0], 1080)
            pix = img.load()
            for x in (0, 540, 1079):
                r, g, b, a = pix[x, img.size[1] // 2]
                self.assertLess(r + g + b, 40, msg="bar must be black")
                self.assertGreaterEqual(a, 250, msg="bar must be opaque")

    def test_ink_is_vertically_centered_in_bar(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("가계빚 2000조요", path, width=1080)
            img = Image.open(path)
            rows = _bright_rows(img)
            self.assertTrue(rows, "caption ink missing")
            ink_mid = (rows[0] + rows[-1]) / 2
            self.assertLess(abs(ink_mid - img.size[1] / 2), img.size[1] * 0.12)
