# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC's three documents for the 2018 TIG round as the Internet Archive
captured them in 2018 and 2019, set against the same documents today
(data/tig_history.json) and against LawNext's November 2018 list.

    python archive_2018.py            # one row per archived document
    python archive_2018.py --summary  # headline figures as JSON
"""
import argparse
import json
import os
import sys

import lawnext_2018
import tig
import tig_history

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "tig_2018_archive.json")


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rows(archive, history, lawnext):
    """One row per capture: how many of its amounts match what the same LSC
    document prints today, its list sum where it prints every grant, and the
    grants where it prints LawNext's amount."""
    rnd = [r for r in history["rounds"] if r["year"] == archive["year"]][0]
    today = {g["tig"]: g for g in rnd["grants"]}
    ln = {g["tig"]: tig_history.usd(g["printed"]) for g in lawnext["grants"]}
    out = []
    for c in archive["captures"]:
        amounts = {t: tig_history.usd(p) for t, p in c["amounts"].items()}
        same = [t for t, v in amounts.items() if v == tig_history.amount(today[t], c["source"])]
        complete = c["source"] in rnd["complete"] and len(amounts) == len(today)
        out.append({
            "source": c["source"], "captured": c["captured"], "url": c["url"],
            "grants": len(amounts), "same": len(same),
            "differ": sorted(set(amounts) - set(same)),
            "listed_usd": sum(amounts.values()) if complete else None,
            "stated_usd": tig_history.usd(c["stated_total"]),
            "stated_same": c["stated_total"] == rnd["stated_total"],
            "lawnext": sorted(t for t, v in amounts.items() if v == ln[t]),
        })
    return out


def summary(archive, history, lawnext):
    rs = rows(archive, history, lawnext)
    return {
        "captures": len(rs),
        "amounts": sum(r["grants"] for r in rs),
        "same_as_today": sum(r["same"] for r in rs),
        "differ": {r["source"]: r["differ"] for r in rs if r["differ"]},
        "stated_all_same": all(r["stated_same"] for r in rs),
        "lawnext": {r["source"]: r["lawnext"] for r in rs if r["lawnext"]},
        "since_2000": {c["source"]: c["since_2000"] for c in archive["captures"] if c["since_2000"]},
    }


def markdown(rs):
    lines = ["| LSC document | Archived copy | Grants printed | Same amount as today | Sum of the list | Stated total | Prints LawNext's amount for |",
             "|---|---|---|---|---|---|---|"]
    for r in rs:
        lines.append("| %s | [%s](%s) | %d | %d | %s | %s | %s |" % (
            tig_history.SOURCES[r["source"]], r["captured"], r["url"], r["grants"], r["same"],
            tig.dollars(r["listed_usd"]) if r["listed_usd"] is not None else "-",
            tig.dollars(r["stated_usd"]), ", ".join(r["lawnext"]) or "none"))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--history", default=tig_history.DATA)
    p.add_argument("--lawnext", default=lawnext_2018.DATA)
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    args = p.parse_args(argv)
    archive = load(args.data)
    history = tig_history.load(args.history)
    lawnext = lawnext_2018.load(args.lawnext)
    if args.summary:
        json.dump(summary(archive, history, lawnext), sys.stdout, indent=2)
        print()
    else:
        print(markdown(rows(archive, history, lawnext)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
