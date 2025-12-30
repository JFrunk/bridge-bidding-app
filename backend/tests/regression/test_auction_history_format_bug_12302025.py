"""
Regression Test: Auction History Format Bug (2025-12-30)

Bug: Backend crashed when auction_history contained {bid, explanation} objects
     instead of plain bid strings.

Root Cause: Frontend stores auction as [{bid, explanation, player}] objects internally.
            Most API calls correctly extract strings with .map(a => a.bid), but the
            backend never validated the format. When objects arrived, deep code in
            auction_context.py crashed with "unhashable type: 'dict'" or
            "'dict' object has no attribute 'endswith'".

Error Timeline:
- 2025-11-02: KeyError: 1 (masked by Michaels cuebid issue)
- 2025-12-24: AttributeError: 'dict' object has no attribute 'endswith'
- 2025-12-25: TypeError: unhashable type: 'dict'
- 2025-12-29: TypeError: unhashable type: 'dict'

Fix: Added normalization in server.py to convert objects to strings:
     auction_history = [item.get('bid', 'Pass') if isinstance(item, dict) else item
                        for item in auction_history_raw]

Affected Endpoints:
- /api/get-next-bid
- /api/get-next-bid-structured
- /api/get-feedback
- /api/evaluate-bid

This test ensures the bug stays fixed by testing all affected endpoints with
both object format (what frontend might send) and string format (backward compat).
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from server import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def deal_hands(client):
    """Deal hands before testing bidding endpoints."""
    response = client.get('/api/deal-hands')
    assert response.status_code == 200
    return response.get_json()


class TestAuctionHistoryFormatNormalization:
    """
    Test that all bidding endpoints handle both auction history formats:
    1. Object format: [{"bid": "1NT", "explanation": "..."}]
    2. String format: ["1NT", "Pass"]
    """

    # === /api/get-next-bid Tests ===

    def test_get_next_bid_with_object_format(self, client, deal_hands):
        """
        REGRESSION TEST: /api/get-next-bid with {bid, explanation} objects.

        This was the exact format that caused the production crash.
        Error logged: {"auction_history": [{"bid": "1NT", "explanation": "North bid 1NT"}]}
        """
        # Object format - what frontend might accidentally send
        response = client.post('/api/get-next-bid', json={
            "auction_history": [
                {"bid": "1NT", "explanation": "Opening 1NT with 15-17 HCP balanced"},
            ],
            "current_player": "East",
            "dealer": "North"
        })

        assert response.status_code == 200, f"Failed with object format: {response.get_json()}"
        data = response.get_json()
        assert 'bid' in data, "Response should contain 'bid'"
        assert 'explanation' in data, "Response should contain 'explanation'"

    def test_get_next_bid_with_string_format(self, client, deal_hands):
        """Verify string format still works (backward compatibility)."""
        response = client.post('/api/get-next-bid', json={
            "auction_history": ["1NT"],
            "current_player": "East",
            "dealer": "North"
        })

        assert response.status_code == 200, f"Failed with string format: {response.get_json()}"
        data = response.get_json()
        assert 'bid' in data

    def test_get_next_bid_with_mixed_format(self, client, deal_hands):
        """Handle mixed format (edge case)."""
        response = client.post('/api/get-next-bid', json={
            "auction_history": [
                {"bid": "1NT", "explanation": "Opening"},
                "Pass",  # String format
                {"bid": "2♣", "explanation": "Stayman"}
            ],
            "current_player": "West",
            "dealer": "North"
        })

        assert response.status_code == 200, f"Failed with mixed format: {response.get_json()}"

    def test_get_next_bid_with_empty_auction(self, client, deal_hands):
        """Opening bid with empty auction."""
        response = client.post('/api/get-next-bid', json={
            "auction_history": [],
            "current_player": "North",
            "dealer": "North"
        })

        assert response.status_code == 200

    def test_get_next_bid_object_with_player_field(self, client, deal_hands):
        """Object format including player field (full frontend format)."""
        response = client.post('/api/get-next-bid', json={
            "auction_history": [
                {"bid": "1♠", "explanation": "Opening 1 spade", "player": "North"},
                {"bid": "Pass", "explanation": "", "player": "East"},
            ],
            "current_player": "South",
            "dealer": "North"
        })

        assert response.status_code == 200

    # === /api/get-next-bid-structured Tests ===

    def test_get_next_bid_structured_with_object_format(self, client, deal_hands):
        """Structured endpoint with object format."""
        response = client.post('/api/get-next-bid-structured', json={
            "auction_history": [
                {"bid": "1♥", "explanation": "Opening hearts"},
            ],
            "current_player": "East"
        })

        assert response.status_code == 200, f"Structured endpoint failed: {response.get_json()}"

    def test_get_next_bid_structured_with_string_format(self, client, deal_hands):
        """Structured endpoint with string format."""
        response = client.post('/api/get-next-bid-structured', json={
            "auction_history": ["1♥"],
            "current_player": "East"
        })

        assert response.status_code == 200

    # === /api/get-feedback Tests ===

    def test_get_feedback_with_object_format(self, client, deal_hands):
        """Feedback endpoint with object format auction including user's bid."""
        response = client.post('/api/get-feedback', json={
            "auction_history": [
                {"bid": "1NT", "explanation": "Opening"},
                {"bid": "Pass", "explanation": ""},
                {"bid": "2♣", "explanation": "User bid Stayman"},  # User's bid is last
            ]
        })

        assert response.status_code == 200, f"Feedback failed: {response.get_json()}"

    def test_get_feedback_with_string_format(self, client, deal_hands):
        """Feedback endpoint with string format."""
        response = client.post('/api/get-feedback', json={
            "auction_history": ["1NT", "Pass", "2♣"]
        })

        assert response.status_code == 200

    # === /api/evaluate-bid Tests ===

    def test_evaluate_bid_with_object_format(self, client, deal_hands):
        """Evaluate-bid endpoint with object format (auction BEFORE user's bid)."""
        response = client.post('/api/evaluate-bid', json={
            "user_bid": "2♣",
            "auction_history": [
                {"bid": "1NT", "explanation": "Partner opened 1NT"},
                {"bid": "Pass", "explanation": ""},
            ],
            "current_player": "South",
            "user_id": 1
        })

        assert response.status_code == 200, f"Evaluate-bid failed: {response.get_json()}"

    def test_evaluate_bid_with_string_format(self, client, deal_hands):
        """Evaluate-bid endpoint with string format."""
        response = client.post('/api/evaluate-bid', json={
            "user_bid": "2♣",
            "auction_history": ["1NT", "Pass"],
            "current_player": "South",
            "user_id": 1
        })

        assert response.status_code == 200

    def test_evaluate_bid_empty_auction(self, client, deal_hands):
        """Evaluate opening bid (empty auction before)."""
        response = client.post('/api/evaluate-bid', json={
            "user_bid": "1NT",
            "auction_history": [],
            "current_player": "South",
            "user_id": 1
        })

        assert response.status_code == 200


class TestSpecificBugScenarios:
    """
    Test the exact scenarios that caused production crashes.
    These are based on actual error log entries.
    """

    def test_1nt_opening_object_format_east_response(self, client, deal_hands):
        """
        EXACT BUG REPRODUCTION from error logs.

        Error log showed:
        {
            "auction_history": [{"bid": "1NT", "explanation": "North bid 1NT"}],
            "current_player": "East"
        }

        This caused: TypeError: unhashable type: 'dict'
        Location: auction_context.py line 403
        """
        response = client.post('/api/get-next-bid', json={
            "auction_history": [{"bid": "1NT", "explanation": "North bid 1NT"}],
            "current_player": "East"
        })

        assert response.status_code == 200, (
            f"REGRESSION: 1NT object format still fails! "
            f"Error: {response.get_json()}"
        )

        data = response.get_json()
        assert data.get('bid') is not None, "AI should return a bid"
        # East should pass or make an overcall, not crash
        assert data['bid'] in ['Pass', 'X', '2♣', '2♦', '2♥', '2♠', '2NT', '3♣', '3♦', '3♥', '3♠'], \
            f"Unexpected bid: {data['bid']}"

    def test_preempt_3h_object_format(self, client, deal_hands):
        """
        Test scenario from user's bug report.

        Auction showed 3♥ preempt by East, then bidding stopped.
        """
        response = client.post('/api/get-next-bid', json={
            "auction_history": [
                {"bid": "Pass", "explanation": ""},
                {"bid": "3♥", "explanation": "Preemptive opening"}
            ],
            "current_player": "South",
            "dealer": "North"
        })

        assert response.status_code == 200, f"3H preempt scenario failed: {response.get_json()}"

    def test_long_auction_object_format(self, client, deal_hands):
        """Test a longer auction sequence in object format."""
        response = client.post('/api/get-next-bid', json={
            "auction_history": [
                {"bid": "1♠", "explanation": "Opening"},
                {"bid": "Pass", "explanation": ""},
                {"bid": "2♠", "explanation": "Raise"},
                {"bid": "Pass", "explanation": ""},
                {"bid": "4♠", "explanation": "Game bid"},
                {"bid": "Pass", "explanation": ""},
                {"bid": "Pass", "explanation": ""},
            ],
            "current_player": "West",
            "dealer": "North"
        })

        assert response.status_code == 200


class TestEdgeCases:
    """Edge cases for auction format handling."""

    def test_object_with_missing_bid_key(self, client, deal_hands):
        """Object without 'bid' key should default to 'Pass'."""
        response = client.post('/api/get-next-bid', json={
            "auction_history": [
                {"explanation": "Oops, no bid key"},  # Missing 'bid'
            ],
            "current_player": "East",
            "dealer": "North"
        })

        # Should not crash, should treat as Pass
        assert response.status_code == 200

    def test_object_with_null_bid(self, client, deal_hands):
        """Object with null bid value."""
        response = client.post('/api/get-next-bid', json={
            "auction_history": [
                {"bid": None, "explanation": "Null bid"},
            ],
            "current_player": "East",
            "dealer": "North"
        })

        # Should handle gracefully
        assert response.status_code == 200

    def test_deeply_nested_format_rejected(self, client, deal_hands):
        """Ensure we don't accept deeply nested formats."""
        # This should still work - we only extract top-level 'bid'
        response = client.post('/api/get-next-bid', json={
            "auction_history": [
                {"bid": "1NT", "metadata": {"nested": "data"}},
            ],
            "current_player": "East",
            "dealer": "North"
        })

        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
