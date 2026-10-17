# LSC technology grants by state, without national services

[tig-national.md](tig-national.md) set aside LawHelp Interactive's seven grants before
comparing states. [national-services.md](national-services.md) found 13 more grants that
LSC's own text says pay for a service it calls national; nine of them ("whole" grants)
pay for nothing else. This page sets those nine aside too.

Code: `tig_states.py --without-services` (Apache-2.0) sets aside the grants in
`data/national_services.json` with scope "whole". The four "part" grants also fund work
in the grantee's own state, so they stay in. The hand sums are pinned in
`test_tig_services.py`; `test_tig_services_doc.py` checks this page against the code.

    python tig_states.py --without-services --summary
    python tig_states.py --without-national --without-services --summary
    python tig_states.py --without-national --without-services   # the full table

## What each state loses

Only six states have a whole grant. Every other state's dollars stay the same.

| State | 2014-2019 | 2020-2025 | 2014-2025 |
|---|---|---|---|
| AK | $179,879 | $0 | $179,879 |
| HI | $0 | $93,290 | $93,290 |
| ID | $251,985 | $0 | $251,985 |
| ME | $175,250 | $50,000 | $225,250 |
| MI | $209,825 | $858,470 | $1,068,295 |
| WA | $297,175 | $0 | $297,175 |

## Totals and indexes

The index is a state's share of TIG dollars divided by its share of the poverty
population behind LSC's 2025 basic field money (1.0 means in proportion). LSC never
printed a full 2015 list, so 2015 is in no period, as in the other pages.

| | 2014-2019 | 2020-2025 | 2014-2025 |
|---|---|---|---|
| TIG dollars, all grants | $19,722,832 | $28,416,786 | $48,139,618 |
| TIG dollars, without the nine | $18,608,718 | $27,415,026 | $46,023,744 |
| TIG dollars, without the nine and LawHelp Interactive | $14,751,268 | $26,623,626 | $41,374,894 |
| Rise in every other state's index, without the nine | 6.0% | 3.7% | 4.6% |
| Rise in every other state's index, without both | 33.7% | 6.7% | 16.3% |
| Ohio's share, without both | 3.5% | 2.8% | 3.0% |
| Ohio's index, without both | 1.0 | 0.8 | 0.8 |

"Every other state" means every state that none of the 16 set-aside grants counts to
(not Ohio or the six above).

## Findings

- **Setting aside all 16 national-service grants takes 25.2% of the 2014-2019 TIG dollars out, and 6.3% of the 2020-2025 dollars.** Every other state's index rises by 33.7% in 2014-2019 and by 6.7% in 2020-2025.
- **Ohio's 2014-2019 index goes from 0.90 to 0.96** once the other national services are set aside as well as LawHelp Interactive, so its own projects come close to its share of people in poverty. It stays below 1.0 in every period.
- **TIG dollars per person in poverty, 2014-2025: $1.14 with every grant, $1.09 without the nine, $0.98 without both.**
- **Michigan loses $858,470 of its 2020-2025 TIG dollars**, more than any other state in that period, all for A2J Author (2020) and LSNTAP (2022).

## Limits

- The nine grants rest on LSC's wording, as listed in
  [national-services.md](national-services.md), not on grant budgets.
- Part grants stay in, even where LSC printed a national share for them (2014 Maine
  $75,270; 2015 Washington $429,960, in no period anyway).
- The new indexes for the six states themselves are in the table the commands above print.
  This page does not quote them yet.
- Setting grants aside is a way of reading the figures, not LSC's accounting. Amounts are
  as LSC printed them; poverty population is LSC's 2025 basis for every year.

Compiled by MV2 of Munim, Inc., with AI agents working in his name. Docs CC BY 4.0,
code Apache-2.0. Information about public grants, not legal advice.
