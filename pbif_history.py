# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Pro Bono Innovation Fund (PBIF) rounds 2014-2021 from LSC's own press
releases, and LSC's running totals for the program checked against every
grant the releases and the awards page list.

    python pbif_history.py             # one row per round, 2014-2021
    python pbif_history.py --running   # LSC's running totals against the lists
    python pbif_history.py --states    # states with a PBIF grant, 2014-2025
    python pbif_history.py --summary   # headline figures as JSON
"""
import argparse
import json
import os
import sys

import basic_field
import pbif
import tig

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "pbif_history.json")
STATES = [j for j in tig.JURISDICTIONS if j != "DC"]


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def usd(printed):
    return pbif.parse_amount(printed.lstrip("$"))


def rounds(history):
    """One row per round. `round_usd` is the listed total, or LSC's stated
    total where the release leaves grants out (2020's supplemental grants)."""
    rows = []
    for r in history["rounds"]:
        listed = sum(usd(g["printed"]) for g in r["grants"])
        stated = usd(r["stated_total"]) if r["stated_total"] else None
        rows.append({"year": r["year"], "grants": len(r["grants"]), "unlisted": r["unlisted_grants"],
                     "organizations": len({pbif.norm(g["grantee"]) for g in r["grants"]}),
                     "stated_organizations": r["stated_organizations"],
                     "listed_usd": listed, "fund_usd": r["fund_usd"], "share": listed / r["fund_usd"],
                     "stated_total": r["stated_total"], "stated_usd": stated,
                     "round_usd": listed if r["complete"] else stated, "url": r["url"]})
    return rows


def later(page_awards, releases, service_areas):
    """The 2022-2025 rounds: the awards page plus the grants only a press
    release prints, as in pbif.py."""
    return pbif.combined(page_awards, pbif.reconcile(page_awards, releases), service_areas)


def running(history, later_awards):
    """Each of LSC's running totals next to the grants listed up to the same
    round: all of them, and without the grants no release names."""
    rows = []
    early = rounds(history)
    for s in history["statements"]:
        upto = [r for r in early if r["year"] <= s["through"]]
        more = [a for a in later_awards if a["year"] <= s["through"]]
        listed = sum(r["grants"] for r in upto) + len(more)
        rows.append({"source": s["source"], "url": s["url"], "through": s["through"],
                     "count": s["count"], "unit": s["unit"], "dollars": s["dollars"],
                     "listed": listed + sum(r["unlisted"] for r in upto),
                     "listed_named": listed,
                     "listed_usd": sum(r["round_usd"] for r in upto) + sum(a["amount_usd"] for a in more)})
    return rows


def jurisdictions(history, later_awards):
    early = {g["state"] for r in history["rounds"] for g in r["grants"]}
    return early, {a["state"] for a in later_awards}


def state_rows(early, late):
    every = early | late
    return [("2014-2021", early), ("2022-2025", late), ("2014-2025", every),
            ("2014-2021 only", early - late), ("2022-2025 only", late - early),
            ("Never, 2014-2025", set(STATES) - every)]


def rounds_markdown(rows):
    lines = ["| Year | Grants listed | Not listed | Organizations listed | Listed total | Fund | Listed share of fund | LSC's stated total |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %d | %d | %d | %s | %s | %s | %s |" % (
            r["year"], r["grants"], r["unlisted"], r["organizations"], tig.dollars(r["listed_usd"]),
            tig.dollars(r["fund_usd"]), tig.pct(r["listed_usd"], r["fund_usd"]), r["stated_total"] or "none"))
    return "\n".join(lines)


def running_markdown(rows):
    lines = ["| LSC's statement | Through | LSC's count | Grants listed | Without the 2020 supplemental grants | LSC's dollars | Listed dollars |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %d | %d %s | %d | %d | %s | $%.2f million |" % (
            r["source"], r["through"], r["count"], r["unit"], r["listed"], r["listed_named"],
            r["dollars"], r["listed_usd"] / 1e6))
    return "\n".join(lines)


def states_markdown(rows):
    lines = ["| Period | States | Also | Which states |", "|---|---|---|---|"]
    for label, js in rows:
        states = sorted(j for j in js if j in STATES)
        other = sorted(j for j in js if j not in STATES)
        lines.append("| %s | %d | %s | %s |" % (label, len(states), ", ".join(other) or "-", " ".join(states)))
    return "\n".join(lines)


def summary(history, later_awards):
    early, late = jurisdictions(history, later_awards)
    rows = rounds(history)
    return {
        "rounds": [{k: r[k] for k in ("year", "grants", "unlisted", "organizations", "listed_usd",
                                      "fund_usd", "stated_usd")} for r in rows],
        "listed_2014_2021_usd": sum(r["listed_usd"] for r in rows),
        "running": running(history, later_awards),
        "states": {label: sorted(js) for label, js in state_rows(early, late)},
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--pbif-data", default=pbif.DATA)
    p.add_argument("--releases-data", default=pbif.RELEASES)
    p.add_argument("--basic-field", default=basic_field.DATA)
    p.add_argument("--running", action="store_true", help="LSC's running totals against the lists")
    p.add_argument("--states", action="store_true", help="states with a PBIF grant, 2014-2025")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    history = load(args.data)
    if not (args.running or args.states or args.summary):
        print(rounds_markdown(rounds(history)))
        return 0
    areas = basic_field.load(args.basic_field)["service_areas"]
    late = later(pbif.load(args.pbif_data)["awards"], pbif.load_releases(args.releases_data), areas)
    if args.running:
        print(running_markdown(running(history, late)))
    elif args.states:
        print(states_markdown(state_rows(*jurisdictions(history, late))))
    else:
        json.dump(summary(history, late), sys.stdout, indent=2)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
