"""
Manual test scenarios for end-to-end bidding validation.
Run these to verify bidding logic works with real-world hands.
"""

from engine.hand import Hand, Card

def print_hand(hand, player=""):
    """Pretty print a bridge hand."""
    print(f"\n{player} Hand:")
    for suit in ['♠', '♥', '♦', '♣']:
        cards_in_suit = [c.rank for c in hand.cards if c.suit == suit]
        print(f"  {suit} {' '.join(cards_in_suit)}")
    print(f"  HCP: {hand.hcp}, Total Points: {hand.total_points}")
    print(f"  Balanced: {hand.is_balanced}")

def scenario_1_jacoby_transfer():
    """
    Test Jacoby Transfer with super-accept.
    North: 17 HCP, 4 hearts (should super-accept)
    South: 8 HCP, 5 hearts (should transfer, then invite)
    """
    print("\n" + "="*60)
    print("SCENARIO 1: Jacoby Transfer with Super-Accept")
    print("="*60)

    # North: 17 HCP, balanced, 4 hearts
    north_cards = [
        Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
        Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'),
        Card('K', '♦'), Card('5', '♦'), Card('4', '♦'),
        Card('9', '♣'), Card('8', '♣'), Card('7', '♣')
    ]
    north = Hand(north_cards)
    print_hand(north, "North (Opener)")

    # South: 8 HCP, 5 hearts
    south_cards = [
        Card('5', '♠'), Card('4', '♠'), Card('3', '♠'),
        Card('T', '♥'), Card('9', '♥'), Card('8', '♥'), Card('7', '♥'), Card('6', '♥'),
        Card('A', '♦'), Card('6', '♦'),
        Card('6', '♣'), Card('5', '♣'), Card('4', '♣')
    ]
    south = Hand(south_cards)
    print_hand(south, "South (Responder)")

    print("\nExpected Auction:")
    print("  North: 1NT (15-17 HCP, balanced)")
    print("  South: 2♦ (Jacoby Transfer to hearts)")
    print("  North: 3♥ (Super-accept with 17 HCP and 4 hearts)")
    print("  South: 4♥ (Game bid with 8+ HCP after super-accept)")

    return north, south

def scenario_2_reverse_bid():
    """
    Test reverse bid logic.
    North: 17 HCP, 5 clubs, 4 diamonds (should reverse to 2♦ after 1♠ response)
    South: 8 HCP, 4 spades
    """
    print("\n" + "="*60)
    print("SCENARIO 2: Reverse Bid (17+ HCP)")
    print("="*60)

    # North: 17 HCP, 5 clubs, 4 diamonds
    north_cards = [
        Card('K', '♠'), Card('5', '♠'),
        Card('A', '♥'), Card('K', '♥'), Card('4', '♥'),
        Card('A', '♦'), Card('K', '♦'), Card('Q', '♦'), Card('5', '♦'),
        Card('A', '♣'), Card('K', '♣'), Card('9', '♣'), Card('8', '♣')
    ]
    north = Hand(north_cards)
    print_hand(north, "North (Opener)")

    # South: 8 HCP, 4 spades
    south_cards = [
        Card('A', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'),
        Card('6', '♥'), Card('5', '♥'), Card('3', '♥'),
        Card('7', '♦'), Card('6', '♦'),
        Card('6', '♣'), Card('5', '♣'), Card('4', '♣'), Card('3', '♣')
    ]
    south = Hand(south_cards)
    print_hand(south, "South (Responder)")

    print("\nExpected Auction:")
    print("  North: 1♣ (5+ clubs)")
    print("  South: 1♠ (4+ spades)")
    print("  North: 2♦ (REVERSE - shows 17+ HCP, forcing)")

    return north, south

def scenario_3_weak_jump_overcall():
    """
    Test weak jump overcall.
    North: 13 HCP, opens 1♥
    East: 8 HCP, 6 spades (should make weak jump overcall to 2♠)
    """
    print("\n" + "="*60)
    print("SCENARIO 3: Weak Jump Overcall")
    print("="*60)

    # North: 13 HCP, 5 hearts
    north_cards = [
        Card('K', '♠'), Card('5', '♠'), Card('4', '♠'),
        Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'), Card('5', '♥'),
        Card('9', '♦'), Card('8', '♦'), Card('7', '♦'),
        Card('K', '♣'), Card('5', '♣')
    ]
    north = Hand(north_cards)
    print_hand(north, "North (Opener)")

    # East: 8 HCP, 6 spades (weak jump overcall)
    east_cards = [
        Card('A', '♠'), Card('K', '♠'), Card('J', '♠'), Card('T', '♠'), Card('9', '♠'), Card('8', '♠'),
        Card('5', '♥'), Card('4', '♥'),
        Card('6', '♦'), Card('5', '♦'), Card('4', '♦'),
        Card('7', '♣'), Card('6', '♣')
    ]
    east = Hand(east_cards)
    print_hand(east, "East (Overcaller)")

    print("\nExpected Auction:")
    print("  North: 1♥ (5+ hearts)")
    print("  East: 2♠ (Weak jump overcall - 6-10 HCP, 6 spades, preemptive)")

    return north, east

def scenario_4_advancer_cuebid():
    """
    Test advancer cuebid (game-forcing).
    North: 13 HCP, opens 1♥
    East: 11 HCP, overcalls 1♠
    West: 12 HCP, 3 spades (should cuebid 2♥)
    """
    print("\n" + "="*60)
    print("SCENARIO 4: Advancer Cuebid (Game-Forcing)")
    print("="*60)

    # East: 11 HCP, 5 spades (overcaller)
    east_cards = [
        Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('5', '♠'),
        Card('6', '♥'), Card('5', '♥'),
        Card('K', '♦'), Card('7', '♦'), Card('6', '♦'),
        Card('8', '♣'), Card('7', '♣'), Card('6', '♣')
    ]
    east = Hand(east_cards)
    print_hand(east, "East (Overcaller)")

    # West: 12 HCP, 3 spades (advancer)
    west_cards = [
        Card('T', '♠'), Card('9', '♠'), Card('8', '♠'),
        Card('A', '♥'), Card('K', '♥'), Card('7', '♥'),
        Card('A', '♦'), Card('Q', '♦'), Card('5', '♦'),
        Card('9', '♣'), Card('8', '♣'), Card('7', '♣'), Card('6', '♣')
    ]
    west = Hand(west_cards)
    print_hand(west, "West (Advancer)")

    print("\nExpected Auction:")
    print("  North: 1♥")
    print("  East: 1♠ (overcall)")
    print("  South: Pass")
    print("  West: 2♥ (Cuebid - game-forcing, showing 12+ pts and fit)")

    return east, west

def run_all_scenarios():
    """Run all manual test scenarios."""
    print("\n" + "#"*60)
    print("#  MANUAL BIDDING TEST SCENARIOS")
    print("#  Phase 1 & Phase 2 Validation")
    print("#"*60)

    scenario_1_jacoby_transfer()
    scenario_2_reverse_bid()
    scenario_3_weak_jump_overcall()
    scenario_4_advancer_cuebid()

    print("\n" + "="*60)
    print("SCENARIOS COMPLETE")
    print("="*60)
    print("\nTo test these scenarios live:")
    print("1. Use these exact hands in your bridge app")
    print("2. Verify the AI makes the expected bids")
    print("3. Check bid explanations match SAYC standards")
    print("\nAll scenarios test Phase 1 & Phase 2 fixes.")

if __name__ == '__main__':
    run_all_scenarios()
