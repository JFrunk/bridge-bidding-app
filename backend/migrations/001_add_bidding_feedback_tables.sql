-- Migration: Add Bidding Feedback System Tables
-- Phase 1: Real-time bidding feedback and quality tracking
-- Created: 2025-10-17
-- Description: Adds tables to support detailed bidding feedback, quality scoring,
--              and integration with learning dashboard

-- ============================================================================
-- Table: bidding_decisions
-- Purpose: Store detailed feedback for every bidding decision
-- ============================================================================
CREATE TABLE IF NOT EXISTS bidding_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Hand Analysis Reference (optional, for post-hand analysis)
    hand_analysis_id INTEGER,

    -- User Info
    user_id INTEGER NOT NULL,
    session_id TEXT,

    -- Bidding Context
    bid_number INTEGER NOT NULL,          -- Position in auction (1-based)
    position TEXT NOT NULL,               -- 'North', 'East', 'South', 'West'
    dealer TEXT,                          -- Dealer for this hand
    vulnerability TEXT,                   -- Vulnerability state

    -- Bidding Decision
    user_bid TEXT NOT NULL,               -- What user bid (e.g., "2♥", "Pass")
    optimal_bid TEXT NOT NULL,            -- AI recommended bid
    auction_before TEXT,                  -- JSON: auction history before this bid

    -- Evaluation
    correctness TEXT NOT NULL,            -- 'optimal', 'acceptable', 'suboptimal', 'error'
    score REAL NOT NULL,                  -- 0-10 scale
    impact TEXT,                          -- 'none', 'minor', 'significant', 'critical'

    -- Categorization
    error_category TEXT,                  -- From ErrorCategorizer (if error)
    error_subcategory TEXT,
    key_concept TEXT,                     -- e.g., "Support points", "HCP counting"
    difficulty TEXT,                      -- 'beginner', 'intermediate', 'advanced'

    -- Explanation (stored for history)
    helpful_hint TEXT,                    -- Short actionable advice
    reasoning TEXT,                       -- Full explanation

    -- Metadata
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_bidding_decisions_user_time
    ON bidding_decisions(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_bidding_decisions_correctness
    ON bidding_decisions(user_id, correctness, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_bidding_decisions_category
    ON bidding_decisions(user_id, error_category, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_bidding_decisions_concept
    ON bidding_decisions(user_id, key_concept, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_bidding_decisions_session
    ON bidding_decisions(session_id, bid_number);

-- ============================================================================
-- Table: hand_analyses (placeholder for Phase 3)
-- Purpose: Store comprehensive post-hand analysis
-- Note: This table will be fully populated in Phase 3, but we create it now
--       for foreign key references
-- ============================================================================
CREATE TABLE IF NOT EXISTS hand_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- User Info
    user_id INTEGER NOT NULL,
    session_id TEXT,

    -- Hand Context
    dealer TEXT,
    vulnerability TEXT,
    contract TEXT,

    -- Scores
    overall_score REAL,
    bidding_score REAL,
    play_score REAL,

    -- Full analysis (JSON)
    analysis_data TEXT,                   -- JSON blob with complete analysis

    -- Hand data (JSON)
    hands_data TEXT,                      -- JSON: all four hands
    auction_data TEXT,                    -- JSON: complete auction

    -- Metadata
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_hand_analyses_user_time
    ON hand_analyses(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_hand_analyses_contract
    ON hand_analyses(user_id, contract, timestamp DESC);

-- ============================================================================
-- View: v_bidding_feedback_stats
-- Purpose: Aggregate bidding feedback statistics for dashboard
-- ============================================================================
CREATE VIEW IF NOT EXISTS v_bidding_feedback_stats AS
SELECT
    user_id,
    COUNT(*) as total_decisions,

    -- Quality metrics
    AVG(score) as avg_score,

    -- Correctness breakdown
    SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
    SUM(CASE WHEN correctness = 'acceptable' THEN 1 ELSE 0 END) as acceptable_count,
    SUM(CASE WHEN correctness = 'suboptimal' THEN 1 ELSE 0 END) as suboptimal_count,
    SUM(CASE WHEN correctness = 'error' THEN 1 ELSE 0 END) as error_count,

    -- Rates
    CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) as optimal_rate,
    CAST(SUM(CASE WHEN correctness = 'error' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) as error_rate,

    -- Impact breakdown
    SUM(CASE WHEN impact = 'critical' THEN 1 ELSE 0 END) as critical_errors,
    SUM(CASE WHEN impact = 'significant' THEN 1 ELSE 0 END) as significant_errors,

    -- Recent activity (last 30 days)
    SUM(CASE WHEN timestamp >= datetime('now', '-30 days') THEN 1 ELSE 0 END) as recent_decisions,

    -- Date range
    MIN(timestamp) as first_decision,
    MAX(timestamp) as last_decision
FROM bidding_decisions
GROUP BY user_id;

-- ============================================================================
-- View: v_recent_bidding_decisions
-- Purpose: Show recent decisions for dashboard display
-- ============================================================================
CREATE VIEW IF NOT EXISTS v_recent_bidding_decisions AS
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

    -- Format for display
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

-- ============================================================================
-- View: v_concept_mastery
-- Purpose: Track mastery of key concepts
-- ============================================================================
CREATE VIEW IF NOT EXISTS v_concept_mastery AS
SELECT
    user_id,
    key_concept,
    COUNT(*) as attempts,
    AVG(score) as avg_score,
    SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
    CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) as mastery_rate,
    MIN(timestamp) as first_attempt,
    MAX(timestamp) as last_attempt,

    -- Status classification
    CASE
        WHEN CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) >= 0.90 THEN 'mastered'
        WHEN CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) >= 0.70 THEN 'proficient'
        WHEN CAST(SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) >= 0.50 THEN 'learning'
        ELSE 'needs_practice'
    END as status

FROM bidding_decisions
WHERE key_concept IS NOT NULL
GROUP BY user_id, key_concept;

-- ============================================================================
-- Migration Notes:
--
-- This migration adds the foundation for Phase 1: Bidding Feedback
--
-- Tables added:
-- 1. bidding_decisions - Core feedback storage
-- 2. hand_analyses - Placeholder for future phases
--
-- Views added:
-- 1. v_bidding_feedback_stats - Dashboard statistics
-- 2. v_recent_bidding_decisions - Recent decisions for display
-- 3. v_concept_mastery - Concept-level tracking
--
-- This migration is backward compatible and does not modify existing tables.
-- It extends the learning analytics system with detailed bidding feedback.
-- ============================================================================
