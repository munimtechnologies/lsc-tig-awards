# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import basic_field  # noqa: E402
import poverty  # noqa: E402
import tig  # noqa: E402

PRINTED_KIND = {"Basic Field - General": "general", "Agricultural Worker": "agricultural_worker",
                "Native American": "native_american", "Naative American": "native_american"}


class Codes(unittest.TestCase):
    def test_kind(self):
        for code, k in [("AK-1", "general"), ("MA-10", "general"), ("NC-5", "general"),
                        ("NM-1", "general"), ("MCA", "agricultural_worker"),
                        ("MMX-1", "agricultural_worker"), ("MSX-2", "agricultural_worker"),
                        ("NAZ-5", "native_american"), ("NNM-2", "native_american")]:
            self.assertEqual(poverty.kind(code), k, code)
        with self.assertRaises(ValueError):
            poverty.kind("AK")

    def test_kind_matches_lsc_printed_type(self):
        for r in poverty.load()["service_areas"]:
            self.assertEqual(poverty.kind(r["service_area"]), PRINTED_KIND[r["type"]], r["service_area"])

    def test_2025_has_27_native_american_areas(self):
        # LSC's service area page: "27 Native American service areas".
        areas = basic_field.load()["service_areas"]
        self.assertEqual(sum(poverty.kind(a["service_area"]) == "native_american" for a in areas), 27)


class Printed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.printed = poverty.load()["service_areas"]
        cls.areas = basic_field.load()["service_areas"]
        cls.check = poverty.check(cls.areas, cls.printed)

    def test_snapshot(self):
        codes = [r["service_area"] for r in self.printed]
        self.assertEqual(len(codes), 60)
        self.assertEqual(len(set(codes)), 60)
        for r in self.printed:
            self.assertEqual(r["poverty_population"] is None,
                             poverty.kind(r["service_area"]) == "native_american", r["service_area"])

    def test_every_printed_area_is_in_2025(self):
        have = {a["service_area"] for a in self.areas}
        self.assertEqual([r["service_area"] for r in self.printed if r["service_area"] not in have], [])

    def test_one_rate_per_person(self):
        # Each 2025 amount divided by the common rate gives back the poverty
        # population LSC printed for 2027, to about a person.
        self.assertTrue(11 < self.check["usd_per_person_2025"] < 13, self.check["usd_per_person_2025"])
        for r in self.check["rows"]:
            if r["poverty_population"] is not None:
                self.assertLessEqual(abs(r["implied_minus_printed"]), 1 + 1e-5 * r["poverty_population"],
                                     r["service_area"])

    def test_2027_estimates_scale_2025(self):
        # Every 2027 estimate, Native American areas included, is the 2025
        # amount times one factor.
        self.assertTrue(0.9 < self.check["scale_2027_over_2025"] < 1.0)
        for r in self.check["rows"]:
            self.assertLessEqual(abs(r["estimate_minus_scaled_2025"]), 3 + 1e-5 * r["amount_2025_usd"],
                                 r["service_area"])

    def test_native_american_set_aside(self):
        # LSC: a fixed 2.802% of basic field money goes to Native American areas.
        self.assertAlmostEqual(poverty.native_share(self.areas), 0.02802, places=5)


class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.printed = poverty.load()["service_areas"]
        cls.areas = basic_field.load()["service_areas"]
        cls.awards = tig.load()["awards"]
        cls.pov = poverty.poverty_areas(cls.areas, cls.printed)
        cls.rows = poverty.compare(cls.awards, cls.areas, cls.printed)
        cls.by = {r["state"]: r for r in cls.rows}

    def test_areas(self):
        self.assertEqual(len(self.pov), 190 - 27)
        self.assertEqual(sum(r["source"] == "printed" for r in self.pov), 46)
        self.assertTrue(all(r["poverty_population"] > 0 for r in self.pov))

    def test_every_jurisdiction(self):
        self.assertEqual(len(self.rows), 56)
        for s in tig.JURISDICTIONS:
            self.assertIn(s, self.by)

    def test_shares_sum_to_one(self):
        self.assertAlmostEqual(sum(r["poverty_share"] for r in self.rows), 1.0)
        self.assertAlmostEqual(sum(r["tig_share"] for r in self.rows), 1.0)

    def test_tig_total_matches_summary(self):
        listed = sum(y["dollars_listed"] for y in tig.summary(self.awards))
        self.assertAlmostEqual(sum(r["tig_usd"] for r in self.rows), listed, places=1)

    def test_vermont_is_one_printed_area(self):
        self.assertEqual(self.by["VT"]["poverty_population"], 54718)

    def test_index_definition(self):
        r = self.by["MT"]
        self.assertAlmostEqual(r["index"], r["tig_share"] / r["poverty_share"])
        self.assertAlmostEqual(r["tig_per_person_in_poverty"], r["tig_usd"] / r["poverty_population"])

    def test_states_with_no_award_have_index_zero(self):
        zero = sorted(s for s, r in self.by.items() if r["tig_usd"] == 0 and s in tig.JURISDICTIONS)
        self.assertEqual(zero, ["IA", "IN", "MD", "NJ", "RI", "UT", "WY"])

    def test_sorted_by_index(self):
        idx = [r["index"] for r in self.rows]
        self.assertEqual(idx, sorted(idx, reverse=True))

    def test_markdown(self):
        lines = poverty.markdown(self.rows).splitlines()
        self.assertEqual(len(lines), len(self.rows) + 2)
        self.assertTrue(lines[0].startswith("| State | People in poverty |"))


class Output(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.printed = poverty.load()["service_areas"]
        cls.areas = basic_field.load()["service_areas"]

    def test_readme_table_is_current(self):
        rows = poverty.compare(tig.load()["awards"], self.areas, self.printed)
        with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
            self.assertIn(poverty.markdown(rows), f.read())

    def test_areas_file_is_current(self):
        with open(os.path.join(HERE, "data", "poverty_areas_2025.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f), poverty.poverty_areas(self.areas, self.printed))


if __name__ == "__main__":
    unittest.main()
