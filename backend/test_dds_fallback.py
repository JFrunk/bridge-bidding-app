#!/usr/bin/env python3
"""
Test DDS AI fallback mechanism
Verifies that DDS AI gracefully handles crashes and falls back to heuristic play
"""

from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE
from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract
import sys

def create_test_state():
    """Create a simple test state for card play"""
    # Create hands for all positions
    hands = {
        'N': Hand([Card('A', '♠'), Card('K', '♥'), Card('Q', '♦'), Card('J', '♣')]),
        'E': Hand([Card('2', '♠'), Card('3', '♥'), Card('4', '♦'), Card('5', '♣')]),
        'S': Hand([Card('6', '♠'), Card('7', '♥'), Card('8', '♦'), Card('9', '♣')]),
        'W': Hand([Card('T', '♠'), Card('9', '♥'), Card('8', '♦'), Card('7', '♣')])
    }

    # Create a simple 1NT contract by South
    contract = Contract(level=1, strain='NT', declarer='S', doubled=0)

    # Create play state
    state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[],
        tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
        trick_history=[],
        next_to_play='W',  # West leads
        dummy_revealed=False
    )

    return state

def test_dds_fallback():
    """Test that DDS AI can handle errors gracefully"""
    print("=" * 60)
    print("Testing DDS AI Fallback Mechanism")
    print("=" * 60)

    if not DDS_AVAILABLE:
        print("❌ DDS not available - cannot test")
        return False

    print(f"✓ DDS library available")

    # Create AI instance
    try:
        ai = DDSPlayAI()
        print(f"✓ DDS AI initialized: {ai.get_name()}")
    except Exception as e:
        print(f"❌ Failed to initialize DDS AI: {e}")
        return False

    # Create test state
    state = create_test_state()
    print(f"✓ Test state created: {state.contract}")

    # Try to choose a card
    print("\nAttempting to choose card for West (opening leader)...")
    try:
        card = ai.choose_card(state, 'W')
        print(f"✓ AI successfully chose card: {card.rank}{card.suit}")

        # Verify it's a legal card
        legal_cards = [c for c in state.hands['W'].cards]
        if card in legal_cards:
            print(f"✓ Card is legal")
        else:
            print(f"❌ Card {card.rank}{card.suit} is not in West's hand!")
            return False

        return True

    except Exception as e:
        print(f"❌ AI failed to choose card: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_directly():
    """Test the fallback method directly"""
    print("\n" + "=" * 60)
    print("Testing Fallback Method Directly")
    print("=" * 60)

    if not DDS_AVAILABLE:
        print("❌ DDS not available - cannot test")
        return False

    ai = DDSPlayAI()
    state = create_test_state()
    legal_cards = list(state.hands['W'].cards)

    print(f"Legal cards for West: {[f'{c.rank}{c.suit}' for c in legal_cards]}")

    try:
        card = ai._fallback_choose_card(state, 'W', legal_cards)
        print(f"✓ Fallback chose: {card.rank}{card.suit}")

        if card in legal_cards:
            print(f"✓ Fallback card is legal")
            return True
        else:
            print(f"❌ Fallback card not in legal cards!")
            return False

    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n🧪 DDS AI Fallback Test Suite\n")

    results = []

    # Test 1: Normal operation
    results.append(("DDS AI Normal Operation", test_dds_fallback()))

    # Test 2: Fallback method
    results.append(("Fallback Method", test_fallback_directly()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
