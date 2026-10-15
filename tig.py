# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Summarise LSC Technology Initiative Grant awards by year: how many awards,
and how many dollars, went to projects whose LSC description mentions AI.

    python tig.py              # markdown table by year
    python tig.py --json       # the same as JSON
    python tig.py --ai 2025    # the AI awards of one year
    python tig.py --states     # how many rounds each state had an award in
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "awards.json")

# The 50 states and DC. A territory is added to the states table only if it
# has an award.
JURISDICTIONS = """AK AL AR AZ CA CO CT DC DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT
NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY""".split()


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def summary(awards):
    """One row per year. Awards with no published amount count as awards
    but are left out of both dollar totals."""
    years = {}
    for a in awards:
        y = years.setdefault(a["year"], {
            "year": a["year"], "awards": 0, "ai_awards": 0, "ai_intake_awards": 0,
            "dollars_listed": 0.0, "ai_dollars": 0.0, "unpriced": 0})
        y["awards"] += 1
        amount = a["amount_usd"]
        if amount is None:
            y["unpriced"] += 1
        else:
            y["dollars_listed"] += amount
        if a["mentions_ai"]:
            y["ai_awards"] += 1
            if amount is not None:
                y["ai_dollars"] += amount
            if a["mentions_intake"]:
                y["ai_intake_awards"] += 1
    rows = []
    for year in sorted(years):
        y = years[year]
        y["dollars_listed"] = round(y["dollars_listed"], 2)
        y["ai_dollars"] = round(y["ai_dollars"], 2)
        rows.append(y)
    return rows


def pct(num, den):
    return "%.1f%%" % (100.0 * num / den)


def dollars(x):
    return "$" + format(int(round(x)), ",")


def markdown(rows):
    lines = ["| Year | Awards | Mention AI | Share of awards | Dollars listed | AI dollars | AI share of dollars | AI and intake |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %d | %d | %s | %s | %s | %s | %d |" % (
            r["year"], r["awards"], r["ai_awards"], pct(r["ai_awards"], r["awards"]),
            dollars(r["dollars_listed"]), dollars(r["ai_dollars"]),
            pct(r["ai_dollars"], r["dollars_listed"]), r["ai_intake_awards"]))
    return "\n".join(lines)


def ai_awards(awards, year):
    return [a for a in awards if a["year"] == year and a["mentions_ai"]]


def state_rounds(awards):
    """For each state and DC, the number of rounds in which at least one of
    its programs had an award (0 for none)."""
    years = {}
    for a in awards:
        years.setdefault(a["state"], set()).add(a["year"])
    return {s: len(years.get(s, ())) for s in set(JURISDICTIONS) | set(years)}


def every_round(awards):
    """Grantees, by the name LSC printed, with an award in every round."""
    rounds = {a["year"] for a in awards}
    seen = {}
    for a in awards:
        seen.setdefault(a["grantee"], set()).add(a["year"])
    return sorted(g for g, ys in seen.items() if ys == rounds)


def states_markdown(awards):
    counts = state_rounds(awards)
    n = len({a["year"] for a in awards})
    lines = ["| Rounds with a TIG (of %d) | States |" % n, "|---|---|"]
    for k in range(n, -1, -1):
        group = sorted(s for s, c in counts.items() if c == k)
        if group:
            lines.append("| %d | %s (%d) |" % (k, ", ".join(group), len(group)))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--json", action="store_true", help="print the summary as JSON")
    p.add_argument("--ai", type=int, metavar="YEAR", help="list one year's AI awards")
    p.add_argument("--states", action="store_true", help="rounds with an award, by state")
    args = p.parse_args(argv)
    awards = load(args.data)["awards"]
    if args.ai:
        for a in ai_awards(awards, args.ai):
            amount = "unpublished" if a["amount_usd"] is None else dollars(a["amount_usd"])
            intake = " [intake]" if a["mentions_intake"] else ""
            print("%s (%s) %s%s: %s" % (a["grantee"], a["state"], amount, intake, a["ai_terms"]))
    elif args.states:
        print(states_markdown(awards))
        print()
        print("Award in every round: " + "; ".join(every_round(awards)))
    elif args.json:
        json.dump(summary(awards), sys.stdout, indent=2)
        print()
    else:
        print(markdown(summary(awards)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
