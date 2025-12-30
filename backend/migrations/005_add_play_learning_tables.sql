-- Migration 005: Add Play Learning Mode Tables
-- Created: 2025-12-29
-- Purpose: Add play skill progress tracking tables for Card Play Learning

-- User Play Progress - tracks mastery of each play skill
CREATE TABLE IF NOT EXISTS user_play_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_id TEXT NOT NULL,
    skill_level INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0.0,
    status TEXT DEFAULT 'not_started',  -- not_started, in_progress, mastered
    started_at TIMESTAMP,
    last_practiced TIMESTAMP,
    mastered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, skill_id)
);

-- Play Practice History - records each play practice attempt
CREATE TABLE IF NOT EXISTS play_practice_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_id TEXT NOT NULL,
    skill_level INTEGER DEFAULT 0,
    hand_id TEXT,
    user_answer TEXT,
    correct_answer TEXT,
    was_correct BOOLEAN NOT NULL,
    practice_format TEXT DEFAULT 'single_decision',  -- single_decision, mini_hand, full_hand
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_play_progress_user ON user_play_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_play_progress_skill ON user_play_progress(skill_id);
CREATE INDEX IF NOT EXISTS idx_user_play_progress_status ON user_play_progress(status);
CREATE INDEX IF NOT EXISTS idx_play_practice_history_user ON play_practice_history(user_id, skill_id);
CREATE INDEX IF NOT EXISTS idx_play_practice_history_timestamp ON play_practice_history(timestamp);
