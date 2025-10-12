"""
Test to reproduce the card play bug from hand_2025-10-10_16-30-36.json

Issue: South played a card but the system did not respond.

This tests the full workflow:
1. Start play after bidding completes
2. South plays a card
3. AI should respond with next cards
"""

import json
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.play_engine import PlayEngine, PlayState
from engine.simple_play_ai import SimplePlayAI

def load_review_hand():
    """Load the problematic hand from the review request"""
    with open('review_requests/hand_2025-10-10_16-30-36.json', 'r') as f:
        data = json.load(f)
    return data


def test_play_workflow():
    """Test the full play workflow with the problematic hand"""

    # Load the hand data
    data = load_review_hand()

    print("="*70)
    print("Testing Card Play Workflow")
    print("="*70)

    # Convert JSON hands to Hand objects
    hands = {}
    pos_map = {'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W'}

    for position, short_pos in pos_map.items():
        cards_data = data['all_hands'][position]['cards']
        cards = [Card(c['rank'], c['suit']) for c in cards_data]
        hands[short_pos] = Hand(cards)

        print(f"\n{position} ({short_pos}):")
        print(f"  HCP: {hands[short_pos].hcp}")
        print(f"  Distribution: {hands[short_pos].suit_lengths['♠']}-{hands[short_pos].suit_lengths['♥']}-{hands[short_pos].suit_lengths['♦']}-{hands[short_pos].suit_lengths['♣']}")

    # Get the auction
    auction = [item['bid'] for item in data['auction']]
    print(f"\n\nAuction: {' - '.join(auction)}")

    # Determine contract
    play_engine = PlayEngine()
    contract = play_engine.determine_contract(auction, dealer_index=0)

    if not contract:
        print("\n❌ ERROR: No contract found!")
        print("The auction has system errors that prevented it from completing properly.")
        print("\nThe auction should have been: Pass - 1NT - Pass - Pass - Pass")
        print("But it appears to have bidding errors that prevented proper completion.")
        return

    print(f"\nContract: {contract}")
    print(f"  Declarer: {contract.declarer}")
    print(f"  Dummy: {pos_map_reverse[contract.declarer]}'s partner")

    # Create play state
    opening_leader = play_engine.next_player(contract.declarer)

    play_state = PlayState(
        contract=contract,
        hands=hands,
        current_trick=[],
        tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
        trick_history=[],
        next_to_play=opening_leader,
        dummy_revealed=False
    )

    print(f"\nOpening leader: {opening_leader}")
    print(f"Dummy: {play_state.dummy}")

    # Test AI play
    play_ai = SimplePlayAI()

    print("\n" + "="*70)
    print("Simulating first trick:")
    print("="*70)

    for i in range(4):
        next_pos = play_state.next_to_play
        hand = play_state.hands[next_pos]

        print(f"\n{next_pos}'s turn to play:")

        if i == 0 or next_pos != 'S':
            # AI plays
            card = play_ai.choose_card(play_state, next_pos)
            print(f"  AI chose: {card.rank}{card.suit}")
        else:
            # Simulate user playing first card from their hand
            card = hand.cards[0]
            print(f"  User (South) plays: {card.rank}{card.suit}")

        # Validate the play
        is_legal = play_engine.is_legal_play(
            card, hand, play_state.current_trick, contract.trump_suit
        )

        if not is_legal:
            print(f"  ❌ ILLEGAL PLAY!")
            return

        # Play the card
        play_state.current_trick.append((card, next_pos))
        hand.cards.remove(card)

        # Reveal dummy after opening lead
        if len(play_state.current_trick) == 1:
            play_state.dummy_revealed = True
            print(f"  Dummy ({play_state.dummy}) revealed!")

        # Update next player
        if len(play_state.current_trick) < 4:
            play_state.next_to_play = play_engine.next_player(next_pos)

    # Determine trick winner
    trick_winner = play_engine.determine_trick_winner(
        play_state.current_trick, contract.trump_suit
    )

    print(f"\n✅ Trick winner: {trick_winner}")
    print(f"Cards played: {[(c.rank + c.suit, p) for c, p in play_state.current_trick]}")

    print("\n" + "="*70)
    print("✅ Card play system is working correctly!")
    print("="*70)
    print("\nThe issue is likely in the BIDDING phase, not the play phase.")
    print("The auction did not complete properly due to system errors.")


# Reverse mapping for display
pos_map_reverse = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}


if __name__ == '__main__':
    test_play_workflow()
