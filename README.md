# lsc-tig-awards

Every award the Legal Services Corporation (LSC) lists for the 2021-2025 rounds of its **Technology Initiative Grant (TIG)** program, the main US federal funder of technology at civil legal aid programs. The data is one machine-readable record per award (164 awards, $24.47 million), transcribed from LSC's own pages. Each record says whether LSC's description of the project mentions AI, with the phrase that does, and whether it mentions intake.

Maintained by MV2 of Munim, Inc. The data, code and this write-up were made with AI agents working in his name. Information only: not legal, grant-writing or funding advice, and not affiliated with LSC.

## What it shows

**AI went from one award in 2021 to about two in every five TIG dollars by 2024.**

| Round | Awards listed | Organisations | Listed total | Awards mentioning AI | Their dollars | Share of dollars |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 35 | 29 | $4,265,737.84 | 1 (2.9%) | $93,290 | **2.2%** |
| 2022 | 33 | 29 | $4,679,135.03 | 2 (6.1%) | $261,418.49 | **5.6%** |
| 2023 | 33 | 29 | $5,157,033 | 4 (12.1%) | $1,089,634 | **21.1%** |
| 2024 | 32 | 29 | $6,306,081 | 9 (28.1%) | $2,720,420 | **43.1%** |
| 2025 | 31 | 28 | $4,064,308 | 11 (35.5%) | $1,643,948 | **40.4%** |

- Up to 2024, every award that mentions AI builds or deploys an AI tool. In 2025, five of the eleven only plan for AI or name it as a possible feature. Counting only grants that build or deploy AI, 2025's share is **29.8%** ($1,210,748).
- Both figures for 2025 are low, because one award is missing from LSC's list page (below). LSC's press release describes it as Legal Services of Greater Miami "expanding its use of AI agents". If it is the 32nd award, and the round really totalled over $4.2 million, it brings at least $135,692 more, which lifts 2025 above 42.4% (all mentions) and 32.1% (builds only).
- In 2024, eleven small Technology Improvement Project awards ($374,000) were listed without descriptions, so they could not be tagged.

**Where AI is going into intake.** Nine awards in 2024-2025 mention both AI and intake. Four put AI directly into a program's intake: Legal Aid of North Carolina (2024), Florida Rural Legal Services and Legal Aid Society of Middle Tennessee and the Cumberlands (voice agents, 2025), and Southern Minnesota Regional Legal Services (generative AI in Minnesota's coordinated intake, 2025). Five plan or consider it: Legal Aid of the Bluegrass, Legal Services of Eastern Missouri, Legal Services of the Hudson Valley, Legal Aid Services of Oregon and Legal Aid of Southeastern Pennsylvania. TIG projects carry an evaluation plan approved by LSC. Florida Rural Legal Services and Middle Tennessee have already asked for bids on an independent one (see [legal-aid-intake-eval](https://github.com/munimtechnologies/legal-aid-intake-eval) for open tooling built for that kind of evaluation). Run `python tig.py --ai-intake 2024 2025` to see the list.

**LSC's own counts and totals don't match its lists in 2024 and 2025.** `python tig.py --check`:

| Round | LSC states | Listed awards add up to | Agrees? |
|---|---|---|---|
| 2021 | 35 grants, 29 organisations, over $4 million | 35, 29, $4,265,737.84 | yes |
| 2022 | 33 grants, 29 providers, $4,679,135 (headline $4.6 million) | 33, 29, $4,679,135.03 | yes, to the dollar |
| 2023 | 33 grants, 29 organisations, $5.1 million | 33, 29, $5,157,033 | yes |
| 2024 headline | $5.9 million to 31 providers | $6,306,081 to 29 organisations | no |
| 2024 body | 32 grants totalling $6.2 million | 32, $6,306,081 | count yes, total no |
| 2025 list page | 32 grants to 22 organisations, over $4.2 million | 31, 28 organisations, $4,064,308 | no |
| 2025 press release | 32 grants, $4.2 million, 22 states | 31, 21 states, $4,064,308 | no |

The exact match for 2022 is a check on the transcription. These are reporting slips on public pages, not a finding about how any grant was spent.

## Use

```
python tig.py                       # the table above
python tig.py --kinds builds        # only grants that build or deploy AI
python tig.py --check               # LSC's statements against the listed awards
python tig.py --ai-intake 2024 2025 # awards that mention both AI and intake
python tig.py --csv awards.csv      # one row per award
python -m unittest -v
```

Standard library only (Python 3.8+). `data/tig_awards.json` holds each round's source URL, LSC's own count and total statements (quoted), notes on printing quirks, and the awards.

## Method

- **Amounts** are as printed on each round's LSC page, stored in cents. Typos are kept in the record's `note`: a stray minus sign, a space inside a number, a state printed as OH for an Oklahoma grantee, "Northwest" for Northeast Legal Aid. Unprinted states (2021) are filled from the organisation's location and noted.
- **AI tag**: LSC's description of the award contains the word AI (case-sensitive, so *aid* and *API* do not count), *artificial intelligence*, *chatbot*, *OpenAI*, *Copilot*, *natural language processing* or *predictive analytics*. Every tag carries a verbatim phrase of 15 words or fewer as evidence. `ai_kind` is read by hand: **builds** (builds, deploys or extends an AI tool), **plans** (the deliverable is a plan, blueprint or assessment for AI) or **considers** (AI named only as a possible feature).
- **Intake tag**: the description contains the word *intake*.
- Organisations are counted by name within a round, with one spelling used for each organisation.

## Limits

- This counts what LSC's descriptions *say*, not what each project built. A project can use AI without saying so, and a one-line mention can overstate AI's role. `ai_kind` and the phrases let you apply a stricter reading.
- 2021-2023 pages print no TIG/SEA/TIP subtypes (2022-2023: none at all), so `category` is not comparable across years.
- Transcribed from LSC's pages as read on 14 October 2026. The 2022 exact total and the 2023 count both match LSC. The other rounds have no exact total to check against. Corrections are welcome as issues.
- Award descriptions are not copied. Follow each round's `list_url` to read them.
- Rounds before 2021 are in LSC's own Airtable base, linked from LSC's [TIG awards page](https://www.lsc.gov/grants/technology-initiative-grant-program/technology-initiative-grant-awards-tig-projects-funded-year), and are not included here.

## Prior work

LSC's press releases name individual AI projects. Its December 2025 report *The Next Frontier* and its AI Peer Learning Labs discuss AI adoption across legal aid. We found no machine-readable list of the 2021-2025 awards and no count of how much TIG money goes to AI projects, or how that share has changed: not on GitHub, not in LSC's releases, and not in legal-tech press coverage (searched 14 October 2026).

## Licence

Code: Apache-2.0 (see LICENSE). Data (`data/`) and this README: CC BY 4.0. Facts are from public pages of the Legal Services Corporation; LSC does not endorse this project.
