-- Migration: Add signal columns to play_decisions table
-- Purpose: Store tactical signal reasoning for educational feedback
-- Date: 2025-01-05

-- Add signal_reason column - explains WHY a card was chosen from equivalence set
ALTER TABLE play_decisions ADD COLUMN signal_reason TEXT;

-- Add signal_heuristic column - which heuristic was applied (e.g., MIN_OF_EQUALS)
ALTER TABLE play_decisions ADD COLUMN signal_heuristic TEXT;

-- Add signal_context column - the play context (e.g., SECOND_HAND_FOLLOW)
ALTER TABLE play_decisions ADD COLUMN signal_context TEXT;

-- Add is_signal_optimal column - whether the play follows standard conventions
ALTER TABLE play_decisions ADD COLUMN is_signal_optimal BOOLEAN DEFAULT 1;

-- Create index for signal-related queries
CREATE INDEX IF NOT EXISTS idx_play_decisions_signal ON play_decisions(user_id, is_signal_optimal);
