# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC's basic field grantees as the base for its two competitive programs:
how many organizations hold an LSC basic field grant for 2025, and how many
of them won a Technology Initiative Grant (TIG), a Pro Bono Innovation Fund
(PBIF) grant, both, or neither in 2014-2025.

    python grantee_base.py             # one row per 2025 grantee, markdown
    python grantee_base.py --summary   # headline figures as JSON
    python grantee_base.py --out DIR   # write summary.json, grantees.json,
                                       # grantees.md and unmatched.md into DIR

Grantees come from data/basic_field_2025.json (LSC's Notice of Intent to
Award for 2025, one row per service area). Rows that print the same name
are one organization. Its home state is the state of the service areas that
hold most of its basic field dollars: DNA-People's Legal Services serves
Arizona and New Mexico areas and counts in Arizona, as the TIG lists print
it; Micronesian Legal Services Corporation counts in the Northern Mariana
Islands. A row naming two possible grantees ('A or B') is an undecided
award: it is kept apart and is no organization.

Match rules, tried in this order within the home state:
  exact    (state, tig_grantees.plain(name)) is a TIG or PBIF organization
           or one of the names LSC printed for it (data/grantee_names.json
           and data/pbif_names.json already join those).
  loose    pbif.norm of the name, after pbif_grantees.cleaned, equals that
           of exactly one organization's names.
  none     no organization matched.
  via_tig  (PBIF only) the grantee's TIG organization is also a PBIF
           organization, as pbif_grantees.py already joined them.
A TIG organization counts as a winner when it won a complete round (2015
has no list); a PBIF organization when LSC named it in any round. TIG and
PBIF organizations that match no 2025 grantee are listed for hand review
(unmatched.md): an organization that lost or gave up its basic field grant,
merged, or is printed under a name these rules do not join. Both programs
are open only to LSC grantees, so this is the base rate the TIG and PBIF
overlap counts should be read against. Mergers are not followed.
"""
import argparse
import json
import os
import statistics
import sys

import basic_field
import pbif
import pbif_grantees
import tig
import tig_grantees

OR = " or "
GROUPS = ("both", "tig_only", "pbif_only", "neither")
# Basic field dollars for 2025, lower bound inclusive, upper exclusive.
TIERS = (("under $1M", 0, 1000000), ("$1M to $3M", 1000000, 3000000),
         ("$3M to $6M", 3000000, 6000000), ("$6M and over", 6000000, None))


def grantees(areas):
    """One row per 2025 basic field grantee, and the undecided rows."""
    by_name, undecided = {}, []
    for r in areas:
        if OR in r["grantee"]:
            undecided.append({"printed": r["grantee"], "state": r["state"],
                              "service_area": r["service_area"], "amount_usd": r["amount_usd"],
                              "candidates": [tig_grantees.plain(c) for c in r["grantee"].split(OR)]})
            continue
        name = tig_grantees.plain(r["grantee"])
        o = by_name.setdefault(name, {"names": set(), "areas": [], "usd_by_state": {}})
        o["names"].add(r["grantee"])
        o["areas"].append(r["service_area"])
        o["usd_by_state"][r["state"]] = o["usd_by_state"].get(r["state"], 0) + r["amount_usd"]
    rows = []
    for name, o in by_name.items():
        state = max(sorted(o["usd_by_state"]), key=lambda s: o["usd_by_state"][s])
        rows.append({"organization": name, "state": state, "names": sorted(o["names"]),
                     "service_areas": sorted(o["areas"]), "states": sorted(o["usd_by_state"]),
                     "basic_field_usd": sum(o["usd_by_state"].values())})
    rows.sort(key=lambda r: (-r["basic_field_usd"], r["state"], r["organization"]))
    return rows, undecided


def index(orgs):
    """exact and loose lookups from (state, name) to an organization's key,
    over the organization's name and every name LSC printed for it."""
    exact, loose = {}, {}
    for o in orgs:
        key = (o["state"], o["organization"])
        for n in list(o["names"]) + [o["organization"]]:
            exact[(o["state"], tig_grantees.plain(n))] = key
            loose.setdefault((o["state"], pbif.norm(pbif_grantees.cleaned(n))), set()).add(key)
    return exact, loose


def find(state, name, exact, loose):
    key = exact.get((state, tig_grantees.plain(name)))
    if key is not None:
        return key, "exact"
    found = loose.get((state, pbif.norm(pbif_grantees.cleaned(name))), set())
    if len(found) == 1:
        return next(iter(found)), "loose"
    return None, "none"


def match(rows, tig_orgs, pbif_orgs):
    """Set each grantee's TIG and PBIF organization (or None), the rule that
    found each, its rounds, and its group."""
    tig_won = [o for o in tig_orgs if o["rounds"]]
    t_exact, t_loose = index(tig_won)
    p_exact, p_loose = index(pbif_orgs)
    tig_by_key = {(o["state"], o["organization"]): o for o in tig_won}
    pbif_by_key = {(o["state"], o["organization"]): o for o in pbif_orgs}
    for g in rows:
        tk, tr = find(g["state"], g["organization"], t_exact, t_loose)
        if tk in pbif_by_key:
            pk, pr = tk, "via_tig"
        else:
            pk, pr = find(g["state"], g["organization"], p_exact, p_loose)
        t = tig_by_key.get(tk) if tk else None
        p = pbif_by_key.get(pk) if pk else None
        g["tig_organization"], g["tig_rule"] = (tk[1] if tk else None), tr
        g["tig_rounds"] = t["rounds"] if t else []
        g["tig_partial"] = t["partial"] if t else []
        g["tig_usd"] = t["usd"] if t else 0.0
        g["pbif_organization"], g["pbif_rule"] = (pk[1] if pk else None), pr
        g["pbif_rounds"] = sorted(p["pbif_rounds"] + p["pbif_partial"]) if p else []
        g["pbif_usd"] = p["pbif_usd"] if p else 0.0
        won_t, won_p = bool(g["tig_rounds"]), bool(g["pbif_rounds"])
        g["group"] = "both" if won_t and won_p else "tig_only" if won_t else "pbif_only" if won_p else "neither"
    return rows


def unmatched(rows, tig_orgs, pbif_orgs):
    """TIG and PBIF organizations no 2025 grantee matched, and any
    organization two grantees matched."""
    t_hit, p_hit = {}, {}
    for g in rows:
        if g["tig_organization"]:
            t_hit.setdefault((g["state"], g["tig_organization"]), []).append(g["organization"])
        if g["pbif_organization"]:
            p_hit.setdefault((g["state"], g["pbif_organization"]), []).append(g["organization"])
    tig_won = [o for o in tig_orgs if o["rounds"]]
    return {
        "tig": [o for o in tig_won if (o["state"], o["organization"]) not in t_hit],
        "pbif": [o for o in pbif_orgs if (o["state"], o["organization"]) not in p_hit],
        "double": {"%s (%s)" % (k[1], k[0]): v for k, v in list(t_hit.items()) + list(p_hit.items()) if len(v) > 1},
    }


def tier_of(usd):
    for label, low, high in TIERS:
        if usd >= low and (high is None or usd < high):
            return label
    raise ValueError(usd)


def headline(rows, undecided, tig_orgs, pbif_orgs):
    miss = unmatched(rows, tig_orgs, pbif_orgs)
    tig_won = [o for o in tig_orgs if o["rounds"]]
    total = sum(r["basic_field_usd"] for r in rows)
    n = len(rows)

    def group(rs):
        usd = sum(r["basic_field_usd"] for r in rs)
        return {"grantees": len(rs), "share_of_grantees": round(len(rs) / n, 4),
                "basic_field_usd": usd, "share_of_basic_field_usd": round(usd / total, 4),
                "median_basic_field_usd": int(statistics.median(r["basic_field_usd"] for r in rs)) if rs else None,
                "states": sorted({r["state"] for r in rs})}

    groups = {g: group([r for r in rows if r["group"] == g]) for g in GROUPS}
    tiers = []
    for label, low, high in TIERS:
        rs = [r for r in rows if tier_of(r["basic_field_usd"]) == label]
        tiers.append({"tier": label, "grantees": len(rs),
                      "won_tig": sum(1 for r in rs if r["tig_rounds"]),
                      "won_pbif": sum(1 for r in rs if r["pbif_rounds"]),
                      "won_both": sum(1 for r in rs if r["group"] == "both"),
                      "neither": sum(1 for r in rs if r["group"] == "neither"),
                      "share_won_either": round(sum(1 for r in rs if r["group"] != "neither") / len(rs), 4) if rs else None})
    rules = {}
    for which in ("tig", "pbif"):
        for g in rows:
            k = "%s_%s" % (which, g[which + "_rule"])
            rules[k] = rules.get(k, 0) + 1
    matched_tig_rounds = sum(len(r["tig_rounds"]) for r in rows)
    all_tig_rounds = sum(len(o["rounds"]) for o in tig_won)
    matched_pbif_usd = round(sum(r["pbif_usd"] for r in rows), 2)
    all_pbif_usd = round(sum(o["pbif_usd"] for o in pbif_orgs), 2)
    return {
        "grantees": n,
        "service_area_rows": sum(len(r["service_areas"]) for r in rows) + len(undecided),
        "basic_field_usd": total,
        "undecided": undecided,
        "undecided_usd": sum(u["amount_usd"] for u in undecided),
        "multi_state_grantees": ["%s (%s)" % (r["organization"], ", ".join(r["states"])) for r in rows if len(r["states"]) > 1],
        "tig_organizations": len(tig_won),
        "tig_organizations_matched": len(tig_won) - len(miss["tig"]),
        "tig_organizations_unmatched": ["%s (%s, %d rounds)" % (o["organization"], o["state"], len(o["rounds"])) for o in miss["tig"]],
        "tig_round_wins": all_tig_rounds,
        "tig_round_wins_by_2025_grantees": matched_tig_rounds,
        "tig_usd_by_2025_grantees": round(sum(r["tig_usd"] for r in rows), 2),
        "tig_usd_total": round(sum(o["usd"] for o in tig_won), 2),
        "pbif_organizations": len(pbif_orgs),
        "pbif_organizations_matched": len(pbif_orgs) - len(miss["pbif"]),
        "pbif_organizations_unmatched": ["%s (%s)" % (o["organization"], o["state"]) for o in miss["pbif"]],
        "pbif_usd_by_2025_grantees": matched_pbif_usd,
        "pbif_usd_total": all_pbif_usd,
        "double_matched": miss["double"],
        "match_rules": rules,
        "groups": groups,
        "won_either": {"grantees": n - groups["neither"]["grantees"],
                       "share_of_grantees": round((n - groups["neither"]["grantees"]) / n, 4)},
        "tiers": tiers,
        "largest_neither": max((r["basic_field_usd"] for r in rows if r["group"] == "neither"), default=None),
        "smallest_both": min((r["basic_field_usd"] for r in rows if r["group"] == "both"), default=None),
        "neither": [{"organization": r["organization"], "state": r["state"], "basic_field_usd": r["basic_field_usd"],
                     "service_areas": r["service_areas"]} for r in rows if r["group"] == "neither"],
    }


def build():
    """The 2025 grantees matched to TIG and PBIF organizations, the undecided
    rows, the TIG and PBIF organizations, and the headline figures."""
    areas = basic_field.load(basic_field.DATA)["service_areas"]
    rows, undecided = grantees(areas)
    tig_orgs = tig_grantees.organizations(tig_grantees.build(tig_grantees.load_names(), tig_grantees.KINDS))
    pbif_orgs = pbif_grantees.build()[1]
    rows = match(rows, tig_orgs, pbif_orgs)
    return rows, undecided, tig_orgs, pbif_orgs, headline(rows, undecided, tig_orgs, pbif_orgs)


def markdown(rows):
    lines = ["| Organization | State | Basic field 2025 | Service areas | TIG rounds (of 11) | PBIF rounds (of 12) | Won |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["organization"], r["state"], tig.dollars(r["basic_field_usd"]), ", ".join(r["service_areas"]),
            len(r["tig_rounds"]) or "-", len(r["pbif_rounds"]) or "-", r["group"].replace("_", " ")))
    return "\n".join(lines)


def review_markdown(rows, undecided, tig_orgs, pbif_orgs):
    miss = unmatched(rows, tig_orgs, pbif_orgs)
    lines = ["# 2025 grantee base: rows to hand-check", "",
             "## TIG organizations no 2025 grantee matched", "",
             "| Organization | State | TIG rounds | Names printed |", "|---|---|---|---|"]
    for o in miss["tig"]:
        lines.append("| %s | %s | %d | %s |" % (o["organization"], o["state"], len(o["rounds"]), "; ".join(sorted(o["names"]))))
    lines += ["", "## PBIF organizations no 2025 grantee matched", "",
              "| Organization | State | PBIF rounds | Names printed |", "|---|---|---|---|"]
    for o in miss["pbif"]:
        lines.append("| %s | %s | %d | %s |" % (o["organization"], o["state"], len(o["pbif_rounds"]) + len(o["pbif_partial"]), "; ".join(o["names"])))
    lines += ["", "## Organizations two grantees matched", ""]
    lines += ["- %s: %s" % (k, "; ".join(v)) for k, v in miss["double"].items()] or ["- none"]
    lines += ["", "## Grantees matched loosely", "", "| Grantee | State | Program | Taken as |", "|---|---|---|---|"]
    for g in rows:
        for which in ("tig", "pbif"):
            if g[which + "_rule"] == "loose":
                lines.append("| %s | %s | %s | %s |" % (g["organization"], g["state"], which.upper(), g[which + "_organization"]))
    lines += ["", "## Undecided rows", ""]
    lines += ["- %s %s: %s (%s)" % (u["state"], u["service_area"], u["printed"], tig.dollars(u["amount_usd"])) for u in undecided] or ["- none"]
    lines += ["", "## Grantees with service areas in more than one state", ""]
    lines += ["- %s: %s" % (r["organization"], ", ".join(r["service_areas"])) for r in rows if len(r["states"]) > 1] or ["- none"]
    lines += ["", "## Grantees that won neither program", "", "| Organization | State | Basic field 2025 | Service areas |", "|---|---|---|---|"]
    for r in rows:
        if r["group"] == "neither":
            lines.append("| %s | %s | %s | %s |" % (r["organization"], r["state"], tig.dollars(r["basic_field_usd"]), ", ".join(r["service_areas"])))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    p.add_argument("--out", metavar="DIR", help="write summary.json, grantees.json, grantees.md, unmatched.md")
    args = p.parse_args(argv)

    rows, undecided, tig_orgs, pbif_orgs, head = build()

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(head, f, indent=2)
        with open(os.path.join(args.out, "grantees.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)
        with open(os.path.join(args.out, "grantees.md"), "w", encoding="utf-8") as f:
            f.write(markdown(rows) + "\n")
        with open(os.path.join(args.out, "unmatched.md"), "w", encoding="utf-8") as f:
            f.write(review_markdown(rows, undecided, tig_orgs, pbif_orgs) + "\n")
        print("wrote", args.out)
    if args.summary or args.out:
        json.dump(head, sys.stdout, indent=2)
        print()
    else:
        print(markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
