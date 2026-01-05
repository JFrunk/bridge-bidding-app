-- Migration: Add deal_data column to bidding_decisions table
-- This stores the complete deal so bidding history can be reviewed
-- without requiring session_hands records (which only get created after play completes)

-- Add deal_data column (JSON) to store all 4 hands
ALTER TABLE bidding_decisions ADD COLUMN deal_data TEXT;
