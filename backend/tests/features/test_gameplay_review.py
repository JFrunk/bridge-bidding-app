#!/usr/bin/env python3
"""
Test script for AI Review feature during gameplay phase
Tests that gameplay data (contract, tricks, card play) is captured correctly
"""

import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_gameplay_review():
    print("="*60)
    print("Testing AI Review Feature During Gameplay Phase")
    print("="*60)
    print()

    # Step 1: Deal a new hand
    print("1. Dealing a new hand...")
    response = requests.get(f"{BASE_URL}/api/deal-hands")
    if response.status_code != 200:
        print(f"❌ Failed to deal hands: {response.status_code}")
        return False
    print("✅ Hands dealt successfully")
    print()

    # Step 2: Simulate a simple auction to reach a contract
    print("2. Simulating auction to reach a contract...")
    auction = []
    players = ['North', 'East', 'South', 'West']
    next_player_idx = 0

    # Simple auction: 1NT - Pass - 3NT - Pass - Pass - Pass
    test_auction = [
        ('North', '1NT'),
        ('East', 'Pass'),
        ('South', '3NT'),
        ('West', 'Pass'),
        ('North', 'Pass'),
        ('East', 'Pass')
    ]

    for player, bid_str in test_auction:
        response = requests.post(f"{BASE_URL}/api/get-next-bid", json={
            'auction_history': auction,
            'current_player': player
        })

        if response.status_code == 200:
            data = response.json()
            ai_bid = data['bid']
            explanation = data['explanation']

            # For this test, we'll use our predetermined bids
            # In a real scenario, we'd use the AI's bid
            auction.append({'bid': bid_str, 'explanation': f'{player} bid {bid_str}'})
            print(f"   {player}: {bid_str}")
        else:
            print(f"❌ Failed to get bid for {player}")
            return False

    print("✅ Auction complete: 1NT - Pass - 3NT - Pass - Pass - Pass")
    print()

    # Step 3: Start play phase
    print("3. Starting play phase...")
    response = requests.post(f"{BASE_URL}/api/start-play", json={
        'auction_history': [a['bid'] for a in auction],
        'vulnerability': 'None'
    })

    if response.status_code != 200:
        print(f"❌ Failed to start play phase: {response.text}")
        return False

    play_data = response.json()
    print(f"✅ Play phase started")
    print(f"   Contract: {play_data['contract']}")
    print(f"   Declarer: {play_data['contract_details']['declarer']}")
    print(f"   Opening leader: {play_data['opening_leader']}")
    print(f"   Dummy: {play_data['dummy']}")
    print()

    # Step 4: Play a few cards to generate trick history
    print("4. Playing a few cards to generate trick history...")

    # Let AI play opening lead
    response = requests.post(f"{BASE_URL}/api/get-ai-play", json={})
    if response.status_code != 200:
        print(f"❌ Failed AI play: {response.text}")
        return False

    ai_play = response.json()
    print(f"   {ai_play['position']} played {ai_play['card']['rank']}{ai_play['card']['suit']}")

    # Play a few more cards with AI
    for i in range(3):
        response = requests.post(f"{BASE_URL}/api/get-ai-play", json={})
        if response.status_code == 200:
            ai_play = response.json()
            print(f"   {ai_play['position']} played {ai_play['card']['rank']}{ai_play['card']['suit']}")

            if ai_play.get('trick_complete'):
                print(f"   🎯 Trick complete! Winner: {ai_play['trick_winner']}")
                # Clear the trick
                requests.post(f"{BASE_URL}/api/clear-trick", json={})
                print()

    print("✅ Several cards played successfully")
    print()

    # Step 5: Get current play state
    print("5. Getting current play state...")
    response = requests.get(f"{BASE_URL}/api/get-play-state")
    if response.status_code != 200:
        print(f"❌ Failed to get play state: {response.text}")
        return False

    play_state = response.json()
    print(f"✅ Play state retrieved")
    print(f"   Tricks won: N={play_state['tricks_won']['N']}, E={play_state['tricks_won']['E']}, "
          f"S={play_state['tricks_won']['S']}, W={play_state['tricks_won']['W']}")
    print(f"   Current trick: {len(play_state['current_trick'])} cards")
    print()

    # Step 6: Request AI review during gameplay phase
    print("6. Requesting AI review during gameplay phase...")
    response = requests.post(f"{BASE_URL}/api/request-review", json={
        'auction_history': auction,
        'user_concern': 'Was the opening lead correct? What about declarer\'s plan?',
        'game_phase': 'playing'
    })

    if response.status_code != 200:
        print(f"❌ Failed to request review: {response.text}")
        return False

    review_data = response.json()
    print(f"✅ Review request saved successfully")
    print(f"   Filename: {review_data['filename']}")
    print()

    # Step 7: Read and validate the saved review file
    print("7. Validating saved review file...")
    if review_data.get('saved_to_file'):
        filepath = os.path.join('review_requests', review_data['filename'])

        if not os.path.exists(filepath):
            print(f"❌ Review file not found: {filepath}")
            return False

        with open(filepath, 'r') as f:
            saved_review = json.load(f)

        print(f"✅ Review file loaded successfully")
        print()
        print("   Checking required fields...")

        required_fields = [
            'timestamp',
            'game_phase',
            'all_hands',
            'auction',
            'vulnerability',
            'user_concern',
            'play_data'
        ]

        for field in required_fields:
            if field in saved_review:
                print(f"   ✅ {field}: present")
            else:
                print(f"   ❌ {field}: MISSING")
                return False

        # Validate play_data structure
        print()
        print("   Checking play_data structure...")
        play_data_fields = [
            'contract',
            'dummy',
            'opening_leader',
            'trick_history',
            'current_trick',
            'tricks_won',
            'tricks_taken_ns',
            'tricks_taken_ew',
            'next_to_play',
            'dummy_revealed',
            'is_complete'
        ]

        for field in play_data_fields:
            if field in saved_review['play_data']:
                value = saved_review['play_data'][field]
                print(f"   ✅ play_data.{field}: {value if not isinstance(value, (list, dict)) else type(value).__name__}")
            else:
                print(f"   ❌ play_data.{field}: MISSING")
                return False

        # Show summary statistics
        print()
        print("   📊 Review Data Summary:")
        print(f"      Game Phase: {saved_review['game_phase']}")
        print(f"      Contract: {saved_review['play_data']['contract']['string']}")
        print(f"      Tricks Played: {len(saved_review['play_data']['trick_history'])}")
        print(f"      Current Trick Cards: {len(saved_review['play_data']['current_trick'])}")
        print(f"      Tricks NS: {saved_review['play_data']['tricks_taken_ns']}")
        print(f"      Tricks EW: {saved_review['play_data']['tricks_taken_ew']}")
        print(f"      User Concern: '{saved_review['user_concern']}'")
        print()

        # Show sample of trick history
        if saved_review['play_data']['trick_history']:
            print("   📝 Sample Trick from History:")
            first_trick = saved_review['play_data']['trick_history'][0]
            print(f"      Leader: {first_trick['leader']}")
            print(f"      Winner: {first_trick['winner']}")
            print(f"      Cards played:")
            for card_play in first_trick['cards']:
                card = card_play['card']
                player = card_play['player']
                print(f"         {player}: {card['rank']}{card['suit']}")
            print()

    else:
        print("⚠️  File not saved (running on Render), but review_data is in response")
        print(f"   Review data keys: {list(review_data.get('review_data', {}).keys())}")
        print()

    print("="*60)
    print("✅ All tests passed! AI Review captures gameplay data correctly")
    print("="*60)
    return True


if __name__ == "__main__":
    try:
        success = test_gameplay_review()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
