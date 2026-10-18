# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pbif  # noqa: E402
import pbif_2026  # noqa: E402
import pbif_history  # noqa: E402
import tig  # noqa: E402


class Doc(unittest.TestCase):
    """Every 2026 figure docs/pbif-history.md quotes, computed from the code."""

    @classmethod
    def setUpClass(cls):
        cls.data = pbif_2026.load()
        cls.s = pbif_2026.summary(cls.data, pbif_history.load(), pbif.load_releases())
        with open(os.path.join(HERE, "docs", "pbif-history.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_tables_are_current(self):
        self.assertIn(pbif_2026.markdown(self.data), self.doc)
        self.assertIn(pbif_2026.releases_markdown(pbif_2026.release_rows(self.data)), self.doc)

    def test_smallest_since(self):
        s = self.s
        self.assertIn("**The 2026 round is the smallest since %d.**" % s["smallest_since"], self.doc)
        self.assertIn("%s less than 2025's $5.5 million" % tig.pct(s["drop_from_2025"], 1), self.doc)
        self.assertIn("Every round from %d to 2025 was at least %s (%d)." % (
            s["smallest_since"] + 1, tig.dollars(s["lowest_after"]["usd"]), s["lowest_after"]["year"]), self.doc)
        gap = s["lowest_after"]["usd"] - s["stated_usd"]
        self.assertEqual(gap, 197185)
        self.assertIn("about $%s higher than stated" % format(int(round(gap, -5)), ","), self.doc)

    def test_named(self):
        r = self.s["readings"]
        states = self.s["named_states"]
        self.assertIn("The releases name %d project grants (%s, %s of the stated total, in %s and %s)" % (
            r["named_grants"], tig.dollars(r["named_usd"]), tig.pct(self.s["named_share"], 1),
            ", ".join(states[:-1]), states[-1]), self.doc)
        self.assertIn("one of nine new Grantee Engagement Scholarships (%s to Greater Bakersfield"
                      % tig.dollars(r["scholarship_usd"]), self.doc)

    def test_california(self):
        ca = [x for x in self.s["releases"] if x["scope"] == "CA"][0]
        parts = [tig.dollars(pbif_2026.usd(a)) for a in self.data["awards"] if ca["url"] in a["sources"]]
        self.assertIn("%s = %s" % (" + ".join(parts), tig.dollars(ca["named_usd"])), self.doc)
        self.assertEqual(ca["named_usd"], ca["stated_usd"])

    def test_readings(self):
        r = self.s["readings"]
        self.assertIn("The seven named grants average %s." % tig.dollars(r["named_mean"]), self.doc)
        self.assertIn("the %d not named would average about %s" % (
            r["all_grants"]["unnamed"], tig.dollars(r["all_grants"]["mean"])), self.doc)
        self.assertIn("the %d unnamed project grants would average about %s" % (
            r["with_scholarships"]["unnamed"], tig.dollars(r["with_scholarships"]["mean"])), self.doc)
        self.assertAlmostEqual(r["all_grants"]["mean"] / r["named_mean"], 1 / 3.0, places=1)

    def test_running_note_kept(self):
        self.assertIn("180 + %d = 200" % self.s["running_added"], self.doc)


if __name__ == "__main__":
    unittest.main()
