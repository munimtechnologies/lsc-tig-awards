# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Pro Bono Innovation Fund (PBIF) dollars per person in poverty, by
state, 2014-2025, and whether the states that got the most before 2022 kept
getting the most after.

    python pbif_poverty.py            # markdown table, most over-represented first
    python pbif_poverty.py --json     # the same rows as JSON
    python pbif_poverty.py --summary  # headline figures as JSON

The 2014-2021 grants are the named grants in pbif_history.py; the 2022-2025
grants are the awards page plus the release-only grants, as in pbif.py. The
eight 2020 supplemental grants (about $1.2 million) are left out: no release
names them or their states. Every year is set against the poverty
population behind LSC's 2025 basic field money (poverty.py).
"""
import argparse
import json
import os
import sys

import basic_field
import pbif
import pbif_history
import poverty
import tig

HERE = os.path.dirname(os.path.abspath(__file__))
PERIODS = ("2014-2021", "2022-2025", "2014-2025")


def early_awards(history):
    return [{"year": r["year"], "grantee": g["grantee"], "state": g["state"],
             "amount_usd": pbif_history.usd(g["printed"])}
            for r in history["rounds"] for g in r["grants"]]


def periods(history, later_awards):
    early = early_awards(history)
    return dict(zip(PERIODS, (early, later_awards, early + later_awards)))


def poverty_by_state(areas, printed):
    pov = {}
    for r in poverty.poverty_areas(areas, printed):
        pov[r["state"]] = pov.get(r["state"], 0) + r["poverty_population"]
    return pov


def compare(history, later_awards, areas, printed):
    """One row per jurisdiction LSC funds by poverty population. For each
    period, `index` is the state's share of PBIF dollars divided by its share
    of the poverty population: 1.0 means PBIF money in proportion to people
    in poverty."""
    pov = poverty_by_state(areas, printed)
    usd = {}
    for label, awards in periods(history, later_awards).items():
        got = usd[label] = {}
        for a in awards:
            got[a["state"]] = got.get(a["state"], 0) + a["amount_usd"]
        missing = set(got) - set(pov)
        if missing:
            raise ValueError("PBIF states with no poverty population: %s" % sorted(missing))
    pov_total = sum(pov.values())
    totals = {label: sum(got.values()) for label, got in usd.items()}
    rows = []
    for state, people in pov.items():
        row = {"state": state, "poverty_population": people, "poverty_share": people / pov_total}
        for label in PERIODS:
            t = usd[label].get(state, 0)
            row[label] = {"pbif_usd": round(t, 2), "pbif_share": t / totals[label],
                          "per_person_in_poverty": t / people,
                          "index": (t / totals[label]) / (people / pov_total)}
        rows.append(row)
    rows.sort(key=lambda r: (-r["2014-2025"]["index"], r["state"]))
    return rows


def correlation(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / (sxx * syy) ** 0.5


def headline(rows):
    def group(label, pred):
        g = [r for r in rows if pred(r[label])]
        return {"states": sorted(r["state"] for r in g), "count": len(g),
                "poverty_share": sum(r["poverty_share"] for r in g),
                "pbif_share": sum(r[label]["pbif_share"] for r in g)}
    people = sum(r["poverty_population"] for r in rows)
    out = {"jurisdictions": len(rows), "poverty_population": people}
    for label in PERIODS:
        usd = sum(r[label]["pbif_usd"] for r in rows)
        out[label] = {"pbif_usd": round(usd, 2), "per_person_in_poverty": usd / people,
                      "none": group(label, lambda p: p["pbif_usd"] == 0),
                      "under_half": group(label, lambda p: p["index"] < 0.5),
                      "over_double": group(label, lambda p: p["index"] >= 2)}
    out["top5"] = [{"state": r["state"], "index": round(r["2014-2025"]["index"], 2)} for r in rows[:5]]

    def both(pred):
        return sorted(r["state"] for r in rows if pred(r["2014-2021"]) and pred(r["2022-2025"]))
    out["both_periods"] = {
        "none": both(lambda p: p["pbif_usd"] == 0),
        "under_half": both(lambda p: p["index"] < 0.5),
        "over_double": both(lambda p: p["index"] >= 2),
        "per_person_correlation": correlation([r["2014-2021"]["per_person_in_poverty"] for r in rows],
                                              [r["2022-2025"]["per_person_in_poverty"] for r in rows]),
    }
    return out


def markdown(rows):
    lines = ["| State | People in poverty | Share | PBIF 2014-2021 | PBIF 2022-2025 | PBIF 2014-2025 | Share | Per person in poverty | Index | Index 2014-2021 | Index 2022-2025 |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a, b, c = (r[label] for label in PERIODS)
        lines.append("| %s | %s | %s | %s | %s | %s | %s | $%.2f | %.2f | %.2f | %.2f |" % (
            r["state"], format(r["poverty_population"], ","), tig.pct(r["poverty_share"], 1),
            tig.dollars(a["pbif_usd"]), tig.dollars(b["pbif_usd"]), tig.dollars(c["pbif_usd"]),
            tig.pct(c["pbif_share"], 1), c["per_person_in_poverty"], c["index"], a["index"], b["index"]))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=pbif_history.DATA)
    p.add_argument("--pbif-data", default=pbif.DATA)
    p.add_argument("--releases-data", default=pbif.RELEASES)
    p.add_argument("--basic-field", default=basic_field.DATA)
    p.add_argument("--competition", default=poverty.DATA)
    p.add_argument("--json", action="store_true", help="print the rows as JSON")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    areas = basic_field.load(args.basic_field)["service_areas"]
    printed = poverty.load(args.competition)["service_areas"]
    late = pbif_history.later(pbif.load(args.pbif_data)["awards"], pbif.load_releases(args.releases_data), areas)
    rows = compare(pbif_history.load(args.data), late, areas, printed)
    if args.summary:
        json.dump(headline(rows), sys.stdout, indent=2)
        print()
    elif args.json:
        json.dump(rows, sys.stdout, indent=2)
        print()
    else:
        print(markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
