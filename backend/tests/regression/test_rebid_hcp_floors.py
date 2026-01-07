"""
Regression test for Rebid HCP Floors fix.

Bug: The rebid logic was using AuctionContext's combined_midpoint which
inflates the estimate because it uses the opener's RANGE midpoint (17)
instead of the ACTUAL hand's HCP.

Example failure:
- Opener has 13 HCP, partner made simple raise (6-10 support points)
- AuctionContext calculated: opener range (13-21) midpoint 17 + responder 8 = 25
- This incorrectly triggered game bid with minimum hand
- Correct calculation: actual 13 HCP + partner midpoint 8 = 21 (not enough for game)

Fix: Changed rebid logic to use actual hand.hcp/hand.total_points + partner's
midpoint estimate instead of AuctionContext combined_midpoint.

Date: 2026-01-07
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


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


class TestMinimumOpenerAfterSimpleRaise:
    """Tests for opener's rebid after simple raise (1♠-2♠)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_13_hcp_passes_after_simple_raise(self):
        """
        13 HCP opener should PASS after partner's simple raise.
        Combined: 13 + 8 (partner midpoint) = 21, not enough for game (25).
        """
        # 13 HCP: AQJ (6) + K (3) + Q (2) + J (1) + J (1) = 13
        hand = create_hand("♠AQJ53 ♥K65 ♦Q98 ♣J2")

        auction = ["1♠", "Pass", "2♠", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "South", "None")

        assert bid == "Pass", f"13 HCP should pass after simple raise, got {bid}"

    def test_14_hcp_without_shape_passes_after_simple_raise(self):
        """
        14 HCP opener without extra shape or quality suit should PASS.
        Combined: 14 + 8 = 22, still not enough for game.

        The threshold for invitation is:
        - realistic_combined >= 23 AND total_points >= 15 AND (6-card OR 6+ suit HCP)

        This test uses a hand with only 14 total points (no distribution bonus)
        and weak trump suit (K = 3 suit HCP, well below 6 threshold).
        """
        # 14 HCP with weak trump suit: K (3 in spades) = 3 suit HCP
        # K(3) + AQ(6) + K(3) + Q(2) = 14 HCP, balanced = 14 total
        hand = create_hand("♠K9753 ♥AQ6 ♦K98 ♣Q2")

        auction = ["1♠", "Pass", "2♠", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "South", "None")

        # 14 total + 8 = 22, with only 3 suit HCP, should pass
        assert bid == "Pass", f"14 HCP (14 total) without quality suit should pass after simple raise, got {bid}"

    def test_15_hcp_with_shape_invites_after_simple_raise(self):
        """
        15 HCP opener with 6-card suit should INVITE after simple raise.
        Combined: 15 + 8 = 23, close to game with good shape.
        """
        # 15 HCP: AKQJ (10) + Q (2) + K (3) = 15, with 6-card spade suit
        hand = create_hand("♠AKQJ53 ♥Q6 ♦K98 ♣92")

        auction = ["1♠", "Pass", "2♠", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "South", "None")

        # With 16-18 pts total (15 HCP + distribution), medium hand logic applies
        # Should invite with 3♠ or bid based on medium hand logic
        assert bid in ["3♠", "4♠"], f"15 HCP with 6-card suit should invite or bid game, got {bid}"


class TestMinimumOpenerAfterInvitationalRaise:
    """Tests for opener's rebid after invitational raise (1♠-3♠)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_13_hcp_declines_invitation(self):
        """
        13 HCP opener should DECLINE invitation (pass).
        Combined: 13 + 10 (partner midpoint HCP) = 23, not enough.
        """
        # 13 HCP: AQJ (6) + K (3) + Q (2) + J (1) + J (1) = 13
        hand = create_hand("♠AQJ53 ♥K65 ♦Q98 ♣J2")

        auction = ["1♠", "Pass", "3♠", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "South", "None")

        assert bid == "Pass", f"13 HCP should decline invitation, got {bid}"

    def test_14_hcp_with_good_suit_accepts_invitation(self):
        """
        14 HCP opener with good 6-card suit should ACCEPT invitation.
        Combined: 14 + 10 = 24, with shape bonus = accept.
        """
        # 14 HCP with AKQJ in spades (quality suit) and 6 cards
        hand = create_hand("♠AKQJ53 ♥65 ♦K98 ♣92")

        auction = ["1♠", "Pass", "3♠", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "South", "None")

        assert bid == "4♠", f"14 HCP with quality 6-card suit should accept invitation, got {bid}"

    def test_15_hcp_accepts_invitation(self):
        """
        15 HCP opener should ACCEPT invitation.
        Combined: 15 + 10 = 25, enough for game.
        """
        # 15 HCP balanced
        hand = create_hand("♠AKJ53 ♥A65 ♦K98 ♣Q2")

        auction = ["1♠", "Pass", "3♠", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "South", "None")

        assert bid == "4♠", f"15 HCP should accept invitation, got {bid}"


class TestEdgeCases:
    """Edge cases for rebid HCP floors."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_13_hcp_with_exceptional_shape_can_accept(self):
        """
        13 HCP with 6-card suit AND strong honors (AKQ) may accept invitation.
        This is the only exception for minimum hands.
        """
        # 13 HCP with AKQ in 6-card spade suit
        hand = create_hand("♠AKQ653 ♥J65 ♦K98 ♣2")

        auction = ["1♠", "Pass", "3♠", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "South", "None")

        # With exceptional shape (6 cards + AKQ = 9 HCP in suit), may accept
        # The threshold is suit_hcp >= 8 AND suit_length >= 6
        assert bid in ["Pass", "4♠"], f"13 HCP with exceptional shape may accept, got {bid}"

    def test_minimum_after_1nt_response(self):
        """
        Minimum opener should PASS after 1NT response (not rebid a 5-card suit).
        """
        hand = create_hand("♠AKJ53 ♥Q65 ♦K98 ♣J2")

        auction = ["1♠", "Pass", "1NT", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "South", "None")

        # With only 5-card suit and 13 HCP, should pass 1NT
        assert bid == "Pass", f"Minimum with 5-card suit should pass 1NT, got {bid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
