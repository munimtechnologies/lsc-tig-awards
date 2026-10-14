# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import contextlib
import csv
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402

DATA = tig.load()
AWARDS = DATA["awards"]

# Hand-summed from LSC's pages (see README); amounts in cents.
LISTED = {
    2021: (35, 29, 426573784),
    2022: (33, 29, 467913503),
    2023: (33, 29, 515703300),
    2024: (32, 29, 630608100),
    2025: (31, 28, 406430800),
}
AI_ALL = {2021: (1, 9329000), 2022: (2, 26141849), 2023: (4, 108963400),
          2024: (9, 272042000), 2025: (11, 164394800)}


class DataFile(unittest.TestCase):
    def test_well_formed(self):
        self.assertEqual(tig.validate(DATA), [])

    def test_counts_orgs_totals(self):
        s = tig.summarize(AWARDS)
        self.assertEqual(sorted(s), sorted(LISTED))
        for year, (n, orgs, cents) in LISTED.items():
            self.assertEqual((s[year]["awards"], s[year]["organizations"], s[year]["total_cents"]),
                             (n, orgs, cents), year)
        self.assertEqual(len(AWARDS), 164)

    def test_2022_matches_lsc_exact_total(self):
        # LSC states $4,679,135 for 2022; the listed awards sum to $4,679,135.03.
        self.assertEqual(tig.summarize(AWARDS)[2022]["total_cents"] // 100, 4679135)

    def test_2024_tips_have_no_description(self):
        rows = [a for a in AWARDS if a["year"] == 2024 and a["category"] == "TIP"]
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(not a["described"] and a["intake"] is None for a in rows))

    def test_missing_2025_award_is_noted_not_invented(self):
        self.assertFalse(any(a["year"] == 2025 and "Greater Miami" in a["grantee"] for a in AWARDS))
        self.assertIn("Greater Miami", " ".join(DATA["rounds"]["2025"]["notes"]))


class AIShare(unittest.TestCase):
    def test_ai_counts_and_dollars(self):
        s = tig.summarize(AWARDS)
        for year, (n, cents) in AI_ALL.items():
            self.assertEqual((s[year]["ai_awards"], s[year]["ai_cents"]), (n, cents), year)

    def test_dollar_share_by_round(self):
        s = tig.summarize(AWARDS)
        got = {y: round(v["ai_dollar_share"] * 100, 1) for y, v in s.items()}
        self.assertEqual(got, {2021: 2.2, 2022: 5.6, 2023: 21.1, 2024: 43.1, 2025: 40.4})

    def test_builds_only(self):
        s = tig.summarize(AWARDS, kinds=("builds",))
        self.assertEqual((s[2025]["ai_awards"], s[2025]["ai_cents"]), (6, 121074800))
        self.assertEqual(round(s[2025]["ai_dollar_share"] * 100, 1), 29.8)
        # Every AI mention before 2025 is a grant that builds or deploys AI.
        for year in (2021, 2022, 2023, 2024):
            self.assertEqual(s[year]["ai_cents"], AI_ALL[year][1], year)

    def test_shares_are_fractions_and_kinds_nest(self):
        wide = tig.summarize(AWARDS)
        narrow = tig.summarize(AWARDS, kinds=("builds",))
        for year in wide:
            for key in ("ai_award_share", "ai_dollar_share"):
                self.assertGreaterEqual(wide[year][key], 0.0)
                self.assertLessEqual(wide[year][key], 1.0)
                self.assertLessEqual(narrow[year][key], wide[year][key])

    def test_word_ai_is_case_sensitive_in_evidence(self):
        self.assertIsNotNone(tig.PHRASE_EVIDENCE.search("an AI-driven legal issue search"))
        self.assertIsNotNone(tig.PHRASE_EVIDENCE.search("Artificial Intelligence"))
        self.assertIsNone(tig.PHRASE_EVIDENCE.search("legal aid, an API and both bots"))
        self.assertIsNone(tig.PHRASE_EVIDENCE.search("Legal Aid Content Intelligence"))

    def test_ai_intake_leads(self):
        leads = tig.ai_intake(AWARDS, years={2024, 2025})
        self.assertEqual(sorted((a["year"], a["grantee"]) for a in leads), sorted([
            (2024, "Legal Aid of North Carolina"),
            (2025, "Florida Rural Legal Services"),
            (2025, "Legal Aid of the Bluegrass"),
            (2025, "Southern Minnesota Regional Legal Services"),
            (2025, "Legal Services of Eastern Missouri"),
            (2025, "Legal Services of the Hudson Valley"),
            (2025, "Legal Aid Services of Oregon"),
            (2025, "Legal Aid of Southeastern Pennsylvania"),
            (2025, "Legal Aid Society of Middle Tennessee and the Cumberlands"),
        ]))


class Statements(unittest.TestCase):
    def test_total_rules(self):
        self.assertTrue(tig.total_agrees(515703300, 510000000, "millions"))   # $5.16M as "$5.1 million"
        self.assertFalse(tig.total_agrees(630608100, 620000000, "millions"))  # $6.31M is not "$6.2 million"
        self.assertTrue(tig.total_agrees(467913503, 467913500, "exact"))
        self.assertFalse(tig.total_agrees(406430800, 420000000, "over"))
        with self.assertRaises(ValueError):
            tig.total_agrees(1, 1, "about")

    def test_which_statements_agree(self):
        got = [(r["year"], r["source"].split()[0], r["agrees"]) for r in tig.check_statements(DATA)]
        self.assertEqual(got, [
            (2021, "list", True),
            (2022, "headline", True),
            (2022, "body", True),
            (2023, "body", True),
            (2024, "headline", False),
            (2024, "body", False),
            (2025, "list", False),
            (2025, "press", False),
        ])

    def test_2025_details(self):
        r = [r for r in tig.check_statements(DATA) if r["year"] == 2025]
        self.assertEqual(r[0]["grants"], {"stated": 32, "listed": 31, "agrees": False})
        self.assertEqual(r[0]["organizations"], {"stated": 22, "listed": 28, "agrees": False})
        self.assertEqual(r[1]["states"], {"stated": 22, "listed": 21, "agrees": False})

    def test_2024_body_count_agrees_but_total_does_not(self):
        r = [r for r in tig.check_statements(DATA) if r["year"] == 2024 and r["source"] == "body"][0]
        self.assertTrue(r["grants"]["agrees"])
        self.assertFalse(r["total"]["agrees"])


class Output(unittest.TestCase):
    def test_dollars(self):
        self.assertEqual(tig.dollars(467913503), "$4,679,135.03")
        self.assertEqual(tig.dollars(3500000), "$35,000")

    def test_csv(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "awards.csv")
            tig.write_csv(AWARDS, path)
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 164)
        self.assertEqual(list(rows[0]), tig.CSV_FIELDS)
        self.assertEqual(sum(round(float(r["amount_usd"]) * 100) for r in rows),
                         sum(v[2] for v in LISTED.values()))

    def test_cli(self):
        for argv in ([], ["--check"], ["--kinds", "builds"], ["--ai-intake", "2025"]):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(tig.main(argv), 0)
            self.assertTrue(buf.getvalue().strip(), argv)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            tig.main(["--ai-intake", "2025"])
        self.assertEqual(len(buf.getvalue().strip().splitlines()), 8)


if __name__ == "__main__":
    unittest.main()
