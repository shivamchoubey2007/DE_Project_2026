-- =====================================================================
-- Dream11 Fantasy Sports Database: Load seed data (Phase 2)
-- Team: AI_Web_Builder · Team No.: T0080
--
-- Prerequisites:
--   psql -d dream11 -f sql/01_schema.sql   (schema must exist first)
--
-- Run from the repository root so that the relative seed_data/ paths work:
--   psql -d dream11 -f sql/02_load_data.sql
--
-- Tables are loaded in parent-to-child order to satisfy foreign keys.
-- =====================================================================

SET search_path TO dream11;

-- 1. teams  (18 rows expected)
\copy teams (team_id, team_name, short_name, team_type) FROM 'seed_data/teams.csv' WITH (FORMAT csv, HEADER true)

-- 2. players  (450 rows expected)
\copy players (player_id, full_name, team_id, role, credits, is_active) FROM 'seed_data/players.csv' WITH (FORMAT csv, HEADER true)

-- 3. matches  (212 rows expected)
\copy matches (match_id, tournament, home_team_id, away_team_id, venue, starts_at, status) FROM 'seed_data/matches.csv' WITH (FORMAT csv, HEADER true)

-- 4. users  (50,000 rows expected)
\copy users (user_id, username, phone, email, state_code, kyc_status, created_at) FROM 'seed_data/users.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- 5. player_match_stats  (4,444 rows expected)
\copy player_match_stats (match_id, player_id, runs, balls_faced, fours, sixes, wickets, catches, fantasy_points) FROM 'seed_data/player_match_stats.csv' WITH (FORMAT csv, HEADER true)

-- 6. user_teams  (39,975 rows expected)
\copy user_teams (user_team_id, user_id, match_id, team_label, captain_id, vice_captain_id, total_points, created_at) FROM 'seed_data/user_teams.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- 7. user_team_players  (439,925 rows expected)
\copy user_team_players (user_team_id, player_id) FROM 'seed_data/user_team_players.csv' WITH (FORMAT csv, HEADER true)

-- 8. contests  (2,544 rows expected)
\copy contests (contest_id, match_id, contest_name, contest_type, entry_fee, total_spots, prize_pool, is_guaranteed, invite_code) FROM 'seed_data/contests.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- 9. contest_entries  (42,746 rows expected)
\copy contest_entries (entry_id, contest_id, user_team_id, joined_at, final_rank, winnings) FROM 'seed_data/contest_entries.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- 10. wallet_transactions  (118,343 rows expected)
\copy wallet_transactions (txn_id, user_id, txn_type, amount, reference_entry_id, status, created_at) FROM 'seed_data/wallet_transactions.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- Update planner statistics after bulk load
ANALYZE;

-- ─────────────────────────────────────────────────────────────────────
-- Verification: row counts (compare with expected values above)
-- ─────────────────────────────────────────────────────────────────────
SELECT 'teams'               AS tbl, count(*) AS rows FROM teams
UNION ALL
SELECT 'players',                    count(*)         FROM players
UNION ALL
SELECT 'matches',                    count(*)         FROM matches
UNION ALL
SELECT 'player_match_stats',         count(*)         FROM player_match_stats
UNION ALL
SELECT 'users',                      count(*)         FROM users
UNION ALL
SELECT 'user_teams',                 count(*)         FROM user_teams
UNION ALL
SELECT 'user_team_players',          count(*)         FROM user_team_players
UNION ALL
SELECT 'contests',                   count(*)         FROM contests
UNION ALL
SELECT 'contest_entries',            count(*)         FROM contest_entries
UNION ALL
SELECT 'wallet_transactions',        count(*)         FROM wallet_transactions
ORDER BY tbl;

-- ─────────────────────────────────────────────────────────────────────
-- Integrity check 1: every fantasy team must have exactly 11 players
-- ─────────────────────────────────────────────────────────────────────
SELECT 'IC1 teams NOT having exactly 11 players' AS check_name, count(*) AS violations
FROM (
    SELECT user_team_id FROM user_team_players
    GROUP BY user_team_id HAVING count(*) <> 11
) x;

-- ─────────────────────────────────────────────────────────────────────
-- Integrity check 2: players in each fantasy team must all belong to
-- the home or away team of that match
-- ─────────────────────────────────────────────────────────────────────
SELECT 'IC2 players not from match teams' AS check_name, count(*) AS violations
FROM user_team_players utp
JOIN user_teams ut ON ut.user_team_id = utp.user_team_id
JOIN players p     ON p.player_id = utp.player_id
JOIN matches m     ON m.match_id = ut.match_id
WHERE p.team_id NOT IN (m.home_team_id, m.away_team_id);

-- ─────────────────────────────────────────────────────────────────────
-- Integrity check 3: every paid contest entry must have exactly one
-- ENTRY_FEE wallet debit
-- ─────────────────────────────────────────────────────────────────────
SELECT 'IC3 paid entries missing wallet debit' AS check_name, count(*) AS violations
FROM contest_entries ce
JOIN contests c ON c.contest_id = ce.contest_id AND c.entry_fee > 0
WHERE ce.entry_id NOT IN (
    SELECT reference_entry_id FROM wallet_transactions
    WHERE txn_type = 'ENTRY_FEE' AND reference_entry_id IS NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────
-- Integrity check 4: NULL counts for nullable columns
-- ─────────────────────────────────────────────────────────────────────
SELECT 'users.email NULLs'                        AS column_name, count(*) FILTER (WHERE email IS NULL)              AS null_count FROM users
UNION ALL
SELECT 'user_teams.total_points NULLs',                           count(*) FILTER (WHERE total_points IS NULL)       FROM user_teams
UNION ALL
SELECT 'contests.invite_code NULLs',                              count(*) FILTER (WHERE invite_code IS NULL)        FROM contests
UNION ALL
SELECT 'contest_entries.final_rank NULLs',                        count(*) FILTER (WHERE final_rank IS NULL)         FROM contest_entries
UNION ALL
SELECT 'wallet_transactions.reference_entry_id NULLs',            count(*) FILTER (WHERE reference_entry_id IS NULL) FROM wallet_transactions;
