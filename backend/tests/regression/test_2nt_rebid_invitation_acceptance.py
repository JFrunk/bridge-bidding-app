"""
Regression test for opener accepting invitations after 2NT rebid.

After auction 1♦ - P - 1♥ - P - 2NT - P - 3NT
Opener should pass (partner accepted and bid game).

After auction 1♥ - P - 1♠ - P - 2NT - P - 3♥
Opener with 19 HCP (maximum of 18-19) should bid 4♥.

This test ensures opener correctly evaluates follow-up bids after 2NT rebid.

Date: 2025-10-29
Related to: 1NT rebid invitation acceptance fix
"""

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


def test_pass_after_partner_bids_3nt():
    """
    Test that opener passes when partner bids 3NT after 2NT rebid.

    Auction: 1♦ - P - 1♥ - P - 2NT - P - 3NT - P
    North: 18 HCP (minimum), balanced

    Expected: North passes (partner accepted and bid game)
    """

    # Create North's hand (opener) - 18 HCP
    north_cards = [
        Card('A', '♠'), Card('Q', '♠'), Card('5', '♠'),  # 3 spades (6 HCP)
        Card('K', '♥'), Card('J', '♥'), Card('4', '♥'),  # 3 hearts (4 HCP)
        Card('A', '♦'), Card('K', '♦'), Card('7', '♦'), Card('3', '♦'),  # 4 diamonds (7 HCP)
        Card('K', '♣'), Card('8', '♣'), Card('2', '♣')   # 3 clubs (3 HCP)
    ]
    north_hand = Hand(north_cards)

    print(f"North's hand (opener): {north_hand}")
    print(f"  HCP: {north_hand.hcp}, Total Points: {north_hand.total_points}")
    print(f"  Balanced: {north_hand.is_balanced}")
    print()

    # Create the auction history
    auction_history = [
        '1♦',   # North opens
        'Pass', # East passes
        '1♥',   # South responds
        'Pass', # West passes
        '2NT',  # North rebids 2NT (18-19 HCP, balanced)
        'Pass', # East passes
        '3NT',  # South bids 3NT (accepting, going to game)
        'Pass'  # West passes
    ]

    print("Auction:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Create bidding engine
    engine = BiddingEngine()

    # Get North's bid
    bid, explanation = engine.get_next_bid(
        hand=north_hand,
        auction_history=auction_history,
        my_position='North',
        vulnerability='None'
    )

    print("="*70)
    print(f"NORTH'S BID: {bid}")
    print(f"Explanation: {explanation}")
    print("="*70)
    print()

    # Verify the bid
    if bid == 'Pass':
        print("✅ TEST PASSED: North correctly passes (partner bid game)!")
        return True
    else:
        print(f"❌ TEST FAILED: North bid {bid} instead of Pass")
        return False


def test_accept_3level_major_with_maximum():
    """
    Test that opener accepts 3-level major invitation with maximum HCP.

    Auction: 1♥ - P - 1♠ - P - 2NT - P - 3♥ - P
    North: 19 HCP (maximum of 18-19), 5 hearts

    Expected: North bids 4♥ (accepting invitation with maximum)
    """

    # Create North's hand (opener) - 19 HCP, 5 hearts
    north_cards = [
        Card('A', '♠'), Card('K', '♠'), Card('5', '♠'),  # 3 spades (7 HCP)
        Card('A', '♥'), Card('K', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'),  # 5 hearts (8 HCP)
        Card('K', '♦'), Card('7', '♦'), Card('3', '♦'),  # 3 diamonds (3 HCP)
        Card('Q', '♣'), Card('2', '♣')   # 2 clubs (2 HCP)
    ]
    north_hand = Hand(north_cards)

    print(f"North's hand (opener): {north_hand}")
    print(f"  HCP: {north_hand.hcp}, Total Points: {north_hand.total_points}")
    print(f"  Distribution: ♠{north_hand.suit_lengths['♠']} ♥{north_hand.suit_lengths['♥']} ♦{north_hand.suit_lengths['♦']} ♣{north_hand.suit_lengths['♣']}")
    print()

    # Create the auction history
    auction_history = [
        '1♥',   # North opens
        'Pass', # East passes
        '1♠',   # South responds
        'Pass', # West passes
        '2NT',  # North rebids 2NT (18-19 HCP, balanced)
        'Pass', # East passes
        '3♥',   # South shows heart preference (3-card support)
        'Pass'  # West passes
    ]

    print("Auction:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Create bidding engine
    engine = BiddingEngine()

    # Get North's bid
    bid, explanation = engine.get_next_bid(
        hand=north_hand,
        auction_history=auction_history,
        my_position='North',
        vulnerability='None'
    )

    print("="*70)
    print(f"NORTH'S BID: {bid}")
    print(f"Explanation: {explanation}")
    print("="*70)
    print()

    # Verify the bid
    if bid == '4♥':
        print("✅ TEST PASSED: North correctly bids 4♥ (accepting with maximum 19 HCP)!")
        return True
    elif bid == 'Pass':
        print("❌ TEST FAILED: North passed (should accept with maximum)")
        return False
    else:
        print(f"⚠️  UNEXPECTED: North bid {bid} instead of 4♥")
        return False


def test_decline_3level_with_minimum():
    """
    Test that opener declines 3-level invitation with minimum HCP.

    Auction: 1♠ - P - 2♣ - P - 2NT - P - 3♠ - P
    North: 18 HCP (minimum of 18-19)

    Expected: North passes (declining with minimum)
    """

    # Create North's hand (opener) - 18 HCP, 5 spades
    north_cards = [
        Card('A', '♠'), Card('K', '♠'), Card('J', '♠'), Card('T', '♠'), Card('5', '♠'),  # 5 spades (8 HCP)
        Card('Q', '♥'), Card('J', '♥'), Card('4', '♥'),  # 3 hearts (3 HCP)
        Card('A', '♦'), Card('7', '♦'), Card('3', '♦'),  # 3 diamonds (4 HCP)
        Card('K', '♣'), Card('2', '♣')   # 2 clubs (3 HCP)
    ]
    north_hand = Hand(north_cards)

    print(f"North's hand (opener): {north_hand}")
    print(f"  HCP: {north_hand.hcp}, Total Points: {north_hand.total_points}")
    print()

    # Create the auction history
    auction_history = [
        '1♠',   # North opens
        'Pass', # East passes
        '2♣',   # South responds (forcing)
        'Pass', # West passes
        '2NT',  # North rebids 2NT (18-19 HCP, balanced)
        'Pass', # East passes
        '3♠',   # South shows spade preference
        'Pass'  # West passes
    ]

    print("Auction:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Create bidding engine
    engine = BiddingEngine()

    # Get North's bid
    bid, explanation = engine.get_next_bid(
        hand=north_hand,
        auction_history=auction_history,
        my_position='North',
        vulnerability='None'
    )

    print("="*70)
    print(f"NORTH'S BID: {bid}")
    print(f"Explanation: {explanation}")
    print("="*70)
    print()

    # Verify the bid
    if bid == 'Pass':
        print("✅ TEST PASSED: North correctly passes (declining with minimum 18 HCP)!")
        return True
    elif bid == '4♠':
        print("❌ TEST FAILED: North bid 4♠ (should decline with minimum)")
        return False
    else:
        print(f"⚠️  UNEXPECTED: North bid {bid}")
        return False


if __name__ == '__main__':
    print("\n" + "="*70)
    print("TEST 1: Pass after partner bids 3NT")
    print("="*70 + "\n")
    test1 = test_pass_after_partner_bids_3nt()

    print("\n" + "="*70)
    print("TEST 2: Accept 3-level major with maximum (19 HCP)")
    print("="*70 + "\n")
    test2 = test_accept_3level_major_with_maximum()

    print("\n" + "="*70)
    print("TEST 3: Decline 3-level invitation with minimum (18 HCP)")
    print("="*70 + "\n")
    test3 = test_decline_3level_with_minimum()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Test 1 (Pass after 3NT): {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (Accept with maximum): {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Test 3 (Decline with minimum): {'✅ PASSED' if test3 else '❌ FAILED'}")

    all_passed = test1 and test2 and test3
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    exit(0 if all_passed else 1)
