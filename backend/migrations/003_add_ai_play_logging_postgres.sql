-- Migration: Add AI Play Logging for PostgreSQL
-- Purpose: Track AI play decisions for DDS quality monitoring
-- Date: 2025-11-25
-- Run this on production to enable DDS monitoring

-- Main logging table for AI play decisions
CREATE TABLE IF NOT EXISTS ai_play_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    session_id TEXT,
    hand_number INTEGER,
    trick_number INTEGER,
    position TEXT NOT NULL CHECK(position IN ('N', 'E', 'S', 'W')),
    ai_level TEXT NOT NULL CHECK(ai_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    card_played TEXT NOT NULL,
    solve_time_ms REAL,
    used_fallback BOOLEAN DEFAULT FALSE,
    contract TEXT,
    trump_suit TEXT
);

-- Indexes for efficient DDS health queries
CREATE INDEX IF NOT EXISTS idx_ai_play_log_timestamp ON ai_play_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_play_log_ai_level ON ai_play_log(ai_level);
CREATE INDEX IF NOT EXISTS idx_ai_play_log_fallback ON ai_play_log(used_fallback);
CREATE INDEX IF NOT EXISTS idx_ai_play_log_session ON ai_play_log(session_id);

-- ============================================================================
-- USER PLAY DECISIONS (for gameplay feedback)
-- ============================================================================

CREATE TABLE IF NOT EXISTS play_decisions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id TEXT,
    position TEXT NOT NULL CHECK(position IN ('N', 'E', 'S', 'W')),
    trick_number INTEGER,
    user_card TEXT NOT NULL,
    optimal_card TEXT,
    score REAL NOT NULL,
    rating TEXT NOT NULL CHECK(rating IN ('optimal', 'good', 'suboptimal', 'blunder', 'illegal', 'not_evaluated', 'error')),
    tricks_cost INTEGER DEFAULT 0,
    contract TEXT,
    feedback TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_play_decisions_user_time ON play_decisions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_play_decisions_rating ON play_decisions(user_id, rating);
CREATE INDEX IF NOT EXISTS idx_play_decisions_session ON play_decisions(session_id);

-- Verify tables were created
SELECT 'ai_play_log and play_decisions tables created successfully' as status;
