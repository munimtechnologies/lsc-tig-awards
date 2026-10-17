# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Technology Initiative Grant (TIG) rounds 2014 and 2015: the 2014 list
(a PDF still on lsc.gov, one row per grantee) summed and set against LSC's
releases and its own counts; the 2015 round, for which LSC never printed a
list, assembled from the grants its releases name; and LSC's cumulative
"since 2000" figures checked across the two releases.

    python tig_2014_2015.py              # each round's rows, sums and stated totals
    python tig_2014_2015.py --sources    # each release's amounts, parts and group totals
    python tig_2014_2015.py --headlines  # LSC's statements and cumulative figures
    python tig_2014_2015.py --summary    # headline figures as JSON
"""
import argparse
import json
import os
import sys

import tig
import tig_history

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "tig_2014_2015.json")
SOURCES = {"release": "release", "local": "local releases", "bundle": "per-grantee release",
           "pbif_bundle": "PBIF per-grantee release", "event": "event release"}
ORDER = ("release", "local", "bundle", "pbif_bundle", "event")
LIST_KIND = {"pdf": "PDF on lsc.gov", "none": "none (releases only)"}
COUNTS = ("projects", "organizations", "places", "grants")
usd = tig_history.usd


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def complete(rnd):
    """Whether LSC printed a full list for the round."""
    return rnd["list"]["kind"] != "none"


def label(rnd, source):
    if source == "list":
        return "PDF list" if complete(rnd) else "list page (archived)"
    return SOURCES[source]


def by_id(rnd):
    return {g["id"]: g for g in rnd["grantees"]}


def listed(rnd):
    """Grantee rows, organizations (distinct printed names), states (with DC),
    territories, and the least number of grants the rows can hold (a row
    with no grant count counts as one grant)."""
    places = {g["state"] for g in rnd["grantees"]}
    territories = places & set(tig_history.TERRITORIES)
    return {"grantees": len(rnd["grantees"]),
            "organizations": len({g["grantee"] for g in rnd["grantees"]}),
            "states": len(places - territories), "territories": len(territories),
            "grants_at_least": sum(g["grants"] or 1 for g in rnd["grantees"])}


def totals(history):
    """One row per round: the rows' sum against the list's stated total, and
    how many grantees have an amount in a release still on lsc.gov."""
    rows = []
    for r in history["rounds"]:
        got = listed(r)
        total = sum(usd(g["printed"]) for g in r["grantees"])
        stated = usd(r["list"]["stated_total"]) if r["list"]["stated_total"] else None
        on_site = set()
        for amounts in r["amounts"].values():
            on_site |= set(amounts)
        rows.append(dict(got, year=r["year"], complete=complete(r), list=LIST_KIND[r["list"]["kind"]],
                         sum_usd=total, stated_usd=stated,
                         difference=None if stated is None else total - stated,
                         stated_organizations=r["stated"]["organizations"],
                         stated_grants=r["stated"]["grants"] or r["stated"]["projects"],
                         on_lsc_today=len(on_site)))
    return rows


def sources(history):
    """One row per round and release: how many amounts it prints for single
    grantees, how many equal the dataset's amount (the list's for 2014, the
    first release's for 2015), and which differ."""
    rows = []
    for r in history["rounds"]:
        grantees = by_id(r)
        for source in ORDER:
            if source not in r["amounts"]:
                continue
            got = r["amounts"][source]
            differ = [{"id": i, "grantee": grantees[i]["grantee"], "source_usd": usd(p),
                       "list_usd": usd(grantees[i]["printed"])}
                      for i, p in got.items() if p != grantees[i]["printed"]]
            rows.append({"year": r["year"], "source": source, "url": r["sources"][source],
                         "printed": len(got), "same": len(got) - len(differ), "differ": differ})
    return rows


def parts(history):
    """Each set of parts a release prints for one grantee, and each total it
    states for a group of grantees, against the dataset's amounts."""
    rows = []
    for r in history["rounds"]:
        grantees = by_id(r)
        for p in r["parts"]:
            total = sum(usd(x) for x in p["printed"])
            stated = usd(grantees[p["id"]]["printed"])
            rows.append({"year": r["year"], "source": p["source"], "grantee": grantees[p["id"]]["grantee"],
                         "stated_usd": stated, "parts_usd": [usd(x) for x in p["printed"]],
                         "sum_usd": total, "difference": stated - total})
        for t in r["group_totals"]:
            total = sum(usd(grantees[i]["printed"]) for i in t["ids"])
            stated = usd(t["printed"])
            rows.append({"year": r["year"], "source": t["source"], "grantee": t["label"],
                         "stated_usd": stated, "parts_usd": [usd(grantees[i]["printed"]) for i in t["ids"]],
                         "sum_usd": total, "difference": stated - total})
    return rows


def fits(rule, total):
    """Whether a dollar total meets a statement's rule; None if no rule or no total."""
    if not rule or total is None:
        return None
    (kind, x), = rule.items()
    if kind == "exactly":
        return total == x
    if kind == "more_than":
        return total > x
    if kind == "nearly":
        return total < x
    raise ValueError(kind)


def statements(history):
    """Each of LSC's statements: which of its counts miss the list, which
    cannot be checked (a per-grantee list cannot count projects; an
    incomplete round checks nothing), and whether its dollar figure fits."""
    by_year = {t["year"]: t for t in totals(history)}
    rows = []
    for r in history["rounds"]:
        got = listed(r)
        t = by_year[r["year"]]
        for s in r["statements"]:
            stated = {k: s.get(k) for k in COUNTS if s.get(k) is not None}
            wrong, unchecked = [], []
            for k, n in stated.items():
                if not complete(r) or k in ("projects", "grants"):
                    unchecked.append(k)
                elif k == "places":
                    if n != got["states"] + got["territories"]:
                        wrong.append(k)
                elif n != got[k]:
                    wrong.append(k)
            rows.append({"year": r["year"], "source": s["source"], "quote": s["quote"], "stated": stated,
                         "usd": s["usd"], "wrong": wrong, "unchecked": unchecked,
                         "fits": fits(s["usd"], t["sum_usd"]) if complete(r) else None})
    return rows


def cumulative(history):
    """LSC's 'since 2000' figures: the 2014 release's count and dollars, plus
    the two rounds as LSC states them, against the 2015 release's figures."""
    first, second = history["rounds"]
    before = first["cumulative"]
    after = second["cumulative"]
    added = [first["stated"]["projects"], second["stated"]["grants"]]
    (_, usd_before), = before["usd"].items()
    (_, usd_after), = after["usd"].items()
    round_usd = [usd(first["list"]["stated_total"]), 4200000]
    return {"before_grants": before["grants"], "before_usd_more_than": usd_before,
            "added_grants": added, "added_usd_at_least": round_usd,
            "implied_grants": before["grants"] + sum(added),
            "implied_usd_at_least": usd_before + sum(round_usd),
            "after_grants": after["grants"], "after_usd_more_than": usd_after,
            "grants_fit": before["grants"] + sum(added) == after["grants"],
            "usd_fit": usd_after < usd_before + sum(round_usd) < usd_after + 1000000}


def says(s):
    words = {"projects": "projects", "organizations": "organizations",
             "places": "states and territories", "grants": "grants"}
    out = ["%d %s" % (n, words[k]) for k, n in s["stated"].items()]
    if s["usd"]:
        (kind, x), = s["usd"].items()
        out.append("%s %s" % (kind.replace("_", " "), tig.dollars(x)))
    return ", ".join(out)


def yes_no(x):
    return "-" if x is None else ("yes" if x else "no")


def totals_markdown(rows):
    lines = ["| Year | List | Grantee rows | Organizations | States | Territories | Grants (at least) | Sum of the amounts | LSC's stated total | Difference | Grantees with an amount on lsc.gov today |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %s | %d | %d | %d | %d | %d | %s | %s | %s | %d |" % (
            r["year"], r["list"], r["grantees"], r["organizations"], r["states"], r["territories"],
            r["grants_at_least"], tig.dollars(r["sum_usd"]),
            tig.dollars(r["stated_usd"]) if r["stated_usd"] is not None else "-",
            tig_history.signed(r["difference"]) if r["difference"] is not None else "-", r["on_lsc_today"]))
    return "\n".join(lines)


def sources_markdown(rows):
    lines = ["| Year | LSC release | Amounts printed | Same | Different |", "|---|---|---|---|---|"]
    for r in rows:
        differ = "; ".join("%s %s: %s vs %s" % (d["id"], d["grantee"], tig.dollars(d["source_usd"]),
                                                tig.dollars(d["list_usd"])) for d in r["differ"])
        lines.append("| %d | [%s](%s) | %d | %d | %s |" % (
            r["year"], SOURCES[r["source"]], r["url"], r["printed"], r["same"], differ or "none"))
    return "\n".join(lines)


def parts_markdown(rows):
    lines = ["| Year | Source | Grantee | Stated | Parts | Sum of the parts | Difference |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %s | %s | %s | %s | %s | %s |" % (
            r["year"], SOURCES[r["source"]], r["grantee"], tig.dollars(r["stated_usd"]),
            " + ".join(tig.dollars(x) for x in r["parts_usd"]), tig.dollars(r["sum_usd"]),
            tig_history.signed(r["difference"])))
    return "\n".join(lines)


def statements_markdown(history, rows):
    rounds = {r["year"]: r for r in history["rounds"]}
    lines = ["| Year | Source | LSC says | Counts that miss the list | Not checkable | Dollar figure fits the sum |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %s | %s | %s | %s | %s |" % (
            r["year"], label(rounds[r["year"]], r["source"]), says(r),
            "-" if not complete(rounds[r["year"]]) else (", ".join(r["wrong"]) or "none"),
            ", ".join(r["unchecked"]) or "none", yes_no(r["fits"])))
    return "\n".join(lines)


def cumulative_markdown(c):
    return "\n".join([
        "| | Grants | Dollars |", "|---|---|---|",
        "| Cumulative stated in the 2014 release | %d | more than %s |" % (c["before_grants"], tig.dollars(c["before_usd_more_than"])),
        "| 2014 round, as LSC states it | %d | %s |" % (c["added_grants"][0], tig.dollars(c["added_usd_at_least"][0])),
        "| 2015 round, as LSC states it | %d | more than %s |" % (c["added_grants"][1], tig.dollars(c["added_usd_at_least"][1])),
        "| Sum of those three | %d | more than %s |" % (c["implied_grants"], tig.dollars(c["implied_usd_at_least"])),
        "| Cumulative stated in the 2015 release | %d | more than %s |" % (c["after_grants"], tig.dollars(c["after_usd_more_than"])),
    ])


def summary(history):
    return {
        "totals": totals(history),
        "sources": [{k: r[k] for k in ("year", "source", "printed", "same", "differ")} for r in sources(history)],
        "parts_differ": [r for r in parts(history) if r["difference"]],
        "statements_missing_counts": [{k: r[k] for k in ("year", "source", "quote", "wrong")}
                                      for r in statements(history) if r["wrong"]],
        "statements_dollars": [{k: r[k] for k in ("year", "source", "usd", "fits")}
                               for r in statements(history) if r["usd"]],
        "cumulative": cumulative(history),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--sources", action="store_true", help="each release's amounts, parts and group totals")
    p.add_argument("--headlines", action="store_true", help="LSC's statements and cumulative figures")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    history = load(args.data)
    if args.sources:
        print(sources_markdown(sources(history)))
        print()
        print(parts_markdown(parts(history)))
    elif args.headlines:
        print(statements_markdown(history, statements(history)))
        print()
        print(cumulative_markdown(cumulative(history)))
    elif args.summary:
        json.dump(summary(history), sys.stdout, indent=2)
        print()
    else:
        print(totals_markdown(totals(history)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
