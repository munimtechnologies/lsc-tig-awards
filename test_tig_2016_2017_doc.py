# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_2016_2017  # noqa: E402
import tig_history  # noqa: E402


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2016_2017.load()
        with open(os.path.join(HERE, "docs", "tig-2016-2017.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_tables_are_current(self):
        h = self.history
        self.assertIn(tig_2016_2017.totals_markdown(tig_2016_2017.totals(h)), self.doc)
        self.assertIn(tig_2016_2017.sources_markdown(tig_2016_2017.sources(h)), self.doc)
        self.assertIn(tig_2016_2017.grantee_totals_markdown(tig_2016_2017.grantee_totals(h)), self.doc)
        self.assertIn(tig_2016_2017.statements_markdown(tig_2016_2017.statements(h)), self.doc)

    def test_doc_figures(self):
        rows = tig_2016_2017.totals(self.history)
        self.assertIn("which is %s short of $4.2 million" % tig.dollars(4200000 - rows[0]["page_usd"]), self.doc)
        self.assertIn("That is %s over" % tig.dollars(rows[0]["filled_usd"] - 4200000), self.doc)
        self.assertIn("amounts for %d of the %d grants. The other %d" % (
            rows[0]["on_lsc_today"], rows[0]["grants"], rows[0]["grants"] - rows[0]["on_lsc_today"]), self.doc)
        self.assertIn("All %d statements fit" % len(tig_2016_2017.statements(self.history)), self.doc)
        self.assertIn("data/tig_2016_2017.json", self.doc)
        self.assertIn("python tig_2016_2017.py", self.doc)

    def test_comparison_with_2018_2020(self):
        # The doc's statements about tig-history.md.
        older = tig_history.load()
        changed = {(r["year"], r["tig"]) for r in tig_history.differences(older)}
        self.assertIn("where %d\ngrants have two different amounts" % len(changed), self.doc)
        misses = [r["year"] for r in tig_history.headlines(older, tig.load()["awards"]) if r["wrong"]]
        self.assertEqual(min(misses), 2019)


if __name__ == "__main__":
    unittest.main()
