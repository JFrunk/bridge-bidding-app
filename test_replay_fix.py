#!/usr/bin/env python3
"""
Test script to verify replay functionality fix
Tests that original_deal is preserved and used during replay
"""

import requests
import json

API_URL = "http://localhost:5001"

def test_replay_fix():
    """Test that replay uses preserved original_deal"""
    print("=" * 60)
    print("Testing Replay Functionality Fix")
    print("=" * 60)

    # Generate a unique session ID for this test
    import uuid
    session_id = str(uuid.uuid4())
    headers = {'X-Session-ID': session_id, 'Content-Type': 'application/json'}

    print(f"\n1. Creating new session: {session_id[:8]}...")

    # Step 1: Play a random hand
    print("\n2. Starting a random hand (AI bids all positions)...")
    response = requests.post(f"{API_URL}/api/play-random-hand", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create random hand: {response.text}")
        return False

    data = response.json()
    print(f"✅ Random hand created: {data['contract']}")
    print(f"   Opening leader: {data['opening_leader']}")

    # Step 2: Get initial play state
    print("\n3. Getting initial play state...")
    response = requests.get(f"{API_URL}/api/get-play-state", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get play state: {response.text}")
        return False

    initial_state = response.json()
    print(f"✅ Initial state retrieved")
    print(f"   Next to play: {initial_state['next_to_play']}")

    # Step 3: Play out all 13 tricks using AI
    print("\n4. Playing all 13 tricks with AI...")
    tricks_played = 0
    max_plays = 52  # 13 tricks * 4 players

    for i in range(max_plays):
        # Get current state
        response = requests.get(f"{API_URL}/api/get-play-state", headers=headers)
        state = response.json()

        # Check if complete
        total_tricks = sum(state['tricks_won'].values())
        if total_tricks >= 13:
            print(f"✅ All 13 tricks completed")
            break

        # AI plays next card
        next_player = state['next_to_play']
        response = requests.post(
            f"{API_URL}/api/get-ai-play",
            headers=headers,
            json={'position': next_player}
        )

        if response.status_code != 200:
            print(f"❌ AI play failed: {response.text}")
            return False

        play_data = response.json()

        # If trick complete, clear it
        if play_data.get('trick_complete'):
            requests.post(f"{API_URL}/api/clear-trick", headers=headers)
            tricks_played += 1
            print(f"   Trick {tricks_played} completed")

    # Step 4: Complete the play
    print("\n5. Completing play and getting score...")
    response = requests.post(
        f"{API_URL}/api/complete-play",
        headers=headers,
        json={'vulnerability': data.get('vulnerability', 'None')}
    )

    if response.status_code != 200:
        print(f"❌ Failed to complete play: {response.text}")
        return False

    score_data = response.json()
    print(f"✅ Play completed")
    print(f"   Result: {score_data.get('result', 'Unknown')}")

    # Step 5: Get all hands to verify they're empty
    print("\n6. Verifying hands are empty after play...")
    response = requests.get(f"{API_URL}/api/get-all-hands", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get all hands: {response.text}")
        return False

    hands_after_play = response.json()
    for pos in ['N', 'E', 'S', 'W']:
        pos_full = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}[pos]
        card_count = len(hands_after_play['hands'][pos_full]['hand'])
        print(f"   {pos_full}: {card_count} cards remaining")

    # Step 6: Replay the hand
    print("\n7. 🎯 REPLAY TEST: Starting replay with replay=true flag...")
    response = requests.post(
        f"{API_URL}/api/start-play",
        headers=headers,
        json={
            'auction_history': [b['bid'] for b in data.get('auction', [])],
            'vulnerability': data.get('vulnerability', 'None'),
            'replay': True  # This should trigger use of original_deal
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to start replay: {response.text}")
        return False

    replay_data = response.json()
    print(f"✅ Replay started successfully!")
    print(f"   Contract: {replay_data['contract']}")

    # Step 7: Get play state after replay to verify hands are restored
    print("\n8. Verifying hands are restored after replay...")
    response = requests.get(f"{API_URL}/api/get-all-hands", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get all hands after replay: {response.text}")
        return False

    hands_after_replay = response.json()
    all_hands_valid = True
    for pos in ['N', 'E', 'S', 'W']:
        pos_full = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}[pos]
        card_count = len(hands_after_replay['hands'][pos_full]['hand'])
        status = "✅" if card_count == 13 else "❌"
        print(f"   {status} {pos_full}: {card_count} cards")
        if card_count != 13:
            all_hands_valid = False

    # Final verdict
    print("\n" + "=" * 60)
    if all_hands_valid:
        print("✅ REPLAY FIX SUCCESSFUL!")
        print("   All hands correctly restored to 13 cards each")
        print("   The 'Position W has no cards' bug is FIXED! 🎉")
    else:
        print("❌ REPLAY FIX FAILED")
        print("   Hands were not properly restored")
    print("=" * 60)

    return all_hands_valid


if __name__ == "__main__":
    try:
        success = test_replay_fix()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
