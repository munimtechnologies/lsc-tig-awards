# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Compare each state's share of LSC technology grant (TIG) dollars with its
share of LSC basic field money, which LSC allocates by poverty population.

    python basic_field.py                 # markdown table, most over-represented first
    python basic_field.py --json          # the same rows as JSON
    python basic_field.py --summary       # headline figures as JSON
    python basic_field.py --build FR.txt  # parse an LSC Notice of Intent to Award
"""
import argparse
import html
import json
import os
import re
import sys

import tig

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "basic_field_2025.json")
SOURCE = {
    "document": "2024-26004",
    "citation": "89 FR 88814 (8 November 2024)",
    "title": "Legal Services Corporation: Notice of Intent To Award - Grant Awards for the Delivery of Civil Legal Services to Eligible Low-Income Clients Beginning January 1, 2025",
    "url": "https://www.federalregister.gov/documents/full_text/text/2024/11/08/2024-26004.txt",
    "column": "Estimated annualized 2025 funding",
}

# One table row: applicant name, state, service area, amount. Long names wrap
# onto lines that start with a single space.
ROW = re.compile(r"^(?P<name>\S.*?)\s+(?P<state>[A-Z]{2})\s+(?P<area>[A-Z]{2,4}(?:-\d+)?)"
                 r"\s+\$?(?P<amount>\d{1,3}(?:,\d{3})*)\s*$")
CONTINUATION = re.compile(r"^ \S")
PAGE = re.compile(r"^\[\[Page \d+\]\]$")
# The last header line ends "2025 funding"; the rule under it opens the table.
HEADER_END = re.compile(r"\bfunding\s*$")


def clean_name(name):
    return re.sub(r"\s+", " ", name).strip().rstrip(".").strip()


def parse_notice(text):
    """Rows of the notice's table, in printed order. The body runs from the
    rule under the header to the next rule; the notice has other rule lines
    before the table."""
    rows, in_body, prev, open_row = [], False, "", None
    for line in text.splitlines():
        if line.startswith("-----"):
            if in_body:
                break
            in_body = bool(HEADER_END.search(prev))
            continue
        if line.strip():
            prev = line
        if not in_body or not line.strip() or PAGE.match(line.strip()):
            continue
        m = ROW.match(line)
        if m:
            open_row = {"grantee": m.group("name"), "state": m.group("state"),
                        "service_area": m.group("area"),
                        "amount_usd": int(m.group("amount").replace(",", ""))}
            rows.append(open_row)
        elif CONTINUATION.match(line) and open_row is not None:
            open_row["grantee"] += " " + line.strip()
        else:
            raise ValueError("unrecognised table line: %r" % line)
    for r in rows:
        r["grantee"] = clean_name(r["grantee"])
    if len(rows) < 100:
        raise ValueError("only %d rows parsed; is this the right document?" % len(rows))
    return rows


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def by_state(rows):
    totals = {}
    for r in rows:
        totals[r["state"]] = totals.get(r["state"], 0) + r["amount_usd"]
    return totals


def compare(awards, service_areas):
    """One row per jurisdiction with basic field money. `index` is the
    state's share of TIG dollars divided by its share of basic field dollars:
    1.0 means TIG money reached it in proportion to its poverty population."""
    bf = by_state(service_areas)
    tig_usd = {}
    for a in awards:
        if a["amount_usd"] is not None:
            tig_usd[a["state"]] = tig_usd.get(a["state"], 0) + a["amount_usd"]
    missing = set(tig_usd) - set(bf)
    if missing:
        raise ValueError("TIG states with no basic field money: %s" % sorted(missing))
    rounds = len({a["year"] for a in awards})
    bf_total, tig_total = sum(bf.values()), sum(tig_usd.values())
    rows = []
    for state, usd in bf.items():
        t = tig_usd.get(state, 0)
        tig_share, bf_share = t / tig_total, usd / bf_total
        rows.append({"state": state, "basic_field_usd": usd, "basic_field_share": bf_share,
                     "tig_usd": round(t, 2), "tig_share": tig_share,
                     "index": tig_share / bf_share,
                     "tig_per_1000_basic_field_per_round": 1000.0 * t / rounds / usd})
    rows.sort(key=lambda r: (-r["index"], r["state"]))
    return rows


def headline(rows):
    def group(pred):
        g = [r for r in rows if pred(r)]
        return {"states": sorted(r["state"] for r in g), "count": len(g),
                "basic_field_share": sum(r["basic_field_share"] for r in g),
                "tig_share": sum(r["tig_share"] for r in g)}
    return {
        "jurisdictions": len(rows),
        "basic_field_usd": sum(r["basic_field_usd"] for r in rows),
        "tig_usd": round(sum(r["tig_usd"] for r in rows), 2),
        "no_tig": group(lambda r: r["tig_usd"] == 0),
        "under_half": group(lambda r: r["index"] < 0.5),
        "over_double": group(lambda r: r["index"] >= 2),
        "top5": [{"state": r["state"], "index": round(r["index"], 2)} for r in rows[:5]],
    }


def markdown(rows):
    lines = ["| State | Basic field 2025 | Share | TIG 2021-2025 | Share | Index |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %.2f |" % (
            r["state"], tig.dollars(r["basic_field_usd"]),
            tig.pct(r["basic_field_share"], 1), tig.dollars(r["tig_usd"]),
            tig.pct(r["tig_share"], 1), r["index"]))
    return "\n".join(lines)


def build(path):
    # federalregister.gov serves the "text" version inside an HTML <pre>.
    with open(path, encoding="utf-8") as f:
        rows = parse_notice(html.unescape(f.read()))
    return {"name": "lsc-basic-field-2025", "source": SOURCE,
            "description": "LSC basic field service areas and estimated annualized 2025 funding as printed in LSC's Notice of Intent to Award. Names lose the printer's dot leaders. CC BY 4.0.",
            "service_areas": rows}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--awards", default=tig.DATA)
    p.add_argument("--json", action="store_true", help="print the rows as JSON")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    p.add_argument("--build", metavar="NOTICE_TXT", help="parse a notice and print the data file")
    args = p.parse_args(argv)
    if args.build:
        json.dump(build(args.build), sys.stdout, indent=1)
        print()
        return 0
    rows = compare(tig.load(args.awards)["awards"], load(args.data)["service_areas"])
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
