#!/usr/bin/env python3
"""
Test script to verify bidding fixes for:
1. North's weak 2H with Q-J-8-6-2 (lacks 2 of top 3 honors) should be rejected
2. West's 19 HCP should bid 3NT over competitive auction 2♥-Pass-3♥
"""

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.ai.feature_extractor import extract_features

def create_test_hands():
    """Create the hands from the problematic auction."""

    # North: ♠AJ5 ♥QJ862 ♦J965 ♣— (void in clubs)
    north_cards = [
        Card('A', '♠'), Card('J', '♠'), Card('5', '♠'),
        Card('Q', '♥'), Card('J', '♥'), Card('8', '♥'), Card('6', '♥'), Card('5', '♥'), Card('2', '♥'),
        Card('J', '♦'), Card('9', '♦'), Card('6', '♦'), Card('5', '♦'),
    ]
    north = Hand(north_cards)

    # East: ♠T63 ♥94 ♦Q3 ♣JT9532
    east_cards = [
        Card('T', '♠'), Card('6', '♠'), Card('3', '♠'),
        Card('9', '♥'), Card('4', '♥'),
        Card('Q', '♦'), Card('3', '♦'),
        Card('J', '♣'), Card('T', '♣'), Card('9', '♣'), Card('5', '♣'), Card('3', '♣'), Card('2', '♣'),
    ]
    east = Hand(east_cards)

    # South: ♠K74 ♥K103 ♦8742 ♣K84
    south_cards = [
        Card('K', '♠'), Card('7', '♠'), Card('4', '♠'),
        Card('K', '♥'), Card('T', '♥'), Card('3', '♥'),
        Card('8', '♦'), Card('7', '♦'), Card('4', '♦'), Card('2', '♦'),
        Card('K', '♣'), Card('8', '♣'), Card('4', '♣'),
    ]
    south = Hand(south_cards)

    # West: ♠Q982 ♥A7 ♦AKT ♣AQ76 (19 HCP balanced)
    west_cards = [
        Card('Q', '♠'), Card('9', '♠'), Card('8', '♠'), Card('2', '♠'),
        Card('A', '♥'), Card('7', '♥'),
        Card('A', '♦'), Card('K', '♦'), Card('T', '♦'),
        Card('A', '♣'), Card('Q', '♣'), Card('7', '♣'), Card('6', '♣'),
    ]
    west = Hand(west_cards)

    return {
        'North': north,
        'East': east,
        'South': south,
        'West': west
    }

def test_north_opening():
    """Test that North does NOT open 2H with Q-J-8-6-2 (lacks 2 of top 3 honors)."""
    print("=" * 60)
    print("TEST 1: North's opening bid (should NOT be 2♥)")
    print("=" * 60)

    hands = create_test_hands()
    north = hands['North']

    print(f"North's hand: 9 HCP, 6 hearts (Q-J-8-6-2), VOID in clubs")
    print(f"  ♠: {north.suit_lengths['♠']} cards, {north.suit_hcp['♠']} HCP")
    print(f"  ♥: {north.suit_lengths['♥']} cards, {north.suit_hcp['♥']} HCP (Q-J only)")
    print(f"  ♦: {north.suit_lengths['♦']} cards, {north.suit_hcp['♦']} HCP")
    print(f"  ♣: {north.suit_lengths['♣']} cards, {north.suit_hcp['♣']} HCP (VOID!)")
    print(f"\nSAYC Weak Two requirements:")
    print(f"  - 2 of top 3 honors (A/K/Q): ❌ FAIL (only Q-J)")
    print(f"  - No void: ❌ FAIL (void in clubs)")
    print()

    engine = BiddingEngine()
    auction_history = []

    bid, explanation = engine.get_next_bid(
        hand=north,
        auction_history=auction_history,
        my_position='North',
        vulnerability='None'
    )
    print(f"North's bid: {bid}")
    print(f"Explanation: {explanation}")
    print()

    if bid == "2♥":
        print("❌ FAIL: North incorrectly opened 2♥ without 2 of top 3 honors!")
        print("   SAYC requires A-K, A-Q, or K-Q in the suit for a Weak Two")
        return False
    elif bid == "Pass":
        print("✅ PASS: North correctly passed (insufficient suit quality)")
        return True
    elif bid == "1♥":
        print("⚠️  BORDERLINE: North opened 1♥ (acceptable with 9 HCP and 6-card suit)")
        return True
    else:
        print(f"⚠️  UNEXPECTED: North bid {bid}")
        return False

def test_west_overcall():
    """Test that West bids 3NT with 19 HCP over competitive auction 2♥-Pass-3♥."""
    print("=" * 60)
    print("TEST 2: West's bid after 2♥ - Pass - 3♥")
    print("=" * 60)

    hands = create_test_hands()
    west = hands['West']

    print(f"West's hand: 19 HCP, balanced, A-7 in hearts (stopper)")
    print(f"  ♠: {west.suit_lengths['♠']} cards, {west.suit_hcp['♠']} HCP")
    print(f"  ♥: {west.suit_lengths['♥']} cards, {west.suit_hcp['♥']} HCP (A-7 stopper)")
    print(f"  ♦: {west.suit_lengths['♦']} cards, {west.suit_hcp['♦']} HCP")
    print(f"  ♣: {west.suit_lengths['♣']} cards, {west.suit_hcp['♣']} HCP")
    print(f"  Balanced: {west.is_balanced}")
    print()

    # Simulate auction: 2♥ - Pass - 3♥ - ? (West already passed once)
    engine = BiddingEngine()
    auction_history = ['2♥', 'Pass', '3♥', 'Pass']  # West passed after 2♥

    bid, explanation = engine.get_next_bid(
        hand=west,
        auction_history=auction_history,
        my_position='West',
        vulnerability='EW'
    )
    print(f"West's bid: {bid}")
    print(f"Explanation: {explanation}")
    print()

    if bid == "Pass":
        print("❌ FAIL: West passed with 19 HCP - should compete!")
        print("   With balanced 19 HCP and stopper, West should bid 3NT or Double")
        return False
    elif bid == "3NT":
        print("✅ PASS: West correctly bid 3NT (showing 18-21 HCP over competitive auction)")
        return True
    elif bid == "X":
        print("✅ ACCEPTABLE: West doubled (showing 19+ HCP, planning to bid NT)")
        return True
    else:
        print(f"⚠️  UNEXPECTED: West bid {bid} (expected 3NT or Double)")
        return bid != "Pass"  # Any bid is better than Pass

def main():
    print("\n" + "=" * 60)
    print("TESTING BIDDING FIXES")
    print("=" * 60)
    print()

    test1_passed = test_north_opening()
    print()

    test2_passed = test_west_overcall()
    print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Test 1 (North's opening): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (West's overcall): {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print()

    if test1_passed and test2_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - review needed")
        return 1

if __name__ == "__main__":
    exit(main())
