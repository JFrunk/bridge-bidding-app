"""
Simple test for master trump detection

Scenario: Defender has master trump (opponents are VOID)
- Contract: 2♠ by South (declarer)
- East (defender) has A♠ (master trump) remaining
- South and West are both VOID in spades
- East leads and should play A♠ to win

This is DEFINITELY a master trump situation.
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from engine.hand import Card
from engine.play_engine import Contract
from engine.play.ai.evaluation import PositionEvaluator


def test_master_trump_detection():
    """
    Test that master trump detection works

    Setup:
    - Contract: 2♠ by S (spades are trumps)
    - North (dummy) has: 2♠ (low trump)
    - East (defender) has: A♠ (MASTER TRUMP - highest spade left!)
    - South (declarer) has: 3♥ (no spades - VOID in trumps!)
    - West (defender) has: 4♥ (no spades - VOID in trumps!)

    In this position, East's A♠ is a GUARANTEED WINNER because:
    1. It's the highest trump remaining
    2. One opponent (South) is void in trumps
    3. Partner (West) is also void in trumps
    4. Only North has a trump (2♠), which is lower than A♠

    The evaluator should recognize East's A♠ as a master trump.
    """
    print("\n" + "="*80)
    print("TEST: Master Trump Detection - East has A♠ (master trump)")
    print("="*80)

    # Create minimal hands for testing
    class PartialHand:
        def __init__(self, cards):
            self.cards = cards

    # Setup: East has master trump (A♠), others don't have higher trumps
    hands = {
        'N': PartialHand([Card('2', '♠')]),  # Dummy - has low trump
        'E': PartialHand([Card('A', '♠')]),   # Defender - MASTER TRUMP!
        'S': PartialHand([Card('3', '♥')]),   # Declarer - VOID in trumps
        'W': PartialHand([Card('4', '♥')])    # Defender - VOID in trumps
    }

    # Contract: 2♠ by South
    contract = Contract(level=2, strain='♠', declarer='S')

    # Create a minimal PlayState
    from engine.play_engine import PlayState
    play_state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[],
        tricks_won={'N': 5, 'E': 3, 'S': 4, 'W': 1},
        next_to_play='E'
    )

    # Evaluate from East's perspective
    evaluator = PositionEvaluator()

    print(f"\nSetup:")
    print(f"  Contract: {contract}")
    print(f"  Trump suit: ♠")
    print(f"")
    print(f"  North (dummy): {[f'{c.rank}{c.suit}' for c in hands['N'].cards]}")
    print(f"  East (defender): {[f'{c.rank}{c.suit}' for c in hands['E'].cards]} <- MASTER TRUMP!")
    print(f"  South (declarer): {[f'{c.rank}{c.suit}' for c in hands['S'].cards]} <- VOID in trumps")
    print(f"  West (defender): {[f'{c.rank}{c.suit}' for c in hands['W'].cards]} <- VOID in trumps")

    # Get component scores
    components = evaluator.get_component_scores(play_state, 'E')

    print(f"\n--- Evaluation Components for East ---")
    print(f"  Sure winners: {components['sure_winners']:.2f}")
    print(f"  Trump control: {components['trump_control']:.2f}")

    # Check if evaluator detected the master trump
    print(f"\n--- Master Trump Detection ---")

    if components['sure_winners'] >= 1.0:
        print(f"  ✅ PASS: Evaluator correctly identified A♠ as master trump")
        print(f"     (sure_winners = {components['sure_winners']:.2f}, expected >= 1.0)")
        return True
    else:
        print(f"  ❌ FAIL: Evaluator did NOT recognize A♠ as master trump")
        print(f"     (sure_winners = {components['sure_winners']:.2f}, expected >= 1.0)")
        print(f"\n  This means the master trump fix is not working!")
        return False


def test_no_master_trump():
    """
    Negative test: When opponents have higher trumps, should NOT detect master

    Setup:
    - Contract: 2♠ by S
    - East has: K♠ (high trump, but NOT master)
    - South (opponent) has: A♠ (HIGHER trump)
    """
    print("\n" + "="*80)
    print("TEST: No Master Trump - East has K♠ but South has A♠")
    print("="*80)

    class PartialHand:
        def __init__(self, cards):
            self.cards = cards

    hands = {
        'N': PartialHand([Card('2', '♠')]),   # Dummy - low trump
        'E': PartialHand([Card('K', '♠')]),   # Defender - high but NOT master
        'S': PartialHand([Card('A', '♠')]),   # Declarer - HAS ACE (higher!)
        'W': PartialHand([Card('3', '♥')])    # Defender - void
    }

    contract = Contract(level=2, strain='♠', declarer='S')

    from engine.play_engine import PlayState
    play_state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[],
        tricks_won={'N': 5, 'E': 3, 'S': 4, 'W': 1},
        next_to_play='E'
    )

    evaluator = PositionEvaluator()

    print(f"\nSetup:")
    print(f"  Contract: {contract}")
    print(f"  East (defender): {[f'{c.rank}{c.suit}' for c in hands['E'].cards]} <- K♠ (NOT master)")
    print(f"  South (declarer): {[f'{c.rank}{c.suit}' for c in hands['S'].cards]} <- A♠ (higher!)")

    components = evaluator.get_component_scores(play_state, 'E')

    print(f"\n--- Evaluation Components for East ---")
    print(f"  Sure winners: {components['sure_winners']:.2f}")

    # K♠ should NOT be counted as master trump (A♠ is higher)
    if components['sure_winners'] < 1.0:
        print(f"  ✅ PASS: Correctly did NOT mark K♠ as master (A♠ is higher)")
        return True
    else:
        print(f"  ❌ FAIL: Incorrectly marked K♠ as master trump")
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("MASTER TRUMP DETECTION - Simple Test Suite")
    print("="*80)

    success1 = test_master_trump_detection()
    success2 = test_no_master_trump()

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Master trump detection: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Non-master trump test: {'✅ PASS' if success2 else '❌ FAIL'}")

    if success1 and success2:
        print("\n🎉 All tests passed! Master trump detection is working.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed.")
        sys.exit(1)
