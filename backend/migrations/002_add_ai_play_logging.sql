-- Migration: AI Play Logging for DDS Quality Monitoring
-- Purpose: Track AI play decisions for quality analysis and monitoring
-- Date: 2025-10-23

-- Main logging table for AI play decisions
CREATE TABLE IF NOT EXISTS ai_play_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Timing
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Session context
    session_id TEXT,
    hand_number INTEGER,
    trick_number INTEGER,

    -- AI context
    position TEXT NOT NULL CHECK(position IN ('N', 'E', 'S', 'W')),
    ai_level TEXT NOT NULL CHECK(ai_level IN ('beginner', 'intermediate', 'advanced', 'expert')),

    -- Play decision
    card_played TEXT NOT NULL,  -- Format: "AS" (Ace of Spades), "KH" (King of Hearts)

    -- Performance metrics
    solve_time_ms REAL,  -- Time taken to choose card
    used_fallback BOOLEAN DEFAULT 0,  -- Whether DDS crashed and fallback was used

    -- Optional: Contract context for deeper analysis
    contract TEXT,  -- Format: "4S" or "3NT"
    trump_suit TEXT,  -- ♠, ♥, ♦, ♣, or NULL for NT

    -- Indexing for common queries
    FOREIGN KEY (session_id) REFERENCES game_sessions(id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_ai_play_log_timestamp
    ON ai_play_log(timestamp);

CREATE INDEX IF NOT EXISTS idx_ai_play_log_session
    ON ai_play_log(session_id);

CREATE INDEX IF NOT EXISTS idx_ai_play_log_ai_level
    ON ai_play_log(ai_level);

CREATE INDEX IF NOT EXISTS idx_ai_play_log_fallback
    ON ai_play_log(used_fallback);

-- View for dashboard metrics (last 24 hours)
CREATE VIEW IF NOT EXISTS v_ai_health_24h AS
SELECT
    COUNT(*) as total_plays,
    COUNT(DISTINCT session_id) as unique_sessions,
    ai_level,
    AVG(solve_time_ms) as avg_solve_time_ms,
    MAX(solve_time_ms) as max_solve_time_ms,
    MIN(solve_time_ms) as min_solve_time_ms,
    AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as fallback_rate,
    COUNT(CASE WHEN used_fallback THEN 1 END) as fallback_count
FROM ai_play_log
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY ai_level;

-- View for per-session quality metrics
CREATE VIEW IF NOT EXISTS v_session_ai_quality AS
SELECT
    session_id,
    ai_level,
    COUNT(*) as plays_count,
    AVG(solve_time_ms) as avg_solve_time_ms,
    MAX(solve_time_ms) as max_solve_time_ms,
    SUM(CASE WHEN used_fallback THEN 1 ELSE 0 END) as fallback_count,
    MIN(timestamp) as session_start,
    MAX(timestamp) as session_end
FROM ai_play_log
WHERE session_id IS NOT NULL
GROUP BY session_id, ai_level;

-- View for overall DDS health
CREATE VIEW IF NOT EXISTS v_dds_health_summary AS
SELECT
    COUNT(*) as total_plays_all_time,
    COUNT(DISTINCT DATE(timestamp)) as days_with_data,
    AVG(solve_time_ms) as avg_solve_time_ms,
    AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as overall_fallback_rate,
    MAX(timestamp) as last_play_time
FROM ai_play_log;
