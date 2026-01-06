"""
Test server state after dealing hands

This test requires a running server on localhost:5001.
Run with: pytest tests/integration/test_server_state.py -v -s
"""
import pytest
import requests
import json

API_URL = "http://localhost:5001"


def is_server_running():
    """Check if the server is running."""
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=1)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.Timeout:
        return False


@pytest.mark.skipif(not is_server_running(), reason="Server not running on localhost:5001")
class TestServerState:
    """Test server state after dealing hands."""

    def test_deal_hands_endpoint(self):
        """Test that /api/deal-hands returns valid hand data."""
        print("\n=== Testing /api/deal-hands endpoint ===")
        response = requests.get(f"{API_URL}/api/deal-hands")
        print(f"Status: {response.status_code}")

        assert response.status_code == 200
        deal_data = response.json()

        assert 'points' in deal_data
        assert 'hcp' in deal_data['points']
        print(f"South hand HCP: {deal_data['points']['hcp']}")

    def test_get_all_hands_endpoint(self):
        """Test that /api/get-all-hands returns all four hands."""
        # First deal to ensure we have hands
        requests.get(f"{API_URL}/api/deal-hands")

        print("\n=== Testing /api/get-all-hands endpoint ===")
        response = requests.get(f"{API_URL}/api/get-all-hands")

        assert response.status_code == 200
        all_hands_data = response.json()

        assert 'hands' in all_hands_data
        for position in ['North', 'East', 'South', 'West']:
            assert position in all_hands_data['hands']
            points = all_hands_data['hands'][position]['points']
            print(f"{position}: {points['hcp']} HCP, balanced={points['suit_lengths']}")

    def test_simulated_bidding_round(self):
        """Test simulating a round of AI bidding."""
        # First deal new hands
        requests.get(f"{API_URL}/api/deal-hands")

        print("\n=== Simulating first round of AI bidding ===")
        auction = []
        positions = ['North', 'East', 'South']  # First 3 positions

        for position in positions:
            print(f"\n{position}'s turn (auction: {[b['bid'] if isinstance(b, dict) else b for b in auction]})")

            response = requests.post(
                f"{API_URL}/api/get-next-bid",
                headers={'Content-Type': 'application/json'},
                json={
                    'auction_history': [b['bid'] if isinstance(b, dict) else b for b in auction],
                    'current_player': position
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            bid_data = response.json()

            assert 'bid' in bid_data, f"Response missing 'bid': {bid_data}"
            assert 'explanation' in bid_data, f"Response missing 'explanation': {bid_data}"

            print(f"  Bid: {bid_data['bid']}")
            print(f"  Explanation: {bid_data['explanation'][:100]}...")

            auction.append({'bid': bid_data['bid'], 'explanation': bid_data['explanation']})

        print("\n=== Final auction (first 3 bids) ===")
        print([b['bid'] for b in auction])

        # Verify we got 3 bids
        assert len(auction) == 3
