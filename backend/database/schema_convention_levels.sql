-- ============================================================================
-- Convention Levels Database Schema
-- Part of Structured Learning Platform
-- ============================================================================

-- Convention definitions (metadata from ConventionRegistry)
CREATE TABLE IF NOT EXISTS conventions (
    convention_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT NOT NULL CHECK(level IN ('essential', 'intermediate', 'advanced')),
    category TEXT,
    frequency TEXT,
    complexity TEXT,
    description TEXT,
    short_description TEXT,
    learning_time_minutes INTEGER,
    practice_hands_required INTEGER,
    passing_accuracy REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Convention prerequisites (many-to-many)
CREATE TABLE IF NOT EXISTS convention_prerequisites (
    convention_id TEXT NOT NULL,
    prerequisite_id TEXT NOT NULL,
    prerequisite_type TEXT NOT NULL CHECK(prerequisite_type IN ('skill', 'convention')),
    PRIMARY KEY (convention_id, prerequisite_id),
    FOREIGN KEY (convention_id) REFERENCES conventions(convention_id)
);

-- User convention progress
CREATE TABLE IF NOT EXISTS user_convention_progress (
    user_id INTEGER NOT NULL,
    convention_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'locked' CHECK(status IN ('locked', 'unlocked', 'in_progress', 'mastered')),
    attempts INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0.0,
    started_at TIMESTAMP,
    mastered_at TIMESTAMP,
    last_practiced TIMESTAMP,
    PRIMARY KEY (user_id, convention_id),
    FOREIGN KEY (convention_id) REFERENCES conventions(convention_id)
);

-- Convention practice history (detailed tracking)
CREATE TABLE IF NOT EXISTS convention_practice_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    convention_id TEXT NOT NULL,
    hand_id TEXT,
    user_bid TEXT,
    correct_bid TEXT,
    was_correct BOOLEAN NOT NULL,
    hints_used INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (convention_id) REFERENCES conventions(convention_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_convention_progress_user
    ON user_convention_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_convention_progress_status
    ON user_convention_progress(status);
CREATE INDEX IF NOT EXISTS idx_convention_practice_history_user
    ON convention_practice_history(user_id, convention_id);
CREATE INDEX IF NOT EXISTS idx_convention_practice_history_timestamp
    ON convention_practice_history(timestamp);

-- Views for common queries

-- User progress summary view
CREATE VIEW IF NOT EXISTS v_user_convention_summary AS
SELECT
    user_id,
    COUNT(*) as total_conventions,
    SUM(CASE WHEN status = 'mastered' THEN 1 ELSE 0 END) as mastered_count,
    SUM(CASE WHEN status = 'unlocked' OR status = 'in_progress' THEN 1 ELSE 0 END) as available_count,
    ROUND(AVG(CASE WHEN status = 'mastered' THEN accuracy ELSE NULL END) * 100, 1) as avg_accuracy
FROM user_convention_progress
GROUP BY user_id;

-- Convention level progress view
CREATE VIEW IF NOT EXISTS v_user_level_progress AS
SELECT
    ucp.user_id,
    c.level,
    COUNT(*) as total_in_level,
    SUM(CASE WHEN ucp.status = 'mastered' THEN 1 ELSE 0 END) as mastered_in_level,
    ROUND(SUM(CASE WHEN ucp.status = 'mastered' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as level_completion_pct
FROM user_convention_progress ucp
JOIN conventions c ON ucp.convention_id = c.convention_id
GROUP BY ucp.user_id, c.level;
