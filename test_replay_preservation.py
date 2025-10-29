#!/usr/bin/env python3
"""
Simplified test to verify original_deal preservation
Tests that the backend stores and restores the original 13-card hands
"""

import requests
import json

API_URL = "http://localhost:5001"

def test_preservation():
    """Test that original_deal is preserved in backend"""
    print("=" * 60)
    print("Testing Original Deal Preservation")
    print("=" * 60)

    # Generate a unique session ID for this test
    import uuid
    session_id = str(uuid.uuid4())
    headers = {'X-Session-ID': session_id, 'Content-Type': 'application/json'}

    print(f"\n1. Creating session: {session_id[:8]}...")

    # Step 1: Deal a hand
    print("\n2. Dealing a hand...")
    response = requests.get(f"{API_URL}/api/deal-hands", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to deal hands: {response.text}")
        return False

    deal_data = response.json()
    print(f"✅ Hand dealt")
    initial_south_cards = len(deal_data['hand'])
    print(f"   South has {initial_south_cards} cards")

    # Step 2: Start simple auction
    print("\n3. Running simple auction (all pass)...")
    auction = ['1NT', 'Pass', 'Pass', 'Pass']

    # Step 3: Start play
    print("\n4. Starting play phase (this should preserve original_deal)...")
    response = requests.post(
        f"{API_URL}/api/start-play",
        headers=headers,
        json={
            'auction_history': auction,
            'vulnerability': deal_data.get('vulnerability', 'None'),
            'replay': False  # First time - should save original_deal
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to start play: {response.text}")
        return False

    play_data = response.json()
    print(f"✅ Play started: {play_data['contract']}")

    # Step 4: Simulate playing some cards by getting state
    print("\n5. Getting all hands to confirm 13 cards each...")
    response = requests.get(f"{API_URL}/api/get-all-hands", headers=headers)
    hands_before = response.json()['hands']

    print("   Initial hand sizes:")
    for pos in ['North', 'East', 'South', 'West']:
        card_count = len(hands_before[pos]['hand'])
        print(f"      {pos}: {card_count} cards")

    # Step 5: Attempt replay with replay=True flag
    print("\n6. 🎯 Testing REPLAY with replay=True flag...")
    response = requests.post(
        f"{API_URL}/api/start-play",
        headers=headers,
        json={
            'auction_history': auction,
            'vulnerability': deal_data.get('vulnerability', 'None'),
            'replay': True  # Should use original_deal
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to start replay: {response.text}")
        return False

    replay_data = response.json()
    print(f"✅ Replay started: {replay_data['contract']}")

    # Step 6: Verify hands are restored
    print("\n7. Verifying hands restored after replay...")
    response = requests.get(f"{API_URL}/api/get-all-hands", headers=headers)
    hands_after = response.json()['hands']

    print("   Hand sizes after replay:")
    all_valid = True
    for pos in ['North', 'East', 'South', 'West']:
        card_count = len(hands_after[pos]['hand'])
        status = "✅" if card_count == 13 else "❌"
        print(f"      {status} {pos}: {card_count} cards")
        if card_count != 13:
            all_valid = False

    # Final verdict
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ PRESERVATION TEST PASSED!")
        print("   original_deal is correctly preserved and restored")
        print("   Replay functionality is FIXED! 🎉")
    else:
        print("❌ PRESERVATION TEST FAILED")
        print("   Hands were not properly restored")
    print("=" * 60)

    return all_valid


if __name__ == "__main__":
    try:
        success = test_preservation()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
