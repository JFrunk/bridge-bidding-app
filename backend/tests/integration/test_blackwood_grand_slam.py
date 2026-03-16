"""
Test for RKCB 1430 slam bidding.

Tests signoff decisions after receiving RKCB keycard responses.
RKCB 1430 responses:
  5♣ = 1 or 4 keycards
  5♦ = 0 or 3 keycards
  5♥ = 2 keycards WITHOUT trump queen
  5♠ = 2 keycards WITH trump queen
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
    """Test that opener bids slam when all keycards are confirmed via RKCB.

    North: ♠A5 ♥AQ864 ♦AKJ4 ♣Q7 (20 HCP, keycards: ♠A + ♥A + ♦A = 3, no ♥K)
    Trump: ♥. North's keycards = 3 (3 aces, no trump king ♥K).
    South responds 5♠ (2 keycards WITH trump queen) → total = 5 keycards.
    North should bid slam (6♥ or 7♥).
    """
    engine = BiddingEngine()
    north_hand = create_hand("♠A5 ♥AQ864 ♦AKJ4 ♣Q7")

    # South's RKCB response: 5♠ = 2 keycards with queen (e.g., ♥K + ♣A + ♥Q)
    auction = ['1♥', 'Pass', '4♥', 'Pass', '4NT', 'Pass', '5♠', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    print(f"\nTest: RKCB Slam with 5 keycards")
    print(f"North hand: ♠A5 ♥AQ864 ♦AKJ4 ♣Q7 (20 HCP, 3 keycards)")
    print(f"South's response: 5♠ (2 keycards WITH queen)")
    print(f"North's bid: {bid} — {explanation}")

    assert bid in ['6♥', '7♥'], f"Expected slam bid (6♥ or 7♥) with 5 keycards, got {bid}"
    print(f"✅ Test passed: North correctly bid slam!")

def test_blackwood_small_slam_3_aces():
    """Test that opener bids small slam when missing 1 keycard.

    North: ♠A5 ♥AQ864 ♦KQJ4 ♣Q7 (19 HCP, keycards: ♠A + ♥A = 2, no ♥K)
    Trump: ♥. North's keycards = 2 (2 aces, no trump king).
    South responds 5♣ (1 or 4 keycards) → with my 2, partner likely has 1 → total 3, missing 2.
    South responds 5♥ (2 keycards no queen) → total 4, missing 1 → small slam.
    """
    engine = BiddingEngine()
    north_hand = create_hand("♠A5 ♥AQ864 ♦KQJ4 ♣Q7")

    # South's RKCB response: 5♥ = 2 keycards without queen → total 4, missing 1
    auction = ['1♥', 'Pass', '4♥', 'Pass', '4NT', 'Pass', '5♥', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    print(f"\nTest: RKCB Small Slam (missing 1 keycard)")
    print(f"North hand: ♠A5 ♥AQ864 ♦KQJ4 ♣Q7 (19 HCP, 2 keycards)")
    print(f"South's response: 5♥ (2 keycards, no queen)")
    print(f"North's bid: {bid} — {explanation}")

    assert bid == '6♥', f"Expected 6♥ (small slam, missing 1 keycard), got {bid}"
    print(f"✅ Test passed: North correctly bid small slam!")

def test_blackwood_signoff_2_aces():
    """Test that opener signs off at 5-level when missing 2+ keycards.

    North: ♠K5 ♥KQ864 ♦AQJ4 ♣Q7 (16 HCP)
    Trump: ♥. North's keycards = 1 (♦A only; ♥K is trump king = 2 total).
    Actually: ♠K, ♥K (trump king!), ♥Q, ♦A, ♦Q, ♦J, ♣Q = keycards = ♦A + ♥K = 2.
    South responds 5♦ (0 or 3 keycards) → with my 2, partner could have 0 or 3.
    If partner has 0 → total 2, missing 3 → signoff.
    """
    engine = BiddingEngine()
    north_hand = create_hand("♠K5 ♥KQ864 ♦AQJ4 ♣Q7")

    # South's RKCB response: 5♦ = 0 or 3 keycards
    # North has 2 keycards (♦A + ♥K); if partner has 3, total = 5 (all present)
    # If partner has 0, total = 2 (missing 3)
    # Resolve: 2 + 3 = 5 ≤ 5, so partner could have 3; 2 + 0 = 2, could have 0
    # Default to lower for safety → 0, total = 2, missing 3 → signoff
    auction = ['1♥', 'Pass', '4♥', 'Pass', '4NT', 'Pass', '5♦', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    print(f"\nTest: RKCB Signoff (missing keycards)")
    print(f"North hand: ♠K5 ♥KQ864 ♦AQJ4 ♣Q7 (16 HCP, 2 keycards)")
    print(f"South's response: 5♦ (0 or 3 keycards)")
    print(f"North's bid: {bid} — {explanation}")

    assert bid == '5♥', f"Expected 5♥ (signoff, missing keycards), got {bid}"
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
