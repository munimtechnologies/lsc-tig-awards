# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Technology Initiative Grant (TIG) rounds 2018-2020 from LSC's own
description pages and press releases, each list summed against LSC's stated
total, and LSC's counts of grants, organizations and states for 2018-2025
checked against the lists.

    python tig_history.py              # list sums against LSC's stated totals
    python tig_history.py --amounts    # grants two LSC sources print differently
    python tig_history.py --headlines  # LSC's counts against the lists
    python tig_history.py --summary    # headline figures as JSON
"""
import argparse
import json
import os
import sys

import tig

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "tig_history.json")
TERRITORIES = ["AS", "GU", "MP", "PR", "VI"]
SOURCES = {"page": "description page", "release": "release", "bundle": "per-grantee release",
           "index": "index page", "headline": "release headline"}
COUNTS = (("grants", "grants"), ("organizations", "organizations"), ("states", "states"))


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def usd(printed):
    return int(printed.lstrip("$").replace(",", ""))


def amount(grant, source):
    """The amount `source` prints for a grant: the page's unless it differs."""
    return usd(grant.get("other", {}).get(source, grant["printed"]))


def totals(history):
    """One row per round and per source that prints every grant."""
    rows = []
    for r in history["rounds"]:
        stated = usd(r["stated_total"])
        for source in r["complete"]:
            listed = sum(amount(g, source) for g in r["grants"])
            rows.append({"year": r["year"], "source": source, "grants": len(r["grants"]),
                         "listed_usd": listed, "stated_usd": stated, "difference": listed - stated})
    return rows


def differences(history):
    """Every grant another LSC source prints with a different amount, and the
    page's list total with only that one amount changed."""
    rows = []
    for r in history["rounds"]:
        page = sum(usd(g["printed"]) for g in r["grants"])
        stated = usd(r["stated_total"])
        for g in r["grants"]:
            for source, printed in sorted(g.get("other", {}).items()):
                total = page - usd(g["printed"]) + usd(printed)
                rows.append({"year": r["year"], "grantee": g["grantee"], "tig": g["tig"],
                             "page": g["printed"], "source": source, "other": printed,
                             "total_usd": total, "equals_stated": total == stated})
    return rows


def listed(history, awards):
    """Grants, organizations (distinct printed names) and states, DC and
    territories in each round's list: 2018-2020 from this file, 2021-2025
    from data/awards.json."""
    by_year = {r["year"]: list(r["grants"]) for r in history["rounds"]}
    for a in awards:
        by_year.setdefault(a["year"], []).append(a)
    return {y: {"grants": len(gs), "organizations": len({g["grantee"] for g in gs}),
                "states": len({g["state"] for g in gs})} for y, gs in by_year.items()}


def headlines(history, awards):
    """Each of LSC's statements with the counts of the same round's list and
    the counts that differ."""
    counts = listed(history, awards)
    rows = []
    for h in history["headlines"]:
        got = counts[h["year"]]
        wrong = [k for k, _ in COUNTS if h[k] is not None and h[k] != got[k]]
        rows.append(dict(h, listed=got, wrong=wrong))
    return rows


def signed(x):
    if x == 0:
        return "$0"
    return ("+" if x > 0 else "-") + tig.dollars(abs(x))


def totals_markdown(rows):
    lines = ["| Year | Source | Grants | Sum of the list | LSC's stated total | Difference |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %s | %d | %s | %s | %s |" % (
            r["year"], SOURCES[r["source"]], r["grants"], tig.dollars(r["listed_usd"]),
            tig.dollars(r["stated_usd"]), signed(r["difference"])))
    return "\n".join(lines)


def differences_markdown(rows):
    lines = ["| Year | Grantee | TIG # | Description page | Other source | It prints | Page list with that amount | Equals stated total |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %s | %s | %s | %s | %s | %s | %s |" % (
            r["year"], r["grantee"], r["tig"], r["page"], SOURCES[r["source"]], r["other"],
            tig.dollars(r["total_usd"]), "yes" if r["equals_stated"] else "no"))
    return "\n".join(lines)


def says(h):
    return ", ".join("%d %s" % (h[k], word) for k, word in COUNTS if h[k] is not None)


def headlines_markdown(rows):
    lines = ["| Year | Source | LSC says | Grants listed | Organizations listed | States, DC and territories listed | Fits the list |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        got = r["listed"]
        fits = "no (%s)" % ", ".join(r["wrong"]) if r["wrong"] else "yes"
        lines.append("| %d | %s | %s | %d | %d | %d | %s |" % (
            r["year"], SOURCES[r["source"]], says(r), got["grants"], got["organizations"],
            got["states"], fits))
    return "\n".join(lines)


def summary(history, awards):
    return {
        "totals": totals(history),
        "differences": differences(history),
        "listed": {str(y): c for y, c in sorted(listed(history, awards).items())},
        "not_fitting": [{k: r[k] for k in ("year", "source", "quote", "wrong")}
                        for r in headlines(history, awards) if r["wrong"]],
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--awards", default=tig.DATA)
    p.add_argument("--amounts", action="store_true", help="grants two LSC sources print differently")
    p.add_argument("--headlines", action="store_true", help="LSC's counts against the lists")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    history = load(args.data)
    if args.amounts:
        print(differences_markdown(differences(history)))
    elif args.headlines or args.summary:
        awards = tig.load(args.awards)["awards"]
        if args.headlines:
            print(headlines_markdown(headlines(history, awards)))
        else:
            json.dump(summary(history, awards), sys.stdout, indent=2)
            print()
    else:
        print(totals_markdown(totals(history)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
