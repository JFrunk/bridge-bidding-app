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


class TestBiddingStateIntegration:
    """Test governor's use of BiddingState for HCP estimation."""

    def _make_features_with_bidding_state(self, auction, dealer='North', my_position='South'):
        """Build features dict with bidding_state included."""
        from engine.ai.bidding_state import BiddingStateBuilder
        positions = ['North', 'East', 'South', 'West']
        my_index = positions.index(my_position)
        bidding_state = BiddingStateBuilder().build(auction, dealer)
        return {
            'bidding_state': bidding_state,
            'positions': positions,
            'my_index': my_index,
            'auction_features': {
                'opener_relationship': 'Partner' if dealer == 'North' else 'Me',
                'opening_bid': auction[0] if auction else '',
            },
        }

    def test_combined_hcp_with_1nt_opening(self):
        """BiddingState knows 1NT opener is 15-17, so partner estimate = 16."""
        checker = SanityChecker()
        # I have 10 HCP as South, partner (North) opened 1NT
        hand = create_test_hand(10, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        auction = ['1NT', 'Pass']
        features = self._make_features_with_bidding_state(auction, dealer='North', my_position='South')

        combined = checker._estimate_combined_hcp(hand, features, auction)
        # Partner belief: (15, 17), midpoint = 16. Combined = 10 + 16 = 26
        assert combined == 26

    def test_combined_hcp_with_weak_two(self):
        """Weak two opener is 6-10, midpoint = 8."""
        checker = SanityChecker()
        hand = create_test_hand(12, {'♠': 3, '♥': 3, '♦': 4, '♣': 3})
        auction = ['2♥', 'Pass']
        features = self._make_features_with_bidding_state(auction, dealer='North', my_position='South')

        combined = checker._estimate_combined_hcp(hand, features, auction)
        # Partner belief: (6, 10), midpoint = 8. Combined = 12 + 8 = 20
        assert combined == 20

    def test_hard_ceiling_with_1nt_opening(self):
        """Hard ceiling uses partner max: 1NT opener max = 17."""
        checker = SanityChecker()
        hand = create_test_hand(16, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        auction = ['1NT', 'Pass']
        features = self._make_features_with_bidding_state(auction, dealer='North', my_position='South')

        ceiling = checker._calculate_hard_ceiling(hand, features, auction)
        # Partner max = 17. Ceiling = 16 + 17 = 33
        assert ceiling == 33

    def test_hard_ceiling_with_1_level_opening(self):
        """1-level suit opener max = 21."""
        checker = SanityChecker()
        hand = create_test_hand(14, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        auction = ['1♠', 'Pass']
        features = self._make_features_with_bidding_state(auction, dealer='North', my_position='South')

        ceiling = checker._calculate_hard_ceiling(hand, features, auction)
        # Partner max = 21. Ceiling = 14 + 21 = 35
        assert ceiling == 35

    def test_blocks_game_when_partner_passed_opening(self):
        """Partner passed in 1st seat (max 11 HCP), blocks game with weak hand."""
        checker = SanityChecker()
        # I have 10 HCP, partner passed (max 11)
        hand = create_test_hand(10, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        auction = ['Pass', 'Pass', '1♠', 'Pass']  # N passes, E passes, S opens
        features = self._make_features_with_bidding_state(auction, dealer='North', my_position='South')

        combined = checker._estimate_combined_hcp(hand, features, auction)
        # North passed: (0, 11), midpoint = 5. Combined = 10 + 5 = 15
        assert combined == 15

        # 4♠ should be blocked (combined 15, max level 2)
        should_bid, final_bid, reason = checker.check("4♠", hand, features, auction)
        assert should_bid is False

    def test_allows_game_when_partner_opened(self):
        """Partner opened 1♥ (12-21 HCP), game allowed with 13 HCP."""
        checker = SanityChecker()
        hand = create_test_hand(13, {'♠': 3, '♥': 4, '♦': 3, '♣': 3})
        auction = ['1♥', 'Pass']
        features = self._make_features_with_bidding_state(auction, dealer='North', my_position='South')

        combined = checker._estimate_combined_hcp(hand, features, auction)
        # Partner belief: (12, 21), midpoint = 16. Combined = 13 + 16 = 29
        assert combined == 29

        # 4♥ should be allowed
        should_bid, final_bid, reason = checker.check("4♥", hand, features, auction)
        assert should_bid is True

    def test_blocks_slam_when_partner_limited(self):
        """Partner made a simple raise (6-10 HCP), blocks slam."""
        checker = SanityChecker()
        hand = create_test_hand(18, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        auction = ['1♠', 'Pass', '2♠', 'Pass']
        features = self._make_features_with_bidding_state(auction, dealer='North', my_position='North')
        # Override my_position to North (the opener rebidding)
        features['my_index'] = 0

        ceiling = checker._calculate_hard_ceiling(hand, features, auction)
        # Hand helper caps at 16 HCP (4 aces). South raised simply: max = 10.
        # Ceiling = 16 + 10 = 26
        assert ceiling == 26

        # 6♠ should be blocked (ceiling 26, need 33)
        should_bid, final_bid, reason = checker.check("6♠", hand, features, auction)
        assert should_bid is False

    def test_competitive_opponent_overcall_awareness(self):
        """BiddingState narrows opponent overcall, helps estimate correctly."""
        checker = SanityChecker()
        hand = create_test_hand(14, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        # N opens 1♠, E overcalls 2♣
        auction = ['1♠', '2♣']
        features = self._make_features_with_bidding_state(auction, dealer='North', my_position='South')

        combined = checker._estimate_combined_hcp(hand, features, auction)
        # Partner (North) opened 1♠: (12, 21), midpoint = 16. Combined = 14 + 16 = 30
        assert combined == 30
