#!/usr/bin/env python3
"""
Test that responder cannot pass in a 2♣ auction after making an artificial 2♦ response.
This tests the fix for the bug where North passed at 2♠ after the sequence:
North: Pass, East: Pass, South: 2♣, West: Pass, North: 2♦, East: Pass, South: 2♠, West: Pass, North: Pass (BUG!)
"""

import sys
sys.path.append('/Users/simonroy/Desktop/bridge_bidding_app/backend')

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_hand(cards_str):
    """Create a Hand object from a string of cards."""
    cards = []
    for card_str in cards_str.split():
        rank = card_str[0]
        suit = card_str[1]
        cards.append(Card(rank=rank, suit=suit))
    return Hand(cards)

def test_2club_forcing_to_game():
    """Test the exact hand from the review request."""
    print("=" * 80)
    print("Testing 2♣ forcing-to-game auction")
    print("=" * 80)

    # Create hands from the review request
    # North: 7 HCP, 5-4-4-2 (♠52 ♥98 ♦QT92 ♣A9532)
    north_cards = "5♠ 2♠ 9♥ 8♥ Q♦ T♦ 9♦ 2♦ A♣ 9♣ 5♣ 3♣ 2♣"
    north = create_hand(north_cards)

    # East: 9 HCP, 5-4-4-0 (♥QJ65 ♦K654 ♣QJ864)
    east_cards = "Q♥ J♥ 6♥ 5♥ K♦ 6♦ 5♦ 4♦ Q♣ J♣ 8♣ 6♣ 4♣"
    east = create_hand(east_cards)

    # South: 21 HCP, 6-4-2-1 (♠AKT863 ♥AK43 ♦A3 ♣K)
    south_cards = "A♠ K♠ T♠ 8♠ 6♠ 3♠ A♥ K♥ 4♥ 3♥ A♦ 3♦ K♣"
    south = create_hand(south_cards)

    # West: 4 HCP, 5-2-3-3 (♠QJ974 ♥T7 ♦J87 ♣T72) - adjusted to 13 cards
    west_cards = "Q♠ J♠ 9♠ 7♠ 4♠ T♥ 7♥ J♦ 8♦ 7♦ T♣ 7♣ 2♣"
    west = create_hand(west_cards)

    hands = [north, east, south, west]

    # Simulate the auction
    engine = BiddingEngine()
    dealer = 0  # North is dealer
    vulnerability = "EW"  # East-West vulnerable

    print(f"\nNorth (Dealer): {north.hcp} HCP, {north.total_points} total points")
    print(f"East: {east.hcp} HCP, {east.total_points} total points")
    print(f"South: {south.hcp} HCP, {south.total_points} total points")
    print(f"West: {west.hcp} HCP, {west.total_points} total points")
    print()

    # Start the auction
    auction = []
    current_player = dealer
    passes = 0
    position_names = ['North', 'East', 'South', 'West']

    print("Auction:")
    print("-" * 80)

    for round_num in range(20):  # Max 20 bids to prevent infinite loop
        hand = hands[current_player]
        my_position = position_names[current_player]

        bid, explanation = engine.get_next_bid(hand, auction, my_position, vulnerability)

        print(f"{my_position:5s}: {bid:4s} - {explanation}")

        auction.append(bid)

        if bid == "Pass":
            passes += 1
            if passes >= 3 and len(auction) >= 4:
                # Three passes in a row after at least one non-pass bid
                print("\nAuction complete!")
                break
        else:
            passes = 0

        current_player = (current_player + 1) % 4

    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("=" * 80)

    # Check if North passed at the wrong time
    # The sequence should be: Pass, Pass, 2♣, Pass, 2♦, Pass, 2♠, Pass, ???
    if len(auction) >= 9:
        if (auction[0] == "Pass" and auction[1] == "Pass" and
            auction[2] == "2♣" and auction[3] == "Pass" and
            auction[4] == "2♦" and auction[5] == "Pass" and
            auction[6] == "2♠" and auction[7] == "Pass"):

            north_rebid = auction[8]
            print(f"\nAfter 2♣ - 2♦ - 2♠, North's rebid: {north_rebid}")

            if north_rebid == "Pass":
                print("❌ FAIL: North passed in a forcing-to-game auction!")
                print("   North must bid until game is reached after responding 2♦ to 2♣.")
                return False
            else:
                print(f"✓ PASS: North correctly bid {north_rebid} instead of passing.")
                print("   The auction is forcing to game after 2♣ - 2♦.")

                # Check if auction reached game
                game_bids = ["3NT", "4♠", "4♥", "5♣", "5♦", "6♣", "6♦", "6♥", "6♠", "6NT", "7♣", "7♦", "7♥", "7♠", "7NT"]
                reached_game = any(bid in game_bids for bid in auction)

                if reached_game:
                    print(f"✓ Auction correctly reached game level.")
                else:
                    print(f"⚠ Warning: Auction did not reach game (may need further investigation).")

                return True

    print("\n❌ FAIL: Auction did not follow expected sequence")
    return False

if __name__ == "__main__":
    success = test_2club_forcing_to_game()
    sys.exit(0 if success else 1)
