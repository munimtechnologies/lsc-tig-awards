# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Checks that README.md links every page in docs/ and that every docs/ page
it links exists."""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
DOCS = os.path.join(HERE, "docs")


@unittest.skipUnless(os.path.exists(README) and os.path.isdir(DOCS), "needs README.md and docs/")
class ReadmeDocs(unittest.TestCase):
    def setUp(self):
        with open(README, encoding="utf-8") as f:
            self.text = f.read()

    def test_every_page_linked(self):
        pages = sorted(n for n in os.listdir(DOCS) if n.endswith(".md"))
        self.assertTrue(pages)
        self.assertEqual([n for n in pages if "(docs/%s)" % n not in self.text], [])

    def test_every_link_exists(self):
        links = sorted(set(re.findall(r"\(docs/([\w.-]+\.md)\)", self.text)))
        self.assertTrue(links)
        self.assertEqual([n for n in links if not os.path.exists(os.path.join(DOCS, n))], [])


if __name__ == "__main__":
    unittest.main()
