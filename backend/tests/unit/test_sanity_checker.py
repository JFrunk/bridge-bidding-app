"""
Unit tests for Sanity Checker

Tests the final safety net that prevents impossible contracts
and runaway auctions.

Part of ADR-0002: Bidding System Robustness Improvements
Layer 3: Sanity Check Layer
"""

import pytest
from engine.ai.sanity_checker import SanityChecker
from engine.hand import Hand, Card


def create_test_hand(hcp, suit_lengths):
    """Helper to create test hands."""
    cards = []
    suits = ['♠', '♥', '♦', '♣']

    for i, suit in enumerate(suits):
        length = suit_lengths[suits[i]]
        for j in range(length):
            if hcp > 0 and j == 0:
                rank = 'A' if hcp >= 4 else 'K' if hcp >= 3 else 'Q' if hcp >= 2 else 'J'
                hcp -= {'A': 4, 'K': 3, 'Q': 2, 'J': 1}.get(rank, 0)
            else:
                rank = str(9 - j % 9)
            cards.append(Card(rank=rank, suit=suit))

    return Hand(cards)


class TestSanityChecker:
    """Test the sanity checker."""

    def test_pass_always_allowed(self):
        """Test that Pass is always allowed."""
        checker = SanityChecker()
        hand = create_test_hand(5, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})

        should_bid, final_bid, reason = checker.check("Pass", hand, {}, [])
        assert should_bid is True
        assert final_bid == "Pass"
        assert reason is None

    def test_doubles_allowed(self):
        """Test that doubles/redoubles are allowed."""
        checker = SanityChecker()
        hand = create_test_hand(8, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})

        should_bid, final_bid, reason = checker.check("X", hand, {}, [])
        assert should_bid is True

        should_bid, final_bid, reason = checker.check("XX", hand, {}, [])
        assert should_bid is True


class TestMaximumBidLevel:
    """Test maximum bid level enforcement."""

    def test_part_score_with_weak_hand(self):
        """Test that weak hands limited to part score."""
        checker = SanityChecker()

        # 10 HCP, partner passed (0 HCP assumed)
        hand = create_test_hand(10, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        features = {}
        auction = ["Pass", "Pass"]

        # 3-level should be rejected (combined ~10 HCP, max level 2)
        should_bid, final_bid, reason = checker.check("3♣", hand, features, auction)
        assert should_bid is False
        assert final_bid == "Pass"
        assert "safe maximum" in reason

    def test_game_with_opening_strength(self):
        """Test that opening strength allows game bidding."""
        checker = SanityChecker()

        # 13 HCP, partner opened (13+ HCP assumed)
        hand = create_test_hand(13, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        features = {'opener': 'partner'}
        auction = ["1♥", "Pass"]

        # 4-level should be allowed (combined ~26 HCP, max level 4)
        should_bid, final_bid, reason = checker.check("4♥", hand, features, auction)
        assert should_bid is True

    def test_slam_requires_high_hcp(self):
        """Test that slam bidding requires 33+ combined HCP."""
        checker = SanityChecker()

        # 16 HCP, partner opened (13 HCP assumed)
        hand = create_test_hand(16, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        features = {'opener': 'partner'}
        auction = ["1♠", "Pass"]

        # 6-level should be rejected (combined ~29 HCP, max level 4)
        should_bid, final_bid, reason = checker.check("6♠", hand, features, auction)
        assert should_bid is False
        assert final_bid == "Pass"
        # Maximum level check catches this before slam-specific check
        assert "safe maximum" in reason


class TestRunawayAuctionPrevention:
    """
    Regression tests for preventing runaway auctions.

    Based on hand_2025-10-29_15-12-17.json where auction went:
    1NT → 2♥ → 2♠ → X → 2NT → 3NT → 4NT → 5♦ (disaster!)
    """

    def test_prevents_5_level_disaster(self):
        """
        Test that sanity checker prevents 5-level bids with inadequate
        combined HCP.

        Note: If 4NT is in the auction, it's treated as Blackwood and
        bypass checks apply. This test uses an auction without 4NT.
        """
        checker = SanityChecker()

        # Hand with 10 HCP
        hand = create_test_hand(10, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})

        # Simple auction: partner opened 1♦, I responded 1♠
        # Without 4NT to avoid Blackwood bypass
        # Estimated combined: 10 + 13 (opening) = 23 HCP
        features = {
            'auction_features': {
                'opener_relationship': 'Partner',
                'opening_bid': '1♦'
            }
        }
        auction = ["1♦", "Pass", "1♠", "Pass", "2♦", "Pass"]

        # 5♦ should be REJECTED (10 + 13 = 23 HCP, max level 3)
        should_bid, final_bid, reason = checker.check("5♦", hand, features, auction)
        assert should_bid is False
        assert final_bid == "Pass"
        assert "safe maximum" in reason.lower() or "level" in reason.lower()

    def test_allows_reasonable_game_contract(self):
        """Test that reasonable game contracts are allowed."""
        checker = SanityChecker()

        # 16 HCP, partner has 10 HCP (estimated combined 26)
        hand = create_test_hand(16, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        features = {'opener': 'partner'}
        auction = ["1NT", "Pass", "2♥", "Pass", "2♠"]  # Transfer to spades

        # 4♠ should be ALLOWED (combined ~26 HCP, game level)
        should_bid, final_bid, reason = checker.check("4♠", hand, features, auction)
        assert should_bid is True


class TestCompetitiveAuction:
    """Test sanity checks in competitive auctions."""

    def test_stops_competitive_bidding_at_4_level_with_weak_hand(self):
        """Test that competitive bidding stops at 4-level without strength."""
        checker = SanityChecker()

        # 10 HCP in competitive auction
        hand = create_test_hand(10, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        features = {'competitive_auction': True}
        auction = ["1♠", "2♥", "3♠"]

        # 4♥ should be rejected (10 HCP without partner support)
        should_bid, final_bid, reason = checker.check("4♥", hand, features, auction)
        assert should_bid is False
        assert final_bid == "Pass"

    def test_allows_competitive_4_level_with_partner_support(self):
        """Test that 4-level competitive bidding allowed with partner."""
        checker = SanityChecker()

        # 13 HCP, partner has bid (opener=partner means they have 13+)
        hand = create_test_hand(13, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        features = {'competitive_auction': True, 'opener': 'partner'}
        auction = ["1♥", "2♠", "3♥"]

        # 4♥ should be ALLOWED (combined ~26 HCP)
        should_bid, final_bid, reason = checker.check("4♥", hand, features, auction)
        assert should_bid is True


class TestTrumpFitCheck:
    """Test trump fit checking for high-level suit contracts."""

    def test_rejects_game_without_partner_support(self):
        """Test that game-level bid rejected without partner."""
        checker = SanityChecker()

        # 13 HCP but no partner support indicated
        hand = create_test_hand(13, {'♠': 3, '♥': 4, '♦': 3, '♣': 3})
        features = {}
        auction = ["1♥", "Pass", "2♥"]

        # 4♠ should be rejected (13 HCP + 0 estimated = too low for game)
        should_bid, final_bid, reason = checker.check("4♠", hand, features, auction)
        assert should_bid is False
        assert final_bid == "Pass"

    def test_allows_game_with_5_card_suit(self):
        """Test that game allowed with 5+ card suit (assumes fit)."""
        checker = SanityChecker()

        # 13 HCP with 5 spades
        hand = create_test_hand(13, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        features = {'opener': 'partner'}
        auction = ["1♣", "Pass"]

        # 4♠ should be ALLOWED (5+ spades, assumes support)
        should_bid, final_bid, reason = checker.check("4♠", hand, features, auction)
        assert should_bid is True

    def test_allows_nt_game_without_suit_fit(self):
        """Test that NT games don't check for trump fit."""
        checker = SanityChecker()

        # 16 HCP balanced
        hand = create_test_hand(16, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        features = {'opener': 'partner'}
        auction = ["1NT", "Pass"]

        # 3NT should be ALLOWED (NT doesn't need trump fit)
        should_bid, final_bid, reason = checker.check("3NT", hand, features, auction)
        assert should_bid is True


class TestSanityCheckerControl:
    """Test sanity checker enable/disable functionality."""

    def test_can_disable_sanity_checking(self):
        """Test that sanity checking can be disabled for testing."""
        checker = SanityChecker()
        checker.disable()

        # Insane bid should pass when disabled
        hand = create_test_hand(5, {'♠': 2, '♥': 2, '♦': 5, '♣': 4})
        should_bid, final_bid, reason = checker.check("7NT", hand, {}, [])
        assert should_bid is True

    def test_can_re_enable_sanity_checking(self):
        """Test that sanity checking can be re-enabled."""
        checker = SanityChecker()
        checker.disable()
        checker.enable()

        # Insane bid should be rejected when re-enabled
        hand = create_test_hand(5, {'♠': 2, '♥': 2, '♦': 5, '♣': 4})
        should_bid, final_bid, reason = checker.check("7NT", hand, {}, [])
        assert should_bid is False
