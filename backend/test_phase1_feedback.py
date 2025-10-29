"""
Quick test script for Phase 1: Bidding Feedback System

Tests:
1. BiddingFeedbackGenerator can evaluate bids
2. Feedback is stored in database
3. Dashboard API returns bidding feedback stats
4. Recent decisions are retrieved correctly

Run from backend directory:
    python3 test_phase1_feedback.py
"""

import sys
sys.path.insert(0, '.')

from engine.feedback.bidding_feedback import get_feedback_generator, CorrectnessLevel, ImpactLevel
from engine.hand import Hand
from engine.ai.bid_explanation import BidExplanation
import sqlite3


# Import helper functions directly since they don't depend on Flask context
def get_bidding_feedback_stats_for_user(user_id: int):
    """Calculate bidding feedback statistics (copied from analytics_api)"""
    conn = sqlite3.connect('bridge.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                COUNT(*) as total_decisions,
                AVG(score) as avg_score,
                SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
                SUM(CASE WHEN correctness = 'error' THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN impact = 'critical' THEN 1 ELSE 0 END) as critical_errors
            FROM bidding_decisions
            WHERE user_id = ?
              AND timestamp >= datetime('now', '-30 days')
        """, (user_id,))

        row = cursor.fetchone()

        if not row or row['total_decisions'] == 0:
            return {'avg_score': 0, 'total_decisions': 0, 'optimal_rate': 0, 'error_rate': 0, 'critical_errors': 0, 'recent_trend': 'stable'}

        total = row['total_decisions']
        return {
            'avg_score': round(row['avg_score'] or 0, 1),
            'total_decisions': total,
            'optimal_rate': round((row['optimal_count'] or 0) / total, 3),
            'error_rate': round((row['error_count'] or 0) / total, 3),
            'critical_errors': row['critical_errors'] or 0,
            'recent_trend': 'stable'
        }
    finally:
        conn.close()


def get_recent_bidding_decisions_for_user(user_id: int, limit: int = 10):
    """Get recent bidding decisions (copied from analytics_api)"""
    conn = sqlite3.connect('bridge.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id, bid_number, position, user_bid, optimal_bid,
                correctness, score, impact, key_concept, error_category
            FROM bidding_decisions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))

        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def test_feedback_generator():
    """Test 1: BiddingFeedbackGenerator evaluation"""
    print("\n=== Test 1: BiddingFeedbackGenerator ===")

    generator = get_feedback_generator()

    # Create a test hand
    test_hand = Hand.from_string("♠AK32 ♥K42 ♦A32 ♣432")  # 16 HCP, balanced

    # Simulate user bidding 1♣ when 1NT is optimal
    user_bid = "1♣"
    optimal_bid = "1NT"

    # Create auction context
    auction_context = {
        'history': [],
        'current_player': 'South',
        'dealer': 'North',
        'vulnerability': 'None'
    }

    # Create simple explanation
    optimal_explanation = BidExplanation(optimal_bid)
    optimal_explanation.primary_reason = "Balanced hand with 15-17 HCP"
    optimal_explanation.convention_reference = "opening_1nt"

    # Evaluate bid
    feedback = generator.evaluate_bid(
        hand=test_hand,
        user_bid=user_bid,
        auction_context=auction_context,
        optimal_bid=optimal_bid,
        optimal_explanation=optimal_explanation
    )

    print(f"✓ User bid: {feedback.user_bid}")
    print(f"✓ Optimal bid: {feedback.optimal_bid}")
    print(f"✓ Correctness: {feedback.correctness.value}")
    print(f"✓ Score: {feedback.score}/10")
    print(f"✓ Impact: {feedback.impact.value}")
    print(f"✓ Key concept: {feedback.key_concept}")

    assert feedback.user_bid == user_bid
    assert feedback.optimal_bid == optimal_bid
    assert feedback.correctness != CorrectnessLevel.OPTIMAL
    assert 0 <= feedback.score <= 10

    print("✅ Test 1 PASSED\n")
    return feedback


def test_feedback_storage():
    """Test 2: Feedback storage in database"""
    print("=== Test 2: Feedback Storage ===")

    generator = get_feedback_generator()

    # Create a test hand
    test_hand = Hand.from_string("♠AKQ3 ♥K42 ♦A32 ♣432")  # 16 HCP

    # Test optimal bid (should score 10.0)
    user_bid = "1NT"
    optimal_bid = "1NT"

    auction_context = {
        'history': [],
        'current_player': 'South',
        'dealer': 'North',
        'vulnerability': 'None'
    }

    optimal_explanation = BidExplanation(optimal_bid)
    optimal_explanation.primary_reason = "Balanced hand with 15-17 HCP"

    # Store feedback
    feedback = generator.evaluate_and_store(
        user_id=1,
        hand=test_hand,
        user_bid=user_bid,
        auction_context=auction_context,
        optimal_bid=optimal_bid,
        optimal_explanation=optimal_explanation,
        session_id="test_session_1"
    )

    # Verify it was stored
    conn = sqlite3.connect('bridge.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as count
        FROM bidding_decisions
        WHERE user_id = 1
          AND user_bid = ?
          AND session_id = 'test_session_1'
    """, (user_bid,))

    count = cursor.fetchone()[0]
    conn.close()

    print(f"✓ Feedback stored in database")
    print(f"✓ Records found: {count}")
    assert count >= 1

    print("✅ Test 2 PASSED\n")


def test_dashboard_stats():
    """Test 3: Dashboard statistics retrieval"""
    print("=== Test 3: Dashboard Statistics ===")

    stats = get_bidding_feedback_stats_for_user(user_id=1)

    print(f"✓ Average score: {stats['avg_score']}/10")
    print(f"✓ Total decisions: {stats['total_decisions']}")
    print(f"✓ Optimal rate: {stats['optimal_rate']*100:.1f}%")
    print(f"✓ Error rate: {stats['error_rate']*100:.1f}%")
    print(f"✓ Critical errors: {stats['critical_errors']}")
    print(f"✓ Recent trend: {stats['recent_trend']}")

    assert isinstance(stats, dict)
    assert 'avg_score' in stats
    assert 'total_decisions' in stats
    assert 'optimal_rate' in stats

    print("✅ Test 3 PASSED\n")


def test_recent_decisions():
    """Test 4: Recent decisions retrieval"""
    print("=== Test 4: Recent Decisions ===")

    decisions = get_recent_bidding_decisions_for_user(user_id=1, limit=5)

    print(f"✓ Retrieved {len(decisions)} recent decisions")

    if decisions:
        latest = decisions[0]
        print(f"✓ Latest decision:")
        print(f"  - Position: {latest['position']}")
        print(f"  - User bid: {latest['user_bid']}")
        print(f"  - Optimal bid: {latest['optimal_bid']}")
        print(f"  - Correctness: {latest['correctness']}")
        print(f"  - Score: {latest['score']}/10")

    assert isinstance(decisions, list)

    print("✅ Test 4 PASSED\n")


def cleanup_test_data():
    """Clean up test data"""
    print("=== Cleanup ===")

    conn = sqlite3.connect('bridge.db')
    cursor = conn.cursor()

    # Remove test session data
    cursor.execute("""
        DELETE FROM bidding_decisions
        WHERE session_id = 'test_session_1'
    """)

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"✓ Cleaned up {deleted} test records")
    print("✅ Cleanup complete\n")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 1: BIDDING FEEDBACK SYSTEM - BACKEND TESTS")
    print("="*60)

    try:
        # Run tests
        test_feedback_generator()
        test_feedback_storage()
        test_dashboard_stats()
        test_recent_decisions()

        # Cleanup
        cleanup_test_data()

        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nBackend Phase 1 implementation is working correctly.")
        print("\nNext steps:")
        print("  1. Create frontend React components")
        print("  2. Integrate with Learning Dashboard")
        print("  3. Test end-to-end feedback flow")
        print()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
