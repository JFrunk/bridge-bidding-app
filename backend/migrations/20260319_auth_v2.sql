-- Auth V2 Migration: JWT + OAuth + Magic Link infrastructure
-- Per AUTH_PRD.md (docs/features/AUTH_PRD.md)
-- Idempotent: safe to run multiple times

-- =============================================================
-- 1. ALTER users table: add auth columns
-- =============================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- =============================================================
-- 2. auth_providers: tracks Google, password, magic_link per user
-- =============================================================

CREATE TABLE IF NOT EXISTS auth_providers (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,          -- 'google', 'password', 'magic_link'
    provider_id TEXT,                -- External provider's user ID (e.g. Google sub)
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT _provider_identity_uc UNIQUE (provider, provider_id)
);

CREATE INDEX IF NOT EXISTS idx_auth_providers_user
    ON auth_providers(user_id);

-- =============================================================
-- 3. auth_tokens: email verification, password reset, magic links
-- =============================================================

CREATE TABLE IF NOT EXISTS auth_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,  -- SHA-256 of the token (never store raw)
    token_type TEXT NOT NULL,         -- 'email_verify', 'password_reset', 'magic_link'
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,               -- NULL until consumed
    metadata JSONB,                  -- Request context: ip_address, user_agent
    created_at TIMESTAMP DEFAULT NOW()
);

-- Note: token_hash UNIQUE constraint already provides B-tree index for lookups.
-- No separate idx_auth_tokens_hash needed.

CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_type
    ON auth_tokens(user_id, token_type);

-- =============================================================
-- 4. refresh_tokens: JWT rotation (HttpOnly secure cookie)
-- =============================================================

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,  -- SHA-256 of the refresh token
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP             -- NULL until revoked
);

-- Note: token_hash UNIQUE constraint already provides B-tree index for lookups.
-- No separate idx_refresh_tokens_hash needed.

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user
    ON refresh_tokens(user_id);
