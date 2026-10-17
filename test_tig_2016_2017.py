# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_2016_2017  # noqa: E402
import tig_history  # noqa: E402

# (year, grants, amounts on the page, sum of the page's amounts, sum with gaps
# filled, grants with an amount on lsc.gov today), each list summed by hand
# from the raw text of LSC's documents.
TOTALS = [
    (2016, 34, 33, 4143487, 4203221, 18),
    (2017, 25, 25, 3927974, 3927974, 25),
]

# (year, source, amounts printed, same as the page, fills a gap)
SOURCES = [
    (2016, "release", 7, 7, []),
    (2016, "bundle", 16, 16, []),
    (2016, "pbif_bundle", 2, 1, ["16007"]),
    (2017, "release", 25, 25, []),
    (2017, "pbif_bundle", 6, 6, []),
]

# (grants, organizations, states with DC, territories), counted by hand.
LISTED = {2016: (34, 27, 20, 1), 2017: (25, 22, 18, 0)}

STATES_2016 = "AS AZ CA CT FL IA ID IL MI MT NE NY OH OK PA SC TN TX UT VA WA".split()
STATES_2017 = "FL GA HI KS LA MA ME MI MN MT NM NY OH PA TN VA VT WA".split()


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2016_2017.load()
        cls.rounds = {r["year"]: r for r in cls.history["rounds"]}

    def test_years(self):
        self.assertEqual([r["year"] for r in self.history["rounds"]], [2016, 2017])

    def test_urls(self):
        for r in self.history["rounds"]:
            self.assertTrue(r["page"].startswith("https://web.archive.org/web/2019"), r["page"])
            self.assertTrue(r["page"].endswith(r["page_today"]), r["page"])
            for url in r["sources"].values():
                self.assertTrue(url.startswith("https://www.lsc.gov/press-release/"), url)
            self.assertEqual(set(r["amounts"]), set(r["sources"]))

    def test_states_hand_checked(self):
        self.assertEqual(sorted({g["state"] for g in self.rounds[2016]["grants"]}), STATES_2016)
        self.assertEqual(sorted({g["state"] for g in self.rounds[2017]["grants"]}), STATES_2017)
        for r in self.history["rounds"]:
            for g in r["grants"]:
                self.assertIn(g["state"], tig.JURISDICTIONS + tig_history.TERRITORIES, g["grantee"])

    def test_tig_numbers(self):
        for r in self.history["rounds"]:
            numbers = [g["tig"] for g in r["grants"]]
            for n in numbers:
                self.assertRegex(n, r"^%d\d{3}$" % (r["year"] % 100))
            self.assertEqual(len(numbers), len(set(numbers)), r["year"])
            self.assertEqual(numbers, sorted(numbers), r["year"])

    def test_amounts_name_grants_of_the_round(self):
        for r in self.history["rounds"]:
            numbers = {g["tig"] for g in r["grants"]}
            for source, amounts in r["amounts"].items():
                self.assertLessEqual(set(amounts), numbers, source)
                for printed in amounts.values():
                    self.assertGreater(tig_history.usd(printed), 25000)
            for t in r["grantee_totals"]:
                self.assertLessEqual(set(t["tigs"]), numbers)
                names = {g["grantee"] for g in r["grants"] if g["tig"] in t["tigs"]}
                self.assertEqual(names, {t["grantee"]})
            for h in r["headings"]:
                self.assertIn(h["tig"], r["amounts"][h["source"]])

    def test_only_iowa_has_no_page_amount(self):
        missing = [(r["year"], g["grantee"]) for r in self.history["rounds"] for g in r["grants"] if not g["printed"]]
        self.assertEqual(missing, [(2016, "Iowa Legal Aid")])

    def test_quotes_carry_the_counts(self):
        for r in self.history["rounds"]:
            for s in r["statements"]:
                stated = [s[k] for k in ("grants", "organizations", "states") if s[k] is not None]
                self.assertTrue(stated or s["usd"], s["quote"])
                for n in stated:
                    self.assertIn(str(n), s["quote"])
                if s["territories"] == 1:
                    self.assertIn("one territory", s["quote"])
                if s["usd"]:
                    (kind, x), = s["usd"].items()
                    self.assertIn("$%g" % (x / 1e6), s["quote"].replace(" Million", " million"))


class Totals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2016_2017.load()

    def test_totals(self):
        got = [(r["year"], r["grants"], r["printed"], r["page_usd"], r["filled_usd"], r["on_lsc_today"])
               for r in tig_2016_2017.totals(self.history)]
        self.assertEqual(got, TOTALS)

    def test_iowa_filled_from_pbif_release(self):
        rows = tig_2016_2017.totals(self.history)
        self.assertEqual([[tuple(x) for x in r["filled_from"]] for r in rows], [[("16007", "pbif_bundle")], []])
        self.assertEqual(rows[0]["filled_usd"] - rows[0]["page_usd"], 59734)
        # Without Iowa the page's list is $56,513 short of $4.2 million;
        # Iowa's $59,734 takes it $3,221 over.
        self.assertEqual(4200000 - rows[0]["page_usd"], 56513)
        self.assertEqual(rows[0]["filled_usd"] - 4200000, 3221)

    def test_sources(self):
        got = [(r["year"], r["source"], r["printed"], r["same"], r["fills"]) for r in tig_2016_2017.sources(self.history)]
        self.assertEqual(got, SOURCES)
        for r in tig_2016_2017.sources(self.history):
            self.assertEqual(r["differ"], [], (r["year"], r["source"]))

    def test_grantee_totals(self):
        rows = tig_2016_2017.grantee_totals(self.history)
        self.assertEqual(len(rows), 7)
        differ = [(r["year"], r["source"], r["grantee"], r["stated_usd"], r["parts_usd"], r["difference"])
                  for r in rows if r["difference"]]
        self.assertEqual(differ, [(2016, "bundle", "Idaho Legal Aid Services, Inc.", 322919, 332919, -10000)])

    def test_heading_carried_from_previous_release(self):
        r = tig_2016_2017.load()["rounds"][1]
        (h,) = r["headings"]
        self.assertEqual((h["tig"], h["heading"]), ("17005", "$97,750"))
        self.assertEqual(r["amounts"]["pbif_bundle"]["17005"], "$185,250")
        self.assertEqual(r["amounts"]["pbif_bundle"]["17041"], h["heading"])


class Statements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2016_2017.load()
        cls.rows = tig_2016_2017.statements(cls.history)

    def test_listed(self):
        got = {r["year"]: tuple(tig_2016_2017.listed(r)[k] for k in ("grants", "organizations", "states", "territories"))
               for r in self.history["rounds"]}
        self.assertEqual(got, LISTED)

    def test_every_count_fits(self):
        self.assertEqual(len(self.rows), 9)
        self.assertEqual([r for r in self.rows if r["wrong"]], [])

    def test_dollar_figures(self):
        got = [(r["year"], r["source"], r["fits_page"], r["fits_filled"]) for r in self.rows if r["usd"]]
        self.assertEqual(got, [
            (2016, "page", False, True),
            (2016, "release", False, True),
            (2016, "bundle", False, True),
            (2017, "release", True, True),
        ])

    def test_fits(self):
        self.assertTrue(tig_2016_2017.fits({"about": 4200000}, 4203221))
        self.assertFalse(tig_2016_2017.fits({"about": 4200000}, 4143487))
        self.assertTrue(tig_2016_2017.fits({"about": 4200000}, 4150000))
        self.assertFalse(tig_2016_2017.fits({"more_than": 4200000}, 4200000))
        self.assertTrue(tig_2016_2017.fits({"nearly": 4000000}, 3927974))
        self.assertIsNone(tig_2016_2017.fits(None, 1))
        self.assertIsNone(tig_2016_2017.fits({"nearly": 1}, None))
        with self.assertRaises(ValueError):
            tig_2016_2017.fits({"exactly": 1}, 1)


class Output(unittest.TestCase):
    def test_markdown_rows(self):
        history = tig_2016_2017.load()
        self.assertEqual(len(tig_2016_2017.totals_markdown(tig_2016_2017.totals(history)).splitlines()), 4)
        self.assertEqual(len(tig_2016_2017.sources_markdown(tig_2016_2017.sources(history)).splitlines()), 7)
        self.assertEqual(len(tig_2016_2017.grantee_totals_markdown(tig_2016_2017.grantee_totals(history)).splitlines()), 9)
        table = tig_2016_2017.statements_markdown(tig_2016_2017.statements(history))
        self.assertEqual(len(table.splitlines()), 11)
        self.assertIn("| 2016 | release | 34 grants, 27 organizations, 20 states, 1 territory | none | - | - |", table)
        self.assertIn("| 2016 | description page (archived) | 34 grants, 27 organizations, about $4,200,000 | none | no | yes |", table)

    def test_main_runs(self):
        for argv in ([], ["--sources"], ["--headlines"], ["--summary"]):
            self.assertEqual(tig_2016_2017.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
