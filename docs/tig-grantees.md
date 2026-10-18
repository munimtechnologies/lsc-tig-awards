# Who wins LSC's technology grants: organizations and repeat winners, 2014-2025

[tig-states.md](tig-states.md) adds up LSC's Technology Initiative Grants (TIG) by state. This page counts the organizations behind them: how many different legal aid organizations won a TIG in the 11 complete rounds from 2014 to 2025, how many rounds each won, and how many of each round's winners were new. LSC never published a list for 2015, so 2015 is in no count here. [tig-history.md](tig-history.md) checks each round's list against LSC's own counts.

    python tig_grantees.py            # one row per organization, most rounds first
    python tig_grantees.py --rounds   # organizations and newcomers per round
    python tig_grantees.py --summary  # the figures on this page, as JSON

`test_tig_grantees.py` pins every count below, counted by hand from the lists. `test_tig_grantees_doc.py` checks each figure on this page against the code.

## How names are matched

The grants are the lists `tig_states.py` uses (one row per grantee for 2014), plus the 2025 grant to Legal Services of Greater Miami that LSC listed without an amount: it counts as a round won, not as dollars. Two names are one organization when they differ only by a leading "The" or a trailing "Inc.", or when [data/grantee_names.json](../data/grantee_names.json) pairs them. It holds 16 pairs:

- 9 spellings of one name, such as "Legal Aid of Chicago" (2024) for Legal Aid Chicago and "Philadelphia Legal Assistance" (2023) for Philadelphia Legal Assistance Center.
- 1 short form: LSC's 2014 list prints "Idaho Legal Services". Idaho is one LSC service area, served by Idaho Legal Aid Services, which won TIGs in 2016 and 2024.
- 6 renames, each with the organization's own page as the source: Legal Assistance Foundation (2014, 2018) and LAF (2015) to Legal Aid Chicago; Land of Lincoln Legal Assistance Foundation to Land of Lincoln Legal Aid (2019); Legal Aid Society of Orange County to Community Legal Aid SoCal (2019); Legal Advice & Referral Center to 603 Legal Aid (2021, on merging with the New Hampshire Bar Association's Pro Bono Referral Program); Legal Aid Service of Northeastern Minnesota to Justice North (2023).

Each organization goes by the name LSC printed in its latest round. No pair joins two names within one round: each round has as many organizations as distinct names, the counts tig-history.md checks.

## Findings

- **110 different organizations won at least one TIG in the 11 complete rounds**, 301 round wins in all. Counting names instead (no short form or rename joined) gives 115.
- **No organization won all 11 rounds.** Montana Legal Services Association won 10 (all but 2019), Northwest Justice Project 9 and Legal Aid Chicago 8.
- **32 organizations won once. 19 won five rounds or more and hold 119 of the 301 round wins (39.5%).**
- **Repeat winners got larger grants.** The 19 that won five rounds or more received $23,613,472 of the $48,139,618 (49.1%), against 39.5% of round wins: $198,433 per round won, against $112,382 for the 32 that won once, who received 7.5% of the dollars for 10.6% of round wins. The 19 include Ohio State Legal Services, whose seven LawHelp Interactive grants ([tig-national.md](tig-national.md)) come to $4,648,850; without those, the 19 received 43.6% of the rest.
- **61 organizations won in both periods.** 79 won in 2014-2019 and 92 in 2020-2025: of the 92, 31 had no TIG in any complete round from 2014 to 2019, and of the 79, 18 have had none since.
- **Fewer newcomers since 2020.** From 2020 to 2025, 4 to 7 of each round's 24 to 29 organizations had won no complete round since 2014: 31 of 169 round wins (18.3%). From 2016 to 2019 it was 49 of 102 (48.0%), but those rounds look back over fewer years.

| Rounds won (of 11) | Organizations |
|---|---|
| 10 | 1 |
| 9 | 1 |
| 8 | 1 |
| 7 | 4 |
| 6 | 4 |
| 5 | 8 |
| 4 | 8 |
| 3 | 16 |
| 2 | 35 |
| 1 | 32 |

The 11 organizations that won six rounds or more:

| Organization | State | Rounds won | Rounds missed |
|---|---|---|---|
| Montana Legal Services Association | MT | 10 | 2019 |
| Northwest Justice Project | WA | 9 | 2023, 2025 |
| Legal Aid Chicago | IL | 8 | 2016, 2017, 2022 |
| Land of Lincoln Legal Aid | IL | 7 | 2017, 2018, 2019, 2020 |
| Michigan Advocacy Program | MI | 7 | 2014, 2018, 2023, 2024 |
| Ohio State Legal Services | OH | 7 | 2022, 2023, 2024, 2025 |
| Philadelphia Legal Assistance Center | PA | 7 | 2014, 2021, 2022, 2025 |
| Legal Services of Greater Miami | FL | 6 | 2016, 2017, 2019, 2023, 2024 |
| Atlanta Legal Aid Society | GA | 6 | 2014, 2016, 2018, 2022, 2024 |
| Legal Aid of the Bluegrass | KY | 6 | 2014, 2016, 2017, 2020, 2021 |
| Pine Tree Legal Assistance | ME | 6 | 2016, 2019, 2023, 2024, 2025 |

Organizations and newcomers per round ("new" means no complete round won since 2014, so all of 2014's 30 are new by construction):

| Round | Organizations | New since 2014 |
|---|---|---|
| 2014 | 30 | 30 |
| 2016 | 27 | 14 |
| 2017 | 22 | 9 |
| 2018 | 24 | 12 |
| 2019 | 29 | 14 |
| 2020 | 24 | 4 |
| 2021 | 29 | 5 |
| 2022 | 29 | 6 |
| 2023 | 29 | 7 |
| 2024 | 29 | 4 |
| 2025 | 29 | 5 |

The seven organizations LSC's releases name for 2015 all won at least one complete round too.

## The base: LSC's 2025 grantees

Only organizations that hold an LSC basic field grant may apply for a TIG or a PBIF grant, so the base for the counts on this page and in [pbif-history.md](pbif-history.md) is LSC's grantees. `grantee_base.py` takes the 2025 grantees from [data/basic_field_2025.json](../data/basic_field_2025.json), LSC's Notice of Intent to Award for 2025 (89 FR 88814) with its estimated annualized 2025 funding, and matches each one to the TIG organizations above and to the PBIF organizations. Service areas that print the same name are one grantee, counted in the state that holds most of its dollars.

    python grantee_base.py            # one row per 2025 grantee
    python grantee_base.py --summary  # the figures in this section, as JSON

`test_grantee_base.py` pins these counts, checked by hand against the notice. `test_grantee_base_doc.py` checks this section against the code.

- **130 organizations hold a 2025 basic field grant, and 114 of them (87.7%) won a TIG or a PBIF grant from 2014 to 2025**: 74 won both, 34 a TIG only and 6 PBIF only. All 80 PBIF organizations are among the 130.
- **16 won neither.** Together they hold $31,906,185 (6.2%) of the $513,988,916 in estimated 2025 funding for the 130. The largest of them, MidPenn Legal Services, has $3,765,838; every grantee with more won at least one of the two programs.
- **Two TIG organizations match no 2025 grantee.** Ohio State Legal Services (7 rounds) has no 2025 service area under its name. Memphis Area Legal Services (2 rounds) is named only in TN-4, the one service area the notice leaves undecided ("Memphis Area Legal Services, Inc. or West Tennessee Legal Services, Inc", $2,111,084), which counts as no grantee here. The other 292 of the 301 round wins went to 2025 grantees.
- **The share of winners is higher for larger grantees.** Below $3M, 56 of 69 grantees (81.2%) won at least one of the two programs; from $3M up, 58 of 61 (95.1%) did, including all 24 with $6M or more. Basic field funding mostly follows the number of people in poverty in each service area ([LSC's allocation process](https://www.lsc.gov/grants/basic-field-grant/basic-field-allocation-process)), so a tier measures size, not performance, and the lists do not say why the share rises with it.

| Estimated 2025 basic field funding | Grantees | Won a TIG | Won PBIF | Won both | Won neither | Won either |
|---|---|---|---|---|---|---|
| under $1M | 12 | 8 | 5 | 3 | 2 | 83.3% |
| $1M to $3M | 57 | 43 | 33 | 30 | 11 | 80.7% |
| $3M to $6M | 37 | 34 | 27 | 27 | 3 | 91.9% |
| $6M and over | 24 | 23 | 15 | 14 | 0 | 100.0% |

Each tier includes its lower bound and excludes its upper one.

The 16 that won neither:

| Organization | State | Basic field 2025 | Service areas |
|---|---|---|---|
| MidPenn Legal Services | PA | $3,765,838 | PA-25 |
| South Jersey Legal Services | NJ | $3,695,134 | MNJ, NJ-20 |
| Three Rivers Legal Services | FL | $3,382,885 | FL-14 |
| Legal Aid Society of Greater Cincinnati | OH | $2,369,019 | OH-18 |
| Legal Services of Southern Missouri | MO | $2,233,446 | MO-7 |
| Micronesian Legal Services Corporation | MP | $2,223,505 | GU-1, MP-1 |
| Neighborhood Legal Services | NY | $2,032,390 | NY-24 |
| Dakota Plains Legal Services | SD | $1,984,652 | NSD-1, SD-4 |
| Central Jersey Legal Services | NJ | $1,869,464 | NJ-17 |
| Summit Legal Aid | PA | $1,632,271 | PA-27 |
| South Coastal Counties Legal Services | MA | $1,579,769 | MA-12 |
| Essex-Newark Legal Services Project | NJ | $1,378,205 | NJ-8 |
| Rhode Island Legal Services | RI | $1,347,809 | RI-1 |
| Legal Services of Northern Michigan | MI | $1,199,133 | MI-9 |
| Northwestern Legal Services | PA | $912,334 | PA-26 |
| Community Law Office | PR | $300,331 | PR-2 |

LSC has built tracks for this group. Its 2026 PBIF Project Incubation Grants are for newcomers: "Project Incubation Grants are available to organizations that have never received PBIF funding", and to organizations with no PBIF grant since 2019 or an unsuccessful 2025 application ([PBIF program description](https://www.lsc.gov/grants/pro-bono-innovation-fund/pbif-program-description)). LSC's December 2019 PBIF notice ([84 FR 67477](https://www.govinfo.gov/content/pkg/FR-2019-12-10/html/2019-26499.htm)) said its Transformation Grants were "primarily intended for LSC grantees who have been unsuccessful applying for Project Grants" or had never applied. Its 2018 TIG notice ([FR Doc. 2018-02435](https://www.govinfo.gov/content/pkg/FR-2018-02-07/html/2018-02435.htm)) offered Technology Improvement Projects of up to $25,000, for which "only LSC grantees that have not had a TIG award in the last five years (since 2013) are eligible". The lists name winners, not applicants, so whether the 16 applied is not known from them.

## Limits

- Since 2014 only. The TIG program began in 2000, so "new" means no TIG in a complete round since 2014, not a first TIG ever, and a round's look-back grows from one round (2016) to ten (2025).
- Rounds, not grants: an organization with two grants in one round wins that round once. The 2014 list has one row per grantee.
- Dollars per round won count Legal Services of Greater Miami's 2025 round, which LSC listed without an amount, as a round with no dollars. The lists do not say why some grants are larger, and project scope is not compared here.
- Mergers between grantees are not followed: two grantees that later merged count as two. A rename joins two names only where data/grantee_names.json lists it with the organization's own page. The Idaho short form rests on Idaho having one LSC grantee, not on a statement by LSC.
- Only organizations holding an LSC basic field grant may apply for a TIG, so the pool is LSC's grantees, not all legal aid organizations.
- The base is the 2025 list. An organization that won while it was a grantee and is not one in 2025 under the same name is in no group, and a grantee formed by a merger counts only under its 2025 name, without its predecessors' wins. The basic field figures are LSC's estimates in the notice, not final awards.
- "Won neither" says nothing about applying. The tier table shows how the share of winners changes with basic field funding, not why.
- Information about public grants, compiled by MV2 of Munim, Inc. with AI agents working in his name. Not legal advice.
