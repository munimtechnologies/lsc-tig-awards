# LSC technology grants by state, with LawHelp Interactive set aside

[tig-states.md](tig-states.md) counts each Technology Initiative Grant (TIG) to its
grantee's state. Seven of the grants it counts to Ohio paid for LawHelp Interactive, the
online legal forms platform that LSC's own descriptions say is used in more than 40
states. This page sets those seven grants aside and shows what changes.

`data/national_grants.json` (CC BY 4.0) lists them, each with LSC's own words and a link
to the LSC page (or its archived copy) that describes it. `tig_states.py` takes them out
of the grant list before comparing states; each must match exactly one grant by year,
state and amount.

    python tig_states.py --without-national             # per person in poverty
    python tig_states.py --without-national --summary   # headline figures as JSON

Tests: `test_tig_national.py` pins the hand sums and `test_tig_national_doc.py` checks
this page against the code.

## The seven grants

| Year | Grant | LSC's description calls LawHelp Interactive |
|---|---|---|
| 2014 | $725,200 | "the national online document assembly service" |
| 2016 | $808,000 | "the national online document assembly platform" |
| 2017 | $751,250 | a forms website, with enhancements for "legal aid programs nationwide" |
| 2018 | $783,000 | "the national online document assembly initiative used by more than 40 states" |
| 2019 | $790,000 | "a free online resource for drafting legal forms and documents in over 40 states" |
| 2020 | $526,400 | "a national document assembly platform used in more than 40 states" |
| 2021 | $265,000 | "a national document assembly platform used in more than 40 states" |

Together $4,648,850: $3,857,450 in 2014-2019 and $791,400 in 2020-2025.

## What changes

The index is a state's share of TIG dollars divided by its share of the poverty
population behind LSC's 2025 basic field money. 1.0 means TIG money in proportion to
people in poverty. Ohio has 3.6% of that population.

| | 2014-2019 | 2020-2025 | 2014-2025 |
|---|---|---|---|
| TIG dollars, all grants | $19,722,832 | $28,416,786 | $48,139,618 |
| TIG dollars, without the seven | $15,865,382 | $27,625,386 | $43,490,768 |
| Ohio's share, all grants | 22.2% | 5.4% | 12.3% |
| Ohio's share, without the seven | 3.2% | 2.7% | 2.9% |
| Ohio's index, all grants | 6.1 | 1.5 | 3.4 |
| Ohio's index, without the seven | 0.9 | 0.7 | 0.8 |
| Rise in every other state's index | 24.3% | 2.9% | 10.7% |

## Findings

- **Without LawHelp Interactive, Ohio was below its share in every period.** Its index
  in 2014-2019 falls from 6.1 to 0.9.
- **Ohio drops from 10 complete rounds with a grant to 8.** Its only 2017 and 2020
  grants were for LawHelp Interactive.
- **Six states had a grant in 10 of the 11 complete rounds: CA, FL, IL, MI, MT and PA.**
- **Every other state's index rises by 24.3% in 2014-2019** and by 2.9% in 2020-2025,
  because the seven grants were 19.6% and 2.8% of all TIG dollars in those periods.
- TIG dollars per person in poverty, 2014-2025, fall from $1.14 to $1.03.

## Limits

- Only the LawHelp Interactive grants are set aside. Other grants may serve more than one
  state too; none is flagged unless LSC's own description says so.
- Setting a grant aside is a way of reading the figures, not LSC's accounting. LSC paid
  these grants to Ohio State Legal Services.
- Amounts are as LSC printed them in the list each round's module uses. The 2014 local
  release gives $735,200 for this grant; the 2014 list and full release give $725,200
  (see [tig-2014-2015.md](tig-2014-2015.md)).
- Poverty population is LSC's 2025 basis for every year, as in
  [tig-states.md](tig-states.md).

Compiled by MV2 of Munim, Inc., with AI agents working in his name. Docs and data
CC BY 4.0, code Apache-2.0. Information about public grants, not legal advice.
