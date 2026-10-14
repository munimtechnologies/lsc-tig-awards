# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Summaries of LSC Technology Initiative Grant (TIG) awards, 2021-2025.

Reads data/tig_awards.json and reports, for each funding round, the awards
and dollars LSC lists, whether they agree with the counts and totals LSC
states, and the share of awards and dollars whose LSC description mentions AI.

    python tig.py                      # table by round
    python tig.py --kinds builds       # count only grants that build or deploy AI
    python tig.py --check              # listed awards against LSC's own statements
    python tig.py --ai-intake 2024 2025
    python tig.py --csv awards.csv     # one row per award

Standard library only. Information, not legal or funding advice.
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(HERE, "data", "tig_awards.json")

STATES = set(
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV "
    "NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR GU VI AS MP".split())
CATEGORIES = {"TIG", "TIG General", "TIG General - Initial Planning", "SEA", "TIP", None}
KINDS = ("builds", "plans", "considers")
TERMS = {"AI", "artificial intelligence", "chatbot", "generative AI", "agentic AI", "OpenAI",
         "Copilot", "natural language processing", "predictive analytics"}
TOTAL_KINDS = {"exact", "over", "millions"}
PHRASE_EVIDENCE = re.compile(r"\bAI\b|(?i:artificial intelligence|chatbot)")
PHRASE_MAX_WORDS = 15
CSV_FIELDS = ["year", "grantee", "state", "category", "amount_usd", "described", "intake",
              "ai_terms", "ai_kind", "ai_phrase", "note"]


def load(path=DEFAULT_DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(data):
    """Return a list of problems; empty when the file is well formed."""
    problems = []
    rounds = data.get("rounds", {})
    for year, rnd in rounds.items():
        for s in rnd.get("statements", []):
            if s.get("total_kind") not in TOTAL_KINDS:
                problems.append(f"{year}: statement total_kind {s.get('total_kind')!r}")
    for i, a in enumerate(data.get("awards", [])):
        where = f"award {i} ({a.get('year')} {a.get('grantee')})"
        if str(a.get("year")) not in rounds:
            problems.append(f"{where}: year has no round")
        if not isinstance(a.get("grantee"), str) or not a["grantee"].strip():
            problems.append(f"{where}: grantee")
        if a.get("state") not in STATES:
            problems.append(f"{where}: state {a.get('state')!r}")
        if a.get("category") not in CATEGORIES:
            problems.append(f"{where}: category {a.get('category')!r}")
        cents = a.get("amount_cents")
        if not isinstance(cents, int) or isinstance(cents, bool) or cents <= 0:
            problems.append(f"{where}: amount_cents")
        if not isinstance(a.get("described"), bool):
            problems.append(f"{where}: described")
        intake = a.get("intake")
        if a.get("described") is False and intake is not None:
            problems.append(f"{where}: intake must be null without a description")
        if a.get("described") is True and not isinstance(intake, bool):
            problems.append(f"{where}: intake must be true or false")
        terms = a.get("ai_terms")
        if not isinstance(terms, list) or not set(terms) <= TERMS:
            problems.append(f"{where}: ai_terms {terms!r}")
            continue
        kind, phrase = a.get("ai_kind"), a.get("ai_phrase")
        if terms:
            if a.get("described") is not True:
                problems.append(f"{where}: AI terms without a description")
            if kind not in KINDS:
                problems.append(f"{where}: ai_kind {kind!r}")
            if not isinstance(phrase, str) or not PHRASE_EVIDENCE.search(phrase):
                problems.append(f"{where}: ai_phrase does not show the term")
            elif len(phrase.split()) > PHRASE_MAX_WORDS:
                problems.append(f"{where}: ai_phrase longer than {PHRASE_MAX_WORDS} words")
        elif kind is not None or phrase is not None:
            problems.append(f"{where}: ai_kind or ai_phrase without ai_terms")
    return problems


def is_ai(award, kinds=KINDS):
    return bool(award["ai_terms"]) and award["ai_kind"] in kinds


def by_year(awards):
    out = {}
    for a in awards:
        out.setdefault(a["year"], []).append(a)
    return dict(sorted(out.items()))


def summarize(awards, kinds=KINDS):
    """Per round: awards, organisations, states, dollars, and the AI share."""
    out = {}
    for year, rows in by_year(awards).items():
        total = sum(a["amount_cents"] for a in rows)
        ai = [a for a in rows if is_ai(a, kinds)]
        ai_cents = sum(a["amount_cents"] for a in ai)
        out[year] = {
            "awards": len(rows),
            "organizations": len({a["grantee"] for a in rows}),
            "states": len({a["state"] for a in rows}),
            "described": sum(1 for a in rows if a["described"]),
            "total_cents": total,
            "ai_awards": len(ai),
            "ai_cents": ai_cents,
            "ai_award_share": len(ai) / len(rows),
            "ai_dollar_share": ai_cents / total if total else 0.0,
        }
    return out


def total_agrees(listed_cents, stated_cents, kind):
    """Whether a listed sum agrees with a stated total.

    exact: equal to the dollar. over: listed is above the figure.
    millions: a figure like "$5.1 million" agrees if rounding or truncating
    the listed sum to one decimal could give it, i.e. listed is in
    [figure - $50,000, figure + $100,000).
    """
    if kind == "exact":
        return listed_cents // 100 == stated_cents // 100
    if kind == "over":
        return listed_cents > stated_cents
    if kind == "millions":
        return stated_cents - 5_000_000 <= listed_cents < stated_cents + 10_000_000
    raise ValueError(kind)


def check_statements(data):
    """Compare each statement LSC makes about a round with the listed awards."""
    summary = summarize(data["awards"])
    results = []
    for year, rnd in sorted(data["rounds"].items()):
        s_year = summary.get(int(year))
        if s_year is None:
            continue
        for st in rnd["statements"]:
            res = {"year": int(year), "source": st["source"]}
            for field, listed in (("grants", s_year["awards"]),
                                  ("organizations", s_year["organizations"]),
                                  ("states", s_year["states"])):
                if st.get(field) is not None:
                    res[field] = {"stated": st[field], "listed": listed, "agrees": st[field] == listed}
            if st.get("total_cents") is not None:
                res["total"] = {"stated_cents": st["total_cents"], "kind": st["total_kind"],
                                "listed_cents": s_year["total_cents"],
                                "agrees": total_agrees(s_year["total_cents"], st["total_cents"],
                                                       st["total_kind"])}
            res["agrees"] = all(v["agrees"] for k, v in res.items() if isinstance(v, dict))
            results.append(res)
    return results


def ai_intake(awards, years=None, kinds=KINDS):
    """Awards whose description mentions both AI and intake."""
    return [a for a in awards
            if (years is None or a["year"] in years) and is_ai(a, kinds) and a["intake"]]


def dollars(cents):
    whole, part = divmod(cents, 100)
    return f"${whole:,}" + (f".{part:02d}" if part else "")


def write_csv(awards, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for a in awards:
            w.writerow({
                "year": a["year"], "grantee": a["grantee"], "state": a["state"],
                "category": a["category"] or "", "amount_usd": f"{a['amount_cents'] / 100:.2f}",
                "described": a["described"], "intake": "" if a["intake"] is None else a["intake"],
                "ai_terms": "; ".join(a["ai_terms"]), "ai_kind": a["ai_kind"] or "",
                "ai_phrase": a["ai_phrase"] or "", "note": a.get("note", ""),
            })


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DEFAULT_DATA)
    p.add_argument("--kinds", nargs="+", choices=KINDS, default=list(KINDS),
                   help="which AI mentions count (default: all)")
    p.add_argument("--check", action="store_true", help="compare with LSC's stated counts and totals")
    p.add_argument("--ai-intake", nargs="*", type=int, metavar="YEAR",
                   help="list awards that mention both AI and intake")
    p.add_argument("--csv", metavar="PATH", help="write one row per award")
    args = p.parse_args(argv)

    data = load(args.data)
    problems = validate(data)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    kinds = tuple(args.kinds)

    if args.csv:
        write_csv(data["awards"], args.csv)
        print(f"wrote {len(data['awards'])} awards to {args.csv}")
        return 0
    if args.ai_intake is not None:
        years = set(args.ai_intake) or None
        for a in ai_intake(data["awards"], years, kinds):
            print(f"{a['year']}  {a['state']}  {dollars(a['amount_cents']):>12}  {a['ai_kind']:<9}  {a['grantee']}")
        return 0
    if args.check:
        for r in check_statements(data):
            parts = []
            for field in ("grants", "organizations", "states"):
                if field in r:
                    parts.append(f"{field} {r[field]['stated']} stated / {r[field]['listed']} listed")
            if "total" in r:
                t = r["total"]
                parts.append(f"total {t['kind']} {dollars(t['stated_cents'])} / {dollars(t['listed_cents'])} listed")
            print(f"{r['year']} {r['source'][:10]:<10} {'agrees' if r['agrees'] else 'DIFFERS':<7}  " + "; ".join(parts))
        return 0

    print(f"{'round':<6}{'awards':>7}{'orgs':>6}{'listed':>16}{'AI awards':>11}{'AI dollars':>15}{'AI share $':>12}")
    for year, s in summarize(data["awards"], kinds).items():
        print(f"{year:<6}{s['awards']:>7}{s['organizations']:>6}{dollars(s['total_cents']):>16}"
              f"{s['ai_awards']:>11}{dollars(s['ai_cents']):>15}{s['ai_dollar_share'] * 100:>11.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
