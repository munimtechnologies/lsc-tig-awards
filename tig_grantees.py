# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""The organizations behind LSC's Technology Initiative Grants (TIG),
2014-2025: how many complete rounds each won, and how many of each round's
organizations were new since 2014.

    python tig_grantees.py            # one row per organization, most rounds first
    python tig_grantees.py --rounds   # organizations and newcomers per round
    python tig_grantees.py --summary  # headline figures as JSON
    python tig_grantees.py --json     # the rows as JSON

The grants are the lists tig_states.py uses (one row per grantee for 2014),
plus the grants data/awards.json lists with no published amount: they count
as a round won, not as dollars. LSC never printed a 2015 list, so 2015 is in
no count; the organizations its releases name are under `partial`. Names that
differ only by a leading 'The' or a trailing 'Inc.' are one organization, and
so are the names data/grantee_names.json pairs (spellings, a short form and
renames). Each organization goes by the name LSC printed in its latest round.
Mergers between grantees are not followed: two grantees that later merged
count as two.
"""
import argparse
import json
import os
import sys

import tig
import tig_states

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = os.path.join(HERE, "data", "grantee_names.json")
KINDS = ("spelling", "short_form", "renamed")
COMPLETE = tuple(y for y in tig_states.YEARS if y not in tig_states.PARTIAL)
EARLY, LATE = tig_states.PERIODS["2014-2019"], tig_states.PERIODS["2020-2025"]


def load_names(path=NAMES):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def plain(name):
    """The name with runs of spaces made single and without a leading 'The'
    or a trailing 'Inc.'."""
    n = " ".join(name.split())
    if n.startswith("The "):
        n = n[4:]
    for tail in (", Inc.", ", Inc", " Inc."):
        if n.endswith(tail):
            n = n[:-len(tail)]
    return n


def build(names=None, kinds=KINDS, awards_path=tig.DATA):
    """One row per grant with its year, grantee, state, amount (None where LSC
    published none) and organization. Only entries of data/grantee_names.json
    whose kind is in `kinds` join names."""
    names = load_names() if names is None else names
    to = {(e["state"], e["printed"]): e["organization"] for e in names["names"] if e["kind"] in kinds}
    rows = tig_states.build(awards_path=awards_path)
    rows += [{"year": a["year"], "grantee": a["grantee"], "state": a["state"], "amount_usd": None}
             for a in tig.load(awards_path)["awards"] if a["amount_usd"] is None]
    for g in rows:
        p = plain(g["grantee"])
        g["organization"] = to.get((g["state"], p), p)
    return rows


def unused(rows, names):
    """Entries of data/grantee_names.json that match no grant."""
    seen = {(g["state"], plain(g["grantee"])) for g in rows}
    return [e for e in names["names"] if (e["state"], e["printed"]) not in seen]


def organizations(rows):
    """One row per organization: the complete rounds it won and missed, the
    names LSC printed for it, and its TIG dollars in complete rounds."""
    out = {}
    for g in rows:
        o = out.setdefault((g["state"], g["organization"]), {"names": set(), "rounds": set(), "partial": set(), "usd": 0})
        o["names"].add(g["grantee"])
        if g["year"] in tig_states.PARTIAL:
            o["partial"].add(g["year"])
            continue
        o["rounds"].add(g["year"])
        if g["amount_usd"] is not None:
            o["usd"] += g["amount_usd"]
    rows = [{"organization": org, "state": state, "names": sorted(o["names"]), "rounds": sorted(o["rounds"]),
             "missed": [y for y in COMPLETE if y not in o["rounds"]], "partial": sorted(o["partial"]),
             "usd": round(o["usd"], 2)} for (state, org), o in out.items()]
    rows.sort(key=lambda r: (-len(r["rounds"]), -r["usd"], r["state"], r["organization"]))
    return rows


def by_round(orgs):
    """For each complete round, its organizations and how many of them had
    won no earlier complete round since 2014 (all of 2014's, by construction)."""
    out = {}
    for y in COMPLETE:
        won = [o for o in orgs if y in o["rounds"]]
        out[str(y)] = {"organizations": len(won), "new": sum(1 for o in won if o["rounds"][0] == y)}
    return out


def headline(orgs, names_count=None):
    orgs = [o for o in orgs if o["rounds"]]
    hist = {}
    for o in orgs:
        h = hist.setdefault(len(o["rounds"]), {"organizations": 0, "usd": 0})
        h["organizations"] += 1
        h["usd"] += o["usd"]
    periods = {}
    for label, span in (("2014-2019", EARLY), ("2020-2025", LATE)):
        won = [o for o in orgs if any(y in span for y in o["rounds"])]
        periods[label] = {"organizations": len(won),
                          "round_wins": sum(1 for o in won for y in o["rounds"] if y in span)}
    periods["both"] = sum(1 for o in orgs if any(y in EARLY for y in o["rounds"]) and any(y in LATE for y in o["rounds"]))
    often = [o for o in orgs if len(o["rounds"]) >= 5]
    return {
        "complete_rounds": len(COMPLETE),
        "organizations": len(orgs),
        "names": names_count,
        "round_wins": sum(len(o["rounds"]) for o in orgs),
        "usd": round(sum(o["usd"] for o in orgs), 2),
        "rounds_won": {str(k): {"organizations": h["organizations"], "usd": round(h["usd"], 2)}
                       for k, h in sorted(hist.items(), reverse=True)},
        "five_or_more": {"organizations": len(often), "round_wins": sum(len(o["rounds"]) for o in often)},
        "periods": periods,
        "rounds": by_round(orgs),
        "most": [{"organization": o["organization"], "state": o["state"], "rounds": len(o["rounds"]),
                  "missed": o["missed"]} for o in orgs if len(o["rounds"]) >= 6],
        "partial": sorted("%s (%s)" % (o["organization"], o["state"]) for o in orgs if o["partial"]),
    }


def summary(names=None, awards_path=tig.DATA):
    """headline() with `names`: the count of organizations when only
    spellings are joined (no short form, no rename)."""
    names = load_names() if names is None else names
    by_name = [o for o in organizations(build(names, ("spelling",), awards_path)) if o["rounds"]]
    return headline(organizations(build(names, KINDS, awards_path)), len(by_name))


def markdown(orgs):
    lines = ["| Organization | State | Rounds won (of %d) | Rounds | TIG dollars, complete rounds | Other names LSC printed |" % len(COMPLETE),
             "|---|---|---|---|---|---|"]
    for o in orgs:
        if not o["rounds"]:
            continue
        other = sorted({plain(n) for n in o["names"]} - {o["organization"]})
        lines.append("| %s | %s | %d | %s | %s | %s |" % (
            o["organization"], o["state"], len(o["rounds"]), ", ".join(str(y) for y in o["rounds"]),
            tig.dollars(o["usd"]), "; ".join(other) or "-"))
    return "\n".join(lines)


def rounds_markdown(orgs):
    lines = ["| Round | Organizations | New since 2014 |", "|---|---|---|"]
    for y, r in by_round(orgs).items():
        lines.append("| %s | %d | %d |" % (y, r["organizations"], r["new"]))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--names", default=NAMES)
    p.add_argument("--awards", default=tig.DATA)
    p.add_argument("--rounds", action="store_true", help="print organizations and newcomers per round")
    p.add_argument("--json", action="store_true", help="print the rows as JSON")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    names = load_names(args.names)
    orgs = organizations(build(names, KINDS, args.awards))
    if args.summary:
        json.dump(summary(names, args.awards), sys.stdout, indent=2)
        print()
    elif args.json:
        json.dump(orgs, sys.stdout, indent=2)
        print()
    elif args.rounds:
        print(rounds_markdown(orgs))
    else:
        print(markdown(orgs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
