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

-- Verify table was created
SELECT 'ai_play_log table created successfully' as status;
