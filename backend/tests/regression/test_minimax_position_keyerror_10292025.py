"""
Regression test for minimax AI KeyError bug

Bug Report: backend/review_requests/hand_2025-10-29_14-26-11.json
Error: KeyError: 'West' in minimax_ai.py line 372 and 320

Root Cause: Minimax AI incorrectly converted position from 'W' to 'West'
and tried to access state.hands['West'], but the dict uses short keys ('W').

This test ensures minimax AI works with all 4 positions as opening leader.
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, Contract
from engine.play.ai.minimax_ai import MinimaxPlayAI


def test_minimax_ai_handles_all_positions():
    """
    Test that minimax AI can play from all 4 positions without KeyError.

    This test reproduces the bug where minimax AI crashed with:
    KeyError: 'West' when trying to play from position 'W'.

    The bug was caused by incorrect position mapping from short ('W')
    to full names ('West'), but state.hands uses short keys.
    """

    # Create simple test hands for all positions
    test_cases = [
        ('N', 'E'),  # North declares, East leads
        ('E', 'S'),  # East declares, South leads
        ('S', 'W'),  # South declares, West leads
        ('W', 'N'),  # West declares, North leads
    ]

    for declarer, expected_leader in test_cases:
        # Create hands with SHORT keys (N/E/S/W)
        hands = {
            'N': Hand([
                Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
                Card('T', '♠'), Card('9', '♠'), Card('8', '♠'), Card('7', '♠'),
                Card('6', '♠'), Card('5', '♠'), Card('4', '♠'), Card('3', '♠'), Card('2', '♠')
            ]),
            'E': Hand([
                Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'),
                Card('T', '♥'), Card('9', '♥'), Card('8', '♥'), Card('7', '♥'),
                Card('6', '♥'), Card('5', '♥'), Card('4', '♥'), Card('3', '♥'), Card('2', '♥')
            ]),
            'S': Hand([
                Card('A', '♦'), Card('K', '♦'), Card('Q', '♦'), Card('J', '♦'),
                Card('T', '♦'), Card('9', '♦'), Card('8', '♦'), Card('7', '♦'),
                Card('6', '♦'), Card('5', '♦'), Card('4', '♦'), Card('3', '♦'), Card('2', '♦')
            ]),
            'W': Hand([
                Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'), Card('J', '♣'),
                Card('T', '♣'), Card('9', '♣'), Card('8', '♣'), Card('7', '♣'),
                Card('6', '♣'), Card('5', '♣'), Card('4', '♣'), Card('3', '♣'), Card('2', '♣')
            ])
        }

        contract = Contract(level=3, strain='NT', declarer=declarer, doubled=0)
        play_state = PlayEngine.create_play_session(contract, hands)

        # Verify opening leader is correct
        assert play_state.next_to_play == expected_leader, \
            f"Opening leader should be {expected_leader}, got {play_state.next_to_play}"

        # Create minimax AI (depth 2 for speed)
        ai = MinimaxPlayAI(max_depth=2)

        # CRITICAL TEST: AI must be able to choose card without KeyError
        try:
            card = ai.choose_card(play_state, expected_leader)

            # Verify AI selected a valid card
            assert card is not None, \
                f"AI failed to select card for position {expected_leader}"

            leader_hand = play_state.hands[expected_leader]
            assert card in leader_hand.cards, \
                f"AI selected card not in {expected_leader}'s hand"

            print(f"✅ Minimax AI successfully played from {expected_leader} "
                  f"(declarer={declarer}): {card.rank}{card.suit}")

        except KeyError as e:
            # This was the original bug - should NOT happen anymore
            pytest.fail(
                f"❌ REGRESSION: KeyError when playing from {expected_leader}: {e}\n"
                f"   Declarer: {declarer}, Opening leader: {expected_leader}\n"
                f"   This indicates the position mapping bug has returned!"
            )
        except Exception as e:
            pytest.fail(
                f"❌ Unexpected error when playing from {expected_leader}: {e}"
            )


def test_minimax_ai_with_real_bug_scenario():
    """
    Test using the exact scenario from the bug report.

    Contract: 5♦ by South
    Opening leader: West
    Bug: KeyError: 'West' when West tried to make opening lead
    """

    # Simplified version of hands from bug report
    hands = {
        'N': Hand([
            Card('K', '♠'), Card('2', '♠'),
            Card('9', '♥'), Card('2', '♥'),
            Card('T', '♦'), Card('8', '♦'), Card('7', '♦'), Card('3', '♦'), Card('2', '♦'),
            Card('A', '♣'), Card('7', '♣'), Card('5', '♣'), Card('2', '♣')
        ]),
        'E': Hand([
            Card('A', '♠'), Card('7', '♠'), Card('4', '♠'), Card('3', '♠'),
            Card('K', '♥'), Card('Q', '♥'), Card('T', '♥'), Card('3', '♥'),
            Card('5', '♦'),
            Card('Q', '♣'), Card('J', '♣'), Card('6', '♣'), Card('3', '♣')
        ]),
        'S': Hand([
            Card('Q', '♠'), Card('8', '♠'), Card('6', '♠'),
            Card('A', '♥'), Card('J', '♥'),
            Card('A', '♦'), Card('K', '♦'), Card('Q', '♦'), Card('9', '♦'), Card('6', '♦'), Card('4', '♦'),
            Card('T', '♣'), Card('8', '♣')
        ]),
        'W': Hand([
            Card('J', '♠'), Card('T', '♠'), Card('9', '♠'), Card('5', '♠'),
            Card('8', '♥'), Card('7', '♥'), Card('6', '♥'), Card('5', '♥'), Card('4', '♥'),
            Card('J', '♦'),
            Card('K', '♣'), Card('9', '♣'), Card('4', '♣')
        ])
    }

    contract = Contract(level=5, strain='♦', declarer='S', doubled=0)
    play_state = PlayEngine.create_play_session(contract, hands)

    # Verify West is opening leader
    assert play_state.next_to_play == 'W', "Opening leader should be West"

    # Minimax AI should handle West without KeyError
    ai = MinimaxPlayAI(max_depth=2)

    try:
        card = ai.choose_card(play_state, 'W')

        assert card is not None, "AI must select a card"
        assert card in hands['W'].cards, "AI must select card from West's hand"

        print(f"✅ Minimax AI opening lead from West: {card.rank}{card.suit}")
        print(f"   Contract: 5♦ by South")
        print(f"   Bug FIXED: No KeyError on position 'W'")

    except KeyError as e:
        pytest.fail(
            f"❌ REGRESSION: Original bug has returned!\n"
            f"   KeyError when West tries to play: {e}\n"
            f"   This is the exact scenario from the bug report."
        )


if __name__ == "__main__":
    print("Running regression tests for minimax AI position KeyError bug...")
    print("=" * 70)

    try:
        test_minimax_ai_handles_all_positions()
        test_minimax_ai_with_real_bug_scenario()
        print("=" * 70)
        print("✅ ALL TESTS PASSED - Minimax AI position bug is FIXED")
    except AssertionError as e:
        print("=" * 70)
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print("=" * 70)
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
