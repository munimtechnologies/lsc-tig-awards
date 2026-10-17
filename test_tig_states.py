# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import basic_field  # noqa: E402
import poverty  # noqa: E402
import tig  # noqa: E402
import tig_2014_2015  # noqa: E402
import tig_2016_2017  # noqa: E402
import tig_history  # noqa: E402
import tig_states  # noqa: E402

# Grants and dollars per round, summed by hand in groups of five: 2014 the PDF
# (30 grantee rows); 2015 the seven grantees LSC's releases name; 2016 the page
# plus Iowa's $59,734; 2017-2020 the pages; 2021-2025 data/awards.json (2022
# in cents; one 2025 grant has no amount).
ROUNDS = {
    2014: (30, 3467978), 2015: (7, 1214048), 2016: (34, 4203221), 2017: (25, 3927974),
    2018: (26, 3892257), 2019: (30, 4231402), 2020: (26, 3941298), 2021: (35, 4268931),
    2022: (33, 4679135.03), 2023: (33, 5157033), 2024: (32, 6306081), 2025: (31, 4064308),
}
EARLY_USD = 19722832        # 2014 and 2016-2019
LATE_USD = 28416786.03      # 2020-2025
POVERTY = 42301792          # as in test_pbif_poverty

# Read by hand from the four data files.
# OH: 2014 $94,150 + $725,200; 2016 $808,000 + $46,576; 2017 $751,250;
# 2018 $209,750 + $783,000; 2019 $162,500 + $790,000; 2020 $526,400;
# 2021 $218,621 + $35,000 + $265,000; 2022 none; 2023 $215,070;
# 2024 $35,000 x 2; 2025 $165,756 + $35,000.
# MI: 2014 $81,400; 2016 $57,000 + $127,000; 2017 $209,825; 2018 none;
# 2019 $114,300 + $177,500 + $180,838; 2020 $68,650 + $259,500 + $70,896 +
# $100,400; 2021 $30,000 + $244,993; 2022 $102,950 + $598,970;
# 2023 $275,000 + $110,404 + $34,410; 2024 $225,000; 2025 $298,300.
# WV: 2015 $90,600 (partial round, in no period); 2020 $149,736;
# 2023 $137,826; 2024 $432,900.
HAND = {
    "OH": {"rounds": 10, "2014-2019": 4370426, "2020-2025": 1530847, "2014-2025": 5901273},
    "MI": {"rounds": 10, "2014-2019": 947863, "2020-2025": 2419473, "2014-2025": 3367336},
    "WV": {"rounds": 3, "2014-2019": 0, "2020-2025": 720462, "2014-2025": 720462},
    "AS": {"rounds": 2, "2014-2019": 134940, "2020-2025": 0, "2014-2025": 134940},
    "PR": {"rounds": 1, "2014-2019": 83900, "2020-2025": 0, "2014-2025": 83900},
}

# No TIG in any complete round 2014-2025 (2015's 23 unnamed grantees aside).
NEVER = ["GU", "MD", "MP", "RI", "VI"]
# A TIG in 10 of the 11 complete rounds; none has all 11.
TEN = ["CA", "FL", "IL", "MI", "MT", "OH", "PA"]


def grant_rows():
    return tig_states.build()


def build():
    areas = basic_field.load()["service_areas"]
    printed = poverty.load()["service_areas"]
    return tig_states.compare(grant_rows(), areas, printed)


class Rounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.totals = tig_states.round_totals(grant_rows())

    def test_hand_sums(self):
        self.assertEqual(sorted(self.totals), list(tig_states.YEARS))
        for year, (n, usd) in ROUNDS.items():
            self.assertEqual(self.totals[year]["grants"], n, year)
            self.assertAlmostEqual(self.totals[year]["usd"], usd, places=2, msg=year)

    def test_same_as_each_module(self):
        for r in tig_2014_2015.totals(tig_2014_2015.load()):
            self.assertEqual(self.totals[r["year"]]["usd"], r["sum_usd"])
        for r in tig_2016_2017.totals(tig_2016_2017.load()):
            self.assertEqual(self.totals[r["year"]]["usd"], r["filled_usd"])
        for r in tig_history.totals(tig_history.load()):
            if r["source"] == "page":
                self.assertEqual(self.totals[r["year"]]["usd"], r["listed_usd"])
        for r in tig.summary(tig.load()["awards"]):
            self.assertAlmostEqual(self.totals[r["year"]]["usd"], r["dollars_listed"], places=2)

    def test_totals_markdown(self):
        lines = tig_states.totals_markdown(grant_rows()).splitlines()
        self.assertEqual(len(lines), 2 + 12 + 1)
        self.assertEqual(lines[3], "| 2015 (partial) | 7 | $1,214,048 |")
        self.assertEqual(lines[-1], "| 2014-2025 (complete rounds) | 335 | $48,139,618 |")

    def test_markdown(self):
        lines = tig_states.rounds_markdown(grant_rows()).splitlines()
        self.assertTrue(lines[0].startswith("| State | 2014 | 2015 (partial) | 2016 |"))
        self.assertEqual(lines[-2].split(" | ")[-1], "$48,139,618 |")
        self.assertEqual(lines[-1], "| Grants | 30 | 7 | 34 | 25 | 26 | 30 | 26 | 35 | 33 | 33 | 32 | 31 | 335 |")


class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = build()
        cls.by = {r["state"]: r for r in cls.rows}

    def test_jurisdictions(self):
        self.assertEqual(len(self.rows), 56)
        self.assertEqual(sum(r["poverty_population"] for r in self.rows), POVERTY)

    def test_totals(self):
        total = lambda label: sum(r[label]["tig_usd"] for r in self.rows)  # noqa: E731
        self.assertEqual(total("2014-2019"), EARLY_USD)
        self.assertAlmostEqual(total("2020-2025"), LATE_USD, places=2)
        self.assertAlmostEqual(total("2014-2025"), EARLY_USD + LATE_USD, places=2)

    def test_shares(self):
        self.assertAlmostEqual(sum(r["poverty_share"] for r in self.rows), 1.0)
        for label in tig_states.PERIODS:
            self.assertAlmostEqual(sum(r[label]["tig_share"] for r in self.rows), 1.0)
            self.assertAlmostEqual(sum(r[label]["index"] * r["poverty_share"] for r in self.rows), 1.0)

    def test_hand_checked_states(self):
        for state, want in HAND.items():
            r = self.by[state]
            self.assertEqual(r["rounds"], want["rounds"], state)
            for label in tig_states.PERIODS:
                self.assertEqual(r[label]["tig_usd"], want[label], (state, label))
        self.assertEqual(self.by["WV"]["by_year"]["2015"], 90600)

    def test_ohio_share(self):
        oh = self.by["OH"]
        self.assertEqual("%.1f" % (100 * oh["2014-2019"]["tig_share"]), "22.2")
        self.assertEqual("%.1f" % (100 * oh["2020-2025"]["tig_share"]), "5.4")
        self.assertEqual("%.1f" % (100 * oh["2014-2025"]["tig_share"]), "12.3")

    def test_never(self):
        self.assertEqual(sorted(r["state"] for r in self.rows if r["2014-2025"]["tig_usd"] == 0), NEVER)
        self.assertEqual(sorted(r["state"] for r in self.rows if r["rounds"] == 0), NEVER)

    def test_sorted(self):
        index = [r["2014-2025"]["index"] for r in self.rows]
        self.assertEqual(index, sorted(index, reverse=True))

    def test_missing_state_raises(self):
        areas = basic_field.load()["service_areas"]
        printed = poverty.load()["service_areas"]
        rows = [{"year": 2025, "grantee": "Nowhere", "state": "ZZ", "amount_usd": 1}]
        with self.assertRaises(ValueError):
            tig_states.compare(rows, areas, printed)


class Headline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.head = tig_states.headline(build())

    def test_rounds(self):
        self.assertEqual(self.head["complete_rounds"], 11)
        self.assertNotIn("11", self.head["rounds"])
        self.assertEqual(self.head["rounds"]["10"], TEN)
        self.assertEqual(self.head["rounds"]["0"], NEVER)
        self.assertEqual(sum(len(s) for s in self.head["rounds"].values()), 56)

    def test_none(self):
        self.assertEqual(self.head["2014-2025"]["none"]["states"], NEVER)
        self.assertEqual(self.head["2014-2025"]["none"]["tig_share"], 0)
        self.assertLessEqual(set(NEVER), set(self.head["both_periods"]["none"]))

    def test_per_person(self):
        self.assertAlmostEqual(self.head["2014-2025"]["per_person_in_poverty"], (EARLY_USD + LATE_USD) / POVERTY)

    def test_groups_nest(self):
        both = self.head["both_periods"]
        for key in ("under_half", "over_double"):
            for label in ("2014-2019", "2020-2025"):
                self.assertLessEqual(set(both[key]), set(self.head[label][key]["states"]))
        self.assertTrue(-1 <= both["per_person_correlation"] <= 1)

    def test_correlation(self):
        self.assertAlmostEqual(tig_states.correlation([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(tig_states.correlation([1, 2, 3], [3, 2, 1]), -1.0)


class Output(unittest.TestCase):
    def test_markdown_rows(self):
        lines = tig_states.markdown(build()).splitlines()
        self.assertEqual(len(lines), 2 + 56)
        self.assertTrue(lines[2].startswith("| "))

    def test_main_runs(self):
        for argv in ([], ["--rounds"], ["--json"], ["--summary"]):
            self.assertEqual(tig_states.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
