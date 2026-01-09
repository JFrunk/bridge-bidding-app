-- Migration: Auto-complete foundational conventions for existing users
--
-- This migration automatically marks all foundational conventions as mastered
-- for users who have already mastered any Essential or higher level conventions.
-- This ensures existing users aren't blocked by the new foundational requirement.
--
-- Foundational conventions (Level 0):
-- when_to_pass, opening_one_major, opening_one_minor, opening_1nt,
-- single_raise, limit_raise, new_suit_response, dustbin_1nt_response,
-- game_raise, two_over_one_response, opener_rebid, responder_rebid

-- First, find users who have mastered any Essential+ conventions
-- Essential conventions: stayman, jacoby_transfers, weak_two, takeout_double
-- If they've mastered these, they clearly know the foundational material

-- Insert foundational convention progress for existing advanced users
-- Only insert if they have at least one Essential convention mastered
-- and don't already have the foundational convention

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'when_to_pass' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'when_to_pass'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'opening_one_major' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'opening_one_major'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'opening_one_minor' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'opening_one_minor'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'opening_1nt' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'opening_1nt'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'single_raise' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'single_raise'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'limit_raise' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'limit_raise'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'new_suit_response' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'new_suit_response'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'dustbin_1nt_response' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'dustbin_1nt_response'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'game_raise' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'game_raise'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'two_over_one_response' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'two_over_one_response'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'opener_rebid' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'opener_rebid'
);

INSERT OR IGNORE INTO user_convention_progress (user_id, convention_id, is_mastered, accuracy, practice_count, last_practiced)
SELECT DISTINCT
    ucp.user_id,
    'responder_rebid' as convention_id,
    1 as is_mastered,
    1.0 as accuracy,
    10 as practice_count,
    CURRENT_TIMESTAMP as last_practiced
FROM user_convention_progress ucp
WHERE ucp.is_mastered = 1
AND ucp.convention_id IN ('stayman', 'jacoby_transfers', 'weak_two', 'takeout_double',
                          'blackwood', 'michaels_cuebid', 'unusual_2nt', 'negative_double', 'fourth_suit_forcing')
AND NOT EXISTS (
    SELECT 1 FROM user_convention_progress ucp2
    WHERE ucp2.user_id = ucp.user_id AND ucp2.convention_id = 'responder_rebid'
);
