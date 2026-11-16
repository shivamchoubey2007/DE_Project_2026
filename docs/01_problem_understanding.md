# Phase 1: Problem Understanding

**Team:** AI_Web_Builder | **Team No.:** T0080 | **Sections:** A, B, C, E

## Overall picture

Dream11 users pick 11 players for a real match, join paid contests from their wallet, and win money based on how those players score. All of this runs on one database that has no documented schema, so the first job is to rebuild it properly. The second is to make sure two kinds of work don't get in each other's way. On one side are match-day screens where a user is waiting, and on the other are audits, payouts and reports where being correct matters more than being instant.

## Problems, stakeholders and type

| # | What the business needs | Who is affected | Type |
|---|---|---|---|
| P1 | Lobby, player pool, contest list and most-picked captains should open instantly. Most users build teams in the last few minutes before a match locks, so this is the busiest time. (R01, R02, R04, R08) | Fantasy players, user-app team | Customer-facing / real-time |
| P2 | Saved teams, team preview, leaderboard and wallet history should stay quick while a match is live and everyone keeps refreshing. (R03, R05, R07, R09) | Fantasy players, support | Customer-facing / real-time |
| P3 | Saving a team, joining a contest and debiting the fee should be fast, and the three steps must agree with each other. No duplicate entries, no wrong charges. (W01, W02, W03) | Contest engine, players, finance | Customer-facing / real-time |
| P4 | Find teams that break the selection rules (not 11 players, over 100 credits, more than 7 from one side) and users who put several teams into the same contest. (R06, R17) | Fair-play team | Reporting / analytics |
| P5 | Find paid entries that have no entry-fee debit. Right now this returns nothing, which finance rightly finds hard to believe, so this looks like a wrong-result problem and not a speed problem. (R13) | Finance and audit | Reporting / analytics |
| P6 | Track withdrawals pending for over 24 hours, users from restricted states in paid contests, KYC/TDS cases and abandoned-match entries that never got a refund. (R10, R11, R18, R25, W05) | Payouts, finance, compliance, support | Reporting / analytics (W05 is time-sensitive payout work) |
| P7 | Recompute team scores after a match ends, and keep player averages, recent form and pick counts from timing out. (R12, R19, R24, W04) | Points engine, stats team | Reporting / analytics (W04 is an operational update) |
| P8 | Fill rate, winnings, head-to-head and deposit reports have to survive 20× more users. Support's transaction console (R22) is in the same bucket. (R14, R15, R20, R21, R22) | Product, finance, support | Reporting / analytics |
| P8 (lookups) | Player search and login by mobile number sit under P8 in the brief, but a user waits on both. (R16, R23) | Players, support | Customer-facing / real-time |

Real-time problems (P1 to P3) get the strictest targets, since a delay is visible to the user straight away. The rest scan large tables, so we expect indexes and query rewrites to help the most there.

## Assumptions

1. The ten CSV files and `workload_30.sql` define the scope of the project.
2. Match-day screens and actions are latency-sensitive. Reports can be slower, but their numbers must be right.
3. The seed data is a true copy of production. If something looks odd, for example free contests or a match with status `LIVE`, we treat it as real data and fit the constraints to it. We will not delete the rows.
4. P5 is most likely a NULL issue. In the seed data, deposits, bonuses and withdrawals (63,000 of 118,343 wallet rows) have no `reference_entry_id`, so it cannot be a mandatory column. We think this is also why R13 returns nothing (`NOT IN` against a column that contains NULLs), and we will check it in Phase 4.
5. Rules like exactly 11 players, 100 credits and at most 7 per team involve many rows, so a plain row-level CHECK cannot enforce them. We assume the app or a trigger does that, and R06 only audits it afterwards.
6. Money is in rupees and stored as exact decimals. Timestamps carry the +05:30 offset, so they are stored with time zone.
7. The restricted states in R11 (AS, OD, TG, AP) are taken as given in the query. We are not making any legal claim about them.
8. Tuning must not change results. The one exception is a query that is itself wrong.