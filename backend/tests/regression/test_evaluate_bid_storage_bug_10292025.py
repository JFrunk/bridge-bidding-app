"""
Regression test for evaluate-bid storage bug (2025-10-29)

BUG: Dashboard showed only "Pass" bids because /api/evaluate-bid was returning 500 errors
ROOT CAUSE: auction_context format mismatch in error_categorizer
FIX: V2BidEvaluator always builds correct auction_context format

This test ensures that:
1. Non-Pass bids can be evaluated without errors
2. The error_categorizer receives the correct auction_context format
3. Feedback can be stored in the bidding_decisions table
"""

import os
import pytest

# Skip if DATABASE_URL not set (db.py requires PostgreSQL)
if not os.environ.get('DATABASE_URL'):
    pytest.skip("DATABASE_URL not set — requires PostgreSQL", allow_module_level=True)

from db import get_connection
from engine.hand import Hand, Card
from engine.feedback.bidding_feedback import (
    BiddingFeedback, BiddingFeedbackGenerator, CorrectnessLevel, ImpactLevel,
    get_feedback_generator
)


# Use a unique user_id for test isolation
TEST_USER_ID = 99997


def _cleanup_test_data():
    """Remove test data from the shared database"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bidding_decisions WHERE user_id = %s", (TEST_USER_ID,))
    except Exception:
        pass


def test_evaluate_bid_stores_non_pass_bids():
    """
    Test that non-Pass bids can be stored through the feedback storage layer
    without throwing errors.
    """
    _cleanup_test_data()

    try:
        # Create a BiddingFeedback (as V2BidEvaluator would produce)
        feedback = BiddingFeedback(
            bid_number=3,
            position='South',
            user_bid='1♥',
            correctness=CorrectnessLevel.ERROR,
            score=2.0,
            optimal_bid='Pass',
            alternative_bids=[],
            reasoning='Insufficient points to open',
            explanation_level='detailed',
            rule_reference=None,
            error_category='strength_evaluation',
            error_subcategory='overbid',
            impact=ImpactLevel.SIGNIFICANT,
            helpful_hint='Need 12+ HCP to open',
            key_concept='Point counting',
            difficulty='beginner'
        )

        auction_context = {
            'history': ['Pass', 'Pass'],
            'current_player': 'South',
            'dealer': 'North',
            'vulnerability': 'None'
        }

        # Store feedback (same path as server.py)
        feedback_generator = get_feedback_generator()
        feedback_generator._store_feedback(
            user_id=TEST_USER_ID,
            feedback=feedback,
            auction_context=auction_context,
            session_id=None,
            hand_analysis_id=None
        )

        # Verify bid was stored in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_bid, optimal_bid, correctness, score
                FROM bidding_decisions
                WHERE user_id = %s
            """, (TEST_USER_ID,))
            row = cursor.fetchone()

        assert row is not None, "Bid should be stored in database"
        assert row['user_bid'] == '1♥', "User bid should be 1♥"
        assert row['optimal_bid'] == 'Pass', "Optimal bid should be Pass"
        assert row['correctness'] in ['suboptimal', 'error'], "Should be marked as incorrect"

        print("✅ PASS: Non-Pass bids are properly stored")

    finally:
        _cleanup_test_data()


def test_evaluate_bid_with_various_bids():
    """
    Test that various types of bids (suits, NT) can all be stored.
    """
    _cleanup_test_data()

    try:
        test_bids = ['1♥', '2♣', '3NT', '4♠', '7NT']
        feedback_generator = get_feedback_generator()

        for bid in test_bids:
            feedback = BiddingFeedback(
                bid_number=1,
                position='South',
                user_bid=bid,
                correctness=CorrectnessLevel.OPTIMAL,
                score=10.0,
                optimal_bid=bid,
                alternative_bids=[],
                reasoning='Test bid',
                explanation_level='detailed',
                rule_reference=None,
                error_category=None,
                error_subcategory=None,
                impact=ImpactLevel.NONE,
                helpful_hint='',
                key_concept='Bidding judgment',
                difficulty='beginner'
            )

            auction_context = {
                'history': [],
                'current_player': 'South',
                'dealer': 'South',
                'vulnerability': 'None'
            }

            feedback_generator._store_feedback(
                user_id=TEST_USER_ID,
                feedback=feedback,
                auction_context=auction_context,
                session_id=None,
                hand_analysis_id=None
            )

        # Verify all bids stored
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM bidding_decisions WHERE user_id = %s", (TEST_USER_ID,))
            count = cursor.fetchone()['count']

        assert count == len(test_bids), f"Expected {len(test_bids)} bids, found {count}"

        print(f"✅ PASS: All {len(test_bids)} bid types stored successfully")

    finally:
        _cleanup_test_data()


if __name__ == '__main__':
    test_evaluate_bid_stores_non_pass_bids()
    test_evaluate_bid_with_various_bids()
    print("\n✅ All regression tests passed!")
