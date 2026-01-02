-- ============================================================================
-- Migration 007: Add DDS Analysis Storage
--
-- Adds columns to store Double Dummy Solver analysis results for each hand.
-- This enables:
-- - Post-game analysis ("What if you played 4 Spades?")
-- - Par score comparison ("Did you reach the optimal contract?")
-- - ACBL result import and analysis
-- - Training feedback based on optimal play
--
-- SQLite-compatible (no JSONB, uses TEXT for JSON storage)
-- ============================================================================

-- Add DDS analysis column to session_hands
-- Stores full DD table and par result as JSON
ALTER TABLE session_hands ADD COLUMN dds_analysis TEXT DEFAULT NULL;

-- Add par score column for quick queries (extracted from dds_analysis)
ALTER TABLE session_hands ADD COLUMN par_score INTEGER DEFAULT NULL;

-- Add par contract for quick display
ALTER TABLE session_hands ADD COLUMN par_contract TEXT DEFAULT NULL;

-- Add DD tricks for the actual contract played (for comparison)
-- This is the number of tricks declarer SHOULD make with perfect play
ALTER TABLE session_hands ADD COLUMN dd_tricks INTEGER DEFAULT NULL;

-- Index for hands with DDS analysis (for analytics queries)
CREATE INDEX IF NOT EXISTS idx_session_hands_has_analysis
    ON session_hands(id) WHERE dds_analysis IS NOT NULL;

-- Index for par score queries (e.g., "hands where par was not reached")
CREATE INDEX IF NOT EXISTS idx_session_hands_par_score
    ON session_hands(par_score) WHERE par_score IS NOT NULL;

-- ============================================================================
-- Updated view for hand history with DDS analysis
-- ============================================================================

-- Drop and recreate the view to include DDS data
DROP VIEW IF EXISTS v_hand_history_with_analysis;

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
        ELSE printf('%d%s', sh.contract_level, sh.contract_strain) ||
             CASE sh.contract_doubled
                 WHEN 1 THEN 'X'
                 WHEN 2 THEN 'XX'
                 ELSE ''
             END ||
             ' by ' || sh.contract_declarer
    END as contract_display,
    sh.tricks_taken,
    sh.tricks_needed,
    sh.made,
    sh.hand_score,
    sh.ns_total_after,
    sh.ew_total_after,
    sh.user_was_declarer,

    -- DDS Analysis fields
    sh.dd_tricks,
    sh.par_score,
    sh.par_contract,

    -- Calculated fields for analysis
    CASE
        WHEN sh.dd_tricks IS NOT NULL AND sh.tricks_taken IS NOT NULL
        THEN sh.tricks_taken - sh.dd_tricks
        ELSE NULL
    END as tricks_vs_dd,  -- Positive = better than DD, Negative = worse

    CASE
        WHEN sh.dd_tricks IS NOT NULL AND sh.tricks_taken IS NOT NULL
        THEN sh.tricks_taken >= sh.dd_tricks
        ELSE NULL
    END as played_optimally,

    sh.dds_analysis,  -- Full JSON analysis data
    sh.played_at

FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
ORDER BY sh.session_id, sh.hand_number;

-- ============================================================================
-- New table for imported hands (for ACBL result import)
-- ============================================================================

CREATE TABLE IF NOT EXISTS imported_hands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Import metadata
    source TEXT NOT NULL DEFAULT 'pbn',  -- 'pbn', 'lin', 'acbl'
    source_file TEXT,  -- Original filename
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Event metadata (from PBN tags)
    event_name TEXT,
    event_date TEXT,
    board_number INTEGER,

    -- Deal setup
    dealer TEXT CHECK(dealer IN ('N', 'E', 'S', 'W')),
    vulnerability TEXT,

    -- Hand data (PBN format)
    deal_pbn TEXT NOT NULL,  -- Full deal: "N:AKQ.xxx.xxx.xxx ..."

    -- Auction (if available)
    auction TEXT,  -- JSON array of bids

    -- Contract and result (if available)
    contract_level INTEGER CHECK(contract_level BETWEEN 1 AND 7 OR contract_level IS NULL),
    contract_strain TEXT,
    contract_declarer TEXT CHECK(contract_declarer IN ('N', 'E', 'S', 'W') OR contract_declarer IS NULL),
    contract_doubled INTEGER DEFAULT 0,
    tricks_taken INTEGER,

    -- Scoring (from import)
    score_ns INTEGER,
    score_matchpoints REAL,  -- For matchpoint games
    score_imps INTEGER,      -- For IMP games

    -- DDS Analysis (populated after import)
    dds_analysis TEXT,
    par_score INTEGER,
    par_contract TEXT,
    dd_tricks INTEGER,

    -- Analysis status
    analysis_status TEXT DEFAULT 'pending',  -- 'pending', 'completed', 'failed'

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for imported hands
CREATE INDEX IF NOT EXISTS idx_imported_hands_user
    ON imported_hands(user_id, imported_at DESC);

CREATE INDEX IF NOT EXISTS idx_imported_hands_event
    ON imported_hands(event_name, board_number);

CREATE INDEX IF NOT EXISTS idx_imported_hands_analysis_status
    ON imported_hands(analysis_status) WHERE analysis_status = 'pending';
