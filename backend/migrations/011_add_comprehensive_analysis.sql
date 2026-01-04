-- ============================================================================
-- Migration 011: Add Comprehensive Analysis Columns
--
-- Adds columns to support advanced hand analysis features:
-- - Decay curve (trick-by-trick potential tracking)
-- - Quadrant classification (bidding vs play quality)
-- - Bidding efficiency analysis (underbid/optimal/overbid)
-- - Leave-table points calculation
-- - Opening lead quality assessment
-- - Full DD matrix storage
-- - ACBL import support with field results
--
-- Risk Level: LOW
-- - All changes are additive (ADD COLUMN with DEFAULT NULL)
-- - No existing data is modified
-- - New tables use IF NOT EXISTS
-- - Rollback: Simply drop new columns/tables
--
-- Prerequisites: Migration 007 (dds_analysis columns) must be applied
-- ============================================================================

-- ============================================================================
-- PART 1: Enhanced Session Hands - Play Analysis
-- ============================================================================

-- Decay curve: JSON array of trick potential at each card played
-- Format: [10, 10, 10, 8, 8, 7, 7, ...] (up to 52 entries, one per card)
-- Normalized to DECLARER's perspective (always shows declarer's max tricks)
-- Used for: Sparkline visualization, mistake identification
ALTER TABLE session_hands ADD COLUMN decay_curve TEXT DEFAULT NULL;

-- Major errors: JSON array of significant mistakes during play
-- Format: [{"trick": 4, "card_index": 12, "card": "SQ", "position": "S",
--           "loss": 2, "optimal_card": "S10", "reasoning": "..."}]
-- Used for: Error highlighting, learning feedback
ALTER TABLE session_hands ADD COLUMN major_errors TEXT DEFAULT NULL;

-- Quadrant classification (pre-calculated for quick dashboard display)
-- Q1 = Good Bidding + Good Play (Top-Right, Green)
-- Q2 = Good Bidding + Bad Play (Top-Left, Yellow)
-- Q3 = Bad Bidding + Bad Play (Bottom-Left, Red)
-- Q4 = Bad Bidding + Good Play (Bottom-Right, Yellow)
--
-- "Good Bidding" = Reached optimal bonus level (game/slam) OR no bonus available
-- "Good Play" = Actual tricks >= DD tricks for contract
ALTER TABLE session_hands ADD COLUMN quadrant TEXT DEFAULT NULL;

-- Bidding efficiency classification
-- 'optimal' = Contract achieves maximum available bonus
-- 'underbid' = Game/slam available but not bid (left points on table)
-- 'overbid' = Contract unmakeable by DD analysis
ALTER TABLE session_hands ADD COLUMN bid_efficiency TEXT DEFAULT NULL;

-- Points left on table from underbidding
-- Calculated as: (potential game/slam bonus) - (actual score)
-- Only populated when bid_efficiency = 'underbid'
ALTER TABLE session_hands ADD COLUMN points_left_on_table INTEGER DEFAULT 0;

-- Opening lead analysis (populated when user was on opening lead)
ALTER TABLE session_hands ADD COLUMN opening_lead_card TEXT DEFAULT NULL;

-- Opening lead quality classification
-- 'optimal' = Lead achieves maximum tricks for defense (or tied)
-- 'neutral' = Within 1 trick of optimal lead
-- 'leaking' = Costs 2+ tricks vs optimal lead
ALTER TABLE session_hands ADD COLUMN opening_lead_quality TEXT DEFAULT NULL;

-- Tricks cost by opening lead (0 = optimal, positive = tricks given away)
ALTER TABLE session_hands ADD COLUMN opening_lead_cost INTEGER DEFAULT 0;

-- ============================================================================
-- PART 2: Full DD Matrix Storage
-- ============================================================================

-- Store full 20-result DD table as JSON for rich analysis
-- Format: {"N":{"NT":9,"S":10,"H":8,"D":7,"C":6},"E":{...},"S":{...},"W":{...}}
-- This enables "What if you played in Hearts?" analysis
-- Note: par_score and par_contract already exist from migration 007
ALTER TABLE session_hands ADD COLUMN dd_matrix TEXT DEFAULT NULL;

-- ============================================================================
-- PART 3: Strain-Level Statistics (for Heatmap)
-- ============================================================================

-- These are computed per-hand but enable efficient aggregation queries
-- Contract strain normalized to single char: 'N'=NT, 'S'=Spades, 'H'=Hearts, 'D'=Diamonds, 'C'=Clubs
-- (contract_strain column already exists, this just documents its use)

-- ============================================================================
-- PART 4: ACBL/PBN Import Support - Enhanced Tables
-- ============================================================================

-- Note: imported_hands table already exists from migration 007
-- We add a new table for field results (traveling scores)

-- Field results from other tables at the same event
-- Enables comparative analysis: "You scored 420, field average was 380"
CREATE TABLE IF NOT EXISTS imported_field_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    imported_hand_id INTEGER NOT NULL,

    -- Table/pair identification
    table_number INTEGER,
    round_number INTEGER,
    ns_pair_number INTEGER,
    ew_pair_number INTEGER,
    ns_pair_names TEXT,
    ew_pair_names TEXT,

    -- Contract and result
    contract_level INTEGER CHECK(contract_level BETWEEN 1 AND 7 OR contract_level IS NULL),
    contract_strain TEXT,
    contract_declarer TEXT CHECK(contract_declarer IN ('N', 'E', 'S', 'W') OR contract_declarer IS NULL),
    contract_doubled INTEGER DEFAULT 0 CHECK(contract_doubled IN (0, 1, 2)),

    -- Result
    tricks_taken INTEGER CHECK(tricks_taken BETWEEN 0 AND 13 OR tricks_taken IS NULL),
    score_ns INTEGER,  -- Score from NS perspective (standard)

    -- Opening lead (if available in PBN)
    opening_lead TEXT,

    -- Matchpoints / IMPs (if available)
    matchpoints_ns REAL,
    matchpoints_ew REAL,
    matchpoints_pct_ns REAL,
    matchpoints_pct_ew REAL,
    imps_ns REAL,
    imps_ew REAL,

    FOREIGN KEY(imported_hand_id) REFERENCES imported_hands(id) ON DELETE CASCADE
);

-- ============================================================================
-- PART 5: Indexes for Performance
-- ============================================================================

-- Index for quadrant queries (dashboard aggregation)
CREATE INDEX IF NOT EXISTS idx_session_hands_quadrant
    ON session_hands(quadrant) WHERE quadrant IS NOT NULL;

-- Index for bidding efficiency queries
CREATE INDEX IF NOT EXISTS idx_session_hands_bid_efficiency
    ON session_hands(bid_efficiency) WHERE bid_efficiency IS NOT NULL;

-- Index for opening lead analysis
CREATE INDEX IF NOT EXISTS idx_session_hands_opening_lead
    ON session_hands(opening_lead_quality) WHERE opening_lead_quality IS NOT NULL;

-- Index for field results lookup
CREATE INDEX IF NOT EXISTS idx_imported_field_results_hand
    ON imported_field_results(imported_hand_id);

-- ============================================================================
-- PART 6: Aggregated User Statistics View
-- ============================================================================

-- Drop existing view if it exists (safe recreation)
DROP VIEW IF EXISTS v_user_analysis_stats;

-- Comprehensive analysis statistics per user
-- Used by dashboard to show bidding/play efficiency metrics
CREATE VIEW v_user_analysis_stats AS
SELECT
    gs.user_id,

    -- Total hands analyzed
    COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END) as total_analyzed_hands,

    -- Quadrant distribution (counts)
    SUM(CASE WHEN sh.quadrant = 'Q1' THEN 1 ELSE 0 END) as q1_count,  -- Good/Good
    SUM(CASE WHEN sh.quadrant = 'Q2' THEN 1 ELSE 0 END) as q2_count,  -- Good Bid/Bad Play
    SUM(CASE WHEN sh.quadrant = 'Q3' THEN 1 ELSE 0 END) as q3_count,  -- Bad/Bad
    SUM(CASE WHEN sh.quadrant = 'Q4' THEN 1 ELSE 0 END) as q4_count,  -- Bad Bid/Good Play

    -- Quadrant distribution (percentages)
    ROUND(100.0 * SUM(CASE WHEN sh.quadrant = 'Q1' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END), 0), 1) as q1_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.quadrant = 'Q2' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END), 0), 1) as q2_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.quadrant = 'Q3' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END), 0), 1) as q3_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.quadrant = 'Q4' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.quadrant IS NOT NULL THEN 1 END), 0), 1) as q4_pct,

    -- Bidding efficiency (counts)
    SUM(CASE WHEN sh.bid_efficiency = 'optimal' THEN 1 ELSE 0 END) as optimal_bids,
    SUM(CASE WHEN sh.bid_efficiency = 'underbid' THEN 1 ELSE 0 END) as underbids,
    SUM(CASE WHEN sh.bid_efficiency = 'overbid' THEN 1 ELSE 0 END) as overbids,

    -- Bidding efficiency (percentages)
    ROUND(100.0 * SUM(CASE WHEN sh.bid_efficiency = 'optimal' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.bid_efficiency IS NOT NULL THEN 1 END), 0), 1) as optimal_bid_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.bid_efficiency = 'underbid' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.bid_efficiency IS NOT NULL THEN 1 END), 0), 1) as underbid_pct,
    ROUND(100.0 * SUM(CASE WHEN sh.bid_efficiency = 'overbid' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(CASE WHEN sh.bid_efficiency IS NOT NULL THEN 1 END), 0), 1) as overbid_pct,

    -- Total points left on table (from underbidding)
    SUM(COALESCE(sh.points_left_on_table, 0)) as total_points_left,
    AVG(CASE WHEN sh.points_left_on_table > 0 THEN sh.points_left_on_table END) as avg_points_left_when_underbid,

    -- Opening lead statistics
    SUM(CASE WHEN sh.opening_lead_quality = 'optimal' THEN 1 ELSE 0 END) as optimal_leads,
    SUM(CASE WHEN sh.opening_lead_quality = 'neutral' THEN 1 ELSE 0 END) as neutral_leads,
    SUM(CASE WHEN sh.opening_lead_quality = 'leaking' THEN 1 ELSE 0 END) as leaking_leads,
    SUM(COALESCE(sh.opening_lead_cost, 0)) as total_lead_cost,

    -- Play quality (tricks vs DD)
    AVG(CASE WHEN sh.dd_tricks IS NOT NULL AND sh.tricks_taken IS NOT NULL
        THEN sh.tricks_taken - sh.dd_tricks END) as avg_tricks_vs_dd,

    -- Contract success rate (already available, included for completeness)
    SUM(CASE WHEN sh.user_was_declarer AND sh.made THEN 1 ELSE 0 END) as contracts_made,
    SUM(CASE WHEN sh.user_was_declarer THEN 1 ELSE 0 END) as contracts_declared,

    -- Par comparison (when par_score available)
    AVG(CASE WHEN sh.par_score IS NOT NULL AND sh.hand_score IS NOT NULL
        THEN sh.hand_score - sh.par_score END) as avg_score_vs_par

FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
GROUP BY gs.user_id;

-- ============================================================================
-- PART 7: Strain Accuracy View (for Heatmap)
-- ============================================================================

DROP VIEW IF EXISTS v_user_strain_accuracy;

-- Bidding accuracy broken down by contract strain
-- Shows which suits the user bids most accurately
CREATE VIEW v_user_strain_accuracy AS
SELECT
    gs.user_id,
    sh.contract_strain as strain,

    -- Total contracts in this strain
    COUNT(*) as total_contracts,

    -- Makeable contracts (DD says it should make)
    SUM(CASE WHEN sh.dd_tricks >= sh.tricks_needed THEN 1 ELSE 0 END) as makeable_contracts,

    -- Actually made contracts
    SUM(CASE WHEN sh.made THEN 1 ELSE 0 END) as made_contracts,

    -- Accuracy: % of contracts that were makeable
    ROUND(100.0 * SUM(CASE WHEN sh.dd_tricks >= sh.tricks_needed THEN 1 ELSE 0 END) /
          NULLIF(COUNT(*), 0), 1) as bidding_accuracy_pct,

    -- Execution: % of makeable contracts that were actually made
    ROUND(100.0 * SUM(CASE WHEN sh.made AND sh.dd_tricks >= sh.tricks_needed THEN 1 ELSE 0 END) /
          NULLIF(SUM(CASE WHEN sh.dd_tricks >= sh.tricks_needed THEN 1 ELSE 0 END), 0), 1) as execution_pct,

    -- Average tricks vs DD for this strain
    AVG(sh.tricks_taken - sh.dd_tricks) as avg_tricks_vs_dd

FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
WHERE sh.contract_strain IS NOT NULL
  AND sh.dd_tricks IS NOT NULL
GROUP BY gs.user_id, sh.contract_strain;

-- ============================================================================
-- PART 8: Recent Boards for Quadrant Chart
-- ============================================================================

DROP VIEW IF EXISTS v_recent_boards_for_quadrant;

-- Pre-formatted data for quadrant chart visualization
-- Returns last N boards with all needed fields for plotting
CREATE VIEW v_recent_boards_for_quadrant AS
SELECT
    sh.id as hand_id,
    sh.session_id,
    gs.user_id,
    sh.hand_number,
    sh.played_at,

    -- Contract display
    CASE
        WHEN sh.contract_level IS NULL THEN 'Pass'
        ELSE printf('%d%s', sh.contract_level, sh.contract_strain) ||
             CASE sh.contract_doubled WHEN 1 THEN 'X' WHEN 2 THEN 'XX' ELSE '' END
    END as contract_display,
    sh.contract_declarer,

    -- Results
    sh.tricks_taken,
    sh.tricks_needed,
    sh.dd_tricks,
    sh.made,
    sh.hand_score,
    sh.par_score,

    -- Analysis results
    sh.quadrant,
    sh.bid_efficiency,
    sh.points_left_on_table,

    -- For circle styling (solid vs hollow)
    sh.user_was_declarer,

    -- Play delta for positioning within quadrant
    CASE
        WHEN sh.dd_tricks IS NOT NULL AND sh.tricks_taken IS NOT NULL
        THEN sh.tricks_taken - sh.dd_tricks
        ELSE 0
    END as play_delta,

    -- Bid delta for positioning (score vs par)
    CASE
        WHEN sh.par_score IS NOT NULL AND sh.hand_score IS NOT NULL
        THEN sh.hand_score - sh.par_score
        ELSE 0
    END as bid_delta

FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
WHERE sh.quadrant IS NOT NULL
ORDER BY sh.played_at DESC;

-- ============================================================================
-- Migration Complete
-- ============================================================================
--
-- New columns added to session_hands:
--   - decay_curve (TEXT/JSON)
--   - major_errors (TEXT/JSON)
--   - quadrant (TEXT: Q1/Q2/Q3/Q4)
--   - bid_efficiency (TEXT: optimal/underbid/overbid)
--   - points_left_on_table (INTEGER)
--   - opening_lead_card (TEXT)
--   - opening_lead_quality (TEXT: optimal/neutral/leaking)
--   - opening_lead_cost (INTEGER)
--   - dd_matrix (TEXT/JSON)
--
-- New tables:
--   - imported_field_results (for ACBL traveling scores)
--
-- New views:
--   - v_user_analysis_stats (aggregate user metrics)
--   - v_user_strain_accuracy (per-strain bidding accuracy)
--   - v_recent_boards_for_quadrant (chart data)
--
-- To apply: sqlite3 bridge.db < migrations/011_add_comprehensive_analysis.sql
-- To rollback: See comments at top of file
-- ============================================================================
