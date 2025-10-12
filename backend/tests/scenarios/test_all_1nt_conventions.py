#!/usr/bin/env python3
"""
Comprehensive test for all 1NT convention completions
"""
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_hand_from_string(spades, hearts, diamonds, clubs):
    """Create a hand from string representations like 'AK4'"""
    cards = []
    for rank in spades:
        cards.append(Card(rank, '♠'))
    for rank in hearts:
        cards.append(Card(rank, '♥'))
    for rank in diamonds:
        cards.append(Card(rank, '♦'))
    for rank in clubs:
        cards.append(Card(rank, '♣'))
    return Hand(cards)

def test_scenario(name, hand, auction, expected_bid, description):
    """Test a single bidding scenario"""
    print(f"\n{'=' * 70}")
    print(f"Test: {name}")
    print(f"{'=' * 70}")

    engine = BiddingEngine()

    print(f"Hand: {hand.hcp} HCP, {hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
    print(f"Auction: {' - '.join(auction)}")
    print(f"Expected: {expected_bid}")

    bid, explanation = engine.get_next_bid(hand, auction, 'North', 'None')

    print(f"Result: {bid}")
    print(f"Explanation: {explanation}")

    if bid == expected_bid:
        print(f"✅ PASS - {description}")
        return True
    else:
        print(f"❌ FAIL - Got {bid}, expected {expected_bid}")
        return False

def run_all_tests():
    """Run comprehensive tests for 1NT conventions"""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE 1NT CONVENTION COMPLETION TESTS")
    print("=" * 70)

    tests_passed = 0
    tests_total = 0

    # Test 1: Jacoby Transfer to Spades (3-card support, simple acceptance)
    tests_total += 1
    hand1 = create_hand_from_string('AK4', 'K53', '862', 'AQJ8')
    if test_scenario(
        "Jacoby Transfer to Spades - Simple Acceptance",
        hand1,
        ['1NT', 'Pass', '2♥', 'Pass'],
        '2♠',
        "3-card support, complete transfer"
    ):
        tests_passed += 1

    # Test 2: Jacoby Transfer to Spades (4-card support, super-accept)
    tests_total += 1
    hand2 = create_hand_from_string('AK74', 'K5', '862', 'AQJ8')
    if test_scenario(
        "Jacoby Transfer to Spades - Super-Accept",
        hand2,
        ['1NT', 'Pass', '2♥', 'Pass'],
        '3♠',
        "4-card support + 17 HCP, super-accept"
    ):
        tests_passed += 1

    # Test 3: Jacoby Transfer to Hearts (3-card support)
    tests_total += 1
    hand3 = create_hand_from_string('AK4', 'KJ5', '862', 'AQJ8')
    if test_scenario(
        "Jacoby Transfer to Hearts - Simple Acceptance",
        hand3,
        ['1NT', 'Pass', '2♦', 'Pass'],
        '2♥',
        "3-card heart support, complete transfer"
    ):
        tests_passed += 1

    # Test 4: Jacoby Transfer with only 2-card support (reject with 2NT)
    tests_total += 1
    hand4 = create_hand_from_string('AK', 'K53', '8642', 'AQJ8')
    if test_scenario(
        "Jacoby Transfer to Spades - Rejection (doubleton)",
        hand4,
        ['1NT', 'Pass', '2♥', 'Pass'],
        '2NT',
        "Only 2 spades + 17 HCP, reject transfer with 2NT"
    ):
        tests_passed += 1

    # Test 5: Stayman with 4-card major
    tests_total += 1
    hand5 = create_hand_from_string('AK74', 'K5', '862', 'AQJ8')
    if test_scenario(
        "Stayman Response - 4-card Spades",
        hand5,
        ['1NT', 'Pass', '2♣', 'Pass'],
        '2♠',
        "4 spades, respond to Stayman"
    ):
        tests_passed += 1

    # Test 6: Stayman with 4-card hearts
    tests_total += 1
    hand6 = create_hand_from_string('AK4', 'KJ75', '86', 'AQJ8')
    if test_scenario(
        "Stayman Response - 4-card Hearts",
        hand6,
        ['1NT', 'Pass', '2♣', 'Pass'],
        '2♥',
        "4 hearts, respond to Stayman"
    ):
        tests_passed += 1

    # Test 7: Stayman with no 4-card major
    tests_total += 1
    hand7 = create_hand_from_string('AK4', 'K53', '862', 'AQJ8')
    if test_scenario(
        "Stayman Response - No 4-card Major",
        hand7,
        ['1NT', 'Pass', '2♣', 'Pass'],
        '2♦',
        "No 4-card major, deny with 2♦"
    ):
        tests_passed += 1

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("✅ ALL TESTS PASSED!")
        return True
    else:
        print(f"❌ {tests_total - tests_passed} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
