# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_2021  # noqa: E402


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2021.load()
        cls.awards = tig.load()
        with open(os.path.join(HERE, "docs", "tig-2021.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_tables_are_current(self):
        h = self.history
        self.assertIn(tig_2021.totals_markdown(tig_2021.totals(h)), self.doc)
        self.assertIn(tig_2021.sections_markdown(tig_2021.sections(h)), self.doc)
        self.assertIn(tig_2021.differ_markdown(h), self.doc)
        self.assertIn(tig_2021.swaps_markdown(tig_2021.swaps(h)), self.doc)
        self.assertIn(tig_2021.statements_markdown(tig_2021.statements(h)), self.doc)
        self.assertIn(tig_2021.cumulative_markdown(tig_2021.cumulative(h, self.awards)), self.doc)

    def test_doc_figures(self):
        h = self.history
        with_cents = [g for g in h["grants"] if tig_2021.cents(g["page"]) % 100]
        self.assertIn("The page prints cents for %d grants" % len(with_cents), self.doc)
        self.assertIn("All %d statements' counts fit" % len(tig_2021.statements(h)), self.doc)
        last = tig_2021.cumulative(h, self.awards)[-1]
        self.assertIn("%d plus the %d grants" % (last["previous_grants"], last["round_grants"]), self.doc)
        step = tig_2021.step_2020(h)
        self.assertIn("least %s apart" % tig.dollars(step["if_2020_includes_its_round"]["short_by_at_least"]), self.doc)
        self.assertIn("more than %s before 2021" % tig.dollars(step["before_2021_more_than"]), self.doc)
        self.assertIn("data/tig_2021.json", self.doc)
        self.assertIn("python tig_2021.py", self.doc)


if __name__ == "__main__":
    unittest.main()
