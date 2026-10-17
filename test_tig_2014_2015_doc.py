# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_2014_2015  # noqa: E402


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2014_2015.load()
        with open(os.path.join(HERE, "docs", "tig-2014-2015.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_tables_are_current(self):
        h = self.history
        self.assertIn(tig_2014_2015.totals_markdown(tig_2014_2015.totals(h)), self.doc)
        self.assertIn(tig_2014_2015.sources_markdown(tig_2014_2015.sources(h)), self.doc)
        self.assertIn(tig_2014_2015.parts_markdown(tig_2014_2015.parts(h)), self.doc)
        self.assertIn(tig_2014_2015.statements_markdown(h, tig_2014_2015.statements(h)), self.doc)
        self.assertIn(tig_2014_2015.cumulative_markdown(tig_2014_2015.cumulative(h)), self.doc)

    def test_doc_figures(self):
        rows = tig_2014_2015.totals(self.history)
        self.assertIn("which is %s short of $3.5 million" % tig.dollars(3500000 - rows[0]["sum_usd"]), self.doc)
        self.assertIn("only %d of the %d grantees are known" % (rows[1]["grantees"], rows[1]["stated_organizations"]), self.doc)
        self.assertIn("at least %s of \"more than $4.2 million\", across %d" % (
            tig.dollars(4200000 - rows[1]["sum_usd"]), rows[1]["stated_organizations"] - rows[1]["grantees"]), self.doc)
        self.assertIn("the known grants are %d of the %d" % (rows[1]["grants_at_least"], rows[1]["stated_grants"]), self.doc)
        self.assertIn("least %d projects" % rows[0]["grants_at_least"], self.doc)
        c = tig_2014_2015.cumulative(self.history)
        self.assertIn("%d + %d + %d = %d" % (c["before_grants"], c["added_grants"][0], c["added_grants"][1], c["after_grants"]), self.doc)
        self.assertIn("is at least %s" % tig.dollars(c["implied_usd_at_least"]), self.doc)
        self.assertIn(self.history["rounds"][0]["list"]["sha256"], self.doc)
        self.assertIn("data/tig_2014_2015.json", self.doc)
        self.assertIn("python tig_2014_2015.py", self.doc)

    def test_single_difference_is_named(self):
        (row,) = [r for r in tig_2014_2015.sources(self.history) if r["differ"]]
        (d,) = row["differ"]
        self.assertIn("Ohio State Legal Services %s more than its\n  list" % tig.dollars(d["source_usd"] - d["list_usd"]), self.doc)


if __name__ == "__main__":
    unittest.main()
