# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""LSC Pro Bono Innovation Fund (PBIF) awards by state, set against LSC basic
field money (allocated by poverty population) and against TIG awards.

    python pbif.py                 # PBIF table, most over-represented first
    python pbif.py --both          # TIG and PBIF dollars together
    python pbif.py --page          # PBIF table from the awards page alone
    python pbif.py --releases      # the awards page checked against LSC's press releases
    python pbif.py --summary       # headline figures as JSON
    python pbif.py --build PAGE    # parse LSC's PBIF awards page (saved HTML)
"""
import argparse
import html
import json
import os
import re
import sys

import basic_field
import tig

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "pbif_awards.json")
RELEASES = os.path.join(HERE, "data", "pbif_releases.json")
SOURCE = {
    "title": "LSC Pro Bono Innovation Fund: PBIF Awards",
    "url": "https://www.lsc.gov/grants-grantee-resources/our-grant-programs/pro-bono-innovation-fund/awards",
}
TRACKS = ("Planning", "Project", "Sustainability", "Transformation")

# "Iowa Legal Aid (ILA) ($489,100.00)- 2025- Expungement". The subject is
# printed for Project and Sustainability grants only.
HEADING = re.compile(r"^(?P<name>[^()]+?)\s*\((?P<abbr>[^()]+)\)\s*\(\s*\$(?P<amount>[\d.,]+)\s*\)"
                     r"\s*-\s*(?P<year>20\d\d)\b\s*(?:-\s*(?P<subject>.+?))?\s*$")
SECTION = re.compile(r"^(?P<track>%s) Grant(?:ee)?s?:?$" % "|".join(TRACKS), re.I)
HIDDEN = re.compile(r"<(script|style|noscript)\b.*?</\1>"
                    r"|<span\b[^>]*class=\"[^\"]*(?:visually-hidden|sr-only)[^\"]*\"[^>]*>.*?</span>",
                    re.S | re.I)
BLOCK = re.compile(r"</?(?:p|div|h[1-6]|li|ul|ol|button|summary|details|section|article|br|tr|td|th|table)\b[^>]*>",
                   re.I)
TOGGLE = re.compile(r"\b(?:expand and show|collapse and hide) content\b", re.I)

# Names LSC printed on the PBIF page or in a press release that differ from
# the grantee name in the basic field notice, beyond case, punctuation, "Inc",
# "Corporation" and "the".
ALIASES = {
    "legal aid foundation of los angeles county": "legal aid foundation of los angeles",
    "legal aid of western virginia": "legal aid of west virginia",
    "legal aid of western new york": "legal assistance of western new york",
    "legal action wisconsin": "legal action of wisconsin",
    "legal aid of chicago": "legal aid chicago",
}


def parse_amount(text):
    """'489,100.00' -> 489100.0. Two amounts are printed with a comma before
    the cents ('481,386,29'); a final group of two digits is read as cents."""
    m = re.fullmatch(r"(\d{1,3}(?:,\d{3})*)(?:[.,](\d{2}))?", text)
    if not m:
        raise ValueError("unreadable amount: %r" % text)
    return int(m.group(1).replace(",", "")) + int(m.group(2) or 0) / 100.0


def page_lines(text):
    text = HIDDEN.sub(" ", text)
    text = BLOCK.sub("\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", TOGGLE.sub(" ", line.replace("\xa0", " "))).strip()
        if line:
            lines.append(line)
    return lines


def parse_page(text):
    """Award headings of the PBIF page in printed order, each with the track
    of the section it sits in."""
    awards, track = [], None
    for line in page_lines(text):
        s = SECTION.match(line)
        if s:
            track = s.group("track").capitalize()
            continue
        m = HEADING.match(line)
        if m:
            awards.append({"grantee": m.group("name").strip(), "abbreviation": m.group("abbr").strip(),
                           "track": track, "year": int(m.group("year")),
                           "subject": m.group("subject"), "printed_amount": "$" + m.group("amount"),
                           "amount_usd": parse_amount(m.group("amount"))})
    return awards


def norm(name):
    s = re.sub(r"[^a-z ]", " ", name.lower().replace("&", " and "))
    s = " ".join(w for w in s.split() if w not in ("inc", "the", "corporation"))
    return ALIASES.get(s, s)


def grantee_states(service_areas):
    """Normalised grantee name -> state, from the basic field notice. A grantee
    with areas in several states (Pine Tree: ME and a Native American area in
    CT) takes the state of its general service areas."""
    found = {}
    for r in service_areas:
        general = re.fullmatch(r"[A-Z]{2}-\d+", r["service_area"]) is not None
        found.setdefault(norm(r["grantee"]), []).append((general, r["state"]))
    states = {}
    for name, seen in found.items():
        pick = {s for g, s in seen if g} or {s for g, s in seen}
        if len(pick) == 1:
            states[name] = pick.pop()
    return states


def assign_states(awards, service_areas):
    """Set each award's state from the basic field notice; return the names
    that matched no single grantee."""
    states = grantee_states(service_areas)
    unmatched = []
    for a in awards:
        a["state"] = states.get(norm(a["grantee"]))
        if a["state"] is None:
            unmatched.append(a["grantee"])
    return sorted(set(unmatched))


def build(text, service_areas):
    awards = parse_page(text)
    unmatched = assign_states(awards, service_areas)
    return {"name": "lsc-pbif-awards", "source": SOURCE,
            "description": "LSC Pro Bono Innovation Fund awards as printed in the headings of LSC's PBIF Awards page, with each grantee's state taken from LSC's 2025 basic field notice. CC BY 4.0.",
            "unmatched": unmatched, "awards": awards}


def load(path=DATA):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_releases(path=RELEASES):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["releases"]


def same_amount(page_usd, release_usd):
    # Releases print whole dollars, rounded or cut: $372,223 for $372,223.60.
    return abs(page_usd - release_usd) < 1


def reconcile(page_awards, releases):
    """Each grant a press release prints, matched to a page heading of the
    same grantee and year: 'same' (under $1 apart), 'amount differs', or
    'release only'. For a release that lists every grant of its round, page
    headings of that year left unmatched are 'page only'."""
    rows = []
    for rel in releases:
        pool = [a for a in page_awards if a["year"] == rel["year"]]
        grants = [dict(g, usd=parse_amount(g["printed"].lstrip("$"))) for g in rel["grants"]]
        found, used = {}, set()
        # Equal amounts first, so a grantee with two grants pairs each correctly.
        for exact in (True, False):
            for i, g in enumerate(grants):
                for j, a in enumerate(pool):
                    if i in found or j in used or norm(a["grantee"]) != norm(g["grantee"]):
                        continue
                    if exact and not same_amount(a["amount_usd"], g["usd"]):
                        continue
                    found[i] = j
                    used.add(j)
        for i, g in enumerate(grants):
            a = pool[found[i]] if i in found else None
            if a is None:
                status = "release only"
            else:
                status = "same" if same_amount(a["amount_usd"], g["usd"]) else "amount differs"
            rows.append({"year": rel["year"], "grantee": g["grantee"], "printed": g["printed"],
                         "release_usd": g["usd"], "page_usd": a["amount_usd"] if a else None,
                         "status": status, "url": rel["url"]})
        if rel["complete"]:
            for j, a in enumerate(pool):
                if j not in used:
                    rows.append({"year": rel["year"], "grantee": a["grantee"], "printed": None,
                                 "release_usd": None, "page_usd": a["amount_usd"],
                                 "status": "page only", "url": rel["url"]})
    return rows


def combined(page_awards, recon, service_areas):
    """The page's awards plus the grants that only a press release prints,
    each with its state. Where both print an amount, the page's is used."""
    states = grantee_states(service_areas)
    extra = [{"grantee": r["grantee"], "abbreviation": None, "track": None, "year": r["year"],
              "subject": None, "printed_amount": r["printed"], "amount_usd": r["release_usd"],
              "state": states.get(norm(r["grantee"])), "source": r["url"]}
             for r in recon if r["status"] == "release only"]
    return page_awards + extra


def markdown(rows, label):
    lines = ["| State | Basic field 2025 | Share | %s | Share | Index |" % label,
             "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %.2f |" % (
            r["state"], tig.dollars(r["basic_field_usd"]),
            tig.pct(r["basic_field_share"], 1), tig.dollars(r["tig_usd"]),
            tig.pct(r["tig_share"], 1), r["index"]))
    return "\n".join(lines)


def releases_markdown(recon):
    """The grants whose page and release records disagree, in year order."""
    lines = ["| Year | Grantee | Press release | PBIF page | Status |", "|---|---|---|---|---|"]
    for r in recon:
        if r["status"] == "same":
            continue
        lines.append("| %d | %s | %s | %s | %s |" % (
            r["year"], r["grantee"], r["printed"] or "not listed",
            tig.dollars(r["page_usd"]) if r["page_usd"] is not None else "not listed", r["status"]))
    return "\n".join(lines)


def headline(pbif_awards, tig_awards, service_areas):
    pb = basic_field.compare(pbif_awards, service_areas)
    both = basic_field.compare(pbif_awards + tig_awards, service_areas)
    t = {r["state"]: r for r in basic_field.compare(tig_awards, service_areas)}
    p = {r["state"]: r for r in pb}
    return {
        "pbif_awards": len(pbif_awards),
        "pbif_usd": round(sum(a["amount_usd"] for a in pbif_awards), 2),
        "pbif_years": sorted({a["year"] for a in pbif_awards}),
        "pbif": basic_field.headline(pb),
        "both": basic_field.headline(both),
        "no_tig_but_pbif": sorted(s for s in t if t[s]["tig_usd"] == 0 and p[s]["tig_usd"] > 0),
        "neither": sorted(s for s in t if t[s]["tig_usd"] == 0 and p[s]["tig_usd"] == 0),
    }


def release_summary(page_awards, recon, releases):
    """Per release: grants printed, how each matched, and the page's count
    of grantees and states for that year next to the counts LSC stated."""
    out = []
    for rel in releases:
        rows = [r for r in recon if r["year"] == rel["year"]]
        page = [a for a in page_awards if a["year"] == rel["year"]]
        count = {s: sum(1 for r in rows if r["status"] == s)
                 for s in ("same", "amount differs", "release only", "page only")}
        out.append({"year": rel["year"], "url": rel["url"], "complete": rel["complete"],
                    "grants_printed": len(rel["grants"]), **count,
                    "page_headings": len(page),
                    "page_grantees": len({norm(a["grantee"]) for a in page}),
                    "page_states": len({a["state"] for a in page}),
                    "stated_organizations": rel.get("stated_organizations"),
                    "stated_states": rel.get("stated_states"),
                    "stated_total": rel.get("stated_total")})
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=DATA)
    p.add_argument("--releases-data", default=RELEASES)
    p.add_argument("--basic-field", default=basic_field.DATA)
    p.add_argument("--awards", default=tig.DATA)
    p.add_argument("--both", action="store_true", help="TIG and PBIF dollars together")
    p.add_argument("--page", action="store_true", help="the awards page alone, without release-only grants")
    p.add_argument("--releases", action="store_true", help="where the page and the press releases disagree")
    p.add_argument("--summary", action="store_true", help="print headline figures as JSON")
    p.add_argument("--build", metavar="PAGE_HTML", help="parse a saved PBIF page and print the data file")
    args = p.parse_args(argv)
    areas = basic_field.load(args.basic_field)["service_areas"]
    if args.build:
        with open(args.build, encoding="utf-8") as f:
            json.dump(build(f.read(), areas), sys.stdout, indent=1)
        print()
        return 0
    page_awards = load(args.data)["awards"]
    releases = load_releases(args.releases_data)
    recon = reconcile(page_awards, releases)
    pbif_awards = page_awards if args.page else combined(page_awards, recon, areas)
    tig_awards = tig.load(args.awards)["awards"]
    if args.releases:
        print(releases_markdown(recon))
    elif args.summary:
        head = headline(pbif_awards, tig_awards, areas)
        head["releases"] = release_summary(page_awards, recon, releases)
        json.dump(head, sys.stdout, indent=2)
        print()
    elif args.both:
        print(markdown(basic_field.compare(pbif_awards + tig_awards, areas), "TIG and PBIF"))
    else:
        print(markdown(basic_field.compare(pbif_awards, areas), "PBIF 2022-2025"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
