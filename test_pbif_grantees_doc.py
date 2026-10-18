# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pbif_grantees  # noqa: E402
import tig  # noqa: E402


class Doc(unittest.TestCase):
    """Every PBIF x TIG figure docs/pbif-history.md quotes, computed from the code."""

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.orgs, cls.tig_orgs, cls.h = pbif_grantees.build()
        cls.names = pbif_grantees.load_names()
        with open(os.path.join(HERE, "docs", "pbif-history.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_method(self):
        self.assertIn("by four hand-checked PBIF names in `data/pbif_names.json`", self.doc)
        self.assertEqual(len(self.names["names"]), 4)
        self.assertIn("a loose rule whose %d matches were each checked by hand" % self.h["match_rules"]["loose"], self.doc)
        vt = [e for e in self.names["names"] if e["kind"] == "renamed"][0]
        self.assertIn("(%s)" % vt["source"], self.doc)
        self.assertIn("Legal Services Law Line of Vermont \"will now be called Legal Services Vermont\"", self.doc)

    def test_pbif_side(self):
        h = self.h
        self.assertIn("**%d organizations won the %d PBIF grants, and %d of them (%s) also won a TIG.**" % (
            h["pbif_organizations"], h["pbif_grants"], h["both"], tig.pct(h["both"], h["pbif_organizations"])), self.doc)
        self.assertIn("Those %d received %s of the %s in PBIF grants (%s)." % (
            h["both"], tig.dollars(h["pbif_usd_to_tig_winners"]), tig.dollars(h["pbif_usd"]),
            tig.pct(h["pbif_usd_to_tig_winners"], h["pbif_usd"])), self.doc)

    def test_pbif_only(self):
        only = [o for o in self.orgs if not o["tig"]]
        self.assertEqual(len(only), self.h["pbif_only"])
        self.assertIn("**Six PBIF organizations won no TIG in 2014-2025:**", self.doc)
        self.assertEqual(len(only), 6)
        for o in only:
            self.assertIn(o["organization"], self.doc)
        usd = self.h["pbif_usd"] - self.h["pbif_usd_to_tig_winners"]
        self.assertAlmostEqual(usd, sum(o["pbif_usd"] for o in only), places=2)
        self.assertIn("with %s together." % tig.dollars(usd), self.doc)

    def test_tig_side(self):
        h = self.h
        self.assertIn("**%d of the %d TIG organizations (%s) also won PBIF**" % (
            h["both"], h["tig_organizations"], tig.pct(h["both"], h["tig_organizations"])), self.doc)
        self.assertIn("they received %s of the %s in TIG grants (%s)." % (
            tig.dollars(h["tig_usd_to_pbif_winners"]), tig.dollars(h["tig_usd_total"]),
            tig.pct(h["tig_usd_to_pbif_winners"], h["tig_usd_total"])), self.doc)
        m = h["mean_tig_rounds"]
        self.assertIn("They won %.2f TIG rounds each on average; the %d TIG organizations with no PBIF grant won %.2f." % (
            m["tig_orgs_with_pbif"], h["tig_only"], m["tig_orgs_without_pbif"]), self.doc)

    def test_tig_five_or_more(self):
        five = self.h["tig_five_or_more"]
        self.assertIn("**%d of the %d organizations that won five or more TIG rounds also won PBIF.**" % (
            five["with_pbif"], five["organizations"]), self.doc)
        others = [o["organization"] for o in self.tig_orgs
                  if len(o["rounds"]) >= 5 and "%s (%s)" % (o["organization"], o["state"]) not in five["names"]]
        self.assertEqual(len(others), 3)
        self.assertIn("The other three are %s, %s and %s." % tuple(others), self.doc)

    def test_most_pbif(self):
        top = self.orgs[0]
        self.assertIn("%s won PBIF in %d of the %d rounds and TIG once." % (
            top["organization"], len(top["pbif_rounds"]) + len(top["pbif_partial"]), self.h["pbif_rounds"]), self.doc)
        self.assertEqual(len(top["tig_rounds"]), 1)
        hist = list(self.h["pbif_rounds_won_histogram"].items())
        parts = ["%d with %s" % (n, k) for k, n in hist]
        self.assertIn("PBIF organizations by rounds won: %s and %s." % (", ".join(parts[:-1]), parts[-1]), self.doc)

    def test_earlier_sections_kept(self):
        self.assertIn("## The rounds, 2014-2021", self.doc)
        self.assertIn("## States with a PBIF grant", self.doc)
        self.assertLess(self.doc.index("## PBIF and TIG winners, 2014-2025"), self.doc.index("## Sources and method"))


if __name__ == "__main__":
    unittest.main()
