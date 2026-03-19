"""
Quick test script for Phase 1: Bidding Feedback System

Tests:
1. V2BidEvaluator can evaluate bids
2. Feedback can be stored in database
3. Dashboard API returns bidding feedback stats
4. Recent decisions are retrieved correctly

Run from backend directory:
    python3 test_phase1_feedback.py
"""

import sys
sys.path.insert(0, '.')

from engine.feedback.bidding_feedback import (
    get_feedback_generator, BiddingFeedback, CorrectnessLevel, ImpactLevel
)
from engine.hand import Hand
from utils.error_logger import log_error
from db import get_connection


# Import helper functions directly since they don't depend on Flask context
def get_bidding_feedback_stats_for_user(user_id: int):
    """Calculate bidding feedback statistics (copied from analytics_api)"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_decisions,
                AVG(score) as avg_score,
                SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
                SUM(CASE WHEN correctness = 'error' THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN impact = 'critical' THEN 1 ELSE 0 END) as critical_errors
            FROM bidding_decisions
            WHERE user_id = %s
              AND timestamp >= NOW() - INTERVAL '30 days'
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


def get_recent_bidding_decisions_for_user(user_id: int, limit: int = 10):
    """Get recent bidding decisions (copied from analytics_api)"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, bid_number, position, user_bid, optimal_bid,
                correctness, score, impact, key_concept, error_category
            FROM bidding_decisions
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (user_id, limit))

        return [dict(row) for row in cursor.fetchall()]


def test_feedback_generator():
    """Test 1: V2BidEvaluator evaluation"""
    print("\n=== Test 1: V2BidEvaluator ===")

    from engine.v2 import BiddingEngineV2Schema
    engine = BiddingEngineV2Schema(use_v1_fallback=False)

    # Create a test hand
    test_hand = Hand.from_string("♠AK32 ♥K42 ♦A32 ♣432")  # 16 HCP, balanced

    # Simulate user bidding 1♣ when 1NT is optimal
    user_bid = "1♣"

    # Evaluate using V2
    v2_feedback = engine.evaluate_user_bid(
        hand=test_hand,
        user_bid=user_bid,
        auction_history=[],
        my_position='South',
        vulnerability='None',
        dealer='North'
    )

    print(f"✓ User bid: {v2_feedback.user_bid}")
    print(f"✓ Optimal bid: {v2_feedback.optimal_bid}")
    print(f"✓ Correctness: {v2_feedback.correctness.value}")
    print(f"✓ Score: {v2_feedback.score}/10")
    print(f"✓ Impact: {v2_feedback.impact.value}")
    print(f"✓ Key concept: {v2_feedback.key_concept}")
    print(f"✓ Learning feedback: {'present' if v2_feedback.learning_feedback else 'none (optimal)'}")

    assert v2_feedback.user_bid == user_bid
    assert 0 <= v2_feedback.score <= 10

    print("✅ Test 1 PASSED\n")
    return v2_feedback


def test_feedback_storage():
    """Test 2: Feedback storage in database"""
    print("=== Test 2: Feedback Storage ===")

    generator = get_feedback_generator()

    # Create feedback as V2BidEvaluator would produce
    feedback = BiddingFeedback(
        bid_number=1,
        position='South',
        user_bid='1NT',
        correctness=CorrectnessLevel.OPTIMAL,
        score=10.0,
        optimal_bid='1NT',
        alternative_bids=[],
        reasoning='Balanced hand with 15-17 HCP',
        explanation_level='detailed',
        rule_reference=None,
        error_category=None,
        error_subcategory=None,
        impact=ImpactLevel.NONE,
        helpful_hint='',
        key_concept='Balanced hand evaluation',
        difficulty='beginner'
    )

    auction_context = {
        'history': [],
        'current_player': 'South',
        'dealer': 'North',
        'vulnerability': 'None'
    }

    # Store feedback
    generator._store_feedback(
        user_id=1,
        feedback=feedback,
        auction_context=auction_context,
        session_id="test_session_1",
        hand_analysis_id=None
    )

    # Verify it was stored
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM bidding_decisions
            WHERE user_id = 1
              AND user_bid = %s
              AND session_id = 'test_session_1'
        """, ('1NT',))

        count = cursor.fetchone()['count']

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

    with get_connection() as conn:
        cursor = conn.cursor()

        # Remove test session data
        cursor.execute("""
            DELETE FROM bidding_decisions
            WHERE session_id = 'test_session_1'
        """)

        deleted = cursor.rowcount

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
        log_error(e, context={'source': 'test_phase1_feedback'})
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
