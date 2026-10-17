# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lawnext_2018  # noqa: E402
import tig  # noqa: E402
import tig_history  # noqa: E402


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lawnext = lawnext_2018.load()
        cls.history = tig_history.load()
        cls.rows = lawnext_2018.rows(cls.lawnext, cls.history)
        cls.summary = lawnext_2018.summary(cls.lawnext, cls.history)
        with open(os.path.join(HERE, "docs", "tig-history.md"), encoding="utf-8") as f:
            cls.doc = f.read()
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            cls.readme = f.read()

    def test_table_is_current(self):
        self.assertIn(lawnext_2018.markdown(lawnext_2018.notable(self.rows)), self.doc)

    def test_doc_figures(self):
        s = self.summary
        self.assertIn("%d of LawNext's %d amounts are exactly $2,000 below" % (s["at_gap"], s["grants"]), self.doc)
        self.assertIn("LawNext's list adds up to %s, while its text says \"%s\"" % (
            tig.dollars(s["listed_usd"]), self.lawnext["stated_total"]), self.doc)
        self.assertIn("%s above LawNext's own list and %s above LSC's stated %s" % (
            tig.dollars(s["stated_minus_listed"]), tig.dollars(s["stated_minus_lsc_stated"]),
            tig.dollars(s["lsc_stated_usd"])), self.doc)
        self.assertIn(self.lawnext["url"], self.doc)
        self.assertIn("python lawnext_2018.py", self.doc)
        self.assertIn("data/tig_2018_lawnext.json", self.doc)

    def test_readme_links_the_doc(self):
        self.assertIn("docs/tig-history.md", self.readme)


if __name__ == "__main__":
    unittest.main()
