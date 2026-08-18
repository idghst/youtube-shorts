from __future__ import annotations

import unittest

from shorts.render import _wrap_caption_lines


class DummyDraw:
    def textbbox(self, _xy, text, font=None, stroke_width=0):
        return (0, 0, len(text) * 10, 20)


class CaptionWrapTests(unittest.TestCase):
    def test_fits_without_wrap(self):
        self.assertEqual(_wrap_caption_lines("가계빚 2000조요", DummyDraw(), None, 1000), ["가계빚 2000조요"])

    def test_wraps_only_when_too_wide(self):
        lines = _wrap_caption_lines("가" * 40, DummyDraw(), None, 200)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(lines))
