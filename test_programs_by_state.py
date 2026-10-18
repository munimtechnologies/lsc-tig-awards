# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Checks for programs_by_state.py. The lists and sums were derived by hand
from tig_states.py and pbif_poverty.py output before the module first ran."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import programs_by_state  # noqa: E402
import tig  # noqa: E402


def row(state, people, tig_usd, pbif_usd):
    return ({"state": state, "poverty_population": people, "poverty_share": people / 100,
             "2014-2025": {"tig_usd": tig_usd, "per_person_in_poverty": tig_usd / people, "index": 1.0}},
            {"state": state, "poverty_population": people, "poverty_share": people / 100,
             "2014-2025": {"pbif_usd": pbif_usd, "per_person_in_poverty": pbif_usd / people, "index": 1.0}})


class Combine(unittest.TestCase):
    def test_groups_and_index(self):
        pairs = [row("AA", 50, 10, 10), row("BB", 25, 20, 0), row("CC", 15, 0, 10), row("DD", 10, 0, 0)]
        rows = programs_by_state.combine([a for a, _ in pairs], [b for _, b in pairs])
        by = {r["state"]: r for r in rows}
        self.assertEqual([by[s]["group"] for s in ("AA", "BB", "CC", "DD")],
                         ["both", "tig_only", "pbif_only", "neither"])
        self.assertAlmostEqual(by["BB"]["index"], (20 / 50) / 0.25)
        self.assertEqual(rows[-1]["state"], "DD")

    def test_mismatch_raises(self):
        a, b = row("AA", 50, 10, 10)
        c, _ = row("BB", 50, 10, 10)
        with self.assertRaises(ValueError):
            programs_by_state.combine([a, c], [b])
        b2 = dict(b, poverty_population=49)
        with self.assertRaises(ValueError):
            programs_by_state.combine([a], [b2])


class Live(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = programs_by_state.build()
        cls.head = programs_by_state.headline(cls.rows)

    def test_base(self):
        self.assertEqual(self.head["jurisdictions"], 56)
        self.assertEqual(self.head["poverty_population"], 42301792)

    def test_dollars(self):
        self.assertAlmostEqual(self.head["tig_usd"], 48139618.03, places=2)
        self.assertAlmostEqual(self.head["pbif_usd"], 51070976.14, places=2)
        self.assertAlmostEqual(self.head["usd"], 99210594.17, places=2)
        self.assertEqual("%.2f" % self.head["per_person_in_poverty"], "2.35")
        self.assertEqual("%.2f" % self.head["tig_per_person_in_poverty"], "1.14")
        self.assertEqual("%.2f" % self.head["pbif_per_person_in_poverty"], "1.21")

    def test_groups(self):
        g = self.head["groups"]
        self.assertEqual(g["neither"]["states"], ["GU", "MP", "RI"])
        self.assertEqual(g["pbif_only"]["states"], ["MD", "VI"])
        self.assertEqual(g["tig_only"]["states"],
                         ["AL", "AS", "AZ", "CT", "DE", "MS", "ND", "NH", "OK", "OR", "PR", "SD", "WY"])
        self.assertEqual(g["both"]["count"], 38)
        self.assertEqual(sum(x["count"] for x in g.values()), 56)

    def test_group_people_and_dollars(self):
        g = self.head["groups"]
        self.assertEqual(g["neither"]["poverty_population"], 29408 + 158094 + 113657)
        self.assertEqual(g["pbif_only"]["poverty_population"], 574160 + 19338)
        self.assertAlmostEqual(g["pbif_only"]["pbif_usd"], 533744 + 204429, places=2)
        self.assertEqual(g["pbif_only"]["tig_usd"], 0)
        self.assertEqual(g["tig_only"]["pbif_usd"], 0)
        self.assertEqual((g["neither"]["tig_usd"], g["neither"]["pbif_usd"]), (0, 0))
        self.assertEqual([tig.pct(g[n]["poverty_share"], 1) for n in programs_by_state.GROUPS],
                         ["85.3%", "12.6%", "1.4%", "0.7%"])
        self.assertEqual(sum(x["poverty_population"] for x in g.values()), self.head["poverty_population"])
        self.assertAlmostEqual(sum(x["tig_usd"] + x["pbif_usd"] for x in g.values()), self.head["usd"], places=2)

    def test_rows(self):
        self.assertAlmostEqual(sum(r["share"] for r in self.rows), 1.0)
        self.assertTrue(-1 <= self.head["per_person_correlation"] <= 1)
        self.assertEqual([r["index"] for r in self.rows], sorted((r["index"] for r in self.rows), reverse=True))

    def test_markdown(self):
        self.assertEqual(len(programs_by_state.markdown(self.rows).splitlines()), 2 + 56)
        self.assertIn("| Neither | 3 | 301,159 | 0.7% | $0 | $0 |", programs_by_state.groups_markdown(self.head))


if __name__ == "__main__":
    unittest.main()
