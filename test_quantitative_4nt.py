#!/usr/bin/env python3
"""
Test that quantitative 4NT still works (not treated as Blackwood).

Pattern: 1NT - 4NT should be quantitative (inviting 6NT), not Blackwood
"""

import sys
sys.path.insert(0, 'backend')

from engine.hand import Hand
from engine.bidding_engine import BiddingEngine

def create_hand_17hcp():
    """Create a 17 HCP balanced hand (4-3-3-3)"""
    cards = []
    # Spades: AKQ5 (11 HCP)
    for rank in ['A', 'K', 'Q', '5']:
        cards.append(type('Card', (), {'rank': rank, 'suit': '♠'})())
    # Hearts: Q54 (2 HCP)
    for rank in ['Q', '5', '4']:
        cards.append(type('Card', (), {'rank': rank, 'suit': '♥'})())
    # Diamonds: K32 (3 HCP)
    for rank in ['K', '3', '2']:
        cards.append(type('Card', (), {'rank': rank, 'suit': '♦'})())
    # Clubs: J32 (1 HCP)
    for rank in ['J', '3', '2']:
        cards.append(type('Card', (), {'rank': rank, 'suit': '♣'})())

    hand = Hand(cards)
    return hand

def test_quantitative_4nt():
    """Test that 1NT-4NT is quantitative, not Blackwood"""

    engine = BiddingEngine()
    hand = create_hand_17hcp()

    print("Hand: ♠AKQ5 ♥Q54 ♦K32 ♣J32")
    print(f"HCP: {hand.hcp}, Total Points: {hand.total_points}")
    print()

    # Auction: Partner opened 1NT, we bid 4NT quantitative
    # Now partner needs to decide: Pass (minimum) or bid 6NT (maximum)
    auction_history = ['1NT', 'Pass', '4NT', 'Pass']
    my_position = 'North'
    vulnerability = 'None'

    print("Auction so far:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Get the bid
    bid, explanation = engine.get_next_bid(hand, auction_history, my_position, vulnerability)

    print(f"North's bid: {bid}")
    print(f"Explanation: {explanation}")
    print()

    # After 1NT-4NT, opener should Pass (with minimum) or bid 6NT (with maximum)
    # It should NOT be treated as Blackwood (ace-asking)
    if bid in ['5♣', '5♦', '5♥', '5♠']:
        print(f"❌ ERROR: Bid {bid} looks like Blackwood response (showing aces)")
        print("   This should be quantitative, not Blackwood!")
        return False
    elif bid in ['Pass', '5NT', '6NT']:
        print(f"✓ CORRECT: Bid {bid} is appropriate for quantitative 4NT")
        return True
    else:
        print(f"⚠ UNEXPECTED: Bid {bid} - need to review")
        return False

if __name__ == '__main__':
    success = test_quantitative_4nt()
    sys.exit(0 if success else 1)
