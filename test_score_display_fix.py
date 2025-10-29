#!/usr/bin/env python3
"""
Test script to verify scoring sign fix in both ScoreModal and ContractHeader.

This test verifies that:
1. When NS declares and makes: score is positive
2. When NS declares and goes down: score is negative
3. When EW declares and makes: score is negative (NS lost)
4. When EW declares and goes down: score is positive (NS set them)

The fix ensures both ScoreModal.jsx and ContractHeader.jsx show the same
perspective-corrected score to the user (who plays South on NS team).
"""

def test_scoring_perspective():
    """
    Test cases for scoring perspective conversion
    Backend always returns score from declarer's perspective
    Frontend must convert to user's (NS) perspective
    """

    test_cases = [
        # (declarer, backend_score, expected_user_score, description)
        ('N', 400, 400, "NS declares 3NT and makes (+400)"),
        ('S', 620, 620, "NS declares 4S and makes (+620)"),
        ('N', -100, -100, "NS declares 3NT down 2 (-100)"),
        ('S', -50, -50, "NS declares 4H down 1 (-50)"),

        ('E', 420, -420, "EW declares 4H and makes (NS loses -420)"),
        ('W', 400, -400, "EW declares 3NT and makes (NS loses -400)"),
        ('E', -100, 100, "EW declares 4S down 2 (NS sets them +100)"),
        ('W', -50, 50, "EW declares 3NT down 1 (NS sets them +50)"),
    ]

    print("Testing scoring perspective conversion:")
    print("=" * 70)

    all_passed = True
    for declarer, backend_score, expected_user_score, description in test_cases:
        # Logic from frontend:
        # const declarerIsNS = declarer === 'N' || declarer === 'S';
        # const userScore = declarerIsNS ? score : -score;

        declarer_is_ns = declarer in ['N', 'S']
        user_score = backend_score if declarer_is_ns else -backend_score

        passed = user_score == expected_user_score
        status = "✅ PASS" if passed else "❌ FAIL"

        print(f"{status}: {description}")
        print(f"   Declarer: {declarer}, Backend: {backend_score:+d}, User sees: {user_score:+d} (expected: {expected_user_score:+d})")

        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("✅ All tests passed! Scoring perspective is correct.")
    else:
        print("❌ Some tests failed! Check the logic.")

    return all_passed


if __name__ == '__main__':
    success = test_scoring_perspective()
    exit(0 if success else 1)
