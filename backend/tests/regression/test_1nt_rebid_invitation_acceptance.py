"""
Regression test for opener accepting invitations after 1NT rebid.

Bug: After auction 1♥ - P - 1♠ - P - 1NT - P - 2♦ - P
North (opener) passed with 13 HCP (maximum of 12-14 range).
Should have bid 3NT to accept partner's invitational 2♦ bid.

This test ensures opener correctly evaluates invitational bids after 1NT rebid
and accepts with maximum values (13-14 HCP).

Date: 2025-10-29
User Concern: "With game points it should have gone to 3NT at least."
"""

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


def test_accept_invitation_after_1nt_rebid_maximum():
    """
    Test that opener accepts invitation after 1NT rebid with maximum HCP.

    Auction: 1♥ - P - 1♠ - P - 1NT - P - 2♦ - P
    North: 13 HCP (maximum), 5♥-3♣-3♦-2♠
    South: 14 HCP, 5♦-4♠-2♥-2♣

    Expected: North bids 3NT (accepting invitation with maximum 13 HCP)
    """

    # Create North's hand (opener)
    north_cards = [
        Card('5', '♠'), Card('4', '♠'),  # 2 spades
        Card('A', '♥'), Card('K', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'),  # 5 hearts
        Card('K', '♦'), Card('7', '♦'), Card('4', '♦'),  # 3 diamonds
        Card('Q', '♣'), Card('T', '♣'), Card('3', '♣')   # 3 clubs
    ]
    north_hand = Hand(north_cards)

    print(f"North's hand (opener): {north_hand}")
    print(f"  HCP: {north_hand.hcp}, Total Points: {north_hand.total_points}")
    print(f"  Distribution: ♠{north_hand.suit_lengths['♠']} ♥{north_hand.suit_lengths['♥']} ♦{north_hand.suit_lengths['♦']} ♣{north_hand.suit_lengths['♣']}")
    print(f"  Balanced: {north_hand.is_balanced}")
    print()

    # Create the auction history
    auction_history = [
        '1♥',   # North opens
        'Pass', # East passes
        '1♠',   # South responds (partner)
        'Pass', # West passes
        '1NT',  # North rebids 1NT (12-14 HCP, balanced, no spade fit)
        'Pass', # East passes
        '2♦',   # South bids 2♦ (invitational, 5+ diamonds)
        'Pass'  # West passes
    ]

    print("Auction:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Create bidding engine
    engine = BiddingEngine()

    # Get North's second rebid
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
    if bid == '3NT':
        print("✅ TEST PASSED: North correctly bids 3NT (accepting invitation with maximum 13 HCP)!")
        return True
    elif bid == 'Pass':
        print("❌ TEST FAILED: North incorrectly passed (original bug - missing game)")
        print("   Combined HCP: 27 (13 + 14) → Should reach 3NT")
        return False
    else:
        print(f"⚠️  UNEXPECTED: North bid {bid} instead of 3NT")
        return False


def test_decline_invitation_after_1nt_rebid_minimum():
    """
    Test that opener declines invitation after 1NT rebid with minimum HCP.

    Auction: 1♥ - P - 1♠ - P - 1NT - P - 2♦ - P
    North: 12 HCP (minimum), 5♥-3♣-3♦-2♠
    South: Invitational 2♦ bid

    Expected: North passes (declining invitation with minimum 12 HCP)
    """

    # Create North's hand (opener) - 12 HCP version
    north_cards = [
        Card('5', '♠'), Card('4', '♠'),  # 2 spades
        Card('A', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'), Card('8', '♥'),  # 5 hearts (only AJ)
        Card('K', '♦'), Card('7', '♦'), Card('4', '♦'),  # 3 diamonds
        Card('Q', '♣'), Card('T', '♣'), Card('3', '♣')   # 3 clubs
    ]
    north_hand = Hand(north_cards)

    print(f"North's hand (opener): {north_hand}")
    print(f"  HCP: {north_hand.hcp}, Total Points: {north_hand.total_points}")
    print(f"  Distribution: ♠{north_hand.suit_lengths['♠']} ♥{north_hand.suit_lengths['♥']} ♦{north_hand.suit_lengths['♦']} ♣{north_hand.suit_lengths['♣']}")
    print(f"  Balanced: {north_hand.is_balanced}")
    print()

    # Create the auction history
    auction_history = [
        '1♥',   # North opens
        'Pass', # East passes
        '1♠',   # South responds (partner)
        'Pass', # West passes
        '1NT',  # North rebids 1NT (12-14 HCP, balanced, no spade fit)
        'Pass', # East passes
        '2♦',   # South bids 2♦ (invitational, 5+ diamonds)
        'Pass'  # West passes
    ]

    print("Auction:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Create bidding engine
    engine = BiddingEngine()

    # Get North's second rebid
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
        print("✅ TEST PASSED: North correctly passes (declining invitation with minimum 12 HCP)!")
        return True
    elif bid == '3NT':
        print("❌ TEST FAILED: North incorrectly bid 3NT (should decline with minimum)")
        return False
    else:
        print(f"⚠️  UNEXPECTED: North bid {bid} instead of Pass")
        return False


def test_accept_2nt_invitation_with_maximum():
    """
    Test that opener accepts 2NT invitation with maximum HCP.

    Auction: 1♦ - P - 1♥ - P - 1NT - P - 2NT - P
    North: 13 HCP (maximum)

    Expected: North bids 3NT (accepting 2NT invitation)
    """

    # Create North's hand (opener)
    north_cards = [
        Card('K', '♠'), Card('J', '♠'), Card('5', '♠'),  # 3 spades
        Card('Q', '♥'), Card('T', '♥'), Card('4', '♥'),  # 3 hearts
        Card('A', '♦'), Card('9', '♦'), Card('7', '♦'), Card('3', '♦'),  # 4 diamonds
        Card('K', '♣'), Card('8', '♣'), Card('2', '♣')   # 3 clubs
    ]
    north_hand = Hand(north_cards)

    print(f"North's hand (opener): {north_hand}")
    print(f"  HCP: {north_hand.hcp}, Total Points: {north_hand.total_points}")
    print()

    # Create the auction history
    auction_history = [
        '1♦',   # North opens
        'Pass', # East passes
        '1♥',   # South responds
        'Pass', # West passes
        '1NT',  # North rebids 1NT
        'Pass', # East passes
        '2NT',  # South invites with 2NT (11-12 HCP)
        'Pass'  # West passes
    ]

    print("Auction:")
    positions = ['North', 'East', 'South', 'West']
    for i, bid in enumerate(auction_history):
        print(f"  {positions[i % 4]}: {bid}")
    print()

    # Create bidding engine
    engine = BiddingEngine()

    # Get North's second rebid
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
    if bid == '3NT':
        print("✅ TEST PASSED: North correctly bids 3NT (accepting 2NT invitation)!")
        return True
    else:
        print(f"❌ TEST FAILED: North bid {bid} instead of 3NT")
        return False


if __name__ == '__main__':
    print("\n" + "="*70)
    print("TEST 1: Accept invitation after 1NT rebid (maximum 13 HCP)")
    print("="*70 + "\n")
    test1 = test_accept_invitation_after_1nt_rebid_maximum()

    print("\n" + "="*70)
    print("TEST 2: Decline invitation after 1NT rebid (minimum 12 HCP)")
    print("="*70 + "\n")
    test2 = test_decline_invitation_after_1nt_rebid_minimum()

    print("\n" + "="*70)
    print("TEST 3: Accept 2NT invitation with maximum HCP")
    print("="*70 + "\n")
    test3 = test_accept_2nt_invitation_with_maximum()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Test 1 (Accept with maximum): {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (Decline with minimum): {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Test 3 (Accept 2NT invitation): {'✅ PASSED' if test3 else '❌ FAILED'}")

    all_passed = test1 and test2 and test3
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    exit(0 if all_passed else 1)
