# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_history  # noqa: E402

# (year, source, sum of the list, difference from LSC's stated total), each
# list summed by hand from the raw text of LSC's pages.
TOTALS = [
    (2018, "page", 3892257, 8000),
    (2018, "release", 3862257, -22000),
    (2019, "page", 4231402, 684),
    (2019, "release", 4231392, 674),
    (2020, "page", 3941298, 0),
    (2020, "release", 3941298, 0),
]

# (year, grantee, source, amount there, page list with only that amount changed)
DIFFERENCES = [
    (2018, "Northwest Justice Project", "release", "$267,175", 3862257),
    (2018, "Legal Assistance Foundation", "bundle", "$264,000", 3890257),
    (2018, "Alaska Legal Services Corporation", "bundle", "$171,879", 3884257),
    (2019, "South Carolina Legal Services, Inc.", "release", "$155,940", 4231392),
    (2020, "Michigan Advocacy Program", "release", "$70,895", 3941297),
    (2020, "Statewide Legal Services of Connecticut, Inc.", "release", "$143,584", 3941299),
]

# (grants, organizations, states with DC and territories), counted by hand.
LISTED = {2018: (26, 24, 21), 2019: (30, 29, 20), 2020: (26, 24, 20), 2021: (35, 29, 24),
          2022: (33, 29, 25), 2023: (33, 29, 22), 2024: (32, 29, 22), 2025: (32, 29, 21)}

NOT_FITTING = [
    (2019, "page", ["organizations"]),
    (2019, "release", ["organizations"]),
    (2020, "page", ["organizations"]),
    (2021, "index", ["organizations"]),
    (2022, "index", ["organizations"]),
    (2024, "headline", ["organizations"]),
    (2025, "release", ["states"]),
    (2025, "index", ["organizations"]),
]

STATES_2019 = "AK AS CA CO DC GA IL KY MI MN MO MS NH NJ OH PA SC VT WA WY".split()


def awards():
    return tig.load()["awards"]


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_history.load()

    def test_years(self):
        self.assertEqual([r["year"] for r in self.history["rounds"]], [2018, 2019, 2020])

    def test_sources(self):
        for r in self.history["rounds"]:
            for key in ["page"] + r["complete"] + (["bundle"] if "bundle" in r else []):
                self.assertTrue(r[key].startswith("https://www.lsc.gov/"), r[key])
        for h in self.history["headlines"]:
            self.assertTrue(h["url"].startswith("https://www.lsc.gov/"), h["url"])
            self.assertIn(h["source"], tig_history.SOURCES)

    def test_states(self):
        for r in self.history["rounds"]:
            for g in r["grants"]:
                self.assertIn(g["state"], tig.JURISDICTIONS + tig_history.TERRITORIES, g["grantee"])

    def test_states_2019_hand_checked(self):
        r = self.history["rounds"][1]
        self.assertEqual(sorted({g["state"] for g in r["grants"]}), STATES_2019)

    def test_amounts_parse(self):
        for r in self.history["rounds"]:
            for g in r["grants"]:
                self.assertGreater(tig_history.usd(g["printed"]), 25000, g["grantee"])
                for printed in g.get("other", {}).values():
                    self.assertGreater(tig_history.usd(printed), 25000, g["grantee"])

    def test_tig_numbers(self):
        for r in self.history["rounds"]:
            numbers = [g["tig"] for g in r["grants"] if g["tig"] is not None]
            for n in numbers:
                self.assertRegex(n, r"^%d\d{3}$" % (r["year"] % 100))
            repeated = sorted({n for n in numbers if numbers.count(n) > 1})
            self.assertEqual(repeated, ["19044"] if r["year"] == 2019 else [], r["year"])
        unnumbered = [(r["year"], g["grantee"]) for r in self.history["rounds"] for g in r["grants"] if g["tig"] is None]
        self.assertEqual(unnumbered, [(2019, "Atlanta Legal Aid Society, Inc.")])

    def test_other_sources_exist(self):
        for r in self.history["rounds"]:
            for g in r["grants"]:
                for source in g.get("other", {}):
                    self.assertIn(source, r, g["grantee"])

    def test_quotes_carry_the_counts(self):
        for h in self.history["headlines"]:
            stated = [h[k] for k, _ in tig_history.COUNTS if h[k] is not None]
            self.assertTrue(stated, h["quote"])
            for n in stated:
                self.assertIn(str(n), h["quote"])


class Totals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_history.load()

    def test_totals(self):
        got = [(r["year"], r["source"], r["listed_usd"], r["difference"]) for r in tig_history.totals(self.history)]
        self.assertEqual(got, TOTALS)

    def test_differences(self):
        got = [(r["year"], r["grantee"], r["source"], r["other"], r["total_usd"])
               for r in tig_history.differences(self.history)]
        self.assertEqual(got, DIFFERENCES)

    def test_only_alaska_reaches_2018_total(self):
        fits = [(r["year"], r["grantee"]) for r in tig_history.differences(self.history) if r["equals_stated"]]
        self.assertEqual(fits, [(2018, "Alaska Legal Services Corporation")])

    def test_2020_release_differences_cancel(self):
        rows = [r for r in tig_history.differences(self.history) if r["year"] == 2020]
        self.assertEqual(sum(tig_history.usd(r["other"]) - tig_history.usd(r["page"]) for r in rows), 0)
        michigan = [g for g in self.history["rounds"][2]["grants"] if g["grantee"] == "Michigan Advocacy Program"]
        self.assertEqual(sum(tig_history.amount(g, "release") for g in michigan), 399045)

    def test_2019_has_no_single_amount_fix(self):
        # No grant of the 2019 list equals the $684 surplus, so dropping or
        # mistyping one whole grant does not explain it.
        r = self.history["rounds"][1]
        self.assertNotIn(684, [tig_history.usd(g["printed"]) for g in r["grants"]])


class Headlines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_history.load()
        cls.awards = awards()
        cls.rows = tig_history.headlines(cls.history, cls.awards)

    def test_listed(self):
        got = {y: (c["grants"], c["organizations"], c["states"])
               for y, c in tig_history.listed(self.history, self.awards).items()}
        self.assertEqual(got, LISTED)

    def test_not_fitting(self):
        self.assertEqual([(r["year"], r["source"], r["wrong"]) for r in self.rows if r["wrong"]], NOT_FITTING)

    def test_grants_counted_as_organizations(self):
        # Three of the statements that miss give the number of grants as the
        # number of organizations.
        for year, source in ((2019, "page"), (2020, "page"), (2022, "index")):
            r = [r for r in self.rows if (r["year"], r["source"]) == (year, source)][0]
            self.assertEqual(r["organizations"], r["listed"]["grants"], year)

    def test_2024_states_count_dc(self):
        states = {a["state"] for a in self.awards if a["year"] == 2024}
        self.assertIn("DC", states)
        self.assertEqual(len(states - {"DC"}), 21)

    def test_readme_earlier_rounds(self):
        # The main README's statements about 2018-2020.
        early = {}
        for r in self.history["rounds"]:
            for g in r["grants"]:
                early.setdefault(g["state"], []).append((r["year"], tig_history.usd(g["printed"])))
        for state in ("IA", "MD", "RI"):
            self.assertNotIn(state, early)
        self.assertEqual(early["IN"], [(2018, 27000), (2020, 125384)])
        self.assertEqual(early["UT"], [(2018, 308047), (2020, 57900)])
        self.assertEqual(early["WY"], [(2018, 27000), (2019, 105000)])
        self.assertEqual(early["NJ"], [(2019, 27500)])


class Output(unittest.TestCase):
    def test_markdown_rows(self):
        history = tig_history.load()
        self.assertEqual(len(tig_history.totals_markdown(tig_history.totals(history)).splitlines()), 2 + len(TOTALS))
        self.assertEqual(len(tig_history.differences_markdown(tig_history.differences(history)).splitlines()),
                         2 + len(DIFFERENCES))
        table = tig_history.headlines_markdown(tig_history.headlines(history, awards()))
        self.assertIn("| 2025 | index page | 32 grants, 22 organizations | 32 | 29 | 21 | no (organizations) |", table)

    def test_signed(self):
        self.assertEqual(tig_history.signed(8000), "+$8,000")
        self.assertEqual(tig_history.signed(-22000), "-$22,000")
        self.assertEqual(tig_history.signed(0), "$0")

    def test_main_runs(self):
        for argv in ([], ["--amounts"], ["--headlines"], ["--summary"]):
            self.assertEqual(tig_history.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
