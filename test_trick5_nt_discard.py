"""
Test for BUG-H002: AI Discarding King in Trick 5 of NT Contract

This test specifically reproduces the user's reported bug where the AI
inappropriately discarded a King in trick 5 during NoTrump play.
"""

from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.minimax_ai import MinimaxPlayAI


def test_trick5_nt_king_discard():
    """
    Test that AI doesn't discard King in trick 5 of NT contract

    Scenario: 1NT contract, trick 5, East is void in led suit
    East holds King and low cards - should discard low card, not King
    """
    print("=" * 80)
    print("TEST: Trick 5 NT Contract - AI Should NOT Discard King")
    print("=" * 80)
    print()

    # Create a 1NT contract scenario in trick 5
    # Contract: 1NT by South
    contract = Contract(level=1, strain='NT', declarer='S', doubled=0)

    # Hands (each hand has 13 cards)
    # East is void in spades and will be forced to discard
    north_hand = Hand([
        Card('A', '♦'), Card('Q', '♦'), Card('8', '♦'), Card('3', '♦'), Card('2', '♦'),
        Card('9', '♣'), Card('7', '♣'), Card('5', '♣'), Card('4', '♣'),
        Card('K', '♥'), Card('J', '♥'), Card('7', '♥'),
        Card('5', '♠')
    ])

    east_hand = Hand([
        # No spades - will have to discard when spade is led
        Card('K', '♣'),  # King - should NOT discard
        Card('6', '♣'),  # Low club - OK to discard
        Card('3', '♣'),  # Low club - OK to discard
        Card('2', '♣'),  # Low club - OK to discard
        Card('T', '♦'),  # Ten of diamonds
        Card('7', '♦'),  # Low diamond - BEST choice to discard
        Card('6', '♦'),  # Low diamond - BEST choice to discard
        Card('4', '♦'),  # Low diamond
        Card('Q', '♥'),
        Card('T', '♥'),
        Card('8', '♥'),
        Card('5', '♥'),
        Card('3', '♥')
    ])

    south_hand = Hand([
        Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('T', '♠'),
        Card('A', '♥'), Card('9', '♥'), Card('6', '♥'),
        Card('J', '♣'), Card('T', '♣'), Card('8', '♣'),
        Card('J', '♦'), Card('9', '♦'), Card('5', '♦')
    ])

    west_hand = Hand([
        Card('J', '♠'), Card('9', '♠'), Card('8', '♠'), Card('7', '♠'), Card('6', '♠'),
        Card('4', '♥'), Card('2', '♥'),
        Card('A', '♣'), Card('Q', '♣'),
        Card('K', '♦'),
        Card('2', '♠'), Card('3', '♠'), Card('4', '♠')
    ])

    hands = {
        'N': north_hand,
        'E': east_hand,
        'S': south_hand,
        'W': west_hand
    }

    # Create play state for trick 5
    # North leads a spade (East is void)
    state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[
            (Card('5', '♠'), 'N')  # North led spade
        ],
        tricks_won={'N': 1, 'E': 1, 'S': 1, 'W': 1},  # 2-2 so far (trick 5)
        trick_history=[],  # Not needed for this test
        next_to_play='E',
        dummy_revealed=True
    )

    print("Scenario:")
    print(f"  Contract: {contract.level}{contract.strain} by {contract.declarer}")
    print(f"  Trick: 5 (of 13)")
    print(f"  North led: 5♠")
    print(f"  East (void in spades) must discard")
    print(f"  East holds: K♣ 6♣ 3♣ 2♣ T♦ 7♦ 6♦ 4♦ Q♥ T♥ 8♥ 5♥ 3♥")
    print()
    print(f"  ✅ CORRECT: Discard 6♦ or 7♦ or low club (low from weak suit)")
    print(f"  ❌ BUG: Discard K♣ (high card)")
    print()

    # Test with Minimax AI (Expert level - depth 4)
    print("-" * 80)
    print("Testing Minimax AI (depth 4 - Expert 8/10)")
    print("-" * 80)
    print()

    ai = MinimaxPlayAI(max_depth=4)
    chosen_card = ai.choose_card(state, 'E')

    print(f"  AI chose: {chosen_card}")
    print()

    # Check if AI chose a low card (not King, Queen, Jack, or Ace)
    is_low_card = chosen_card.rank in ['2', '3', '4', '5', '6', '7', '8', '9']
    is_not_king = chosen_card.rank != 'K'

    if is_low_card:
        print(f"  ✅ PASS: AI discarded a low card ({chosen_card})")
    elif is_not_king:
        print(f"  ⚠️  PARTIAL: AI discarded {chosen_card} (not King, but not ideal)")
    else:
        print(f"  ❌ FAIL: AI discarded {chosen_card} (high card!)")

    print()
    print("=" * 80)
    if is_low_card:
        print("✅ TEST PASSED - AI correctly avoids discarding King in trick 5")
    elif is_not_king:
        print("⚠️  TEST PARTIAL - AI avoided King but could be better")
    else:
        print("❌ TEST FAILED - AI still discarding high cards")
    print("=" * 80)

    # Assert for automated testing
    assert is_not_king, f"AI should not discard King, but chose {chosen_card}"
    assert is_low_card, f"AI should discard low card, but chose {chosen_card}"


if __name__ == '__main__':
    test_trick5_nt_king_discard()
