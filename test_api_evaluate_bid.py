#!/usr/bin/env python3
"""
Test the /api/evaluate-bid endpoint directly to see what error occurs
"""
import requests
import json

API_URL = "http://localhost:5001"

# First, we need to deal a hand
print("1. Dealing a hand...")
deal_response = requests.get(f"{API_URL}/api/deal-hands")
if deal_response.status_code != 200:
    print(f"❌ Failed to deal hand: {deal_response.status_code}")
    print(deal_response.text)
    exit(1)

deal_data = deal_response.json()
print(f"✓ Hand dealt. Dealer: {deal_data.get('dealer', 'Unknown')}")
print(f"  Your hand: {deal_data['points']['total_points']} total points")

# Now try to evaluate a bid
print("\n2. Making a bid (Pass)...")
evaluate_payload = {
    "user_bid": "Pass",
    "auction_history": [],  # First bid in auction
    "current_player": "South",
    "user_id": 1,
    "feedback_level": "intermediate"
}

print(f"   Sending: {json.dumps(evaluate_payload, indent=2)}")

evaluate_response = requests.post(
    f"{API_URL}/api/evaluate-bid",
    headers={"Content-Type": "application/json"},
    json=evaluate_payload
)

print(f"\n3. Response status: {evaluate_response.status_code}")

if evaluate_response.status_code == 200:
    result = evaluate_response.json()
    print("✓ Success!")
    print(f"   Feedback: {result.get('user_message', 'No message')}")
    print(f"   Was correct: {result.get('was_correct')}")

    # Check database
    import sqlite3
    conn = sqlite3.connect('backend/bridge.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bidding_decisions")
    count = cursor.fetchone()[0]
    print(f"\n4. Database check: {count} bidding_decisions records")
    conn.close()
else:
    print("❌ Error!")
    print(f"   Response: {evaluate_response.text}")

print("\n✓ Test complete")
