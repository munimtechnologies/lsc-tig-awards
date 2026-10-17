# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Technology Initiative Grant (TIG) dollars by state for every round
2014-2025, and TIG dollars per person in poverty, by state, before and since
2020.

    python tig_states.py            # markdown table, most over-represented first
    python tig_states.py --rounds   # dollars per round, then per state and round
    python tig_states.py --json     # the rows as JSON
    python tig_states.py --summary  # headline figures as JSON

Each round's grants are the list the module that checks it uses: 2014 the PDF
on lsc.gov, one row per grantee (tig_2014_2015.py); 2016 and 2017 the archived
description pages, with Iowa's 2016 amount from the PBIF release
(tig_2016_2017.py); 2018-2020 the description pages (tig_history.py);
2021-2025 data/awards.json (tig.py), leaving out the one 2025 grant with no
published amount. LSC never printed a 2015 list: the seven grantees its
releases name are in --rounds but in no period. A grant counts to its
grantee's state even where the project serves other states too (Ohio State
Legal Services' LawHelp Interactive grants). Every period is set against the
poverty population behind LSC's 2025 basic field money (poverty.py).
"""
import argparse
import json
import os
import sys

import basic_field
import poverty
import tig
import tig_2014_2015
import tig_2016_2017
import tig_history

HERE = os.path.dirname(os.path.abspath(__file__))
YEARS = tuple(range(2014, 2026))
PARTIAL = (2015,)
PERIODS = {"2014-2019": range(2014, 2020), "2020-2025": range(2020, 2026), "2014-2025": range(2014, 2026)}


def grants(early, middle, late, awards):
    """One row per grant (per grantee for 2014 and 2015) with its year,
    grantee, state and amount."""
    rows = []
    for r in early["rounds"]:
        for g in r["grantees"]:
            rows.append({"year": r["year"], "grantee": g["grantee"], "state": g["state"],
                         "amount_usd": tig_history.usd(g["printed"])})
    for r in middle["rounds"]:
        amounts = tig_2016_2017.filled(r)
        for g in r["grants"]:
            rows.append({"year": r["year"], "grantee": g["grantee"], "state": g["state"],
                         "amount_usd": amounts[g["tig"]][0]})
    for r in late["rounds"]:
        for g in r["grants"]:
            rows.append({"year": r["year"], "grantee": g["grantee"], "state": g["state"],
                         "amount_usd": tig_history.usd(g["printed"])})
    for a in awards:
        if a["amount_usd"] is not None:
            rows.append({"year": a["year"], "grantee": a["grantee"], "state": a["state"],
                         "amount_usd": a["amount_usd"]})
    return rows


def round_totals(rows):
    """Grants and dollars per round."""
    out = {}
    for g in rows:
        t = out.setdefault(g["year"], {"grants": 0, "usd": 0})
        t["grants"] += 1
        t["usd"] += g["amount_usd"]
    return {y: {"grants": t["grants"], "usd": round(t["usd"], 2)} for y, t in sorted(out.items())}


def by_state(rows):
    """Dollars per state and round."""
    out = {}
    for g in rows:
        years = out.setdefault(g["state"], {})
        years[g["year"]] = years.get(g["year"], 0) + g["amount_usd"]
    return out


def poverty_by_state(areas, printed):
    pov = {}
    for r in poverty.poverty_areas(areas, printed):
        pov[r["state"]] = pov.get(r["state"], 0) + r["poverty_population"]
    return pov


def compare(rows, areas, printed):
    """One row per jurisdiction LSC funds by poverty population. For each
    period, `index` is the state's share of TIG dollars divided by its share
    of the poverty population: 1.0 means TIG money in proportion to people in
    poverty. `rounds` counts the complete rounds (all but 2015) with a grant."""
    pov = poverty_by_state(areas, printed)
    states = by_state(rows)
    missing = set(states) - set(pov)
    if missing:
        raise ValueError("TIG states with no poverty population: %s" % sorted(missing))
    usd = {label: {s: sum(t for y, t in years.items() if y in span and y not in PARTIAL)
                   for s, years in states.items()} for label, span in PERIODS.items()}
    totals = {label: sum(got.values()) for label, got in usd.items()}
    pov_total = sum(pov.values())
    out = []
    for state, people in pov.items():
        years = states.get(state, {})
        row = {"state": state, "poverty_population": people, "poverty_share": people / pov_total,
               "rounds": sum(1 for y in years if y not in PARTIAL),
               "by_year": {str(y): round(years[y], 2) for y in sorted(years)}}
        for label in PERIODS:
            t = usd[label].get(state, 0)
            row[label] = {"tig_usd": round(t, 2), "tig_share": t / totals[label],
                          "per_person_in_poverty": t / people,
                          "index": (t / totals[label]) / (people / pov_total)}
        out.append(row)
    out.sort(key=lambda r: (-r["2014-2025"]["index"], r["state"]))
    return out


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
                "tig_share": sum(r[label]["tig_share"] for r in g)}
    people = sum(r["poverty_population"] for r in rows)
    complete = len(YEARS) - len(PARTIAL)
    out = {"jurisdictions": len(rows), "poverty_population": people, "complete_rounds": complete}
    for label in PERIODS:
        usd = sum(r[label]["tig_usd"] for r in rows)
        out[label] = {"tig_usd": round(usd, 2), "per_person_in_poverty": usd / people,
                      "none": group(label, lambda p: p["tig_usd"] == 0),
                      "under_half": group(label, lambda p: p["index"] < 0.5),
                      "over_double": group(label, lambda p: p["index"] >= 2)}
    out["top5"] = [{"state": r["state"], "index": round(r["2014-2025"]["index"], 2),
                    "tig_share": round(r["2014-2025"]["tig_share"], 4)} for r in rows[:5]]
    out["rounds"] = {str(k): sorted(r["state"] for r in rows if r["rounds"] == k)
                     for k in range(complete, -1, -1) if any(r["rounds"] == k for r in rows)}

    def both(pred):
        return sorted(r["state"] for r in rows if pred(r["2014-2019"]) and pred(r["2020-2025"]))
    out["both_periods"] = {
        "none": both(lambda p: p["tig_usd"] == 0),
        "under_half": both(lambda p: p["index"] < 0.5),
        "over_double": both(lambda p: p["index"] >= 2),
        "per_person_correlation": correlation([r["2014-2019"]["per_person_in_poverty"] for r in rows],
                                              [r["2020-2025"]["per_person_in_poverty"] for r in rows]),
    }
    return out


def markdown(rows):
    lines = ["| State | People in poverty | Share | Rounds with a TIG (of 11) | TIG 2014-2019 | TIG 2020-2025 | TIG 2014-2025 | Share | Per person in poverty | Index | Index 2014-2019 | Index 2020-2025 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a, b, c = (r[label] for label in PERIODS)
        lines.append("| %s | %s | %s | %d | %s | %s | %s | %s | $%.2f | %.2f | %.2f | %.2f |" % (
            r["state"], format(r["poverty_population"], ","), tig.pct(r["poverty_share"], 1), r["rounds"],
            tig.dollars(a["tig_usd"]), tig.dollars(b["tig_usd"]), tig.dollars(c["tig_usd"]),
            tig.pct(c["tig_share"], 1), c["per_person_in_poverty"], c["index"], a["index"], b["index"]))
    return "\n".join(lines)


def totals_markdown(rows):
    totals = round_totals(rows)
    lines = ["| Year | Grants | Dollars |", "|---|---|---|"]
    for y in YEARS:
        lines.append("| %s | %d | %s |" % ("%d (partial)" % y if y in PARTIAL else y,
                                           totals[y]["grants"], tig.dollars(totals[y]["usd"])))
    complete = [t for y, t in totals.items() if y not in PARTIAL]
    lines.append("| 2014-2025 (complete rounds) | %d | %s |" % (
        sum(t["grants"] for t in complete), tig.dollars(sum(t["usd"] for t in complete))))
    return "\n".join(lines)


def rounds_markdown(rows):
    """Dollars per state and round, states with any grant only; 2015 holds
    only the grants LSC's releases name."""
    states = by_state(rows)
    totals = round_totals(rows)
    head = ["2015 (partial)" if y in PARTIAL else str(y) for y in YEARS]
    lines = ["| State | " + " | ".join(head) + " | 2014-2025 (complete rounds) |",
             "|---" * (len(YEARS) + 2) + "|"]
    for state in sorted(states):
        years = states[state]
        cells = [tig.dollars(years[y]) if y in years else "-" for y in YEARS]
        whole = sum(t for y, t in years.items() if y not in PARTIAL)
        lines.append("| %s | %s | %s |" % (state, " | ".join(cells), tig.dollars(whole)))
    whole = sum(t["usd"] for y, t in totals.items() if y not in PARTIAL)
    lines.append("| All | %s | %s |" % (" | ".join(tig.dollars(totals[y]["usd"]) for y in YEARS), tig.dollars(whole)))
    lines.append("| Grants | %s | %d |" % (" | ".join(str(totals[y]["grants"]) for y in YEARS),
                                            sum(t["grants"] for y, t in totals.items() if y not in PARTIAL)))
    return "\n".join(lines)


def build(early_path=tig_2014_2015.DATA, middle_path=tig_2016_2017.DATA,
          late_path=tig_history.DATA, awards_path=tig.DATA):
    return grants(tig_2014_2015.load(early_path), tig_2016_2017.load(middle_path),
                  tig_history.load(late_path), tig.load(awards_path)["awards"])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--early", default=tig_2014_2015.DATA)
    p.add_argument("--middle", default=tig_2016_2017.DATA)
    p.add_argument("--late", default=tig_history.DATA)
    p.add_argument("--awards", default=tig.DATA)
    p.add_argument("--basic-field", default=basic_field.DATA)
    p.add_argument("--competition", default=poverty.DATA)
    p.add_argument("--rounds", action="store_true", help="print dollars per state and round")
    p.add_argument("--json", action="store_true", help="print the rows as JSON")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    grant_rows = build(args.early, args.middle, args.late, args.awards)
    if args.rounds:
        print(totals_markdown(grant_rows))
        print()
        print(rounds_markdown(grant_rows))
        return 0
    areas = basic_field.load(args.basic_field)["service_areas"]
    printed = poverty.load(args.competition)["service_areas"]
    rows = compare(grant_rows, areas, printed)
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
