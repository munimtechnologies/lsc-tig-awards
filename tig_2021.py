# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Technology Initiative Grant (TIG) round 2021 from LSC's description
page (amounts to the cent) matched grant by grant to its press release, both
summed and set against LSC's stated total and counts; and LSC's cumulative
"since the program's inception" figures in its 2020-2025 TIG releases, each
set against the one before plus the round between them.

    python tig_2021.py              # page and release sums against the stated total
    python tig_2021.py --sources    # amounts that differ and which figures make the total
    python tig_2021.py --headlines  # LSC's statements and cumulative figures
    python tig_2021.py --summary    # headline figures as JSON
"""
import argparse
import itertools
import json
import os
import sys

import tig

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "tig_2021.json")
SECTIONS = {"TIG": "Technology Initiative Grant awards", "TIP": "Technology Improvement Project awards"}
SUMS = ("page", "release", "reconciled")
SUM_LABELS = {"page": "description page", "release": "release",
              "reconciled": "release's amounts with the page's cents"}


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cents(printed):
    """'$150, 593.60' -> 15059360."""
    s = printed.lstrip("$").replace(",", "").replace(" ", "")
    whole, _, frac = s.partition(".")
    return int(whole) * 100 + int((frac + "00")[:2])


def rounded(c):
    """Cents to whole dollars, half up."""
    return (c + 50) // 100


def money(c):
    out = "$" + format(c // 100, ",")
    return out + (".%02d" % (c % 100) if c % 100 else "")


def signed(c):
    if c == 0:
        return "$0"
    return ("+" if c > 0 else "-") + money(abs(c))


def differ(history):
    """Grants whose release amount is not the page's amount cut to whole dollars."""
    return [g for g in history["grants"] if cents(g["release"]) != cents(g["page"]) // 100 * 100]


def reconciled(g):
    """A grant's amount with the release's whole dollars and the page's cents."""
    return cents(g["release"]) + cents(g["page"]) % 100


def totals(history):
    """The page's sum, the release's sum, and the release's amounts with the
    page's cents, each against LSC's stated total."""
    (stated,) = [s["usd"]["exactly"] for s in history["statements"] if s["usd"] and "exactly" in s["usd"]]
    grants = history["grants"]
    sums = {"page": sum(cents(g["page"]) for g in grants),
            "release": sum(cents(g["release"]) for g in grants),
            "reconciled": sum(reconciled(g) for g in grants)}
    return [{"sum": k, "grants": len(grants), "sum_cents": c, "stated_usd": stated,
             "difference_cents": c - stated * 100, "rounds_to_stated": rounded(c) == stated}
            for k, c in sums.items()]


def sections(history):
    """One row per section of the page: grants, sum, smallest and largest."""
    rows = []
    for key in SECTIONS:
        amounts = [cents(g["page"]) for g in history["grants"] if g["section"] == key]
        rows.append({"section": key, "grants": len(amounts), "sum_cents": sum(amounts),
                     "min_cents": min(amounts), "max_cents": max(amounts)})
    return rows


def swaps(history):
    """The page's list with each set of its differing amounts replaced by the
    release's (keeping the page's cents), against the stated total."""
    (stated,) = [s["usd"]["exactly"] for s in history["statements"] if s["usd"] and "exactly" in s["usd"]]
    page = sum(cents(g["page"]) for g in history["grants"])
    odd = differ(history)
    rows = []
    for n in range(len(odd) + 1):
        for chosen in itertools.combinations(odd, n):
            c = page + sum(reconciled(g) - cents(g["page"]) for g in chosen)
            rows.append({"swapped": [g["organization"] for g in chosen], "sum_cents": c,
                         "difference_cents": c - stated * 100, "rounds_to_stated": rounded(c) == stated})
    return rows


def cut_to_dollars(history):
    """Grants the page prints with cents, all of which the release prints cut
    (not rounded) to whole dollars."""
    return [g for g in history["grants"] if cents(g["page"]) % 100 and g not in differ(history)]


def listed(history):
    """Grants, organizations (by the release's name) and states (with DC)."""
    grants = history["grants"]
    return {"grants": len(grants), "organizations": len({g["organization"] for g in grants}),
            "states": len({g["state"] for g in grants})}


def fits(rule, c):
    """Whether a sum in cents meets a statement's rule; None if no rule."""
    if not rule:
        return None
    (kind, x), = rule.items()
    if kind == "exactly":
        return rounded(c) == x
    if kind == "more_than":
        return c > x * 100
    if kind == "nearly":
        return c < x * 100
    raise ValueError(kind)


def statements(history):
    """Each of LSC's statements with the counts that miss the list and
    whether its dollar figure fits each of the three sums."""
    got = listed(history)
    sums = {t["sum"]: t["sum_cents"] for t in totals(history)}
    rows = []
    for s in history["statements"]:
        wrong = [k for k in ("grants", "organizations") if s[k] is not None and s[k] != got[k]]
        rows.append(dict(s, listed=got, wrong=wrong, fits={k: fits(s["usd"], sums[k]) for k in SUMS}))
    return rows


def rounds(awards):
    """Grants and the sum of priced grants per round in data/awards.json."""
    out = {}
    for a in awards["awards"]:
        r = out.setdefault(a["year"], {"grants": 0, "usd": 0.0, "unpriced": 0})
        r["grants"] += 1
        if a["amount_usd"] is None:
            r["unpriced"] += 1
        else:
            r["usd"] += a["amount_usd"]
    for r in out.values():
        r["usd"] = int(round(r["usd"]))
    return out


def cumulative(history, awards):
    """Each cumulative figure from 2022 on against the year before plus the
    round between them (grants listed in data/awards.json; dollars a lower
    bound: the previous 'more than' plus the round's priced grants)."""
    by_year = rounds(awards)
    rows = []
    figures = [c for c in history["cumulative"] if c["grants"] is not None]
    for prev, cur in zip(figures, figures[1:]):
        r = by_year[cur["year"]]
        implied = prev["grants"] + r["grants"]
        at_least = prev["usd"]["more_than"] + r["usd"]
        rows.append({"year": cur["year"], "previous_grants": prev["grants"], "round_grants": r["grants"],
                     "implied_grants": implied, "stated_grants": cur["grants"],
                     "grants_difference": cur["grants"] - implied,
                     "round_usd": r["usd"], "round_unpriced": r["unpriced"],
                     "implied_usd_more_than": at_least, "stated_usd_more_than": cur["usd"]["more_than"],
                     "usd_below_implied": at_least - cur["usd"]["more_than"]})
    return rows


def step_2020(history):
    """The 2020-to-2021 step in dollars: what 2021's 'more than' leaves for
    the years before the 2021 round, against 2020's 'nearly', read two ways."""
    first, second = history["cumulative"][0], history["cumulative"][1]
    (stated,) = [s["usd"]["exactly"] for s in history["statements"] if s["usd"] and "exactly" in s["usd"]]
    before_2021 = second["usd"]["more_than"] - stated
    nearly = first["usd"]["nearly"]
    with_2020 = nearly
    without_2020 = nearly + history["round_2020"]["usd"]
    return {"before_2021_more_than": before_2021, "nearly_2020": nearly,
            "if_2020_includes_its_round": {"before_2021_less_than": with_2020,
                                           "fits": before_2021 < with_2020,
                                           "short_by_at_least": max(0, before_2021 - with_2020)},
            "if_2020_excludes_its_round": {"before_2021_less_than": without_2020,
                                           "fits": before_2021 < without_2020,
                                           "short_by_at_least": max(0, before_2021 - without_2020)}}


def yes_no(x):
    return "-" if x is None else ("yes" if x else "no")


def totals_markdown(rows):
    lines = ["| Sum | Grants | Sum of the amounts | LSC's stated total | Difference | Rounds to the stated total |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %d | %s | %s | %s | %s |" % (
            SUM_LABELS[r["sum"]], r["grants"], money(r["sum_cents"]), tig.dollars(r["stated_usd"]),
            signed(r["difference_cents"]), yes_no(r["rounds_to_stated"])))
    return "\n".join(lines)


def sections_markdown(rows):
    lines = ["| Page section | Grants | Sum | Smallest | Largest |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %d | %s | %s | %s |" % (
            SECTIONS[r["section"]], r["grants"], money(r["sum_cents"]), money(r["min_cents"]), money(r["max_cents"])))
    return "\n".join(lines)


def differ_markdown(history):
    lines = ["| Grantee | Application | Page | Release | Release minus page |", "|---|---|---|---|---|"]
    for g in differ(history):
        lines.append("| %s | %s | %s | %s | %s |" % (
            g["organization"], g["ap"], money(cents(g["page"])), money(cents(g["release"])),
            signed(reconciled(g) - cents(g["page"]))))
    return "\n".join(lines)


def swaps_markdown(rows):
    lines = ["| Page list with the release's amount for | Sum | Against $4,268,938 | Rounds to it |",
             "|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s |" % (
            " and ".join(r["swapped"]) or "neither (the page as printed)", money(r["sum_cents"]),
            signed(r["difference_cents"]), yes_no(r["rounds_to_stated"])))
    return "\n".join(lines)


def says(s):
    parts = ["%d %s" % (s[k], k) for k in ("grants", "organizations") if s[k] is not None]
    if s["usd"]:
        (kind, x), = s["usd"].items()
        parts.append("%s %s" % (kind.replace("_", " "), tig.dollars(x)))
    return ", ".join(parts)


def statements_markdown(rows):
    lines = ["| Source | LSC says | Counts that miss the list | Fits the page's sum | Fits the release's sum | Fits the release's amounts with the page's cents |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            SUM_LABELS[r["source"]], says(r), ", ".join(r["wrong"]) or "none",
            yes_no(r["fits"]["page"]), yes_no(r["fits"]["release"]), yes_no(r["fits"]["reconciled"])))
    return "\n".join(lines)


def cumulative_markdown(rows):
    lines = ["| Release | Previous release's grants | Grants in the round | Sum | LSC says | Difference | Previous 'more than' plus the round's priced grants | LSC says more than | Below the sum by |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %d | %d | %d | %d | %d | %+d | %s | %s | %s |" % (
            r["year"], r["previous_grants"], r["round_grants"], r["implied_grants"], r["stated_grants"],
            r["grants_difference"], tig.dollars(r["implied_usd_more_than"]),
            tig.dollars(r["stated_usd_more_than"]), tig.dollars(r["usd_below_implied"])))
    return "\n".join(lines)


def summary(history, awards):
    return {
        "totals": totals(history),
        "sections": sections(history),
        "differ": [{k: g[k] for k in ("organization", "ap", "page", "release")} for g in differ(history)],
        "cut_to_dollars": len(cut_to_dollars(history)),
        "swaps_matching": [r["swapped"] for r in swaps(history) if r["rounds_to_stated"]],
        "headings_differ": history["headings"],
        "listed": listed(history),
        "statements_missing_counts": [{k: r[k] for k in ("source", "quote", "wrong")}
                                      for r in statements(history) if r["wrong"]],
        "statements_dollars": [{k: r[k] for k in ("source", "usd", "fits")}
                               for r in statements(history) if r["usd"]],
        "cumulative": cumulative(history, awards),
        "step_2020": step_2020(history),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--awards", default=tig.DATA)
    p.add_argument("--sources", action="store_true", help="amounts that differ and which figures make the total")
    p.add_argument("--headlines", action="store_true", help="LSC's statements and cumulative figures")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    history = load(args.data)
    awards = tig.load(args.awards)
    if args.sources:
        print(differ_markdown(history))
        print()
        print(swaps_markdown(swaps(history)))
    elif args.headlines:
        print(statements_markdown(statements(history)))
        print()
        print(cumulative_markdown(cumulative(history, awards)))
    elif args.summary:
        json.dump(summary(history, awards), sys.stdout, indent=2)
        print()
    else:
        print(totals_markdown(totals(history)))
        print()
        print(sections_markdown(sections(history)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
