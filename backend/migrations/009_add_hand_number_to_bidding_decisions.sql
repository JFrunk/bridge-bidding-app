-- Migration: Add hand_number column to bidding_decisions table
-- This allows filtering bidding decisions by specific hand within a session
-- Matches the pattern used in play_decisions

-- Create new index for efficient querying by session + hand
CREATE INDEX IF NOT EXISTS idx_bidding_decisions_session_hand
ON bidding_decisions(session_id, hand_number);
