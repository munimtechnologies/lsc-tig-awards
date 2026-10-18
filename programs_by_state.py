# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Both of LSC's competitive grant programs by state, 2014-2025: Technology
Initiative Grant (TIG) and Pro Bono Innovation Fund (PBIF) dollars per person
in poverty, which jurisdictions got both, one or neither, and how closely the
two programs' per-person figures track each other.

    python programs_by_state.py            # markdown table, most over-represented first
    python programs_by_state.py --groups   # both / TIG only / PBIF only / neither
    python programs_by_state.py --json     # the rows as JSON
    python programs_by_state.py --summary  # headline figures as JSON

TIG dollars are tig_states.py's eleven complete rounds 2014-2025 (2015, with
no published list, left out); PBIF dollars are pbif_poverty.py's named grants
2014-2025. Both are set against the poverty population behind LSC's 2025
basic field money (poverty.py). LSC prints no poverty population for GU-1 or
MP-1, so poverty.py derives both from their 2025 amounts. MP-1's grantee,
Micronesian Legal Services Corporation, also works in the Federated States
of Micronesia, where the Compact of Free Association Act makes LSC's services
available (LSC advisory opinion AO-2017-007): MP's row is LSC's MP-1 service
area, not the Northern Mariana Islands alone.
"""
import argparse
import json
import sys

import basic_field
import pbif
import pbif_history
import pbif_poverty
import poverty
import tig
import tig_2014_2015
import tig_2016_2017
import tig_history
import tig_states

PERIOD = "2014-2025"
GROUPS = ("both", "tig_only", "pbif_only", "neither")
GROUP_NAMES = {"both": "Both", "tig_only": "TIG only", "pbif_only": "PBIF only", "neither": "Neither"}


def group_of(tig_usd, pbif_usd):
    if tig_usd and pbif_usd:
        return "both"
    if tig_usd:
        return "tig_only"
    if pbif_usd:
        return "pbif_only"
    return "neither"


def combine(tig_rows, pbif_rows):
    """One row per jurisdiction from tig_states.compare and
    pbif_poverty.compare. `index` is the state's share of both programs'
    dollars divided by its share of the poverty population."""
    pbif_by = {r["state"]: r for r in pbif_rows}
    if set(pbif_by) != {r["state"] for r in tig_rows}:
        raise ValueError("the TIG and PBIF tables cover different jurisdictions")
    out = []
    for t in tig_rows:
        p = pbif_by[t["state"]]
        if p["poverty_population"] != t["poverty_population"]:
            raise ValueError("poverty population differs for %s" % t["state"])
        tu, pu = t[PERIOD]["tig_usd"], p[PERIOD]["pbif_usd"]
        out.append({"state": t["state"], "poverty_population": t["poverty_population"],
                    "poverty_share": t["poverty_share"], "group": group_of(tu, pu),
                    "tig_usd": tu, "pbif_usd": pu, "usd": round(tu + pu, 2),
                    "tig_per_person_in_poverty": t[PERIOD]["per_person_in_poverty"],
                    "pbif_per_person_in_poverty": p[PERIOD]["per_person_in_poverty"],
                    "per_person_in_poverty": (tu + pu) / t["poverty_population"],
                    "tig_index": t[PERIOD]["index"], "pbif_index": p[PERIOD]["index"]})
    total = sum(r["usd"] for r in out)
    for r in out:
        r["share"] = r["usd"] / total
        r["index"] = r["share"] / r["poverty_share"]
    out.sort(key=lambda r: (-r["index"], r["state"]))
    return out


def headline(rows):
    people = sum(r["poverty_population"] for r in rows)
    tig_usd = sum(r["tig_usd"] for r in rows)
    pbif_usd = sum(r["pbif_usd"] for r in rows)
    out = {"jurisdictions": len(rows), "poverty_population": people,
           "tig_usd": round(tig_usd, 2), "pbif_usd": round(pbif_usd, 2),
           "usd": round(tig_usd + pbif_usd, 2),
           "per_person_in_poverty": (tig_usd + pbif_usd) / people,
           "tig_per_person_in_poverty": tig_usd / people,
           "pbif_per_person_in_poverty": pbif_usd / people, "groups": {}}
    for name in GROUPS:
        g = [r for r in rows if r["group"] == name]
        out["groups"][name] = {"states": sorted(r["state"] for r in g), "count": len(g),
                               "poverty_population": sum(r["poverty_population"] for r in g),
                               "poverty_share": sum(r["poverty_share"] for r in g),
                               "tig_usd": round(sum(r["tig_usd"] for r in g), 2),
                               "pbif_usd": round(sum(r["pbif_usd"] for r in g), 2)}
    out["per_person_correlation"] = tig_states.correlation(
        [r["tig_per_person_in_poverty"] for r in rows], [r["pbif_per_person_in_poverty"] for r in rows])
    out["both_over_double"] = sorted(r["state"] for r in rows if r["tig_index"] >= 2 and r["pbif_index"] >= 2)
    out["both_under_half"] = sorted(r["state"] for r in rows if r["tig_index"] < 0.5 and r["pbif_index"] < 0.5)
    out["under_half"] = sorted(r["state"] for r in rows if r["index"] < 0.5)
    out["over_double"] = sorted(r["state"] for r in rows if r["index"] >= 2)
    out["top5"] = [{"state": r["state"], "index": round(r["index"], 2)} for r in rows[:5]]
    return out


def markdown(rows):
    lines = ["| State | People in poverty | Share | Programs | TIG 2014-2025 | PBIF 2014-2025 | Both programs | Share | Per person in poverty | Index | TIG index | PBIF index |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | $%.2f | %.2f | %.2f | %.2f |" % (
            r["state"], format(r["poverty_population"], ","), tig.pct(r["poverty_share"], 1),
            GROUP_NAMES[r["group"]], tig.dollars(r["tig_usd"]), tig.dollars(r["pbif_usd"]),
            tig.dollars(r["usd"]), tig.pct(r["share"], 1), r["per_person_in_poverty"],
            r["index"], r["tig_index"], r["pbif_index"]))
    return "\n".join(lines)


def groups_markdown(head):
    lines = ["| Programs won 2014-2025 | Jurisdictions | People in poverty | Share | TIG | PBIF |",
             "|---|---|---|---|---|---|"]
    for name in GROUPS:
        g = head["groups"][name]
        lines.append("| %s | %d | %s | %s | %s | %s |" % (
            GROUP_NAMES[name], g["count"], format(g["poverty_population"], ","),
            tig.pct(g["poverty_share"], 1), tig.dollars(g["tig_usd"]), tig.dollars(g["pbif_usd"])))
    lines.append("| All | %d | %s | 100.0%% | %s | %s |" % (
        head["jurisdictions"], format(head["poverty_population"], ","),
        tig.dollars(head["tig_usd"]), tig.dollars(head["pbif_usd"])))
    return "\n".join(lines)


def build(basic_field_path=basic_field.DATA, competition_path=poverty.DATA,
          history_path=pbif_history.DATA, pbif_path=pbif.DATA, releases_path=pbif.RELEASES,
          early_path=tig_2014_2015.DATA, middle_path=tig_2016_2017.DATA,
          late_path=tig_history.DATA, awards_path=tig.DATA):
    areas = basic_field.load(basic_field_path)["service_areas"]
    printed = poverty.load(competition_path)["service_areas"]
    tig_rows = tig_states.compare(tig_states.build(early_path, middle_path, late_path, awards_path),
                                  areas, printed)
    late = pbif_history.later(pbif.load(pbif_path)["awards"], pbif.load_releases(releases_path), areas)
    pbif_rows = pbif_poverty.compare(pbif_history.load(history_path), late, areas, printed)
    return combine(tig_rows, pbif_rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--groups", action="store_true", help="print the four groups as a table")
    p.add_argument("--json", action="store_true", help="print the rows as JSON")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    rows = build()
    if args.summary:
        json.dump(headline(rows), sys.stdout, indent=2)
        print()
    elif args.groups:
        print(groups_markdown(headline(rows)))
    elif args.json:
        json.dump(rows, sys.stdout, indent=2)
        print()
    else:
        print(markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
