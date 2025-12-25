-- Migration 002: Add play_decisions table for play feedback system
-- Created: 2025-11-26
-- Description: Stores user play decisions for dashboard analytics and learning feedback

-- User play decision logging for dashboard analytics
-- Similar to bidding_decisions but for card play evaluation
CREATE TABLE IF NOT EXISTS play_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for play decision queries
CREATE INDEX IF NOT EXISTS idx_play_decisions_user_time ON play_decisions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_play_decisions_rating ON play_decisions(user_id, rating);
CREATE INDEX IF NOT EXISTS idx_play_decisions_session ON play_decisions(session_id);

-- AI play logging table (for DDS quality monitoring)
CREATE TABLE IF NOT EXISTS ai_play_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position TEXT NOT NULL CHECK(position IN ('N', 'E', 'S', 'W')),
    ai_level TEXT NOT NULL,
    card_played TEXT NOT NULL,
    solve_time_ms INTEGER,
    used_fallback INTEGER DEFAULT 0,
    session_id TEXT,
    hand_number INTEGER,
    trick_number INTEGER,
    contract TEXT,
    trump_suit TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for AI play log queries
CREATE INDEX IF NOT EXISTS idx_ai_play_log_timestamp ON ai_play_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_play_log_ai_level ON ai_play_log(ai_level);
CREATE INDEX IF NOT EXISTS idx_ai_play_log_fallback ON ai_play_log(used_fallback);
