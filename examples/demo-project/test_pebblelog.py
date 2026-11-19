# -*- coding: utf-8 -*-
"""PebbleLog 的最小自测（示例台架）。"""
import os
import tempfile
import unittest

import pebblelog as pl


class TestPebbleLog(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="pebble_")
        self.path = os.path.join(self.dir, "notes.txt")

    def test_add_then_read(self):
        pl.add_note("第一条", self.path)
        pl.add_note("第二条", self.path)
        self.assertEqual(pl.read_notes(self.path), ["第一条", "第二条"])

    def test_empty_file(self):
        self.assertEqual(pl.read_notes(self.path), [])


if __name__ == "__main__":
    unittest.main()
