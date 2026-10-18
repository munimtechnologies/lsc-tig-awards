# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Pro Bono Innovation Fund (PBIF) 2026 round from LSC's two 14 October
2026 press releases, before the PBIF Awards page lists it: the named awards,
each release's list against its own total, and the round set against the
rounds before it.

    python pbif_2026.py              # the named awards
    python pbif_2026.py --releases   # each release's named awards against its total
    python pbif_2026.py --summary    # headline figures as JSON
"""
import argparse
import json
import os
import re
import sys

import pbif
import pbif_history
import tig

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "pbif_2026.json")
MILLION = re.compile(r"\$(\d+(?:\.\d+)?) million")


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def usd(award):
    return pbif.parse_amount(award["printed"].lstrip("$"))


def named(data, kind):
    return [a for a in data["awards"] if a["kind"] == kind]


def release_rows(data):
    """Each release: the awards it names, their sum and LSC's stated total.
    A release marked complete names every award it counts."""
    rows = []
    for rel in data["releases"]:
        awards = [a for a in data["awards"] if rel["url"] in a["sources"]]
        rows.append({"title": rel["title"], "url": rel["url"], "scope": rel["scope"],
                     "complete": rel["complete"], "stated_usd": rel["stated_total_usd"],
                     "stated_organizations": rel["stated_organizations"],
                     "awards": len(awards), "named_usd": sum(usd(a) for a in awards)})
    return rows


def earlier_rounds(history, releases):
    """Year -> round dollars before 2026: the listed total, or LSC's stated
    total where a release leaves grants out (2014-2021, as in pbif_history.py),
    then LSC's stated totals for 2022-2025."""
    rounds = {r["year"]: r["round_usd"] for r in pbif_history.rounds(history)}
    for rel in releases:
        rounds[rel["year"]] = int(round(float(MILLION.search(rel["stated_total"]).group(1)) * 1e6))
    return rounds


def readings(data):
    """What the stated total leaves for the awards LSC did not name, read two
    ways: every one of the 20 organizations got a project grant, or the nine
    scholarship organizations are among the 20 and each got what the one
    named scholarship got."""
    r = data["round"]
    grants = named(data, "grant")
    named_usd = sum(usd(a) for a in grants)
    scholarship_usd = usd(named(data, "scholarship")[0])
    a_count = r["stated_organizations"] - len(grants)
    a_left = r["stated_total_usd"] - named_usd
    b_count = r["stated_organizations"] - r["scholarship_organizations"] - len(grants)
    b_left = a_left - r["scholarship_organizations"] * scholarship_usd
    return {"named_grants": len(grants), "named_usd": named_usd, "named_mean": named_usd / len(grants),
            "scholarship_usd": scholarship_usd,
            "all_grants": {"unnamed": a_count, "left_usd": a_left, "mean": a_left / a_count},
            "with_scholarships": {"unnamed": b_count, "left_usd": b_left, "mean": b_left / b_count}}


def summary(data, history, releases):
    r = data["round"]
    total = r["stated_total_usd"]
    before = earlier_rounds(history, releases)
    since = max(y for y, v in before.items() if v < total)
    low = min((v, y) for y, v in before.items() if y > since)
    return {
        "stated_usd": total,
        "awards": len(data["awards"]),
        "named_states": sorted({a["state"] for a in named(data, "grant")}),
        "readings": readings(data),
        "named_share": sum(usd(a) for a in named(data, "grant")) / total,
        "drop_from_2025": (before[2025] - total) / before[2025],
        "smallest_since": since,
        "lowest_after": {"year": low[1], "usd": low[0]},
        "running_added": r["running_count"] - r["previous_running_count"],
        "releases": release_rows(data),
    }


def markdown(data):
    lines = ["| Grantee | State | Kind | Amount | Amount printed by |", "|---|---|---|---|---|"]
    for a in data["awards"]:
        lines.append("| %s | %s | %s | %s | %s |" % (a["grantee"], a["state"], a["kind"], a["printed"],
                                                    a["printed_by"]))
    return "\n".join(lines)


def releases_markdown(rows):
    lines = ["| Release | Scope | LSC's total | Organizations | Awards named | Named total |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| [%s](%s) | %s | %s | %d | %d | %s |" % (
            r["title"], r["url"], r["scope"], tig.dollars(r["stated_usd"]), r["stated_organizations"],
            r["awards"], tig.dollars(r["named_usd"])))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--history-data", default=pbif_history.DATA)
    p.add_argument("--releases-data", default=pbif.RELEASES)
    p.add_argument("--releases", action="store_true", help="each release's named awards against its total")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    data = load(args.data)
    if args.releases:
        print(releases_markdown(release_rows(data)))
    elif args.summary:
        json.dump(summary(data, pbif_history.load(args.history_data), pbif.load_releases(args.releases_data)),
                  sys.stdout, indent=2)
        print()
    else:
        print(markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
