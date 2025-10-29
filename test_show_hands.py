#!/usr/bin/env python3
"""
Test script to diagnose the "show hands" issue on localhost
"""
import requests
import json

API_URL = "http://localhost:5001"

# Create a session to maintain cookies
session = requests.Session()

# Generate a test session ID
session_id = "test_session_diagnostic"
headers = {
    "X-Session-ID": session_id,
    "Content-Type": "application/json"
}

print("=" * 60)
print("TESTING 'SHOW HANDS' FUNCTIONALITY")
print("=" * 60)

# Step 1: Deal hands (this should create a deal in the session)
print("\n1️⃣ Dealing new hands...")
response = session.get(f"{API_URL}/api/deal-hands", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ Got South's hand with {len(data['hand'])} cards")
    print(f"   ✓ Dealer: {data.get('dealer', 'Unknown')}")
    print(f"   ✓ Vulnerability: {data['vulnerability']}")
else:
    print(f"   ✗ Error: {response.text}")
    exit(1)

# Step 2: Immediately try to get all hands
print("\n2️⃣ Requesting all hands...")
response = session.get(f"{API_URL}/api/get-all-hands", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ Success! Got hands for all positions:")
    for position in ['North', 'East', 'South', 'West']:
        hand = data['hands'].get(position)
        if hand:
            print(f"      {position}: {len(hand['hand'])} cards")
        else:
            print(f"      {position}: MISSING ⚠️")
    print(f"\n   📋 Response structure:")
    print(f"      - hands: {list(data.get('hands', {}).keys())}")
    print(f"      - vulnerability: {data.get('vulnerability', 'Unknown')}")
else:
    error_data = response.json()
    print(f"   ✗ Error: {error_data.get('error', 'Unknown error')}")
    print(f"\n   🔍 This error means the backend couldn't find the deal in session state.")
    print(f"   Possible causes:")
    print(f"      - Session ID mismatch between requests")
    print(f"      - Session state not being preserved")
    print(f"      - Deal not being stored in backend session")

# Step 3: Check if session state exists
print("\n3️⃣ Checking session status...")
response = session.get(f"{API_URL}/api/session/status?user_id=2", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   Session active: {data.get('active', False)}")
    if data.get('active'):
        print(f"   Session data: {data.get('session', {})}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
