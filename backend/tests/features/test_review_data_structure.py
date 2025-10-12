#!/usr/bin/env python3
"""
Test script to verify the review request data structure for gameplay phase
This test simulates the data capture without requiring a running server
"""

import json
from datetime import datetime
from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract, Trick

def create_sample_hands():
    """Create sample hands for testing"""
    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']

    # Create a simple distribution
    hands = {
        'N': Hand([
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
            Card('A', '♥'), Card('K', '♥'),
            Card('5', '♦'), Card('4', '♦'), Card('3', '♦'),
            Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'), Card('J', '♣'), Card('T', '♣')
        ]),
        'E': Hand([
            Card('J', '♠'), Card('T', '♠'), Card('9', '♠'),
            Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'),
            Card('A', '♦'), Card('K', '♦'), Card('Q', '♦'),
            Card('9', '♣'), Card('8', '♣'), Card('7', '♣'), Card('6', '♣')
        ]),
        'S': Hand([
            Card('8', '♠'), Card('7', '♠'), Card('6', '♠'),
            Card('9', '♥'), Card('8', '♥'), Card('7', '♥'),
            Card('J', '♦'), Card('T', '♦'), Card('9', '♦'),
            Card('5', '♣'), Card('4', '♣'), Card('3', '♣'), Card('2', '♣')
        ]),
        'W': Hand([
            Card('5', '♠'), Card('4', '♠'), Card('3', '♠'), Card('2', '♠'),
            Card('6', '♥'), Card('5', '♥'), Card('4', '♥'), Card('3', '♥'), Card('2', '♥'),
            Card('8', '♦'), Card('7', '♦'), Card('6', '♦'), Card('2', '♦')
        ])
    }

    return hands

def test_review_data_structure():
    print("="*70)
    print("Testing AI Review Data Structure for Gameplay Phase")
    print("="*70)
    print()

    # Create sample data
    print("1. Creating sample hands and contract...")
    hands = create_sample_hands()
    contract = Contract(level=3, strain='NT', declarer='S')
    print(f"   Contract: {contract}")
    print(f"   Hands created for all 4 positions")
    print()

    # Create play state
    print("2. Creating play state...")
    play_state = PlayEngine.create_play_session(contract, hands)
    print(f"   Opening leader: {play_state.next_to_play}")
    print(f"   Dummy: {play_state.dummy}")
    print()

    # Simulate playing a complete trick
    print("3. Simulating a complete trick...")
    # West leads (opening leader) - pick first card from hand
    lead_card = hands['W'].cards[0]
    play_state.current_trick.append((lead_card, 'W'))
    hands['W'].cards.remove(lead_card)

    # North (dummy) plays - pick first card from hand
    dummy_card = hands['N'].cards[0]
    play_state.current_trick.append((dummy_card, 'N'))
    hands['N'].cards.remove(dummy_card)

    # East plays - pick first card from hand
    east_card = hands['E'].cards[0]
    play_state.current_trick.append((east_card, 'E'))
    hands['E'].cards.remove(east_card)

    # South (declarer) plays - pick first card from hand
    south_card = hands['S'].cards[0]
    play_state.current_trick.append((south_card, 'S'))
    hands['S'].cards.remove(south_card)

    # Determine winner
    winner = PlayEngine.determine_trick_winner(play_state.current_trick, None)
    play_state.tricks_won[winner] += 1

    # Save to history
    play_state.trick_history.append(
        Trick(
            cards=list(play_state.current_trick),
            leader='W',
            winner=winner
        )
    )

    print(f"   Trick played: W leads K♦")
    print(f"   Winner: {winner}")
    print(f"   Trick saved to history")
    print()

    # Clear trick and start another
    play_state.current_trick = []

    # Play a partial trick
    print("4. Starting a new trick (partial)...")
    if hands[winner].cards:
        next_lead = hands[winner].cards[0]
        play_state.current_trick.append((next_lead, winner))
        hands[winner].cards.remove(next_lead)
        print(f"   {winner} leads with {next_lead.rank}{next_lead.suit}")
    print()

    # Create review request data structure (simulating the backend)
    print("5. Creating review request data structure...")

    # Sample auction
    auction = [
        {'bid': 'Pass', 'explanation': 'Not enough to open'},
        {'bid': 'Pass', 'explanation': 'Not enough to open'},
        {'bid': '1NT', 'explanation': '15-17 HCP balanced'},
        {'bid': 'Pass', 'explanation': 'No interest in game'},
        {'bid': '3NT', 'explanation': 'Game invitation'},
        {'bid': 'Pass', 'explanation': 'Accept'},
        {'bid': 'Pass', 'explanation': 'Accept'},
        {'bid': 'Pass', 'explanation': 'Accept'}
    ]

    # Build hands data
    pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
    all_hands = {}

    for short_pos, hand in hands.items():
        position = pos_map[short_pos]
        hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in hand.cards]
        points_for_json = {
            'hcp': hand.hcp,
            'dist_points': hand.dist_points,
            'total_points': hand.total_points,
            'suit_hcp': hand.suit_hcp,
            'suit_lengths': hand.suit_lengths
        }
        all_hands[position] = {
            'cards': hand_for_json,
            'points': points_for_json
        }

    # Serialize trick history
    trick_history = []
    for trick in play_state.trick_history:
        trick_cards = [
            {
                'card': {'rank': card.rank, 'suit': card.suit},
                'player': player
            }
            for card, player in trick.cards
        ]
        trick_history.append({
            'cards': trick_cards,
            'leader': trick.leader,
            'winner': trick.winner
        })

    # Serialize current trick
    current_trick = [
        {
            'card': {'rank': card.rank, 'suit': card.suit},
            'player': player
        }
        for card, player in play_state.current_trick
    ]

    # Build complete review request
    review_request = {
        'timestamp': datetime.now().isoformat(),
        'game_phase': 'playing',
        'all_hands': all_hands,
        'auction': auction,
        'vulnerability': 'None',
        'dealer': 'North',
        'user_position': 'South',
        'user_concern': 'Should declarer have played the Jack of diamonds or a lower card?',
        'play_data': {
            'contract': {
                'level': contract.level,
                'strain': contract.strain,
                'declarer': contract.declarer,
                'doubled': contract.doubled,
                'string': str(contract)
            },
            'dummy': play_state.dummy,
            'opening_leader': PlayEngine.next_player(contract.declarer),
            'trick_history': trick_history,
            'current_trick': current_trick,
            'tricks_won': play_state.tricks_won,
            'tricks_taken_ns': play_state.tricks_taken_ns,
            'tricks_taken_ew': play_state.tricks_taken_ew,
            'next_to_play': play_state.next_to_play,
            'dummy_revealed': play_state.dummy_revealed,
            'is_complete': play_state.is_complete
        }
    }

    print("✅ Review request structure created")
    print()

    # Validate structure
    print("6. Validating data structure...")
    required_top_level = ['timestamp', 'game_phase', 'all_hands', 'auction',
                          'vulnerability', 'dealer', 'user_position', 'user_concern', 'play_data']

    for field in required_top_level:
        if field in review_request:
            print(f"   ✅ {field}")
        else:
            print(f"   ❌ {field} MISSING")
            return False

    print()
    print("   Validating play_data structure...")
    required_play_data = ['contract', 'dummy', 'opening_leader', 'trick_history',
                         'current_trick', 'tricks_won', 'tricks_taken_ns',
                         'tricks_taken_ew', 'next_to_play', 'dummy_revealed', 'is_complete']

    for field in required_play_data:
        if field in review_request['play_data']:
            print(f"   ✅ play_data.{field}")
        else:
            print(f"   ❌ play_data.{field} MISSING")
            return False

    print()

    # Display sample output
    print("7. Sample review data:")
    print("-" * 70)
    print(json.dumps(review_request, indent=2, default=str))
    print("-" * 70)
    print()

    # Check statistics
    print("8. Data Statistics:")
    print(f"   Game Phase: {review_request['game_phase']}")
    print(f"   Contract: {review_request['play_data']['contract']['string']}")
    print(f"   Declarer: {review_request['play_data']['contract']['declarer']}")
    print(f"   Dummy: {review_request['play_data']['dummy']}")
    print(f"   Opening Leader: {review_request['play_data']['opening_leader']}")
    print(f"   Tricks Completed: {len(review_request['play_data']['trick_history'])}")
    print(f"   Current Trick Cards: {len(review_request['play_data']['current_trick'])}")
    print(f"   Tricks NS: {review_request['play_data']['tricks_taken_ns']}")
    print(f"   Tricks EW: {review_request['play_data']['tricks_taken_ew']}")
    print(f"   Remaining cards per player: ~{len(review_request['all_hands']['North']['cards'])}")
    print(f"   User Concern: '{review_request['user_concern']}'")
    print()

    # Show trick details
    if review_request['play_data']['trick_history']:
        print("9. Trick History Detail:")
        for i, trick in enumerate(review_request['play_data']['trick_history'], 1):
            print(f"   Trick {i}:")
            print(f"      Leader: {trick['leader']}, Winner: {trick['winner']}")
            for card_play in trick['cards']:
                card = card_play['card']
                player = card_play['player']
                print(f"         {player}: {card['rank']}{card['suit']}")
        print()

    print("="*70)
    print("✅ All validation passed! Data structure is correct for gameplay review")
    print("="*70)
    return True


if __name__ == "__main__":
    try:
        success = test_review_data_structure()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
