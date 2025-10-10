"""
Test for Blackwood grand slam bidding bug fix.

Tests the scenario from hand_2025-10-10_10-05-49.json where:
- North opens 1♥ with 19 HCP and 3 aces
- South responds 4♥ with 13 HCP and 1 ace
- North asks 4NT (Blackwood)
- South responds 5♦ (1 ace)
- North should bid 7♥ (grand slam with all 4 aces)
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

def test_blackwood_grand_slam_all_aces():
    """Test that opener bids grand slam when all 4 aces are confirmed."""
    engine = BiddingEngine()

    # North: 20 HCP, 5 hearts, 3 aces (♠A, ♥A, ♦A)
    north_hand = create_hand("♠A5 ♥AQ864 ♦AKJ4 ♣Q7")

    # Auction: North opened 1♥, South jumped to 4♥, North asked 4NT, South responded 5♦ (1 ace)
    auction = ['1♥', 'Pass', '4♥', 'Pass', '4NT', 'Pass', '5♦', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    print(f"\nTest: Blackwood Grand Slam with All Aces")
    print(f"North hand: ♠A5 ♥AQ864 ♦AKJ4 ♣Q7 (20 HCP, 3 aces)")
    print(f"Auction: {' - '.join(auction)}")
    print(f"North's aces: 3")
    print(f"Partner's aces (from 5♦): 1")
    print(f"Total aces: 4")
    print(f"\nNorth's bid: {bid}")
    print(f"Explanation: {explanation}")

    assert bid == '7♥', f"Expected 7♥ (grand slam with 4 aces), got {bid}"
    print(f"✅ Test passed: North correctly bid grand slam!")

def test_blackwood_small_slam_3_aces():
    """Test that opener bids small slam with 3 aces."""
    engine = BiddingEngine()

    # North: 18 HCP, 5 hearts, 2 aces (♠A, ♥A)
    north_hand = create_hand("♠A5 ♥AQ864 ♦KQJ4 ♣Q7")

    # Auction: North opened 1♥, South jumped to 4♥, North asked 4NT, South responded 5♦ (1 ace)
    auction = ['1♥', 'Pass', '4♥', 'Pass', '4NT', 'Pass', '5♦', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    print(f"\nTest: Blackwood Small Slam with 3 Aces")
    print(f"North hand: ♠A5 ♥AQ864 ♦KQJ4 ♣Q7 (19 HCP, 2 aces)")
    print(f"Auction: {' - '.join(auction)}")
    print(f"North's aces: 2")
    print(f"Partner's aces (from 5♦): 1")
    print(f"Total aces: 3")
    print(f"\nNorth's bid: {bid}")
    print(f"Explanation: {explanation}")

    assert bid == '6♥', f"Expected 6♥ (small slam with 3 aces), got {bid}"
    print(f"✅ Test passed: North correctly bid small slam!")

def test_blackwood_signoff_2_aces():
    """Test that opener signs off at 5-level with 2 aces."""
    engine = BiddingEngine()

    # North: 16 HCP, 5 hearts, 1 ace
    north_hand = create_hand("♠K5 ♥AQ864 ♦KQJ4 ♣Q7")

    # Auction: North opened 1♥, South jumped to 4♥, North asked 4NT, South responded 5♦ (1 ace)
    # But let's change North to have only 1 ace
    north_hand = create_hand("♠K5 ♥KQ864 ♦AQJ4 ♣Q7")

    auction = ['1♥', 'Pass', '4♥', 'Pass', '4NT', 'Pass', '5♦', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    print(f"\nTest: Blackwood Signoff with 2 Aces")
    print(f"North hand: ♠K5 ♥KQ864 ♦AQJ4 ♣Q7 (16 HCP, 1 ace)")
    print(f"Auction: {' - '.join(auction)}")
    print(f"North's aces: 1")
    print(f"Partner's aces (from 5♦): 1")
    print(f"Total aces: 2")
    print(f"\nNorth's bid: {bid}")
    print(f"Explanation: {explanation}")

    assert bid == '5♥', f"Expected 5♥ (signoff with 2 aces), got {bid}"
    print(f"✅ Test passed: North correctly signed off at 5-level!")

if __name__ == '__main__':
    print("=" * 70)
    print("BLACKWOOD GRAND SLAM BUG FIX - TEST SUITE")
    print("=" * 70)

    try:
        test_blackwood_grand_slam_all_aces()
        test_blackwood_small_slam_3_aces()
        test_blackwood_signoff_2_aces()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED! ✅")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import sys
        sys.exit(1)
