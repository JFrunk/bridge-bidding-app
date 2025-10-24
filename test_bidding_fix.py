#!/usr/bin/env python3
"""
Test the bidding fix for hand_2025-10-24_05-34-51.json

This hand exposed a critical bug where West bid to 7NT with only 9 HCP.
"""

import sys
sys.path.insert(0, 'backend')

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_hand_from_cards(cards):
    """Create a Hand object from list of card dicts."""
    card_objects = [Card(rank=c['rank'], suit=c['suit']) for c in cards]
    return Hand(card_objects)

def test_problematic_auction():
    """Test the exact auction that caused the 7NT disaster."""

    # Create hands
    north_cards = [
        {"rank": "3", "suit": "♠"},
        {"rank": "K", "suit": "♥"}, {"rank": "J", "suit": "♥"}, {"rank": "9", "suit": "♥"},
        {"rank": "4", "suit": "♥"}, {"rank": "3", "suit": "♥"}, {"rank": "2", "suit": "♥"},
        {"rank": "9", "suit": "♦"}, {"rank": "8", "suit": "♦"}, {"rank": "7", "suit": "♦"},
        {"rank": "2", "suit": "♦"},
        {"rank": "8", "suit": "♣"}, {"rank": "3", "suit": "♣"}
    ]

    east_cards = [
        {"rank": "8", "suit": "♠"}, {"rank": "7", "suit": "♠"},
        {"rank": "Q", "suit": "♥"}, {"rank": "8", "suit": "♥"},
        {"rank": "A", "suit": "♦"}, {"rank": "K", "suit": "♦"}, {"rank": "5", "suit": "♦"},
        {"rank": "A", "suit": "♣"}, {"rank": "K", "suit": "♣"}, {"rank": "Q", "suit": "♣"},
        {"rank": "T", "suit": "♣"}, {"rank": "6", "suit": "♣"}, {"rank": "2", "suit": "♣"}
    ]

    south_cards = [
        {"rank": "Q", "suit": "♠"}, {"rank": "9", "suit": "♠"}, {"rank": "6", "suit": "♠"},
        {"rank": "4", "suit": "♠"},
        {"rank": "A", "suit": "♥"}, {"rank": "T", "suit": "♥"},
        {"rank": "Q", "suit": "♦"}, {"rank": "6", "suit": "♦"}, {"rank": "4", "suit": "♦"},
        {"rank": "3", "suit": "♦"},
        {"rank": "J", "suit": "♣"}, {"rank": "9", "suit": "♣"}, {"rank": "7", "suit": "♣"}
    ]

    west_cards = [
        {"rank": "A", "suit": "♠"}, {"rank": "K", "suit": "♠"}, {"rank": "J", "suit": "♠"},
        {"rank": "T", "suit": "♠"}, {"rank": "5", "suit": "♠"}, {"rank": "2", "suit": "♠"},
        {"rank": "7", "suit": "♥"}, {"rank": "6", "suit": "♥"}, {"rank": "5", "suit": "♥"},
        {"rank": "J", "suit": "♦"}, {"rank": "T", "suit": "♦"},
        {"rank": "5", "suit": "♣"}, {"rank": "4", "suit": "♣"}
    ]

    north_hand = create_hand_from_cards(north_cards)
    east_hand = create_hand_from_cards(east_cards)
    south_hand = create_hand_from_cards(south_cards)
    west_hand = create_hand_from_cards(west_cards)

    print("=" * 80)
    print("TESTING BIDDING FIX FOR 7NT DISASTER")
    print("=" * 80)
    print()
    print("Hand Analysis:")
    print(f"  North: {north_hand.hcp} HCP, {north_hand.total_points} total")
    print(f"  East:  {east_hand.hcp} HCP, {east_hand.total_points} total (opener)")
    print(f"  South: {south_hand.hcp} HCP, {south_hand.total_points} total")
    print(f"  West:  {west_hand.hcp} HCP, {west_hand.total_points} total (responder)")
    print(f"  E/W Combined: {east_hand.hcp + west_hand.hcp} HCP")
    print()
    print("Expected: E/W should stop at 4♣ or 5♣, NOT bid slam/grand slam")
    print()

    # Simulate the auction
    engine = BiddingEngine()
    auction_history = []
    dealer = "North"
    positions = ["North", "East", "South", "West"]
    hands = {
        "North": north_hand,
        "East": east_hand,
        "South": south_hand,
        "West": west_hand
    }

    # Start bidding
    dealer_index = positions.index(dealer)
    max_rounds = 20  # Prevent infinite loops
    consecutive_passes = 0

    print("-" * 80)
    print("BIDDING SEQUENCE:")
    print("-" * 80)

    for round_num in range(max_rounds):
        for i in range(4):
            current_position = positions[(dealer_index + len(auction_history)) % 4]
            current_hand = hands[current_position]

            # Get AI bid
            bid, explanation = engine.get_next_bid(
                current_hand,
                auction_history,
                current_position,
                "None"
            )

            auction_history.append(bid)
            print(f"{current_position:6s}: {bid:4s} - {explanation[:80]}")

            # Track consecutive passes
            if bid == "Pass":
                consecutive_passes += 1
            else:
                consecutive_passes = 0

            # Check if auction is over (3 consecutive passes after opening)
            if consecutive_passes >= 3 and len(auction_history) > 3:
                print()
                print("-" * 80)
                print("AUCTION COMPLETE")
                print("-" * 80)

                # Find final contract
                final_contract = None
                for bid in reversed(auction_history):
                    if bid not in ["Pass", "X", "XX"]:
                        final_contract = bid
                        break

                print(f"Final Contract: {final_contract if final_contract else 'PASSED OUT'}")
                print()

                # Analyze result
                if final_contract:
                    level = int(final_contract[0])
                    if level >= 6:
                        print("❌ FAILED: AI bid to slam level (6 or 7)!")
                        print(f"   With only {east_hand.hcp + west_hand.hcp} combined HCP and missing an ace,")
                        print("   slam is unreasonable.")
                        return False
                    elif level == 5:
                        print("⚠️  BORDERLINE: 5-level contract")
                        print(f"   With {east_hand.hcp + west_hand.hcp} HCP, 5-level is aggressive but possible.")
                        return True
                    elif level == 4:
                        print("✅ SUCCESS: Stopped at game level (4)")
                        print(f"   Appropriate for {east_hand.hcp + west_hand.hcp} combined HCP.")
                        return True
                    else:
                        print("✅ SUCCESS: Conservative bidding")
                        return True
                else:
                    print("✅ Auction passed out (no fit found)")
                    return True

    print()
    print("❌ FAILED: Auction did not end after 20 rounds (infinite loop detected)")
    return False

if __name__ == "__main__":
    success = test_problematic_auction()
    sys.exit(0 if success else 1)
