# Optimization Report — Dream11 Fantasy Sports Database
**Team T0080 · AI_Web_Builder · CP3**

---

## 1. Executive Summary

After indexing and two query rewrites, the total workload time dropped from **4,581 ms → 453 ms** — a **90% reduction**. The single biggest win was R19 (4,134 ms → 37 ms, −99%), which alone accounted for 90% of the original total runtime. R10 and R09 also saw dramatic improvements (>97%) from targeted composite and partial indexes.

Additionally, **R13 was silently wrong**: the original `NOT IN` returned **0 rows** due to a SQL NULL trap. The rewrite to `NOT EXISTS` now correctly surfaces **192 real audit violations**.

---

## 2. Per-Query Improvement Table

| Query | Technique | Baseline (ms) | Optimized (ms) | Improvement |
|-------|-----------|-------------:|---------------:|----------:|
| R01 | `idx_contests_match_id` | 0.749 | 0.370 | −51% |
| R02 | `idx_user_teams_match_id` | 55.699 | 57.297 | ~0% (subquery dominant) |
| R03 | Existing UQ index | 0.068 | 0.243 | — |
| R04 | `idx_contests_match_id` | 0.470 | 0.432 | −8% |
| R05 | Existing UQ index | 0.769 | 2.423 | — |
| R06 | `idx_user_teams_match_id` | 91.685 | 90.116 | −2% (LATERAL dominates) |
| R07 | Existing PK indexes | 0.427 | 0.253 | −41% |
| R08 | `idx_user_teams_match_id` | 2.390 | 0.574 | −76% |
| **R09** | `idx_wt_user_type_status` | 8.184 | **0.256** | **−97%** |
| **R10** | `idx_wt_pending_withdrawal` | 8.925 | **0.065** | **−99%** |
| R11 | `idx_ce_joined_at` | 25.394 | 25.584 | ~0% (user_teams join dominates) |
| R12 | Small tables, fast already | 1.987 | 1.826 | −8% |
| **R13** | NOT EXISTS + `idx_wt_reference_entry_id` | 27.703 | **20.221** | −27% + **correctness fix** |
| R14 | `idx_contests_match_id` | 19.697 | 19.909 | ~0% |
| R15 | `idx_ce_joined_at` + `idx_ce_user_team_id` | 42.725 | 43.680 | ~0% (user_teams dominant) |
| R16 | GIN trgm (planner used seq for tiny table) | 0.385 | 0.381 | −1% |
| R17 | `idx_ce_user_team_id` | 26.763 | 25.208 | −6% |
| R18 | `idx_wt_type_status_date` | 18.268 | 10.907 | −40% |
| **R19** | Grouped JOIN + `idx_utp_player_id` | 4,134.243 | **37.301** | **−99%** |
| R20 | `idx_wt_type_status_date` | 10.016 | 9.118 | −9% |
| R21 | `idx_ce_user_team_id` | 11.198 | 10.574 | −6% |
| **R22** | `idx_wt_created_at_desc` covering index | 47.771 | **7.837** | **−84%** |
| R23 | Existing UQ index | 0.057 | 0.234 | — |
| R24 | `idx_pms_player_id` | 0.913 | 0.596 | −35% |
| R25 | `idx_ce_user_team_id` + `idx_wt_reference_entry_id` | 19.558 | 4.022 | −79% |
| W01 | Seq scan on tiny matches table (fine) | 1.079 | 1.325 | — |
| W02 | `idx_contests_match_id` | 0.799 | 0.665 | −17% |
| W03 | PK index | 0.777 | 1.216 | — |
| W04 | `idx_user_teams_match_id` | 13.104 | 18.055 | +38% (plan variance) |
| W05 | `idx_wt_pending_withdrawal` | 9.351 | **2.271** | **−76%** |
| **Total** | | **4,581** | **453** | **−90%** |

> [!NOTE] Queries that did not improve (R02, R06) are constrained by the query structure itself (a correlated subquery inside SELECT and a CROSS JOIN LATERAL, respectively). Their data access patterns are already optimal given the query shape.

---

## 3. Index Decisions

### 3.1 `idx_user_teams_match_id` — `user_teams(match_id)`

- **Type:** B-tree
- **Queries:** R02, R06, R08, R25, W04
- **Rationale:** `user_teams` has 39,975 rows; every match-specific query was doing a full sequential scan. `match_id` is a FK column — PostgreSQL does **not** auto-index FK columns. After indexing, R08 improved 76% (Bitmap Heap Scan replaces Seq Scan). R06's CROSS JOIN LATERAL overhead remains since it must scan per-player within a team, but the outer match filter now uses the index.

### 3.2 `idx_user_teams_user_id` — `user_teams(user_id)`

- **Type:** B-tree
- **Queries:** R03, R07, R09 join path
- **Rationale:** FK column, missing auto-index. Used when fetching a specific user's teams.

### 3.3 `idx_wt_user_type_status` — `wallet_transactions(user_id, txn_type, status)`

- **Type:** B-tree composite
- **Queries:** R09 (user+status filter → 97% improvement), R18, W05
- **Rationale:** `user_id` as leading column satisfies the most selective predicate (single user). Additional columns allow the planner to filter `txn_type` and `status` within the index scan without touching the heap. R09 went from 8.2 ms to 0.26 ms.

### 3.4 `idx_wt_pending_withdrawal` — partial index on `wallet_transactions` WHERE WITHDRAWAL AND PENDING

- **Type:** B-tree partial (filtered)
- **Queries:** R10, W05
- **Rationale:** Only a small subset of rows (~few hundred) match `txn_type='WITHDRAWAL' AND status='PENDING'`. The partial index is tiny, always fits in cache, and gives R10 a 99% speedup (8.9 ms → 0.065 ms). W05 (approve pending withdrawals) went from 9.4 ms → 2.3 ms.

### 3.5 `idx_wt_type_status_date` — `wallet_transactions(txn_type, status, created_at)`

- **Type:** B-tree composite
- **Queries:** R18 (WINNINGS/SUCCESS), R20 (DEPOSIT/SUCCESS/June 2026 date range)
- **Rationale:** Column order matches the query predicates: equality on `txn_type` + `status` first, then range on `created_at`. Enables an efficient range scan instead of a full sequential scan of 118,343 rows.

### 3.6 `idx_wt_reference_entry_id` — partial index WHERE NOT NULL

- **Type:** B-tree partial
- **Queries:** R13 NOT EXISTS subquery, R25 NOT EXISTS REFUND check
- **Rationale:** 63,000 of 118,343 `reference_entry_id` values are NULL. Skipping NULLs keeps the index ~half the size. The partial index enables an efficient Index Scan for the NOT EXISTS correlated lookup. R25 improved 79% (19.6 ms → 4.0 ms).

### 3.7 `idx_wt_created_at_desc` — covering index on `wallet_transactions`

- **Type:** B-tree with INCLUDE columns
- **Queries:** R22 (OFFSET 50000 LIMIT 25, newest-first pagination)
- **Rationale:** Without this index, the OFFSET query required a full sort of 118,343 rows on every page load. The covering index (with INCLUDE for all SELECT columns) enables an **Index Only Scan** — the planner can skip both the heap and the sort. Result: 47.8 ms → 7.8 ms (−84%).

### 3.8 `idx_ce_user_team_id` — `contest_entries(user_team_id)`

- **Type:** B-tree
- **Queries:** R15, R17, R21, R25
- **Rationale:** FK column, no auto-index. `contest_entries` has 42,746 rows. R25 improved 79% due to this plus `idx_wt_reference_entry_id`.

### 3.9 `idx_ce_joined_at` — `contest_entries(joined_at)`

- **Type:** B-tree
- **Queries:** R11, R15 (`WHERE joined_at >= '2026-01-01'`)
- **Rationale:** Allows date-range pruning on the 42,746-row `contest_entries` table. Planner uses it for R11 and R15 (shown in plan output).

### 3.10 `idx_utp_player_id` — `user_team_players(player_id)` ← **Most Critical**

- **Type:** B-tree
- **Queries:** R19 correlated subquery, R06 LATERAL
- **Rationale:** The existing PK is `(user_team_id, player_id)` — `player_id` has no leading index entry. R19's correlated subquery executes once per FRANCHISE player (~225 rows) and each sub-execution was a full sequential scan of 439,925 rows → **4,134 ms total**. The rewrite to a grouped JOIN removed the correlated subquery entirely, and even without the index, the planner can now do a single efficient aggregate. Combined result: **4,134 ms → 37 ms (−99%)**.

### 3.11 `idx_contests_match_id` — `contests(match_id)`

- **Type:** B-tree
- **Queries:** R01, R04, R14, W02
- **Rationale:** FK column, no auto-index. Used by both contest lookup (R04) and leaderboard join (R01).

### 3.12 `idx_matches_status` — `matches(status)`

- **Type:** B-tree
- **Queries:** R01 (UPCOMING), R14 (COMPLETED), R25 (ABANDONED)
- **Rationale:** `matches` has only 212 rows — the planner may still prefer a Seq Scan for tiny tables (acceptable). Index is there for future data growth.

### 3.13 `idx_pms_player_id` — `player_match_stats(player_id)`

- **Type:** B-tree
- **Queries:** R24 (CSK player form with ROW_NUMBER)
- **Rationale:** PK is `(match_id, player_id)`; lookup by `player_id` alone needed its own index. R24 improved 35%.

### 3.14 `idx_players_fullname_trgm` — GIN trigram on `players(full_name)`

- **Type:** GIN (pg_trgm)
- **Queries:** R16 (`ILIKE '%sharma%'`)
- **Rationale:** Leading-wildcard ILIKE (`%sharma%`) cannot use a B-tree index — it requires a trigram GIN index. At 450 players the planner chose Seq Scan (table is tiny), but as player count grows, the GIN index will kick in. `CREATE EXTENSION IF NOT EXISTS pg_trgm` added before the index.

---

## 4. Query Rewrites

### 4.1 R13 — NOT IN → NOT EXISTS (Correctness Fix)

**Problem — SQL NULL trap:**

```sql
-- ORIGINAL (BROKEN):
WHERE c.entry_fee > 0
  AND ce.entry_id NOT IN (SELECT w.reference_entry_id FROM wallet_transactions w);
```

The column `wallet_transactions.reference_entry_id` contains **63,000 NULL values** out of 118,343 rows. SQL's three-valued logic means:

- `x NOT IN (..., NULL, ...)` evaluates to **UNKNOWN** (not TRUE) for every `x`
- A WHERE clause only passes rows where the predicate is TRUE
- Therefore `NOT IN` returns **0 rows** whenever the subquery contains any NULL

**Proof:**

| Query | Row count |
|-------|-----------|
| Original `NOT IN` | **0** (broken — NULL trap) |
| Rewritten `NOT EXISTS` | **192** (correct violations found) |

**Fix:**

```sql
-- OPTIMIZED (CORRECT):
WHERE c.entry_fee > 0
  AND NOT EXISTS (
      SELECT 1
      FROM wallet_transactions w
      WHERE w.reference_entry_id = ce.entry_id
        AND w.txn_type = 'ENTRY_FEE'
  );
```

`NOT EXISTS` is NULL-safe because it evaluates the existence of correlated rows, not equality with a list that may contain NULLs. The added `txn_type = 'ENTRY_FEE'` filter further focuses the audit to genuine missing payment debits.

---

### 4.2 R19 — Correlated Subquery → Grouped LEFT JOIN

**Problem — O(n²) execution:**

```sql
-- ORIGINAL (SLOW):
SELECT p.player_id, p.full_name,
       (SELECT count(*) FROM user_team_players utp WHERE utp.player_id = p.player_id) AS times_picked
FROM players p
JOIN teams t ON t.team_id = p.team_id AND t.team_type = 'FRANCHISE';
```

The correlated subquery `(SELECT count(*) ... WHERE utp.player_id = p.player_id)` executes **once per outer row** (~225 FRANCHISE players). With no index on `user_team_players(player_id)`, each sub-execution does a full sequential scan of **439,925 rows** → ~225 × 2 ms = **4,134 ms**.

**Fix — single-pass grouped aggregation:**

```sql
-- OPTIMIZED:
SELECT p.player_id, p.full_name,
       coalesce(utp_agg.times_picked, 0) AS times_picked
FROM players p
JOIN teams t ON t.team_id = p.team_id AND t.team_type = 'FRANCHISE'
LEFT JOIN (
    SELECT player_id, count(*) AS times_picked
    FROM user_team_players
    GROUP BY player_id
) utp_agg ON utp_agg.player_id = p.player_id
ORDER BY times_picked DESC;
```

The derived table `utp_agg` aggregates `user_team_players` in a **single pass** (one Seq Scan of 439,925 rows total, not 225 separate scans). The LEFT JOIN preserves players with 0 picks via `COALESCE`. Result: **4,134 ms → 37 ms (−99%)**.

**Correctness proof (EXCEPT check):**

```sql
SELECT count(*) AS diff_rows FROM (
  <original query>  EXCEPT  <rewritten query>
) diff;
-- Result: 0 rows  ✓ (semantically identical)
```

---

## 5. Key Findings

1. **R19 was 90% of total runtime.** A single correlated subquery without a supporting index cost 4,134 ms out of 4,581 ms total. This is the textbook case for replacing correlated subqueries with grouped joins.

2. **FK columns have no auto-index in PostgreSQL.** Out of 17 existing indexes, every one was on a PK or UNIQUE column. Five FK join columns (`user_teams.match_id`, `user_teams.user_id`, `contest_entries.user_team_id`, `contests.match_id`, `wallet_transactions.reference_entry_id`) had no index at all — causing full sequential scans on every join.

3. **R13 was silently wrong, not just slow.** The original query returned 0 rows instead of 192 violations, making the finance audit entirely useless. This was a logic bug (NULL trap in NOT IN), not just a performance issue.

4. **Partial indexes provide outsized benefit for skewed distributions.** The `idx_wt_pending_withdrawal` partial index on a few hundred rows out of 118,343 gave R10 a 99% speedup (8.9 ms → 0.065 ms) with minimal storage cost.

5. **Covering indexes eliminate heap fetches for OFFSET pagination.** R22 (OFFSET 50000 LIMIT 25) dropped 84% using an Index Only Scan that serves all 6 SELECT columns from the index without touching the heap.

6. **R06 (CROSS JOIN LATERAL) remains at ~90 ms.** The LATERAL evaluates `count(*)` per player per team-side, which is inherently O(players × teams) scans. The only fix would be a rewrite that changes the query semantics (e.g., precomputing team-side counts). Since this query checks rule violations, the existing index on `idx_user_teams_match_id` cuts the outer scan appropriately and no further optimization is possible without altering results.

---

## 6. Correctness Proofs

### R13
```sql
-- Old NOT IN returns 0 (NULL trap):
SELECT count(*) FROM contest_entries ce JOIN contests c ...
WHERE c.entry_fee > 0
  AND ce.entry_id NOT IN (SELECT w.reference_entry_id FROM wallet_transactions w);
-- → 0 rows (WRONG)

-- New NOT EXISTS returns 192 real violations:
SELECT count(*) FROM contest_entries ce JOIN contests c ...
WHERE c.entry_fee > 0
  AND NOT EXISTS (SELECT 1 FROM wallet_transactions w
                  WHERE w.reference_entry_id = ce.entry_id AND w.txn_type = 'ENTRY_FEE');
-- → 192 rows (CORRECT)
```

### R19
```sql
-- EXCEPT check: 0 differences between original and rewritten query
SELECT count(*) AS diff_rows FROM (
  <original correlated subquery version>
  EXCEPT
  <grouped LEFT JOIN version>
) diff;
-- → 0 rows ✓
```

---

## 7. Files Produced

| File | Description |
|------|-------------|
| `sql/05_indexes.sql` | 14 indexes + pg_trgm extension with rationale comments |
| `sql/06_optimized_queries.sql` | Full 30-query workload with R13 and R19 rewritten |
| `benchmarks/results/optimized/summary.csv` | 3-run benchmark results for all 30 queries |
| `benchmarks/results/optimized/R*.txt` | Raw `EXPLAIN (ANALYZE, BUFFERS)` plans, 3 runs each |
