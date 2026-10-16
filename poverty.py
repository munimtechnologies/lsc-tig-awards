# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""People in poverty behind LSC's basic field money, and TIG dollars per
person in poverty, by state.

    python poverty.py            # markdown table, most over-represented first
    python poverty.py --json     # the same rows as JSON
    python poverty.py --summary  # headline figures as JSON
    python poverty.py --check    # LSC's printed 2027 figures against the 2025 amounts
    python poverty.py --areas    # poverty population of every general and
                                 # agricultural worker service area, as JSON

LSC divides basic field money, after a fixed set-aside for Native American
service areas, by each area's share of the poverty population. Its 2027
competition page prints the poverty population of 46 areas; their 2025
amounts divided by those populations give one dollar rate, and that rate
turns every other 2025 amount back into a poverty population.
"""
import argparse
import json
import os
import re
import sys

import basic_field
import tig

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "lsc_2027_competition.json")

# Service area codes: AK-1 (general), MCA or MMX-1 (agricultural worker),
# NAZ-5 (Native American). MA-10 and NC-5 are general.
NATIVE = re.compile(r"^N[A-Z]{2}-\d+$")
AGRICULTURAL = re.compile(r"^M[A-Z]{2}(?:-\d+)?$")
GENERAL = re.compile(r"^[A-Z]{2}-\d+$")


def kind(code):
    if NATIVE.match(code):
        return "native_american"
    if AGRICULTURAL.match(code):
        return "agricultural_worker"
    if GENERAL.match(code):
        return "general"
    raise ValueError("unknown service area code: %r" % code)


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def native_share(areas):
    """Share of basic field dollars in Native American service areas."""
    total = sum(a["amount_usd"] for a in areas)
    return sum(a["amount_usd"] for a in areas if kind(a["service_area"]) == "native_american") / total


def rate(areas, printed):
    """2025 basic field dollars per person in poverty, over the areas whose
    poverty population LSC printed."""
    amount = {a["service_area"]: a["amount_usd"] for a in areas}
    rows = [r for r in printed if r["poverty_population"] is not None]
    return sum(amount[r["service_area"]] for r in rows) / sum(r["poverty_population"] for r in rows)


def check(areas, printed):
    """Each printed 2027 row next to its 2025 amount: the poverty population
    that amount implies, and the 2027 estimate as a fraction of it."""
    amount = {a["service_area"]: a["amount_usd"] for a in areas}
    usd = rate(areas, printed)
    scale = sum(r["estimated_grant_usd"] for r in printed) / sum(amount[r["service_area"]] for r in printed)
    rows = []
    for r in printed:
        a = amount[r["service_area"]]
        row = {"service_area": r["service_area"], "kind": kind(r["service_area"]),
               "printed_type": r["type"], "amount_2025_usd": a,
               "estimated_2027_usd": r["estimated_grant_usd"],
               "estimate_minus_scaled_2025": r["estimated_grant_usd"] - a * scale,
               "poverty_population": r["poverty_population"]}
        if r["poverty_population"] is not None:
            row["implied_poverty_population"] = a / usd
            row["implied_minus_printed"] = a / usd - r["poverty_population"]
        rows.append(row)
    return {"usd_per_person_2025": usd, "scale_2027_over_2025": scale, "rows": rows}


def poverty_areas(areas, printed):
    """Every general and agricultural worker area with its poverty population:
    LSC's printed figure where there is one, otherwise derived from the 2025
    amount at the common rate."""
    usd = rate(areas, printed)
    known = {r["service_area"]: r["poverty_population"] for r in printed
             if r["poverty_population"] is not None}
    rows = []
    for a in areas:
        k = kind(a["service_area"])
        if k == "native_american":
            continue
        code = a["service_area"]
        rows.append({"service_area": code, "state": a["state"], "kind": k,
                     "amount_2025_usd": a["amount_usd"],
                     "poverty_population": known.get(code, int(round(a["amount_usd"] / usd))),
                     "source": "printed" if code in known else "derived"})
    return rows


def compare(awards, areas, printed):
    """One row per jurisdiction. `index` is the state's share of TIG dollars
    divided by its share of the poverty population LSC funds against: 1.0
    means TIG money in proportion to people in poverty."""
    pov = {}
    for r in poverty_areas(areas, printed):
        pov[r["state"]] = pov.get(r["state"], 0) + r["poverty_population"]
    tig_usd = {}
    for a in awards:
        if a["amount_usd"] is not None:
            tig_usd[a["state"]] = tig_usd.get(a["state"], 0) + a["amount_usd"]
    missing = set(tig_usd) - set(pov)
    if missing:
        raise ValueError("TIG states with no poverty population: %s" % sorted(missing))
    old = {r["state"]: r["index"] for r in basic_field.compare(awards, areas)}
    pov_total, tig_total = sum(pov.values()), sum(tig_usd.values())
    rows = []
    for state, people in pov.items():
        t = tig_usd.get(state, 0)
        tig_share, pov_share = t / tig_total, people / pov_total
        rows.append({"state": state, "poverty_population": people, "poverty_share": pov_share,
                     "tig_usd": round(t, 2), "tig_share": tig_share,
                     "tig_per_person_in_poverty": t / people,
                     "index": tig_share / pov_share, "basic_field_index": old[state]})
    rows.sort(key=lambda r: (-r["index"], r["state"]))
    return rows


def headline(rows, areas, printed):
    def group(pred):
        g = [r for r in rows if pred(r)]
        return {"states": sorted(r["state"] for r in g), "count": len(g),
                "poverty_share": sum(r["poverty_share"] for r in g),
                "tig_share": sum(r["tig_share"] for r in g)}
    people = sum(r["poverty_population"] for r in rows)
    usd = sum(r["tig_usd"] for r in rows)
    return {
        "jurisdictions": len(rows),
        "poverty_population": people,
        "tig_usd": round(usd, 2),
        "tig_per_person_in_poverty": usd / people,
        "usd_per_person_2025": rate(areas, printed),
        "native_american_share_2025": native_share(areas),
        "no_tig": group(lambda r: r["tig_usd"] == 0),
        "under_half": group(lambda r: r["index"] < 0.5),
        "over_double": group(lambda r: r["index"] >= 2),
        "top5": [{"state": r["state"], "index": round(r["index"], 2)} for r in rows[:5]],
    }


def markdown(rows):
    lines = ["| State | People in poverty | Share | TIG 2021-2025 | Share | TIG per person in poverty | Index | Index on dollars (0.3.0) |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | $%.2f | %.2f | %.2f |" % (
            r["state"], format(r["poverty_population"], ","), tig.pct(r["poverty_share"], 1),
            tig.dollars(r["tig_usd"]), tig.pct(r["tig_share"], 1),
            r["tig_per_person_in_poverty"], r["index"], r["basic_field_index"]))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--basic-field", default=basic_field.DATA)
    p.add_argument("--awards", default=tig.DATA)
    p.add_argument("--json", action="store_true", help="print the rows as JSON")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    p.add_argument("--check", action="store_true", help="print the 2027 rows checked against 2025")
    p.add_argument("--areas", action="store_true", help="print poverty population by service area")
    args = p.parse_args(argv)
    printed = load(args.data)["service_areas"]
    areas = basic_field.load(args.basic_field)["service_areas"]
    if args.check:
        json.dump(check(areas, printed), sys.stdout, indent=1)
        print()
        return 0
    if args.areas:
        json.dump(poverty_areas(areas, printed), sys.stdout, indent=1)
        print()
        return 0
    rows = compare(tig.load(args.awards)["awards"], areas, printed)
    if args.summary:
        json.dump(headline(rows, areas, printed), sys.stdout, indent=2)
        print()
    elif args.json:
        json.dump(rows, sys.stdout, indent=2)
        print()
    else:
        print(markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
