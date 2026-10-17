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

## Limits

- Since 2014 only. The TIG program began in 2000, so "new" means no TIG in a complete round since 2014, not a first TIG ever, and a round's look-back grows from one round (2016) to ten (2025).
- Rounds, not grants: an organization with two grants in one round wins that round once. The 2014 list has one row per grantee.
- Mergers between grantees are not followed: two grantees that later merged count as two. A rename joins two names only where data/grantee_names.json lists it with the organization's own page. The Idaho short form rests on Idaho having one LSC grantee, not on a statement by LSC.
- Only organizations holding an LSC basic field grant may apply for a TIG, so the pool is LSC's grantees, not all legal aid organizations.
- Information about public grants, compiled by MV2 of Munim, Inc. with AI agents working in his name. Not legal advice.
