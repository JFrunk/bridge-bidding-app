"""
Integration test for takeout double fix.
Tests the full bidding engine with the problematic hand scenario.
"""

import sys
sys.path.insert(0, '/Users/simonroy/Desktop/bridge_bidding_app/backend')

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_hand_from_cards_dict(cards_list):
    """Helper to create Hand from dictionary of cards."""
    return Hand([Card(c['rank'], c['suit']) for c in cards_list])

def test_full_auction_with_east_hand():
    """
    Test the full auction from hand_2025-10-11_14-28-29.json
    Auction should be: Pass - Pass - 1♦ - Pass - 1♥ - Pass (NOT X)
    """

    # Create all four hands
    north_cards = [
        {'rank': 'A', 'suit': '♠'}, {'rank': '4', 'suit': '♠'}, {'rank': '3', 'suit': '♠'},
        {'rank': 'Q', 'suit': '♥'}, {'rank': 'J', 'suit': '♥'}, {'rank': '7', 'suit': '♥'}, {'rank': '6', 'suit': '♥'},
        {'rank': '4', 'suit': '♦'}, {'rank': '2', 'suit': '♦'},
        {'rank': 'K', 'suit': '♣'}, {'rank': 'T', 'suit': '♣'}, {'rank': '7', 'suit': '♣'}, {'rank': '4', 'suit': '♣'}
    ]

    east_cards = [
        {'rank': 'K', 'suit': '♠'}, {'rank': 'Q', 'suit': '♠'}, {'rank': '9', 'suit': '♠'}, {'rank': '7', 'suit': '♠'},
        {'rank': 'A', 'suit': '♥'}, {'rank': 'T', 'suit': '♥'}, {'rank': '4', 'suit': '♥'}, {'rank': '2', 'suit': '♥'},
        {'rank': 'Q', 'suit': '♦'}, {'rank': 'J', 'suit': '♦'},
        {'rank': '8', 'suit': '♣'}, {'rank': '3', 'suit': '♣'}, {'rank': '2', 'suit': '♣'}
    ]

    south_cards = [
        {'rank': 'T', 'suit': '♠'}, {'rank': '6', 'suit': '♠'}, {'rank': '5', 'suit': '♠'},
        {'rank': '9', 'suit': '♥'}, {'rank': '3', 'suit': '♥'},
        {'rank': 'A', 'suit': '♦'}, {'rank': 'K', 'suit': '♦'}, {'rank': '9', 'suit': '♦'}, {'rank': '5', 'suit': '♦'}, {'rank': '3', 'suit': '♦'},
        {'rank': 'A', 'suit': '♣'}, {'rank': 'Q', 'suit': '♣'}, {'rank': '9', 'suit': '♣'}
    ]

    west_cards = [
        {'rank': 'J', 'suit': '♠'}, {'rank': '8', 'suit': '♠'}, {'rank': '2', 'suit': '♠'},
        {'rank': 'K', 'suit': '♥'}, {'rank': '8', 'suit': '♥'}, {'rank': '5', 'suit': '♥'},
        {'rank': 'T', 'suit': '♦'}, {'rank': '8', 'suit': '♦'}, {'rank': '7', 'suit': '♦'}, {'rank': '6', 'suit': '♦'},
        {'rank': 'J', 'suit': '♣'}, {'rank': '6', 'suit': '♣'}, {'rank': '5', 'suit': '♣'}
    ]

    hands = {
        'N': create_hand_from_cards_dict(north_cards),
        'E': create_hand_from_cards_dict(east_cards),
        'S': create_hand_from_cards_dict(south_cards),
        'W': create_hand_from_cards_dict(west_cards)
    }

    # Initialize bidding engine
    engine = BiddingEngine()
    vulnerability = 'EW'

    print("=" * 70)
    print("INTEGRATION TEST: Full Auction")
    print("=" * 70)
    print("\nHands:")
    print(f"North (10 HCP): ♠A43 ♥QJ76 ♦42 ♣KT74")
    print(f"East  (12 HCP): ♠KQ97 ♥AT42 ♦QJ ♣832  ← 4 hearts!")
    print(f"South (13 HCP): ♠T65 ♥93 ♦AK953 ♣AQ9")
    print(f"West  (5 HCP):  ♠J82 ♥K85 ♦T876 ♣J65")
    print("\nDealer: North | Vulnerability: EW")
    print("\nExpected Auction: Pass - Pass - 1♦ - Pass - 1♥ - Pass")
    print("                                              ↑ NOT X!")
    print("\nActual Auction:")

    # Simulate the auction
    positions = ['North', 'East', 'South', 'West']
    position_abbr = ['N', 'E', 'S', 'W']
    auction_history = []
    bids_and_explanations = []

    for i in range(10):  # Max 10 bids
        position = positions[i % 4]
        abbr = position_abbr[i % 4]
        hand = hands[abbr]

        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=auction_history,
            my_position=position,
            vulnerability=vulnerability
        )

        bids_and_explanations.append((position, bid, explanation))
        auction_history.append(bid)
        print(f"  {position}: {bid}")

        # Check if auction is over (3 passes after a bid, or 4 passes to start)
        if len(auction_history) >= 4:
            if auction_history[-3:] == ['Pass', 'Pass', 'Pass']:
                break
            if len(auction_history) == 4 and all(b == 'Pass' for b in auction_history):
                break

    print("\n" + "=" * 70)

    # Check if East made a takeout double
    east_bids = [bid for pos, bid, _ in bids_and_explanations if pos == 'East']

    if 'X' in east_bids:
        print("❌ FAILED: East made a takeout double!")
        print("   East has 4 hearts and should NOT double 1♥")
        print(f"\n   East's actual bids: {east_bids}")
        return False
    else:
        print("✅ PASSED: East did NOT make a takeout double")
        print("   Correct - East has 4 hearts and cannot double 1♥")
        print(f"\n   East's actual bids: {east_bids}")
        return True

if __name__ == "__main__":
    success = test_full_auction_with_east_hand()
    print("=" * 70)
    sys.exit(0 if success else 1)
