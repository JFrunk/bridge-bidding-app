-- Migration: Add partnerships table and partnership_id FK on session_hands
-- Supports Partner Practice feature (Phase 1)

-- Partnerships table
CREATE TABLE IF NOT EXISTS partnerships (
    id SERIAL PRIMARY KEY,
    player_a_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    player_b_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invite_code VARCHAR(8) UNIQUE,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('pending', 'active', 'dissolved')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_a_id, player_b_id)
);

CREATE INDEX IF NOT EXISTS idx_partnerships_player_a ON partnerships(player_a_id);
CREATE INDEX IF NOT EXISTS idx_partnerships_player_b ON partnerships(player_b_id);

-- Add partnership_id to session_hands (nullable FK for solo vs partner play)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'session_hands' AND column_name = 'partnership_id'
    ) THEN
        ALTER TABLE session_hands ADD COLUMN partnership_id INTEGER REFERENCES partnerships(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_session_hands_partnership ON session_hands(partnership_id) WHERE partnership_id IS NOT NULL;
