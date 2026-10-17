# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_2021  # noqa: E402

# (sum, sum in cents, difference from $4,268,938 in cents, rounds to it),
# each list summed by hand from the raw text of LSC's page and release in
# groups of five and cross-checked by page section.
TOTALS = [
    ("page", 426573784, -320016, False),
    ("release", 426893100, -700, False),
    ("reconciled", 426893784, -16, True),
]

# (section, grants, sum, smallest, largest), in cents.
SECTIONS = [
    ("TIG", 19, 375780320, 7566500, 34330636),
    ("TIP", 16, 50793464, 2000000, 3500000),
]

STATES = "AK CA CT DC FL GA HI IL KS KY LA MA ME MI MN MT NH OH OR PA SD TN VA WA".split()

# (year, previous grants, grants in the round, stated grants, round's priced
# grants in whole dollars, previous 'more than' plus the round)
CUMULATIVE = [
    (2022, 826, 33, 859, 4679135, 81679135),
    (2023, 859, 33, 892, 5157033, 86157033),
    (2024, 892, 32, 924, 6306081, 92306081),
    (2025, 924, 32, 955, 4064308, 95064308),
]


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2021.load()

    def test_urls(self):
        self.assertTrue(self.history["page"].startswith("https://www.lsc.gov/grants/technology-initiative-grant-program/"))
        self.assertTrue(self.history["page"].endswith("/2021-tig-award-project-descriptions"))
        self.assertTrue(self.history["release"].startswith("https://www.lsc.gov/press-release/"))
        for c in self.history["cumulative"]:
            self.assertTrue(c["source"].startswith("https://www.lsc.gov/press-release/"), c["source"])

    def test_cents(self):
        self.assertEqual(tig_2021.cents("$150, 593.60"), 15059360)
        self.assertEqual(tig_2021.cents("$172,743.88"), 17274388)
        self.assertEqual(tig_2021.cents("$35,000"), 3500000)
        self.assertEqual(tig_2021.cents("$1.5"), 150)
        self.assertEqual(tig_2021.rounded(426893784), 4268938)
        self.assertEqual(tig_2021.rounded(426573750), 4265738)
        self.assertEqual(tig_2021.money(426573784), "$4,265,737.84")
        self.assertEqual(tig_2021.money(3500000), "$35,000")
        self.assertEqual(tig_2021.signed(-16), "-$0.16")
        self.assertEqual(tig_2021.signed(0), "$0")

    def test_sections_in_page_order(self):
        sections = [g["section"] for g in self.history["grants"]]
        self.assertEqual(sections, ["TIG"] * 19 + ["TIP"] * 16)

    def test_states_hand_checked(self):
        self.assertEqual(sorted({g["state"] for g in self.history["grants"]}), STATES)
        for g in self.history["grants"]:
            self.assertIn(g["state"], tig.JURISDICTIONS, g["grantee"])

    def test_application_numbers(self):
        aps = [g["ap"] for g in self.history["grants"]]
        printed = [a for a in aps if a]
        self.assertEqual(len(printed), 33)
        self.assertEqual(len(printed), len(set(printed)))
        self.assertEqual([a for a in printed if not a.startswith("AP-")], ["AP19"])
        missing = [g["organization"] for g in self.history["grants"] if not g["ap"]]
        self.assertEqual(missing, ["Legal Aid Society of Middle Tennessee and the Cumberlands",
                                   "Neighborhood Legal Services Association"])

    def test_release_matches_awards_json(self):
        # The release's amounts are what data/awards.json already holds for 2021.
        mine = sorted((g["organization"], g["state"], tig_2021.cents(g["release"]) // 100)
                      for g in self.history["grants"])
        theirs = sorted((a["grantee"], a["state"], int(a["amount_usd"]))
                        for a in tig.load()["awards"] if a["year"] == 2021)
        self.assertEqual(mine, theirs)

    def test_heading_against_text(self):
        (h,) = self.history["headings"]
        (g,) = [g for g in self.history["grants"] if g["ap"] == h["ap"]]
        self.assertEqual((g["grantee"], g["organization"]), (h["heading"], h["release"]))
        self.assertTrue(h["text"].startswith(h["release"]))
        self.assertEqual(g["state"], "MA")

    def test_quotes_carry_the_figures(self):
        for s in self.history["statements"]:
            for k in ("grants", "organizations"):
                if s[k] is not None:
                    self.assertIn(str(s[k]), s["quote"])
            if s["usd"]:
                (kind, x), = s["usd"].items()
                if kind == "exactly":
                    self.assertIn(tig.dollars(x), s["quote"])
                else:
                    self.assertIn("$%d" % (x // 1000000), s["quote"].replace("$4 Million", "$4 million"))
        for c in self.history["cumulative"]:
            if c["grants"] is not None:
                self.assertIn(str(c["grants"]), c["quote"])
            (kind, x), = c["usd"].items()
            self.assertIn("$%d million" % (x // 1000000), c["quote"])
        self.assertIn(tig.dollars(self.history["round_2020"]["usd"]), self.history["round_2020"]["quote"])


class Totals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2021.load()

    def test_totals(self):
        got = [(r["sum"], r["sum_cents"], r["difference_cents"], r["rounds_to_stated"])
               for r in tig_2021.totals(self.history)]
        self.assertEqual(got, TOTALS)

    def test_release_sum_is_tig_py_2021(self):
        # tig.py's test pins the 2021 list at $4,268,931, $7 under the stated total.
        (release,) = [r for r in tig_2021.totals(self.history) if r["sum"] == "release"]
        self.assertEqual(release["sum_cents"], 4268931 * 100)

    def test_sections(self):
        got = [(r["section"], r["grants"], r["sum_cents"], r["min_cents"], r["max_cents"])
               for r in tig_2021.sections(self.history)]
        self.assertEqual(got, SECTIONS)
        self.assertEqual(sum(r[2] for r in SECTIONS), TOTALS[0][1])

    def test_two_amounts_differ(self):
        got = [(g["organization"], g["page"], g["release"]) for g in tig_2021.differ(self.history)]
        self.assertEqual(got, [("Legal Services of Greater Miami", "$174,774.94", "$177,774"),
                               ("Land of Lincoln Legal Aid", "$26,678", "$26,878")])
        # Each differs from the page in one digit.
        for _, page, release in got:
            a, b = page.split(".")[0], release
            self.assertEqual(len(a), len(b))
            self.assertEqual(sum(1 for x, y in zip(a, b) if x != y), 1)

    def test_other_amounts_cut_to_whole_dollars(self):
        cut = tig_2021.cut_to_dollars(self.history)
        self.assertEqual(len(cut), 8)
        page_cents = sum(tig_2021.cents(g["page"]) % 100 for g in self.history["grants"])
        self.assertEqual(page_cents, 684)
        for g in cut:
            self.assertEqual(tig_2021.cents(g["release"]), tig_2021.cents(g["page"]) // 100 * 100)
        # Rounding instead of cutting would change 7 of the 8.
        self.assertEqual(sum(1 for g in cut if tig_2021.cents(g["page"]) % 100 >= 50), 7)

    def test_only_both_swaps_reach_the_stated_total(self):
        got = [(r["swapped"], r["sum_cents"], r["rounds_to_stated"]) for r in tig_2021.swaps(self.history)]
        self.assertEqual(got, [
            ([], 426573784, False),
            (["Legal Services of Greater Miami"], 426873784, False),
            (["Land of Lincoln Legal Aid"], 426593784, False),
            (["Legal Services of Greater Miami", "Land of Lincoln Legal Aid"], 426893784, True),
        ])


class Statements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2021.load()
        cls.rows = tig_2021.statements(cls.history)

    def test_listed(self):
        self.assertEqual(tig_2021.listed(self.history), {"grants": 35, "organizations": 29, "states": 24})

    def test_every_count_fits(self):
        self.assertEqual(len(self.rows), 4)
        self.assertEqual([r for r in self.rows if r["wrong"]], [])

    def test_dollar_figures(self):
        got = [(r["source"], r["fits"]["page"], r["fits"]["release"], r["fits"]["reconciled"])
               for r in self.rows if r["usd"]]
        self.assertEqual(got, [
            ("page", True, True, True),
            ("release", True, True, True),
            ("release", False, False, True),
        ])

    def test_fits(self):
        self.assertTrue(tig_2021.fits({"exactly": 4268938}, 426893784))
        self.assertFalse(tig_2021.fits({"exactly": 4268938}, 426893100))
        self.assertTrue(tig_2021.fits({"more_than": 4000000}, 400000001))
        self.assertFalse(tig_2021.fits({"more_than": 4000000}, 400000000))
        self.assertTrue(tig_2021.fits({"nearly": 70000000}, 6999999999))
        self.assertIsNone(tig_2021.fits(None, 1))
        with self.assertRaises(ValueError):
            tig_2021.fits({"about": 1}, 1)


class Cumulative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2021.load()
        cls.rows = tig_2021.cumulative(cls.history, tig.load())

    def test_rows(self):
        got = [(r["year"], r["previous_grants"], r["round_grants"], r["stated_grants"], r["round_usd"],
                r["implied_usd_more_than"]) for r in self.rows]
        self.assertEqual(got, CUMULATIVE)

    def test_grants_chain_exact_until_2025(self):
        self.assertEqual([r["grants_difference"] for r in self.rows], [0, 0, 0, -1])

    def test_dollar_figures_all_hold_2024_most_below(self):
        below = [r["usd_below_implied"] for r in self.rows]
        self.assertEqual(below, [679135, 157033, 1306081, 64308])
        self.assertTrue(all(b > 0 for b in below))
        self.assertEqual([r["round_unpriced"] for r in self.rows], [0, 0, 0, 1])

    def test_step_2020(self):
        s = tig_2021.step_2020(self.history)
        self.assertEqual(s["before_2021_more_than"], 72731062)
        self.assertFalse(s["if_2020_includes_its_round"]["fits"])
        self.assertEqual(s["if_2020_includes_its_round"]["short_by_at_least"], 2731062)
        self.assertTrue(s["if_2020_excludes_its_round"]["fits"])
        self.assertEqual(s["if_2020_excludes_its_round"]["before_2021_less_than"], 73941298)


class Output(unittest.TestCase):
    def test_markdown_rows(self):
        history = tig_2021.load()
        awards = tig.load()
        table = tig_2021.totals_markdown(tig_2021.totals(history))
        self.assertEqual(len(table.splitlines()), 5)
        self.assertIn("| description page | 35 | $4,265,737.84 | $4,268,938 | -$3,200.16 | no |", table)
        self.assertIn("| release's amounts with the page's cents | 35 | $4,268,937.84 | $4,268,938 | -$0.16 | yes |", table)
        self.assertEqual(len(tig_2021.sections_markdown(tig_2021.sections(history)).splitlines()), 4)
        self.assertEqual(len(tig_2021.differ_markdown(history).splitlines()), 4)
        self.assertEqual(len(tig_2021.swaps_markdown(tig_2021.swaps(history)).splitlines()), 6)
        self.assertEqual(len(tig_2021.statements_markdown(tig_2021.statements(history)).splitlines()), 6)
        cumulative = tig_2021.cumulative_markdown(tig_2021.cumulative(history, awards))
        self.assertIn("| 2025 | 924 | 32 | 956 | 955 | -1 | $95,064,308 | $95,000,000 | $64,308 |", cumulative)

    def test_main_runs(self):
        for argv in ([], ["--sources"], ["--headlines"], ["--summary"]):
            self.assertEqual(tig_2021.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
