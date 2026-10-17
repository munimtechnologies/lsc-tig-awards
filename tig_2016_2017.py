# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Technology Initiative Grant (TIG) rounds 2016 and 2017 from LSC's
per-year description pages (archived copies: their lsc.gov addresses now open
the TIG index page) and the press releases still on lsc.gov, each list summed
and set against LSC's own counts and dollar figures.

    python tig_2016_2017.py              # list sums, with gaps filled from LSC's releases
    python tig_2016_2017.py --sources    # each release's amounts against the page
    python tig_2016_2017.py --headlines  # LSC's statements against the lists
    python tig_2016_2017.py --summary    # headline figures as JSON
"""
import argparse
import json
import os
import sys

import tig
import tig_history

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "tig_2016_2017.json")
SOURCES = {"page": "description page (archived)", "release": "release",
           "bundle": "per-grantee release", "pbif_bundle": "PBIF per-grantee release"}
ORDER = ("release", "bundle", "pbif_bundle")


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def filled(rnd):
    """Each grant's amount and where it comes from: the page's, or where the
    page prints none, the first LSC release that does."""
    out = {}
    for g in rnd["grants"]:
        if g["printed"]:
            out[g["tig"]] = (tig_history.usd(g["printed"]), "page")
            continue
        for source in ORDER:
            if g["tig"] in rnd["amounts"].get(source, {}):
                out[g["tig"]] = (tig_history.usd(rnd["amounts"][source][g["tig"]]), source)
                break
    return out


def totals(history):
    """One row per round: the page's list sum, the sum with gaps filled from
    LSC's releases, and how many grants have an amount on lsc.gov today."""
    rows = []
    for r in history["rounds"]:
        amounts = filled(r)
        printed = [tig_history.usd(g["printed"]) for g in r["grants"] if g["printed"]]
        on_site = set()
        for source in r["amounts"].values():
            on_site |= set(source)
        rows.append({
            "year": r["year"], "grants": len(r["grants"]), "printed": len(printed),
            "page_usd": sum(printed),
            "filled_usd": sum(a for a, _ in amounts.values()) if len(amounts) == len(r["grants"]) else None,
            "filled_from": sorted((t, s) for t, (_, s) in amounts.items() if s != "page"),
            "on_lsc_today": len(on_site),
        })
    return rows


def sources(history):
    """One row per round and release: how many of its amounts are the page's,
    which differ, and which fill a grant the page prints no amount for."""
    rows = []
    for r in history["rounds"]:
        page = {g["tig"]: g["printed"] for g in r["grants"]}
        for source in ORDER:
            if source not in r["amounts"]:
                continue
            got = r["amounts"][source]
            rows.append({
                "year": r["year"], "source": source, "url": r["sources"][source], "printed": len(got),
                "same": sum(1 for t, p in got.items() if page[t] == p),
                "differ": sorted(t for t, p in got.items() if page[t] and page[t] != p),
                "fills": sorted(t for t in got if not page[t]),
            })
    return rows


def grantee_totals(history):
    """Each per-grantee total a release states, against the sum of that
    grantee's grants."""
    rows = []
    for r in history["rounds"]:
        amounts = filled(r)
        for t in r["grantee_totals"]:
            parts = sum(amounts[n][0] for n in t["tigs"])
            stated = tig_history.usd(t["printed"])
            rows.append({"year": r["year"], "source": t["source"], "grantee": t["grantee"],
                         "stated_usd": stated, "parts_usd": parts, "difference": stated - parts})
    return rows


def listed(rnd):
    """Grants, organizations (distinct printed names), states (with DC) and
    territories in a round's list."""
    places = {g["state"] for g in rnd["grants"]}
    territories = places & set(tig_history.TERRITORIES)
    return {"grants": len(rnd["grants"]), "organizations": len({g["grantee"] for g in rnd["grants"]}),
            "states": len(places - territories), "territories": len(territories)}


def fits(rule, total):
    """Whether a dollar total meets a statement's rule; None if no rule or no total."""
    if not rule or total is None:
        return None
    (kind, x), = rule.items()
    if kind == "more_than":
        return total > x
    if kind == "nearly":
        return total < x
    if kind == "about":
        return (total + 50000) // 100000 * 100000 == x
    raise ValueError(kind)


def statements(history):
    """Each of LSC's statements with the counts that miss the list and whether
    its dollar figure fits the page's sum and the filled sum."""
    by_year = {t["year"]: t for t in totals(history)}
    rows = []
    for r in history["rounds"]:
        got = listed(r)
        t = by_year[r["year"]]
        for s in r["statements"]:
            wrong = [k for k in ("grants", "organizations", "states") if s[k] is not None and s[k] != got[k]]
            if s["states"] is not None and (s["territories"] or 0) != got["territories"]:
                wrong.append("territories")
            rows.append(dict(s, year=r["year"], listed=got, wrong=wrong,
                             fits_page=fits(s["usd"], t["page_usd"]),
                             fits_filled=fits(s["usd"], t["filled_usd"])))
    return rows


def says(s):
    parts = ["%d %s" % (s[k], "territory" if (k, s[k]) == ("territories", 1) else k)
             for k in ("grants", "organizations", "states", "territories") if s[k]]
    if s["usd"]:
        (kind, x), = s["usd"].items()
        parts.append("%s %s" % (kind.replace("_", " "), tig.dollars(x)))
    return ", ".join(parts)


def yes_no(x):
    return "-" if x is None else ("yes" if x else "no")


def totals_markdown(rows):
    lines = ["| Year | Grants | Amounts on the page | Sum of the page's amounts | Gaps filled from | Sum with gaps filled | Grants with an amount on lsc.gov today |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %d | %d | %s | %s | %s | %d |" % (
            r["year"], r["grants"], r["printed"], tig.dollars(r["page_usd"]),
            ", ".join("TIG %s (%s)" % (t, SOURCES[s]) for t, s in r["filled_from"]) or "none",
            tig.dollars(r["filled_usd"]) if r["filled_usd"] is not None else "-", r["on_lsc_today"]))
    return "\n".join(lines)


def sources_markdown(rows):
    lines = ["| Year | LSC release | Amounts printed | Same as the page | Different | Fill a gap in the page |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | [%s](%s) | %d | %d | %s | %s |" % (
            r["year"], SOURCES[r["source"]], r["url"], r["printed"], r["same"],
            ", ".join(r["differ"]) or "none", ", ".join(r["fills"]) or "none"))
    return "\n".join(lines)


def grantee_totals_markdown(rows):
    lines = ["| Year | Source | Grantee | Stated total | Sum of its grants | Difference |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %s | %s | %s | %s | %s |" % (
            r["year"], SOURCES[r["source"]], r["grantee"], tig.dollars(r["stated_usd"]),
            tig.dollars(r["parts_usd"]), tig_history.signed(r["difference"])))
    return "\n".join(lines)


def statements_markdown(rows):
    lines = ["| Year | Source | LSC says | Counts that miss the list | Dollar figure fits the page's sum | Fits the sum with gaps filled |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %s | %s | %s | %s | %s |" % (
            r["year"], SOURCES[r["source"]], says(r), ", ".join(r["wrong"]) or "none",
            yes_no(r["fits_page"]), yes_no(r["fits_filled"])))
    return "\n".join(lines)


def summary(history):
    return {
        "totals": totals(history),
        "sources": [{k: r[k] for k in ("year", "source", "printed", "same", "differ", "fills")}
                    for r in sources(history)],
        "grantee_totals_differ": [r for r in grantee_totals(history) if r["difference"]],
        "headings_differ": [dict(h, year=r["year"]) for r in history["rounds"] for h in r["headings"]],
        "statements_missing_counts": [{k: r[k] for k in ("year", "source", "quote", "wrong")}
                                      for r in statements(history) if r["wrong"]],
        "statements_dollars": [{k: r[k] for k in ("year", "source", "usd", "fits_page", "fits_filled")}
                               for r in statements(history) if r["usd"]],
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--sources", action="store_true", help="each release's amounts against the page")
    p.add_argument("--headlines", action="store_true", help="LSC's statements against the lists")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    history = load(args.data)
    if args.sources:
        print(sources_markdown(sources(history)))
        print()
        print(grantee_totals_markdown(grantee_totals(history)))
    elif args.headlines:
        print(statements_markdown(statements(history)))
    elif args.summary:
        json.dump(summary(history), sys.stdout, indent=2)
        print()
    else:
        print(totals_markdown(totals(history)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
