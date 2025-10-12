"""
Test script for card play Flask endpoints
Tests the new card play endpoints directly
"""
import requests
import json
from engine.hand import Hand, Card

BASE_URL = "http://localhost:5001/api"

def create_test_hand(cards_str):
    """Helper to create a hand from string like '♠AK5 ♥Q72 ♦A843 ♣K62'"""
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        for rank in part[1:]:
            cards.append(Card(rank, suit))
    return cards

def test_card_play_endpoints():
    """Test complete card play flow"""

    print("=" * 80)
    print("TESTING CARD PLAY ENDPOINTS")
    print("=" * 80)

    # Create test hands manually
    print("\n[Step 1] Creating test hands...")

    # Define 4 hands for testing
    north_cards = create_test_hand("♠AK5 ♥Q72 ♦A843 ♣K62")
    east_cards = create_test_hand("♠Q73 ♥J984 ♦K72 ♣A85")
    south_cards = create_test_hand("♠J82 ♥AK5 ♦QJ65 ♣QT4")
    west_cards = create_test_hand("♠T964 ♥T63 ♦T9 ♣J973")

    # Convert to JSON format (list of dicts)
    north_hand = [{"rank": c.rank, "suit": c.suit} for c in north_cards]
    east_hand = [{"rank": c.rank, "suit": c.suit} for c in east_cards]
    south_hand = [{"rank": c.rank, "suit": c.suit} for c in south_cards]
    west_hand = [{"rank": c.rank, "suit": c.suit} for c in west_cards]

    print(f"✓ Created 4 test hands")
    print(f"  North: {len(north_hand)} cards")
    print(f"  East: {len(east_hand)} cards")
    print(f"  South: {len(south_hand)} cards")
    print(f"  West: {len(west_hand)} cards")

    # Step 2: Start play phase with a 3NT contract
    print("\n[Step 2] Starting play phase with 3NT contract...")

    auction = ["1NT", "Pass", "3NT", "Pass", "Pass", "Pass"]
    vulnerability = {"NS": False, "EW": False}

    start_play_data = {
        "auction_history": auction,  # Note: endpoint expects "auction_history" not "auction"
        "hands": {
            "N": north_hand,
            "E": east_hand,
            "S": south_hand,
            "W": west_hand
        },
        "vulnerability": "None"  # Note: endpoint expects string "None", "NS", "EW", or "Both"
    }

    response = requests.post(f"{BASE_URL}/start-play", json=start_play_data)

    if response.status_code != 200:
        print(f"✗ ERROR: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

    play_data = response.json()
    print(f"✓ Play started successfully")
    print(f"  Contract: {play_data['contract_details']['level']}{play_data['contract_details']['strain']}")
    print(f"  Declarer: {play_data['contract_details']['declarer']}")
    print(f"  Opening Leader: {play_data['opening_leader']}")
    print(f"  Dummy: {play_data['dummy']}")

    # Step 3: Get play state
    print("\n[Step 3] Getting initial play state...")
    state_response = requests.get(f"{BASE_URL}/get-play-state")

    if state_response.status_code != 200:
        print(f"✗ ERROR: {state_response.status_code}")
        print(f"  Response: {state_response.text}")
        return False

    state_data = state_response.json()
    print(f"✓ Got play state")
    print(f"  Next to play: {state_data['next_to_play']}")
    print(f"  Current trick: {state_data['current_trick']}")
    print(f"  Tricks won: {state_data['tricks_won']}")

    # Step 4: AI makes opening lead
    print("\n[Step 4] AI making opening lead...")
    ai_play_data = {
        "position": play_data['opening_leader']
    }

    ai_response = requests.post(f"{BASE_URL}/get-ai-play", json=ai_play_data)

    if ai_response.status_code != 200:
        print(f"✗ ERROR: {ai_response.status_code}")
        print(f"  Response: {ai_response.text}")
        return False

    ai_data = ai_response.json()
    print(f"✓ AI played card")
    print(f"  Card: {ai_data['card']['rank']}{ai_data['card']['suit']}")
    print(f"  Next to play: {ai_data['next_to_play']}")
    print(f"  Explanation: {ai_data.get('explanation', 'N/A')}")

    # Step 5: Play one complete trick with all AI players
    print("\n[Step 5] Playing complete trick with AI...")

    for i in range(3):  # 3 more cards to complete the trick
        state_response = requests.get(f"{BASE_URL}/get-play-state")
        state_data = state_response.json()

        next_player = state_data['next_to_play']
        print(f"  {next_player} to play...")

        ai_response = requests.post(f"{BASE_URL}/get-ai-play", json={"position": next_player})

        if ai_response.status_code != 200:
            print(f"  ✗ ERROR: {ai_response.status_code}")
            return False

        ai_data = ai_response.json()
        print(f"  → {next_player} played {ai_data['card']['rank']}{ai_data['card']['suit']}")

        if ai_data.get('trick_complete'):
            print(f"  ✓ Trick complete! Winner: {ai_data['trick_winner']}")
            break

    # Step 6: Get updated state
    print("\n[Step 6] Getting updated play state...")
    state_response = requests.get(f"{BASE_URL}/get-play-state")
    state_data = state_response.json()

    print(f"✓ Updated state:")
    print(f"  Tricks won: {state_data['tricks_won']}")
    print(f"  Current trick: {state_data['current_trick']}")
    print(f"  Next to play: {state_data['next_to_play']}")

    print("\n" + "=" * 80)
    print("✓ ALL ENDPOINT TESTS PASSED")
    print("=" * 80)
    print("\nSummary: Card play endpoints are working correctly!")
    print("- /api/start-play: ✓")
    print("- /api/get-play-state: ✓")
    print("- /api/get-ai-play: ✓")
    print("\nReady to build frontend UI for card play.")

    return True

if __name__ == "__main__":
    try:
        success = test_card_play_endpoints()
        if not success:
            print("\n✗ Some tests failed")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to Flask server at http://localhost:5001")
        print("  Make sure the server is running: cd backend && python server.py")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
