#!/usr/bin/env python3
"""
Test script to verify Stayman fix for 7 HCP with 4-4 majors
Tests the exact hand from the bug report
"""
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_south_hand():
    """Create South's hand from bug report: KT73 K982 842 J2"""
    cards = [
        Card('K', '♠'), Card('T', '♠'), Card('7', '♠'), Card('3', '♠'),  # 4 spades
        Card('K', '♥'), Card('9', '♥'), Card('8', '♥'), Card('2', '♥'),  # 4 hearts
        Card('8', '♦'), Card('4', '♦'), Card('2', '♦'),  # 3 diamonds
        Card('J', '♣'), Card('2', '♣')  # 2 clubs
    ]
    return Hand(cards)

def test_stayman_7hcp_both_majors():
    print("=" * 70)
    print("Testing Stayman with 7 HCP and 4-4 Majors (Bug Report Hand)")
    print("=" * 70)

    engine = BiddingEngine()
    south_hand = create_south_hand()

    print("\nSouth's hand (You):")
    print(f"  Spades: K-T-7-3 (4 cards, {south_hand.suit_hcp['♠']} HCP)")
    print(f"  Hearts: K-9-8-2 (4 cards, {south_hand.suit_hcp['♥']} HCP)")
    print(f"  Diamonds: 8-4-2 (3 cards, {south_hand.suit_hcp['♦']} HCP)")
    print(f"  Clubs: J-2 (2 cards, {south_hand.suit_hcp['♣']} HCP)")
    print(f"  Total HCP: {south_hand.hcp}")
    print(f"  Shape: {south_hand.suit_lengths['♠']}-{south_hand.suit_lengths['♥']}-{south_hand.suit_lengths['♦']}-{south_hand.suit_lengths['♣']}")

    # Auction: North opens 1NT, East passes
    auction_history = ['1NT', 'Pass']

    print("\nAuction so far:")
    print("  1. North: 1NT (partner)")
    print("  2. East:  Pass")
    print("  3. South: ???")

    print("\n" + "-" * 70)
    print("Testing South's response...")
    print("-" * 70)

    bid, explanation = engine.get_next_bid(south_hand, auction_history, 'South', 'None')

    print(f"\nResult:")
    print(f"  Bid: {bid}")
    print(f"  Explanation: {explanation}")

    print("\n" + "=" * 70)
    if bid == '2♣':
        print("✅ SUCCESS! Stayman is now allowed with 7 HCP + 4-4 majors!")
        print("=" * 70)
        print("\nAnalysis:")
        print("  - 7 HCP with BOTH 4-card majors justifies Stayman")
        print("  - Finding an 8-card major fit is priority")
        print("  - After partner's response:")
        print("    * If 2♥ or 2♠: Pass (found fit, play at 2-level)")
        print("    * If 2♦: Pass (no fit found, stay at 2-level)")
        return True
    elif bid == 'Pass':
        print("❌ FAILED! Bug still present - system recommends Pass")
        print("=" * 70)
        print("\nStayman module still rejecting 7 HCP with 4-4 majors")
        return False
    else:
        print(f"❌ UNEXPECTED! South bid {bid} (expected 2♣)")
        print("=" * 70)
        return False

def test_edge_cases():
    """Test edge cases to ensure fix is correct"""
    print("\n" + "=" * 70)
    print("Testing Edge Cases")
    print("=" * 70)

    engine = BiddingEngine()
    auction = ['1NT', 'Pass']

    # Test 1: 7 HCP with only ONE 4-card major (should Pass)
    cards1 = [
        Card('K', '♠'), Card('T', '♠'), Card('7', '♠'), Card('3', '♠'),  # 4 spades
        Card('K', '♥'), Card('9', '♥'), Card('8', '♥'),  # 3 hearts (NOT 4)
        Card('8', '♦'), Card('4', '♦'), Card('2', '♦'),
        Card('J', '♣'), Card('2', '♣'), Card('3', '♣')
    ]
    hand1 = Hand(cards1)
    bid1, _ = engine.get_next_bid(hand1, auction, 'South', 'None')
    print(f"\nTest 1: 7 HCP, 4 spades, 3 hearts → {bid1}")
    if bid1 == 'Pass':
        print("  ✅ Correctly passes (7 HCP needs 4-4 majors)")
    else:
        print(f"  ❌ Should pass but got {bid1}")

    # Test 2: 6 HCP with 4-4 majors (should Pass)
    cards2 = [
        Card('K', '♠'), Card('T', '♠'), Card('7', '♠'), Card('3', '♠'),
        Card('Q', '♥'), Card('9', '♥'), Card('8', '♥'), Card('2', '♥'),  # 4 hearts but only 6 HCP
        Card('8', '♦'), Card('4', '♦'), Card('2', '♦'),
        Card('J', '♣'), Card('2', '♣')
    ]
    hand2 = Hand(cards2)
    bid2, _ = engine.get_next_bid(hand2, auction, 'South', 'None')
    print(f"\nTest 2: 6 HCP, 4-4 majors → {bid2}")
    if bid2 == 'Pass':
        print("  ✅ Correctly passes (minimum 7 HCP required)")
    else:
        print(f"  ❌ Should pass but got {bid2}")

    # Test 3: 8 HCP with one 4-card major (should bid Stayman)
    cards3 = [
        Card('K', '♠'), Card('Q', '♠'), Card('7', '♠'), Card('3', '♠'),  # 4 spades, 5 HCP
        Card('K', '♥'), Card('9', '♥'), Card('8', '♥'),  # 3 hearts
        Card('8', '♦'), Card('4', '♦'), Card('2', '♦'),
        Card('J', '♣'), Card('2', '♣'), Card('3', '♣')
    ]
    hand3 = Hand(cards3)
    bid3, _ = engine.get_next_bid(hand3, auction, 'South', 'None')
    print(f"\nTest 3: 8 HCP, 4 spades, 3 hearts → {bid3}")
    if bid3 == '2♣':
        print("  ✅ Correctly bids Stayman (8+ HCP with 4-card major)")
    else:
        print(f"  ❌ Should bid Stayman but got {bid3}")

if __name__ == "__main__":
    success = test_stayman_7hcp_both_majors()
    test_edge_cases()
    exit(0 if success else 1)
