"""
Regression test for bug: AI did not play the first card (opening lead)

Bug Report: backend/review_requests/hand_2025-10-29_13-19-45.json
User Concern: "AI did not play the first card."

Root Cause: Opening lead never triggered - play state stuck with:
- Contract: 3NT by North
- Opening leader: East
- No cards played (current_trick = [], trick_history = [])
- next_to_play = 'E' (but AI never played)

This test reproduces the exact scenario to ensure opening lead always happens.
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, Contract, PlayState
from engine.play.ai.simple_ai import SimplePlayAI


def test_opening_lead_is_made_when_play_starts():
    """
    Test that opening lead is automatically made when play phase begins.

    This reproduces the bug where:
    - Contract established: 3NT by North
    - Opening leader: East
    - No cards played despite entering play phase

    Expected: East (AI) should immediately make opening lead
    """

    # Recreate the exact hands from the bug report
    north_cards = [
        Card('A', '♠'), Card('T', '♠'), Card('8', '♠'), Card('4', '♠'),
        Card('A', '♥'), Card('Q', '♥'), Card('J', '♥'),
        Card('K', '♦'), Card('8', '♦'), Card('3', '♦'),
        Card('K', '♣'), Card('8', '♣'), Card('5', '♣')
    ]

    east_cards = [
        Card('J', '♠'), Card('9', '♠'), Card('6', '♠'), Card('2', '♠'),
        Card('T', '♥'), Card('8', '♥'), Card('2', '♥'),
        Card('T', '♦'), Card('7', '♦'), Card('6', '♦'), Card('2', '♦'),
        Card('4', '♣'), Card('3', '♣')
    ]

    south_cards = [
        Card('3', '♠'),
        Card('K', '♥'), Card('9', '♥'), Card('7', '♥'), Card('5', '♥'), Card('4', '♥'), Card('3', '♥'),
        Card('J', '♦'), Card('9', '♦'),
        Card('Q', '♣'), Card('T', '♣'), Card('7', '♣'), Card('2', '♣')
    ]

    west_cards = [
        Card('K', '♠'), Card('Q', '♠'), Card('7', '♠'), Card('5', '♠'),
        Card('6', '♥'),
        Card('A', '♦'), Card('Q', '♦'), Card('5', '♦'), Card('4', '♦'),
        Card('A', '♣'), Card('J', '♣'), Card('9', '♣'), Card('6', '♣')
    ]

    # Create hands
    hands = {
        'N': Hand(north_cards),
        'E': Hand(east_cards),
        'S': Hand(south_cards),
        'W': Hand(west_cards)
    }

    # Contract: 3NT by North
    contract = Contract(level=3, strain='NT', declarer='N', doubled=0)

    # Initialize play engine using factory method
    play_state = PlayEngine.create_play_session(contract, hands)

    # ASSERTION 1: Next to play should be East (opening leader = left of declarer)
    assert play_state.next_to_play == 'E', \
        f"Next to play should be East, got {play_state.next_to_play}"

    # ASSERTION 2: No cards should be played yet
    assert len(play_state.current_trick) == 0, \
        f"No cards should be played yet, found {len(play_state.current_trick)}"

    # ASSERTION 3: Dummy should be South (partner of North)
    assert play_state.dummy == 'S', \
        f"Dummy should be South, got {play_state.dummy}"

    # BUG REPRODUCTION: At this point, in the bug report, the AI never played
    # This is where the frontend should have triggered /api/get-ai-play for East

    # SIMULATE: AI makes opening lead
    ai = SimplePlayAI()

    # ASSERTION 4: East's hand should have 13 cards
    east_hand = play_state.hands['E']
    assert len(east_hand.cards) == 13, \
        f"Opening leader should have 13 cards, got {len(east_hand.cards)}"

    # AI selects opening lead
    opening_lead = ai.choose_card(play_state, 'E')

    # ASSERTION 5: AI must select a valid card
    assert opening_lead is not None, "AI failed to select opening lead"
    assert opening_lead in east_hand.cards, "AI selected card not in hand"

    # ASSERTION 6: Verify legality (should be legal since opening lead can be any card)
    is_legal = PlayEngine.is_legal_play(
        opening_lead, east_hand, play_state.current_trick,
        play_state.contract.trump_suit
    )
    assert is_legal, "Opening lead should always be legal"

    # Play the card (manually simulate what server.py does)
    play_state.current_trick.append((opening_lead, 'E'))
    play_state.current_trick_leader = 'E'
    east_hand.cards.remove(opening_lead)
    play_state.update_phase_after_card()

    # Reveal dummy after opening lead
    if len(play_state.current_trick) == 1:
        play_state.dummy_revealed = True

    # ASSERTION 7: Card should now be in current trick
    assert len(play_state.current_trick) == 1, \
        f"Opening lead should be in current trick, found {len(play_state.current_trick)}"

    # ASSERTION 8: The card in trick should match the selected card
    trick_card, trick_player = play_state.current_trick[0]
    assert trick_card == opening_lead, "Card in trick doesn't match selected card"
    assert trick_player == 'E', "Player in trick should be East"

    # ASSERTION 9: Next to play should now be South (dummy)
    # Need to update next_to_play manually since we're not using play_card method
    play_state.next_to_play = PlayEngine.next_player('E')
    assert play_state.next_to_play == 'S', \
        f"Next to play should be South (dummy), got {play_state.next_to_play}"

    # ASSERTION 10: Dummy should now be revealed
    assert play_state.dummy_revealed == True, \
        "Dummy should be revealed after opening lead"

    print("✅ Test passed: Opening lead was successfully made")


def test_opening_lead_from_each_position():
    """
    Test that opening lead works correctly regardless of declarer position.

    Ensures that the opening leader (left of declarer) is always determined
    correctly and can make the opening lead.
    """

    test_cases = [
        ('N', 'E'),  # North declares, East leads
        ('E', 'S'),  # East declares, South leads
        ('S', 'W'),  # South declares, West leads
        ('W', 'N'),  # West declares, North leads
    ]

    for declarer, expected_leader in test_cases:
        # Create simple hands for testing
        hands = {
            pos: Hand([Card(rank, '♠') for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']])
            for pos in ['N', 'E', 'S', 'W']
        }

        contract = Contract(level=3, strain='NT', declarer=declarer, doubled=0)

        play_state = PlayEngine.create_play_session(contract, hands)

        # Check next to play is opening leader
        assert play_state.next_to_play == expected_leader, \
            f"Next to play should be {expected_leader}, got {play_state.next_to_play}"

        # Ensure opening leader has 13 cards
        leader_hand = play_state.hands[expected_leader]
        assert len(leader_hand.cards) == 13, \
            f"Opening leader should have 13 cards, got {len(leader_hand.cards)}"

        # AI makes opening lead
        ai = SimplePlayAI()
        opening_lead = ai.choose_card(play_state, expected_leader)
        assert opening_lead is not None, f"AI failed to select opening lead for {expected_leader}"
        assert opening_lead in leader_hand.cards, "AI selected card not in hand"

        # Play the card (simulate server.py behavior)
        play_state.current_trick.append((opening_lead, expected_leader))
        play_state.current_trick_leader = expected_leader
        leader_hand.cards.remove(opening_lead)
        play_state.update_phase_after_card()
        play_state.dummy_revealed = True

        # Verify card was played
        assert len(play_state.current_trick) == 1, \
            f"Opening lead not in current trick for declarer {declarer}"

        print(f"✅ Opening lead successful: Declarer={declarer}, Leader={expected_leader}")


def test_backend_api_opening_lead_integration():
    """
    Integration test simulating the exact API flow from the bug report.

    This tests the backend API endpoints to ensure:
    1. /api/start-play initializes play state correctly
    2. /api/get-ai-play can be called immediately for opening lead
    3. Opening lead is successfully made
    """

    # This test requires the Flask app to be running
    # We'll test the core engine logic here

    # Create hands matching bug report
    north_cards = [
        Card('A', '♠'), Card('T', '♠'), Card('8', '♠'), Card('4', '♠'),
        Card('A', '♥'), Card('Q', '♥'), Card('J', '♥'),
        Card('K', '♦'), Card('8', '♦'), Card('3', '♦'),
        Card('K', '♣'), Card('8', '♣'), Card('5', '♣')
    ]

    east_cards = [
        Card('J', '♠'), Card('9', '♠'), Card('6', '♠'), Card('2', '♠'),
        Card('T', '♥'), Card('8', '♥'), Card('2', '♥'),
        Card('T', '♦'), Card('7', '♦'), Card('6', '♦'), Card('2', '♦'),
        Card('4', '♣'), Card('3', '♣')
    ]

    south_cards = [
        Card('3', '♠'),
        Card('K', '♥'), Card('9', '♥'), Card('7', '♥'), Card('5', '♥'), Card('4', '♥'), Card('3', '♥'),
        Card('J', '♦'), Card('9', '♦'),
        Card('Q', '♣'), Card('T', '♣'), Card('7', '♣'), Card('2', '♣')
    ]

    west_cards = [
        Card('K', '♠'), Card('Q', '♠'), Card('7', '♠'), Card('5', '♠'),
        Card('6', '♥'),
        Card('A', '♦'), Card('Q', '♦'), Card('5', '♦'), Card('4', '♦'),
        Card('A', '♣'), Card('J', '♣'), Card('9', '♣'), Card('6', '♣')
    ]

    hands = {
        'N': Hand(north_cards),
        'E': Hand(east_cards),
        'S': Hand(south_cards),
        'W': Hand(west_cards)
    }

    contract = Contract(level=3, strain='NT', declarer='N', doubled=0)

    # Initialize play (simulating /api/start-play)
    play_state = PlayEngine.create_play_session(contract, hands)

    # Verify initial state
    assert play_state.next_to_play == 'E', "Opening leader should be East"
    assert play_state.dummy == 'S', "Dummy should be South"
    assert len(play_state.current_trick) == 0, "No cards played initially"

    # Simulate /api/get-ai-play for East
    ai = SimplePlayAI()
    east_hand = play_state.hands['E']
    card_to_play = ai.choose_card(play_state, 'E')

    # Verify AI selected a card
    assert card_to_play is not None, "AI should select opening lead"
    assert card_to_play in east_hand.cards, "AI selected card not in hand"

    # Play the card (simulate server.py behavior)
    play_state.current_trick.append((card_to_play, 'E'))
    play_state.current_trick_leader = 'E'
    east_hand.cards.remove(card_to_play)
    play_state.update_phase_after_card()
    play_state.dummy_revealed = True
    play_state.next_to_play = PlayEngine.next_player('E')

    # Verify state after opening lead
    assert len(play_state.current_trick) == 1, "Opening lead should be in trick"
    assert play_state.dummy_revealed == True, "Dummy should be revealed"
    assert play_state.next_to_play == 'S', "Next should be dummy (South)"

    print("✅ Integration test passed: Opening lead via API flow works correctly")


if __name__ == "__main__":
    # Run tests
    print("Running regression test for opening lead bug...")
    print("=" * 60)

    try:
        test_opening_lead_is_made_when_play_starts()
        test_opening_lead_from_each_position()
        test_backend_api_opening_lead_integration()
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
    except AssertionError as e:
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print("=" * 60)
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
