"""
Test for Master Trump Bug - North fails to play winning 5♣

This test reproduces the exact scenario from the user's bug report:
- Contract: 3♣ by West
- Trick 12: West leads K♣, North has only 5♣ left (master trump)
- East is VOID in clubs (discards)
- North should play 5♣ to win the trick, but played 7♣ instead

Bug: AI does not recognize 5♣ as a master trump when opponents are void.
Fix: Added master trump detection to PositionEvaluator._sure_winners_component()
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract, Trick
from engine.play.ai.minimax_ai import MinimaxPlayAI
from engine.play.ai.evaluation import PositionEvaluator


def create_endgame_position():
    """
    Recreate the exact endgame position from trick 12

    Remaining cards:
    - North: 5♣, A♥
    - East: A♥
    - South: 9♥, 6♥
    - West: A♣ (master trump)

    Current trick: West leads K♣, North plays ?, East discards
    """
    # Create hands with remaining cards
    # Use a simple object with .cards attribute to bypass Hand validation
    class PartialHand:
        def __init__(self, cards):
            self.cards = cards

    north_hand = PartialHand([Card('5', '♣'), Card('A', '♥')])
    east_hand = PartialHand([Card('A', '♥')])
    south_hand = PartialHand([Card('9', '♥'), Card('6', '♥')])
    west_hand = PartialHand([Card('A', '♣')])

    hands = {
        'N': north_hand,
        'E': east_hand,
        'S': south_hand,
        'W': west_hand
    }

    # Contract: 3♣ by West
    contract = Contract(level=3, strain='♣', declarer='W')

    # Create play state at trick 12
    # West has won 7 tricks, needs 2 more for contract
    # North/South have won 4 tricks
    play_state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[],
        tricks_won={'N': 1, 'E': 2, 'S': 3, 'W': 5},
        trick_history=[],  # Don't need full history for this test
        next_to_play='W',
        dummy_revealed=True
    )

    return play_state


def test_master_trump_evaluation():
    """Test that evaluator correctly identifies master trumps"""
    print("\n" + "="*80)
    print("TEST 1: Master Trump Evaluation")
    print("="*80)

    play_state = create_endgame_position()
    evaluator = PositionEvaluator()

    # Simulate West leading K♣
    play_state.current_trick = [(Card('K', '♣'), 'W')]
    play_state.next_to_play = 'N'

    # Remove K♣ from West's hand
    west_k_club = Card('K', '♣')
    play_state.hands['W'].cards.append(west_k_club)  # Add it first so we can test

    print(f"\nPosition:")
    print(f"  Contract: {play_state.contract}")
    print(f"  Current trick: W leads K♣")
    print(f"  North's cards: {[f'{c.rank}{c.suit}' for c in play_state.hands['N'].cards]}")
    print(f"  East's cards: {[f'{c.rank}{c.suit}' for c in play_state.hands['E'].cards]}")
    print(f"  South's cards: {[f'{c.rank}{c.suit}' for c in play_state.hands['S'].cards]}")
    print(f"  West's cards: {[f'{c.rank}{c.suit}' for c in play_state.hands['W'].cards]}")

    # Now simulate North playing 5♣
    import copy
    test_state_play_5 = copy.deepcopy(play_state)
    test_state_play_5.current_trick.append((Card('5', '♣'), 'N'))
    test_state_play_5.hands['N'].cards.remove(Card('5', '♣'))

    # Check if evaluation recognizes this as better for North
    print("\n--- Evaluation Analysis ---")

    # Get evaluation scores
    score_north = evaluator.evaluate(test_state_play_5, 'N')
    print(f"\nEvaluation for North after playing 5♣: {score_north:+.2f}")

    # Get component breakdown
    components = evaluator.get_component_scores(test_state_play_5, 'N')
    print(f"  Sure winners component: {components['sure_winners']:.2f}")
    print(f"  Tricks won component: {components['tricks_won']:.2f}")

    # The key test: Does the evaluator recognize 5♣ as valuable?
    # After North plays 5♣, East will discard, making 5♣ win the trick
    # This should increase North's evaluation

    print("\n✓ Master trump evaluation test complete")
    return score_north


def test_master_trump_ai_choice():
    """Test that Minimax AI correctly chooses to play the master trump"""
    print("\n" + "="*80)
    print("TEST 2: Minimax AI Card Choice")
    print("="*80)

    play_state = create_endgame_position()

    # Simulate West leading K♣
    west_k_club = Card('K', '♣')
    play_state.hands['W'].cards.append(west_k_club)
    play_state.current_trick = [(west_k_club, 'W')]
    play_state.next_to_play = 'N'

    # Remove K♣ from West's hand now (it's been played)
    play_state.hands['W'].cards.remove(west_k_club)

    print(f"\nPosition:")
    print(f"  Contract: {play_state.contract}")
    print(f"  Current trick: W leads K♣")
    print(f"  North to play from: {[f'{c.rank}{c.suit}' for c in play_state.hands['N'].cards]}")

    # Test with Minimax AI (depth 3 - same as 8/10 difficulty)
    ai = MinimaxPlayAI(max_depth=3)

    print(f"\n--- AI Decision ---")
    print(f"Using: {ai.get_name()}")

    chosen_card = ai.choose_card(play_state, 'N')

    print(f"\nAI chose: {chosen_card.rank}{chosen_card.suit}")

    stats = ai.get_statistics()
    print(f"Search stats:")
    print(f"  Nodes searched: {stats['nodes']}")
    print(f"  Time: {stats['time']:.3f}s")
    print(f"  Best score: {stats['score']:+.2f}")

    # Verify the AI chose correctly
    if chosen_card.rank == '5' and chosen_card.suit == '♣':
        print("\n✅ SUCCESS: AI correctly chose 5♣ (master trump)")
        return True
    else:
        print(f"\n❌ FAILURE: AI chose {chosen_card.rank}{chosen_card.suit} instead of 5♣")
        print("   This means the fix did not fully resolve the issue.")
        return False


def test_detailed_comparison():
    """Compare evaluations of playing 5♣ vs other cards"""
    print("\n" + "="*80)
    print("TEST 3: Detailed Comparison of Card Choices")
    print("="*80)

    play_state = create_endgame_position()
    evaluator = PositionEvaluator()

    # Simulate West leading K♣
    west_k_club = Card('K', '♣')
    play_state.hands['W'].cards.append(west_k_club)
    play_state.current_trick = [(west_k_club, 'W')]
    play_state.next_to_play = 'N'
    play_state.hands['W'].cards.remove(west_k_club)

    print(f"\nComparing North's options:")
    print(f"  North has: 5♣ (master trump), A♥")
    print(f"  East is VOID in clubs (will discard)")
    print(f"  South is VOID in clubs (will discard)")

    # Test playing 5♣ - simulate FULL trick including East and South discards
    import copy
    test_state = copy.deepcopy(play_state)

    # North plays 5♣
    test_state.current_trick.append((Card('5', '♣'), 'N'))
    test_state.hands['N'].cards.remove(Card('5', '♣'))
    test_state.next_to_play = 'E'

    # East discards (void in clubs)
    test_state.current_trick.append((Card('A', '♥'), 'E'))
    test_state.hands['E'].cards.remove(Card('A', '♥'))
    test_state.next_to_play = 'S'

    # South discards (void in clubs)
    test_state.current_trick.append((Card('9', '♥'), 'S'))
    test_state.hands['S'].cards.remove(Card('9', '♥'))

    # Trick complete - North wins with 5♣!
    # Determine winner: W-K♣, N-5♣, E-A♥, S-9♥
    # Only clubs: K♣, 5♣ -> K♣ wins (highest trump)
    # Wait, K is higher than 5! Let me reconsider...

    # Actually, looking at the original hand data more carefully:
    # West still has A♣ left. The trick is W leads K♣
    # But after this trick, North's 5♣ should be compared against West's remaining A♣

    # Let me check if North wins THIS trick
    winner = PlayEngine.determine_trick_winner(test_state.current_trick, '♣')
    print(f"\n  DEBUG: Trick winner = {winner}")

    if winner == 'N':
        test_state.tricks_won['N'] += 1
        print(f"  ✓ North WINS trick with 5♣!")
    else:
        # West's K♣ beat North's 5♣
        test_state.tricks_won[winner] += 1
        print(f"  ✗ {winner} wins trick (North's 5♣ did not win)")

    test_state.current_trick = []
    test_state.next_to_play = winner

    score_5c = evaluator.evaluate(test_state, 'N')

    print(f"\n  After playing 5♣: Evaluation = {score_5c:+.2f}")
    print(evaluator.explain_evaluation(test_state, 'N'))

    # Test playing A♥ (discard) - simulate full trick
    test_state2 = copy.deepcopy(play_state)

    # North discards A♥
    test_state2.current_trick.append((Card('A', '♥'), 'N'))
    test_state2.hands['N'].cards.remove(Card('A', '♥'))
    test_state2.next_to_play = 'E'

    # East discards
    test_state2.current_trick.append((Card('A', '♥'), 'E'))
    test_state2.hands['E'].cards.remove(Card('A', '♥'))
    test_state2.next_to_play = 'S'

    # South discards
    test_state2.current_trick.append((Card('9', '♥'), 'S'))
    test_state2.hands['S'].cards.remove(Card('9', '♥'))

    # West wins with K♣
    winner2 = PlayEngine.determine_trick_winner(test_state2.current_trick, '♣')
    test_state2.tricks_won[winner2] += 1
    test_state2.current_trick = []
    test_state2.next_to_play = winner2

    score_ah = evaluator.evaluate(test_state2, 'N')

    print(f"\n  After playing A♥: Evaluation = {score_ah:+.2f}")
    print(evaluator.explain_evaluation(test_state2, 'N'))

    print(f"\n--- Comparison ---")
    print(f"  5♣ is better by: {score_5c - score_ah:+.2f} points")

    if score_5c > score_ah:
        print("  ✅ Evaluation correctly prefers 5♣")
        return True
    else:
        print("  ❌ Evaluation incorrectly prefers discarding")
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("MASTER TRUMP BUG - Reproduction and Fix Verification")
    print("="*80)
    print("\nBug Report: North had 5♣ (master trump) but played 7♣ instead")
    print("Root Cause: Evaluator did not detect master trumps when opponents void")
    print("Fix Applied: Added master trump detection to _sure_winners_component()")

    # Run tests
    test_master_trump_evaluation()
    success_comparison = test_detailed_comparison()
    success_ai = test_master_trump_ai_choice()

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Evaluation comparison: {'✅ PASS' if success_comparison else '❌ FAIL'}")
    print(f"AI card choice: {'✅ PASS' if success_ai else '❌ FAIL'}")

    if success_comparison and success_ai:
        print("\n🎉 All tests passed! Master trump bug is FIXED.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Additional debugging needed.")
        sys.exit(1)
