"""
Regression test for evaluate-bid storage bug (2025-10-29)

BUG: Dashboard showed only "Pass" bids because /api/evaluate-bid was returning 500 errors
ROOT CAUSE: bidding_feedback.py line 184 passed auction_context.get('history', []) (a LIST)
            to error_categorizer.categorize() which expected a DICT with 'vulnerability', etc.
FIX: Pass full auction_context dict instead of extracting just the history list

This test ensures that:
1. Non-Pass bids can be evaluated and stored without 500 errors
2. The error_categorizer receives the correct auction_context format
3. Bids are properly recorded in the bidding_decisions table
"""

from db import get_connection
from engine.hand import Hand, Card
from engine.feedback.bidding_feedback import BiddingFeedbackGenerator
from engine.ai.bid_explanation import BidExplanation


# Use a unique user_id for test isolation
TEST_USER_ID = 99997


def _cleanup_test_data():
    """Remove test data from the shared database"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bidding_decisions WHERE user_id = ?", (TEST_USER_ID,))
    except Exception:
        pass


def test_evaluate_bid_stores_non_pass_bids():
    """
    Test that non-Pass bids (1♥, 2♣, etc.) can be evaluated and stored
    without throwing AttributeError about 'list' object has no attribute 'get'
    """
    _cleanup_test_data()

    try:
        # Create test hand (6 HCP - insufficient to open)
        south_cards = [
            Card('2', '♠'), Card('T', '♥'), Card('8', '♥'), Card('6', '♥'),
            Card('5', '♥'), Card('2', '♥'), Card('J', '♦'), Card('7', '♦'),
            Card('6', '♦'), Card('K', '♣'), Card('J', '♣'), Card('7', '♣'),
            Card('2', '♣')
        ]
        south_hand = Hand(south_cards)

        # Auction context (DICT format - this is what was breaking before)
        auction_context = {
            'history': ['Pass', 'Pass'],
            'current_player': 'South',
            'dealer': 'North',
            'vulnerability': 'None'
        }

        # User makes aggressive 1♥ opening with only 6 HCP
        user_bid = '1♥'
        optimal_bid = 'Pass'  # Correct bid

        optimal_explanation = BidExplanation(optimal_bid)
        optimal_explanation.primary_reason = "Insufficient points to open"

        # Create feedback generator
        feedback_generator = BiddingFeedbackGenerator()

        # THIS SHOULD NOT THROW AttributeError
        feedback = feedback_generator.evaluate_and_store(
            user_id=TEST_USER_ID,
            hand=south_hand,
            user_bid=user_bid,
            auction_context=auction_context,
            optimal_bid=optimal_bid,
            optimal_explanation=optimal_explanation,
            session_id=None
        )

        # Verify feedback was generated
        assert feedback is not None
        assert feedback.user_bid == '1♥'
        assert feedback.optimal_bid == 'Pass'
        assert feedback.correctness.value in ['suboptimal', 'error']
        assert feedback.score < 7.0  # Should be penalized for opening light

        # Verify bid was stored in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_bid, optimal_bid, correctness, score
                FROM bidding_decisions
                WHERE user_id = ?
            """, (TEST_USER_ID,))
            row = cursor.fetchone()

        assert row is not None, "Bid should be stored in database"
        assert row['user_bid'] == '1♥', "User bid should be 1♥"
        assert row['optimal_bid'] == 'Pass', "Optimal bid should be Pass"
        assert row['correctness'] in ['suboptimal', 'error'], "Should be marked as incorrect"

        print("✅ PASS: Non-Pass bids are properly evaluated and stored")

    finally:
        _cleanup_test_data()


def test_evaluate_bid_with_various_bids():
    """
    Test that various types of bids (suits, NT, doubles) can all be stored
    """
    _cleanup_test_data()

    try:
        # Create test hand
        test_cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'),
            Card('A', '♦'), Card('K', '♦'),
            Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'), Card('J', '♣')
        ]
        hand = Hand(test_cards)

        auction_context = {
            'history': [],
            'current_player': 'South',
            'dealer': 'South',
            'vulnerability': 'None'
        }

        # Test various bid types
        test_bids = ['1♥', '2♣', '3NT', '4♠', '7NT']

        feedback_generator = BiddingFeedbackGenerator()

        for bid in test_bids:
            optimal_explanation = BidExplanation(bid)
            optimal_explanation.primary_reason = "Test bid"

            # Should not throw error
            feedback = feedback_generator.evaluate_and_store(
                user_id=TEST_USER_ID,
                hand=hand,
                user_bid=bid,
                auction_context=auction_context,
                optimal_bid=bid,
                optimal_explanation=optimal_explanation,
                session_id=None
            )

            assert feedback is not None
            assert feedback.user_bid == bid

        # Verify all bids stored
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM bidding_decisions WHERE user_id = ?", (TEST_USER_ID,))
            count = cursor.fetchone()['count']

        assert count == len(test_bids), f"Expected {len(test_bids)} bids, found {count}"

        print(f"✅ PASS: All {len(test_bids)} bid types stored successfully")

    finally:
        _cleanup_test_data()


if __name__ == '__main__':
    test_evaluate_bid_stores_non_pass_bids()
    test_evaluate_bid_with_various_bids()
    print("\n✅ All regression tests passed!")
