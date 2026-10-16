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
import tig  # noqa: E402

# Each round's listed grants, summed by hand from the releases.
LISTED = {2014: 2375000, 2015: 3800000, 2016: 3800000, 2017: 3800000,
          2018: 4404749, 2019: 4348143, 2020: 3138716, 2021: 4611046}
GRANTS = {2014: 11, 2015: 15, 2016: 11, 2017: 15, 2018: 15, 2019: 15, 2020: 11, 2021: 13}

# (source, LSC's count, grants listed, without the 2020 supplemental grants,
#  listed dollars in millions to two places)
RUNNING = [
    ("2020 release", 102, 101, 93, "26.88"),
    ("2021 release", 94, 101, 93, "26.88"),
    ("2022 release", 121, 129, 121, "36.24"),
    ("2023 release", 139, 147, 139, "41.29"),
    ("2024 release", 161, 169, 161, "46.72"),
    ("2025 release", 180, 188, 180, "52.28"),
    ("PBIF program page", 180, 188, 180, "52.28"),
]

NEVER = "AL AZ CT DE MS ND NH OK OR RI SD WY".split()


def later_awards():
    page = pbif.load()["awards"]
    return pbif_history.later(page, pbif.load_releases(), basic_field.load()["service_areas"])


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = pbif_history.load()

    def test_years(self):
        self.assertEqual([r["year"] for r in self.history["rounds"]], list(range(2014, 2022)))

    def test_sources(self):
        for r in self.history["rounds"]:
            self.assertTrue(r["url"].startswith("https://www.lsc.gov/press-release/"), r["url"])
        for s in self.history["statements"]:
            self.assertTrue(s["url"].startswith("https://www.lsc.gov/"), s["url"])

    def test_states(self):
        for r in self.history["rounds"]:
            for g in r["grants"]:
                self.assertIn(g["state"], tig.JURISDICTIONS, g["grantee"])

    def test_amounts_parse(self):
        for r in self.history["rounds"]:
            for g in r["grants"]:
                self.assertGreater(pbif_history.usd(g["printed"]), 50000, g["grantee"])

    def test_statement_quotes(self):
        for s in self.history["statements"]:
            self.assertIn(str(s["count"]), s["quote"])
            self.assertIn(s["dollars"].replace("more than ", ""), s["quote"])


class Rounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r["year"]: r for r in pbif_history.rounds(pbif_history.load())}

    def test_listed_totals(self):
        self.assertEqual({y: r["listed_usd"] for y, r in self.rows.items()}, LISTED)
        self.assertEqual({y: r["grants"] for y, r in self.rows.items()}, GRANTS)

    def test_ninety_five_percent(self):
        for year in (2014, 2015, 2016, 2017):
            self.assertEqual(self.rows[year]["listed_usd"] * 100, self.rows[year]["fund_usd"] * 95, year)
        self.assertNotEqual(self.rows[2018]["listed_usd"] * 100, self.rows[2018]["fund_usd"] * 95)

    def test_organizations_match_stated(self):
        for year, r in self.rows.items():
            if year != 2020:
                self.assertEqual(r["organizations"], r["stated_organizations"], year)
        self.assertEqual(self.rows[2019]["organizations"], 14)
        self.assertEqual(self.rows[2021]["organizations"], 12)

    def test_stated_totals(self):
        self.assertEqual(self.rows[2019]["listed_usd"] - self.rows[2019]["stated_usd"], 958)
        self.assertEqual(self.rows[2020]["stated_usd"], self.rows[2019]["stated_usd"])
        self.assertEqual(self.rows[2020]["stated_usd"] - self.rows[2020]["listed_usd"], 1208469)
        self.assertAlmostEqual(self.rows[2021]["stated_usd"] - self.rows[2021]["listed_usd"], 6.97, places=2)

    def test_round_usd(self):
        self.assertEqual(self.rows[2020]["round_usd"], 4347185)
        self.assertEqual(self.rows[2019]["round_usd"], 4348143)
        through_2020 = sum(r["round_usd"] for y, r in self.rows.items() if y <= 2020)
        self.assertEqual(through_2020, 26875077)
        funds = sum(r["fund_usd"] for y, r in self.rows.items() if y <= 2020)
        self.assertEqual(funds, 28000000)


class Running(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.later = later_awards()
        cls.rows = pbif_history.running(pbif_history.load(), cls.later)

    def test_later_rounds(self):
        count = lambda y: sum(1 for a in self.later if a["year"] == y)  # noqa: E731
        self.assertEqual([count(y) for y in (2022, 2023, 2024, 2025)], [15, 18, 22, 19])

    def test_against_statements(self):
        got = [(r["source"], r["count"], r["listed"], r["listed_named"], "%.2f" % (r["listed_usd"] / 1e6))
               for r in self.rows]
        self.assertEqual(got, RUNNING)

    def test_counts_fit_from_2022(self):
        for r in self.rows:
            if r["through"] >= 2022:
                self.assertEqual(r["count"], r["listed_named"], r["source"])
            else:
                self.assertEqual(r["count"] - r["listed_named"], 1 if r["unit"] == "projects" else 9, r["source"])


class States(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.early, cls.late = pbif_history.jurisdictions(pbif_history.load(), later_awards())
        cls.rows = dict(pbif_history.state_rows(cls.early, cls.late))

    def test_program_page_states(self):
        every = self.rows["2014-2025"]
        self.assertEqual(len([j for j in every if j in pbif_history.STATES]), 38)
        self.assertEqual(sorted(j for j in every if j not in pbif_history.STATES), ["DC", "VI"])

    def test_never(self):
        self.assertEqual(sorted(self.rows["Never, 2014-2025"]), NEVER)

    def test_earlier_grants_to_neither_states(self):
        # The main README's "neither" states for 2021-2025 that had PBIF before 2022.
        for state in ("IN", "MD", "UT"):
            self.assertIn(state, self.early)
            self.assertNotIn(state, self.late)

    def test_only_rows(self):
        self.assertEqual(sorted(self.rows["2022-2025 only"]), ["KS", "NC", "NV", "SC", "TN", "VI"])
        self.assertEqual(len(self.rows["2014-2021 only"]), 12)


class Output(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = pbif_history.load()
        cls.later = later_awards()
        with open(os.path.join(HERE, "docs", "pbif-history.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_rounds_table_is_current(self):
        self.assertIn(pbif_history.rounds_markdown(pbif_history.rounds(self.history)), self.doc)

    def test_running_table_is_current(self):
        self.assertIn(pbif_history.running_markdown(pbif_history.running(self.history, self.later)), self.doc)

    def test_states_table_is_current(self):
        rows = pbif_history.state_rows(*pbif_history.jurisdictions(self.history, self.later))
        self.assertIn(pbif_history.states_markdown(rows), self.doc)

    def test_main_runs(self):
        for argv in ([], ["--running"], ["--states"], ["--summary"]):
            self.assertEqual(pbif_history.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
