#!/usr/bin/env python3
"""
Test to reproduce the illegal bid bug: East bids 1♠ after North opens 1♠
"""
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_east_hand():
    """Create East's hand from bug report: 87 Q4 Q6432 T852"""
    cards = [
        Card('8', '♠'), Card('7', '♠'),  # 2 spades, 0 HCP
        Card('Q', '♥'), Card('4', '♥'),  # 2 hearts, 2 HCP
        Card('Q', '♦'), Card('6', '♦'), Card('4', '♦'), Card('3', '♦'), Card('2', '♦'),  # 5 diamonds, 2 HCP
        Card('T', '♣'), Card('8', '♣'), Card('5', '♣'), Card('2', '♣')  # 4 clubs, 0 HCP
    ]
    return Hand(cards)

def test_illegal_duplicate_bid():
    print("=" * 70)
    print("Testing Illegal Duplicate Bid Bug")
    print("=" * 70)

    engine = BiddingEngine()
    east_hand = create_east_hand()

    print("\nEast's hand:")
    print(f"  Spades: 8-7 (2 cards, {east_hand.suit_hcp['♠']} HCP)")
    print(f"  Hearts: Q-4 (2 cards, {east_hand.suit_hcp['♥']} HCP)")
    print(f"  Diamonds: Q-6-4-3-2 (5 cards, {east_hand.suit_hcp['♦']} HCP)")
    print(f"  Clubs: T-8-5-2 (4 cards, {east_hand.suit_hcp['♣']} HCP)")
    print(f"  Total HCP: {east_hand.hcp}")
    print(f"  Total Points: {east_hand.total_points}")
    print(f"  Shape: {east_hand.suit_lengths['♠']}-{east_hand.suit_lengths['♥']}-{east_hand.suit_lengths['♦']}-{east_hand.suit_lengths['♣']}")

    # Auction: North opens 1♠
    auction_history = ['1♠']

    print("\nAuction so far:")
    print("  1. North: 1♠")
    print("  2. East:  ???")

    print("\n" + "-" * 70)
    print("Testing East's bid after North opens 1♠...")
    print("-" * 70)

    bid, explanation = engine.get_next_bid(east_hand, auction_history, 'East', 'EW')

    print(f"\nResult:")
    print(f"  Bid: {bid}")
    print(f"  Explanation: {explanation}")

    print("\n" + "=" * 70)
    if bid == '1♠':
        print("❌ BUG REPRODUCED! East bid 1♠ (same as North's 1♠)")
        print("=" * 70)
        print("\nThis is ILLEGAL - you cannot bid the same bid!")
        print("East should Pass (only 4 HCP, too weak to compete)")
        return False
    elif bid == 'Pass':
        print("✅ CORRECT! East passed (too weak to compete)")
        print("=" * 70)
        return True
    else:
        print(f"⚠️  East bid {bid}")
        print("=" * 70)
        print(f"This is legal but unusual for 4 HCP")
        return True

if __name__ == "__main__":
    success = test_illegal_duplicate_bid()
    exit(0 if success else 1)
