# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Checks that the "Both programs by state" section of docs/tig-states.md and
its README bullet match programs_by_state.py."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import programs_by_state  # noqa: E402
import tig  # noqa: E402

NAMES = {"AL": "Alabama", "AS": "American Samoa", "AZ": "Arizona", "CT": "Connecticut", "DE": "Delaware",
         "MS": "Mississippi", "ND": "North Dakota", "NH": "New Hampshire", "OK": "Oklahoma", "OR": "Oregon",
         "PR": "Puerto Rico", "SD": "South Dakota", "WY": "Wyoming", "MD": "Maryland",
         "VI": "the U.S. Virgin Islands", "GU": "Guam", "MP": "the MP-1 service area", "RI": "Rhode Island"}


def listing(states):
    names = [NAMES[s] for s in states]
    return ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 2 else " and ".join(names)


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = programs_by_state.build()
        cls.head = programs_by_state.headline(cls.rows)
        cls.by = {r["state"]: r for r in cls.rows}
        with open(os.path.join(HERE, "docs", "tig-states.md"), encoding="utf-8") as f:
            cls.doc = f.read()
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            cls.readme = f.read()

    def group(self, name):
        return self.head["groups"][name]

    def test_groups_table(self):
        self.assertIn(programs_by_state.groups_markdown(self.head), self.doc)

    def test_totals(self):
        h = self.head
        self.assertIn("come to $%.2f per person in poverty**: $%.2f from TIG (%s) and $%.2f from PBIF (%s)." % (
            h["per_person_in_poverty"], h["tig_per_person_in_poverty"], tig.dollars(h["tig_usd"]),
            h["pbif_per_person_in_poverty"], tig.dollars(h["pbif_usd"])), self.doc)

    def test_both(self):
        both = self.group("both")
        tig_n = both["count"] + self.group("tig_only")["count"]
        pbif_n = both["count"] + self.group("pbif_only")["count"]
        self.assertIn("%d of the %d jurisdictions had a grant from both programs, and they hold %s of the poverty population.** TIG reached %d of the %d, PBIF %d." % (
            both["count"], self.head["jurisdictions"], tig.pct(both["poverty_share"], 1),
            tig_n, self.head["jurisdictions"], pbif_n), self.doc)

    def test_pbif_only(self):
        g = self.group("pbif_only")
        self.assertIn("PBIF reached only two places TIG did not: %s** (%s of the poverty population, %s in PBIF grants)." % (
            listing(g["states"]), tig.pct(g["poverty_share"], 1), tig.dollars(g["pbif_usd"])), self.doc)
        no_tig = [r for r in self.rows if not r["tig_usd"]]
        largest = max(no_tig, key=lambda r: r["poverty_population"])
        self.assertEqual(largest["state"], "MD")
        self.assertIn("Maryland, with %s people in poverty, is the largest jurisdiction with no TIG" % format(
            largest["poverty_population"], ","), self.doc)

    def test_tig_only(self):
        g = self.group("tig_only")
        self.assertIn("**TIG reached %d that PBIF did not**: %s (%s of the poverty population). Puerto Rico alone holds %s." % (
            g["count"], listing(g["states"]), tig.pct(g["poverty_share"], 1),
            tig.pct(self.by["PR"]["poverty_share"], 1)), self.doc)

    def test_neither(self):
        g = self.group("neither")
        self.assertIn("**Three had neither: %s** (%s of the poverty population)." % (
            listing(g["states"]), tig.pct(g["poverty_share"], 1)), self.doc)

    def test_figures(self):
        h = self.head
        self.assertIn("poverty is %.2f** (unweighted Pearson" % h["per_person_correlation"], self.doc)
        for t in h["top5"]:
            self.assertIn("%s (%.2f)" % (t["state"], t["index"]), self.doc)

    def test_top_five_are_small(self):
        h = self.head
        top = [self.by[t["state"]] for t in h["top5"]]
        self.assertEqual([r["state"] for r in top], ["VT", "DC", "MT", "AK", "ME"])
        people = sum(r["poverty_population"] for r in top)
        usd = sum(r["usd"] for r in top)
        # Hand sums from the lsc-programs-by-state-v2 table.
        self.assertEqual(people, 54718 + 91070 + 129805 + 98225 + 164287)
        self.assertEqual((tig.pct(people, h["poverty_population"]), tig.pct(usd, h["usd"])), ("1.3%", "10.3%"))
        self.assertIn("Together these five hold %s of the poverty population and %s of both programs' dollars" % (
            tig.pct(people, h["poverty_population"]), tig.pct(usd, h["usd"])), self.doc)

    def test_mp_quote(self):
        self.assertIn('"shall be made available to the Federated States of Micronesia and to the Marshall Islands."', self.doc)
        self.assertIn("advisory-opinions/ao-2017-007", self.doc)

    def test_section_before_limits(self):
        self.assertLess(self.doc.index("## Both programs by state"), self.doc.index("## Limits"))

    def test_commands(self):
        self.assertIn("python programs_by_state.py --groups", self.doc)
        self.assertIn("test_programs_by_state.py", self.doc)

    def test_readme(self):
        self.assertIn("38 of the 56 jurisdictions had a grant from both programs** (85.3% of the poverty population)", self.readme)
        self.assertEqual(self.group("both")["count"], 38)
        self.assertEqual(tig.pct(self.group("both")["poverty_share"], 1), "85.3%")
        self.assertIn("PBIF reached only Maryland and the U.S. Virgin Islands where TIG did not, TIG reached %d jurisdictions" % (
            self.group("tig_only")["count"]), self.readme)
        self.assertIn("and %s had neither" % listing(self.group("neither")["states"]), self.readme)
        self.assertIn("python programs_by_state.py --groups\n", self.readme)
        self.assertIn("| `programs_by_state.py` |", self.readme)


if __name__ == "__main__":
    unittest.main()
