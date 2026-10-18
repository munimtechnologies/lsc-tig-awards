# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pbif  # noqa: E402
import pbif_2026  # noqa: E402
import pbif_history  # noqa: E402
import tig  # noqa: E402

NATIONAL = "https://www.lsc.gov/press-release/lsc-awards-415m-pro-bono-legal-services-across-18-states"
CALIFORNIA = "https://www.lsc.gov/press-release/california-legal-services-receive-950000-pro-bono-initiatives"

# Summed by hand from the releases.
NAMED_GRANTS_USD = 2581023      # seven project grants
NATIONAL_NAMED_USD = 2094667    # the six awards the national release names
CALIFORNIA_USD = 950759         # $486,356 + $455,403 + $9,000, LSC's own total


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pbif_2026.load()

    def test_sources(self):
        urls = [r["url"] for r in self.data["releases"]]
        self.assertEqual(urls, [NATIONAL, CALIFORNIA])
        for a in self.data["awards"]:
            self.assertTrue(a["sources"], a["grantee"])
            for url in a["sources"]:
                self.assertIn(url, urls, a["grantee"])

    def test_states(self):
        for a in self.data["awards"]:
            self.assertIn(a["state"], tig.JURISDICTIONS, a["grantee"])

    def test_kinds(self):
        self.assertEqual(len(pbif_2026.named(self.data, "grant")), 7)
        self.assertEqual([a["grantee"] for a in pbif_2026.named(self.data, "scholarship")],
                         ["Greater Bakersfield Legal Assistance"])
        self.assertEqual(len(self.data["awards"]), 8)

    def test_one_amount_from_a_quote(self):
        quoted = [a["grantee"] for a in self.data["awards"] if a["printed_by"] != "LSC"]
        self.assertEqual(quoted, ["Legal Services of Long Island"])

    def test_quotes(self):
        r = self.data["round"]
        self.assertIn(str(r["running_count"]), r["running_quote"])
        for rel in self.data["releases"]:
            self.assertIn(str(rel["stated_organizations"]) if rel["scope"] == "national" else "three", rel["quote"])
        self.assertIn("$4.15 million", self.data["releases"][0]["quote"])
        self.assertIn("$950,759", self.data["releases"][1]["quote"])


class Sums(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pbif_2026.load()
        cls.rows = {r["scope"]: r for r in pbif_2026.release_rows(cls.data)}

    def test_named_grants(self):
        self.assertEqual(sum(pbif_2026.usd(a) for a in pbif_2026.named(self.data, "grant")), NAMED_GRANTS_USD)

    def test_california_adds_up(self):
        ca = self.rows["CA"]
        self.assertTrue(ca["complete"])
        self.assertEqual(ca["awards"], ca["stated_organizations"])
        self.assertEqual(ca["named_usd"], CALIFORNIA_USD)
        self.assertEqual(ca["named_usd"], ca["stated_usd"])

    def test_national_names_six(self):
        nat = self.rows["national"]
        self.assertFalse(nat["complete"])
        self.assertEqual(nat["awards"], 6)
        self.assertEqual(nat["named_usd"], NATIONAL_NAMED_USD)

    def test_inland_counties_in_both(self):
        icls = [a for a in self.data["awards"] if a["grantee"] == "Inland Counties Legal Services"]
        self.assertEqual(len(icls), 1)
        self.assertEqual(icls[0]["sources"], [NATIONAL, CALIFORNIA])


class Summary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pbif_2026.load()
        cls.s = pbif_2026.summary(cls.data, pbif_history.load(), pbif.load_releases())

    def test_earlier_rounds(self):
        before = pbif_2026.earlier_rounds(pbif_history.load(), pbif.load_releases())
        self.assertEqual(sorted(before), list(range(2014, 2026)))
        self.assertEqual([before[y] for y in (2022, 2023, 2024, 2025)], [4750000, 5000000, 5400000, 5500000])
        self.assertEqual(before[2017], 3800000)

    def test_smallest_since_2017(self):
        self.assertEqual(self.s["smallest_since"], 2017)
        self.assertEqual(self.s["lowest_after"], {"year": 2020, "usd": 4347185})

    def test_drop_from_2025(self):
        self.assertEqual(tig.pct(self.s["drop_from_2025"], 1), "24.5%")

    def test_named(self):
        self.assertEqual(self.s["named_states"], ["CA", "KY", "LA", "NM", "NY", "TN"])
        self.assertEqual(tig.pct(self.s["named_share"], 1), "62.2%")

    def test_readings(self):
        r = self.s["readings"]
        self.assertEqual(r["named_grants"], 7)
        self.assertEqual(tig.dollars(r["named_mean"]), "$368,718")
        self.assertEqual(r["scholarship_usd"], 9000)
        self.assertEqual(r["all_grants"]["unnamed"], 13)
        self.assertEqual(r["all_grants"]["left_usd"], 1568977)
        self.assertEqual(tig.dollars(r["all_grants"]["mean"]), "$120,691")
        self.assertEqual(r["with_scholarships"]["unnamed"], 4)
        self.assertEqual(r["with_scholarships"]["left_usd"], 1487977)
        self.assertEqual(tig.dollars(r["with_scholarships"]["mean"]), "$371,994")

    def test_running_count(self):
        self.assertEqual(self.s["running_added"], 20)
        self.assertEqual(self.s["running_added"], self.data["round"]["stated_organizations"])


class Output(unittest.TestCase):
    def test_tables(self):
        data = pbif_2026.load()
        table = pbif_2026.markdown(data)
        self.assertEqual(len(table.splitlines()), 10)
        self.assertIn("| Inland Counties Legal Services | CA | grant | $455,403 | LSC |", table)
        rel = pbif_2026.releases_markdown(pbif_2026.release_rows(data))
        self.assertIn("| CA | $950,759 | 3 | 3 | $950,759 |", rel)
        self.assertIn("| national | $4,150,000 | 20 | 6 | $2,094,667 |", rel)

    def test_main_runs(self):
        for argv in ([], ["--releases"], ["--summary"]):
            self.assertEqual(pbif_2026.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
