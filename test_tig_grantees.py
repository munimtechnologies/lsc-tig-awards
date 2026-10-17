# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig_grantees  # noqa: E402
import tig_states  # noqa: E402

# Counted by hand from the lists: organizations per number of complete rounds won.
ROUNDS_WON = {"10": 1, "9": 1, "8": 1, "7": 4, "6": 4, "5": 8, "4": 8, "3": 16, "2": 35, "1": 32}
# Per round: organizations (as in docs/tig-history.md) and those with no
# earlier complete round since 2014.
ROUNDS = {2014: (30, 30), 2016: (27, 14), 2017: (22, 9), 2018: (24, 12), 2019: (29, 14), 2020: (24, 4),
          2021: (29, 5), 2022: (29, 6), 2023: (29, 7), 2024: (29, 4), 2025: (29, 5)}
MISSED = {("MT", "Montana Legal Services Association"): [2019],
          ("WA", "Northwest Justice Project"): [2023, 2025],
          ("IL", "Legal Aid Chicago"): [2016, 2017, 2022],
          ("IL", "Land of Lincoln Legal Aid"): [2017, 2018, 2019, 2020],
          ("MI", "Michigan Advocacy Program"): [2014, 2018, 2023, 2024],
          ("OH", "Ohio State Legal Services"): [2022, 2023, 2024, 2025],
          ("PA", "Philadelphia Legal Assistance Center"): [2014, 2021, 2022, 2025],
          ("FL", "Legal Services of Greater Miami"): [2016, 2017, 2019, 2023, 2024],
          ("GA", "Atlanta Legal Aid Society"): [2014, 2016, 2018, 2022, 2024],
          ("KY", "Legal Aid of the Bluegrass"): [2014, 2016, 2017, 2020, 2021],
          ("ME", "Pine Tree Legal Assistance"): [2016, 2019, 2023, 2024, 2025]}
PERIODS = {"2014-2019": {"organizations": 79, "round_wins": 132},
           "2020-2025": {"organizations": 92, "round_wins": 169}, "both": 61}
PARTIAL = ["Blue Ridge Legal Services (VA)", "Community Legal Aid SoCal (CA)", "Legal Aid Chicago (IL)",
           "Legal Aid of West Virginia (WV)", "Lone Star Legal Aid (TX)", "Northwest Justice Project (WA)",
           "Volunteer Lawyers Project of the Boston Bar Association (MA)"]
TOTAL = 48139618.03


class Names(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names = tig_grantees.load_names()
        cls.rows = tig_grantees.build(cls.names)

    def test_plain(self):
        self.assertEqual(tig_grantees.plain("The Legal Aid Society of Cleveland"), "Legal Aid Society of Cleveland")
        self.assertEqual(tig_grantees.plain("Utah Legal Services, Inc."), "Utah Legal Services")
        self.assertEqual(tig_grantees.plain("Legal  Services NYC"), "Legal Services NYC")

    def test_every_entry_used(self):
        self.assertEqual(tig_grantees.unused(self.rows, self.names), [])
        self.assertEqual(len(self.names["names"]), 16)
        kinds = [e["kind"] for e in self.names["names"]]
        self.assertEqual((kinds.count("spelling"), kinds.count("short_form"), kinds.count("renamed")), (9, 1, 6))

    def test_years(self):
        for e in self.names["names"]:
            years = sorted({g["year"] for g in self.rows
                            if g["state"] == e["state"] and tig_grantees.plain(g["grantee"]) == e["printed"]})
            self.assertEqual(years, e["years"], e["printed"])

    def test_renames_have_sources(self):
        for e in self.names["names"]:
            self.assertEqual(e["source"] is not None, e["kind"] == "renamed", e["printed"])

    def test_latest_name(self):
        for o in tig_grantees.organizations(self.rows):
            last = max(o["rounds"] + o["partial"])
            printed = {tig_grantees.plain(g["grantee"]) for g in self.rows
                       if g["year"] == last and g["state"] == o["state"] and g["organization"] == o["organization"]}
            self.assertEqual(printed, {o["organization"]}, o["organization"])

    def test_no_join_within_a_round(self):
        for y in tig_grantees.COMPLETE:
            names = {(g["state"], tig_grantees.plain(g["grantee"])) for g in self.rows if g["year"] == y}
            orgs = {(g["state"], g["organization"]) for g in self.rows if g["year"] == y}
            self.assertEqual(len(names), len(orgs), y)
            self.assertEqual(len(orgs), ROUNDS[y][0], y)

    def test_unpriced_grant_counts(self):
        miami = [g for g in self.rows if g["year"] == 2025 and g["state"] == "FL" and g["amount_usd"] is None]
        self.assertEqual([g["organization"] for g in miami], ["Legal Services of Greater Miami"])


class Counts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orgs = tig_grantees.organizations(tig_grantees.build())
        cls.head = tig_grantees.summary()

    def test_hand_sums(self):
        self.assertEqual(sum(ROUNDS_WON.values()), 110)
        self.assertEqual(sum(int(k) * v for k, v in ROUNDS_WON.items()), 301)
        self.assertEqual(sum(o for o, n in ROUNDS.values()), 301)
        self.assertEqual(sum(n for o, n in ROUNDS.values()), 110)
        self.assertEqual(sum(o for y, (o, n) in ROUNDS.items() if y >= 2020), PERIODS["2020-2025"]["round_wins"])
        self.assertEqual(sum(n for y, (o, n) in ROUNDS.items() if y >= 2020),
                         PERIODS["2020-2025"]["organizations"] - PERIODS["both"])

    def test_headline(self):
        h = self.head
        self.assertEqual(h["complete_rounds"], 11)
        self.assertEqual(h["organizations"], 110)
        self.assertEqual(h["names"], 115)
        self.assertEqual(h["round_wins"], 301)
        self.assertEqual({k: v["organizations"] for k, v in h["rounds_won"].items()}, ROUNDS_WON)
        self.assertEqual(h["five_or_more"], {"organizations": 19, "round_wins": 119})
        self.assertEqual(h["periods"], PERIODS)
        self.assertEqual(h["partial"], PARTIAL)

    def test_rounds(self):
        self.assertEqual({int(y): (r["organizations"], r["new"]) for y, r in self.head["rounds"].items()}, ROUNDS)

    def test_most(self):
        self.assertEqual({(m["state"], m["organization"]): m["missed"] for m in self.head["most"]}, MISSED)
        for m in self.head["most"]:
            self.assertEqual(m["rounds"] + len(m["missed"]), 11)

    def test_dollars(self):
        self.assertAlmostEqual(self.head["usd"], TOTAL, places=2)
        self.assertAlmostEqual(sum(v["usd"] for v in self.head["rounds_won"].values()), TOTAL, places=2)
        self.assertAlmostEqual(sum(o["usd"] for o in self.orgs),
                               sum(g["amount_usd"] for g in tig_states.build() if g["year"] not in tig_states.PARTIAL),
                               places=2)

    def test_every_partial_org_won_a_complete_round(self):
        self.assertTrue(all(o["rounds"] for o in self.orgs))


class Cli(unittest.TestCase):
    def test_main_runs(self):
        for argv in ([], ["--rounds"], ["--summary"], ["--json"]):
            self.assertEqual(tig_grantees.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
