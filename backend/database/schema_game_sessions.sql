-- ============================================================================
-- Game Session Scoring System
-- Multi-hand session tracking for Chicago Bridge and other formats
-- Fully multi-user compatible with user management system
-- ============================================================================

-- Game Sessions (collection of hands in a single game)
CREATE TABLE IF NOT EXISTS game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,  -- Required: links to users table
    session_type TEXT DEFAULT 'chicago',  -- 'chicago', 'rubber', 'practice'

    -- Session state
    hands_completed INTEGER DEFAULT 0,
    current_hand_number INTEGER DEFAULT 1,
    max_hands INTEGER DEFAULT 4,  -- 4 for Chicago

    -- Cumulative scoring
    ns_score INTEGER DEFAULT 0,
    ew_score INTEGER DEFAULT 0,

    -- Chicago-specific settings
    dealer_rotation TEXT DEFAULT 'N,E,S,W',  -- Fixed rotation
    vulnerability_schedule TEXT DEFAULT 'None,NS,EW,Both',  -- Chicago standard

    -- Session metadata
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'active',  -- 'active', 'completed', 'abandoned'

    -- Session duration tracking
    total_time_seconds INTEGER DEFAULT 0,

    -- Multi-user support
    player_position TEXT DEFAULT 'S',  -- Which position user plays (S=South by default)
    ai_difficulty TEXT DEFAULT 'intermediate',  -- AI difficulty for this session

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT valid_status CHECK(status IN ('active', 'completed', 'abandoned')),
    CONSTRAINT valid_session_type CHECK(session_type IN ('chicago', 'rubber', 'practice')),
    CONSTRAINT valid_player_position CHECK(player_position IN ('N', 'E', 'S', 'W'))
);

-- Individual Hand Results within a Session
CREATE TABLE IF NOT EXISTS session_hands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    hand_number INTEGER NOT NULL,

    -- Hand setup
    dealer TEXT NOT NULL CHECK(dealer IN ('N', 'E', 'S', 'W')),
    vulnerability TEXT NOT NULL,

    -- Contract details (NULL if passed out)
    contract_level INTEGER CHECK(contract_level BETWEEN 1 AND 7 OR contract_level IS NULL),
    contract_strain TEXT,
    contract_declarer TEXT CHECK(contract_declarer IN ('N', 'E', 'S', 'W') OR contract_declarer IS NULL),
    contract_doubled INTEGER DEFAULT 0 CHECK(contract_doubled IN (0, 1, 2)),

    -- Results
    tricks_taken INTEGER CHECK(tricks_taken BETWEEN 0 AND 13 OR tricks_taken IS NULL),
    tricks_needed INTEGER,
    made BOOLEAN,

    -- Scoring
    hand_score INTEGER NOT NULL DEFAULT 0,  -- Raw score for this hand (positive for declarer)
    score_breakdown TEXT,  -- JSON: detailed breakdown
    honors_bonus INTEGER DEFAULT 0,

    -- Running totals after this hand
    ns_total_after INTEGER NOT NULL,
    ew_total_after INTEGER NOT NULL,

    -- Hand data (for review and replay)
    deal_data TEXT,  -- JSON: all 4 hands
    auction_history TEXT,  -- JSON: bidding sequence
    play_history TEXT,  -- JSON: card play sequence

    -- Hand timing
    hand_duration_seconds INTEGER,

    -- User performance tracking
    user_played_position TEXT CHECK(user_played_position IN ('N', 'E', 'S', 'W', NULL)),
    user_was_declarer BOOLEAN DEFAULT FALSE,
    user_was_dummy BOOLEAN DEFAULT FALSE,

    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES game_sessions(id) ON DELETE CASCADE,
    UNIQUE(session_id, hand_number)
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_game_sessions_user_status
    ON game_sessions(user_id, status);

CREATE INDEX IF NOT EXISTS idx_game_sessions_user_completed
    ON game_sessions(user_id, completed_at DESC)
    WHERE status = 'completed';

CREATE INDEX IF NOT EXISTS idx_game_sessions_active
    ON game_sessions(status, started_at DESC)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_session_hands_session
    ON session_hands(session_id, hand_number);

CREATE INDEX IF NOT EXISTS idx_session_hands_user_declarer
    ON session_hands(user_was_declarer, made)
    WHERE user_was_declarer = TRUE;

-- Views for Common Queries

-- Active Sessions Summary (Per User)
CREATE VIEW IF NOT EXISTS v_active_sessions AS
SELECT
    gs.id,
    gs.user_id,
    u.username,
    u.display_name,
    gs.session_type,
    gs.hands_completed,
    gs.current_hand_number,
    gs.max_hands,
    gs.ns_score,
    gs.ew_score,
    CASE
        WHEN gs.ns_score > gs.ew_score THEN 'NS'
        WHEN gs.ew_score > gs.ns_score THEN 'EW'
        ELSE 'Tied'
    END as current_leader,
    ABS(gs.ns_score - gs.ew_score) as score_difference,
    gs.player_position,
    gs.ai_difficulty,
    gs.started_at,
    ROUND((julianday('now') - julianday(gs.started_at)) * 86400) as elapsed_seconds
FROM game_sessions gs
LEFT JOIN users u ON gs.user_id = u.id
WHERE gs.status = 'active';

-- Session Summary with All Hands (Per User)
CREATE VIEW IF NOT EXISTS v_session_details AS
SELECT
    gs.id as session_id,
    gs.user_id,
    u.username,
    gs.session_type,
    gs.status,
    gs.hands_completed,
    gs.ns_score as final_ns_score,
    gs.ew_score as final_ew_score,
    CASE
        WHEN gs.ns_score > gs.ew_score THEN 'NS'
        WHEN gs.ew_score > gs.ns_score THEN 'EW'
        WHEN gs.ns_score = gs.ew_score THEN 'Tied'
        ELSE NULL
    END as winner,
    gs.player_position,
    gs.started_at,
    gs.completed_at,
    gs.total_time_seconds,
    COUNT(sh.id) as recorded_hands,
    SUM(CASE WHEN sh.contract_declarer IN ('N', 'S') AND sh.made THEN 1 ELSE 0 END) as ns_made_contracts,
    SUM(CASE WHEN sh.contract_declarer IN ('E', 'W') AND sh.made THEN 1 ELSE 0 END) as ew_made_contracts,
    SUM(CASE WHEN sh.user_was_declarer AND sh.made THEN 1 ELSE 0 END) as user_made_contracts,
    SUM(CASE WHEN sh.user_was_declarer THEN 1 ELSE 0 END) as user_declared_hands,
    AVG(CASE WHEN sh.contract_declarer IN ('N', 'S') THEN sh.tricks_taken ELSE NULL END) as ns_avg_tricks,
    AVG(CASE WHEN sh.contract_declarer IN ('E', 'W') THEN sh.tricks_taken ELSE NULL END) as ew_avg_tricks
FROM game_sessions gs
LEFT JOIN users u ON gs.user_id = u.id
LEFT JOIN session_hands sh ON gs.id = sh.session_id
GROUP BY gs.id;

-- Hand History for Display
CREATE VIEW IF NOT EXISTS v_hand_history AS
SELECT
    sh.id,
    sh.session_id,
    gs.user_id,
    sh.hand_number,
    sh.dealer,
    sh.vulnerability,
    CASE
        WHEN sh.contract_level IS NULL THEN 'Passed Out'
        ELSE printf('%d%s', sh.contract_level, sh.contract_strain) ||
             CASE sh.contract_doubled
                 WHEN 1 THEN 'X'
                 WHEN 2 THEN 'XX'
                 ELSE ''
             END ||
             ' by ' || sh.contract_declarer
    END as contract_display,
    sh.tricks_taken,
    sh.tricks_needed,
    sh.made,
    sh.hand_score,
    sh.honors_bonus,
    sh.ns_total_after,
    sh.ew_total_after,
    sh.user_was_declarer,
    sh.user_was_dummy,
    sh.hand_duration_seconds,
    sh.played_at
FROM session_hands sh
JOIN game_sessions gs ON sh.session_id = gs.id
ORDER BY sh.session_id, sh.hand_number;

-- User Session Statistics (for leaderboards and progress tracking)
CREATE VIEW IF NOT EXISTS v_user_session_stats AS
SELECT
    u.id as user_id,
    u.username,
    u.display_name,
    COUNT(DISTINCT gs.id) as total_sessions,
    COUNT(DISTINCT CASE WHEN gs.status = 'completed' THEN gs.id END) as completed_sessions,
    SUM(gs.hands_completed) as total_hands_played,
    AVG(CASE WHEN gs.status = 'completed' THEN
        CASE
            WHEN (gs.player_position IN ('N', 'S') AND gs.ns_score > gs.ew_score) OR
                 (gs.player_position IN ('E', 'W') AND gs.ew_score > gs.ns_score)
            THEN 1.0 ELSE 0.0
        END
    END) as win_rate,
    SUM(CASE WHEN sh.user_was_declarer AND sh.made THEN 1 ELSE 0 END) as contracts_made,
    SUM(CASE WHEN sh.user_was_declarer THEN 1 ELSE 0 END) as contracts_declared,
    CASE
        WHEN SUM(CASE WHEN sh.user_was_declarer THEN 1 ELSE 0 END) > 0
        THEN CAST(SUM(CASE WHEN sh.user_was_declarer AND sh.made THEN 1 ELSE 0 END) AS REAL) /
             SUM(CASE WHEN sh.user_was_declarer THEN 1 ELSE 0 END)
        ELSE NULL
    END as declarer_success_rate,
    SUM(gs.total_time_seconds) as total_play_time_seconds,
    MAX(gs.completed_at) as last_session_completed
FROM users u
LEFT JOIN game_sessions gs ON u.id = gs.user_id
LEFT JOIN session_hands sh ON gs.id = sh.session_id
GROUP BY u.id;
