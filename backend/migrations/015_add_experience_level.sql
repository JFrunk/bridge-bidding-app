-- Migration 015: Add experience level to users table
-- Tracks user-selected experience level for Learning Mode content locking
--
-- Experience levels:
--   0 = Beginner (New to Bridge) - Only Level 0 unlocked
--   1 = Intermediate (Returning player) - Levels 0-1 unlocked
--   99 = Expert (Experienced player) - All content unlocked
--
-- The unlock_all_content flag overrides experience level when true

-- Add experience_level column (NULL means wizard not completed)
ALTER TABLE users ADD COLUMN experience_level INTEGER DEFAULT NULL;

-- Add unlock_all_content flag (user manually toggled "Unlock All")
ALTER TABLE users ADD COLUMN unlock_all_content BOOLEAN DEFAULT FALSE;

-- Add experience_id for analytics (tracks which wizard option was selected)
ALTER TABLE users ADD COLUMN experience_id TEXT DEFAULT NULL;

-- Add timestamp for when experience was set (for future decay/progression)
ALTER TABLE users ADD COLUMN experience_set_at TIMESTAMP DEFAULT NULL;
