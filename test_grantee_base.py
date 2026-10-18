# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Checks for grantee_base.py. Structure first; then the counts, pinned after
the sandbox output was checked by hand against LSC's 2025 notice."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import basic_field  # noqa: E402
import grantee_base  # noqa: E402


class Structure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.areas = basic_field.load(basic_field.DATA)["service_areas"]
        cls.rows, cls.undecided, cls.tig_orgs, cls.pbif_orgs, cls.head = grantee_base.build()

    def test_every_service_area_row_counted_once(self):
        self.assertEqual(self.head["service_area_rows"], len(self.areas))
        self.assertEqual(self.head["basic_field_usd"] + self.head["undecided_usd"],
                         sum(r["amount_usd"] for r in self.areas))

    def test_undecided_row(self):
        # LSC's notice prints one service area with two possible grantees.
        self.assertEqual(len(self.undecided), 1)
        u = self.undecided[0]
        self.assertEqual((u["state"], u["service_area"]), ("TN", "TN-4"))
        self.assertEqual(u["candidates"], ["Memphis Area Legal Services", "West Tennessee Legal Services"])

    def test_groups_partition_grantees(self):
        groups = self.head["groups"]
        self.assertEqual(sum(g["grantees"] for g in groups.values()), self.head["grantees"])
        self.assertEqual(sum(g["basic_field_usd"] for g in groups.values()), self.head["basic_field_usd"])
        self.assertEqual(set(r["group"] for r in self.rows) <= set(grantee_base.GROUPS), True)
        self.assertEqual(sum(t["grantees"] for t in self.head["tiers"]), self.head["grantees"])

    def test_organization_names_are_plain(self):
        plain = grantee_base.tig_grantees.plain
        for r in self.rows:
            self.assertEqual(r["organization"], plain(r["organization"]))
            self.assertIn(r["state"], r["states"])
            self.assertTrue(r["service_areas"])

    def test_match_bookkeeping(self):
        h = self.head
        self.assertEqual(h["tig_organizations"], 110)
        self.assertEqual(h["pbif_organizations"], 80)
        self.assertEqual(h["tig_organizations_matched"] + len(h["tig_organizations_unmatched"]), 110)
        self.assertEqual(h["pbif_organizations_matched"] + len(h["pbif_organizations_unmatched"]), 80)
        self.assertEqual(h["double_matched"], {})
        for r in self.rows:
            self.assertEqual(bool(r["tig_organization"]), r["tig_rule"] != "none", r["organization"])
            self.assertEqual(bool(r["pbif_organization"]), r["pbif_rule"] != "none", r["organization"])
            if r["group"] == "both":
                self.assertEqual(r["pbif_rule"], "via_tig", r["organization"])

    def test_outputs(self):
        md = grantee_base.markdown(self.rows)
        self.assertEqual(len(md.splitlines()), 2 + len(self.rows))
        review = grantee_base.review_markdown(self.rows, self.undecided, self.tig_orgs, self.pbif_orgs)
        self.assertIn("## Grantees that won neither program", review)


class Counts(unittest.TestCase):
    """Hand counts from data/basic_field_2025.json, read row by row: 131
    printed names, one of them the undecided TN-4 row."""

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.undecided, cls.tig_orgs, cls.pbif_orgs, cls.head = grantee_base.build()

    def test_grantees(self):
        self.assertEqual(self.head["grantees"], 130)
        self.assertEqual(self.head["undecided_usd"], 2111084)
        multi = {r["organization"]: r["state"] for r in self.rows if len(r["states"]) > 1}
        # Home state is the state with most of the grantee's dollars.
        self.assertEqual(len(multi), 5)
        self.assertEqual(multi.get("Micronesian Legal Services Corporation"), "MP")

    def test_groups(self):
        g = self.head["groups"]
        self.assertEqual({k: v["grantees"] for k, v in g.items()},
                         {"both": 74, "tig_only": 34, "pbif_only": 6, "neither": 16})
        self.assertEqual(self.head["won_either"]["grantees"], 114)

    def test_neither(self):
        # Hand sum of the 16 grantees' service areas (Micronesian LSC's GU-1
        # and MP-1, South Jersey's NJ-20 and MNJ, Dakota Plains' SD-4 and NSD-1).
        self.assertEqual(self.head["groups"]["neither"]["basic_field_usd"], 31906185)
        self.assertEqual(self.head["largest_neither"], 3765838)
        largest = [r for r in self.head["neither"] if r["basic_field_usd"] == 3765838]
        self.assertEqual([(r["state"], r["service_areas"]) for r in largest], [("PA", ["PA-25"])])

    def test_unmatched(self):
        self.assertCountEqual(self.head["tig_organizations_unmatched"],
                              ["Ohio State Legal Services (OH, 7 rounds)", "Memphis Area Legal Services (TN, 2 rounds)"])
        self.assertEqual(self.head["pbif_organizations_unmatched"], [])
        self.assertEqual(self.head["tig_round_wins"], 301)
        self.assertEqual(self.head["tig_round_wins_by_2025_grantees"], 292)

    def test_match_rules(self):
        self.assertEqual(self.head["match_rules"],
                         {"tig_exact": 108, "tig_none": 22, "pbif_via_tig": 74, "pbif_exact": 6, "pbif_none": 50})


if __name__ == "__main__":
    unittest.main()
