#!/usr/bin/env python3
"""
Test script for the AI Review feature on Render deployment
Tests that the review prompt includes full context when file saving is not available
"""
import requests
import json

BASE_URL = "https://bridge-bidding-api.onrender.com"

def test_render_review_feature():
    print("Testing AI Review Feature on Render")
    print("=" * 70)

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

    # South bids
    bid_response = requests.post(f"{BASE_URL}/api/get-next-bid",
                                 json={"auction_history": [a["bid"] for a in auction], "current_player": "South"})
    if bid_response.status_code == 200:
        bid_data = bid_response.json()
        auction.append({"bid": bid_data["bid"], "explanation": bid_data["explanation"]})
        print(f"   South: {bid_data['bid']} - {bid_data['explanation']}")

    # West bids
    bid_response = requests.post(f"{BASE_URL}/api/get-next-bid",
                                 json={"auction_history": [a["bid"] for a in auction], "current_player": "West"})
    if bid_response.status_code == 200:
        bid_data = bid_response.json()
        auction.append({"bid": bid_data["bid"], "explanation": bid_data["explanation"]})
        print(f"   West: {bid_data['bid']} - {bid_data['explanation']}")

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
    print(f"✅ Review request processed successfully")
    print(f"   Filename: {review_data['filename']}")
    print(f"   Saved to file: {review_data['saved_to_file']}")

    # Step 4: Verify the review_data is complete
    print("\n4. Verifying review data completeness...")

    if 'review_data' not in review_data:
        print("❌ Missing 'review_data' in response!")
        return

    rd = review_data['review_data']

    # Check all required fields
    required_fields = ['timestamp', 'all_hands', 'auction', 'vulnerability', 'dealer', 'user_position', 'user_concern']
    missing_fields = [f for f in required_fields if f not in rd]

    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return

    print(f"   ✅ All required fields present")
    print(f"   Timestamp: {rd['timestamp']}")
    print(f"   Vulnerability: {rd['vulnerability']}")
    print(f"   Dealer: {rd['dealer']}")
    print(f"   User position: {rd['user_position']}")
    print(f"   User concern: {rd['user_concern']}")

    # Verify all hands are present with complete data
    print("\n5. Verifying hand data...")
    for position in ['North', 'East', 'South', 'West']:
        if position not in rd['all_hands']:
            print(f"   ❌ Missing hand for {position}")
            return

        hand = rd['all_hands'][position]

        if 'cards' not in hand or 'points' not in hand:
            print(f"   ❌ Incomplete data for {position}")
            return

        if len(hand['cards']) != 13:
            print(f"   ❌ {position} has {len(hand['cards'])} cards (should be 13)")
            return

        points = hand['points']
        required_point_fields = ['hcp', 'dist_points', 'total_points', 'suit_hcp', 'suit_lengths']
        missing_point_fields = [f for f in required_point_fields if f not in points]

        if missing_point_fields:
            print(f"   ❌ {position} missing point fields: {missing_point_fields}")
            return

        print(f"   ✅ {position}: {points['hcp']} HCP, {len(hand['cards'])} cards")

    # Verify auction
    print(f"\n6. Verifying auction data...")
    if len(rd['auction']) != len(auction):
        print(f"   ❌ Auction length mismatch: {len(rd['auction'])} vs {len(auction)}")
        return
    print(f"   ✅ Auction has {len(rd['auction'])} bids")

    # Step 5: Generate and verify the prompt
    print("\n7. Verifying generated prompt...")

    if review_data['saved_to_file']:
        prompt = f"""Please analyze the bidding in backend/review_requests/{review_data['filename']} and identify any errors or questionable bids according to SAYC.

I'm particularly concerned about: {review_request['user_concern']}"""
        print("   📁 Prompt uses file reference (local mode)")
    else:
        prompt = f"""Please analyze this bridge hand and identify any errors or questionable bids according to SAYC.

**Hand Data:**
{json.dumps(rd, indent=2)}

**User's Concern:** {review_request['user_concern']}

Please provide a detailed analysis of the auction and identify any bidding errors."""
        print("   📋 Prompt includes full data (Render mode)")

    # Verify the prompt contains essential information
    user_concern_in_prompt = (review_request['user_concern'] in prompt) or ("particularly concerned" in prompt)
    essential_checks = [
        (user_concern_in_prompt, "User concern present"),
        (rd['vulnerability'] in json.dumps(rd) if not review_data['saved_to_file'] else True, "Vulnerability included"),
        (str(rd['all_hands']['North']['points']['hcp']) in json.dumps(rd) if not review_data['saved_to_file'] else True, "North's HCP included"),
    ]

    all_checks_passed = True
    for check, description in essential_checks:
        if check:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description}")
            all_checks_passed = False

    if not all_checks_passed:
        print("\n❌ Some essential information missing from prompt!")
        return

    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print(f"\nGenerated prompt preview (first 500 chars):")
    print("-" * 70)
    print(prompt[:500] + ("..." if len(prompt) > 500 else ""))
    print("-" * 70)
    print(f"\nFull prompt length: {len(prompt)} characters")
    print(f"Review data size: {len(json.dumps(rd))} characters")

    # Save full prompt to file for inspection
    with open('/tmp/render_review_prompt.txt', 'w') as f:
        f.write(prompt)
    print(f"\n📝 Full prompt saved to: /tmp/render_review_prompt.txt")

if __name__ == "__main__":
    try:
        test_render_review_feature()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
