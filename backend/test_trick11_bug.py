"""
Test for Trick 11 Bug - North plays 2♣ instead of winning with 7♣

This reproduces the EXACT scenario from the user's bug report:
- Contract: 3♣ by West
- Trick 11: West leads 3♣
- North has: 7♣, 5♣, 2♣ (all clubs)
- East is VOID in clubs (will discard)
- South is VOID in clubs (will discard)
- North should play 7♣ or 5♣ to WIN, but plays 2♣ instead!

Bug: AI doesn't recognize that 7♣ > 3♣ when opponents are void.
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from engine.hand import Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.minimax_ai import MinimaxPlayAI
from engine.play.ai.evaluation import PositionEvaluator


def create_trick11_position():
    """
    Recreate Trick 11 position

    Remaining cards after 10 tricks:
    - North: 7♣, 5♣, 2♣, A♥
    - East: A♥ (VOID in clubs)
    - South: 9♥, 6♥ (VOID in clubs)
    - West: A♣, K♣, 4♣, 3♣

    Current trick: West leads 3♣, North to play
    """
    class PartialHand:
        def __init__(self, cards):
            self.cards = cards

    north_hand = PartialHand([
        Card('7', '♣'), Card('5', '♣'), Card('2', '♣'), Card('A', '♥')
    ])
    east_hand = PartialHand([Card('A', '♥')])  # VOID in clubs!
    south_hand = PartialHand([Card('9', '♥'), Card('6', '♥')])  # VOID in clubs!
    west_hand = PartialHand([
        Card('A', '♣'), Card('K', '♣'), Card('4', '♣'), Card('3', '♣')
    ])

    hands = {
        'N': north_hand,
        'E': east_hand,
        'S': south_hand,
        'W': west_hand
    }

    # Contract: 3♣ by West (needs 9 tricks)
    contract = Contract(level=3, strain='♣', declarer='W')

    # After 10 tricks: W has 7, NS have 3
    play_state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[],
        tricks_won={'N': 1, 'E': 2, 'S': 2, 'W': 5},
        trick_history=[],
        next_to_play='W',
        dummy_revealed=True
    )

    return play_state


def test_trick_winner_determination():
    """Test that determine_trick_winner works correctly"""
    print("\n" + "="*80)
    print("TEST 1: Trick Winner Determination")
    print("="*80)

    print("\nTest A: West leads 3♣, North plays 7♣, East/South discard")
    trick = [
        (Card('3', '♣'), 'W'),  # West leads
        (Card('7', '♣'), 'N'),  # North plays higher club
        (Card('A', '♥'), 'E'),  # East discards (void)
        (Card('9', '♥'), 'S'),  # South discards (void)
    ]

    winner = PlayEngine.determine_trick_winner(trick, '♣')  # Clubs are trumps
    print(f"  Winner: {winner}")

    if winner == 'N':
        print(f"  ✅ PASS: North wins with 7♣ (higher trump)")
    else:
        print(f"  ❌ FAIL: {winner} wins instead of North!")

    print("\nTest B: West leads 3♣, North plays 2♣, East/South discard")
    trick2 = [
        (Card('3', '♣'), 'W'),
        (Card('2', '♣'), 'N'),  # North plays LOWER club
        (Card('A', '♥'), 'E'),
        (Card('9', '♥'), 'S'),
    ]

    winner2 = PlayEngine.determine_trick_winner(trick2, '♣')
    print(f"  Winner: {winner2}")

    if winner2 == 'W':
        print(f"  ✅ PASS: West wins with 3♣ (higher trump)")
    else:
        print(f"  ❌ FAIL: {winner2} wins instead of West!")


def test_evaluation_comparison():
    """Test that evaluation correctly values winning vs losing"""
    print("\n" + "="*80)
    print("TEST 2: Evaluation Comparison")
    print("="*80)

    play_state = create_trick11_position()
    evaluator = PositionEvaluator()

    # Simulate West leading 3♣
    import copy

    # Remove 3♣ from West's hand
    west_3c = Card('3', '♣')
    play_state.hands['W'].cards.remove(west_3c)
    play_state.current_trick = [(west_3c, 'W')]
    play_state.next_to_play = 'N'

    print(f"\nSetup:")
    print(f"  Current trick: W-3♣")
    print(f"  North to play from: {[f'{c.rank}{c.suit}' for c in play_state.hands['N'].cards]}")
    print(f"  East's cards: {[f'{c.rank}{c.suit}' for c in play_state.hands['E'].cards]} (VOID in ♣)")
    print(f"  South's cards: {[f'{c.rank}{c.suit}' for c in play_state.hands['S'].cards]} (VOID in ♣)")

    # Test A: North plays 7♣ (wins)
    test_state_7c = copy.deepcopy(play_state)
    test_state_7c.current_trick.append((Card('7', '♣'), 'N'))
    test_state_7c.hands['N'].cards.remove(Card('7', '♣'))
    test_state_7c.next_to_play = 'E'

    # East discards
    test_state_7c.current_trick.append((Card('A', '♥'), 'E'))
    test_state_7c.hands['E'].cards.remove(Card('A', '♥'))

    # South discards
    test_state_7c.current_trick.append((Card('9', '♥'), 'S'))
    test_state_7c.hands['S'].cards.remove(Card('9', '♥'))

    # Determine winner
    winner_7c = PlayEngine.determine_trick_winner(test_state_7c.current_trick, '♣')
    test_state_7c.tricks_won[winner_7c] += 1
    test_state_7c.current_trick = []

    score_7c = evaluator.evaluate(test_state_7c, 'N')

    print(f"\n--- After North plays 7♣ ---")
    print(f"  Trick winner: {winner_7c}")
    print(f"  Tricks: N={test_state_7c.tricks_won['N']}, S={test_state_7c.tricks_won['S']}, E={test_state_7c.tricks_won['E']}, W={test_state_7c.tricks_won['W']}")
    print(f"  Evaluation for North: {score_7c:+.2f}")

    # Test B: North plays 2♣ (loses)
    test_state_2c = copy.deepcopy(play_state)
    test_state_2c.current_trick.append((Card('2', '♣'), 'N'))
    test_state_2c.hands['N'].cards.remove(Card('2', '♣'))
    test_state_2c.next_to_play = 'E'

    # East discards
    test_state_2c.current_trick.append((Card('A', '♥'), 'E'))
    test_state_2c.hands['E'].cards.remove(Card('A', '♥'))

    # South discards
    test_state_2c.current_trick.append((Card('9', '♥'), 'S'))
    test_state_2c.hands['S'].cards.remove(Card('9', '♥'))

    # Determine winner
    winner_2c = PlayEngine.determine_trick_winner(test_state_2c.current_trick, '♣')
    test_state_2c.tricks_won[winner_2c] += 1
    test_state_2c.current_trick = []

    score_2c = evaluator.evaluate(test_state_2c, 'N')

    print(f"\n--- After North plays 2♣ ---")
    print(f"  Trick winner: {winner_2c}")
    print(f"  Tricks: N={test_state_2c.tricks_won['N']}, S={test_state_2c.tricks_won['S']}, E={test_state_2c.tricks_won['E']}, W={test_state_2c.tricks_won['W']}")
    print(f"  Evaluation for North: {score_2c:+.2f}")

    print(f"\n--- Comparison ---")
    print(f"  7♣ vs 2♣ score difference: {score_7c - score_2c:+.2f}")

    if score_7c > score_2c:
        print(f"  ✅ PASS: Evaluation correctly prefers 7♣ (wins trick)")
        return True
    else:
        print(f"  ❌ FAIL: Evaluation does NOT prefer 7♣!")
        print(f"     This is the BUG - evaluation can't tell winning from losing")
        return False


def test_ai_choice():
    """Test that AI chooses correctly"""
    print("\n" + "="*80)
    print("TEST 3: Minimax AI Card Choice")
    print("="*80)

    play_state = create_trick11_position()

    # West leads 3♣
    west_3c = Card('3', '♣')
    play_state.hands['W'].cards.remove(west_3c)
    play_state.current_trick = [(west_3c, 'W')]
    play_state.next_to_play = 'N'

    print(f"\nPosition:")
    print(f"  Contract: {play_state.contract}")
    print(f"  Current trick: W-3♣")
    print(f"  North to play from: {[f'{c.rank}{c.suit}' for c in play_state.hands['N'].cards]}")

    # Use Minimax AI depth 4 (deeper search to complete tricks)
    ai = MinimaxPlayAI(max_depth=4)

    print(f"\n--- AI Decision ---")
    print(f"Using: {ai.get_name()}")

    # DEBUG: Manually evaluate each card
    print(f"\n--- DEBUG: Manual Evaluation of Each Card ---")
    evaluator = PositionEvaluator()
    import copy

    for card in [Card('7', '♣'), Card('5', '♣'), Card('2', '♣'), Card('A', '♥')]:
        test_state = copy.deepcopy(play_state)
        # Simulate playing this card
        test_state.current_trick.append((card, 'N'))
        test_state.hands['N'].cards.remove(card)

        # Get immediate evaluation (depth 0)
        score = evaluator.evaluate(test_state, 'N')
        print(f"  {card.rank}{card.suit}: {score:+.2f} (immediate eval)")

    chosen_card = ai.choose_card(play_state, 'N')

    print(f"\nAI chose: {chosen_card.rank}{chosen_card.suit}")

    stats = ai.get_statistics()
    print(f"Search stats:")
    print(f"  Nodes searched: {stats['nodes']}")
    print(f"  Time: {stats['time']:.3f}s")
    print(f"  Best score: {stats['score']:+.2f}")

    # Check if AI chose winning card
    if chosen_card.rank in ['7', '5']:
        print(f"\n✅ SUCCESS: AI chose {chosen_card.rank}♣ (wins trick)")
        return True
    elif chosen_card.rank == '2':
        print(f"\n❌ FAILURE: AI chose 2♣ (loses trick)")
        print(f"   This reproduces the user's bug!")
        return False
    else:
        print(f"\n⚠️  UNEXPECTED: AI chose {chosen_card.rank}{chosen_card.suit}")
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("TRICK 11 BUG - North plays 2♣ instead of winning 7♣")
    print("="*80)

    test_trick_winner_determination()
    success_eval = test_evaluation_comparison()
    success_ai = test_ai_choice()

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Evaluation comparison: {'✅ PASS' if success_eval else '❌ FAIL'}")
    print(f"AI card choice: {'✅ PASS' if success_ai else '❌ FAIL'}")

    if success_eval and success_ai:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Bug reproduced - AI is not choosing winning card")
        sys.exit(1)
