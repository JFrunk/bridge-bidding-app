-- Migration: 014_add_acbl_import_tables.sql
-- Purpose: Add tables for ACBL PBN tournament import and analysis
-- Date: 2026-01-05

-- =============================================================================
-- TABLE: imported_tournaments
-- Stores tournament/event metadata from imported PBN files
-- =============================================================================
CREATE TABLE IF NOT EXISTS imported_tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Event metadata from PBN tags
    event_name TEXT NOT NULL DEFAULT '',
    event_date TEXT,
    event_site TEXT,
    event_format TEXT,           -- 'Duplicate', 'Swiss', 'Round-robin', 'Teams'
    scoring_method TEXT,         -- 'Matchpoints', 'IMPs', 'Teams', 'BAM'

    -- Import source tracking
    source TEXT DEFAULT 'pbn',   -- 'pbn', 'bbo', 'acbl_live', 'common_game'
    source_filename TEXT,
    source_content_hash TEXT,    -- SHA256 hash for deduplication

    -- Import status
    import_status TEXT DEFAULT 'processing',  -- 'processing', 'analyzing', 'complete', 'failed'
    import_error TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    -- Statistics (updated as analysis progresses)
    total_hands INTEGER DEFAULT 0,
    hands_analyzed INTEGER DEFAULT 0,
    hands_with_errors INTEGER DEFAULT 0,

    -- Aggregate audit results (populated after analysis)
    alignment_rate REAL,          -- Percentage of hands matching engine logic
    total_potential_savings INTEGER,
    average_score_delta REAL,
    survival_rate REAL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =============================================================================
-- TABLE: imported_hands
-- Stores individual hands/boards from PBN files with full analysis
-- =============================================================================
CREATE TABLE IF NOT EXISTS imported_hands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    -- Board identification
    board_number INTEGER,

    -- Deal core data (from PBN)
    dealer TEXT CHECK(dealer IN ('N', 'E', 'S', 'W')),
    vulnerability TEXT,           -- 'None', 'NS', 'EW', 'Both'
    deal_pbn TEXT NOT NULL,       -- Full 4-hand deal in PBN format
    deal_json TEXT,               -- JSON representation for quick access

    -- Individual hands (PBN format: S.H.D.C)
    hand_north TEXT,
    hand_east TEXT,
    hand_south TEXT,
    hand_west TEXT,

    -- Auction (from PBN)
    auction_history TEXT,         -- JSON array of bids
    auction_raw TEXT,             -- Original multi-line auction text

    -- Contract and result (tournament ground truth)
    contract_level INTEGER,
    contract_strain TEXT,
    contract_doubled INTEGER DEFAULT 0,  -- 0=undoubled, 1=doubled, 2=redoubled
    contract_declarer TEXT,
    tricks_taken INTEGER,
    score_ns INTEGER,
    score_ew INTEGER,
    matchpoints_earned REAL,
    imps_earned INTEGER,

    -- V3 Engine analysis
    optimal_bid TEXT,
    matched_rule TEXT,
    rule_tier INTEGER,
    theoretical_score INTEGER,
    expected_tricks INTEGER,

    -- Survival/Panic metrics (from DAS)
    panic_index INTEGER DEFAULT 0,
    survival_status TEXT,         -- 'SAFE', 'SURVIVED', 'FAILED', 'LUCKY'
    rescue_action TEXT,

    -- DDS analysis (populated by background job)
    dds_analysis TEXT,            -- Full JSON analysis
    par_score INTEGER,
    par_contract TEXT,
    dd_tricks INTEGER,

    -- Comparative audit results
    is_logic_aligned INTEGER DEFAULT 0,  -- Boolean: tournament matched engine
    is_falsified INTEGER DEFAULT 0,      -- Boolean: tournament beat engine
    score_delta INTEGER,                 -- tournament_score - theoretical_score
    potential_savings INTEGER,           -- Points left on table
    bidding_efficiency TEXT,             -- 'optimal', 'underbid', 'overbid'

    -- Educational categorization
    audit_category TEXT,          -- 'lucky_overbid', 'penalty_trap', 'logic_aligned', etc.
    educational_feedback TEXT,    -- Human-readable explanation
    reasoning TEXT,               -- Detailed reasoning

    -- Quadrant classification (from comprehensive analysis)
    quadrant TEXT,                -- 'Q1', 'Q2', 'Q3', 'Q4'
    bidding_quality TEXT,         -- 'excellent', 'good', 'average', 'poor'
    play_quality TEXT,            -- 'excellent', 'good', 'average', 'poor'

    -- Analysis status
    analysis_status TEXT DEFAULT 'pending',  -- 'pending', 'analyzing', 'complete', 'failed'
    analysis_error TEXT,
    analyzed_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (tournament_id) REFERENCES imported_tournaments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(tournament_id, board_number)
);

-- =============================================================================
-- INDEXES for performance
-- =============================================================================

-- Tournament queries
CREATE INDEX IF NOT EXISTS idx_imported_tournaments_user_id
    ON imported_tournaments(user_id);
CREATE INDEX IF NOT EXISTS idx_imported_tournaments_status
    ON imported_tournaments(import_status);
CREATE INDEX IF NOT EXISTS idx_imported_tournaments_date
    ON imported_tournaments(event_date);

-- Hand queries
CREATE INDEX IF NOT EXISTS idx_imported_hands_tournament_id
    ON imported_hands(tournament_id);
CREATE INDEX IF NOT EXISTS idx_imported_hands_user_id
    ON imported_hands(user_id);
CREATE INDEX IF NOT EXISTS idx_imported_hands_analysis_status
    ON imported_hands(analysis_status);
CREATE INDEX IF NOT EXISTS idx_imported_hands_audit_category
    ON imported_hands(audit_category);
CREATE INDEX IF NOT EXISTS idx_imported_hands_is_falsified
    ON imported_hands(is_falsified);
CREATE INDEX IF NOT EXISTS idx_imported_hands_quadrant
    ON imported_hands(quadrant);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_imported_hands_user_status
    ON imported_hands(user_id, analysis_status);

-- =============================================================================
-- TRIGGER: Update timestamp on imported_hands modification
-- =============================================================================
CREATE TRIGGER IF NOT EXISTS update_imported_hands_timestamp
AFTER UPDATE ON imported_hands
BEGIN
    UPDATE imported_hands
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
