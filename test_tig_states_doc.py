# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import basic_field  # noqa: E402
import poverty  # noqa: E402
import tig  # noqa: E402
import tig_states  # noqa: E402

# Ohio State Legal Services' LawHelp Interactive grants, as LSC's descriptions
# for each round name them (2014 release; 2016-2017 archived pages; 2018-2021
# description pages).
LHI = {2014: 725200, 2016: 808000, 2017: 751250, 2018: 783000, 2019: 790000, 2020: 526400, 2021: 265000}


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grants = tig_states.build()
        areas = basic_field.load()["service_areas"]
        printed = poverty.load()["service_areas"]
        cls.rows = tig_states.compare(cls.grants, areas, printed)
        cls.head = tig_states.headline(cls.rows)
        cls.by = {r["state"]: r for r in cls.rows}
        with open(os.path.join(HERE, "docs", "tig-states.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def test_table_is_current(self):
        self.assertIn(tig_states.totals_markdown(self.grants), self.doc)

    def test_rounds(self):
        rounds = self.head["rounds"]
        self.assertNotIn("11", rounds)
        ten = rounds["10"]
        self.assertIn("Seven had one in 10: %s and %s." % (", ".join(ten[:-1]), ten[-1]), self.doc)
        self.assertEqual(len(ten), 7)
        self.assertEqual(rounds["0"], ["GU", "MD", "MP", "RI", "VI"])
        self.assertIn("**Maryland and Rhode Island had none**, nor did Guam, the Northern Mariana Islands and the U.S. Virgin Islands.", self.doc)

    def test_ohio(self):
        oh = self.by["OH"]
        share = lambda label: "%.1f%%" % (100 * oh[label]["tig_share"])  # noqa: E731
        self.assertIn("Ohio got %s of the dollars in 2014-2019 and %s in 2020-2025" % (
            share("2014-2019"), share("2020-2025")), self.doc)
        self.assertIn("(%s over the" % share("2014-2025"), self.doc)
        self.assertIn("whole period: %s)" % tig.dollars(oh["2014-2025"]["tig_usd"]), self.doc)

    def test_lawhelp_interactive(self):
        for year, usd in LHI.items():
            self.assertTrue(any(g["year"] == year and g["state"] == "OH" and g["amount_usd"] == usd
                                for g in self.grants), year)
            self.assertIn("| %d | %s |" % (year, tig.dollars(usd)), self.doc)
        total = sum(LHI.values())
        early = sum(u for y, u in LHI.items() if y < 2020)
        late = total - early
        pct = lambda x, label: "%.1f%%" % (100.0 * x / self.head[label]["tig_usd"])  # noqa: E731
        self.assertIn("These seven grants total %s. They were %s of all TIG dollars in 2014-2019 and %s in 2020-2025." % (
            tig.dollars(total), pct(early, "2014-2019"), pct(late, "2020-2025")), self.doc)
        self.assertIn("without them Ohio had %s." % tig.dollars(self.by["OH"]["2014-2025"]["tig_usd"] - total), self.doc)

    def test_commands(self):
        self.assertIn("python tig_states.py --rounds", self.doc)
        self.assertIn("test_tig_states.py", self.doc)


if __name__ == "__main__":
    unittest.main()
