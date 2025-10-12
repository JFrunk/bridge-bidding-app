#!/usr/bin/env python3
"""
Test script to verify Jacoby Transfer fix
This reproduces the exact scenario from the bug report
"""
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_test_hand():
    """Create North's hand from the bug report: AK4 K53 862 AQJ8"""
    cards = [
        Card('A', '♠'), Card('K', '♠'), Card('4', '♠'),  # Spades: 3 cards
        Card('K', '♥'), Card('5', '♥'), Card('3', '♥'),  # Hearts: 3 cards
        Card('8', '♦'), Card('6', '♦'), Card('2', '♦'),  # Diamonds: 3 cards
        Card('A', '♣'), Card('Q', '♣'), Card('J', '♣'), Card('8', '♣')  # Clubs: 4 cards
    ]
    return Hand(cards)

def test_jacoby_transfer_completion():
    print("=" * 70)
    print("Testing Jacoby Transfer Completion Fix")
    print("=" * 70)

    engine = BiddingEngine()
    north_hand = create_test_hand()

    print("\nNorth's hand:")
    print(f"  Spades: A-K-4 (3 cards, {north_hand.suit_hcp['♠']} HCP)")
    print(f"  Hearts: K-5-3 (3 cards, {north_hand.suit_hcp['♥']} HCP)")
    print(f"  Diamonds: 8-6-2 (3 cards, {north_hand.suit_hcp['♦']} HCP)")
    print(f"  Clubs: A-Q-J-8 (4 cards, {north_hand.suit_hcp['♣']} HCP)")
    print(f"  Total HCP: {north_hand.hcp}")
    print(f"  Shape: {north_hand.suit_lengths['♠']}-{north_hand.suit_lengths['♥']}-{north_hand.suit_lengths['♦']}-{north_hand.suit_lengths['♣']}")

    # Simulate the auction from the bug report
    # 1NT - Pass - 2♥ (Jacoby Transfer) - Pass - ?
    auction_history = ['1NT', 'Pass', '2♥', 'Pass']

    print("\nAuction so far:")
    print("  1. North: 1NT")
    print("  2. East:  Pass")
    print("  3. South: 2♥ (Jacoby Transfer showing 5+ spades)")
    print("  4. West:  Pass")
    print("  5. North: ???")

    print("\n" + "-" * 70)
    print("Testing North's rebid...")
    print("-" * 70)

    bid, explanation = engine.get_next_bid(north_hand, auction_history, 'North', 'None')

    print(f"\nResult:")
    print(f"  Bid: {bid}")
    print(f"  Explanation: {explanation}")

    print("\n" + "=" * 70)
    if bid == '2♠':
        print("✅ SUCCESS! Jacoby Transfer completed correctly!")
        print("=" * 70)
        print("\nAnalysis:")
        print("  - North correctly completed the transfer to 2♠")
        print("  - With 3-card support and 17 HCP, simple acceptance is correct")
        print("  - Super-accept (3♠) requires 4-card support")
        print("  - The 2NT alternative (doubleton rejection) doesn't apply with 3 cards")
        return True
    elif bid == '2NT':
        print("❌ FAILED! Bug still present - North bid 2NT instead of 2♠")
        print("=" * 70)
        print("\nThis is the original bug - Jacoby module not being consulted")
        return False
    else:
        print(f"❌ UNEXPECTED! North bid {bid} (expected 2♠)")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = test_jacoby_transfer_completion()
    exit(0 if success else 1)
