"""
Test server state after dealing hands
"""
import requests
import json

API_URL = "http://localhost:5001"

print("=== Testing /api/deal-hands endpoint ===")
response = requests.get(f"{API_URL}/api/deal-hands")
print(f"Status: {response.status_code}")
deal_data = response.json()
print(f"South hand HCP: {deal_data['points']['hcp']}")
print()

# Now fetch all hands to see what the server has
print("=== Testing /api/get-all-hands endpoint ===")
response = requests.get(f"{API_URL}/api/get-all-hands")
all_hands_data = response.json()

for position in ['North', 'East', 'South', 'West']:
    points = all_hands_data['hands'][position]['points']
    print(f"{position}: {points['hcp']} HCP, balanced={points['suit_lengths']}")

print()

# Now let's simulate the first round of bidding
auction = []
positions = ['North', 'East', 'South', 'West']

print("=== Simulating first round of AI bidding ===")
for position in positions[0:3]:  # North, East, South
    print(f"\n{position}'s turn (auction: {[b['bid'] if isinstance(b, dict) else b for b in auction]})")

    response = requests.post(
        f"{API_URL}/api/get-next-bid",
        headers={'Content-Type': 'application/json'},
        json={
            'auction_history': [b['bid'] if isinstance(b, dict) else b for b in auction],
            'current_player': position
        }
    )

    bid_data = response.json()
    print(f"  Bid: {bid_data['bid']}")
    print(f"  Explanation: {bid_data['explanation'][:100]}...")

    auction.append({'bid': bid_data['bid'], 'explanation': bid_data['explanation']})

print("\n=== Final auction (first 3 bids) ===")
print([b['bid'] for b in auction])
