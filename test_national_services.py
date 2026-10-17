# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig_states  # noqa: E402

DATA = os.path.join(HERE, "data", "national_services.json")
SERVICES = ["LSNTAP", "A2J Author", "Stateside Legal", "Legal Navigator", "LawHelp.org"]
WHOLE = {(2016, "ID"): 251985, (2017, "ME"): 175250, (2017, "MI"): 209825, (2018, "AK"): 179879,
         (2018, "WA"): 297175, (2020, "ME"): 50000, (2020, "MI"): 259500, (2021, "HI"): 93290,
         (2022, "MI"): 598970}
# (grant, national part LSC prints or None)
PART = {(2014, "ME"): (138139, 75270), (2015, "WA"): (505660, 429960),
        (2017, "GA"): (134720, None), (2018, "NC"): (182000, None)}
COUNTS = {"LSNTAP": 3, "A2J Author": 4, "Stateside Legal": 3, "Legal Navigator": 2, "LawHelp.org": 1}

# Hand sums over the complete rounds (2015 is in no period). By state, whole
# grants: AK 179,879; HI 93,290; ID 251,985; ME 225,250; MI 1,068,295;
# WA 297,175.
WHOLE_USD = {"2014-2019": 1114114, "2020-2025": 1001760, "2014-2025": 2115874}
PART_USD = {"2014-2019": 454859, "2020-2025": 0, "2014-2025": 454859}
LHI_USD = {"2014-2019": 3857450, "2020-2025": 791400, "2014-2025": 4648850}
TOTAL = {"2014-2019": 19722832, "2020-2025": 28416786.03, "2014-2025": 48139618.03}
# Whole grants plus LawHelp Interactive's, per round.
BY_YEAR = {2014: 725200, 2016: 1059985, 2017: 1136325, 2018: 1260054, 2019: 790000,
           2020: 835900, 2021: 358290, 2022: 598970, 2023: 0, 2024: 0, 2025: 0}
# Share of all TIG dollars, worked by hand to one decimal.
SHARE = {"whole": ("5.6", "3.5", "4.4"), "with_lhi": ("25.2", "6.3", "14.1"),
         "with_lhi_and_parts": ("27.5", "6.3", "15.0")}


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def in_period(year, label):
    return year in tig_states.PERIODS[label] and year not in tig_states.PARTIAL


def period_sum(grants, label):
    return sum(g["amount_usd"] for g in grants if in_period(g["year"], label))


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load()

    def test_meta(self):
        self.assertEqual(self.data["license"], "CC BY 4.0")
        self.assertEqual([s["service"] for s in self.data["services"]], SERVICES)
        for s in self.data["services"]:
            self.assertIn("national", s["quote"])
            self.assertTrue(s["source"].startswith("https://www.lsc.gov/"))

    def test_grants(self):
        grants = self.data["grants"]
        self.assertEqual(len(grants), 13)
        self.assertEqual({(g["year"], g["state"]): g["amount_usd"] for g in grants if g["scope"] == "whole"}, WHOLE)
        self.assertEqual({(g["year"], g["state"]): (g["amount_usd"], g["national_part_usd"])
                          for g in grants if g["scope"] == "part"}, PART)
        for g in grants:
            self.assertIn(g["service"], SERVICES)
            self.assertIn(g["named_as"], g["quote"])
            self.assertTrue(g["source"].startswith("https://"))
            if g["scope"] == "whole":
                self.assertEqual(g["national_part_usd"], g["amount_usd"])
        counts = {}
        for g in grants:
            counts[g["service"]] = counts.get(g["service"], 0) + 1
        self.assertEqual(counts, COUNTS)

    def test_printed_parts_add_up(self):
        self.assertEqual(75270 + 62869, 138139)
        self.assertEqual(75700 + 429960, 505660)

    def test_considered(self):
        self.assertEqual(len(self.data["considered"]), 8)
        for c in self.data["considered"]:
            self.assertTrue(c["reason"])
            self.assertTrue(c["amount_printed"].startswith("$"))


class Match(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all = tig_states.build()
        cls.grants = load()["grants"]

    def test_each_matches_one_row(self):
        rest = tig_states.set_aside(self.all, {"grants": self.grants})
        self.assertEqual(len(self.all) - len(rest), 13)

    def test_no_overlap_with_lawhelp_interactive(self):
        rest = tig_states.set_aside(tig_states.set_aside(self.all, tig_states.load_national()),
                                    {"grants": self.grants})
        self.assertEqual(len(self.all) - len(rest), 20)

    def test_round_totals(self):
        totals = tig_states.round_totals(self.all)
        for label in tig_states.PERIODS:
            got = sum(t["usd"] for y, t in totals.items() if in_period(y, label))
            self.assertAlmostEqual(got, TOTAL[label], places=2, msg=label)


class Sums(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        grants = load()["grants"]
        cls.whole = [g for g in grants if g["scope"] == "whole"]
        cls.part = [g for g in grants if g["scope"] == "part"]
        cls.lhi = tig_states.load_national()["grants"]

    def test_periods(self):
        for label in tig_states.PERIODS:
            self.assertEqual(period_sum(self.whole, label), WHOLE_USD[label], label)
            self.assertEqual(period_sum(self.part, label), PART_USD[label], label)
            self.assertEqual(period_sum(self.lhi, label), LHI_USD[label], label)

    def test_by_year(self):
        for year, usd in BY_YEAR.items():
            got = sum(g["amount_usd"] for g in self.whole + self.lhi if g["year"] == year)
            self.assertEqual(got, usd, year)
        self.assertEqual(sum(BY_YEAR.values()), WHOLE_USD["2014-2025"] + LHI_USD["2014-2025"])

    def test_none_named_since_2023(self):
        for g in self.whole + self.part + self.lhi:
            self.assertLess(g["year"], 2023)

    def test_shares(self):
        for i, label in enumerate(tig_states.PERIODS):
            whole = WHOLE_USD[label]
            lhi = whole + LHI_USD[label]
            both = lhi + PART_USD[label]
            self.assertEqual("%.1f" % (100 * whole / TOTAL[label]), SHARE["whole"][i], label)
            self.assertEqual("%.1f" % (100 * lhi / TOTAL[label]), SHARE["with_lhi"][i], label)
            self.assertEqual("%.1f" % (100 * both / TOTAL[label]), SHARE["with_lhi_and_parts"][i], label)


if __name__ == "__main__":
    unittest.main()
