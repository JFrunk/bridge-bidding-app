-- Migration: Add hand_number column to play_decisions table
-- This allows filtering play decisions by specific hand within a session
-- Previously, all plays in a session were grouped together, causing inflated counts

-- Check if column exists and add if not
-- Note: This migration may fail if column already exists - that's OK
-- We use a pattern that SQLite tolerates for re-runs

-- First, try to add column (ignore error if already exists)
-- The migration runner will catch the error gracefully

-- Create new index for efficient querying by session + hand
CREATE INDEX IF NOT EXISTS idx_play_decisions_session_hand
ON play_decisions(session_id, hand_number);
