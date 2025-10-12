"""
Test for Negative Double rebid fix

Tests that opener correctly rebids after partner makes a forcing Negative Double.
Based on the bug found in hand_2025-10-10_14-37-19.json
"""

from engine.bidding_engine import BiddingEngine
from engine.hand import Hand, Card

def create_hand(cards_str):
    """Helper to create a hand from card string"""
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        ranks = part[1:]
        for rank in ranks:
            cards.append(Card(rank, suit))
    return Hand(cards)

def test_negative_double_rebid():
    """Test that East rebids 1♠ after West's Negative Double"""

    # East's hand from the problematic auction
    east_hand = create_hand("♠Q62 ♥AKT7 ♦75 ♣A873")

    # Auction: North Pass, East 1♣, South 1♦, West X (Negative Double)
    # Now East must rebid (not pass!)
    auction = ['Pass', '1♣', '1♦', 'X', 'Pass']

    engine = BiddingEngine()
    bid, explanation = engine.get_next_bid(east_hand, auction, 'East', 'Both')

    print(f"East's hand: {east_hand}")
    print(f"Auction: {auction}")
    print(f"East's rebid: {bid}")
    print(f"Explanation: {explanation}")

    # East should bid 1♠ (supporting partner's negative double showing spades)
    # NOT Pass!
    assert bid != 'Pass', f"ERROR: East passed after partner's forcing Negative Double!"
    assert bid == '1♠', f"ERROR: Expected 1♠, got {bid}"
    assert "spade" in explanation.lower() or "negative double" in explanation.lower(), \
        f"Explanation should mention supporting spades or negative double"

    print("\n✅ TEST PASSED: East correctly rebids 1♠ after partner's Negative Double")
    return True

if __name__ == "__main__":
    try:
        test_negative_double_rebid()
        print("\n🎉 Negative Double rebid fix verified!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
