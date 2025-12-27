-- Migration 004: Add Learning Mode Tables
-- Created: 2025-12-26
-- Purpose: Add skill progress tracking tables for Learning Mode

-- User Skill Progress - tracks mastery of each skill
CREATE TABLE IF NOT EXISTS user_skill_progress (
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

-- Skill Practice History - records each practice attempt
CREATE TABLE IF NOT EXISTS skill_practice_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_id TEXT NOT NULL,
    skill_level INTEGER DEFAULT 0,
    hand_id TEXT,
    user_bid TEXT,
    correct_bid TEXT,
    was_correct BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_skill_progress_user ON user_skill_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_skill_progress_skill ON user_skill_progress(skill_id);
CREATE INDEX IF NOT EXISTS idx_user_skill_progress_status ON user_skill_progress(status);
CREATE INDEX IF NOT EXISTS idx_skill_practice_history_user ON skill_practice_history(user_id, skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_practice_history_timestamp ON skill_practice_history(timestamp);
