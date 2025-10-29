#!/usr/bin/env python3
"""
Test to reproduce the 5NT bug from hand_2025-10-28_11-01-24.json

Auction:
North: 1♠ (opener)
South: 2NT (responder)
North: 3NT (opener rebid)
South: 4NT (Blackwood?)
North: 5NT (WRONG - should be 5♥ showing 2 aces)
"""

import sys
sys.path.insert(0, 'backend')

from engine.hand import Hand
from engine.bidding_engine import BiddingEngine
from engine.ai.feature_extractor import extract_features
from engine.ai.decision_engine import select_bidding_module

def create_north_hand():
    """North: ♠AKJT7 ♥Q6 ♦KJ9 ♣AQT (20 HCP)"""
    cards = []
    # Spades
    for rank in ['A', 'K', 'J', 'T', '7']:
        cards.append(type('Card', (), {'rank': rank, 'suit': '♠'})())
    # Hearts
    for rank in ['Q', '6']:
        cards.append(type('Card', (), {'rank': rank, 'suit': '♥'})())
    # Diamonds
    for rank in ['K', 'J', '9']:
        cards.append(type('Card', (), {'rank': rank, 'suit': '♦'})())
    # Clubs
    for rank in ['A', 'Q', 'T']:
        cards.append(type('Card', (), {'rank': rank, 'suit': '♣'})())

    hand = Hand(cards)
    return hand

def test_5nt_bug():
    """Reproduce the bug where North bids 5NT instead of 5♥"""

    # Setup
    engine = BiddingEngine()
    north_hand = create_north_hand()

    print("North's hand: ♠AKJT7 ♥Q6 ♦KJ9 ♣AQT")
    print(f"HCP: {north_hand.hcp}, Total Points: {north_hand.total_points}")
    print(f"Aces: {sum(1 for c in north_hand.cards if c.rank == 'A')}")
    print()

    # Auction so far:
    # North: 1♠, East: Pass, South: 2NT, West: Pass, North: 3NT, East: Pass, South: 4NT, West: Pass
    # Now it's North's turn to respond to 4NT

    auction_history = ['1♠', 'Pass', '2NT', 'Pass', '3NT', 'Pass', '4NT', 'Pass']
    my_position = 'North'
    vulnerability = 'None'

    print("Auction so far:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Extract features and determine module
    features = extract_features(north_hand, auction_history, my_position, vulnerability)
    module_name = select_bidding_module(features)

    print(f"Selected module: {module_name}")
    print()

    # Key features
    print("Key features:")
    print(f"  Partner's last bid: {features['auction_features'].get('partner_last_bid')}")
    print(f"  Opening bid: {features['auction_features'].get('opening_bid')}")
    print(f"  Opener relationship: {features['auction_features'].get('opener_relationship')}")
    print()

    # Check if Blackwood module would trigger
    blackwood = engine.modules['blackwood']

    # Test _is_ace_answering_applicable
    print("Testing Blackwood detection:")
    is_answering = blackwood._is_ace_answering_applicable(features)
    print(f"  _is_ace_answering_applicable: {is_answering}")

    if is_answering:
        ace_answer = blackwood._get_ace_answer_bid(north_hand)
        print(f"  Ace answer would be: {ace_answer}")
    else:
        print("  Blackwood not detected - analyzing why...")

        # Check partner's NT bids
        my_index = features.get('my_index', 0)
        partner_index = (my_index + 2) % 4
        partner_bids = [
            bid for i, bid in enumerate(auction_history)
            if (i % 4) == partner_index and bid not in ['Pass', 'X', 'XX']
        ]
        print(f"  Partner's bids: {partner_bids}")

        nt_bids = [bid for bid in partner_bids[:-1] if 'NT' in bid]
        print(f"  Partner's NT bids (before 4NT): {nt_bids}")

        # Check suit agreement
        my_suits = [bid[1] for bid in auction_history if (auction_history.index(bid) % 4) == my_index
                    and len(bid) >= 2 and bid[1] in '♣♦♥♠']
        partner_suits = [bid[1] for bid in partner_bids if len(bid) >= 2 and bid[1] in '♣♦♥♠']
        print(f"  My suits: {my_suits}")
        print(f"  Partner's suits: {partner_suits}")
        print(f"  Common suits: {set(my_suits) & set(partner_suits)}")

    print()

    # Get the actual bid
    bid, explanation = engine.get_next_bid(north_hand, auction_history, my_position, vulnerability)

    print(f"North's bid: {bid}")
    print(f"Explanation: {explanation}")
    print()

    if bid != "5♥":
        print("❌ BUG CONFIRMED: North should bid 5♥ (showing 2 aces) but bid", bid)
        return False
    else:
        print("✓ CORRECT: North bid 5♥ showing 2 aces")
        return True

if __name__ == '__main__':
    success = test_5nt_bug()
    sys.exit(0 if success else 1)
