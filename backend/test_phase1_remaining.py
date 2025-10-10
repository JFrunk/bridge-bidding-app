"""
Test suite for remaining Phase 1 critical fixes:
- Negative Doubles (applicability and level-adjusted HCP)
- Preempts (3-level and 4-level preemptive bids)
"""

from engine.bidding_engine import BiddingEngine
from engine.hand import Hand, Card

def create_hand(hand_str):
    """Helper to create a hand from string representation."""
    cards = []
    for char in hand_str:
        if char in '♠♥♦♣':
            current_suit = char
        elif char in 'AKQJT98765432':
            cards.append(Card(char, current_suit))
    return Hand(cards)

# ============================================================================
# TEST 1: Negative Doubles - Level-Adjusted HCP Requirements
# ============================================================================

def test_negative_double_1level():
    """Test negative double at 1-level (6+ HCP)."""
    engine = BiddingEngine()

    # South: 6 HCP, 4 spades (partner opened 1♣, RHO overcalled 1♥)
    south_hand = create_hand("♠QJ85 ♥94 ♦K752 ♣865")
    auction = ['1♣', 'Pass', '1♥', 'Pass']  # Partner opened, opp overcalled

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == 'X', f"Expected X (negative double) with 6 HCP at 1-level, got {bid}"
    print(f"✓ Test 1 passed: {bid} - {explanation}")

def test_negative_double_2level():
    """Test negative double at 2-level (6+ HCP)."""
    engine = BiddingEngine()

    # South: 7 HCP, 4 spades (partner opened 1♦, RHO overcalled 2♣)
    south_hand = create_hand("♠KJ85 ♥94 ♦Q752 ♣865")
    auction = ['1♦', 'Pass', '2♣', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == 'X', f"Expected X (negative double) with 7 HCP at 2-level, got {bid}"
    print(f"✓ Test 2 passed: {bid} - {explanation}")

def test_negative_double_3level_insufficient():
    """Test no negative double at 3-level with only 6 HCP (need 8+)."""
    engine = BiddingEngine()

    # South: 6 HCP, 4 spades (partner opened 1♦, RHO overcalled 3♣)
    south_hand = create_hand("♠QJ85 ♥94 ♦K752 ♣865")
    auction = ['1♦', 'Pass', '3♣', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid != 'X', f"Expected Pass (insufficient HCP for 3-level), got {bid}"
    print(f"✓ Test 3 passed: {bid} - {explanation}")

def test_negative_double_3level_sufficient():
    """Test negative double at 3-level (8+ HCP)."""
    engine = BiddingEngine()

    # South: 8 HCP, 4 spades (partner opened 1♦, RHO overcalled 3♣)
    south_hand = create_hand("♠KJ85 ♥K4 ♦Q752 ♣865")
    auction = ['1♦', 'Pass', '3♣', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == 'X', f"Expected X (negative double) with 8 HCP at 3-level, got {bid}"
    print(f"✓ Test 4 passed: {bid} - {explanation}")

def test_negative_double_4level_insufficient():
    """Test no negative double at 4-level with only 10 HCP (need 12+)."""
    engine = BiddingEngine()

    # South: 10 HCP, 4 spades (partner opened 1♥, RHO overcalled 4♣)
    south_hand = create_hand("♠KJ85 ♥K4 ♦Q752 ♣Q86")
    auction = ['1♥', 'Pass', '4♣', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid != 'X', f"Expected Pass (insufficient HCP for 4-level), got {bid}"
    print(f"✓ Test 5 passed: {bid} - {explanation}")

def test_negative_double_4level_sufficient():
    """Test negative double at 4-level (12+ HCP)."""
    engine = BiddingEngine()

    # South: 12 HCP, 4 spades (partner opened 1♥, RHO overcalled 4♣)
    south_hand = create_hand("♠AJ85 ♥K4 ♦Q752 ♣Q86")
    auction = ['1♥', 'Pass', '4♣', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == 'X', f"Expected X (negative double) with 12 HCP at 4-level, got {bid}"
    print(f"✓ Test 6 passed: {bid} - {explanation}")

# ============================================================================
# TEST 2: Negative Doubles - Improved Applicability
# ============================================================================

def test_negative_double_after_pass():
    """Test negative double works after RHO passes (balancing position)."""
    engine = BiddingEngine()

    # South: 8 HCP, 4 spades (partner opened 1♣, RHO overcalled 1♥, LHO passed)
    south_hand = create_hand("♠KJ85 ♥94 ♦Q752 ♣865")
    auction = ['1♣', 'Pass', '1♥', 'Pass', 'Pass', 'Pass']  # More passes in auction

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    # Should still be able to make negative double
    assert bid == 'X', f"Expected X (negative double) in balancing position, got {bid}"
    print(f"✓ Test 7 passed: {bid} - {explanation}")

# ============================================================================
# TEST 3: Preempts - 3-Level Preemptive Bids
# ============================================================================

def test_preempt_3level():
    """Test 3-level preempt with 7-card suit."""
    engine = BiddingEngine()

    # North: 8 HCP, 7-card spade suit with 2+ honors
    north_hand = create_hand("♠KQJ9876 ♥4 ♦932 ♣85")
    auction = []  # Opening bid

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '3♠', f"Expected 3♠ (3-level preempt) with 7-card suit, got {bid}"
    print(f"✓ Test 8 passed: {bid} - {explanation}")

def test_preempt_3level_diamonds():
    """Test 3-level preempt in diamonds."""
    engine = BiddingEngine()

    # North: 7 HCP, 7-card diamond suit with 2+ honors
    north_hand = create_hand("♠54 ♥98 ♦KQJ9876 ♣85")
    auction = []

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '3♦', f"Expected 3♦ (3-level preempt) with 7-card suit, got {bid}"
    print(f"✓ Test 9 passed: {bid} - {explanation}")

def test_preempt_3level_hearts():
    """Test 3-level preempt in hearts."""
    engine = BiddingEngine()

    # North: 9 HCP, 7-card heart suit with 2+ honors
    north_hand = create_hand("♠54 ♥KQJ9876 ♦932 ♣8")
    auction = []

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '3♥', f"Expected 3♥ (3-level preempt) with 7-card suit, got {bid}"
    print(f"✓ Test 10 passed: {bid} - {explanation}")

# ============================================================================
# TEST 4: Preempts - 4-Level Preemptive Bids
# ============================================================================

def test_preempt_4level():
    """Test 4-level preempt with 8-card suit."""
    engine = BiddingEngine()

    # North: 8 HCP, 8-card spade suit with 2+ honors
    north_hand = create_hand("♠KQJ98765 ♥4 ♦932 ♣8")
    auction = []

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '4♠', f"Expected 4♠ (4-level preempt) with 8-card suit, got {bid}"
    print(f"✓ Test 11 passed: {bid} - {explanation}")

def test_preempt_4level_hearts():
    """Test 4-level preempt in hearts."""
    engine = BiddingEngine()

    # North: 7 HCP, 8-card heart suit with 2+ honors
    north_hand = create_hand("♠5 ♥KQJ98765 ♦932 ♣8")
    auction = []

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '4♥', f"Expected 4♥ (4-level preempt) with 8-card suit, got {bid}"
    print(f"✓ Test 12 passed: {bid} - {explanation}")

# ============================================================================
# TEST 5: Preempts - Priority (Longer Suits Take Precedence)
# ============================================================================

def test_preempt_priority_8over7():
    """Test that 8-card suit gets 4-level preempt over 7-card 3-level."""
    engine = BiddingEngine()

    # More realistic: 8-card spades should get priority
    north_hand = create_hand("♠KQJ98765 ♥4 ♦93 ♣82")
    auction = []

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '4♠', f"Expected 4♠ (8-card suit) with priority, got {bid}"
    print(f"✓ Test 13 passed: {bid} - {explanation}")

def test_preempt_priority_7over6():
    """Test that 7-card suit gets 3-level preempt over 6-card 2-level."""
    engine = BiddingEngine()

    # North: 8 HCP, 7-card spades - should bid 3♠ not 2♠
    north_hand = create_hand("♠KQJ9876 ♥4 ♦932 ♣85")
    auction = []

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '3♠', f"Expected 3♠ (7-card suit) over 2♠, got {bid}"
    print(f"✓ Test 14 passed: {bid} - {explanation}")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("=" * 70)
    print("PHASE 1 REMAINING FIXES - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("Negative Double - 1-level (6+ HCP)", test_negative_double_1level),
        ("Negative Double - 2-level (6+ HCP)", test_negative_double_2level),
        ("Negative Double - 3-level insufficient (6 HCP)", test_negative_double_3level_insufficient),
        ("Negative Double - 3-level sufficient (8 HCP)", test_negative_double_3level_sufficient),
        ("Negative Double - 4-level insufficient (10 HCP)", test_negative_double_4level_insufficient),
        ("Negative Double - 4-level sufficient (12 HCP)", test_negative_double_4level_sufficient),
        ("Negative Double - Balancing position", test_negative_double_after_pass),
        ("Preempt - 3♠ with 7-card suit", test_preempt_3level),
        ("Preempt - 3♦ with 7-card suit", test_preempt_3level_diamonds),
        ("Preempt - 3♥ with 7-card suit", test_preempt_3level_hearts),
        ("Preempt - 4♠ with 8-card suit", test_preempt_4level),
        ("Preempt - 4♥ with 8-card suit", test_preempt_4level_hearts),
        ("Preempt - 8-card priority over 7-card", test_preempt_priority_8over7),
        ("Preempt - 7-card priority over 6-card", test_preempt_priority_7over6),
    ]

    passed = 0
    failed = 0
    errors = []

    for test_name, test_func in tests:
        try:
            print(f"Running: {test_name}")
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"✗ FAILED: {e}")
        except Exception as e:
            failed += 1
            errors.append((test_name, f"ERROR: {e}"))
            print(f"✗ ERROR: {e}")
        print()

    print("=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print("=" * 70)

    if errors:
        print("\nFailed tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")

    return passed == len(tests)

if __name__ == '__main__':
    import sys
    sys.exit(0 if main() else 1)
