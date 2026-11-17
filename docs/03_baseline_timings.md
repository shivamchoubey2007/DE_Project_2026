# Phase 3: Baseline Query Timings

**Team:** AI_Web_Builder | **Team No.:** T0080 | **Section:** A, B, C, E  
**Repository:** [DE_Project_2026](https://github.com/shivamchoubey2007/DE_Project_2026)  
**Database:** PostgreSQL 18.0 · **Schema:** `dream11`  
**Dataset:** 10 tables, 698,657 rows (unmodified seed data)  
**Methodology:** Each query executed 3 times using `EXPLAIN (ANALYZE, BUFFERS)` via `./benchmarks/run_benchmark.sh dream11 baseline`. Write queries wrapped in `BEGIN ... ROLLBACK`. Raw plans saved in `benchmarks/results/baseline/`.

---

## 1. Baseline Timing Table (30 Queries)

| SQL Query | Type | Run 1 (ms) | Run 2 (ms) | Run 3 (ms) | Average (ms) |
|---|---|---:|---:|---:|---:|
| R01: Lobby: upcoming matches with the number of contests and total prize money on offer | READ | 1.202 | 0.540 | 0.505 | 0.749 |
| R02: Create team screen: player pool of match 207 with credits and % of teams that picked each player | READ | 55.696 | 55.591 | 55.810 | 55.699 |
| R03: "My teams": user 1006's teams for match 130 with captain and vice-captain names | READ | 0.066 | 0.070 | 0.069 | 0.068 |
| R04: Contest list for match 207: spots left, biggest prize first | READ | 0.684 | 0.368 | 0.357 | 0.470 |
| R05: Leaderboard: contest 2185 ranked by team points | READ | 0.832 | 0.719 | 0.755 | 0.769 |
| R06: Fair play: teams that break the rules (not exactly 11 players, over 100 credits, or more than 7 from one side) | READ | 90.638 | 92.278 | 92.139 | 91.685 |
| R07: Team preview: points of each player in user 1006's first team for match 130 (captain 2x, vice-captain 1.5x) | READ | 0.898 | 0.169 | 0.213 | 0.427 |
| R08: Match insights: most-picked captains for match 207 | READ | 2.388 | 2.417 | 2.365 | 2.390 |
| R09: Wallet: user 1006's transactions with a running balance | READ | 8.368 | 7.621 | 8.563 | 8.184 |
| R10: Payouts team: withdrawals pending for more than 24 hours (checked at 23:59 on 30 Jun 2026) | READ | 8.944 | 8.856 | 8.974 | 8.925 |
| R11: Compliance: users from states where paid fantasy contests are not allowed who joined paid contests in 2026 | READ | 25.863 | 25.182 | 25.136 | 25.394 |
| R12: Stats hub: top players by average fantasy points in IPL 2026 (at least 5 matches) | READ | 2.449 | 1.780 | 1.733 | 1.987 |
| R13: Finance audit: paid contest entries that have no entry-fee debit in the wallet | READ | 27.447 | 28.347 | 27.316 | 27.703 |
| R14: Product analytics: average fill rate per contest type for completed 2026 matches | READ | 20.465 | 19.415 | 19.211 | 19.697 |
| R15: Leaderboards: top 20 users by winnings in 2026 | READ | 38.471 | 44.705 | 44.999 | 42.725 |
| R16: Player search | READ | 0.391 | 0.373 | 0.392 | 0.385 |
| R17: Fair play: users with more than one team in the same contest | READ | 27.695 | 25.819 | 26.776 | 26.763 |
| R18: Tax compliance: users without verified KYC who have won more than ₹1,000 in total | READ | 18.090 | 18.037 | 18.676 | 18.268 |
| R19: Selection report: in how many teams was each IPL player picked (all time) | READ | 4135.860 | 4135.543 | 4131.326 | 4134.243 |
| R20: Finance: successful deposits per day and running total, June 2026 | READ | 10.865 | 9.306 | 9.876 | 10.016 |
| R21: Engagement: users' head-to-head win rate (at least 3 head-to-head contests) | READ | 10.644 | 11.405 | 11.544 | 11.198 |
| R22: Support console: all wallet transactions, newest first, page 2,001 (25 per page) | READ | 46.944 | 48.518 | 47.850 | 47.771 |
| R23: Login with mobile number | READ | 0.080 | 0.043 | 0.049 | 0.057 |
| R24: Player form: last 5 fantasy scores of every Chennai Super Kings player | READ | 0.919 | 0.910 | 0.909 | 0.913 |
| R25: Refund audit: paid entries in abandoned matches that were never refunded | READ | 16.085 | 16.510 | 26.078 | 19.558 |
| W01: Create team: user 1006 saves team T9 for match 207 | WRITE | 1.398 | 0.962 | 0.878 | 1.079 |
| W02: Join contest: user 1006's newest team for match 207 joins the mega contest of that match | WRITE | 1.081 | 0.688 | 0.629 | 0.799 |
| W03: Wallet: debit the entry fee for the most recent contest entry | WRITE | 0.902 | 0.734 | 0.694 | 0.777 |
| W04: Points engine: recompute total points of every team for match 183 | WRITE | 15.185 | 11.783 | 12.343 | 13.104 |
| W05: Payouts: approve all withdrawals pending for more than 24 hours | WRITE | 9.570 | 9.487 | 8.997 | 9.351 |
| **Total (sum of all 30)** | | **4580.120** | **4578.176** | **4585.162** | **4581.153** |

---

## 2. Query-by-Query Execution Plan & Bottleneck Analysis

### R01: Lobby upcoming matches with contest count & prize money
- **Scan type:** `Seq Scan on contests | Seq Scan on matches | Seq Scan on teams`
- **Why fast/slow:** Relatively fast (0.75 ms) because matches (212 rows) and teams (18 rows) are very small tables, but performs sequential scans on all three tables due to missing indexes on `matches(status)` and `contests(match_id)`.

### R02: Player pool selection percentage for match 207
- **Scan type:** `Seq Scan on user_teams | Index Only Scan using pk_user_team_players on user_team_players | Seq Scan on matches | Seq Scan on players | Seq Scan on teams`
- **Why fast/slow:** Slow (55.70 ms) because it executes a full sequential scan on `user_teams` (39,975 rows) to filter by `match_id = 207` both in the main query and in the scalar subquery, lacking an index on `user_teams(match_id)`.

### R03: User 1006's teams for match 130
- **Scan type:** `Index Scan using uq_user_teams_label on user_teams | Index Scan using pk_players on players`
- **Why fast/slow:** Extremely fast (0.07 ms) because the candidate key `uq_user_teams_label (user_id, match_id, team_label)` provides leading column equality matches on both `user_id` and `match_id`, and player lookups hit the primary key.

### R04: Contest list for match 207 with spots left
- **Scan type:** `Seq Scan on contests | Index Scan using uq_contest_entries_pair on contest_entries`
- **Why fast/slow:** Fast (0.47 ms) as contests has only 2,544 rows, but still performs a sequential scan over `contests` because there is no foreign key index on `contests(match_id)`.

### R05: Leaderboard for contest 2185
- **Scan type:** `Index Only Scan using uq_contest_entries_pair on contest_entries | Index Scan using pk_user_teams on user_teams | Index Scan using pk_users on users`
- **Why fast/slow:** Very fast (0.77 ms) because `uq_contest_entries_pair (contest_id, user_team_id)` provides an index scan on `contest_id = 2185`, and subsequent joins use PK lookups.

### R06: Fair play rule violations (11 players, 100 credits, max 7 per side)
- **Scan type:** `Seq Scan on user_teams | Index Only Scan using pk_user_team_players on user_team_players | Seq Scan on players`
- **Why fast/slow:** High latency (91.69 ms) due to a full sequential scan on `user_teams` for `match_id = 183`, joined with an expensive nested `CROSS JOIN LATERAL` subquery recalculating player counts per team without dedicated indexes.

### R07: Team preview player scores with captain/vice-captain multipliers
- **Scan type:** `Index Scan using uq_user_teams_label on user_teams | Index Only Scan using pk_user_team_players on user_team_players | Index Scan using pk_players on players | Index Scan using pk_player_match_stats on player_match_stats`
- **Why fast/slow:** Very fast (0.43 ms) because `uq_user_teams_label` filters directly to the single team row (`user_id=1006, match_id=130, team_label='T1'`), and remaining joins use primary key lookups.

### R08: Most-picked captains for match 207
- **Scan type:** `Seq Scan on user_teams | Seq Scan on players`
- **Why fast/slow:** Takes 2.39 ms; performs a full sequential scan over all 39,975 `user_teams` rows because `user_teams(match_id)` is unindexed.

### R09: User 1006 wallet transactions running balance
- **Scan type:** `Seq Scan on wallet_transactions`
- **Why fast/slow:** Takes 8.18 ms; scans all 118,343 rows of `wallet_transactions` to filter for `user_id = 1006 AND status = 'SUCCESS'`, lacking an index on `(user_id, status)`.

### R10: Payouts pending withdrawals > 24 hours
- **Scan type:** `Seq Scan on wallet_transactions`
- **Why fast/slow:** Takes 8.93 ms; performs a full sequential scan on `wallet_transactions` (118,343 rows) filtering on `txn_type = 'WITHDRAWAL'` and `status = 'PENDING'`.

### R11: Compliance: restricted state users in paid contests (2026)
- **Scan type:** `Seq Scan on contest_entries | Seq Scan on user_teams | Seq Scan on users | Seq Scan on contests`
- **Why fast/slow:** Takes 25.39 ms; performs sequential scans across four major tables (`users`, `user_teams`, `contest_entries`, `contests`) and joins them via hash joins due to lack of FK and date indexes.

### R12: Stats hub top players IPL 2026
- **Scan type:** `Seq Scan on player_match_stats | Seq Scan on matches | Seq Scan on players | Seq Scan on teams`
- **Why fast/slow:** Takes 1.99 ms; scans `player_match_stats` (4,444 rows) and `matches` (212 rows); fast due to small data volume, but relies entirely on sequential scans.

### R13: Finance audit: paid entries with no wallet debit
- **Scan type:** `Seq Scan on contest_entries | Seq Scan on wallet_transactions | Seq Scan on contests`
- **Why fast/slow:** Takes 27.70 ms; performs sequential scans on `contest_entries` (42,746 rows) and `wallet_transactions` (118,343 rows). Also suffers from the `NOT IN (SELECT reference_entry_id ...)` NULL trap which returns 0 rows.

### R14: Product analytics: fill rate per contest type (2026)
- **Scan type:** `Seq Scan on contests | Seq Scan on matches | Index Scan using uq_contest_entries_pair on contest_entries`
- **Why fast/slow:** Takes 19.70 ms; scans all `matches` and `contests`, applying hash aggregates over joined contest entries.

### R15: Top 20 users by winnings in 2026
- **Scan type:** `Seq Scan on contest_entries | Seq Scan on user_teams | Seq Scan on users`
- **Why fast/slow:** Takes 42.73 ms; scans 42,746 contest entries filtering on date `joined_at >= '2026-01-01'` and hash joins with `user_teams` and `users` without index support.

### R16: Player search by name
- **Scan type:** `Seq Scan on players | Seq Scan on teams`
- **Why fast/slow:** Fast (0.39 ms) because `players` has only 450 rows, but `ILIKE '%sharma%'` forces a full sequential scan without a trigram GIN index.

### R17: Fair play multi-team entries in same contest
- **Scan type:** `Seq Scan on contest_entries | Seq Scan on user_teams`
- **Why fast/slow:** Takes 26.76 ms; sequentially scans `contest_entries` and `user_teams` and performs a heavy hash aggregation to detect multiple entries per user.

### R18: Tax compliance: non-verified users with > ₹1,000 winnings
- **Scan type:** `Seq Scan on wallet_transactions | Seq Scan on users`
- **Why fast/slow:** Takes 18.27 ms; scans all 118,343 `wallet_transactions` to filter for `WINNINGS` and `SUCCESS`, then hash joins with `users`.

### R19: Selection report: all-time pick count for IPL players
- **Scan type:** `Seq Scan on players | Seq Scan on teams | Seq Scan on user_team_players`
- **Why fast/slow:** **Extreme bottleneck (4,134.24 ms, >90% of entire benchmark)**. The correlated subquery `(SELECT count(*) FROM user_team_players utp WHERE utp.player_id = p.player_id)` executes for every franchise player (~225 players). Because `pk_user_team_players` has leading column `user_team_id`, each player lookup forces a full sequential scan of 439,925 rows in `user_team_players` (over 98 million row examinations in total).

### R20: Successful deposits per day (June 2026)
- **Scan type:** `Seq Scan on wallet_transactions`
- **Why fast/slow:** Takes 10.02 ms; sequentially scans all 118,343 rows of `wallet_transactions` and filters on type, status, and cast date `created_at::date`.

### R21: Engagement head-to-head win rate
- **Scan type:** `Seq Scan on user_teams | Seq Scan on contest_entries | Seq Scan on contests`
- **Why fast/slow:** Takes 11.20 ms; sequentially scans `contests` (filtered by `HEAD_TO_HEAD`), joining with `contest_entries` and `user_teams` via hash joins.

### R22: Support console wallet transactions pagination (page 2,001)
- **Scan type:** `Seq Scan on wallet_transactions`
- **Why fast/slow:** Takes 47.77 ms; scans and sorts the entire `wallet_transactions` table (118,343 rows) by `created_at DESC` to discard the first 50,000 rows (`OFFSET 50000 LIMIT 25`).

### R23: Login with mobile number
- **Scan type:** `Index Scan using uq_users_phone on users`
- **Why fast/slow:** Fastest query in the workload (0.057 ms) because `uq_users_phone` allows a direct B-tree point lookup on the unique phone number.

### R24: Player form: last 5 fantasy scores of CSK players
- **Scan type:** `Seq Scan on player_match_stats | Seq Scan on players | Seq Scan on teams | Seq Scan on matches`
- **Why fast/slow:** Takes 0.91 ms; data volume is small enough to fit in cache, but scans all four tables sequentially and sorts for windowing.

### R25: Refund audit: paid entries in abandoned matches without refund
- **Scan type:** `Seq Scan on wallet_transactions | Seq Scan on contest_entries | Seq Scan on user_teams | Seq Scan on matches | Seq Scan on contests`
- **Why fast/slow:** Takes 19.56 ms; evaluates a `NOT EXISTS` subquery against `wallet_transactions` while joining five tables via sequential scans.

### W01: Create fantasy team for match 207
- **Scan type:** `Seq Scan on matches`
- **Why fast/slow:** Fast (1.08 ms); scans `matches` to find `match_id = 207` and inserts 1 row into `user_teams`.

### W02: Join mega contest for match 207
- **Scan type:** `Index Scan using pk_user_teams on user_teams | Seq Scan on contests`
- **Why fast/slow:** Takes 0.80 ms; uses `pk_user_teams` to find the latest team and sequentially scans `contests` for the match's mega contest.

### W03: Wallet debit entry fee for latest entry
- **Scan type:** `Index Only Scan using pk_contest_entries on contest_entries | Index Scan using pk_contest_entries on contest_entries | Index Scan using pk_contests on contests | Index Scan using pk_user_teams on user_teams`
- **Why fast/slow:** Fast (0.78 ms); uses primary key index scans across `contest_entries`, `contests`, and `user_teams`.

### W04: Points engine: recompute total points for match 183
- **Scan type:** `Seq Scan on user_teams | Index Only Scan using pk_user_team_players on user_team_players | Bitmap Heap Scan on player_match_stats | Bitmap Index Scan on pk_player_match_stats`
- **Why fast/slow:** Takes 13.10 ms; updates 278 teams for match 183 after aggregating points from `user_team_players` and `player_match_stats`.

### W05: Payouts: approve pending withdrawals > 24 hours
- **Scan type:** `Seq Scan on wallet_transactions`
- **Why fast/slow:** Takes 9.35 ms; performs a full sequential scan of `wallet_transactions` to locate and update pending withdrawal records.

---

## 3. Key Observations & Optimization Plan for Phase 4

1. **R19 is the single biggest bottleneck:** 4,134 ms out of 4,581 ms total (~90.2% of total runtime). Adding a secondary index on `user_team_players (player_id)` or rewriting the query from a correlated subquery to a grouped `JOIN` will reduce execution time by over 99%.
2. **Missing Foreign Key Indexes:** PostgreSQL does not automatically index foreign key columns. Queries filtering on `user_teams(match_id)`, `contests(match_id)`, and `wallet_transactions(user_id)` are forced to perform full sequential scans on 40k–118k rows.
3. **Compound Indexes for State & Status:** `wallet_transactions(txn_type, status, created_at)` will directly accelerate R10, R18, R20, R22, and W05.
4. **Pagination Optimization (R22):** `OFFSET 50000` scans and sorts 50,000 rows. A covering index on `wallet_transactions(created_at DESC)` will enable fast index-directed retrieval.
5. **Logic Correction for R13:** `NOT IN (SELECT reference_entry_id FROM wallet_transactions)` fails in SQL three-valued logic because `reference_entry_id` contains 63,000 `NULL` values. Rewriting to `NOT EXISTS` or filtering `WHERE reference_entry_id IS NOT NULL` will fix the audit accuracy and improve performance.
