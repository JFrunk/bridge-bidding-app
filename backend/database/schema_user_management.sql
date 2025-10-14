-- ============================================================================
-- User Management & Learning Analytics Database Schema
-- Part of Common Mistake Detection System
-- ============================================================================

-- Core Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_activity TIMESTAMP,
    timezone TEXT DEFAULT 'UTC',
    preferences TEXT,  -- JSON: UI preferences, notification settings, etc.
    CONSTRAINT valid_username CHECK(length(username) >= 3)
);

-- User Settings (Privacy & Preferences)
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    -- Privacy Settings
    tracking_enabled BOOLEAN DEFAULT TRUE,
    share_progress BOOLEAN DEFAULT FALSE,
    show_in_leaderboards BOOLEAN DEFAULT FALSE,

    -- Notification Preferences
    email_weekly_summary BOOLEAN DEFAULT TRUE,
    email_milestones BOOLEAN DEFAULT TRUE,
    celebrate_achievements BOOLEAN DEFAULT TRUE,

    -- Learning Preferences
    difficulty_preference TEXT DEFAULT 'adaptive',  -- 'easy', 'adaptive', 'challenge'
    practice_reminder_time TEXT,  -- HH:MM format
    daily_goal_hands INTEGER DEFAULT 10,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User Gamification Stats
CREATE TABLE IF NOT EXISTS user_gamification (
    user_id INTEGER PRIMARY KEY,

    -- XP & Leveling
    total_xp INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    xp_to_next_level INTEGER DEFAULT 500,

    -- Streaks
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_practice_date DATE,
    streak_freezes_available INTEGER DEFAULT 0,

    -- Practice Stats
    total_hands_practiced INTEGER DEFAULT 0,
    total_practice_time_minutes INTEGER DEFAULT 0,

    -- Accuracy
    overall_accuracy REAL DEFAULT 0.0,
    recent_accuracy REAL DEFAULT 0.0,  -- Last 20 hands

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Practice Session Tracking
CREATE TABLE IF NOT EXISTS practice_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    hands_practiced INTEGER DEFAULT 0,
    correct_hands INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    session_type TEXT,  -- 'daily_practice', 'focused_drill', 'challenge', etc.
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Enhanced Practice History (replaces/extends convention_practice_history)
CREATE TABLE IF NOT EXISTS practice_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id INTEGER,

    -- Hand Information
    hand_id TEXT,
    convention_id TEXT,

    -- Bid Information
    user_bid TEXT NOT NULL,
    correct_bid TEXT NOT NULL,
    was_correct BOOLEAN NOT NULL,

    -- Error Categorization
    error_category TEXT,          -- 'wrong_level', 'wrong_strain', etc.
    error_subcategory TEXT,       -- More specific classification

    -- Hand Characteristics (JSON)
    hand_characteristics TEXT,    -- {hcp: 15, shape: "5332", has_fit: true, ...}

    -- Learning Support
    hints_used INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,

    -- XP & Feedback
    xp_earned INTEGER DEFAULT 0,
    feedback_shown TEXT,          -- What explanation was shown

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES practice_sessions(id) ON DELETE SET NULL
);

-- Mistake Patterns (Aggregated Analysis)
CREATE TABLE IF NOT EXISTS mistake_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Pattern Identification
    convention_id TEXT,
    error_category TEXT NOT NULL,
    error_subcategory TEXT,

    -- Statistics
    total_occurrences INTEGER DEFAULT 1,
    recent_occurrences INTEGER DEFAULT 1,  -- Last 30 days
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,

    -- Accuracy Tracking
    attempts_in_category INTEGER DEFAULT 0,
    correct_in_category INTEGER DEFAULT 0,
    current_accuracy REAL DEFAULT 0.0,
    previous_accuracy REAL DEFAULT 0.0,

    -- Improvement Tracking
    improvement_rate REAL DEFAULT 0.0,     -- Rate of improvement
    trend TEXT DEFAULT 'new',              -- 'new', 'improving', 'stable', 'regressing'
    status TEXT DEFAULT 'active',          -- 'active', 'improving', 'resolved', 'needs_attention'

    -- Recommendations
    recommended_practice_hands INTEGER,
    practice_hands_completed INTEGER DEFAULT 0,

    last_analysis TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Improvement Milestones (Celebrations!)
CREATE TABLE IF NOT EXISTS improvement_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Milestone Information
    milestone_type TEXT NOT NULL,          -- 'pattern_resolved', 'accuracy_improved', 'streak_achieved', etc.
    milestone_subtype TEXT,                -- More specific type

    -- Context
    convention_id TEXT,
    error_category TEXT,

    -- Achievement Details
    previous_value REAL,
    new_value REAL,
    improvement_amount REAL,
    improvement_percentage REAL,

    -- Display
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    celebration_emoji TEXT,

    -- Tracking
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shown_to_user BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,

    -- Rewards
    xp_reward INTEGER DEFAULT 0,
    badge_id TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Streak History (for detailed tracking)
CREATE TABLE IF NOT EXISTS streak_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    streak_start_date DATE NOT NULL,
    streak_end_date DATE,
    streak_length_days INTEGER NOT NULL,

    -- Reason for ending
    ended_reason TEXT,  -- 'ongoing', 'missed_day', 'used_freeze', null

    -- Stats during streak
    total_hands_in_streak INTEGER DEFAULT 0,
    average_accuracy REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Error Category Definitions (Extensible)
CREATE TABLE IF NOT EXISTS error_categories (
    category_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    friendly_name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    sort_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate default error categories
INSERT OR IGNORE INTO error_categories (category_id, display_name, friendly_name, description, sort_order) VALUES
('wrong_level', 'Bid Level', 'Getting comfortable with when to bid higher', 'Choosing between pass, game, or slam', 1),
('wrong_strain', 'Suit Selection', 'Learning which suit to bid', 'Choosing the right suit or notrump', 2),
('wrong_meaning', 'Convention Meaning', 'Clarifying what bids mean', 'Misunderstanding what a bid means', 3),
('missed_fit', 'Finding Fits', 'Spotting when you have a great fit with partner', 'Not recognizing 8+ card fit', 4),
('strength_evaluation', 'Hand Strength', 'Getting better at counting your hand strength', 'Over/under-evaluating hand strength', 5),
('distribution_awareness', 'Shape Recognition', 'Understanding how shape affects bidding', 'Not accounting for hand distribution', 6),
('premature_bid', 'Bidding Sequence', 'Learning the right time to make your bid', 'Bidding too quickly in the auction', 7),
('missed_opportunity', 'Convention Usage', 'Remembering when to use conventions', 'Not using available convention', 8);

-- Celebration Templates (Extensible)
CREATE TABLE IF NOT EXISTS celebration_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT UNIQUE NOT NULL,
    milestone_type TEXT NOT NULL,

    title_template TEXT NOT NULL,
    message_template TEXT NOT NULL,
    emoji TEXT,

    -- Trigger Conditions (JSON)
    trigger_conditions TEXT,  -- {min_improvement: 0.2, min_attempts: 10, etc.}

    xp_reward INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate default celebration templates
INSERT OR IGNORE INTO celebration_templates (template_id, milestone_type, title_template, message_template, emoji, xp_reward) VALUES
('first_correct', 'first_achievement', 'First Correct {convention}!', 'Great start! You got your first {convention} correct!', '🎉', 25),
('pattern_resolved', 'pattern_milestone', 'Breakthrough Moment!', 'You''ve mastered {category}! From {old_accuracy}% to {new_accuracy}%!', '🎉', 50),
('accuracy_milestone', 'accuracy_achievement', 'New Accuracy Record!', 'You''ve reached {accuracy}% accuracy! Keep it up!', '⭐', 30),
('streak_3day', 'streak_milestone', '3-Day Streak!', 'You''ve practiced 3 days in a row! Consistency is key!', '🔥', 20),
('streak_7day', 'streak_milestone', '7-Day Streak!', 'A full week of practice! You''re dedicated!', '🔥', 50),
('streak_30day', 'streak_milestone', '30-Day Streak!', 'A month of consistent practice! Incredible!', '🔥🔥', 150),
('hands_milestone_50', 'hands_milestone', '50 Hands Practiced!', 'You''ve practiced 50 hands! You''re building real skill!', '💪', 40),
('hands_milestone_100', 'hands_milestone', '100 Hands Practiced!', 'Century club! 100 hands is serious dedication!', '🎯', 75),
('improvement_20pct', 'improvement_milestone', 'Major Improvement!', 'You improved {category} by {improvement}%! Amazing progress!', '📈', 35);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_practice_history_user_time
    ON practice_history(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_practice_history_category
    ON practice_history(error_category, was_correct);
CREATE INDEX IF NOT EXISTS idx_mistake_patterns_user_status
    ON mistake_patterns(user_id, status);
CREATE INDEX IF NOT EXISTS idx_milestones_user_unshown
    ON improvement_milestones(user_id, shown_to_user);
CREATE INDEX IF NOT EXISTS idx_sessions_user_date
    ON practice_sessions(user_id, session_start DESC);

-- Views for Common Queries

-- User Progress Summary
CREATE VIEW IF NOT EXISTS v_user_progress_summary AS
SELECT
    u.id as user_id,
    u.username,
    ug.total_hands_practiced,
    ug.overall_accuracy,
    ug.current_streak_days,
    ug.total_xp,
    ug.current_level,
    COUNT(DISTINCT ph.convention_id) as conventions_practiced,
    COUNT(DISTINCT CASE WHEN mp.status = 'resolved' THEN mp.id END) as patterns_resolved,
    COUNT(DISTINCT CASE WHEN mp.status = 'needs_attention' THEN mp.id END) as patterns_needing_attention
FROM users u
LEFT JOIN user_gamification ug ON u.id = ug.user_id
LEFT JOIN practice_history ph ON u.id = ph.user_id
LEFT JOIN mistake_patterns mp ON u.id = mp.user_id
GROUP BY u.id;

-- Recent Activity Summary
CREATE VIEW IF NOT EXISTS v_recent_activity AS
SELECT
    user_id,
    COUNT(*) as hands_last_7_days,
    AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as accuracy_last_7_days,
    SUM(time_taken_seconds) as time_last_7_days,
    COUNT(DISTINCT DATE(timestamp)) as days_active_last_7
FROM practice_history
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY user_id;

-- Active Patterns (Needs Attention)
CREATE VIEW IF NOT EXISTS v_active_mistake_patterns AS
SELECT
    mp.*,
    ec.display_name as category_display_name,
    ec.friendly_name as category_friendly_name,
    (mp.attempts_in_category - mp.practice_hands_completed) as remaining_practice_hands
FROM mistake_patterns mp
JOIN error_categories ec ON mp.error_category = ec.category_id
WHERE mp.status IN ('active', 'needs_attention')
ORDER BY mp.user_id, mp.recent_occurrences DESC;

-- Pending Celebrations
CREATE VIEW IF NOT EXISTS v_pending_celebrations AS
SELECT
    im.*,
    u.username,
    u.display_name
FROM improvement_milestones im
JOIN users u ON im.user_id = u.id
WHERE im.shown_to_user = FALSE
ORDER BY im.achieved_at DESC;
