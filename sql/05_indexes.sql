-- =====================================================================
-- Dream11 DBMS Project – CP3: Optimization Indexes
-- Team T0080 · AI_Web_Builder
-- Applied to schema: dream11
--
-- Strategy: add indexes only on columns that are repeatedly used in
-- WHERE / JOIN / ORDER BY clauses but have no existing B-tree index.
-- Existing auto-indexes (PK / UNIQUE) are NOT recreated.
-- =====================================================================
SET search_path TO dream11;

-- ---------------------------------------------------------------------
-- 1. user_teams(match_id)
--    Helps: R02 (subquery + join), R06 (CROSS JOIN LATERAL on match 183),
--           R08 (GROUP BY match_id), W04 (UPDATE WHERE match_id=183)
--    Without this, every query that filters a single match_id does a
--    full sequential scan of 39,975 rows.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_user_teams_match_id
    ON user_teams (match_id);

-- ---------------------------------------------------------------------
-- 2. user_teams(user_id)
--    Helps: R03, R07, R09 (join path user_id → user_teams → wallet)
--    PostgreSQL does NOT auto-index FK columns.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_user_teams_user_id
    ON user_teams (user_id);

-- ---------------------------------------------------------------------
-- 3. wallet_transactions(user_id, txn_type, status)
--    Composite index: leading column user_id satisfies R09 (single user)
--    while additional columns txn_type, status allow index-only
--    evaluation of R10 / R18 / W05 filter predicates.
--    Column order: user_id first (equality), then txn_type, then status.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_wt_user_type_status
    ON wallet_transactions (user_id, txn_type, status);

-- ---------------------------------------------------------------------
-- 4. wallet_transactions – partial index for PENDING WITHDRAWAL rows
--    Helps: R10 (pending withdrawals older than 24 h), W05 (approve them)
--    A partial index covering only the ~few hundred PENDING WITHDRAWAL
--    rows is tiny and very fast to scan.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_wt_pending_withdrawal
    ON wallet_transactions (created_at)
    WHERE txn_type = 'WITHDRAWAL' AND status = 'PENDING';

-- ---------------------------------------------------------------------
-- 5. wallet_transactions(txn_type, status, created_at)
--    Helps: R20 (DEPOSIT/SUCCESS/June 2026 date range)
--    Allows index range scan instead of full seq-scan of 118,343 rows.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_wt_type_status_date
    ON wallet_transactions (txn_type, status, created_at);

-- ---------------------------------------------------------------------
-- 6. wallet_transactions(reference_entry_id) – partial (NOT NULL only)
--    Helps: R13 (NOT EXISTS subquery), R25 (NOT EXISTS REFUND check)
--    Skipping NULLs keeps the index small; the original R13 NOT IN
--    had a NULL trap (63,000 NULLs caused it to return 0 rows).
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_wt_reference_entry_id
    ON wallet_transactions (reference_entry_id)
    WHERE reference_entry_id IS NOT NULL;

-- ---------------------------------------------------------------------
-- 7. wallet_transactions – covering index for R22 keyset / OFFSET
--    R22 does ORDER BY created_at DESC OFFSET 50000 LIMIT 25.
--    With a covering index the planner uses an Index Only Scan and
--    can skip the sort entirely; the INCLUDE columns avoid heap fetches.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_wt_created_at_desc
    ON wallet_transactions (created_at DESC)
    INCLUDE (txn_id, user_id, txn_type, amount, status);

-- ---------------------------------------------------------------------
-- 8. contest_entries(user_team_id)
--    Helps: R15, R17, R21, R25 all join contest_entries on user_team_id.
--    Without this every such join does a full scan of 42,746 rows.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_ce_user_team_id
    ON contest_entries (user_team_id);

-- ---------------------------------------------------------------------
-- 9. contest_entries(joined_at)
--    Helps: R11, R15 filter WHERE joined_at >= '2026-01-01'
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_ce_joined_at
    ON contest_entries (joined_at);

-- ---------------------------------------------------------------------
-- 10. user_team_players(player_id)   ← MOST CRITICAL INDEX
--    Helps: R19 correlated subquery executes once per FRANCHISE player
--    (~225 rows) and each sub-execution was a full seq-scan of 439,925
--    rows → ~4,134 ms total. With this index each sub-execution becomes
--    an Index Scan returning a few rows → <5 ms total.
--    Also helps R06 (CROSS JOIN LATERAL counts per team-side).
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_utp_player_id
    ON user_team_players (player_id);

-- ---------------------------------------------------------------------
-- 11. contests(match_id)
--    Helps: R01 (LEFT JOIN contests), R04 (WHERE match_id=207),
--           R14 (JOIN matches → contests)
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_contests_match_id
    ON contests (match_id);

-- ---------------------------------------------------------------------
-- 12. matches(status)
--    Helps: R01 WHERE status='UPCOMING', R14 WHERE status='COMPLETED',
--           R25 WHERE status='ABANDONED'
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_matches_status
    ON matches (status);

-- ---------------------------------------------------------------------
-- 13. player_match_stats(player_id)
--    Helps: R19 (JOIN to get player stats per team), R24 (CSK player form)
--    The existing PK is (match_id, player_id) so player_id alone has no
--    leading index entry.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_pms_player_id
    ON player_match_stats (player_id);

-- ---------------------------------------------------------------------
-- 14. GIN trigram index on players.full_name
--    Helps: R16 ILIKE '%sharma%'  (leading wildcard → trigram required)
--    pg_trgm extension must be enabled first.
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_players_fullname_trgm
    ON players USING GIN (full_name gin_trgm_ops);

-- ---------------------------------------------------------------------
-- Refresh planner statistics so the new indexes are used immediately
-- ---------------------------------------------------------------------
ANALYZE teams, players, matches, player_match_stats,
        users, user_teams, user_team_players,
        contests, contest_entries, wallet_transactions;
