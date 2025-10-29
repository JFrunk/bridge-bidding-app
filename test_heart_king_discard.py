#!/usr/bin/env python3
"""
Test to verify that advanced AI (Minimax depth 3) correctly handles
the heart King discard situation that intermediate AI (depth 2) failed.

This recreates the exact position where North incorrectly discarded ♥K.
"""

import sys
sys.path.insert(0, 'backend')

from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract, PlayEngine
from engine.play.ai.minimax_ai import MinimaxPlayAI

def create_test_position():
    """
    Recreate the position from Trick 7 where North must discard.

    North has: ♠65 ♥K54
    Dummy (East) has: ♠- ♥AQ92 ♦- ♣753

    West leads ♦4 (will ruff), North must discard.
    Question: Should North discard a spade or the ♥K?
    Answer: Discard a spade! The ♥K is a guaranteed trick.
    """

    # Recreate remaining cards at this position
    north_cards = [
        Card('6', '♠'), Card('5', '♠'),
        Card('K', '♥'), Card('5', '♥'), Card('4', '♥')
    ]

    east_cards = [
        Card('A', '♥'), Card('Q', '♥'), Card('9', '♥'), Card('2', '♥'),
        Card('7', '♣'), Card('5', '♣'), Card('3', '♣')
    ]

    south_cards = [
        Card('7', '♥'), Card('6', '♥'),
        Card('7', '♦'), Card('5', '♦')
    ]

    west_cards = [
        Card('2', '♠'),
        Card('K', '♦'),
        Card('Q', '♣'), Card('4', '♣')
    ]

    hands = {
        'N': Hand(north_cards),
        'E': Hand(east_cards),
        'S': Hand(south_cards),
        'W': Hand(west_cards)
    }

    contract = Contract(level=3, strain='♣', declarer='W')

    state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[(Card('4', '♦'), 'W')],  # West leading diamond (will ruff)
        tricks_won={'N': 0, 'E': 2, 'S': 3, 'W': 4},
        trick_history=[],
        next_to_play='N',
        dummy_revealed=True,
        current_trick_leader='W'
    )

    return state

def test_ai_discard_decision():
    """Test both intermediate and advanced AI on the discard problem"""

    print("=" * 70)
    print("TEST: North's Discard Decision on Trick 7")
    print("=" * 70)
    print()
    print("Position:")
    print("  North: ♠65 ♥K54")
    print("  East (Dummy): ♥AQ92 ♣753")
    print("  South: ♥76 ♦75")
    print("  West (Declarer): ♠2 ♦K ♣Q4")
    print()
    print("Situation: West leads ♦4 (will ruff), North must discard")
    print("Correct play: Discard a spade (♥K is a guaranteed trick)")
    print()

    state = create_test_position()

    # Test intermediate AI (depth 2) - the one that made the error
    print("-" * 70)
    print("Testing INTERMEDIATE AI (Minimax depth 2) - OLD DEFAULT")
    print("-" * 70)
    ai_intermediate = MinimaxPlayAI(max_depth=2)
    card_intermediate = ai_intermediate.choose_card(state, 'N')
    print(f"AI chose: {card_intermediate.rank}{card_intermediate.suit}")

    if card_intermediate.rank == 'K' and card_intermediate.suit == '♥':
        print("❌ WRONG: Discarded the ♥K (guaranteed trick thrown away!)")
    else:
        print(f"✅ CORRECT: Discarded {card_intermediate.rank}{card_intermediate.suit} (preserving ♥K)")

    stats = ai_intermediate.get_statistics()
    print(f"Search stats: {stats['nodes']} nodes, {stats['time']:.3f}s")
    print()

    # Test advanced AI (depth 3) - the new default
    print("-" * 70)
    print("Testing ADVANCED AI (Minimax depth 3) - NEW DEFAULT")
    print("-" * 70)
    state_advanced = create_test_position()  # Fresh state
    ai_advanced = MinimaxPlayAI(max_depth=3)
    card_advanced = ai_advanced.choose_card(state_advanced, 'N')
    print(f"AI chose: {card_advanced.rank}{card_advanced.suit}")

    if card_advanced.rank == 'K' and card_advanced.suit == '♥':
        print("❌ WRONG: Discarded the ♥K (guaranteed trick thrown away!)")
    else:
        print(f"✅ CORRECT: Discarded {card_advanced.rank}{card_advanced.suit} (preserving ♥K)")

    stats = ai_advanced.get_statistics()
    print(f"Search stats: {stats['nodes']} nodes, {stats['time']:.3f}s")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Intermediate AI (depth 2): {card_intermediate.rank}{card_intermediate.suit}")
    print(f"Advanced AI (depth 3):     {card_advanced.rank}{card_advanced.suit}")
    print()

    if (card_intermediate.rank == 'K' and card_intermediate.suit == '♥') and \
       (card_advanced.rank != 'K' or card_advanced.suit != '♥'):
        print("✅ FIX VALIDATED: Advanced AI makes better decision than intermediate")
        print("   The default change from 'intermediate' to 'advanced' solves the problem!")
    elif card_advanced.rank != 'K' or card_advanced.suit != '♥':
        print("✅ Both AIs make correct decision at this position")
    else:
        print("⚠️  Both AIs still struggling with this position")
    print()

if __name__ == '__main__':
    test_ai_discard_decision()
