-- Migration 006: Add Play Decisions Table
-- Created: 2026-01-01
-- Purpose: Add play_decisions table for DDS-based play feedback tracking
-- This mirrors bidding_decisions but for card play evaluation

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
    tricks_with_user_card INTEGER,
    tricks_with_optimal INTEGER,
    contract TEXT,
    is_declarer_side BOOLEAN DEFAULT 0,
    play_category TEXT,  -- opening_lead, following_suit, discarding, trumping
    key_concept TEXT,    -- what skill this tests
    difficulty TEXT,     -- beginner, intermediate, advanced, expert
    feedback TEXT,
    helpful_hint TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for play decision queries
CREATE INDEX IF NOT EXISTS idx_play_decisions_user_time ON play_decisions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_play_decisions_rating ON play_decisions(user_id, rating);
CREATE INDEX IF NOT EXISTS idx_play_decisions_session ON play_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_play_decisions_category ON play_decisions(user_id, play_category);
