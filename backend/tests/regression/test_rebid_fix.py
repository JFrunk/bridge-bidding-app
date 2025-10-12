"""
Test script to verify the rebid fix for showing a second 4+ card suit.
Tests the specific scenario from the user's hand.
"""

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.ai.feature_extractor import extract_features

def test_north_rebid_with_5_5_minors():
    """
    Test that North correctly rebids 2♣ with 5-5 in minors after:
    North: 1♦
    East: Pass
    South: 1♥ (partner's response)
    West: Pass

    North has: K, 32, AQT94, QT976 (11 HCP, 5-5 minors, 13 total points)
    """

    # Create North's hand
    north_cards = [
        Card('K', '♠'),
        Card('3', '♥'), Card('2', '♥'),
        Card('A', '♦'), Card('Q', '♦'), Card('T', '♦'), Card('9', '♦'), Card('4', '♦'),
        Card('Q', '♣'), Card('T', '♣'), Card('9', '♣'), Card('7', '♣'), Card('6', '♣')
    ]
    north_hand = Hand(north_cards)

    print(f"North's hand: {north_hand}")
    print(f"  HCP: {north_hand.hcp}, Total Points: {north_hand.total_points}")
    print(f"  Distribution: ♠{north_hand.suit_lengths['♠']} ♥{north_hand.suit_lengths['♥']} ♦{north_hand.suit_lengths['♦']} ♣{north_hand.suit_lengths['♣']}")
    print()

    # Create the auction history
    auction_history = [
        '1♦',   # North opens
        'Pass', # East passes
        '1♥',   # South responds
        'Pass'  # West passes
    ]

    print("Auction so far:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Create bidding engine
    engine = BiddingEngine()

    # Get North's rebid
    bid, explanation = engine.get_next_bid(
        hand=north_hand,
        auction_history=auction_history,
        my_position='North',
        vulnerability='Both'
    )

    print("="*60)
    print(f"NORTH'S REBID: {bid}")
    print(f"Explanation: {explanation}")
    print("="*60)
    print()

    # Verify the bid
    if bid == '2♣':
        print("✅ TEST PASSED: North correctly rebids 2♣ to show the second 5-card suit!")
    elif bid == 'Pass':
        print("❌ TEST FAILED: North incorrectly passed (original bug)")
    else:
        print(f"⚠️  UNEXPECTED: North bid {bid} instead of 2♣")

    return bid == '2♣'

if __name__ == '__main__':
    success = test_north_rebid_with_5_5_minors()
    exit(0 if success else 1)
