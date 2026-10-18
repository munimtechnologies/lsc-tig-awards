# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import grantee_base  # noqa: E402
import tig  # noqa: E402


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.undecided, cls.tig_orgs, cls.pbif_orgs, cls.head = grantee_base.build()
        with open(os.path.join(HERE, "docs", "tig-grantees.md"), encoding="utf-8") as f:
            cls.doc = f.read()
        cls.section = cls.doc.split("## The base: LSC's 2025 grantees", 1)[1].split("## Limits", 1)[0]

    def test_no_placeholders(self):
        self.assertNotIn("[FILL", self.doc)

    def test_groups(self):
        h, g = self.head, self.head["groups"]
        self.assertIn("**%d organizations hold a 2025 basic field grant, and %d of them (%s) won a TIG or a PBIF grant "
                      "from 2014 to 2025**: %d won both, %d a TIG only and %d PBIF only." % (
                          h["grantees"], h["won_either"]["grantees"], tig.pct(h["won_either"]["grantees"], h["grantees"]),
                          g["both"]["grantees"], g["tig_only"]["grantees"], g["pbif_only"]["grantees"]), self.section)
        self.assertEqual(h["pbif_organizations_unmatched"], [])
        self.assertIn("All %d PBIF organizations are among the %d." % (h["pbif_organizations"], h["grantees"]), self.section)

    def test_neither(self):
        h, n = self.head, self.head["groups"]["neither"]
        largest = [r for r in h["neither"] if r["basic_field_usd"] == h["largest_neither"]]
        self.assertEqual(len(largest), 1)
        self.assertIn("**%d won neither.** Together they hold %s (%s) of the %s in estimated 2025 funding for the %d. "
                      "The largest of them, %s, has %s; every grantee with more won at least one of the two programs." % (
                          n["grantees"], tig.dollars(n["basic_field_usd"]), tig.pct(n["basic_field_usd"], h["basic_field_usd"]),
                          tig.dollars(h["basic_field_usd"]), h["grantees"], largest[0]["organization"],
                          tig.dollars(h["largest_neither"])), self.section)
        self.assertTrue(all(r["group"] != "neither" for r in self.rows if r["basic_field_usd"] > h["largest_neither"]))
        self.assertIn("The %d that won neither:" % n["grantees"], self.section)
        for r in h["neither"]:
            self.assertIn("| %s | %s | %s | %s |" % (r["organization"], r["state"], tig.dollars(r["basic_field_usd"]),
                                                    ", ".join(r["service_areas"])), self.section)

    def test_unmatched_tig(self):
        h = self.head
        self.assertEqual(len(h["tig_organizations_unmatched"]), 2)
        self.assertIn("**Two TIG organizations match no 2025 grantee.**", self.section)
        for text in h["tig_organizations_unmatched"]:
            name, state, rounds = re.fullmatch(r"(.+) \((\w+), (\d+) rounds\)", text).groups()
            self.assertIn("%s (%s rounds)" % (name, rounds), self.section)
        self.assertEqual(len(self.undecided), 1)
        u = self.undecided[0]
        self.assertIn('is named only in %s, the one service area the notice leaves undecided ("%s", %s)' % (
            u["service_area"], u["printed"], tig.dollars(u["amount_usd"])), self.section)
        self.assertIn("The other %d of the %d round wins went to 2025 grantees." % (
            h["tig_round_wins_by_2025_grantees"], h["tig_round_wins"]), self.section)

    def test_tiers(self):
        for t in self.head["tiers"]:
            self.assertIn("| %s | %d | %d | %d | %d | %d | %s |" % (
                t["tier"], t["grantees"], t["won_tig"], t["won_pbif"], t["won_both"], t["neither"],
                tig.pct(t["grantees"] - t["neither"], t["grantees"])), self.section)
        self.assertEqual([low for _, low, _ in grantee_base.TIERS], [0, 1000000, 3000000, 6000000])
        self.assertIn("Each tier includes its lower bound and excludes its upper one.", self.section)

    def test_gradient(self):
        # The first two tiers are below $3M; the last is $6M and over.
        tiers = self.head["tiers"]
        self.assertEqual(grantee_base.TIERS[2][1], 3000000)
        low, high, top = tiers[:2], tiers[2:], tiers[3]
        low_n = sum(t["grantees"] for t in low)
        low_won = sum(t["grantees"] - t["neither"] for t in low)
        high_n = sum(t["grantees"] for t in high)
        high_won = sum(t["grantees"] - t["neither"] for t in high)
        self.assertEqual(top["tier"], "$6M and over")
        self.assertEqual(top["neither"], 0)
        self.assertIn("**The share of winners is higher for larger grantees.** Below $3M, %d of %d grantees (%s) won at "
                      "least one of the two programs; from $3M up, %d of %d (%s) did, including all %d with $6M or more." % (
                          low_won, low_n, tig.pct(low_won, low_n), high_won, high_n, tig.pct(high_won, high_n),
                          top["grantees"]), self.section)
        self.assertIn("(https://www.lsc.gov/grants/basic-field-grant/basic-field-allocation-process)), so a tier "
                      "measures size, not performance", self.section)

    def test_lsc_tracks(self):
        # Spans read on each source (law runs 83 and 84); the rest is paraphrased.
        for quote in ('"Project Incubation Grants are available to organizations that have never received PBIF funding"',
                      '"primarily intended for LSC grantees who have been unsuccessful applying for Project Grants"',
                      '"only LSC grantees that have not had a TIG award in the last five years (since 2013) are eligible"',
                      "Technology Improvement Projects of up to $25,000"):
            self.assertIn(quote, self.section)
        for link in ("https://www.lsc.gov/grants/pro-bono-innovation-fund/pbif-program-description",
                     "https://www.govinfo.gov/content/pkg/FR-2019-12-10/html/2019-26499.htm",
                     "https://www.govinfo.gov/content/pkg/FR-2018-02-07/html/2018-02435.htm"):
            self.assertIn("(%s)" % link, self.section)

    def test_links_and_commands(self):
        for text in ("python grantee_base.py --summary", "test_grantee_base.py", "(pbif-history.md)",
                     "(../data/basic_field_2025.json)", "89 FR 88814"):
            self.assertIn(text, self.section)
        self.assertIn("- \"Won neither\" says nothing about applying.", self.doc)


if __name__ == "__main__":
    unittest.main()
