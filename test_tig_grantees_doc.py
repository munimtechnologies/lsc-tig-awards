# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tig  # noqa: E402
import tig_grantees  # noqa: E402


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.head = tig_grantees.summary()
        cls.names = tig_grantees.load_names()["names"]
        with open(os.path.join(HERE, "docs", "tig-grantees.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_names(self):
        kinds = [e["kind"] for e in self.names]
        self.assertIn("It holds %d pairs:" % len(self.names), self.doc)
        self.assertIn("- %d spellings of one name" % kinds.count("spelling"), self.doc)
        self.assertIn("- %d short form:" % kinds.count("short_form"), self.doc)
        self.assertIn("- %d renames, each with the organization's own page" % kinds.count("renamed"), self.doc)
        self.assertIn("Legal Assistance Foundation (2014, 2018) and LAF (2015) to Legal Aid Chicago;", self.doc)
        for e in self.names:
            if e["kind"] == "renamed" and e["organization"] != "Legal Aid Chicago":
                self.assertIn("%s to %s" % (e["printed"], e["organization"]), self.doc)

    def test_findings(self):
        h = self.head
        self.assertIn("**%d different organizations won at least one TIG in the %d complete rounds**, %d round wins in all. "
                      "Counting names instead (no short form or rename joined) gives %d." % (
                          h["organizations"], h["complete_rounds"], h["round_wins"], h["names"]), self.doc)
        top = h["most"]
        self.assertLess(top[0]["rounds"], h["complete_rounds"])
        self.assertIn("**No organization won all %d rounds.**" % h["complete_rounds"], self.doc)
        self.assertEqual(len(top[0]["missed"]), 1)
        self.assertIn("%s won %d (all but %d), %s %d and %s %d." % (
            top[0]["organization"], top[0]["rounds"], top[0]["missed"][0], top[1]["organization"], top[1]["rounds"],
            top[2]["organization"], top[2]["rounds"]), self.doc)
        often = h["five_or_more"]
        self.assertIn("**%d organizations won once. %d won five rounds or more and hold %d of the %d round wins (%s).**" % (
            h["rounds_won"]["1"]["organizations"], often["organizations"], often["round_wins"], h["round_wins"],
            tig.pct(often["round_wins"], h["round_wins"])), self.doc)
        p = h["periods"]
        early, late = p["2014-2019"]["organizations"], p["2020-2025"]["organizations"]
        self.assertIn("**%d organizations won in both periods.** %d won in 2014-2019 and %d in 2020-2025: of the %d, "
                      "%d had no TIG in any complete round from 2014 to 2019, and of the %d, %d have had none since." % (
                          p["both"], early, late, late, late - p["both"], early, early - p["both"]), self.doc)

    def test_dollars(self):
        h = self.head
        often = [v for k, v in h["rounds_won"].items() if int(k) >= 5]
        self.assertEqual(sum(v["organizations"] for v in often), h["five_or_more"]["organizations"])
        usd, wins = sum(v["usd"] for v in often), h["five_or_more"]["round_wins"]
        once = h["rounds_won"]["1"]
        # Hand sums of the per-group dollars: 10 rounds down to 5, then the
        # ten groups, which reach the 11 rounds' $48,139,618.03 to the cent.
        self.assertAlmostEqual(usd, 23613471.87, places=2)
        self.assertAlmostEqual(once["usd"], 3596229.00, places=2)
        self.assertAlmostEqual(sum(v["usd"] for v in h["rounds_won"].values()), h["usd"], places=2)
        self.assertAlmostEqual(h["usd"], 48139618.03, places=2)
        self.assertIn("**Repeat winners got larger grants.** The %d that won five rounds or more received %s of the %s (%s), "
                      "against %s of round wins: %s per round won, against %s for the %d that won once, who received %s "
                      "of the dollars for %s of round wins." % (
                          h["five_or_more"]["organizations"], tig.dollars(usd), tig.dollars(h["usd"]), tig.pct(usd, h["usd"]),
                          tig.pct(wins, h["round_wins"]), tig.dollars(usd / wins),
                          tig.dollars(once["usd"] / once["organizations"]), once["organizations"],
                          tig.pct(once["usd"], h["usd"]), tig.pct(once["organizations"], h["round_wins"])), self.doc)
        self.assertGreater(usd / wins, once["usd"] / once["organizations"])
        with open(os.path.join(HERE, "data", "national_grants.json"), encoding="utf-8") as f:
            lhi = [g for g in json.load(f)["grants"] if g["service"] == "LawHelp Interactive"]
        self.assertEqual(len(lhi), 7)
        self.assertTrue(any(m["organization"] == "Ohio State Legal Services" for m in h["most"]))
        lhi_usd = sum(g["amount_usd"] for g in lhi)
        self.assertIn("whose seven LawHelp Interactive grants ([tig-national.md](tig-national.md)) come to %s; without "
                      "those, the %d received %s of the rest." % (
                          tig.dollars(lhi_usd), h["five_or_more"]["organizations"],
                          tig.pct(usd - lhi_usd, h["usd"] - lhi_usd)), self.doc)

    def test_newcomers(self):
        r = {int(y): v for y, v in self.head["rounds"].items()}
        late = [v for y, v in r.items() if y >= 2020]
        mid = [v for y, v in r.items() if 2016 <= y < 2020]
        new_late, wins_late = sum(v["new"] for v in late), sum(v["organizations"] for v in late)
        new_mid, wins_mid = sum(v["new"] for v in mid), sum(v["organizations"] for v in mid)
        self.assertIn("From 2020 to 2025, %d to %d of each round's %d to %d organizations had won no complete round "
                      "since 2014: %d of %d round wins (%s). From 2016 to 2019 it was %d of %d (%s)" % (
                          min(v["new"] for v in late), max(v["new"] for v in late),
                          min(v["organizations"] for v in late), max(v["organizations"] for v in late),
                          new_late, wins_late, tig.pct(new_late, wins_late), new_mid, wins_mid, tig.pct(new_mid, wins_mid)),
                      self.doc)
        self.assertLess(new_late / wins_late, new_mid / wins_mid)
        self.assertEqual(new_late, self.head["periods"]["2020-2025"]["organizations"] - self.head["periods"]["both"])

    def test_tables(self):
        for k, v in self.head["rounds_won"].items():
            self.assertIn("| %s | %d |" % (k, v["organizations"]), self.doc)
        self.assertIn("The %d organizations that won six rounds or more:" % len(self.head["most"]), self.doc)
        for m in self.head["most"]:
            self.assertIn("| %s | %s | %d | %s |" % (m["organization"], m["state"], m["rounds"],
                                                    ", ".join(str(y) for y in m["missed"])), self.doc)
        for y, v in self.head["rounds"].items():
            self.assertIn("| %s | %d | %d |" % (y, v["organizations"], v["new"]), self.doc)
        self.assertIn("all of 2014's %d are new by construction" % self.head["rounds"]["2014"]["new"], self.doc)
        self.assertIn("The seven organizations LSC's releases name for 2015 all won at least one complete round too.", self.doc)
        self.assertEqual(len(self.head["partial"]), 7)

    def test_links_and_commands(self):
        for text in ("python tig_grantees.py --rounds", "python tig_grantees.py --summary", "test_tig_grantees.py",
                     "(tig-states.md)", "(tig-history.md)", "(tig-national.md)", "(../data/grantee_names.json)"):
            self.assertIn(text, self.doc)


if __name__ == "__main__":
    unittest.main()
