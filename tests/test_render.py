from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from shorts.render import _caption_lines, write_caption_png


class CaptionStyleTests(unittest.TestCase):
    def test_does_not_wrap_when_line_fits(self):
        class Dummy:
            pass

        dummy = Dummy()
        with patch("shorts.render._line_width", return_value=(400, 40)):
            lines = _caption_lines("전세보증금이 묶였어요", dummy, dummy, 900)
        self.assertEqual(lines, ["전세보증금이 묶였어요"])

    def test_full_width_black_bar(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.png"
            write_caption_png("이자만 더 붙어요", path, width=1080)
            img = Image.open(path)
            self.assertEqual(img.size[0], 1080)
            self.assertGreaterEqual(img.size[1], 100)
            left = img.getpixel((0, img.size[1] // 2))
            right = img.getpixel((1079, img.size[1] // 2))
            self.assertLessEqual(left[0], 20)
            self.assertLessEqual(right[0], 20)
            self.assertGreaterEqual(left[3], 200)


if __name__ == "__main__":
    unittest.main()
