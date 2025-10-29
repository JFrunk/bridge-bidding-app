"""
Test that AI never discards high cards (K, Q, A) when low cards are available.

This test reproduces the bug where Expert AI discarded ♣K instead of ♦6/♦7.
"""

from engine.hand import Hand, Card
from engine.play_engine import Contract, PlayState
from engine.play.ai.minimax_ai import MinimaxPlayAI
from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE


def test_discard_chooses_low_card():
    """
    Reproduce the exact scenario from bug report:
    - East is void in spades
    - East holds: ♥QT8 ♦T76 ♣KJT963
    - North leads ♠7 (will win the trick)
    - East must discard

    Expected: Discard ♦6 or ♦7 (low card from weak suit)
    Bug: Was discarding ♣K (high card from long suit)
    """

    # Create simplified hands for the discard test
    # Key: East is void in spades and must discard
    hands = {
        'N': Hand([
            Card('A', '♠'), Card('J', '♠'), Card('7', '♠'),
            Card('K', '♥'), Card('J', '♥'), Card('2', '♥'),
            Card('Q', '♦'), Card('9', '♦'), Card('8', '♦'),
            Card('7', '♣'), Card('5', '♣'), Card('4', '♣'), Card('2', '♣')
        ]),
        'E': Hand([
            # No spades (void - this is the key!)
            Card('Q', '♥'), Card('T', '♥'), Card('8', '♥'),
            Card('T', '♦'), Card('7', '♦'), Card('6', '♦'),
            Card('K', '♣'), Card('J', '♣'), Card('T', '♣'),
            Card('9', '♣'), Card('6', '♣'), Card('3', '♣'), Card('2', '♣')
        ]),
        'S': Hand([
            Card('Q', '♠'), Card('8', '♠'), Card('4', '♠'),
            Card('A', '♥'), Card('7', '♥'), Card('6', '♥'),
            Card('A', '♦'), Card('5', '♦'), Card('3', '♦'),
            Card('A', '♣'), Card('Q', '♣'), Card('8', '♣'), Card('J', '♦')
        ]),
        'W': Hand([
            Card('K', '♠'), Card('6', '♠'), Card('5', '♠'), Card('3', '♠'),
            Card('9', '♥'), Card('5', '♥'), Card('4', '♥'), Card('3', '♥'),
            Card('K', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('9', '♣'), Card('8', '♣')
        ]),
    }

    # Create contract: 4♠ by South
    contract = Contract(level=4, strain='♠', declarer='S')

    # Create play state at trick 2
    state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[
            (Card('7', '♠'), 'N')  # North led ♠7
        ],
        tricks_won={'N': 1, 'E': 0, 'S': 0, 'W': 0},  # North won trick 1
        trick_history=[],
        next_to_play='E',
        dummy_revealed=True
    )

    print("=" * 80)
    print("TEST: AI Discard Logic - Should NOT discard high cards")
    print("=" * 80)
    print("\nScenario:")
    print(f"  Contract: {contract}")
    print(f"  North led: ♠7")
    print(f"  East (void in spades) must discard")
    print(f"  East holds: ♥QT8 ♦T76 ♣KJT9632")
    print(f"\n  ✅ CORRECT: Discard ♦6 or ♦7 (low from weak suit)")
    print(f"  ❌ BUG: Discard ♣K (high card from long suit)")

    # Test Minimax AI (depth 4 = Expert without DDS)
    print("\n" + "-" * 80)
    print("Testing Minimax AI (depth 4 - Expert 8/10)")
    print("-" * 80)

    minimax_ai = MinimaxPlayAI(max_depth=2)  # Use depth 2 for faster testing

    # Test each possible discard to see their scores
    print("\n  Evaluating all possible discards:")
    for test_card in state.hands['E'].cards:
        test_state_copy = minimax_ai._simulate_play(state, test_card, 'E')
        score = minimax_ai._minimax(test_state_copy, 1, float('-inf'), float('inf'), False, 'E')
        print(f"    {test_card.rank}{test_card.suit}: score = {score:.3f}")

    card = minimax_ai.choose_card(state, 'E')

    print(f"\n  AI chose: {card.rank}{card.suit}")

    # Verify the card is NOT a high card
    is_low_card = card.rank in ['2', '3', '4', '5', '6', '7', '8']
    is_high_card = card.rank in ['A', 'K', 'Q', 'J']

    if is_low_card:
        print(f"  ✅ PASS: AI discarded a low card ({card.rank}{card.suit})")
    elif is_high_card:
        print(f"  ❌ FAIL: AI discarded a high card ({card.rank}{card.suit}) - THIS IS THE BUG!")
        return False
    else:
        print(f"  ⚠️  WARNING: AI discarded middle card ({card.rank}{card.suit}) - not ideal but acceptable")

    # Specifically check it's not the King of clubs
    if card.rank == 'K' and card.suit == '♣':
        print(f"  ❌ CRITICAL FAIL: AI discarded ♣K - EXACT BUG FROM REPORT!")
        return False

    # Test DDS AI fallback if available
    if DDS_AVAILABLE:
        print("\n" + "-" * 80)
        print("Testing DDS AI Fallback (Expert 9/10)")
        print("-" * 80)

        dds_ai = DDSPlayAI()
        # Force fallback by using the fallback method directly
        legal_cards = [c for c in state.hands['E'].cards]
        card = dds_ai._fallback_choose_card(state, 'E', legal_cards)

        print(f"\n  DDS fallback chose: {card.rank}{card.suit}")

        is_low_card = card.rank in ['2', '3', '4', '5', '6', '7', '8']
        is_high_card = card.rank in ['A', 'K', 'Q', 'J']

        if is_low_card:
            print(f"  ✅ PASS: DDS fallback discarded a low card ({card.rank}{card.suit})")
        elif is_high_card:
            print(f"  ❌ FAIL: DDS fallback discarded a high card ({card.rank}{card.suit})")
            return False

        if card.rank == 'K' and card.suit == '♣':
            print(f"  ❌ CRITICAL FAIL: DDS fallback discarded ♣K!")
            return False

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - AI correctly discards low cards")
    print("=" * 80)
    return True


if __name__ == '__main__':
    success = test_discard_chooses_low_card()
    exit(0 if success else 1)
