# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""The organizations behind LSC's Pro Bono Innovation Fund (PBIF) grants,
2014-2025, and how far they overlap with the organizations behind LSC's
Technology Initiative Grants (TIG) in the same years.

    python pbif_grantees.py              # one row per PBIF organization, markdown
    python pbif_grantees.py --summary    # headline figures as JSON
    python pbif_grantees.py --out DIR    # write summary.json, pbif_orgs.json,
                                         # unmatched.md and tig_only.md into DIR

PBIF rows: 2014-2021 from data/pbif_history.json (LSC's releases, one row
per grant); 2022-2025 from the PBIF awards page plus the grants only a
release prints (pbif.combined, as pbif_history.later does). 2020's eight
supplemental grants are unnamed, so 2020 is a partial round: its named
grantees count, but no organization can be said to have missed it.

Match rules, all within the grantee's state, tried in this order:
  named  the name is in data/pbif_names.json (hand-checked spellings, a
         short form and a sourced rename).
  exact  (state, tig_grantees.plain(name)) is a TIG organization or one of
         the names LSC printed for it in a TIG list (data/grantee_names.json
         already joins those).
  loose  after dropping a parenthetical ('LAF (formerly ...)') and a trailing
         'in <City>', pbif.norm(name) equals pbif.norm of exactly one TIG
         organization's name or printed names.
  none   no TIG organization matched: the organization won PBIF only.
Every loose and none row was checked by hand against LSC's own lists
(unmatched.md). Mergers are not followed. PBIF Sustainability grants go only
to current PBIF grantees, so some repeat PBIF wins are by design.
"""
import argparse
import json
import os
import re
import sys

import basic_field
import pbif
import pbif_history
import tig
import tig_grantees

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = os.path.join(HERE, "data", "pbif_names.json")
ROUNDS = tuple(range(2014, 2026))
PARTIAL = (2020,)
PAREN = re.compile(r"\s*\([^)]*\)")
IN_CITY = re.compile(r"\s+in\s+[A-Z][A-Za-z.'-]+$")


def load_names(path=NAMES):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cleaned(name):
    n = PAREN.sub("", name)
    n = IN_CITY.sub("", n)
    return " ".join(n.split())


def pbif_rows():
    """One row per PBIF grant 2014-2025 with year, grantee, state, amount
    and where the row comes from."""
    rows = []
    for r in pbif_history.load()["rounds"]:
        for g in r["grants"]:
            rows.append({"year": r["year"], "grantee": g["grantee"], "state": g["state"],
                         "amount_usd": pbif_history.usd(g["printed"]), "from": "release"})
    areas = basic_field.load(basic_field.DATA)["service_areas"]
    page = pbif.load(pbif.DATA)["awards"]
    releases = pbif.load_releases(pbif.RELEASES)
    by_norm = {pbif.norm(a["grantee"]): a["state"] for a in page if a.get("state")}
    for a in pbif_history.later(page, releases, areas):
        state = a.get("state") or by_norm.get(pbif.norm(a["grantee"]))
        rows.append({"year": a["year"], "grantee": a["grantee"], "state": state,
                     "amount_usd": a["amount_usd"], "track": a.get("track"),
                     "from": "page" if a.get("track") else "release only"})
    return rows


def tig_index():
    names = tig_grantees.load_names()
    orgs = tig_grantees.organizations(tig_grantees.build(names, tig_grantees.KINDS))
    exact, loose = {}, {}
    for o in orgs:
        key = (o["state"], o["organization"])
        for n in list(o["names"]) + [o["organization"]]:
            exact[(o["state"], tig_grantees.plain(n))] = key
            loose.setdefault((o["state"], pbif.norm(cleaned(n))), set()).add(key)
    return orgs, exact, loose


def match(rows, exact, loose, names=None):
    """Set each PBIF row's organization key and the rule that found it."""
    names = load_names() if names is None else names
    named = {(e["state"], e["printed"]): e["organization"] for e in names["names"]}
    for g in rows:
        st, name = g["state"], g["grantee"]
        key, rule = None, "exact"
        org = named.get((st, tig_grantees.plain(name)))
        if org is not None:
            key, rule = exact.get((st, tig_grantees.plain(org)), (st, org)), "named"
        if key is None:
            key = exact.get((st, tig_grantees.plain(name)))
        if key is None:
            found = loose.get((st, pbif.norm(cleaned(name))), set())
            if len(found) == 1:
                key, rule = next(iter(found)), "loose"
        if key is None:
            key, rule = (st, tig_grantees.plain(cleaned(name))), "none"
        g["organization"], g["rule"] = key[1], rule
    return rows


def unused(rows, names):
    """Entries of data/pbif_names.json that match no PBIF grant."""
    seen = {(g["state"], tig_grantees.plain(g["grantee"])) for g in rows}
    return [e for e in names["names"] if (e["state"], e["printed"]) not in seen]


def organizations(rows, tig_orgs):
    tig_by_key = {(o["state"], o["organization"]): o for o in tig_orgs}
    out = {}
    for g in rows:
        key = (g["state"], g["organization"])
        o = out.setdefault(key, {"organization": g["organization"], "state": g["state"], "names": set(),
                                 "rounds": set(), "partial": set(), "grants": 0, "usd": 0.0,
                                 "sustainability": 0, "rules": set()})
        o["names"].add(g["grantee"])
        o["rules"].add(g["rule"])
        o["grants"] += 1
        o["usd"] += g["amount_usd"] or 0
        if g.get("track") == "Sustainability":
            o["sustainability"] += 1
        (o["partial"] if g["year"] in PARTIAL else o["rounds"]).add(g["year"])
    result = []
    for key, o in out.items():
        t = tig_by_key.get(key)
        result.append({
            "organization": o["organization"], "state": o["state"], "names": sorted(o["names"]),
            "rules": sorted(o["rules"]), "pbif_rounds": sorted(o["rounds"]), "pbif_partial": sorted(o["partial"]),
            "pbif_grants": o["grants"], "pbif_usd": round(o["usd"], 2), "pbif_sustainability": o["sustainability"],
            "tig": t is not None,
            "tig_rounds": t["rounds"] if t else [], "tig_partial": t["partial"] if t else [],
            "tig_usd": t["usd"] if t else 0.0,
        })
    result.sort(key=lambda r: (-(len(r["pbif_rounds"]) + len(r["pbif_partial"])), -r["pbif_usd"], r["state"], r["organization"]))
    return result


def headline(orgs, tig_orgs, rows):
    tig_won = [o for o in tig_orgs if o["rounds"]]
    both = [o for o in orgs if o["tig"] and o["tig_rounds"]]
    pbif_keys = {(o["state"], o["organization"]) for o in orgs}
    tig_only = [o for o in tig_won if (o["state"], o["organization"]) not in pbif_keys]
    often = [o for o in tig_won if len(o["rounds"]) >= 5]
    often_pbif = [o for o in often if (o["state"], o["organization"]) in pbif_keys]
    hist = {}
    for o in orgs:
        n = len(o["pbif_rounds"]) + len(o["pbif_partial"])
        hist[n] = hist.get(n, 0) + 1
    rules = {}
    for g in rows:
        rules[g["rule"]] = rules.get(g["rule"], 0) + 1

    def mean_tig_rounds(group):
        return round(sum(len(o["rounds"]) for o in group) / len(group), 2) if group else None

    both_tig = [o for o in tig_won if (o["state"], o["organization"]) in pbif_keys]
    return {
        "pbif_grants": len(rows),
        "pbif_rounds": len(ROUNDS),
        "pbif_partial_rounds": list(PARTIAL),
        "pbif_usd": round(sum(g["amount_usd"] or 0 for g in rows), 2),
        "pbif_organizations": len(orgs),
        "pbif_rounds_won_histogram": {str(k): v for k, v in sorted(hist.items(), reverse=True)},
        "pbif_sustainability_grants_2022_2025": sum(1 for g in rows if g.get("track") == "Sustainability"),
        "match_rules": rules,
        "rows_with_no_state": sum(1 for g in rows if not g["state"]),
        "tig_organizations": len(tig_won),
        "both": len(both),
        "pbif_only": len(orgs) - len(both),
        "tig_only": len(tig_only),
        "share_of_pbif_orgs_with_tig": round(len(both) / len(orgs), 4) if orgs else None,
        "share_of_tig_orgs_with_pbif": round(len(both) / len(tig_won), 4) if tig_won else None,
        "pbif_usd_to_tig_winners": round(sum(o["pbif_usd"] for o in both), 2),
        "tig_usd_to_pbif_winners": round(sum(o["usd"] for o in both_tig), 2),
        "tig_usd_total": round(sum(o["usd"] for o in tig_won), 2),
        "tig_five_or_more": {"organizations": len(often), "with_pbif": len(often_pbif),
                             "names": ["%s (%s)" % (o["organization"], o["state"]) for o in often_pbif]},
        "mean_tig_rounds": {"tig_orgs_with_pbif": mean_tig_rounds(both_tig),
                            "tig_orgs_without_pbif": mean_tig_rounds(tig_only)},
        "most_pbif": [{"organization": o["organization"], "state": o["state"],
                       "pbif_rounds": o["pbif_rounds"], "pbif_partial": o["pbif_partial"],
                       "tig_rounds": len(o["tig_rounds"])}
                      for o in orgs if len(o["pbif_rounds"]) + len(o["pbif_partial"]) >= 3],
    }


def build():
    """PBIF rows matched to TIG organizations, the PBIF organizations, the
    TIG organizations and the headline figures."""
    rows = pbif_rows()
    tig_orgs, exact, loose = tig_index()
    rows = match(rows, exact, loose)
    orgs = organizations(rows, tig_orgs)
    return rows, orgs, tig_orgs, headline(orgs, tig_orgs, rows)


def markdown(orgs):
    lines = ["| Organization | State | PBIF rounds | PBIF years | PBIF dollars | TIG rounds (of 11) | Match | Names LSC printed in PBIF |",
             "|---|---|---|---|---|---|---|---|"]
    for o in orgs:
        years = ", ".join(str(y) for y in sorted(o["pbif_rounds"] + o["pbif_partial"]))
        lines.append("| %s | %s | %d | %s | %s | %s | %s | %s |" % (
            o["organization"], o["state"], len(o["pbif_rounds"]) + len(o["pbif_partial"]), years,
            tig.dollars(o["pbif_usd"]), len(o["tig_rounds"]) if o["tig"] else "-",
            "/".join(o["rules"]), "; ".join(o["names"])))
    return "\n".join(lines)


def review_markdown(orgs, tig_orgs, rows):
    """Every PBIF name matched loosely or not at all, with the TIG
    organizations of the same state, for hand review."""
    by_state = {}
    for o in tig_orgs:
        by_state.setdefault(o["state"], []).append("%s [%s]" % (o["organization"], "; ".join(sorted(o["names"]))))
    lines = ["# PBIF names to hand-check", "", "| Rule | State | PBIF name as printed | Years | Taken as | TIG organizations in that state [names printed] |",
             "|---|---|---|---|---|---|"]
    seen = set()
    for g in rows:
        if g["rule"] in ("exact", "named"):
            continue
        k = (g["state"], g["grantee"])
        if k in seen:
            continue
        seen.add(k)
        years = sorted(r["year"] for r in rows if (r["state"], r["grantee"]) == k)
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            g["rule"], g["state"], g["grantee"], ", ".join(str(y) for y in years), g["organization"],
            "<br>".join(by_state.get(g["state"], [])) or "-"))
    return "\n".join(lines)


def tig_only_markdown(orgs, tig_orgs):
    pbif_keys = {(o["state"], o["organization"]) for o in orgs}
    lines = ["# TIG organizations with no PBIF grant matched", "", "| Organization | State | TIG rounds | Names printed |", "|---|---|---|---|"]
    for o in tig_orgs:
        if not o["rounds"] or (o["state"], o["organization"]) in pbif_keys:
            continue
        lines.append("| %s | %s | %d | %s |" % (o["organization"], o["state"], len(o["rounds"]), "; ".join(sorted(o["names"]))))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    p.add_argument("--out", metavar="DIR", help="write summary.json, pbif_orgs.json, unmatched.md, tig_only.md")
    args = p.parse_args(argv)

    rows, orgs, tig_orgs, head = build()

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(head, f, indent=2)
        with open(os.path.join(args.out, "pbif_orgs.json"), "w", encoding="utf-8") as f:
            json.dump(orgs, f, indent=2)
        with open(os.path.join(args.out, "pbif_rows.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)
        with open(os.path.join(args.out, "unmatched.md"), "w", encoding="utf-8") as f:
            f.write(review_markdown(orgs, tig_orgs, rows) + "\n")
        with open(os.path.join(args.out, "tig_only.md"), "w", encoding="utf-8") as f:
            f.write(tig_only_markdown(orgs, tig_orgs) + "\n")
        with open(os.path.join(args.out, "pbif_orgs.md"), "w", encoding="utf-8") as f:
            f.write(markdown(orgs) + "\n")
        print("wrote", args.out)
    if args.summary or args.out:
        json.dump(head, sys.stdout, indent=2)
        print()
    else:
        print(markdown(orgs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
