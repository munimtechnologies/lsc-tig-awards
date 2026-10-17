# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import basic_field  # noqa: E402
import poverty  # noqa: E402
import tig_states  # noqa: E402

# Ohio State Legal Services' LawHelp Interactive grants (data/national_grants.json).
LHI = {2014: 725200, 2016: 808000, 2017: 751250, 2018: 783000, 2019: 790000, 2020: 526400, 2021: 265000}
WITH = {"2014-2019": 19722832, "2020-2025": 28416786.03, "2014-2025": 48139618.03}
# Less 3,857,450 (2014, 2016-2019) and 791,400 (2020, 2021).
WITHOUT = {"2014-2019": 15865382, "2020-2025": 27625386.03, "2014-2025": 43490768.03}
POVERTY = 42301792

# Ohio without them, read by hand from the four data files: 2014 $94,150;
# 2016 $46,576; 2018 $209,750; 2019 $162,500; 2021 $218,621 + $35,000;
# 2023 $215,070; 2024 $35,000 x 2; 2025 $165,756 + $35,000. Its only 2017 and
# 2020 grants were for LawHelp Interactive.
OHIO = {"rounds": 8, "2014-2019": 512976, "2020-2025": 739447, "2014-2025": 1252423}
# Ohio's share of TIG dollars and index (share over its 3.6% of the poverty
# population, 1,527,900 people), worked by hand to one decimal.
OHIO_SHARE = {"with": ("22.2", "5.4", "12.3"), "without": ("3.2", "2.7", "2.9")}
OHIO_INDEX = {"with": ("6.1", "1.5", "3.4"), "without": ("0.9", "0.7", "0.8")}
# Every other state's index rises by the ratio of the totals.
RISE = ("24.3", "2.9", "10.7")
SIX = ["CA", "FL", "IL", "MI", "MT", "PA"]
NEVER = ["GU", "MD", "MP", "RI", "VI"]


def compare(rows):
    areas = basic_field.load()["service_areas"]
    printed = poverty.load()["service_areas"]
    return tig_states.compare(rows, areas, printed)


class Data(unittest.TestCase):
    def test_grants(self):
        national = tig_states.load_national()
        self.assertEqual(len(national["grants"]), 7)
        self.assertEqual({g["year"]: g["amount_usd"] for g in national["grants"]}, LHI)
        for g in national["grants"]:
            self.assertEqual(g["state"], "OH")
            self.assertEqual(g["service"], "LawHelp Interactive")
            self.assertIn("LawHelp Interactive", g["quote"])
            self.assertTrue(g["grantee_as_printed"].startswith("Ohio State Legal Services"))
            self.assertTrue(g["source"].startswith("https://"))
        self.assertEqual(national["license"], "CC BY 4.0")


class SetAside(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all = tig_states.build()
        cls.rest = tig_states.set_aside(cls.all, tig_states.load_national())

    def test_removes_seven(self):
        self.assertEqual(len(self.all) - len(self.rest), 7)
        gone = sum(g["amount_usd"] for g in self.all) - sum(g["amount_usd"] for g in self.rest)
        self.assertAlmostEqual(gone, sum(LHI.values()), places=2)
        self.assertEqual(sum(LHI.values()), 4648850)

    def test_rounds(self):
        before = tig_states.round_totals(self.all)
        after = tig_states.round_totals(self.rest)
        self.assertEqual(sorted(after), list(tig_states.YEARS))
        for year in tig_states.YEARS:
            cut = LHI.get(year, 0)
            self.assertEqual(after[year]["grants"], before[year]["grants"] - (1 if cut else 0), year)
            self.assertAlmostEqual(after[year]["usd"], before[year]["usd"] - cut, places=2, msg=year)

    def test_input_unchanged(self):
        self.assertEqual(len(self.all), 342)

    def test_no_match_raises(self):
        with self.assertRaises(ValueError):
            tig_states.set_aside(self.all, {"grants": [{"year": 2014, "state": "OH", "amount_usd": 1}]})
        with self.assertRaises(ValueError):
            tig_states.set_aside(self.rest, tig_states.load_national())


class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        grants = tig_states.build()
        cls.with_ = compare(grants)
        cls.without = compare(tig_states.set_aside(grants, tig_states.load_national()))
        cls.head = {"with": tig_states.headline(cls.with_), "without": tig_states.headline(cls.without)}

    def test_totals(self):
        for label in tig_states.PERIODS:
            self.assertAlmostEqual(sum(r[label]["tig_usd"] for r in self.with_), WITH[label], places=2)
            self.assertAlmostEqual(sum(r[label]["tig_usd"] for r in self.without), WITHOUT[label], places=2)
            self.assertAlmostEqual(WITH[label] - WITHOUT[label],
                                   sum(u for y, u in LHI.items() if y in tig_states.PERIODS[label]), places=2)

    def test_ohio(self):
        oh = {r["state"]: r for r in self.without}["OH"]
        self.assertEqual(oh["rounds"], OHIO["rounds"])
        self.assertEqual(oh["poverty_population"], 1527900)
        for label in tig_states.PERIODS:
            self.assertAlmostEqual(oh[label]["tig_usd"], OHIO[label], places=2)

    def test_ohio_share_and_index(self):
        for key, rows in (("with", self.with_), ("without", self.without)):
            oh = {r["state"]: r for r in rows}["OH"]
            for i, label in enumerate(tig_states.PERIODS):
                self.assertEqual("%.1f" % (100 * oh[label]["tig_share"]), OHIO_SHARE[key][i], (key, label))
                self.assertEqual("%.1f" % oh[label]["index"], OHIO_INDEX[key][i], (key, label))
            self.assertEqual("%.1f" % (100 * oh["poverty_share"]), "3.6")

    def test_other_states_scale(self):
        before = {r["state"]: r for r in self.with_}
        for r in self.without:
            if r["state"] == "OH":
                continue
            b = before[r["state"]]
            for label in tig_states.PERIODS:
                self.assertEqual(r[label]["tig_usd"], b[label]["tig_usd"], (r["state"], label))
                self.assertAlmostEqual(r[label]["index"], b[label]["index"] * WITH[label] / WITHOUT[label],
                                       places=9, msg=(r["state"], label))
        for i, label in enumerate(tig_states.PERIODS):
            self.assertEqual("%.1f" % (100 * (WITH[label] / WITHOUT[label] - 1)), RISE[i])

    def test_rounds(self):
        rounds = self.head["without"]["rounds"]
        self.assertEqual(rounds["10"], SIX)
        self.assertIn("OH", rounds["8"])
        self.assertEqual(rounds["0"], NEVER)
        self.assertEqual(self.head["with"]["rounds"]["10"], sorted(SIX + ["OH"]))

    def test_per_person(self):
        self.assertEqual("%.2f" % self.head["with"]["2014-2025"]["per_person_in_poverty"], "1.14")
        self.assertEqual("%.2f" % self.head["without"]["2014-2025"]["per_person_in_poverty"], "1.03")
        self.assertAlmostEqual(self.head["without"]["2014-2025"]["per_person_in_poverty"], WITHOUT["2014-2025"] / POVERTY)


class Cli(unittest.TestCase):
    def test_main_runs(self):
        for argv in (["--without-national"], ["--without-national", "--summary"],
                     ["--without-national", "--rounds"], ["--without-national", "--json"]):
            self.assertEqual(tig_states.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
