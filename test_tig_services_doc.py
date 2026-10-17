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
        lhi = tig_states.set_aside(grants, tig_states.load_national())
        cls.services = tig_states.load_services()["grants"]
        rows = {"with": grants, "services": tig_states.set_aside(grants, tig_states.load_services()),
                "lhi": lhi, "both": tig_states.set_aside(lhi, tig_states.load_services())}
        cls.rows = {k: tig_states.compare(v, areas, printed) for k, v in rows.items()}
        cls.head = {k: tig_states.headline(v) for k, v in cls.rows.items()}
        cls.state = {k: {r["state"]: r for r in v} for k, v in cls.rows.items()}
        with open(os.path.join(HERE, "docs", "tig-services.md"), encoding="utf-8") as f:
            cls.doc = f.read()

    def total(self, key, label):
        return self.head[key][label]["tig_usd"]

    def row(self, name, cells):
        return "| %s | %s |" % (name, " | ".join(cells))

    def test_drops(self):
        states = sorted(set(g["state"] for g in self.services))
        self.assertEqual(len(states), 6)
        for s in states:
            cells = [tig.dollars(self.state["with"][s][l]["tig_usd"] - self.state["services"][s][l]["tig_usd"])
                     for l in tig_states.PERIODS]
            self.assertIn(self.row(s, cells), self.doc)
        self.assertIn("Only six states have a whole grant.", self.doc)

    def test_table(self):
        labels = list(tig_states.PERIODS)
        for key, name in (("with", "all grants"), ("services", "without the nine"),
                          ("both", "without the nine and LawHelp Interactive")):
            self.assertIn(self.row("TIG dollars, " + name, [tig.dollars(self.total(key, l)) for l in labels]), self.doc)
        for key, name in (("services", "without the nine"), ("both", "without both")):
            rise = ["%.1f%%" % (100 * (self.total("with", l) / self.total(key, l) - 1)) for l in labels]
            self.assertIn(self.row("Rise in every other state's index, " + name, rise), self.doc)
        oh = self.state["both"]["OH"]
        self.assertIn(self.row("Ohio's share, without both", ["%.1f%%" % (100 * oh[l]["tig_share"]) for l in labels]),
                      self.doc)
        self.assertIn(self.row("Ohio's index, without both", ["%.1f" % oh[l]["index"] for l in labels]), self.doc)

    def test_findings(self):
        gone = lambda l: "%.1f%%" % (100 * (1 - self.total("both", l) / self.total("with", l)))  # noqa: E731
        self.assertIn("takes %s of the 2014-2019 TIG dollars out, and %s of the 2020-2025 dollars." % (
            gone("2014-2019"), gone("2020-2025")), self.doc)
        rise = lambda l: "%.1f%%" % (100 * (self.total("with", l) / self.total("both", l) - 1))  # noqa: E731
        self.assertIn("Every other state's index rises by %s in 2014-2019 and by %s in 2020-2025." % (
            rise("2014-2019"), rise("2020-2025")), self.doc)
        self.assertIn("Ohio's 2014-2019 index goes from %.2f to %.2f" % (
            self.state["lhi"]["OH"]["2014-2019"]["index"], self.state["both"]["OH"]["2014-2019"]["index"]), self.doc)
        self.assertTrue(all(self.state["both"]["OH"][l]["index"] < 1 for l in tig_states.PERIODS))
        per = lambda key: "$%.2f" % self.head[key]["2014-2025"]["per_person_in_poverty"]  # noqa: E731
        self.assertIn("2014-2025: %s with every grant, %s without the nine, %s without both." % (
            per("with"), per("services"), per("both")), self.doc)
        drops = {s: self.state["with"][s]["2020-2025"]["tig_usd"] - self.state["services"][s]["2020-2025"]["tig_usd"]
                 for s in self.state["with"]}
        top = max(drops, key=drops.get)
        self.assertEqual(top, "MI")
        self.assertIn("Michigan loses %s of its 2020-2025 TIG dollars" % tig.dollars(drops["MI"]), self.doc)

    def test_links_and_commands(self):
        for text in ("python tig_states.py --without-services --summary",
                     "python tig_states.py --without-national --without-services --summary",
                     "test_tig_services.py", "(national-services.md)", "(tig-national.md)"):
            self.assertIn(text, self.doc)


if __name__ == "__main__":
    unittest.main()
