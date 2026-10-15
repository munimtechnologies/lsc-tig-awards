# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import contextlib
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402

STATES = set("""AK AL AR AZ CA CO CT DC DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT
NC ND NE NH NJ NM NV NY OH OK OR PA PR RI SC SD TN TX UT VA VI VT WA WI WV WY""".split())
AI_WORDS = re.compile(r"\bAI\b|artificial intelligence|chatbot|generative", re.IGNORECASE)
AI_UPPER = re.compile(r"\bAI\b")


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = tig.load()
        cls.awards = cls.doc["awards"]
        cls.rows = {r["year"]: r for r in tig.summary(cls.awards)}

    def test_award_counts_match_lsc(self):
        for year, stated in self.doc["stated_totals"].items():
            self.assertEqual(self.rows[int(year)]["awards"], stated["awards"], year)

    def test_listed_dollars(self):
        # Sums of the amounts as LSC printed them, award by award.
        expected = {2021: 4268931, 2022: 4679135.03, 2023: 5157033, 2024: 6306081, 2025: 4064308}
        for year, usd in expected.items():
            self.assertAlmostEqual(self.rows[year]["dollars_listed"], usd, places=2)
        # 2022 matches LSC's stated total to the dollar; 2021 is $7 under it.
        self.assertEqual(int(self.rows[2022]["dollars_listed"]), self.doc["stated_totals"]["2022"]["usd"])
        self.assertEqual(self.doc["stated_totals"]["2021"]["usd"] - self.rows[2021]["dollars_listed"], 7)

    def test_ai_counts(self):
        got = {y: (r["ai_awards"], r["ai_intake_awards"], r["ai_dollars"]) for y, r in self.rows.items()}
        self.assertEqual(got, {
            2021: (1, 0, 93290),
            2022: (2, 1, 261418.49),
            2023: (4, 1, 1089634),
            2024: (9, 2, 2720420),
            2025: (12, 8, 1643948),
        })

    def test_only_one_unpriced_award(self):
        unpriced = [a for a in self.awards if a["amount_usd"] is None]
        self.assertEqual([(a["year"], a["grantee"]) for a in unpriced],
                         [(2025, "Legal Services of Greater Miami")])
        self.assertEqual(unpriced[0]["source"], "2025-press")

    def test_flags_are_consistent(self):
        for a in self.awards:
            label = "%s %s %s" % (a["year"], a["grantee"], a["amount_usd"])
            self.assertIn(a["state"], STATES, label)
            self.assertIn(str(a["year"]), self.doc["sources"], label)
            self.assertIn(a.get("source", str(a["year"])), self.doc["sources"], label)
            if a["mentions_ai"]:
                self.assertTrue(a["ai_terms"] and AI_WORDS.search(a["ai_terms"]), label)
            else:
                self.assertIsNone(a["ai_terms"], label)
            if not a["described"]:
                self.assertFalse(a["mentions_ai"] or a["mentions_intake"], label)

    def test_ai_needs_uppercase_ai(self):
        # 'Aid' must never count as AI.
        for a in self.awards:
            if a["mentions_ai"] and not re.search("artificial intelligence|chatbot", a["ai_terms"], re.I):
                self.assertTrue(AI_UPPER.search(a["ai_terms"]), a["grantee"])

    def test_sources_are_lsc(self):
        for url in self.doc["sources"].values():
            self.assertTrue(url.startswith("https://www.lsc.gov/"), url)

    def test_2025_ai_intake_awards(self):
        names = sorted(a["grantee"] for a in tig.ai_awards(self.awards, 2025) if a["mentions_intake"])
        self.assertEqual(names, sorted([
            "Florida Rural Legal Services",
            "Legal Aid of the Bluegrass",
            "Southern Minnesota Regional Legal Services",
            "Legal Services of Eastern Missouri",
            "Legal Services of the Hudson Valley",
            "Legal Aid Services of Oregon",
            "Legal Aid of Southeastern Pennsylvania",
            "The Legal Aid Society of Middle Tennessee and the Cumberlands",
        ]))


class States(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.awards = tig.load()["awards"]
        cls.rounds = tig.state_rounds(cls.awards)

    def test_jurisdictions(self):
        self.assertEqual(len(tig.JURISDICTIONS), 51)
        self.assertTrue(set(tig.JURISDICTIONS) <= STATES)

    def test_no_award_in_five_rounds(self):
        never = sorted(s for s, n in self.rounds.items() if n == 0)
        self.assertEqual(never, ["IA", "IN", "MD", "NJ", "RI", "UT", "WY"])

    def test_no_territory(self):
        self.assertEqual(set(self.rounds), set(tig.JURISDICTIONS))

    def test_every_round(self):
        five = sorted(s for s, n in self.rounds.items() if n == 5)
        self.assertEqual(five, ["CA", "FL", "GA", "IL", "KY", "MI", "MT", "PA"])
        self.assertEqual(tig.every_round(self.awards),
                         ["Land of Lincoln Legal Aid", "Montana Legal Services Association"])

    def test_states_per_round(self):
        # LSC's 2024 release says 22 states; its 2025 text says 22, the records give 21.
        per_year = {}
        for a in self.awards:
            per_year.setdefault(a["year"], set()).add(a["state"])
        self.assertEqual({y: len(s) for y, s in per_year.items()},
                         {2021: 24, 2022: 25, 2023: 22, 2024: 22, 2025: 21})


class Output(unittest.TestCase):
    def test_readme_table_is_current(self):
        table = tig.markdown(tig.summary(tig.load()["awards"]))
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            self.assertIn(table, f.read())

    def test_readme_states_table_is_current(self):
        table = tig.states_markdown(tig.load()["awards"])
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            self.assertIn(table, f.read())

    def test_shares(self):
        self.assertEqual(tig.pct(9, 32), "28.1%")
        self.assertEqual(tig.pct(2720420, 6306081), "43.1%")
        self.assertEqual(tig.dollars(261418.49), "$261,418")

    def test_cli(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(tig.main(["--ai", "2025"]), 0)
        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 12)
        self.assertTrue(any(l.startswith("Legal Services of Greater Miami (FL) unpublished") for l in lines))

    def test_cli_states(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(tig.main(["--states"]), 0)
        out = buf.getvalue()
        self.assertIn("| 0 | IA, IN, MD, NJ, RI, UT, WY (7) |", out)
        self.assertTrue(out.rstrip().endswith(
            "Award in every round: Land of Lincoln Legal Aid; Montana Legal Services Association"))

    def test_licence(self):
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            self.assertIn("Apache-2.0", f.read())


if __name__ == "__main__":
    unittest.main()
