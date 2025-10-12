"""
Phase 2 Enhancements - Test Suite

Tests for new bidding features:
1. 2NT invitational response (11-12 HCP, balanced)
2. Jump shift responses (17+ HCP, game-forcing)
3. Reverse bids (17+ HCP, forcing)
"""

import sys
from engine.bidding_engine import BiddingEngine
from engine.hand import Hand, Card

def create_hand(cards_str):
    """Helper to create a hand from card string like '♠AK52 ♥QJ3 ♦K876 ♣Q5'"""
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        ranks = part[1:]
        for rank in ranks:
            cards.append(Card(rank, suit))
    return Hand(cards)

def run_test(test_name, hand, auction, expected_bid, expected_explanation_contains):
    """Run a single test case"""
    print(f"\nRunning: {test_name}")
    print(f"  Hand: {hand}")
    print(f"  Auction: {auction}")

    engine = BiddingEngine()
    bid, explanation = engine.get_next_bid(hand, auction, 'South', 'None')

    # Check if bid matches
    if bid != expected_bid:
        print(f"  ❌ Test failed: Expected '{expected_bid}', got '{bid}'")
        print(f"     Explanation: {explanation}")
        return False

    # Check if explanation contains expected text
    if expected_explanation_contains and expected_explanation_contains.lower() not in explanation.lower():
        print(f"  ❌ Test failed: Expected explanation to contain '{expected_explanation_contains}'")
        print(f"     Got: {explanation}")
        return False

    print(f"  ✅ Test passed: {bid} - {explanation}")
    return True

# ============================================================================
# TEST SUITE
# ============================================================================

def main():
    print("=" * 70)
    print("PHASE 2 ENHANCEMENTS - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    tests_passed = 0
    tests_total = 0

    # ========================================================================
    # 2NT INVITATIONAL RESPONSE TESTS (11-12 HCP, balanced)
    # ========================================================================

    # Test 1: 2NT response with 11 HCP, balanced, no fit
    tests_total += 1
    hand1 = create_hand("♠KJ52 ♥QJ3 ♦K876 ♣Q5")  # 11 HCP, balanced (13 cards)
    if run_test(
        "2NT invitational (11 HCP, balanced, no fit)",
        hand1,
        ['1♣', 'Pass', 'Pass', 'Pass'],  # Partner opened 1♣
        "2NT",
        "11-12 HCP"
    ):
        tests_passed += 1

    # Test 2: 2NT response with 12 HCP, balanced, no fit
    tests_total += 1
    hand2 = create_hand("♠AJ52 ♥QJ3 ♦K876 ♣Q5")  # 12 HCP, balanced (13 cards)
    if run_test(
        "2NT invitational (12 HCP, balanced, no fit)",
        hand2,
        ['1♦', 'Pass', 'Pass', 'Pass'],  # Partner opened 1♦
        "2NT",
        "11-12 HCP"
    ):
        tests_passed += 1

    # Test 3: 1NT with 10 HCP (should NOT bid 2NT)
    tests_total += 1
    hand3 = create_hand("♠KJ52 ♥Q93 ♦K876 ♣Q5")  # 10 HCP, balanced (13 cards)
    if run_test(
        "1NT response (10 HCP, not enough for 2NT)",
        hand3,
        ['1♣', 'Pass', 'Pass', 'Pass'],
        "1NT",
        "6-10 HCP"
    ):
        tests_passed += 1

    # ========================================================================
    # JUMP SHIFT RESPONSE TESTS (17+ HCP, game-forcing)
    # ========================================================================

    # Test 4: Jump shift 2♥ after 1♣ opening (18 HCP, 5+ hearts)
    tests_total += 1
    hand4 = create_hand("♠AK52 ♥AQJ32 ♦KQ ♣54")  # 18 HCP, 5 hearts (13 cards)
    if run_test(
        "Jump shift 2♥ after 1♣ (17+ HCP)",
        hand4,
        ['1♣', 'Pass', 'Pass', 'Pass'],
        "2♥",
        "17+ HCP"
    ):
        tests_passed += 1

    # Test 5: Jump shift 2♠ after 1♦ opening (19 HCP, 5+ spades)
    tests_total += 1
    hand5 = create_hand("♠AKQ32 ♥AQ3 ♦K7 ♣Q54")  # 19 HCP, 5 spades (13 cards)
    if run_test(
        "Jump shift 2♠ after 1♦ (19 HCP)",
        hand5,
        ['1♦', 'Pass', 'Pass', 'Pass'],
        "2♠",
        "17+ HCP"
    ):
        tests_passed += 1

    # Test 6: Jump shift 3♣ after 1♦ opening (19 HCP, 5+ clubs)
    tests_total += 1
    hand6 = create_hand("♠AK52 ♥AQ3 ♦K7 ♣AQ95")  # 19 HCP, 5 clubs (13 cards: corrected to 4 clubs)
    # Actually let's make this 5 clubs
    hand6 = create_hand("♠AK5 ♥AQ3 ♦K72 ♣AQ95")  # 19 HCP, 4 clubs - need 5, fix again
    hand6 = create_hand("♠AK ♥AQ3 ♦K72 ♣AQ954")  # 19 HCP, 5 clubs (13 cards)
    if run_test(
        "Jump shift 3♣ after 1♦ (18+ HCP)",
        hand6,
        ['1♦', 'Pass', 'Pass', 'Pass'],
        "3♣",
        "17+ HCP"
    ):
        tests_passed += 1

    # Test 7: Jump shift 3♦ after 1♠ opening (20 HCP, 5+ diamonds)
    tests_total += 1
    hand7 = create_hand("♠K52 ♥AKQ ♦AQJ32 ♣Q5")  # 20 HCP, 5 diamonds (13 cards)
    if run_test(
        "Jump shift 3♦ after 1♠ (20 HCP)",
        hand7,
        ['1♠', 'Pass', 'Pass', 'Pass'],
        "3♦",
        "17+ HCP"
    ):
        tests_passed += 1

    # Test 8: Regular 1♥ response, not jump shift (13 HCP, not strong enough)
    tests_total += 1
    hand8 = create_hand("♠K52 ♥AQJ32 ♦KQ ♣854")  # 13 HCP, 5 hearts (13 cards)
    if run_test(
        "Regular 1♥ (13 HCP, not jump shift)",
        hand8,
        ['1♣', 'Pass', 'Pass', 'Pass'],
        "1♥",
        "4+ card heart"
    ):
        tests_passed += 1

    # ========================================================================
    # REVERSE BID TESTS (17+ HCP, forcing)
    # ========================================================================

    # Test 9: Reverse 2♥ after 1♦ opening (18 HCP, hearts > diamonds)
    tests_total += 1
    hand9 = create_hand("♠A52 ♥AKJ3 ♦KQ732 ♣Q")  # 18 HCP, 5 diamonds, 4 hearts (13 cards)
    if run_test(
        "Reverse 2♥ after 1♦-1♠ (18 HCP)",
        hand9,
        ['1♦', 'Pass', '1♠', 'Pass'],
        "2♥",
        "reverse"
    ):
        tests_passed += 1

    # Test 10: NOT reverse - should support partner's spades with 19+ HCP
    tests_total += 1
    hand10 = create_hand("♠K52 ♥AKJ32 ♦A7 ♣AQ5")  # 19 HCP, 5 hearts, 3 spades (13 cards)
    if run_test(
        "NOT reverse after 1♥-1♠ (rebid should not be reverse)",
        hand10,
        ['1♥', 'Pass', '1♠', 'Pass'],
        "4♠",  # With 19+ HCP and 3-card support, should jump to game
        "strong"
    ):
        tests_passed += 1

    # Test 11: Reverse 2♥ after 1♣ opening (17 HCP, hearts > clubs)
    tests_total += 1
    hand11 = create_hand("♠A52 ♥AKJ3 ♦Q7 ♣KQ73")  # 17 HCP, 5 clubs (need 5), 4 hearts
    # Fix to have 5 clubs
    hand11 = create_hand("♠A5 ♥AKJ3 ♦Q72 ♣KQ73")  # 17 HCP, 4 clubs (need 5)
    # Fix again
    hand11 = create_hand("♠A5 ♥AKJ3 ♦Q7 ♣KQ732")  # 17 HCP, 5 clubs, 4 hearts (13 cards)
    if run_test(
        "Reverse 2♥ after 1♣-1♦ (17 HCP)",
        hand11,
        ['1♣', 'Pass', '1♦', 'Pass'],
        "2♥",
        "reverse"
    ):
        tests_passed += 1

    # Test 12: NOT reverse - 2♣ after 1♦ (clubs < diamonds, not forcing)
    tests_total += 1
    hand12 = create_hand("♠A52 ♥Q3 ♦AQ732 ♣KJ5")  # 14 HCP, 5 diamonds, 3 clubs (13 cards)
    if run_test(
        "NOT reverse 2♣ after 1♦-1♠ (not reverse, minimum hand)",
        hand12,
        ['1♦', 'Pass', '1♠', 'Pass'],
        "1NT",  # Balanced 12-14, no fit
        "balanced"
    ):
        tests_passed += 1

    # Test 13: Reverse with 19+ HCP shows slam interest
    tests_total += 1
    hand13 = create_hand("♠A52 ♥AKQ3 ♦AQJ32 ♣Q")  # 20 HCP, 5 diamonds, 4 hearts (13 cards)
    if run_test(
        "Reverse 2♥ after 1♦-1♠ (20 HCP, slam interest)",
        hand13,
        ['1♦', 'Pass', '1♠', 'Pass'],
        "2♥",
        "19+ HCP"
    ):
        tests_passed += 1

    # ========================================================================
    # RESULTS
    # ========================================================================

    print("\n" + "=" * 70)
    print(f"RESULTS: {tests_passed}/{tests_total} tests passed")
    print("=" * 70)

    if tests_passed == tests_total:
        print("✅ All Phase 2 enhancement tests passed!")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
