# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pbif_grantees  # noqa: E402

# Every name the loose rule joined, checked by hand against the TIG names of
# its state. The 2024 'Legal Aid of Western New York' row carries LSC's own
# abbreviation for it, LawNY, on the PBIF Awards page.
LOOSE = {
    ("NY", "Legal Assistance of Western New York (LawNY)"): "Legal Assistance of Western New York",
    ("NY", "Legal Aid of Western New York"): "Legal Assistance of Western New York",
    ("IL", "LAF (formerly Legal Assistance Foundation of Metropolitan Chicago)"): "Legal Aid Chicago",
    ("KY", "Legal Aid Society, Inc. in Louisville"): "Legal Aid Society",
    ("MA", "Community Legal Aid, Inc. in Worcester"): "Community Legal Aid",
    ("NJ", "Northeast New Jersey Legal Services"): "Northeast New Jersey Legal Services Corporation",
    ("NY", "Nassau Suffolk Law Services Committee"): "Nassau/Suffolk Law Services Committee",
    ("MN", "Legal Services of Northwest Minnesota"): "Legal Services of Northwest Minnesota Corporation",
    ("WV", "Legal Aid of Western Virginia"): "Legal Aid of West Virginia",
    ("CA", "Legal Aid Foundation of Los Angeles County"): "Legal Aid Foundation of Los Angeles",
    ("WI", "Legal Action Wisconsin"): "Legal Action of Wisconsin",
}
# PBIF winners that won no TIG 2014-2025, checked by hand against every TIG
# organization of their state (Maryland and the Virgin Islands have none).
PBIF_ONLY = {
    ("MD", "Maryland Legal Aid"): 533744,
    ("NY", "Legal Aid Society of Northeastern New York"): 362559,
    ("NJ", "Legal Services of Northwest Jersey"): 299501,
    ("KY", "Appalachian Research and Defense Fund of Kentucky"): 65076,
    ("VA", "Legal Aid Society of Eastern Virginia"): 802276,
    ("VI", "Legal Services of the Virgin Islands"): 204429,
}
# The four organizations data/pbif_names.json joins: PBIF rounds (2020 is
# partial) and PBIF dollars, summed by hand from the two names' rows.
NAMED = {
    ("VT", "Legal Services Vermont"): ([2016, 2018, 2023], [2020], 603952 + 432994),
    ("DC", "Neighborhood Legal Services Program"): ([2016, 2019, 2021], [], 667930 + 386825),
    ("MT", "Montana Legal Services Association"): ([2014, 2018], [2020], 364268 + 236797),
    ("PA", "Legal Aid of Southeastern Pennsylvania"): ([2021, 2025], [], 324556 + 399999),
}
TIG_FIVE_WITHOUT_PBIF = ["Community Legal Services of Mid-Florida (FL)", "Ohio State Legal Services (OH)",
                         "Statewide Legal Services of Connecticut (CT)"]
PBIF_USD = 51070976.14
TIG_USD = 48139618.03


class Names(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names = pbif_grantees.load_names()
        cls.rows, cls.orgs, cls.tig_orgs, cls.head = pbif_grantees.build()

    def test_every_entry_used(self):
        self.assertEqual(pbif_grantees.unused(self.rows, self.names), [])
        kinds = [e["kind"] for e in self.names["names"]]
        self.assertEqual((len(kinds), kinds.count("spelling"), kinds.count("short_form"), kinds.count("renamed")), (4, 2, 1, 1))

    def test_years(self):
        plain = pbif_grantees.tig_grantees.plain
        for e in self.names["names"]:
            years = sorted({g["year"] for g in self.rows if g["state"] == e["state"] and plain(g["grantee"]) == e["printed"]})
            self.assertEqual(years, e["years"], e["printed"])

    def test_renames_have_sources(self):
        for e in self.names["names"]:
            self.assertEqual(e["source"] is not None, e["kind"] == "renamed", e["printed"])

    def test_named_join_tig_organizations(self):
        tig_keys = {(o["state"], o["organization"]) for o in self.tig_orgs if o["rounds"]}
        for e in self.names["names"]:
            self.assertIn((e["state"], e["organization"]), tig_keys, e["printed"])

    def test_loose(self):
        loose = {(g["state"], g["grantee"]): g["organization"] for g in self.rows if g["rule"] == "loose"}
        self.assertEqual(loose, LOOSE)

    def test_none(self):
        none = {(g["state"], g["organization"]) for g in self.rows if g["rule"] == "none"}
        self.assertEqual(none, set(PBIF_ONLY))

    def test_rules(self):
        self.assertEqual(self.head["match_rules"], {"exact": 156, "loose": 11, "named": 5, "none": 8})


class Headline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.orgs, cls.tig_orgs, cls.head = pbif_grantees.build()
        cls.by_key = {(o["state"], o["organization"]): o for o in cls.orgs}

    def test_rows(self):
        self.assertEqual(len(self.rows), 180)
        self.assertEqual(sum(1 for g in self.rows if g["from"] == "release"), 106)
        self.assertEqual(self.head["rows_with_no_state"], 0)
        self.assertAlmostEqual(self.head["pbif_usd"], PBIF_USD, places=2)

    def test_counts(self):
        h = self.head
        self.assertEqual((h["pbif_organizations"], h["both"], h["pbif_only"]), (80, 74, 6))
        self.assertEqual((h["tig_organizations"], h["tig_only"]), (110, 36))
        self.assertEqual(h["share_of_pbif_orgs_with_tig"], 0.925)
        self.assertEqual(h["share_of_tig_orgs_with_pbif"], 0.6727)

    def test_histogram(self):
        self.assertEqual(self.head["pbif_rounds_won_histogram"], {"6": 1, "5": 5, "4": 8, "3": 14, "2": 19, "1": 33})
        self.assertEqual(sum(self.head["pbif_rounds_won_histogram"].values()), 80)

    def test_dollars(self):
        only = sum(PBIF_ONLY.values())
        self.assertEqual(only, 2267585)
        self.assertAlmostEqual(self.head["pbif_usd_to_tig_winners"], PBIF_USD - only, places=2)
        self.assertAlmostEqual(self.head["pbif_usd_to_tig_winners"], 48803391.14, places=2)
        for key, usd in PBIF_ONLY.items():
            self.assertAlmostEqual(self.by_key[key]["pbif_usd"], usd, places=2, msg=key)
            self.assertFalse(self.by_key[key]["tig"], key)
        self.assertAlmostEqual(self.head["tig_usd_total"], TIG_USD, places=2)
        self.assertAlmostEqual(self.head["tig_usd_to_pbif_winners"], 34682277.0, places=2)

    def test_named_organizations(self):
        for key, (rounds, partial, usd) in NAMED.items():
            o = self.by_key[key]
            self.assertEqual((o["pbif_rounds"], o["pbif_partial"]), (rounds, partial), key)
            self.assertAlmostEqual(o["pbif_usd"], usd, places=2, msg=key)
            self.assertTrue(o["tig"], key)
            self.assertIn("named", o["rules"], key)

    def test_tig_five_or_more(self):
        five = self.head["tig_five_or_more"]
        self.assertEqual((five["organizations"], five["with_pbif"]), (19, 16))
        often = sorted("%s (%s)" % (o["organization"], o["state"]) for o in self.tig_orgs if len(o["rounds"]) >= 5)
        self.assertEqual(sorted(set(often) - set(five["names"])), TIG_FIVE_WITHOUT_PBIF)

    def test_mean_tig_rounds(self):
        # 228 round wins for the 74 TIG organizations with a PBIF grant, 73
        # for the 36 without (301 in all, as in docs/tig-grantees.md).
        tig_won = [o for o in self.tig_orgs if o["rounds"]]
        pbif_keys = set(self.by_key)
        with_pbif = [o for o in tig_won if (o["state"], o["organization"]) in pbif_keys]
        without = [o for o in tig_won if (o["state"], o["organization"]) not in pbif_keys]
        self.assertEqual((sum(len(o["rounds"]) for o in with_pbif), sum(len(o["rounds"]) for o in without)), (228, 73))
        self.assertEqual(self.head["mean_tig_rounds"], {"tig_orgs_with_pbif": 3.08, "tig_orgs_without_pbif": 2.03})

    def test_most_pbif(self):
        top = self.orgs[0]
        self.assertEqual((top["organization"], top["state"], top["pbif_rounds"]),
                         ("Legal Action of Wisconsin", "WI", [2016, 2018, 2019, 2021, 2022, 2024]))
        self.assertEqual(len(self.head["most_pbif"]), 1 + 5 + 8 + 14)


class Output(unittest.TestCase):
    def test_main_runs(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(pbif_grantees.main([]), 0)
        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 2 + 80)
        self.assertIn("| Legal Services Vermont | VT | 4 | 2016, 2018, 2020, 2023 |", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
