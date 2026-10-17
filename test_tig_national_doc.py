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


class Doc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        areas = basic_field.load()["service_areas"]
        printed = poverty.load()["service_areas"]
        grants = tig_states.build()
        cls.national = tig_states.load_national()["grants"]
        cls.with_ = tig_states.compare(grants, areas, printed)
        cls.without = tig_states.compare(tig_states.set_aside(grants, {"grants": cls.national}), areas, printed)
        cls.head = {"with": tig_states.headline(cls.with_), "without": tig_states.headline(cls.without)}
        cls.oh = {"with": {r["state"]: r for r in cls.with_}["OH"],
                  "without": {r["state"]: r for r in cls.without}["OH"]}
        with open(os.path.join(HERE, "docs", "tig-national.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def total(self, key, label):
        return self.head[key][label]["tig_usd"]

    def row(self, name, cells):
        return "| %s | %s |" % (name, " | ".join(cells))

    def test_grants(self):
        for g in self.national:
            self.assertIn("| %d | %s |" % (g["year"], tig.dollars(g["amount_usd"])), self.doc)
        early = sum(g["amount_usd"] for g in self.national if g["year"] < 2020)
        late = sum(g["amount_usd"] for g in self.national if g["year"] >= 2020)
        self.assertIn("Together %s: %s in 2014-2019 and %s in 2020-2025." % (
            tig.dollars(early + late), tig.dollars(early), tig.dollars(late)), self.doc)

    def test_table(self):
        labels = list(tig_states.PERIODS)
        for key, name in (("with", "all grants"), ("without", "without the seven")):
            self.assertIn(self.row("TIG dollars, " + name, [tig.dollars(self.total(key, l)) for l in labels]), self.doc)
            self.assertIn(self.row("Ohio's share, " + name,
                                   ["%.1f%%" % (100 * self.oh[key][l]["tig_share"]) for l in labels]), self.doc)
            self.assertIn(self.row("Ohio's index, " + name, ["%.1f" % self.oh[key][l]["index"] for l in labels]), self.doc)
        rise = ["%.1f%%" % (100 * (self.total("with", l) / self.total("without", l) - 1)) for l in labels]
        self.assertIn(self.row("Rise in every other state's index", rise), self.doc)
        self.assertIn("Ohio has %.1f%% of that population." % (100 * self.oh["with"]["poverty_share"]), self.doc)

    def test_findings(self):
        w, wo = self.oh["with"], self.oh["without"]
        self.assertTrue(all(wo[l]["index"] < 1 for l in tig_states.PERIODS))
        self.assertIn("falls from %.1f to %.1f." % (w["2014-2019"]["index"], wo["2014-2019"]["index"]), self.doc)
        self.assertIn("Ohio drops from %d complete rounds with a grant to %d." % (w["rounds"], wo["rounds"]), self.doc)
        ten = self.head["without"]["rounds"]["10"]
        self.assertIn("Six states had a grant in 10 of the 11 complete rounds: %s and %s." % (
            ", ".join(ten[:-1]), ten[-1]), self.doc)
        self.assertEqual(len(ten), 6)
        rise = lambda l: "%.1f%%" % (100 * (self.total("with", l) / self.total("without", l) - 1))  # noqa: E731
        self.assertIn("Every other state's index rises by %s in 2014-2019" % rise("2014-2019"), self.doc)
        self.assertIn("and by %s in 2020-2025," % rise("2020-2025"), self.doc)
        gone = lambda l: "%.1f%%" % (100 * (1 - self.total("without", l) / self.total("with", l)))  # noqa: E731
        self.assertIn("because the seven grants were %s and %s of all TIG dollars" % (
            gone("2014-2019"), gone("2020-2025")), self.doc)
        per = lambda key: "$%.2f" % self.head[key]["2014-2025"]["per_person_in_poverty"]  # noqa: E731
        self.assertIn("fall from %s to %s." % (per("with"), per("without")), self.doc)

    def test_quotes(self):
        for g in self.national:
            for phrase in ("national online document assembly", "more than 40 states", "nationwide", "over 40 states"):
                if phrase in self.doc and phrase in g["quote"]:
                    break
            else:
                self.fail("no phrase from the %d quote on the page" % g["year"])

    def test_commands(self):
        self.assertIn("python tig_states.py --without-national", self.doc)
        self.assertIn("test_tig_national.py", self.doc)


if __name__ == "__main__":
    unittest.main()
