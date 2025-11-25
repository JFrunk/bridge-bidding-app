-- ============================================================================
-- PostgreSQL Schema for Bridge Bidding App
-- Combined schema for production deployment on Render
-- Auto-converted from SQLite schemas
-- ============================================================================

-- ============================================================================
-- USER MANAGEMENT & LEARNING ANALYTICS
-- ============================================================================

-- Core Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_activity TIMESTAMP,
    timezone TEXT DEFAULT 'UTC',
    preferences TEXT,
    CONSTRAINT valid_username CHECK(length(username) >= 3)
);

-- User Settings (Privacy & Preferences)
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    tracking_enabled BOOLEAN DEFAULT TRUE,
    share_progress BOOLEAN DEFAULT FALSE,
    show_in_leaderboards BOOLEAN DEFAULT FALSE,
    email_weekly_summary BOOLEAN DEFAULT TRUE,
    email_milestones BOOLEAN DEFAULT TRUE,
    celebrate_achievements BOOLEAN DEFAULT TRUE,
    difficulty_preference TEXT DEFAULT 'adaptive',
    practice_reminder_time TEXT,
    daily_goal_hands INTEGER DEFAULT 10,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Gamification Stats
CREATE TABLE IF NOT EXISTS user_gamification (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    total_xp INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    xp_to_next_level INTEGER DEFAULT 500,
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_practice_date DATE,
    streak_freezes_available INTEGER DEFAULT 0,
    total_hands_practiced INTEGER DEFAULT 0,
    total_practice_time_minutes INTEGER DEFAULT 0,
    overall_accuracy REAL DEFAULT 0.0,
    recent_accuracy REAL DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Practice Session Tracking
CREATE TABLE IF NOT EXISTS practice_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    hands_practiced INTEGER DEFAULT 0,
    correct_hands INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    session_type TEXT
);

-- Enhanced Practice History
CREATE TABLE IF NOT EXISTS practice_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES practice_sessions(id) ON DELETE SET NULL,
    hand_id TEXT,
    convention_id TEXT,
    user_bid TEXT NOT NULL,
    correct_bid TEXT NOT NULL,
    was_correct BOOLEAN NOT NULL,
    error_category TEXT,
    error_subcategory TEXT,
    hand_characteristics TEXT,
    hints_used INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,
    xp_earned INTEGER DEFAULT 0,
    feedback_shown TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mistake Patterns (Aggregated Analysis)
CREATE TABLE IF NOT EXISTS mistake_patterns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    convention_id TEXT,
    error_category TEXT NOT NULL,
    error_subcategory TEXT,
    total_occurrences INTEGER DEFAULT 1,
    recent_occurrences INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    attempts_in_category INTEGER DEFAULT 0,
    correct_in_category INTEGER DEFAULT 0,
    current_accuracy REAL DEFAULT 0.0,
    previous_accuracy REAL DEFAULT 0.0,
    improvement_rate REAL DEFAULT 0.0,
    trend TEXT DEFAULT 'new',
    status TEXT DEFAULT 'active',
    recommended_practice_hands INTEGER,
    practice_hands_completed INTEGER DEFAULT 0,
    last_analysis TIMESTAMP
);

-- Improvement Milestones
CREATE TABLE IF NOT EXISTS improvement_milestones (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    milestone_type TEXT NOT NULL,
    milestone_subtype TEXT,
    convention_id TEXT,
    error_category TEXT,
    previous_value REAL,
    new_value REAL,
    improvement_amount REAL,
    improvement_percentage REAL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    celebration_emoji TEXT,
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shown_to_user BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    xp_reward INTEGER DEFAULT 0,
    badge_id TEXT
);

-- Streak History
CREATE TABLE IF NOT EXISTS streak_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    streak_start_date DATE NOT NULL,
    streak_end_date DATE,
    streak_length_days INTEGER NOT NULL,
    ended_reason TEXT,
    total_hands_in_streak INTEGER DEFAULT 0,
    average_accuracy REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Error Category Definitions
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

-- Celebration Templates
CREATE TABLE IF NOT EXISTS celebration_templates (
    id SERIAL PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    milestone_type TEXT NOT NULL,
    title_template TEXT NOT NULL,
    message_template TEXT NOT NULL,
    emoji TEXT,
    trigger_conditions TEXT,
    xp_reward INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- GAME SESSION SCORING SYSTEM
-- ============================================================================

-- Game Sessions
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type TEXT DEFAULT 'chicago',
    hands_completed INTEGER DEFAULT 0,
    current_hand_number INTEGER DEFAULT 1,
    max_hands INTEGER DEFAULT 4,
    ns_score INTEGER DEFAULT 0,
    ew_score INTEGER DEFAULT 0,
    dealer_rotation TEXT DEFAULT 'N,E,S,W',
    vulnerability_schedule TEXT DEFAULT 'None,NS,EW,Both',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'active',
    total_time_seconds INTEGER DEFAULT 0,
    player_position TEXT DEFAULT 'S',
    ai_difficulty TEXT DEFAULT 'intermediate',
    CONSTRAINT valid_status CHECK(status IN ('active', 'completed', 'abandoned')),
    CONSTRAINT valid_session_type CHECK(session_type IN ('chicago', 'rubber', 'practice')),
    CONSTRAINT valid_player_position CHECK(player_position IN ('N', 'E', 'S', 'W'))
);

-- Session Hands
CREATE TABLE IF NOT EXISTS session_hands (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    hand_number INTEGER NOT NULL,
    dealer TEXT NOT NULL CHECK(dealer IN ('N', 'E', 'S', 'W')),
    vulnerability TEXT NOT NULL,
    contract_level INTEGER CHECK(contract_level BETWEEN 1 AND 7 OR contract_level IS NULL),
    contract_strain TEXT,
    contract_declarer TEXT CHECK(contract_declarer IN ('N', 'E', 'S', 'W') OR contract_declarer IS NULL),
    contract_doubled INTEGER DEFAULT 0 CHECK(contract_doubled IN (0, 1, 2)),
    tricks_taken INTEGER CHECK(tricks_taken BETWEEN 0 AND 13 OR tricks_taken IS NULL),
    tricks_needed INTEGER,
    made BOOLEAN,
    hand_score INTEGER NOT NULL DEFAULT 0,
    score_breakdown TEXT,
    honors_bonus INTEGER DEFAULT 0,
    ns_total_after INTEGER NOT NULL,
    ew_total_after INTEGER NOT NULL,
    deal_data TEXT,
    auction_history TEXT,
    play_history TEXT,
    hand_duration_seconds INTEGER,
    user_played_position TEXT CHECK(user_played_position IN ('N', 'E', 'S', 'W') OR user_played_position IS NULL),
    user_was_declarer BOOLEAN DEFAULT FALSE,
    user_was_dummy BOOLEAN DEFAULT FALSE,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, hand_number)
);

-- ============================================================================
-- CONVENTION LEVELS
-- ============================================================================

-- Convention definitions
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

-- Convention prerequisites
CREATE TABLE IF NOT EXISTS convention_prerequisites (
    convention_id TEXT NOT NULL REFERENCES conventions(convention_id),
    prerequisite_id TEXT NOT NULL,
    prerequisite_type TEXT NOT NULL CHECK(prerequisite_type IN ('skill', 'convention')),
    PRIMARY KEY (convention_id, prerequisite_id)
);

-- User convention progress
CREATE TABLE IF NOT EXISTS user_convention_progress (
    user_id INTEGER NOT NULL,
    convention_id TEXT NOT NULL REFERENCES conventions(convention_id),
    status TEXT NOT NULL DEFAULT 'locked' CHECK(status IN ('locked', 'unlocked', 'in_progress', 'mastered')),
    attempts INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0.0,
    started_at TIMESTAMP,
    mastered_at TIMESTAMP,
    last_practiced TIMESTAMP,
    PRIMARY KEY (user_id, convention_id)
);

-- Convention practice history
CREATE TABLE IF NOT EXISTS convention_practice_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    convention_id TEXT NOT NULL REFERENCES conventions(convention_id),
    hand_id TEXT,
    user_bid TEXT,
    correct_bid TEXT,
    was_correct BOOLEAN NOT NULL,
    hints_used INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BIDDING FEEDBACK SYSTEM
-- ============================================================================

-- Bidding Decisions
CREATE TABLE IF NOT EXISTS bidding_decisions (
    id SERIAL PRIMARY KEY,
    hand_analysis_id INTEGER,
    user_id INTEGER NOT NULL,
    session_id TEXT,
    bid_number INTEGER NOT NULL,
    position TEXT NOT NULL,
    dealer TEXT,
    vulnerability TEXT,
    user_bid TEXT NOT NULL,
    optimal_bid TEXT NOT NULL,
    auction_before TEXT,
    correctness TEXT NOT NULL,
    score REAL NOT NULL,
    impact TEXT,
    error_category TEXT,
    error_subcategory TEXT,
    key_concept TEXT,
    difficulty TEXT,
    helpful_hint TEXT,
    reasoning TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hand Analyses
CREATE TABLE IF NOT EXISTS hand_analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id TEXT,
    dealer TEXT,
    vulnerability TEXT,
    contract TEXT,
    overall_score REAL,
    bidding_score REAL,
    play_score REAL,
    analysis_data TEXT,
    hands_data TEXT,
    auction_data TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_practice_history_user_time ON practice_history(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_practice_history_category ON practice_history(error_category, was_correct);
CREATE INDEX IF NOT EXISTS idx_mistake_patterns_user_status ON mistake_patterns(user_id, status);
CREATE INDEX IF NOT EXISTS idx_milestones_user_unshown ON improvement_milestones(user_id, shown_to_user);
CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON practice_sessions(user_id, session_start DESC);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user_status ON game_sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_game_sessions_active ON game_sessions(status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_hands_session ON session_hands(session_id, hand_number);
CREATE INDEX IF NOT EXISTS idx_user_convention_progress_user ON user_convention_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_convention_progress_status ON user_convention_progress(status);
CREATE INDEX IF NOT EXISTS idx_convention_practice_history_user ON convention_practice_history(user_id, convention_id);
CREATE INDEX IF NOT EXISTS idx_convention_practice_history_timestamp ON convention_practice_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_bidding_decisions_user_time ON bidding_decisions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_bidding_decisions_correctness ON bidding_decisions(user_id, correctness, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_bidding_decisions_session ON bidding_decisions(session_id, bid_number);
CREATE INDEX IF NOT EXISTS idx_hand_analyses_user_time ON hand_analyses(user_id, timestamp DESC);

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Default error categories
INSERT INTO error_categories (category_id, display_name, friendly_name, description, sort_order) VALUES
('wrong_level', 'Bid Level', 'Getting comfortable with when to bid higher', 'Choosing between pass, game, or slam', 1),
('wrong_strain', 'Suit Selection', 'Learning which suit to bid', 'Choosing the right suit or notrump', 2),
('wrong_meaning', 'Convention Meaning', 'Clarifying what bids mean', 'Misunderstanding what a bid means', 3),
('missed_fit', 'Finding Fits', 'Spotting when you have a great fit with partner', 'Not recognizing 8+ card fit', 4),
('strength_evaluation', 'Hand Strength', 'Getting better at counting your hand strength', 'Over/under-evaluating hand strength', 5),
('distribution_awareness', 'Shape Recognition', 'Understanding how shape affects bidding', 'Not accounting for hand distribution', 6),
('premature_bid', 'Bidding Sequence', 'Learning the right time to make your bid', 'Bidding too quickly in the auction', 7),
('missed_opportunity', 'Convention Usage', 'Remembering when to use conventions', 'Not using available convention', 8)
ON CONFLICT (category_id) DO NOTHING;

-- Default celebration templates
INSERT INTO celebration_templates (template_id, milestone_type, title_template, message_template, emoji, xp_reward) VALUES
('first_correct', 'first_achievement', 'First Correct {convention}!', 'Great start! You got your first {convention} correct!', '🎉', 25),
('pattern_resolved', 'pattern_milestone', 'Breakthrough Moment!', 'You''ve mastered {category}! From {old_accuracy}% to {new_accuracy}%!', '🎉', 50),
('accuracy_milestone', 'accuracy_achievement', 'New Accuracy Record!', 'You''ve reached {accuracy}% accuracy! Keep it up!', '⭐', 30),
('streak_3day', 'streak_milestone', '3-Day Streak!', 'You''ve practiced 3 days in a row! Consistency is key!', '🔥', 20),
('streak_7day', 'streak_milestone', '7-Day Streak!', 'A full week of practice! You''re dedicated!', '🔥', 50),
('streak_30day', 'streak_milestone', '30-Day Streak!', 'A month of consistent practice! Incredible!', '🔥🔥', 150),
('hands_milestone_50', 'hands_milestone', '50 Hands Practiced!', 'You''ve practiced 50 hands! You''re building real skill!', '💪', 40),
('hands_milestone_100', 'hands_milestone', '100 Hands Practiced!', 'Century club! 100 hands is serious dedication!', '🎯', 75),
('improvement_20pct', 'improvement_milestone', 'Major Improvement!', 'You improved {category} by {improvement}%! Amazing progress!', '📈', 35)
ON CONFLICT (template_id) DO NOTHING;
