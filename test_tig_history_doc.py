# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_history  # noqa: E402


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_history.load()
        cls.rows = tig_history.headlines(cls.history, tig.load()["awards"])
        with open(os.path.join(HERE, "docs", "tig-history.md"), encoding="utf-8") as f:
            cls.doc = f.read()
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            cls.readme = f.read()

    def test_totals_table_is_current(self):
        self.assertIn(tig_history.totals_markdown(tig_history.totals(self.history)), self.doc)

    def test_amounts_table_is_current(self):
        self.assertIn(tig_history.differences_markdown(tig_history.differences(self.history)), self.doc)

    def test_headlines_table_is_current(self):
        self.assertIn(tig_history.headlines_markdown(self.rows), self.doc)

    def test_doc_counts(self):
        grants = sum(len(r["grants"]) for r in self.history["rounds"])
        self.assertIn("the %d grants of the three rounds" % grants, self.doc)
        self.assertIn("%d statements by LSC" % len(self.history["headlines"]), self.doc)
        grant_counts = [r for r in self.rows if r["grants"] is not None]
        self.assertFalse([r for r in grant_counts if "grants" in r["wrong"]])
        other = sum(1 for r in self.rows for k in ("organizations", "states") if r[k] is not None)
        missed = sum(len(r["wrong"]) for r in self.rows)
        self.assertIn("All %d counts of grants LSC printed fit its lists. Eight of its %d counts" % (
            len(grant_counts), other), self.doc)
        self.assertEqual(missed, 8)

    def test_readme_points_here(self):
        self.assertIn("docs/tig-history.md", self.readme)
        self.assertIn("python tig_history.py", self.readme)


if __name__ == "__main__":
    unittest.main()
