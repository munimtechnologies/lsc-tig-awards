# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import basic_field  # noqa: E402
import tig  # noqa: E402

# Lines in the layout of the Federal Register text, including wrapped names,
# a page break inside the table (followed by a line holding one space) and the
# one row printed with a dollar sign.
RULE = "-" * 72 + "\n"
HEADER = (
    "                                                             Estimated\n"
    "      Name of applicant           State     Service area    annualized\n"
    "         organization                                      2025 funding\n")
BODY = (
    "Alaska Legal Services          AK           AK-1              $1,164,808\n"
    " Corporation.\n"
    "Legal Services Alabama, Inc..  AL           AL-4               8,750,973\n"
    "DNA-Peoples Legal Services,    AZ           NAZ-5              3,934,252\n"
    " Inc.\n"
    "Community Legal Services, Inc  AZ           MAZ                  487,788\n"
    "\n"
    "[[Page 88816]]\n"
    "\n"
    " \n"
    "Memphis Area Legal Services,   TN           TN-4               2,111,084\n"
    " Inc. or West Tennessee Legal\n"
    " Services, Inc.\n"
    "Bay Area Legal Aid...........  CA           CA-1               9,000,000\n")

# Rows quoted from the 2025 notice, checked against the built data file.
SPOT = {"AK-1": 1164808, "AL-4": 8750973, "TN-10": 4486365, "TN-4": 2111084,
        "TN-7": 1079731, "NAZ-5": 3934252, "MAZ": 487788, "PR-1": 14540452,
        "WV-5": 3388941, "WY-4": 762624, "CA-19": 4477012, "CA-2": 1696585,
        "CA-26": 3763684, "MMX-1": 393989, "MSX-2": 3398860, "NY-9": 17270072,
        "TX-13": 18089444, "DC-1": 1079960}


def notice(body, copies=20):
    # The real notice has two rule lines before the table. parse_notice
    # refuses fewer than 100 rows, so the body is repeated.
    return ("=" * 71 + "\n" + "-" * 71 + "\n    fiscal year 2025 grant awards.\n\n" + "-" * 71 + "\n"
            + "\n[[Page 88815]]\n\n" + RULE + HEADER + RULE + body * copies + RULE
            + "\n    The amounts above are estimates.\n")


class Parser(unittest.TestCase):
    def test_sample(self):
        rows = basic_field.parse_notice(notice(BODY))
        self.assertEqual(len(rows), 6 * 20)
        self.assertEqual(rows[0], {"grantee": "Alaska Legal Services Corporation", "state": "AK",
                                   "service_area": "AK-1", "amount_usd": 1164808})
        self.assertEqual(rows[1]["grantee"], "Legal Services Alabama, Inc")
        self.assertEqual(rows[2]["grantee"], "DNA-Peoples Legal Services, Inc")
        self.assertEqual(rows[2]["service_area"], "NAZ-5")
        self.assertEqual((rows[3]["service_area"], rows[3]["amount_usd"]), ("MAZ", 487788))
        self.assertEqual(rows[4]["grantee"],
                         "Memphis Area Legal Services, Inc. or West Tennessee Legal Services, Inc")
        self.assertEqual(rows[5]["grantee"], "Bay Area Legal Aid")

    def test_too_few_rows(self):
        with self.assertRaises(ValueError):
            basic_field.parse_notice(notice(BODY, copies=1))

    def test_unknown_line_is_an_error(self):
        bad = BODY.replace("Legal Services Alabama, Inc..  AL           AL-4               8,750,973",
                           "Legal Services Alabama  AL  AL-4  pending")
        with self.assertRaises(ValueError):
            basic_field.parse_notice(notice(bad))


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = basic_field.load()
        cls.areas = cls.doc["service_areas"]

    def test_spot_rows(self):
        got = {r["service_area"]: r["amount_usd"] for r in self.areas}
        for area, usd in SPOT.items():
            self.assertEqual(got.get(area), usd, area)

    def test_row_count(self):
        # 72 + 72 + 46 rows over the notice's three pages.
        self.assertEqual(len(self.areas), 190)

    def test_service_areas_unique(self):
        codes = [r["service_area"] for r in self.areas]
        self.assertEqual(len(codes), len(set(codes)))

    def test_every_state_and_dc_has_money(self):
        states = basic_field.by_state(self.areas)
        for s in tig.JURISDICTIONS:
            self.assertGreater(states.get(s, 0), 0, s)

    def test_area_code_names_its_state(self):
        # AK-1, NAZ-5 (Native American), MAZ (agricultural worker). The two
        # multi-state agricultural worker areas are filed under ME and TX.
        odd = sorted(r["service_area"] for r in self.areas
                     if r["service_area"].split("-")[0][-2:] != r["state"])
        self.assertEqual(odd, ["MMX-1", "MSX-2"])

    def test_total_is_plausible(self):
        # LSC's basic field appropriation has been about $0.5 billion a year.
        total = sum(r["amount_usd"] for r in self.areas)
        self.assertTrue(400e6 < total < 560e6, total)

    def test_source(self):
        self.assertTrue(self.doc["source"]["url"].startswith("https://www.federalregister.gov/"))


class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.awards = tig.load()["awards"]
        cls.rows = basic_field.compare(cls.awards, basic_field.load()["service_areas"])
        cls.by = {r["state"]: r for r in cls.rows}

    def test_shares_sum_to_one(self):
        self.assertAlmostEqual(sum(r["basic_field_share"] for r in self.rows), 1.0)
        self.assertAlmostEqual(sum(r["tig_share"] for r in self.rows), 1.0)

    def test_tig_total_matches_summary(self):
        listed = sum(y["dollars_listed"] for y in tig.summary(self.awards))
        self.assertAlmostEqual(sum(r["tig_usd"] for r in self.rows), listed, places=1)

    def test_states_with_no_award_have_index_zero(self):
        zero = sorted(s for s, r in self.by.items() if r["tig_usd"] == 0 and s in tig.JURISDICTIONS)
        self.assertEqual(zero, ["IA", "IN", "MD", "NJ", "RI", "UT", "WY"])
        for s in zero:
            self.assertEqual(self.by[s]["index"], 0)

    def test_sorted_by_index(self):
        idx = [r["index"] for r in self.rows]
        self.assertEqual(idx, sorted(idx, reverse=True))

    def test_index_definition(self):
        r = self.by["MT"]
        self.assertAlmostEqual(r["index"], r["tig_share"] / r["basic_field_share"])

    def test_headline_groups(self):
        h = basic_field.headline(self.rows)
        self.assertEqual(h["jurisdictions"], len(self.rows))
        self.assertTrue(set(h["no_tig"]["states"]) <= set(h["under_half"]["states"]))
        self.assertEqual(h["no_tig"]["tig_share"], 0)

    def test_markdown(self):
        lines = basic_field.markdown(self.rows).splitlines()
        self.assertEqual(len(lines), len(self.rows) + 2)
        self.assertTrue(lines[0].startswith("| State | Basic field 2025 |"))

    def test_readme_table_is_current(self):
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            self.assertIn(basic_field.markdown(self.rows), f.read())


if __name__ == "__main__":
    unittest.main()
