# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lawnext_2018  # noqa: E402
import tig_history  # noqa: E402

# LawNext's 26 amounts summed by hand from the raw text of the article.
LISTED = 3805282

# (TIG #, LawNext, description page, other LSC source, its amount), read by hand.
NOTABLE = [
    ("18008", 266000, 297175, "release", 267175),
    ("18010", 264000, 266000, "bundle", 264000),
    ("18046", 169879, 179879, "bundle", 171879),
    ("18056", 783200, 783000, None, None),
]


class Lawnext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lawnext = lawnext_2018.load()
        cls.history = tig_history.load()
        cls.rows = lawnext_2018.rows(cls.lawnext, cls.history)
        cls.summary = lawnext_2018.summary(cls.lawnext, cls.history)

    def test_source(self):
        self.assertTrue(self.lawnext["url"].startswith("https://www.lawnext.com/2018/11/"))
        self.assertIn(self.lawnext["stated_total"], self.lawnext["quote"])
        self.assertIn("not an LSC document", self.lawnext["description"])

    def test_same_grants_as_lsc(self):
        mine = sorted(g["tig"] for g in self.lawnext["grants"])
        lsc = sorted(g["tig"] for g in self.history["rounds"][0]["grants"])
        self.assertEqual(len(mine), 26)
        self.assertEqual(mine, lsc)

    def test_names_match_lsc(self):
        # LSC's name without ", Inc." or " Corporation" starts the name LawNext prints.
        lsc = {g["tig"]: g["grantee"] for g in self.history["rounds"][0]["grants"]}
        for g in self.lawnext["grants"]:
            short = lsc[g["tig"]].replace(", Inc.", "").replace(" Corporation", "")
            self.assertTrue(g["grantee"].startswith(short), (g["grantee"], lsc[g["tig"]]))

    def test_totals(self):
        s = self.summary
        self.assertEqual(s["listed_usd"], LISTED)
        self.assertEqual(s["stated_usd"], 3891457)
        self.assertEqual(s["stated_minus_listed"], 86175)
        self.assertEqual(s["lsc_stated_usd"], 3884257)
        self.assertEqual(s["stated_minus_lsc_stated"], 7200)
        self.assertEqual(s["page_listed_usd"], 3892257)

    def test_gap(self):
        self.assertEqual(self.summary["grants"], 26)
        self.assertEqual(self.summary["at_gap"], 23)
        self.assertEqual(self.summary["off_gap"], ["18008", "18046", "18056"])
        # Page list minus 23 gaps and the three other differences is LawNext's list.
        self.assertEqual(3892257 + 23 * -2000 - 31175 - 10000 + 200, LISTED)

    def test_notable(self):
        got = []
        for r in lawnext_2018.notable(self.rows):
            source = sorted(r["other"])[0] if r["other"] else None
            got.append((r["tig"], r["lawnext"], r["page"], source, r["other"].get(source)))
        self.assertEqual(got, NOTABLE)

    def test_alaska_fits_the_gap_from_the_per_grantee_release(self):
        ak = [r for r in self.rows if r["tig"] == "18046"][0]
        self.assertEqual(ak["minus_other"]["bundle"], lawnext_2018.GAP)

    def test_markdown(self):
        table = lawnext_2018.markdown(lawnext_2018.notable(self.rows))
        self.assertEqual(len(table.splitlines()), 2 + len(NOTABLE))
        self.assertIn("| Northwest Justice Project | 18008 | $266,000 | $297,175 | -$31,175 | release | $267,175 | -$1,175 |", table)
        self.assertIn("| Alaska Legal Services Corporation | 18046 | $169,879 | $179,879 | -$10,000 | per-grantee release | $171,879 | -$2,000 |", table)
        self.assertIn("| Ohio State Legal Services | 18056 | $783,200 | $783,000 | +$200 | - | - | - |", table)

    def test_main_runs(self):
        for argv in ([], ["--summary"]):
            self.assertEqual(lawnext_2018.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
