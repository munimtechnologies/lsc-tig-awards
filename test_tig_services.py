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

# The nine grants of data/national_services.json with scope 'whole'.
WHOLE = {(2016, "ID"): 251985, (2017, "ME"): 175250, (2017, "MI"): 209825, (2018, "AK"): 179879,
         (2018, "WA"): 297175, (2020, "ME"): 50000, (2020, "MI"): 259500, (2021, "HI"): 93290,
         (2022, "MI"): 598970}
# What each state loses, by period, summed by hand from WHOLE.
DROP = {"AK": (179879, 0, 179879), "HI": (0, 93290, 93290), "ID": (251985, 0, 251985),
        "ME": (175250, 50000, 225250), "MI": (209825, 858470, 1068295), "WA": (297175, 0, 297175)}
WITH = {"2014-2019": 19722832, "2020-2025": 28416786.03, "2014-2025": 48139618.03}
# Less 1,114,114 (2014-2019) and 1,001,760 (2020-2025).
WITHOUT_SERVICES = {"2014-2019": 18608718, "2020-2025": 27415026.03, "2014-2025": 46023744.03}
# Without LawHelp Interactive's seven grants (3,857,450 and 791,400), as in
# test_tig_national.py, then without both.
WITHOUT_LHI = {"2014-2019": 15865382, "2020-2025": 27625386.03, "2014-2025": 43490768.03}
WITHOUT_BOTH = {"2014-2019": 14751268, "2020-2025": 26623626.03, "2014-2025": 41374894.03}
POVERTY = 42301792
# Every state none of the 16 set-aside grants counts to: its index rises by
# the ratio of the totals, worked by hand to one decimal (percent).
RISE = {"services": ("6.0", "3.7", "4.6"), "both": ("33.7", "6.7", "16.3")}
PER_PERSON = {"services": "1.09", "both": "0.98"}
# Ohio with both set aside: dollars as in test_tig_national.py, over 3.6% of
# the poverty population (1,527,900 people); share and index by hand.
OHIO = {"2014-2019": 512976, "2020-2025": 739447, "2014-2025": 1252423}
OHIO_SHARE = ("3.5", "2.8", "3.0")
OHIO_INDEX = ("1.0", "0.8", "0.8")


def compare(rows):
    areas = basic_field.load()["service_areas"]
    printed = poverty.load()["service_areas"]
    return tig_states.compare(rows, areas, printed)


class Load(unittest.TestCase):
    def test_whole_only(self):
        services = tig_states.load_services()
        self.assertEqual({(g["year"], g["state"]): g["amount_usd"] for g in services["grants"]}, WHOLE)
        for g in services["grants"]:
            self.assertEqual(g["scope"], "whole")

    def test_hand_sums(self):
        for i, label in enumerate(tig_states.PERIODS):
            self.assertEqual(sum(d[i] for d in DROP.values()),
                             sum(u for (y, s), u in WHOLE.items() if y in tig_states.PERIODS[label]), label)
            self.assertAlmostEqual(WITH[label] - WITHOUT_SERVICES[label], sum(d[i] for d in DROP.values()), places=2)
        self.assertEqual(sum(WHOLE.values()), 2115874)


class SetAside(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all = tig_states.build()
        cls.rest = tig_states.set_aside(cls.all, tig_states.load_services())
        cls.both = tig_states.set_aside(tig_states.set_aside(cls.all, tig_states.load_national()),
                                        tig_states.load_services())

    def test_removes_nine(self):
        self.assertEqual(len(self.all) - len(self.rest), 9)
        self.assertEqual(len(self.all) - len(self.both), 16)

    def test_part_grants_stay(self):
        for year, state, usd in ((2014, "ME", 138139), (2015, "WA", 505660), (2017, "GA", 134720), (2018, "NC", 182000)):
            hits = [g for g in self.rest if g["year"] == year and g["state"] == state and g["amount_usd"] == usd]
            self.assertEqual(len(hits), 1, (year, state))

    def test_rounds(self):
        before = tig_states.round_totals(self.all)
        after = tig_states.round_totals(self.rest)
        for year in tig_states.YEARS:
            cut = [u for (y, s), u in WHOLE.items() if y == year]
            self.assertEqual(after[year]["grants"], before[year]["grants"] - len(cut), year)
            self.assertAlmostEqual(after[year]["usd"], before[year]["usd"] - sum(cut), places=2, msg=year)

    def test_twice_raises(self):
        with self.assertRaises(ValueError):
            tig_states.set_aside(self.rest, tig_states.load_services())


class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        grants = tig_states.build()
        lhi = tig_states.set_aside(grants, tig_states.load_national())
        cls.with_ = compare(grants)
        cls.lhi = compare(lhi)
        cls.services = compare(tig_states.set_aside(grants, tig_states.load_services()))
        cls.both = compare(tig_states.set_aside(lhi, tig_states.load_services()))

    def test_totals(self):
        for label in tig_states.PERIODS:
            self.assertAlmostEqual(sum(r[label]["tig_usd"] for r in self.services), WITHOUT_SERVICES[label], places=2)
            self.assertAlmostEqual(sum(r[label]["tig_usd"] for r in self.both), WITHOUT_BOTH[label], places=2)

    def test_six_states_drop(self):
        before = {r["state"]: r for r in self.with_}
        after = {r["state"]: r for r in self.services}
        for state, drops in DROP.items():
            for i, label in enumerate(tig_states.PERIODS):
                self.assertAlmostEqual(after[state][label]["tig_usd"], before[state][label]["tig_usd"] - drops[i],
                                       places=2, msg=(state, label))
            self.assertLessEqual(after[state]["rounds"], before[state]["rounds"])

    def test_other_states_scale(self):
        for rows, base, total, key in ((self.services, self.with_, WITHOUT_SERVICES, "services"),
                                       (self.both, self.with_, WITHOUT_BOTH, "both")):
            before = {r["state"]: r for r in base}
            for r in rows:
                if r["state"] in DROP or (key == "both" and r["state"] == "OH"):
                    continue
                b = before[r["state"]]
                self.assertEqual(r["rounds"], b["rounds"], r["state"])
                for label in tig_states.PERIODS:
                    self.assertEqual(r[label]["tig_usd"], b[label]["tig_usd"], (r["state"], label))
                    self.assertAlmostEqual(r[label]["index"], b[label]["index"] * WITH[label] / total[label],
                                           places=9, msg=(key, r["state"], label))
            for i, label in enumerate(tig_states.PERIODS):
                self.assertEqual("%.1f" % (100 * (WITH[label] / total[label] - 1)), RISE[key][i], (key, label))

    def test_ohio(self):
        lhi = {r["state"]: r for r in self.lhi}["OH"]
        oh = {r["state"]: r for r in self.both}["OH"]
        for i, label in enumerate(tig_states.PERIODS):
            self.assertAlmostEqual(oh[label]["tig_usd"], OHIO[label], places=2)
            self.assertAlmostEqual(oh[label]["index"], lhi[label]["index"] * WITHOUT_LHI[label] / WITHOUT_BOTH[label],
                                   places=9, msg=label)
            self.assertEqual("%.1f" % (100 * oh[label]["tig_share"]), OHIO_SHARE[i], label)
            self.assertEqual("%.1f" % oh[label]["index"], OHIO_INDEX[i], label)

    def test_per_person(self):
        for key, rows, total in (("services", self.services, WITHOUT_SERVICES), ("both", self.both, WITHOUT_BOTH)):
            head = tig_states.headline(rows)
            self.assertEqual(head["poverty_population"], POVERTY)
            self.assertEqual("%.2f" % head["2014-2025"]["per_person_in_poverty"], PER_PERSON[key])
            self.assertAlmostEqual(head["2014-2025"]["per_person_in_poverty"], total["2014-2025"] / POVERTY)

    def test_never(self):
        head = tig_states.headline(self.both)
        for state in ["GU", "MD", "MP", "RI", "VI"]:
            self.assertIn(state, head["rounds"]["0"])


class Cli(unittest.TestCase):
    def test_main_runs(self):
        for argv in (["--without-services"], ["--without-services", "--summary"],
                     ["--without-national", "--without-services", "--summary"],
                     ["--without-national", "--without-services", "--rounds"],
                     ["--without-services", "--json"]):
            self.assertEqual(tig_states.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
