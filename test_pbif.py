# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import basic_field  # noqa: E402
import pbif  # noqa: E402
import tig  # noqa: E402

# Every heading on LSC's PBIF Awards page, read separately from the parser
# (16 October 2026): track, abbreviation, year, amount.
SNAPSHOT = [
    ("Planning", "LAET", 2025, 62673.00), ("Planning", "LAWO", 2025, 73211.00),
    ("Planning", "SCLS", 2025, 50523.00), ("Planning", "AppalReD Legal Aid", 2024, 65076.00),
    ("Planning", "ALAS", 2024, 55578.00), ("Planning", "CCLS", 2024, 75655.00),
    ("Planning", "LOLLA", 2024, 89098.00), ("Planning", "LANC", 2024, 87316.00),
    ("Planning", "LAS KY", 2024, 68090.00), ("Planning", "LASMTC", 2024, 73218.00),
    ("Planning", "NSLS", 2024, 75000.00), ("Planning", "LSNV", 2023, 86250.00),
    ("Planning", "NLSLA", 2023, 75752.30), ("Planning", "WTLS", 2023, 56717.00),
    ("Project", "ALSC", 2025, 371593.00), ("Project", "ILA", 2025, 489100.00),
    ("Project", "LOLLA", 2025, 256163.00), ("Project", "LAFLA", 2025, 344578.00),
    ("Project", "LASP", 2025, 324556.00), ("Project", "LABG", 2025, 358129.00),
    ("Project", "LSNM", 2025, 218895.00), ("Project", "MAP", 2025, 379091.00),
    ("Project", "LAC", 2024, 392214.19), ("Project", "LAWV", 2024, 235465.00),
    ("Project", "LASCO", 2024, 359546.00), ("Project", "LawNY", 2024, 204917.00),
    ("Project", "NNJLS", 2024, 350000.00), ("Project", "CLA SoCal", 2023, 313702.00),
    ("Project", "KLS", 2023, 342867.00), ("Project", "LANWT", 2023, 384937.00),
    ("Project", "LASEV", 2023, 398660.00), ("Project", "LSV", 2023, 227982.00),
    ("Project", "MILS", 2023, 181960.00), ("Project", "PTLA", 2023, 372223.60),
    ("Project", "PSLS", 2023, 198599.00), ("Project", "SLLS", 2023, 287321.00),
    ("Project", "LAFLA", 2022, 383695.74), ("Project", "NLS", 2022, 377782.08),
    ("Project", "NLA", 2022, 275000.18),
    ("Sustainability", "CLSoCal", 2025, 336130.00), ("Sustainability", "LASEV", 2025, 403616.00),
    ("Sustainability", "PTLA", 2025, 361097.00), ("Sustainability", "PSLS", 2025, 230300.00),
    ("Sustainability", "CRLA", 2024, 346060.00), ("Sustainability", "LOLLA", 2024, 272211.00),
    ("Sustainability", "LAW", 2024, 314164.00), ("Sustainability", "LASC", 2024, 478532.00),
    ("Sustainability", "MAP", 2024, 311095.00), ("Sustainability", "LAS KY", 2023, 198090.00),
    ("Sustainability", "LSNYC", 2023, 300042.37), ("Sustainability", "CLASI", 2022, 180765.04),
    ("Sustainability", "LAC", 2022, 256495.98), ("Sustainability", "SLLS", 2022, 127055.53),
    ("Transformation", "ALAS", 2025, 422781.00), ("Transformation", "LANC", 2025, 408286.00),
    ("Transformation", "LASMTC", 2025, 106717.00), ("Transformation", "NLSLA", 2025, 363257.00),
    ("Transformation", "CVLAS", 2024, 383909.00), ("Transformation", "LSNV", 2024, 365538.00),
    ("Transformation", "NLSA", 2024, 402867.00), ("Transformation", "WTLS", 2024, 424694.00),
    ("Transformation", "CALS", 2023, 378710.00), ("Transformation", "LAWM", 2023, 443982.00),
    ("Transformation", "LSNF", 2023, 481386.29), ("Transformation", "ALSC", 2022, 350206.04),
    ("Transformation", "ICLS", 2022, 435403.80),
]

# Grants LSC's 2022 and 2023 press releases print that the awards page does
# not, hand-summed: seven 2022 grants ($2,368,147) and PSLS's second 2023 grant.
RELEASE_ONLY = [
    (2022, "California Rural Legal Assistance", 367167, "CA"),
    (2022, "Georgia Legal Services Program", 304946, "GA"),
    (2022, "Land of Lincoln Legal Aid", 369179, "IL"),
    (2022, "Michigan Advocacy Program", 320906, "MI"),
    (2022, "The Legal Aid Society of Cleveland", 433243, "OH"),
    (2022, "Legal Services of the Virgin Islands", 204429, "VI"),
    (2022, "Legal Action of Wisconsin", 368277, "WI"),
    (2023, "Prairie State Legal Services", 318650, "IL"),
]
RELEASE_ONLY_USD = 2686797

# A cut-down accordion in the shape of the page, with a hidden toggle label.
SAMPLE = """<html><head><script>var x = "Fake (F) ($1.00)- 2025";</script></head><body>
<h2>Planning Grantees</h2>
<div class="accordion"><h3><button>Legal Aid of East Tennessee (LAET) ($62,673.00)- 2025
<span class="visually-hidden">expand and show content</span></button></h3>
<div><p>Planning text.</p></div>
<h3><button>Appalachian Research and Defense Fund of Kentucky (AppalReD Legal Aid) ($65,076.00)-2024</button></h3></div>
<h2>Project Grantees</h2>
<h3><button>Kansas Legal Services (KLS) ($342,867.00)- 2023- Driver&#8217;s License Restoration</button></h3>
<h2>Transformation Grantees</h2>
<h3><button>Legal Services of North Florida (LSNF) ($481,386,29)- 2023</button></h3>
</body></html>"""


class Parser(unittest.TestCase):
    def test_amounts(self):
        self.assertEqual(pbif.parse_amount("489,100.00"), 489100.0)
        self.assertEqual(pbif.parse_amount("86,250"), 86250)
        self.assertAlmostEqual(pbif.parse_amount("481,386,29"), 481386.29)
        self.assertAlmostEqual(pbif.parse_amount("435,403,80"), 435403.80)
        with self.assertRaises(ValueError):
            pbif.parse_amount("4,89,100")

    def test_sample(self):
        got = pbif.parse_page(SAMPLE)
        self.assertEqual([(a["track"], a["abbreviation"], a["year"], a["amount_usd"]) for a in got], [
            ("Planning", "LAET", 2025, 62673.0),
            ("Planning", "AppalReD Legal Aid", 2024, 65076.0),
            ("Project", "KLS", 2023, 342867.0),
            ("Transformation", "LSNF", 2023, 481386.29)])
        self.assertEqual(got[0]["grantee"], "Legal Aid of East Tennessee")
        self.assertIsNone(got[0]["subject"])
        self.assertEqual(got[2]["subject"], "Driver’s License Restoration")
        self.assertEqual(got[3]["printed_amount"], "$481,386,29")

    def test_names(self):
        self.assertEqual(pbif.norm("Nassau/Suffolk Law Services Committee, Inc"),
                         pbif.norm("Nassau Suffolk Law Services Committee"))
        self.assertEqual(pbif.norm("Legal Aid of Western Virginia"), "legal aid of west virginia")
        self.assertEqual(pbif.norm("The Legal Aid Society of Cleveland"), "legal aid society of cleveland")
        self.assertEqual(pbif.norm("Legal Aid of Chicago"), pbif.norm("Legal Aid Chicago"))

    def test_same_amount(self):
        self.assertTrue(pbif.same_amount(372223.60, 372223))
        self.assertTrue(pbif.same_amount(383695.74, 383696))
        self.assertFalse(pbif.same_amount(180765.04, 180764))


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = pbif.load()
        cls.awards = cls.doc["awards"]
        cls.areas = basic_field.load()["service_areas"]

    def test_matches_snapshot(self):
        got = [(a["track"], a["abbreviation"], a["year"], round(a["amount_usd"], 2)) for a in self.awards]
        self.assertEqual(got, SNAPSHOT)

    def test_every_grantee_has_a_state(self):
        self.assertEqual(self.doc["unmatched"], [])
        for a in self.awards:
            self.assertIn(a["state"], tig.JURISDICTIONS, a["grantee"])

    def test_states(self):
        got = {a["abbreviation"]: a["state"] for a in self.awards}
        expected = {"CLASI": "OH", "LAWV": "WV", "NLA": "MA", "NLSA": "PA", "LAS KY": "KY",
                    "PTLA": "ME", "CRLA": "CA", "LANC": "NC", "NSLS": "NY", "LawNY": "NY",
                    "LAW": "WI", "ILA": "IA", "NNJLS": "NJ", "MILS": "MI", "WTLS": "TN"}
        for abbr, state in expected.items():
            self.assertEqual(got[abbr], state, abbr)

    def test_source(self):
        self.assertTrue(self.doc["source"]["url"].startswith("https://www.lsc.gov/"))


class Releases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = pbif.load()["awards"]
        cls.areas = basic_field.load()["service_areas"]
        cls.releases = pbif.load_releases()
        cls.recon = pbif.reconcile(cls.page, cls.releases)
        cls.summary = {r["year"]: r for r in pbif.release_summary(cls.page, cls.recon, cls.releases)}

    def test_release_sources(self):
        for rel in self.releases:
            self.assertTrue(rel["url"].startswith("https://www.lsc.gov/press-release/"), rel["url"])

    def test_release_totals(self):
        def total(year):
            rel = [r for r in self.releases if r["year"] == year][0]
            return sum(pbif.parse_amount(g["printed"].lstrip("$")) for g in rel["grants"])
        self.assertEqual(total(2022), 4754551)
        self.assertEqual(total(2023), 5054729)

    def test_status_counts(self):
        def counts(year):
            s = self.summary[year]
            return (s["same"], s["amount differs"], s["release only"], s["page only"])
        self.assertEqual(counts(2022), (7, 1, 7, 0))
        self.assertEqual(counts(2023), (15, 2, 1, 0))
        self.assertEqual(counts(2024), (0, 0, 0, 0))
        self.assertEqual(counts(2025), (2, 1, 0, 0))

    def test_release_only(self):
        got = [(r["year"], r["grantee"], r["release_usd"]) for r in self.recon if r["status"] == "release only"]
        self.assertEqual(got, [(y, g, usd) for y, g, usd, _ in RELEASE_ONLY])

    def test_amount_differs(self):
        got = {(r["year"], r["grantee"]): (r["release_usd"], r["page_usd"])
               for r in self.recon if r["status"] == "amount differs"}
        self.assertEqual(got, {
            (2022, "Community Legal Aid Services, Inc."): (180764, 180765.04),
            (2023, "Center for Arkansas Legal Services"): (394344, 378710),
            (2023, "Kansas Legal Services"): (334132, 342867),
            (2025, "Land of Lincoln Legal Aid"): (265153, 256163)})

    def test_page_counts_match_stated_counts(self):
        # The page agrees with LSC's stated counts for 2023-2025, not for 2022.
        for year in (2024, 2025):
            s = self.summary[year]
            self.assertEqual(s["page_grantees"], s["stated_organizations"], year)
            self.assertEqual(s["page_states"], s["stated_states"], year)
        self.assertEqual(self.summary[2023]["page_grantees"], 17)
        self.assertEqual(self.summary[2022]["page_grantees"], 8)
        self.assertEqual(self.summary[2022]["stated_organizations"], 15)

    def test_combined(self):
        allp = pbif.combined(self.page, self.recon, self.areas)
        extra = allp[len(self.page):]
        self.assertEqual([(a["year"], a["grantee"], a["amount_usd"], a["state"]) for a in extra],
                         [tuple(r) for r in RELEASE_ONLY])
        self.assertEqual(sum(a["amount_usd"] for a in extra), RELEASE_ONLY_USD)
        by_year = lambda y: sum(a["amount_usd"] for a in allp if a["year"] == y)  # noqa: E731
        self.assertLess(abs(by_year(2022) - 4754551), 1)
        self.assertAlmostEqual(by_year(2023), 5047831.56, places=2)

    def test_markdown(self):
        lines = pbif.releases_markdown(self.recon).splitlines()
        self.assertEqual(lines[0], "| Year | Grantee | Press release | PBIF page | Status |")
        self.assertEqual(len(lines), 12 + 2)
        self.assertIn("| 2022 | Legal Services of the Virgin Islands | $204,429 | not listed | release only |", lines)


class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = pbif.load()["awards"]
        cls.areas = basic_field.load()["service_areas"]
        recon = pbif.reconcile(cls.page, pbif.load_releases())
        cls.pbif = pbif.combined(cls.page, recon, cls.areas)
        cls.tig = tig.load()["awards"]
        cls.head = pbif.headline(cls.pbif, cls.tig, cls.areas)

    def test_total(self):
        self.assertAlmostEqual(self.head["pbif_usd"], round(sum(r[3] for r in SNAPSHOT) + RELEASE_ONLY_USD, 2))
        self.assertEqual(self.head["pbif_awards"], 66 + len(RELEASE_ONLY))
        self.assertEqual(self.head["pbif_years"], [2022, 2023, 2024, 2025])

    def test_page_alone(self):
        head = pbif.headline(self.page, self.tig, self.areas)
        self.assertAlmostEqual(head["pbif_usd"], round(sum(r[3] for r in SNAPSHOT), 2))
        self.assertEqual(head["no_tig_but_pbif"], ["IA", "NJ"])

    def test_no_tig_but_pbif(self):
        self.assertEqual(self.head["no_tig_but_pbif"], ["IA", "NJ", "VI"])
        self.assertEqual(self.head["neither"], ["AS", "GU", "IN", "MD", "MP", "PR", "RI", "UT", "WY"])

    def test_shares(self):
        rows = basic_field.compare(self.pbif, self.areas)
        self.assertAlmostEqual(sum(r["tig_share"] for r in rows), 1.0)
        both = basic_field.compare(self.pbif + self.tig, self.areas)
        listed = sum(y["dollars_listed"] for y in tig.summary(self.tig))
        self.assertAlmostEqual(sum(r["tig_usd"] for r in both), listed + self.head["pbif_usd"], places=1)

    def test_markdown(self):
        lines = pbif.markdown(basic_field.compare(self.pbif, self.areas), "PBIF 2022-2025").splitlines()
        self.assertTrue(lines[0].startswith("| State | Basic field 2025 | Share | PBIF 2022-2025 |"))
        self.assertEqual(len(lines), len(basic_field.by_state(self.areas)) + 2)


class Output(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = pbif.load()["awards"]
        cls.areas = basic_field.load()["service_areas"]
        cls.recon = pbif.reconcile(cls.page, pbif.load_releases())
        cls.pbif = pbif.combined(cls.page, cls.recon, cls.areas)
        cls.tig = tig.load()["awards"]
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            cls.readme = f.read()

    def test_readme_pbif_table_is_current(self):
        self.assertIn(pbif.markdown(basic_field.compare(self.pbif, self.areas), "PBIF 2022-2025"), self.readme)

    def test_readme_both_table_is_current(self):
        both = basic_field.compare(self.pbif + self.tig, self.areas)
        self.assertIn(pbif.markdown(both, "TIG and PBIF"), self.readme)

    def test_readme_releases_table_is_current(self):
        self.assertIn(pbif.releases_markdown(self.recon), self.readme)


if __name__ == "__main__":
    unittest.main()
