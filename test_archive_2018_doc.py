# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import archive_2018  # noqa: E402
import lawnext_2018  # noqa: E402
import tig_history  # noqa: E402


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = archive_2018.load()
        history = tig_history.load()
        lawnext = lawnext_2018.load()
        cls.rows = archive_2018.rows(cls.archive, history, lawnext)
        cls.summary = archive_2018.summary(cls.archive, history, lawnext)
        with open(os.path.join(HERE, "docs", "tig-history.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_table_is_current(self):
        self.assertIn(archive_2018.markdown(self.rows), self.doc)

    def test_doc_figures(self):
        s = self.summary
        self.assertIn("holds the %d amounts they print" % s["amounts"], self.doc)
        self.assertIn("All %d archived amounts are the same as LSC prints today" % s["same_as_today"], self.doc)
        for quote in s["since_2000"].values():
            self.assertIn(quote.split("funded ")[1].rstrip("."), self.doc)
        self.assertIn("python archive_2018.py", self.doc)
        self.assertIn("data/tig_2018_archive.json", self.doc)


if __name__ == "__main__":
    unittest.main()
