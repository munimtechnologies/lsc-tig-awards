# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import archive_2018  # noqa: E402
import lawnext_2018  # noqa: E402
import tig_history  # noqa: E402

# Summed by hand from the raw text of each capture.
RELEASE_LISTED = 3862257
PAGE_LISTED = 3892257
BUNDLE_LISTED = 1680389

# The nine grantees of the per-grantee release (Montana has two grants).
BUNDLE_TIGS = ["18009", "18010", "18018", "18019", "18027", "18037", "18041", "18046", "18049", "18057"]


class Archive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = archive_2018.load()
        cls.history = tig_history.load()
        cls.lawnext = lawnext_2018.load()
        cls.rows = archive_2018.rows(cls.archive, cls.history, cls.lawnext)
        cls.summary = archive_2018.summary(cls.archive, cls.history, cls.lawnext)
        cls.by_source = {c["source"]: c for c in cls.archive["captures"]}

    def test_sources(self):
        self.assertEqual([c["source"] for c in self.archive["captures"]], ["release", "bundle", "page"])
        for c in self.archive["captures"]:
            self.assertTrue(c["url"].startswith("https://web.archive.org/web/"))
            self.assertTrue(c["url"].endswith("/" + c["original"]))
            stamp = c["url"].split("/")[4]
            self.assertEqual(c["captured"], "%s-%s-%s" % (stamp[:4], stamp[4:6], stamp[6:8]))
            self.assertTrue(c["original"].startswith("https://www.lsc.gov/"))
            self.assertIn(c["stated_total"], c["quote"])
            self.assertLess(c["captured"], "2019-07-01")

    def test_same_grants_as_lsc(self):
        lsc = sorted(g["tig"] for g in self.history["rounds"][0]["grants"])
        self.assertEqual(sorted(self.by_source["release"]["amounts"]), lsc)
        self.assertEqual(sorted(self.by_source["page"]["amounts"]), lsc)
        self.assertEqual(sorted(self.by_source["bundle"]["amounts"]), BUNDLE_TIGS)

    def test_hand_sums(self):
        def total(source):
            return sum(tig_history.usd(p) for p in self.by_source[source]["amounts"].values())
        self.assertEqual(total("release"), RELEASE_LISTED)
        self.assertEqual(total("page"), PAGE_LISTED)
        self.assertEqual(total("bundle"), BUNDLE_LISTED)
        # Montana's two grants are the $278,714 the per-grantee release's heading prints.
        mt = self.by_source["bundle"]["amounts"]
        self.assertEqual(tig_history.usd(mt["18018"]) + tig_history.usd(mt["18019"]), 278714)

    def test_every_amount_is_the_same_today(self):
        for r in self.rows:
            self.assertEqual(r["same"], r["grants"], r["source"])
            self.assertEqual(r["differ"], [])
            self.assertTrue(r["stated_same"])
        self.assertEqual(self.summary["captures"], 3)
        self.assertEqual(self.summary["amounts"], 62)
        self.assertEqual(self.summary["same_as_today"], 62)
        self.assertEqual(self.summary["differ"], {})
        self.assertTrue(self.summary["stated_all_same"])

    def test_disputed_figures_were_there_in_2018(self):
        a = {c["source"]: c["amounts"] for c in self.archive["captures"]}
        self.assertEqual(a["release"]["18008"], "$267,175")
        self.assertEqual(a["page"]["18008"], "$297,175")
        self.assertEqual(a["bundle"]["18046"], "$171,879")
        self.assertEqual(a["release"]["18046"], "$179,879")
        self.assertEqual(a["page"]["18046"], "$179,879")
        self.assertEqual(a["bundle"]["18010"], "$264,000")

    def test_list_sums(self):
        got = {r["source"]: r["listed_usd"] for r in self.rows}
        self.assertEqual(got, {"release": RELEASE_LISTED, "bundle": None, "page": PAGE_LISTED})
        # The same sums as today's documents.
        today = {(t["source"]): t["listed_usd"] for t in tig_history.totals(self.history) if t["year"] == 2018}
        self.assertEqual(today, {"release": RELEASE_LISTED, "page": PAGE_LISTED})

    def test_lawnext_only_in_one_body(self):
        # Only the per-grantee release's "$264,000 grant" matches LawNext; no
        # capture prints its $3,891,457 or any of its other amounts.
        self.assertEqual(self.summary["lawnext"], {"bundle": ["18010"]})
        for c in self.archive["captures"]:
            self.assertNotIn(self.lawnext["stated_total"], c["quote"])

    def test_two_running_totals_on_the_same_day(self):
        s = self.summary["since_2000"]
        self.assertEqual(sorted(s), ["bundle", "release"])
        self.assertIn("700 technology projects", s["release"])
        self.assertIn("$60 million", s["release"])
        self.assertIn("720 technology projects", s["bundle"])
        self.assertIn("$65 million", s["bundle"])
        self.assertEqual(self.by_source["release"]["dated"], self.by_source["bundle"]["dated"])

    def test_markdown(self):
        table = archive_2018.markdown(self.rows)
        self.assertEqual(len(table.splitlines()), 2 + 3)
        self.assertIn("| release | [2018-12-25](https://web.archive.org/web/20181225104657/", table)
        self.assertIn("| 26 | 26 | $3,862,257 | $3,884,257 | none |", table)
        self.assertIn("| 10 | 10 | - | $3,884,257 | 18010 |", table)
        self.assertIn("| 26 | 26 | $3,892,257 | $3,884,257 | none |", table)

    def test_main_runs(self):
        for argv in ([], ["--summary"]):
            self.assertEqual(archive_2018.main(argv), 0)


if __name__ == "__main__":
    unittest.main()
