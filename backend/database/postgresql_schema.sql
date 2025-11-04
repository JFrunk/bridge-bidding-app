-- ============================================================================
-- PostgreSQL Schema for Bridge Bidding App
-- ============================================================================
-- This schema is designed to be compatible with Render PostgreSQL Free Tier
-- Includes all existing tables PLUS active_play_states for session persistence
-- ============================================================================

-- Enable UUID extension for session IDs (optional but recommended)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USER MANAGEMENT
-- ============================================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    display_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_activity TIMESTAMP,
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB,  -- PostgreSQL native JSON
    CONSTRAINT valid_username CHECK(length(username) >= 3)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_last_activity ON users(last_activity DESC);

-- ============================================================================
-- CRITICAL: ACTIVE PLAY STATES (Session Persistence)
-- ============================================================================
-- This table enables session state to survive server restarts
-- Stores serialized PlayState for active games
-- ============================================================================

CREATE TABLE active_play_states (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- PlayState serialization
    play_state_json JSONB NOT NULL,  -- Complete PlayState as JSON

    -- Quick access fields (denormalized for performance)
    contract_string VARCHAR(20),  -- "3NT by S"
    declarer CHAR(1) CHECK(declarer IN ('N', 'E', 'S', 'W')),
    dummy CHAR(1) CHECK(dummy IN ('N', 'E', 'S', 'W')),
    next_to_play CHAR(1) CHECK(next_to_play IN ('N', 'E', 'S', 'W')),
    tricks_taken_ns INTEGER DEFAULT 0,
    tricks_taken_ew INTEGER DEFAULT 0,

    -- Session metadata
    vulnerability VARCHAR(10),  -- 'None', 'NS', 'EW', 'Both'
    ai_difficulty VARCHAR(20) DEFAULT 'expert',
    dealer CHAR(1) CHECK(dealer IN ('N', 'E', 'S', 'W')),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),

    -- Status
    is_complete BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_active_play_states_user ON active_play_states(user_id);
CREATE INDEX idx_active_play_states_expires ON active_play_states(expires_at) WHERE is_complete = FALSE;
CREATE INDEX idx_active_play_states_last_updated ON active_play_states(last_updated DESC);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_play_state_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_play_state_timestamp
    BEFORE UPDATE ON active_play_states
    FOR EACH ROW
    EXECUTE FUNCTION update_play_state_timestamp();

-- ============================================================================
-- GAME SESSIONS & SCORING
-- ============================================================================

CREATE TABLE game_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type VARCHAR(20) DEFAULT 'chicago' CHECK(session_type IN ('chicago', 'rubber', 'practice')),

    hands_completed INTEGER DEFAULT 0,
    current_hand_number INTEGER DEFAULT 1,
    max_hands INTEGER DEFAULT 4,

    ns_score INTEGER DEFAULT 0,
    ew_score INTEGER DEFAULT 0,

    dealer_rotation VARCHAR(50) DEFAULT 'N,E,S,W',
    vulnerability_schedule VARCHAR(50) DEFAULT 'None,NS,EW,Both',

    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK(status IN ('active', 'completed', 'abandoned')),

    total_time_seconds INTEGER DEFAULT 0,
    player_position CHAR(1) DEFAULT 'S' CHECK(player_position IN ('N', 'E', 'S', 'W')),
    ai_difficulty VARCHAR(20) DEFAULT 'intermediate'
);

CREATE INDEX idx_game_sessions_user_status ON game_sessions(user_id, status);
CREATE INDEX idx_game_sessions_user_completed ON game_sessions(user_id, completed_at DESC) WHERE status = 'completed';
CREATE INDEX idx_game_sessions_active ON game_sessions(status, started_at DESC) WHERE status = 'active';

CREATE TABLE session_hands (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    hand_number INTEGER NOT NULL,

    dealer CHAR(1) NOT NULL CHECK(dealer IN ('N', 'E', 'S', 'W')),
    vulnerability VARCHAR(10) NOT NULL,

    contract_level INTEGER CHECK(contract_level BETWEEN 1 AND 7 OR contract_level IS NULL),
    contract_strain VARCHAR(5),
    contract_declarer CHAR(1) CHECK(contract_declarer IN ('N', 'E', 'S', 'W') OR contract_declarer IS NULL),
    contract_doubled INTEGER DEFAULT 0 CHECK(contract_doubled IN (0, 1, 2)),

    tricks_taken INTEGER CHECK(tricks_taken BETWEEN 0 AND 13 OR tricks_taken IS NULL),
    tricks_needed INTEGER,
    made BOOLEAN,

    hand_score INTEGER NOT NULL DEFAULT 0,
    score_breakdown JSONB,
    honors_bonus INTEGER DEFAULT 0,

    ns_total_after INTEGER NOT NULL,
    ew_total_after INTEGER NOT NULL,

    deal_data JSONB,
    auction_history JSONB,
    play_history JSONB,

    hand_duration_seconds INTEGER,
    user_played_position CHAR(1) CHECK(user_played_position IN ('N', 'E', 'S', 'W', NULL)),
    user_was_declarer BOOLEAN DEFAULT FALSE,
    user_was_dummy BOOLEAN DEFAULT FALSE,

    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(session_id, hand_number)
);

CREATE INDEX idx_session_hands_session ON session_hands(session_id, hand_number);
CREATE INDEX idx_session_hands_user_declarer ON session_hands(user_was_declarer, made) WHERE user_was_declarer = TRUE;

-- ============================================================================
-- BIDDING FEEDBACK & ANALYTICS
-- ============================================================================

CREATE TABLE bidding_decisions (
    id SERIAL PRIMARY KEY,
    hand_analysis_id INTEGER,
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_id VARCHAR(255),

    bid_number INTEGER NOT NULL,
    position VARCHAR(10) NOT NULL,
    dealer VARCHAR(10),
    vulnerability VARCHAR(10),

    user_bid VARCHAR(20) NOT NULL,
    optimal_bid VARCHAR(20) NOT NULL,
    auction_before JSONB,

    correctness VARCHAR(20) NOT NULL,
    score REAL NOT NULL,
    impact VARCHAR(20),

    error_category VARCHAR(100),
    error_subcategory VARCHAR(100),
    key_concept VARCHAR(100),
    difficulty VARCHAR(20),

    helpful_hint TEXT,
    reasoning TEXT,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bidding_decisions_user_time ON bidding_decisions(user_id, timestamp DESC);
CREATE INDEX idx_bidding_decisions_correctness ON bidding_decisions(user_id, correctness, timestamp DESC);
CREATE INDEX idx_bidding_decisions_category ON bidding_decisions(user_id, error_category, timestamp DESC);
CREATE INDEX idx_bidding_decisions_concept ON bidding_decisions(user_id, key_concept, timestamp DESC);
CREATE INDEX idx_bidding_decisions_session ON bidding_decisions(session_id, bid_number);

CREATE TABLE hand_analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_id VARCHAR(255),

    dealer VARCHAR(10),
    vulnerability VARCHAR(10),
    contract VARCHAR(20),

    overall_score REAL,
    bidding_score REAL,
    play_score REAL,

    analysis_data JSONB,
    hands_data JSONB,
    auction_data JSONB,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hand_analyses_user_time ON hand_analyses(user_id, timestamp DESC);
CREATE INDEX idx_hand_analyses_contract ON hand_analyses(user_id, contract, timestamp DESC);

-- ============================================================================
-- AI PLAY LOGGING (DDS Monitoring)
-- ============================================================================

CREATE TABLE ai_play_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    session_id VARCHAR(255),
    hand_number INTEGER,
    trick_number INTEGER,

    position CHAR(1) NOT NULL CHECK(position IN ('N', 'E', 'S', 'W')),
    ai_level VARCHAR(20) NOT NULL CHECK(ai_level IN ('beginner', 'intermediate', 'advanced', 'expert')),

    card_played VARCHAR(5) NOT NULL,
    solve_time_ms REAL,
    used_fallback BOOLEAN DEFAULT FALSE,

    contract VARCHAR(10),
    trump_suit CHAR(1)
);

CREATE INDEX idx_ai_play_log_timestamp ON ai_play_log(timestamp);
CREATE INDEX idx_ai_play_log_session ON ai_play_log(session_id);
CREATE INDEX idx_ai_play_log_ai_level ON ai_play_log(ai_level);
CREATE INDEX idx_ai_play_log_fallback ON ai_play_log(used_fallback);

-- ============================================================================
-- CONVENTION LEARNING SYSTEM
-- ============================================================================

CREATE TABLE conventions (
    convention_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    level VARCHAR(20) NOT NULL CHECK(level IN ('essential', 'intermediate', 'advanced')),
    category VARCHAR(100),
    frequency VARCHAR(20),
    complexity VARCHAR(20),
    description TEXT,
    short_description TEXT,
    learning_time_minutes INTEGER,
    practice_hands_required INTEGER,
    passing_accuracy REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE convention_prerequisites (
    convention_id VARCHAR(100) NOT NULL REFERENCES conventions(convention_id),
    prerequisite_id VARCHAR(100) NOT NULL,
    prerequisite_type VARCHAR(20) NOT NULL CHECK(prerequisite_type IN ('skill', 'convention')),
    PRIMARY KEY (convention_id, prerequisite_id)
);

CREATE TABLE user_convention_progress (
    user_id INTEGER NOT NULL REFERENCES users(id),
    convention_id VARCHAR(100) NOT NULL REFERENCES conventions(convention_id),
    status VARCHAR(20) NOT NULL DEFAULT 'locked' CHECK(status IN ('locked', 'unlocked', 'in_progress', 'mastered')),
    attempts INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0.0,
    started_at TIMESTAMP,
    mastered_at TIMESTAMP,
    last_practiced TIMESTAMP,
    PRIMARY KEY (user_id, convention_id)
);

CREATE INDEX idx_user_convention_progress_user ON user_convention_progress(user_id);
CREATE INDEX idx_user_convention_progress_status ON user_convention_progress(status);

CREATE TABLE convention_practice_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    convention_id VARCHAR(100) NOT NULL REFERENCES conventions(convention_id),
    hand_id VARCHAR(255),
    user_bid VARCHAR(20),
    correct_bid VARCHAR(20),
    was_correct BOOLEAN NOT NULL,
    hints_used INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_convention_practice_history_user ON convention_practice_history(user_id, convention_id);
CREATE INDEX idx_convention_practice_history_timestamp ON convention_practice_history(timestamp);

-- ============================================================================
-- GAMIFICATION & USER ENGAGEMENT
-- ============================================================================

CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    tracking_enabled BOOLEAN DEFAULT TRUE,
    share_progress BOOLEAN DEFAULT FALSE,
    show_in_leaderboards BOOLEAN DEFAULT FALSE,
    email_weekly_summary BOOLEAN DEFAULT TRUE,
    email_milestones BOOLEAN DEFAULT TRUE,
    celebrate_achievements BOOLEAN DEFAULT TRUE,
    difficulty_preference VARCHAR(20) DEFAULT 'adaptive',
    practice_reminder_time VARCHAR(10),
    daily_goal_hands INTEGER DEFAULT 10,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_gamification (
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

CREATE TABLE practice_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    hands_practiced INTEGER DEFAULT 0,
    correct_hands INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    session_type VARCHAR(50)
);

CREATE TABLE practice_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES practice_sessions(id) ON DELETE SET NULL,
    hand_id VARCHAR(255),
    convention_id VARCHAR(100),
    user_bid VARCHAR(20) NOT NULL,
    correct_bid VARCHAR(20) NOT NULL,
    was_correct BOOLEAN NOT NULL,
    error_category VARCHAR(100),
    error_subcategory VARCHAR(100),
    hand_characteristics JSONB,
    hints_used INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,
    xp_earned INTEGER DEFAULT 0,
    feedback_shown TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_practice_history_user_time ON practice_history(user_id, timestamp DESC);
CREATE INDEX idx_practice_history_category ON practice_history(error_category, was_correct);
CREATE INDEX idx_sessions_user_date ON practice_sessions(user_id, session_start DESC);

CREATE TABLE mistake_patterns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    convention_id VARCHAR(100),
    error_category VARCHAR(100) NOT NULL,
    error_subcategory VARCHAR(100),
    total_occurrences INTEGER DEFAULT 1,
    recent_occurrences INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    attempts_in_category INTEGER DEFAULT 0,
    correct_in_category INTEGER DEFAULT 0,
    current_accuracy REAL DEFAULT 0.0,
    previous_accuracy REAL DEFAULT 0.0,
    improvement_rate REAL DEFAULT 0.0,
    trend VARCHAR(20) DEFAULT 'new',
    status VARCHAR(30) DEFAULT 'active',
    recommended_practice_hands INTEGER,
    practice_hands_completed INTEGER DEFAULT 0,
    last_analysis TIMESTAMP
);

CREATE INDEX idx_mistake_patterns_user_status ON mistake_patterns(user_id, status);

CREATE TABLE improvement_milestones (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    milestone_type VARCHAR(50) NOT NULL,
    milestone_subtype VARCHAR(50),
    convention_id VARCHAR(100),
    error_category VARCHAR(100),
    previous_value REAL,
    new_value REAL,
    improvement_amount REAL,
    improvement_percentage REAL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    celebration_emoji VARCHAR(10),
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shown_to_user BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    xp_reward INTEGER DEFAULT 0,
    badge_id VARCHAR(100)
);

CREATE INDEX idx_milestones_user_unshown ON improvement_milestones(user_id, shown_to_user);

CREATE TABLE streak_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    streak_start_date DATE NOT NULL,
    streak_end_date DATE,
    streak_length_days INTEGER NOT NULL,
    ended_reason VARCHAR(50),
    total_hands_in_streak INTEGER DEFAULT 0,
    average_accuracy REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE error_categories (
    category_id VARCHAR(100) PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    friendly_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE celebration_templates (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(100) UNIQUE NOT NULL,
    milestone_type VARCHAR(50) NOT NULL,
    title_template TEXT NOT NULL,
    message_template TEXT NOT NULL,
    emoji VARCHAR(10),
    trigger_conditions JSONB,
    xp_reward INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MIGRATIONS TRACKING
-- ============================================================================

CREATE TABLE migrations_applied (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CLEANUP JOB FOR EXPIRED PLAY STATES
-- ============================================================================
-- Run this periodically to clean up old session states
-- Can be automated with pg_cron extension or external cron job
-- ============================================================================

-- Example cleanup function (can be called manually or scheduled)
CREATE OR REPLACE FUNCTION cleanup_expired_play_states()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM active_play_states
    WHERE expires_at < CURRENT_TIMESTAMP
    OR (is_complete = TRUE AND last_updated < CURRENT_TIMESTAMP - INTERVAL '1 hour');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA / DEFAULTS
-- ============================================================================

-- Insert default error categories (if needed)
-- INSERT INTO error_categories (category_id, display_name, friendly_name, description) VALUES ...

-- ============================================================================
-- GRANT PERMISSIONS (Adjust based on your Render PostgreSQL user)
-- ============================================================================

-- Grant permissions to your application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
