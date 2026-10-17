# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import test_national_services as t  # noqa: E402

DOC = os.path.join(HERE, "docs", "national-services.md")


def usd(x):
    return "$" + format(int(round(x)), ",")


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DOC, encoding="utf-8") as f:
            cls.text = f.read()
        cls.lines = cls.text.splitlines()
        cls.data = t.load()

    def row(self, start):
        hits = [line for line in self.lines if line.startswith(start)]
        self.assertEqual(len(hits), 1, start)
        return hits[0]

    def test_services(self):
        for s in self.data["services"]:
            line = self.row("| %s |" % s["service"])
            self.assertIn(s["quote"].rstrip("."), line)

    def test_grants(self):
        self.assertIn("## The thirteen grants", self.text)
        for g in self.data["grants"]:
            hits = [line for line in self.lines
                    if line.startswith("| %d |" % g["year"]) and "| %s |" % g["state"] in line]
            self.assertEqual(len(hits), 1, (g["year"], g["state"]))
            line = hits[0]
            self.assertIn("| %s |" % usd(g["amount_usd"]), line)
            self.assertIn("| %s |" % g["service"], line)
            self.assertIn("| %s" % g["scope"], line)
            if g["scope"] == "part" and g["national_part_usd"]:
                self.assertIn("(%s printed for it)" % usd(g["national_part_usd"]), line)

    def test_totals(self):
        labels = list(t.TOTAL)
        self.assertEqual(self.row("| All TIG dollars |"),
                         "| All TIG dollars | %s |" % " | ".join(usd(t.TOTAL[k]) for k in labels))
        for name, got in (("Whole grants, five services", t.WHOLE_USD), ("Part grants, five services", t.PART_USD),
                          ("LawHelp Interactive", t.LHI_USD)):
            self.assertEqual(self.row("| %s |" % name), "| %s | %s |" % (name, " | ".join(usd(got[k]) for k in labels)))
        for name, key in (("Share: whole grants", "whole"), ("Share: whole grants and LawHelp Interactive", "with_lhi"),
                          ("Share: all of the above, part grants in full", "with_lhi_and_parts")):
            self.assertEqual(self.row("| %s |" % name), "| %s | %s |" % (name, " | ".join(s + "%" for s in t.SHARE[key])))

    def test_by_round(self):
        years = sorted(t.BY_YEAR)
        self.assertEqual(self.row("| Round |"), "| Round | %s |" % " | ".join(str(y) for y in years))
        self.assertEqual(self.row("| Dollars |"), "| Dollars | %s |" % " | ".join(usd(t.BY_YEAR[y]) for y in years))

    def test_findings(self):
        for phrase in (
                "(25.2%, up to 27.5% with the part grants in full), against 6.3% in 2020-2025",
                "No grant in the 2023, 2024 or 2025 rounds names LawHelp Interactive or any of the five services.",
                "$4,648,850 of %s in whole grants, 2014-2025" % usd(t.WHOLE_USD["2014-2025"] + t.LHI_USD["2014-2025"]),
                "Michigan's TIG total includes %s for national services" % usd(209825 + 259500 + 598970),
                "Maine's includes %s for Stateside Legal" % usd(175250 + 50000),
                "plus eight close calls left out and why",
                "[tig-national.md](tig-national.md)",
                "not legal advice"):
            self.assertIn(phrase, self.text)


if __name__ == "__main__":
    unittest.main()
