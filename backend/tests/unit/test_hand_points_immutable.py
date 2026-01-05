"""
Test that hand point calculations remain constant even after cards are removed during play.

This test verifies the fix for the bug where AI feedback was showing incorrect point counts
because cards were being removed from Hand objects during play, causing HCP recalculation.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from engine.hand import Hand, Card


def test_hand_points_remain_constant_after_card_removal():
    """
    Test that HCP, dist_points, and total_points remain constant
    even after cards are removed from the hand during play.
    """
    # Create a hand with known point count
    cards = [
        Card('A', '♠'), Card('6', '♠'),  # 4 HCP in spades
        Card('K', '♥'), Card('T', '♥'), Card('7', '♥'), Card('5', '♥'),  # 3 HCP, 4 hearts
        Card('K', '♦'), Card('J', '♦'), Card('9', '♦'),  # 4 HCP, 3 diamonds
        Card('T', '♣'), Card('9', '♣'), Card('8', '♣'), Card('5', '♣')  # 0 HCP, 4 clubs
    ]

    hand = Hand(cards)

    # Verify initial point count
    # Shape is 2-4-3-4, so 1 dist point for the doubleton spade
    assert hand.hcp == 11, f"Expected 11 HCP, got {hand.hcp}"
    assert hand.dist_points == 1, f"Expected 1 dist point (doubleton), got {hand.dist_points}"
    assert hand.total_points == 12, f"Expected 12 total points, got {hand.total_points}"
    assert hand.suit_hcp['♠'] == 4, f"Expected 4 spade HCP, got {hand.suit_hcp['♠']}"
    assert hand.suit_hcp['♥'] == 3, f"Expected 3 heart HCP, got {hand.suit_hcp['♥']}"
    assert hand.suit_hcp['♦'] == 4, f"Expected 4 diamond HCP, got {hand.suit_hcp['♦']}"
    assert hand.suit_hcp['♣'] == 0, f"Expected 0 club HCP, got {hand.suit_hcp['♣']}"

    # Simulate play by removing cards (including high cards)
    # Remove A♠ (4 HCP), K♥ (3 HCP), K♦ (3 HCP) = 10 HCP removed
    hand.cards.remove(Card('A', '♠'))
    hand.cards.remove(Card('K', '♥'))
    hand.cards.remove(Card('K', '♦'))

    # Verify that point counts HAVE NOT CHANGED
    # (This is the fix - points should remain as originally calculated)
    assert hand.hcp == 11, f"HCP changed after card removal! Expected 11, got {hand.hcp}"
    assert hand.dist_points == 1, f"Dist points changed after card removal! Expected 1, got {hand.dist_points}"
    assert hand.total_points == 12, f"Total points changed after card removal! Expected 12, got {hand.total_points}"
    assert hand.suit_hcp['♠'] == 4, f"Spade HCP changed! Expected 4, got {hand.suit_hcp['♠']}"
    assert hand.suit_hcp['♥'] == 3, f"Heart HCP changed! Expected 3, got {hand.suit_hcp['♥']}"
    assert hand.suit_hcp['♦'] == 4, f"Diamond HCP changed! Expected 4, got {hand.suit_hcp['♦']}"
    assert hand.suit_hcp['♣'] == 0, f"Club HCP changed! Expected 0, got {hand.suit_hcp['♣']}"

    print("✅ PASS: Hand point counts remain constant after card removal")


def test_hand_with_5_card_suit_dist_points():
    """
    Test that distribution points remain constant after card removal
    for a hand with a 5-card suit.
    """
    cards = [
        Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'),  # 5 spades, 10 HCP
        Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'),  # 3 hearts, 9 HCP
        Card('A', '♦'), Card('K', '♦'),  # 2 diamonds, 7 HCP
        Card('A', '♣'), Card('K', '♣'), Card('Q', '♣')  # 3 clubs, 9 HCP
    ]

    hand = Hand(cards)

    # 5-card suit gets 1 dist point
    assert hand.hcp == 35, f"Expected 35 HCP, got {hand.hcp}"
    assert hand.dist_points == 1, f"Expected 1 dist point (5-card suit), got {hand.dist_points}"
    assert hand.total_points == 36, f"Expected 36 total points, got {hand.total_points}"

    # Remove 3 spades
    hand.cards.remove(Card('A', '♠'))
    hand.cards.remove(Card('K', '♠'))
    hand.cards.remove(Card('Q', '♠'))

    # Verify points haven't changed
    assert hand.hcp == 35, f"HCP changed! Expected 35, got {hand.hcp}"
    assert hand.dist_points == 1, f"Dist points changed! Expected 1, got {hand.dist_points}"
    assert hand.total_points == 36, f"Total points changed! Expected 36, got {hand.total_points}"

    print("✅ PASS: Distribution points remain constant after card removal")


if __name__ == '__main__':
    test_hand_points_remain_constant_after_card_removal()
    test_hand_with_5_card_suit_dist_points()
    print("\n✅ All tests passed!")
