#!/usr/bin/env python3
"""
Test script for the AI Review feature
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_review_feature():
    print("Testing AI Review Feature")
    print("=" * 50)

    # Step 1: Deal hands
    print("\n1. Dealing hands...")
    response = requests.get(f"{BASE_URL}/api/deal-hands")
    if response.status_code != 200:
        print(f"❌ Failed to deal hands: {response.text}")
        return
    print("✅ Hands dealt successfully")

    # Step 2: Make some bids (simulate auction)
    print("\n2. Simulating auction...")
    auction = []

    # North bids
    bid_response = requests.post(f"{BASE_URL}/api/get-next-bid",
                                 json={"auction_history": [], "current_player": "North"})
    if bid_response.status_code == 200:
        bid_data = bid_response.json()
        auction.append({"bid": bid_data["bid"], "explanation": bid_data["explanation"]})
        print(f"   North: {bid_data['bid']} - {bid_data['explanation']}")

    # East bids
    bid_response = requests.post(f"{BASE_URL}/api/get-next-bid",
                                 json={"auction_history": [a["bid"] for a in auction], "current_player": "East"})
    if bid_response.status_code == 200:
        bid_data = bid_response.json()
        auction.append({"bid": bid_data["bid"], "explanation": bid_data["explanation"]})
        print(f"   East: {bid_data['bid']} - {bid_data['explanation']}")

    # Step 3: Request review
    print("\n3. Requesting AI review...")
    review_request = {
        "auction_history": auction,
        "user_concern": "Is North's opening bid correct? What about East's response?"
    }

    review_response = requests.post(f"{BASE_URL}/api/request-review", json=review_request)

    if review_response.status_code != 200:
        print(f"❌ Failed to request review: {review_response.text}")
        return

    review_data = review_response.json()
    print(f"✅ Review request saved successfully")
    print(f"   Filename: {review_data['filename']}")
    print(f"   Filepath: {review_data['filepath']}")

    # Step 4: Read the saved file
    print("\n4. Reading saved review file...")
    with open(review_data['filepath'], 'r') as f:
        saved_data = json.load(f)

    print(f"   Timestamp: {saved_data['timestamp']}")
    print(f"   Vulnerability: {saved_data['vulnerability']}")
    print(f"   User concern: {saved_data['user_concern']}")
    print(f"   Number of hands: {len(saved_data['all_hands'])}")
    print(f"   Auction length: {len(saved_data['auction'])}")

    # Print sample hand data
    print(f"\n   Sample - North's hand:")
    north_hand = saved_data['all_hands']['North']
    print(f"      HCP: {north_hand['points']['hcp']}")
    print(f"      Cards: {len(north_hand['cards'])} cards")

    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print(f"\nGenerated prompt for Claude Code:")
    print("-" * 50)
    prompt = f"""Please analyze the bidding in backend/review_requests/{review_data['filename']} and identify any errors or questionable bids according to SAYC.

I'm particularly concerned about: {review_request['user_concern']}"""
    print(prompt)
    print("-" * 50)

if __name__ == "__main__":
    try:
        test_review_feature()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
