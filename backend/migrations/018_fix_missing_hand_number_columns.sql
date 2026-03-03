-- Migration: Fix missing hand_number columns
-- Migrations 008 and 009 created indexes on hand_number but never added the columns.
-- This corrective migration adds the missing columns to both tables.

-- Add hand_number to bidding_decisions (was missing from migration 009)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'bidding_decisions' AND column_name = 'hand_number'
    ) THEN
        ALTER TABLE bidding_decisions ADD COLUMN hand_number INTEGER;
    END IF;
END $$;

-- Add hand_number to play_decisions (was missing from migration 008)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'play_decisions' AND column_name = 'hand_number'
    ) THEN
        ALTER TABLE play_decisions ADD COLUMN hand_number INTEGER;
    END IF;
END $$;

-- Recreate indexes (safe with IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_bidding_decisions_session_hand
ON bidding_decisions(session_id, hand_number);

CREATE INDEX IF NOT EXISTS idx_play_decisions_session_hand
ON play_decisions(session_id, hand_number);
