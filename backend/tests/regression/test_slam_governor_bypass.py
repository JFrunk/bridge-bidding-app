"""
Regression test for slam Governor bypass fix.

Bug: The SanityChecker's Governor was blocking valid slam bids (6-level)
even when Blackwood/Gerber conventions had been used to establish ace counts.
This resulted in a 3.4% slam success rate.

Fix: Added bypass logic for:
1. King-ask responses (6♣/6♦/6♥/6♠ after 5NT)
2. Slam signoff by the asker after receiving Blackwood response
The "Physics of Information" principle: conventional responses provide
control information that supersedes raw HCP calculations.

Date: 2026-01-07
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.hand import Hand, Card
from engine.ai.sanity_checker import SanityChecker


def create_hand(cards_str: str) -> Hand:
    """Helper to create hand from string like '♠AKQ32 ♥AK ♦KQ32 ♣32'"""
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        ranks = part[1:]
        for rank in ranks:
            cards.append(Card(rank=rank, suit=suit))
    return Hand(cards)


class TestSlamGovernorBypass:
    """Tests for the slam Governor bypass fix."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = SanityChecker()

    def _create_features(self, opener_relationship='Me'):
        """Create minimal features for testing."""
        return {
            'auction_features': {
                'opener_relationship': opener_relationship,
                'is_contested': False
            },
            'auction_context': None  # Will use legacy estimation
        }

    def test_king_ask_response_allowed(self):
        """
        6-level responses to 5NT king-ask should be allowed.
        This was one of the blocked scenarios.
        """
        # Hand with 1 king: should respond 6♦
        hand = create_hand("♠A432 ♥AK32 ♦432 ♣32")
        features = self._create_features(opener_relationship='Partner')

        # Auction: 1♠-3♠-4NT(Blackwood)-5♥(2 aces)-5NT(king ask)-?
        auction = ["1♠", "Pass", "3♠", "Pass", "4NT", "Pass", "5♥", "Pass", "5NT", "Pass"]

        # 6♦ response to king ask should be allowed
        should_bid, final_bid, reason = self.checker.check("6♦", hand, features, auction)

        assert should_bid is True, f"6♦ king response should be allowed, but was blocked: {reason}"
        assert final_bid == "6♦"

    def test_slam_signoff_after_blackwood_response_allowed(self):
        """
        The asker should be able to bid slam after receiving the Blackwood response.
        This was the main blocked scenario.
        """
        # Strong hand with 2 aces, saw partner show 2 aces = all 4 aces
        hand = create_hand("♠AKQ32 ♥AK ♦KQ32 ♣32")
        features = self._create_features(opener_relationship='Me')

        # Auction: 1♠-3♠-4NT(we ask)-5♥(partner shows 2 aces)-?
        # We have 2 aces + partner has 2 = all 4 accounted for
        auction = ["1♠", "Pass", "3♠", "Pass", "4NT", "Pass", "5♥", "Pass"]

        # 6♠ slam bid should be allowed
        should_bid, final_bid, reason = self.checker.check("6♠", hand, features, auction)

        assert should_bid is True, f"6♠ slam after Blackwood should be allowed, but was blocked: {reason}"
        assert final_bid == "6♠"

    def test_grand_slam_after_blackwood_allowed(self):
        """
        Grand slam (7-level) should also be allowed after Blackwood.
        """
        hand = create_hand("♠AKQ32 ♥AK ♦KQ32 ♣A2")  # 23 HCP, 3 aces
        features = self._create_features(opener_relationship='Me')

        # Auction shows we have all aces
        auction = ["1♠", "Pass", "3♠", "Pass", "4NT", "Pass", "5♦", "Pass"]  # 5♦ = 1 ace

        # 7♠ grand slam should be allowed (we have 3 + partner has 1 = 4)
        should_bid, final_bid, reason = self.checker.check("7♠", hand, features, auction)

        assert should_bid is True, f"7♠ grand slam should be allowed, but was blocked: {reason}"
        assert final_bid == "7♠"

    def test_blackwood_ace_response_still_allowed(self):
        """
        5-level Blackwood responses should still be allowed (pre-existing behavior).
        """
        hand = create_hand("♠A432 ♥KQ32 ♦Q32 ♣32")  # 1 ace
        features = self._create_features(opener_relationship='Partner')

        # Auction: 1♠-2♠-4NT(Blackwood)-?
        auction = ["1♠", "Pass", "2♠", "Pass", "4NT", "Pass"]

        # 5♦ response (1 ace) should be allowed
        should_bid, final_bid, reason = self.checker.check("5♦", hand, features, auction)

        assert should_bid is True, f"5♦ ace response should be allowed, but was blocked: {reason}"

    def test_non_blackwood_slam_still_governed(self):
        """
        Slam bids without Blackwood should still be governed by HCP.
        We don't want to remove ALL slam protection.
        """
        # Weak hand trying to bid slam without Blackwood
        hand = create_hand("♠Q432 ♥K32 ♦432 ♣432")  # 5 HCP
        features = self._create_features(opener_relationship='Me')

        # Simple auction without Blackwood
        auction = ["1♠", "Pass", "2♠", "Pass"]

        # 6♠ slam should be blocked - no Blackwood, weak hand
        should_bid, final_bid, reason = self.checker.check("6♠", hand, features, auction)

        # This should be blocked by Governor (insufficient HCP)
        assert should_bid is False, "6♠ without Blackwood and weak hand should be blocked"
        assert final_bid == "Pass"


class TestSanityCheckerHelperMethods:
    """Tests for the new helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = SanityChecker()

    def test_is_king_ask_response_positive(self):
        """_is_king_ask_response should return True for 6-level after 5NT."""
        auction = ["1♠", "Pass", "4NT", "Pass", "5♥", "Pass", "5NT", "Pass"]

        assert self.checker._is_king_ask_response("6♣", auction) is True
        assert self.checker._is_king_ask_response("6♦", auction) is True
        assert self.checker._is_king_ask_response("6♥", auction) is True
        assert self.checker._is_king_ask_response("6♠", auction) is True

    def test_is_king_ask_response_negative(self):
        """_is_king_ask_response should return False without 5NT."""
        auction = ["1♠", "Pass", "4NT", "Pass", "5♥", "Pass"]  # No 5NT

        assert self.checker._is_king_ask_response("6♣", auction) is False
        assert self.checker._is_king_ask_response("6♦", auction) is False

    def test_is_slam_signoff_after_blackwood_positive(self):
        """_is_slam_signoff_after_blackwood should return True after response."""
        auction = ["1♠", "Pass", "4NT", "Pass", "5♥", "Pass"]  # 4NT + response

        assert self.checker._is_slam_signoff_after_blackwood("6♠", auction) is True
        assert self.checker._is_slam_signoff_after_blackwood("7♠", auction) is True

    def test_is_slam_signoff_after_blackwood_negative(self):
        """_is_slam_signoff_after_blackwood should return False without response."""
        auction = ["1♠", "Pass", "4NT", "Pass"]  # 4NT but no response yet

        assert self.checker._is_slam_signoff_after_blackwood("6♠", auction) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
