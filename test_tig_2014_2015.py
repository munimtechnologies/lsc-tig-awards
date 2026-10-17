# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_2014_2015  # noqa: E402
import tig_history  # noqa: E402

# (year, complete, grantee rows, organizations, states, territories, grants at
# least, sum of the amounts, stated total, grantees with an amount on lsc.gov
# today), each summed by hand in groups of five and again by state from the
# raw text of LSC's documents.
TOTALS = [
    (2014, True, 30, 30, 21, 1, 34, 3467978, 3467978, 11),
    (2015, False, 7, 7, 7, 0, 8, 1214048, None, 7),
]

# (year, source, amounts printed, same as the dataset's amount)
SOURCES = [
    (2014, "release", 8, 8),
    (2014, "local", 8, 7),
    (2015, "release", 5, 5),
    (2015, "bundle", 5, 5),
    (2015, "pbif_bundle", 2, 2),
    (2015, "event", 1, 1),
]

STATES_2014 = "AR CA CT FL HI IA ID IL KY LA ME MI MN MT NE NY OH PR TN UT VA WA".split()
STATES_2015 = "CA IL MA TX VA WA WV".split()
SHA_2014 = "1685c827118fbb7d04f04461b0b3326df43b2d37fb29e46ee4ffa5a6964760c2"


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2014_2015.load()
        cls.rounds = {r["year"]: r for r in cls.history["rounds"]}

    def test_years(self):
        self.assertEqual([r["year"] for r in self.history["rounds"]], [2014, 2015])
        self.assertTrue(tig_2014_2015.complete(self.rounds[2014]))
        self.assertFalse(tig_2014_2015.complete(self.rounds[2015]))

    def test_2014_pdf_is_the_same_on_lsc_gov_and_in_the_archive(self):
        lst = self.rounds[2014]["list"]
        self.assertEqual(lst["sha256"], SHA_2014)
        self.assertEqual(lst["archived_sha256"], SHA_2014)
        self.assertTrue(lst["url"].startswith("https://www.lsc.gov/sites/default/files/"))
        self.assertTrue(lst["archived"].startswith("https://web.archive.org/web/2015"))
        self.assertEqual(lst["pdf_created"], "2014-10-17")

    def test_2015_has_no_list(self):
        lst = self.rounds[2015]["list"]
        self.assertEqual(lst["kind"], "none")
        self.assertIsNone(lst["stated_total"])
        self.assertTrue(lst["archived"].startswith("https://web.archive.org/web/20151106"))

    def test_urls(self):
        for r in self.history["rounds"]:
            for url in r["sources"].values():
                self.assertTrue(url.startswith("https://www.lsc.gov/press-release/"), url)
            self.assertEqual(set(r["amounts"]), set(r["sources"]))
            for url in r["archived_sources"].values():
                self.assertTrue(url.startswith("https://web.archive.org/web/2015"), url)

    def test_states_hand_checked(self):
        self.assertEqual(sorted({g["state"] for g in self.rounds[2014]["grantees"]}), STATES_2014)
        self.assertEqual(sorted({g["state"] for g in self.rounds[2015]["grantees"]}), STATES_2015)
        for r in self.history["rounds"]:
            for g in r["grantees"]:
                self.assertIn(g["state"], tig.JURISDICTIONS + tig_history.TERRITORIES, g["grantee"])

    def test_ids(self):
        for r in self.history["rounds"]:
            ids = [g["id"] for g in r["grantees"]]
            for i in ids:
                self.assertRegex(i, r"^%d-\d{2}$" % (r["year"] % 100))
            self.assertEqual(ids, sorted(ids))
            self.assertEqual(len(ids), len(set(ids)))

    def test_amounts_name_grantees_of_the_round(self):
        for r in self.history["rounds"]:
            ids = {g["id"] for g in r["grantees"]}
            for source, amounts in r["amounts"].items():
                self.assertLessEqual(set(amounts), ids, source)
                for printed in amounts.values():
                    self.assertGreater(tig_history.usd(printed), 20000)
            for source, printed in r["as_printed"].items():
                for i, text in printed.items():
                    self.assertEqual(text.replace(" ", ""), r["amounts"][source][i])
            for p in r["parts"]:
                self.assertIn(p["id"], ids)
                if "as_printed" in p:
                    self.assertEqual([x.replace(" ", "") for x in p["as_printed"]], p["printed"])
            for t in r["group_totals"]:
                self.assertLessEqual(set(t["ids"]), ids)
                self.assertEqual(t["as_printed"].replace(" ", ""), t["printed"])
            for n in r["names"]:
                self.assertIn(n["id"], ids)
                self.assertEqual(n["list"], [g for g in r["grantees"] if g["id"] == n["id"]][0]["grantee"])

    def test_every_2015_grantee_is_in_a_release(self):
        r = self.rounds[2015]
        for g in r["grantees"]:
            self.assertIn(g["id"], r["amounts"][g["printed_from"]])
            self.assertEqual(g["printed"], r["amounts"][g["printed_from"]][g["id"]])
        self.assertEqual([g["id"] for g in r["grantees"] if g["printed_from"] == "pbif_bundle"], ["15-06", "15-07"])

    def test_quotes_carry_the_counts(self):
        for r in self.history["rounds"]:
            for s in r["statements"]:
                stated = [s.get(k) for k in tig_2014_2015.COUNTS if s.get(k) is not None]
                self.assertTrue(stated or s["usd"], s["quote"])
                for n in stated:
                    self.assertIn(str(n), s["quote"])
                if s["usd"]:
                    (kind, x), = s["usd"].items()
                    if kind == "exactly":
                        self.assertIn(tig.dollars(x), s["quote"])
                    else:
                        self.assertIn("$%g" % (x / 1e6), s["quote"].replace(" Million", " million"))
            self.assertIn(str(r["cumulative"]["grants"]), r["cumulative"]["quote"])


class Totals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2014_2015.load()

    def test_totals(self):
        got = [(r["year"], r["complete"], r["grantees"], r["organizations"], r["states"], r["territories"],
                r["grants_at_least"], r["sum_usd"], r["stated_usd"], r["on_lsc_today"])
               for r in tig_2014_2015.totals(self.history)]
        self.assertEqual(got, TOTALS)

    def test_2014_list_sums_to_its_stated_total(self):
        r = tig_2014_2015.totals(self.history)[0]
        self.assertEqual(r["difference"], 0)
        self.assertEqual(r["stated_organizations"], None)
        self.assertEqual(r["stated_grants"], 38)
        # The sum is $32,022 short of $3.5 million: "nearly $3.5 million".
        self.assertEqual(3500000 - r["sum_usd"], 32022)

    def test_2015_known_share(self):
        r = tig_2014_2015.totals(self.history)[1]
        self.assertIsNone(r["difference"])
        self.assertEqual((r["stated_organizations"], r["stated_grants"]), (30, 36))
        # 7 of 30 grantees and 8 of 36 grants are known, $1,214,048 of "more
        # than $4.2 million"; at least $2,985,952 for the other 23 is unknown.
        self.assertEqual(r["stated_organizations"] - r["grantees"], 23)
        self.assertEqual(r["stated_grants"] - r["grants_at_least"], 28)
        self.assertEqual(4200000 - r["sum_usd"], 2985952)

    def test_sources(self):
        rows = tig_2014_2015.sources(self.history)
        self.assertEqual([(r["year"], r["source"], r["printed"], r["same"]) for r in rows], SOURCES)
        differ = [(r["year"], r["source"], d["id"], d["source_usd"], d["list_usd"]) for r in rows for d in r["differ"]]
        self.assertEqual(differ, [(2014, "local", "14-23", 735200, 725200)])

    def test_parts_and_group_totals_add_up(self):
        rows = tig_2014_2015.parts(self.history)
        self.assertEqual([(r["year"], r["source"], r["grantee"], r["sum_usd"]) for r in rows], [
            (2014, "local", "Bay Area Legal Aid", 168324),
            (2014, "local", "Pine Tree Legal Assistance, Inc.", 138139),
            (2014, "local", "Legal Assistance of Western New York, Inc.", 195527),
            (2014, "release", "Virginia (three grantees)", 494200),
            (2014, "local", "Virginia (three grantees)", 494200),
            (2015, "bundle", "Northwest Justice Project", 505660),
        ])
        self.assertEqual([r["difference"] for r in rows], [0] * 6)


class Statements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = tig_2014_2015.load()
        cls.rows = tig_2014_2015.statements(cls.history)

    def test_count(self):
        self.assertEqual(len(self.rows), 9)
        self.assertEqual([r["year"] for r in self.rows].count(2014), 4)

    def test_only_the_local_releases_recipient_count_misses(self):
        wrong = [(r["year"], r["source"], r["wrong"]) for r in self.rows if r["wrong"]]
        self.assertEqual(wrong, [(2014, "local", ["organizations"])])

    def test_places_fit(self):
        (lst,) = [r for r in self.rows if (r["year"], r["source"]) == (2014, "list")]
        self.assertEqual(lst["stated"], {"projects": 38, "places": 22})
        self.assertEqual(lst["unchecked"], ["projects"])
        self.assertTrue(lst["fits"])

    def test_incomplete_round_checks_nothing(self):
        for r in self.rows:
            if r["year"] == 2015:
                self.assertEqual(r["wrong"], [])
                self.assertEqual(r["unchecked"], list(r["stated"]))
                self.assertIsNone(r["fits"])

    def test_dollar_figures(self):
        got = [(r["year"], r["source"], r["fits"]) for r in self.rows if r["usd"]]
        self.assertEqual(got, [
            (2014, "list", True), (2014, "release", True), (2014, "local", True),
            (2015, "release", None), (2015, "bundle", None),
        ])

    def test_fits(self):
        f = tig_2014_2015.fits
        self.assertTrue(f({"exactly": 3467978}, 3467978))
        self.assertFalse(f({"exactly": 3467978}, 3467979))
        self.assertTrue(f({"nearly": 3500000}, 3467978))
        self.assertFalse(f({"nearly": 3500000}, 3500000))
        self.assertTrue(f({"more_than": 4200000}, 4203221))
        self.assertIsNone(f(None, 1))
        self.assertIsNone(f({"nearly": 1}, None))
        with self.assertRaises(ValueError):
            f({"about": 1}, 1)

    def test_cumulative_counts_add_up_exactly(self):
        c = tig_2014_2015.cumulative(self.history)
        self.assertEqual((c["before_grants"], c["added_grants"], c["implied_grants"], c["after_grants"]), (570, [38, 36], 644, 644))
        self.assertTrue(c["grants_fit"])
        self.assertEqual(c["implied_usd_at_least"], 53667978)
        self.assertEqual((c["before_usd_more_than"], c["after_usd_more_than"]), (46000000, 53000000))
        self.assertTrue(c["usd_fit"])


class Output(unittest.TestCase):
    def test_markdown_rows(self):
        h = tig_2014_2015.load()
        self.assertEqual(len(tig_2014_2015.totals_markdown(tig_2014_2015.totals(h)).splitlines()), 4)
        self.assertEqual(len(tig_2014_2015.sources_markdown(tig_2014_2015.sources(h)).splitlines()), 8)
        self.assertEqual(len(tig_2014_2015.parts_markdown(tig_2014_2015.parts(h)).splitlines()), 8)
        table = tig_2014_2015.statements_markdown(h, tig_2014_2015.statements(h))
        self.assertEqual(len(table.splitlines()), 11)
        self.assertIn("| 2014 | PDF list | 38 projects, 22 states and territories, exactly $3,467,978 | none | projects | yes |", table)
        self.assertIn("| 2014 | local releases | 38 organizations, nearly $3,500,000 | organizations | none | yes |", table)
        self.assertIn("| 2015 | PBIF per-grantee release | 36 grants | - | grants | - |", table)
        self.assertEqual(len(tig_2014_2015.cumulative_markdown(tig_2014_2015.cumulative(h)).splitlines()), 7)

    def test_main_runs(self):
        for argv in ([], ["--sources"], ["--headlines"], ["--summary"]):
            self.assertEqual(tig_2014_2015.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
