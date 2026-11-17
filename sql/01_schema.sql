-- =====================================================================
-- Dream11 Fantasy Sports Database: Schema (Phase 2)
-- Team: AI_Web_Builder · Team No.: T0080 · Section: A, B, C, E
-- Database: PostgreSQL 15+
--
-- Run on an empty database:
--   createdb dream11
--   psql -d dream11 -f sql/01_schema.sql
-- =====================================================================

-- Create a dedicated schema to namespace all tables.
CREATE SCHEMA IF NOT EXISTS dream11;
SET search_path TO dream11;

-- ─────────────────────────────────────────────────────────────────────
-- 1. teams
-- Stores real cricket teams (IPL franchises and international sides).
-- Parent of: players, matches
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE teams (
    team_id    INTEGER     NOT NULL,
    team_name  VARCHAR(60) NOT NULL,
    short_name VARCHAR(4)  NOT NULL,
    team_type  VARCHAR(20) NOT NULL,

    CONSTRAINT pk_teams PRIMARY KEY (team_id),
    CONSTRAINT uq_teams_short_name UNIQUE (short_name),

    -- Short code must be 2–4 uppercase letters
    CONSTRAINT chk_teams_short_name
        CHECK (short_name ~ '^[A-Z]{2,4}$'),

    -- Only two supported team categories in the supplied data
    CONSTRAINT chk_teams_team_type
        CHECK (team_type IN ('FRANCHISE', 'INTERNATIONAL'))
);

-- ─────────────────────────────────────────────────────────────────────
-- 2. players
-- Stores each player's profile linked to one real cricket team.
-- Parent of: player_match_stats, user_teams (captain/vc),
--            user_team_players
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE players (
    player_id INTEGER      NOT NULL,
    full_name VARCHAR(60)  NOT NULL,
    team_id   INTEGER      NOT NULL,
    role      VARCHAR(4)   NOT NULL,
    credits   NUMERIC(4,1) NOT NULL,
    is_active BOOLEAN      NOT NULL,

    CONSTRAINT pk_players PRIMARY KEY (player_id),

    CONSTRAINT fk_players_team
        FOREIGN KEY (team_id) REFERENCES teams (team_id)
        ON DELETE RESTRICT,

    -- Fantasy role codes as found in the seed data
    CONSTRAINT chk_players_role
        CHECK (role IN ('WK', 'BAT', 'AR', 'BOWL')),

    CONSTRAINT chk_players_credits
        CHECK (credits > 0)
);

-- ─────────────────────────────────────────────────────────────────────
-- 3. matches
-- Stores each cricket fixture with its two participating teams.
-- Parent of: player_match_stats, user_teams, contests
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE matches (
    match_id     INTEGER     NOT NULL,
    tournament   VARCHAR(40) NOT NULL,
    home_team_id INTEGER     NOT NULL,
    away_team_id INTEGER     NOT NULL,
    venue        VARCHAR(80) NOT NULL,
    starts_at    TIMESTAMPTZ NOT NULL,
    status       VARCHAR(10) NOT NULL,

    CONSTRAINT pk_matches PRIMARY KEY (match_id),

    CONSTRAINT fk_matches_home_team
        FOREIGN KEY (home_team_id) REFERENCES teams (team_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_matches_away_team
        FOREIGN KEY (away_team_id) REFERENCES teams (team_id)
        ON DELETE RESTRICT,

    -- A team cannot play itself
    CONSTRAINT chk_matches_teams_differ
        CHECK (home_team_id <> away_team_id),

    -- Statuses present in data; LIVE and ABANDONED included for future
    -- use and because the workload queries reference them (R25, W05)
    CONSTRAINT chk_matches_status
        CHECK (status IN ('UPCOMING', 'LIVE', 'COMPLETED', 'ABANDONED'))
);

-- ─────────────────────────────────────────────────────────────────────
-- 4. player_match_stats
-- Stores one player's performance in one match.
-- Composite PK: (match_id, player_id) — one record per player per match.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE player_match_stats (
    match_id       INTEGER      NOT NULL,
    player_id      INTEGER      NOT NULL,
    runs           SMALLINT     NOT NULL,
    balls_faced    SMALLINT     NOT NULL,
    fours          SMALLINT     NOT NULL,
    sixes          SMALLINT     NOT NULL,
    wickets        SMALLINT     NOT NULL,
    catches        SMALLINT     NOT NULL,
    fantasy_points NUMERIC(6,1) NOT NULL,

    CONSTRAINT pk_player_match_stats PRIMARY KEY (match_id, player_id),

    CONSTRAINT fk_pms_match
        FOREIGN KEY (match_id) REFERENCES matches (match_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_pms_player
        FOREIGN KEY (player_id) REFERENCES players (player_id)
        ON DELETE RESTRICT,

    -- Non-negative batting and fielding figures
    CONSTRAINT chk_pms_runs        CHECK (runs >= 0),
    CONSTRAINT chk_pms_balls_faced CHECK (balls_faced >= 0),
    CONSTRAINT chk_pms_fours       CHECK (fours >= 0),
    CONSTRAINT chk_pms_sixes       CHECK (sixes >= 0),
    CONSTRAINT chk_pms_wickets     CHECK (wickets BETWEEN 0 AND 10),
    CONSTRAINT chk_pms_catches     CHECK (catches >= 0),
    CONSTRAINT chk_pms_fantasy_pts CHECK (fantasy_points >= 0),

    -- Fours cannot exceed balls faced
    CONSTRAINT chk_pms_fours_lte_balls
        CHECK (fours <= balls_faced)
);

-- ─────────────────────────────────────────────────────────────────────
-- 5. users
-- Stores registered Dream11 users and their KYC status.
-- Parent of: user_teams, wallet_transactions
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE users (
    user_id    INTEGER     NOT NULL,
    username   VARCHAR(25) NOT NULL,
    phone      VARCHAR(10) NOT NULL,
    email      VARCHAR(80),              -- nullable: 19,935 missing
    state_code CHAR(2)     NOT NULL,
    kyc_status VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_phone    UNIQUE (phone),
    -- Unique non-NULL email (NULL values are permitted)
    CONSTRAINT uq_users_email    UNIQUE (email),

    -- Alphanumeric + underscore usernames up to 25 characters
    CONSTRAINT chk_users_username
        CHECK (username ~ '^[A-Za-z0-9_]{1,25}$'),

    -- 10-digit Indian mobile number starting with 6–9
    CONSTRAINT chk_users_phone
        CHECK (phone ~ '^[6-9][0-9]{9}$'),

    -- State code must be two uppercase letters
    CONSTRAINT chk_users_state_code
        CHECK (state_code ~ '^[A-Z]{2}$'),

    -- Allowed KYC statuses
    CONSTRAINT chk_users_kyc_status
        CHECK (kyc_status IN ('PENDING', 'VERIFIED', 'REJECTED'))
);

-- ─────────────────────────────────────────────────────────────────────
-- 6. user_teams
-- Stores the fantasy team a user creates for a match.
-- Parent of: user_team_players, contest_entries
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE user_teams (
    user_team_id    INTEGER      NOT NULL,
    user_id         INTEGER      NOT NULL,
    match_id        INTEGER      NOT NULL,
    team_label      VARCHAR(3)   NOT NULL,
    captain_id      INTEGER      NOT NULL,
    vice_captain_id INTEGER      NOT NULL,
    total_points    NUMERIC(6,1),         -- nullable: points not yet settled
    created_at      TIMESTAMPTZ  NOT NULL,

    CONSTRAINT pk_user_teams PRIMARY KEY (user_team_id),

    -- Each user can have at most one team per label per match
    CONSTRAINT uq_user_teams_label
        UNIQUE (user_id, match_id, team_label),

    CONSTRAINT fk_user_teams_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_user_teams_match
        FOREIGN KEY (match_id) REFERENCES matches (match_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_user_teams_captain
        FOREIGN KEY (captain_id) REFERENCES players (player_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_user_teams_vice_captain
        FOREIGN KEY (vice_captain_id) REFERENCES players (player_id)
        ON DELETE RESTRICT,

    -- Team label must match the pattern Tx where x is 1–9
    -- (Seed data uses T1–T3; workload W01 inserts T9, so we allow T1–T9)
    CONSTRAINT chk_user_teams_label
        CHECK (team_label ~ '^T[1-9]$'),

    -- Captain and vice-captain must be different players
    CONSTRAINT chk_user_teams_captain_ne_vc
        CHECK (captain_id <> vice_captain_id),

    -- When set, total_points must not be negative
    CONSTRAINT chk_user_teams_total_points
        CHECK (total_points IS NULL OR total_points >= 0)
);

-- ─────────────────────────────────────────────────────────────────────
-- 7. user_team_players
-- Junction table: maps the 11 players selected for a fantasy team.
-- Composite PK prevents the same player appearing twice in one team.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE user_team_players (
    user_team_id INTEGER NOT NULL,
    player_id    INTEGER NOT NULL,

    CONSTRAINT pk_user_team_players PRIMARY KEY (user_team_id, player_id),

    CONSTRAINT fk_utp_user_team
        FOREIGN KEY (user_team_id) REFERENCES user_teams (user_team_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_utp_player
        FOREIGN KEY (player_id) REFERENCES players (player_id)
        ON DELETE RESTRICT
);

-- ─────────────────────────────────────────────────────────────────────
-- 8. contests
-- Stores the contests offered for a match.
-- Parent of: contest_entries
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE contests (
    contest_id    INTEGER       NOT NULL,
    match_id      INTEGER       NOT NULL,
    contest_name  VARCHAR(40)   NOT NULL,
    contest_type  VARCHAR(15)   NOT NULL,
    entry_fee     NUMERIC(10,2) NOT NULL,
    total_spots   INTEGER       NOT NULL,
    prize_pool    NUMERIC(12,2) NOT NULL,
    is_guaranteed BOOLEAN       NOT NULL,
    invite_code   VARCHAR(8),             -- nullable: public contests have none

    CONSTRAINT pk_contests PRIMARY KEY (contest_id),
    CONSTRAINT uq_contests_invite_code UNIQUE (invite_code),

    CONSTRAINT fk_contests_match
        FOREIGN KEY (match_id) REFERENCES matches (match_id)
        ON DELETE RESTRICT,

    -- Supported contest categories
    CONSTRAINT chk_contests_contest_type
        CHECK (contest_type IN ('MEGA', 'SMALL', 'HEAD_TO_HEAD', 'PRIVATE')),

    -- Entry fee and prize pool cannot be negative
    CONSTRAINT chk_contests_entry_fee  CHECK (entry_fee >= 0),
    CONSTRAINT chk_contests_prize_pool CHECK (prize_pool >= 0),

    -- Total spots must be positive
    CONSTRAINT chk_contests_total_spots CHECK (total_spots > 0),

    -- Head-to-head contests must have exactly 2 spots
    CONSTRAINT chk_contests_h2h_spots
        CHECK (contest_type <> 'HEAD_TO_HEAD' OR total_spots = 2),

    -- Private contests must have an invite code; public contests must not
    CONSTRAINT chk_contests_private_code
        CHECK (
            (contest_type = 'PRIVATE' AND invite_code IS NOT NULL)
            OR (contest_type <> 'PRIVATE' AND invite_code IS NULL)
        ),

    -- When present, invite code must be exactly 8 uppercase letters or digits
    CONSTRAINT chk_contests_invite_code_format
        CHECK (invite_code IS NULL OR invite_code ~ '^[A-Z0-9]{8}$')
);

-- ─────────────────────────────────────────────────────────────────────
-- 9. contest_entries
-- Records the entry of a fantasy team into a contest.
-- Parent of: wallet_transactions (reference_entry_id)
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE contest_entries (
    entry_id     INTEGER       NOT NULL,
    contest_id   INTEGER       NOT NULL,
    user_team_id INTEGER       NOT NULL,
    joined_at    TIMESTAMPTZ   NOT NULL,
    final_rank   INTEGER,               -- nullable: unsettled contests
    winnings     NUMERIC(10,2) NOT NULL DEFAULT 0,

    CONSTRAINT pk_contest_entries PRIMARY KEY (entry_id),

    -- A fantasy team can join each contest only once
    CONSTRAINT uq_contest_entries_pair
        UNIQUE (contest_id, user_team_id),

    CONSTRAINT fk_ce_contest
        FOREIGN KEY (contest_id) REFERENCES contests (contest_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_ce_user_team
        FOREIGN KEY (user_team_id) REFERENCES user_teams (user_team_id)
        ON DELETE RESTRICT,

    -- When set, rank must be positive
    CONSTRAINT chk_ce_final_rank
        CHECK (final_rank IS NULL OR final_rank > 0),

    -- Winnings cannot be negative
    CONSTRAINT chk_ce_winnings CHECK (winnings >= 0),

    -- Unsettled entries (no rank yet) must have zero winnings
    CONSTRAINT chk_ce_unranked_no_winnings
        CHECK (final_rank IS NOT NULL OR winnings = 0)
);

-- ─────────────────────────────────────────────────────────────────────
-- 10. wallet_transactions
-- Stores the wallet ledger for each user.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE wallet_transactions (
    txn_id             INTEGER       NOT NULL,
    user_id            INTEGER       NOT NULL,
    txn_type           VARCHAR(12)   NOT NULL,
    amount             NUMERIC(10,2) NOT NULL,
    reference_entry_id INTEGER,         -- nullable: 63,000 rows have no entry
    status             VARCHAR(10)   NOT NULL,
    created_at         TIMESTAMPTZ   NOT NULL,

    CONSTRAINT pk_wallet_transactions PRIMARY KEY (txn_id),

    CONSTRAINT fk_wt_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_wt_entry
        FOREIGN KEY (reference_entry_id) REFERENCES contest_entries (entry_id)
        ON DELETE RESTRICT,

    -- Supported transaction types
    CONSTRAINT chk_wt_txn_type
        CHECK (txn_type IN ('DEPOSIT', 'WITHDRAWAL', 'ENTRY_FEE',
                             'WINNINGS', 'REFUND', 'BONUS')),

    -- Amount must be positive
    CONSTRAINT chk_wt_amount CHECK (amount > 0),

    -- Supported processing statuses
    CONSTRAINT chk_wt_status
        CHECK (status IN ('SUCCESS', 'PENDING', 'FAILED')),

    -- Entry-related types require a reference; non-entry types must not have one
    CONSTRAINT chk_wt_entry_ref
        CHECK (
            (txn_type IN ('ENTRY_FEE', 'WINNINGS', 'REFUND')
             AND reference_entry_id IS NOT NULL)
            OR
            (txn_type IN ('DEPOSIT', 'WITHDRAWAL', 'BONUS')
             AND reference_entry_id IS NULL)
        )
);

-- =====================================================================
-- Index notes (Phase 2):
-- PostgreSQL automatically creates B-tree indexes for all PRIMARY KEY
-- and UNIQUE constraints declared above.  No additional indexes are
-- created in this phase; they will be measured at baseline (Phase 3)
-- and added in Phase 4 after the unoptimised query plans are recorded.
-- =====================================================================
