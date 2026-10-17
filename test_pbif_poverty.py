# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import basic_field  # noqa: E402
import pbif  # noqa: E402
import pbif_history  # noqa: E402
import pbif_poverty  # noqa: E402
import poverty  # noqa: E402

# Hand sums: the 2014-2021 named grants (as in test_pbif_history), the
# 2022-2025 awards (pbif.py, 74 awards) and the poverty population of the 163
# general and agricultural worker areas (poverty.py).
EARLY_USD = 30277654
LATE_USD = 20793322.14
POVERTY = 42301792

# Never a PBIF grant in 2014-2025: the twelve states of pbif-history.md and
# the four territories other than the Virgin Islands.
NONE = sorted("AL AZ CT DE MS ND NH OK OR RI SD WY".split() + ["AS", "GU", "MP", "PR"])

# Read by hand from data/pbif_history.json, data/pbif_awards.json and
# data/poverty_areas_2025.json.
# VT: 2016 $246,034, 2018 $186,960, 2020 $375,970; 2023 $227,982; VT-1 54,718.
# MT: 2014 $141,087, 2018 $236,797, 2020 $223,181; none since; MT-1 114,631
# and MMT 15,174.
HAND = {
    "VT": {"poverty_population": 54718, "2014-2021": 808964, "2022-2025": 227982, "2014-2025": 1036946},
    "MT": {"poverty_population": 129805, "2014-2021": 601065, "2022-2025": 0, "2014-2025": 601065},
}


def build():
    areas = basic_field.load()["service_areas"]
    printed = poverty.load()["service_areas"]
    late = pbif_history.later(pbif.load()["awards"], pbif.load_releases(), areas)
    return pbif_poverty.compare(pbif_history.load(), late, areas, printed)


class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = build()
        cls.by = {r["state"]: r for r in cls.rows}

    def test_jurisdictions(self):
        self.assertEqual(len(self.rows), 56)
        self.assertEqual(sum(r["poverty_population"] for r in self.rows), POVERTY)

    def test_totals(self):
        total = lambda label: sum(r[label]["pbif_usd"] for r in self.rows)  # noqa: E731
        self.assertEqual(total("2014-2021"), EARLY_USD)
        self.assertAlmostEqual(total("2022-2025"), LATE_USD, places=2)
        self.assertAlmostEqual(total("2014-2025"), EARLY_USD + LATE_USD, places=2)

    def test_shares(self):
        self.assertAlmostEqual(sum(r["poverty_share"] for r in self.rows), 1.0)
        for label in pbif_poverty.PERIODS:
            self.assertAlmostEqual(sum(r[label]["pbif_share"] for r in self.rows), 1.0)
            # The index averages to 1 when weighted by poverty share.
            self.assertAlmostEqual(sum(r[label]["index"] * r["poverty_share"] for r in self.rows), 1.0)

    def test_hand_checked_states(self):
        for state, want in HAND.items():
            r = self.by[state]
            self.assertEqual(r["poverty_population"], want["poverty_population"], state)
            for label in pbif_poverty.PERIODS:
                self.assertEqual(r[label]["pbif_usd"], want[label], (state, label))
        self.assertEqual("%.2f" % self.by["VT"]["2014-2025"]["per_person_in_poverty"], "18.95")
        self.assertEqual("%.2f" % self.by["MT"]["2014-2025"]["per_person_in_poverty"], "4.63")

    def test_none(self):
        none = sorted(r["state"] for r in self.rows if r["2014-2025"]["pbif_usd"] == 0)
        self.assertEqual(none, NONE)

    def test_sorted(self):
        index = [r["2014-2025"]["index"] for r in self.rows]
        self.assertEqual(index, sorted(index, reverse=True))

    def test_missing_state_raises(self):
        areas = basic_field.load()["service_areas"]
        printed = poverty.load()["service_areas"]
        late = [{"year": 2025, "grantee": "Nowhere", "state": "ZZ", "amount_usd": 1.0}]
        with self.assertRaises(ValueError):
            pbif_poverty.compare(pbif_history.load(), late, areas, printed)


class Headline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.head = pbif_poverty.headline(build())

    def test_per_person(self):
        self.assertAlmostEqual(self.head["2014-2025"]["per_person_in_poverty"], (EARLY_USD + LATE_USD) / POVERTY)

    def test_none_groups(self):
        self.assertEqual(self.head["2014-2025"]["none"]["states"], NONE)
        self.assertEqual(self.head["2014-2025"]["none"]["pbif_share"], 0)
        self.assertEqual(self.head["both_periods"]["none"], NONE)

    def test_groups_nest(self):
        both = self.head["both_periods"]
        for key in ("under_half", "over_double"):
            for label in ("2014-2021", "2022-2025"):
                self.assertLessEqual(set(both[key]), set(self.head[label][key]["states"]))
        self.assertTrue(-1 <= both["per_person_correlation"] <= 1)

    def test_correlation(self):
        self.assertAlmostEqual(pbif_poverty.correlation([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(pbif_poverty.correlation([1, 2, 3], [3, 2, 1]), -1.0)


class Output(unittest.TestCase):
    def test_markdown_rows(self):
        lines = pbif_poverty.markdown(build()).splitlines()
        self.assertEqual(len(lines), 2 + 56)
        self.assertTrue(lines[2].startswith("| "))

    def test_main_runs(self):
        for argv in ([], ["--json"], ["--summary"]):
            self.assertEqual(pbif_poverty.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
