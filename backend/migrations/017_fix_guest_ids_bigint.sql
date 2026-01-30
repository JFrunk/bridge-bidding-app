-- ============================================================================
-- Migration 017: Convert user ID columns from INTEGER to BIGINT
--
-- PROBLEM: Guest user IDs (e.g., -7640538002) exceed the 32-bit INTEGER
-- range (-2,147,483,648 to 2,147,483,647), causing "value out of range"
-- errors when guest users access analytics endpoints.
--
-- FIX: Migrate users.id from SERIAL (int4) to BIGINT, and all user_id
-- foreign key columns across 17 dependent tables.
--
-- SCOPE:
--   - 1 primary key column (users.id)
--   - 17 user_id columns across dependent tables
--   - 11 foreign key constraints dropped and re-added
--   - 7 views dropped and recreated (PostgreSQL-native syntax)
--
-- Risk Level: MEDIUM
--   - All changes are type-widening (INTEGER → BIGINT), no data loss
--   - Wrapped in a single transaction for atomicity
--   - Views are recreated with PostgreSQL-compatible syntax
--
-- Target: PostgreSQL only (production on Render)
-- Prerequisites: All prior migrations (001-016) applied
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Drop all views that depend on user_id columns
-- ============================================================================
-- These views reference tables with user_id columns. PostgreSQL will block
-- ALTER COLUMN TYPE if any dependent view exists.

-- From migration 011
DROP VIEW IF EXISTS v_user_analysis_stats;
DROP VIEW IF EXISTS v_user_strain_accuracy;
DROP VIEW IF EXISTS v_recent_boards_for_quadrant;

-- From migration 007
DROP VIEW IF EXISTS v_hand_history_with_analysis;

-- From migration 001
DROP VIEW IF EXISTS v_bidding_feedback_stats;
DROP VIEW IF EXISTS v_recent_bidding_decisions;
DROP VIEW IF EXISTS v_concept_mastery;

-- From base schema files (may or may not exist on production)
DROP VIEW IF EXISTS v_user_progress_summary;
DROP VIEW IF EXISTS v_recent_activity;
DROP VIEW IF EXISTS v_active_mistake_patterns;
DROP VIEW IF EXISTS v_pending_celebrations;
DROP VIEW IF EXISTS v_active_sessions;
DROP VIEW IF EXISTS v_session_details;
DROP VIEW IF EXISTS v_hand_history;
DROP VIEW IF EXISTS v_user_session_stats;
DROP VIEW IF EXISTS v_user_convention_summary;
DROP VIEW IF EXISTS v_user_level_progress;

-- ============================================================================
-- STEP 2: Drop foreign key constraints that reference users(id)
-- ============================================================================
-- PostgreSQL cannot alter a column type when FK constraints exist.
-- Constraint names follow PostgreSQL's auto-naming: {table}_{column}_fkey

ALTER TABLE user_settings DROP CONSTRAINT IF EXISTS user_settings_user_id_fkey;
ALTER TABLE user_gamification DROP CONSTRAINT IF EXISTS user_gamification_user_id_fkey;
ALTER TABLE practice_sessions DROP CONSTRAINT IF EXISTS practice_sessions_user_id_fkey;
ALTER TABLE practice_history DROP CONSTRAINT IF EXISTS practice_history_user_id_fkey;
ALTER TABLE mistake_patterns DROP CONSTRAINT IF EXISTS mistake_patterns_user_id_fkey;
ALTER TABLE improvement_milestones DROP CONSTRAINT IF EXISTS improvement_milestones_user_id_fkey;
ALTER TABLE streak_history DROP CONSTRAINT IF EXISTS streak_history_user_id_fkey;
ALTER TABLE game_sessions DROP CONSTRAINT IF EXISTS game_sessions_user_id_fkey;
ALTER TABLE imported_tournaments DROP CONSTRAINT IF EXISTS imported_tournaments_user_id_fkey;
ALTER TABLE imported_hands DROP CONSTRAINT IF EXISTS imported_hands_user_id_fkey;
ALTER TABLE bidding_decisions DROP CONSTRAINT IF EXISTS bidding_decisions_user_id_fkey;
ALTER TABLE hand_analyses DROP CONSTRAINT IF EXISTS hand_analyses_user_id_fkey;

-- ============================================================================
-- STEP 3: Alter users.id from INTEGER (SERIAL) to BIGINT
-- ============================================================================
-- The sequence (users_id_seq) already supports bigint values; only the
-- column type was limiting it to 32-bit range.

ALTER TABLE users ALTER COLUMN id TYPE BIGINT;

-- ============================================================================
-- STEP 4: Alter all user_id columns to BIGINT
-- ============================================================================

-- Tables with FK constraints (dropped in Step 2, re-added in Step 5)
ALTER TABLE user_settings ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE user_gamification ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE practice_sessions ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE practice_history ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE mistake_patterns ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE improvement_milestones ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE streak_history ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE game_sessions ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE imported_tournaments ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE imported_hands ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE bidding_decisions ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE hand_analyses ALTER COLUMN user_id TYPE BIGINT;

-- Tables without explicit FK constraints
ALTER TABLE user_convention_progress ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE user_skill_progress ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE skill_practice_history ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE convention_practice_history ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE play_decisions ALTER COLUMN user_id TYPE BIGINT;

-- ============================================================================
-- STEP 5: Re-add foreign key constraints
-- ============================================================================

ALTER TABLE user_settings
    ADD CONSTRAINT user_settings_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE user_gamification
    ADD CONSTRAINT user_gamification_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE practice_sessions
    ADD CONSTRAINT practice_sessions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE practice_history
    ADD CONSTRAINT practice_history_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE mistake_patterns
    ADD CONSTRAINT mistake_patterns_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE improvement_milestones
    ADD CONSTRAINT improvement_milestones_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE streak_history
    ADD CONSTRAINT streak_history_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE game_sessions
    ADD CONSTRAINT game_sessions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE imported_tournaments
    ADD CONSTRAINT imported_tournaments_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE imported_hands
    ADD CONSTRAINT imported_hands_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE bidding_decisions
    ADD CONSTRAINT bidding_decisions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE hand_analyses
    ADD CONSTRAINT hand_analyses_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- ============================================================================
-- STEP 6: Recreate views (PostgreSQL-native syntax)
-- ============================================================================
-- Original views used SQLite functions (datetime(), printf()) which are not
-- valid in PostgreSQL. These recreations use PostgreSQL-native equivalents.

-- ---------------------------------------------------------------------------
-- From migration 001: Bidding feedback views
-- ---------------------------------------------------------------------------

CREATE VIEW v_bidding_feedback_stats AS
SELECT
    user_id,
    COUNT(*) as total_decisions,
    AVG(score) as avg_score,
    SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
    SUM(CASE WHEN correctness = 'acceptable' THEN 1 ELSE 0 END) as acceptable_count,
    SUM(CASE WHEN correctness = 'suboptimal' THEN 1 ELSE 0 END) as suboptimal_count,
    SUM(CASE WHEN correctness = 'error' THEN 1 ELSE 0 END) as error_count,
    CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) as optimal_rate,
    CAST(SUM(CASE WHEN correctness = 'error' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) as error_rate,
    SUM(CASE WHEN impact = 'critical' THEN 1 ELSE 0 END) as critical_errors,
    SUM(CASE WHEN impact = 'significant' THEN 1 ELSE 0 END) as significant_errors,
    SUM(CASE WHEN timestamp >= NOW() - INTERVAL '30 days' THEN 1 ELSE 0 END) as recent_decisions,
    MIN(timestamp) as first_decision,
    MAX(timestamp) as last_decision
FROM bidding_decisions
GROUP BY user_id;

CREATE VIEW v_recent_bidding_decisions AS
SELECT
    id,
    user_id,
    bid_number,
    position,
    user_bid,
    optimal_bid,
    correctness,
    score,
    impact,
    key_concept,
    error_category,
    helpful_hint,
    timestamp,
    CASE
        WHEN correctness = 'optimal' THEN '✓'
        WHEN correctness = 'acceptable' THEN 'ⓘ'
        WHEN correctness = 'suboptimal' THEN '⚠'
        WHEN correctness = 'error' THEN '✗'
    END as icon,
    CASE
        WHEN user_bid = optimal_bid THEN user_bid
        ELSE user_bid || ' → ' || optimal_bid
    END as bid_display
FROM bidding_decisions
ORDER BY user_id, timestamp DESC;

CREATE VIEW v_concept_mastery AS
SELECT
    user_id,
    key_concept,
    COUNT(*) as attempts,
    AVG(score) as avg_score,
    SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
    CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) as mastery_rate,
    MIN(timestamp) as first_attempt,
    MAX(timestamp) as last_attempt,
    CASE
        WHEN CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) >= 0.90 THEN 'mastered'
        WHEN CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) >= 0.70 THEN 'proficient'
        WHEN CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) >= 0.50 THEN 'learning'
        ELSE 'needs_practice'
    END as status
FROM bidding_decisions
WHERE key_concept IS NOT NULL
GROUP BY user_id, key_concept;

-- ---------------------------------------------------------------------------
-- From migration 007: Hand history with DDS analysis
-- ---------------------------------------------------------------------------

CREATE VIEW v_hand_history_with_analysis AS
SELECT
    sh.id,
    sh.session_id,
    gs.user_id,
    sh.hand_number,
    sh.dealer,
    sh.vulnerability,
    CASE
        WHEN sh.contract_level IS NULL THEN 'Passed Out'
        ELSE CONCAT(sh.contract_level, sh.contract_strain,
             CASE sh.contract_doubled
                 WHEN 1 THEN 'X'
                 WHEN 2 THEN 'XX'
                 ELSE ''
             END,
             ' by ', sh.contract_declarer)
    END as contract_display,
    sh.tricks_taken,
    sh.tricks_needed,
    sh.made,
    sh.hand_score,
    sh.ns_total_after,
    sh.ew_total_after,
    sh.user_was_declarer,
    sh.dd_tricks,
    sh.par_score,
    sh.par_contract,
    CASE
        WHEN sh.dd_tricks IS NOT NULL AND sh.tricks_taken IS NOT NULL
        THEN sh.tricks_taken - sh.dd_tricks
        ELSE NULL
    END as tricks_vs_dd,
    CASE
        WHEN sh.dd_tricks IS NOT NULL AND sh.tricks_taken IS NOT NULL
        THEN sh.tricks_taken >= sh.dd_tricks
        ELSE NULL
    END as played_optimally,
    sh.dds_analysis,
    sh.played_at
FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
ORDER BY sh.session_id, sh.hand_number;

-- ---------------------------------------------------------------------------
-- From migration 011: Comprehensive analysis views
-- ---------------------------------------------------------------------------

CREATE VIEW v_user_analysis_stats AS
SELECT
    gs.user_id,
    COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END) as total_analyzed_hands,
    SUM(CASE WHEN sh.quadrant = 'Q1' THEN 1 ELSE 0 END) as q1_count,
    SUM(CASE WHEN sh.quadrant = 'Q2' THEN 1 ELSE 0 END) as q2_count,
    SUM(CASE WHEN sh.quadrant = 'Q3' THEN 1 ELSE 0 END) as q3_count,
    SUM(CASE WHEN sh.quadrant = 'Q4' THEN 1 ELSE 0 END) as q4_count,
    ROUND(100.0 * SUM(CASE WHEN sh.quadrant = 'Q1' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END), 0), 1) as q1_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.quadrant = 'Q2' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END), 0), 1) as q2_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.quadrant = 'Q3' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END), 0), 1) as q3_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.quadrant = 'Q4' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END), 0), 1) as q4_pct,
    SUM(CASE WHEN sh.bid_efficiency = 'optimal' THEN 1 ELSE 0 END) as optimal_bids,
    SUM(CASE WHEN sh.bid_efficiency = 'underbid' THEN 1 ELSE 0 END) as underbids,
    SUM(CASE WHEN sh.bid_efficiency = 'overbid' THEN 1 ELSE 0 END) as overbids,
    ROUND(100.0 * SUM(CASE WHEN sh.bid_efficiency = 'optimal' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.bid_efficiency IS NOT NULL THEN 1 END), 0), 1) as optimal_bid_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.bid_efficiency = 'underbid' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.bid_efficiency IS NOT NULL THEN 1 END), 0), 1) as underbid_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.bid_efficiency = 'overbid' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.bid_efficiency IS NOT NULL THEN 1 END), 0), 1) as overbid_pct,
    SUM(COALESCE(sh.points_left_on_table, 0)) as total_points_left,
    AVG(CASE WHEN sh.points_left_on_table > 0 THEN sh.points_left_on_table END) as avg_points_left_when_underbid,
    SUM(CASE WHEN sh.opening_lead_quality = 'optimal' THEN 1 ELSE 0 END) as optimal_leads,
    SUM(CASE WHEN sh.opening_lead_quality = 'neutral' THEN 1 ELSE 0 END) as neutral_leads,
    SUM(CASE WHEN sh.opening_lead_quality = 'leaking' THEN 1 ELSE 0 END) as leaking_leads,
    SUM(COALESCE(sh.opening_lead_cost, 0)) as total_lead_cost,
    AVG(CASE WHEN sh.dd_tricks IS NOT NULL AND sh.tricks_taken IS NOT NULL
        THEN sh.tricks_taken - sh.dd_tricks END) as avg_tricks_vs_dd,
    SUM(CASE WHEN sh.user_was_declarer AND sh.made THEN 1 ELSE 0 END) as contracts_made,
    SUM(CASE WHEN sh.user_was_declarer THEN 1 ELSE 0 END) as contracts_declared,
    AVG(CASE WHEN sh.par_score IS NOT NULL AND sh.hand_score IS NOT NULL
        THEN sh.hand_score - sh.par_score END) as avg_score_vs_par
FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
GROUP BY gs.user_id;

CREATE VIEW v_user_strain_accuracy AS
SELECT
    gs.user_id,
    sh.contract_strain as strain,
    COUNT(*) as total_contracts,
    SUM(CASE WHEN sh.dd_tricks >= sh.tricks_needed THEN 1 ELSE 0 END) as makeable_contracts,
    SUM(CASE WHEN sh.made THEN 1 ELSE 0 END) as made_contracts,
    ROUND(100.0 * SUM(CASE WHEN sh.dd_tricks >= sh.tricks_needed THEN 1 ELSE 0 END) /
          NULLIF(COUNT(*), 0), 1) as bidding_accuracy_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.made AND sh.dd_tricks >= sh.tricks_needed THEN 1 ELSE 0 END) /
          NULLIF(SUM(CASE WHEN sh.dd_tricks >= sh.tricks_needed THEN 1 ELSE 0 END), 0), 1) as execution_pct,
    AVG(sh.tricks_taken - sh.dd_tricks) as avg_tricks_vs_dd
FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
WHERE sh.contract_strain IS NOT NULL
  AND sh.dd_tricks IS NOT NULL
GROUP BY gs.user_id, sh.contract_strain;

CREATE VIEW v_recent_boards_for_quadrant AS
SELECT
    sh.id as hand_id,
    sh.session_id,
    gs.user_id,
    sh.hand_number,
    sh.played_at,
    CASE
        WHEN sh.contract_level IS NULL THEN 'Pass'
        ELSE CONCAT(sh.contract_level, sh.contract_strain,
             CASE sh.contract_doubled WHEN 1 THEN 'X' WHEN 2 THEN 'XX' ELSE '' END)
    END as contract_display,
    sh.contract_declarer,
    sh.tricks_taken,
    sh.tricks_needed,
    sh.dd_tricks,
    sh.made,
    sh.hand_score,
    sh.par_score,
    sh.quadrant,
    sh.bid_efficiency,
    sh.points_left_on_table,
    sh.user_was_declarer,
    CASE
        WHEN sh.dd_tricks IS NOT NULL AND sh.tricks_taken IS NOT NULL
        THEN sh.tricks_taken - sh.dd_tricks
        ELSE 0
    END as play_delta,
    CASE
        WHEN sh.par_score IS NOT NULL AND sh.hand_score IS NOT NULL
        THEN sh.hand_score - sh.par_score
        ELSE 0
    END as bid_delta
FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
WHERE sh.quadrant IS NOT NULL
ORDER BY sh.played_at DESC;

COMMIT;

-- ============================================================================
-- Migration Complete
-- ============================================================================
--
-- Changes:
--   - users.id: SERIAL (int4) → BIGINT
--   - 17 user_id columns: INTEGER → BIGINT
--   - 11 FK constraints: dropped and re-added with ON DELETE CASCADE
--   - 7 views: recreated with PostgreSQL-native syntax
--     (replaced SQLite's datetime()/printf() with NOW()/CONCAT())
--
-- Verification queries:
--   SELECT column_name, data_type
--   FROM information_schema.columns
--   WHERE table_name = 'users' AND column_name = 'id';
--   -- Should return: data_type = 'bigint'
--
--   SELECT column_name, data_type
--   FROM information_schema.columns
--   WHERE column_name = 'user_id'
--   ORDER BY table_name;
--   -- All should return: data_type = 'bigint'
--
-- To rollback (if needed):
--   ALTER TABLE ... ALTER COLUMN ... TYPE INTEGER;
--   (reverse order: drop FKs, alter columns, re-add FKs, recreate views)
-- ============================================================================
