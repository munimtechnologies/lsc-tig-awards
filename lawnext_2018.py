# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LawNext's November 2018 list of the 2018 TIG round (a third-party article,
not an LSC document) set against LSC's 2018 description page and releases.

    python lawnext_2018.py            # grants that don't follow the $2,000 gap, or that LSC prints twice
    python lawnext_2018.py --summary  # headline figures as JSON
"""
import argparse
import json
import os
import sys

import tig
import tig_history

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "tig_2018_lawnext.json")
GAP = -2000  # LawNext's amount minus the description page's, for most grants


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rows(lawnext, history):
    """One row per grant of the round, in the description page's order:
    LawNext's amount, the page's, and any other LSC source's."""
    by_tig = {g["tig"]: tig_history.usd(g["printed"]) for g in lawnext["grants"]}
    rnd = [r for r in history["rounds"] if r["year"] == lawnext["year"]][0]
    out = []
    for g in rnd["grants"]:
        ln = by_tig[g["tig"]]
        page = tig_history.usd(g["printed"])
        other = {s: tig_history.usd(p) for s, p in sorted(g.get("other", {}).items())}
        out.append({"tig": g["tig"], "grantee": g["grantee"], "lawnext": ln, "page": page,
                    "minus_page": ln - page, "other": other,
                    "minus_other": {s: ln - v for s, v in other.items()}})
    return out


def notable(rs):
    """Grants off the usual gap, or printed differently by another LSC source."""
    return [r for r in rs if r["minus_page"] != GAP or r["other"]]


def summary(lawnext, history):
    rs = rows(lawnext, history)
    rnd = [r for r in history["rounds"] if r["year"] == lawnext["year"]][0]
    listed = sum(r["lawnext"] for r in rs)
    stated = tig_history.usd(lawnext["stated_total"])
    lsc_stated = tig_history.usd(rnd["stated_total"])
    return {
        "grants": len(rs),
        "at_gap": sum(1 for r in rs if r["minus_page"] == GAP),
        "gap": GAP,
        "listed_usd": listed,
        "stated_usd": stated,
        "stated_minus_listed": stated - listed,
        "lsc_stated_usd": lsc_stated,
        "stated_minus_lsc_stated": stated - lsc_stated,
        "page_listed_usd": sum(r["page"] for r in rs),
        "off_gap": [r["tig"] for r in rs if r["minus_page"] != GAP],
    }


def markdown(rs):
    lines = ["| Grantee | TIG # | LawNext | Description page | LawNext minus page | Other LSC source | It prints | LawNext minus it |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rs:
        if r["other"]:
            source = sorted(r["other"])[0]
            cells = (tig_history.SOURCES[source], tig.dollars(r["other"][source]),
                     tig_history.signed(r["minus_other"][source]))
        else:
            cells = ("-", "-", "-")
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            (r["grantee"], r["tig"], tig.dollars(r["lawnext"]), tig.dollars(r["page"]),
             tig_history.signed(r["minus_page"])) + cells))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--history", default=tig_history.DATA)
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    lawnext = load(args.data)
    history = tig_history.load(args.history)
    if args.summary:
        json.dump(summary(lawnext, history), sys.stdout, indent=2)
        print()
    else:
        print(markdown(notable(rows(lawnext, history))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
