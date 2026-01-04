-- Migration: Add analysis_source column to play_decisions
-- Tracks whether DDS or Minimax was used for analysis
-- "dds" = exact analysis, "heuristic" = Minimax fallback

ALTER TABLE play_decisions ADD COLUMN analysis_source TEXT DEFAULT 'dds';

-- Create index for monitoring Minimax fallback frequency
CREATE INDEX IF NOT EXISTS idx_play_decisions_analysis_source ON play_decisions(analysis_source);
