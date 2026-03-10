-- Migration 020: Add missing columns to play_decisions and fix ai_play_log type
-- These columns were in the CREATE TABLE schema (migration 006) but the table
-- already existed from an earlier migration, so the columns were never added.

-- Add missing trick analysis columns to play_decisions
ALTER TABLE play_decisions ADD COLUMN IF NOT EXISTS tricks_with_user_card INTEGER;
ALTER TABLE play_decisions ADD COLUMN IF NOT EXISTS tricks_with_optimal INTEGER;
ALTER TABLE play_decisions ADD COLUMN IF NOT EXISTS is_declarer_side INTEGER DEFAULT 0;
ALTER TABLE play_decisions ADD COLUMN IF NOT EXISTS key_concept TEXT;
ALTER TABLE play_decisions ADD COLUMN IF NOT EXISTS difficulty TEXT;
ALTER TABLE play_decisions ADD COLUMN IF NOT EXISTS helpful_hint TEXT;

-- Fix ai_play_log.used_fallback type: code sends INTEGER (0/1) but column is BOOLEAN
-- PostgreSQL strict typing rejects integer-to-boolean implicit cast
ALTER TABLE ai_play_log ALTER COLUMN used_fallback TYPE INTEGER USING CASE WHEN used_fallback THEN 1 ELSE 0 END;
