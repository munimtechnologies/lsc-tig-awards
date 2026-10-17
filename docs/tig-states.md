# LSC technology grants by state, 2014-2025

Each Technology Initiative Grant (TIG) round from 2014 to 2025 has now been checked
against the Legal Services Corporation's (LSC's) own documents:
[tig-2014-2015.md](tig-2014-2015.md), [tig-2016-2017.md](tig-2016-2017.md),
[tig-history.md](tig-history.md), [tig-2021.md](tig-2021.md) and `data/awards.json`.
This page puts the rounds together by state. `tig_states.py` takes each round's
grants from the module that checks it and sets every state's dollars against the
poverty population behind LSC's 2025 basic field money (`poverty.py`), for 2014-2019,
2020-2025 and the whole period.

Code: `tig_states.py` (Apache-2.0), no new data. The hand sums are pinned in
`test_tig_states.py`, which also checks every round's total against the module that
checks that round.

    python tig_states.py            # per person in poverty, most over-represented first
    python tig_states.py --rounds   # dollars per round, then per state and round
    python tig_states.py --json     # the rows as JSON
    python tig_states.py --summary  # headline figures as JSON

## The rounds

| Year | Grants | Dollars |
|---|---|---|
| 2014 | 30 | $3,467,978 |
| 2015 (partial) | 7 | $1,214,048 |
| 2016 | 34 | $4,203,221 |
| 2017 | 25 | $3,927,974 |
| 2018 | 26 | $3,892,257 |
| 2019 | 30 | $4,231,402 |
| 2020 | 26 | $3,941,298 |
| 2021 | 35 | $4,268,931 |
| 2022 | 33 | $4,679,135 |
| 2023 | 33 | $5,157,033 |
| 2024 | 32 | $6,306,081 |
| 2025 | 31 | $4,064,308 |
| 2014-2025 (complete rounds) | 335 | $48,139,618 |

Which list each round uses: 2014, the PDF on lsc.gov (one row per grantee, so 30 rows
for LSC's 38 projects); 2016 and 2017, the archived description pages, with Iowa's 2016
amount from the PBIF release; 2018-2020, the description pages; 2021-2025,
`data/awards.json` (2021 is the release's list; one 2025 grant has no published amount
and is left out). LSC never published a 2015 list. Its releases name 7 of the 30
grantees, so 2015 is shown but left out of every period and count below. "Complete
rounds" means the other 11.

## Findings

- **No state had a grant in all 11 complete rounds.** Seven had one in 10: CA, FL, IL, MI, MT, OH and PA.
- **Maryland and Rhode Island had none**, nor did Guam, the Northern Mariana Islands and the U.S. Virgin Islands.
  All five have LSC basic field grantees. Any of them could be among the 23 unnamed 2015
  grantees.
- **Ohio got 22.2% of the dollars in 2014-2019 and 5.4% in 2020-2025** (12.3% over the
  whole period: $5,901,273). Most of it paid for one national service. LSC's own
  descriptions say Ohio State Legal Services' largest grant in each of 2014 and 2016-2021
  supports LawHelp Interactive, the online document assembly platform used in more than
  40 states:

| Year | Ohio State Legal Services grant for LawHelp Interactive |
|---|---|
| 2014 | $725,200 |
| 2016 | $808,000 |
| 2017 | $751,250 |
| 2018 | $783,000 |
| 2019 | $790,000 |
| 2020 | $526,400 |
| 2021 | $265,000 |

  These seven grants total $4,648,850. They were 19.6% of all TIG dollars in 2014-2019 and 2.8% in 2020-2025.
  None of LSC's 2022-2025 TIG releases mentions LawHelp Interactive. Because a grant
  counts to its grantee's state, Ohio's figures, and every state's share, should be read
  with these seven grants in mind: without them Ohio had $1,252,423.

## Limits

- Amounts are as LSC printed them, from the list each module uses. Where LSC's
  documents disagree (2018, 2019, 2021: see the round pages), this page uses that list
  and does not say which figure LSC paid.
- 2014 is one row per grantee, so its grant count is a count of grantees.
- Grants count to the grantee's state, even where the project serves other states.
- Poverty population is LSC's 2025 basis for every year, as in
  [pbif-poverty.md](pbif-poverty.md).

Compiled by MV2 of Munim, Inc., with AI agents working in his name. Docs CC BY 4.0,
code Apache-2.0. Information about public grants, not legal advice.
