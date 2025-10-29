"""
Unit tests for Validation Pipeline

Tests the centralized validation system that prevents inappropriate bids.

Part of ADR-0002: Bidding System Robustness Improvements
Layer 2: Centralized Validation Pipeline
"""

import pytest
from engine.ai.validation_pipeline import (
    ValidationPipeline,
    HCPRequirementValidator,
    SuitLengthValidator,
    BidLevelAppropriatenessValidator,
    LegalityValidator,
)
from engine.hand import Hand, Card


def create_test_hand(hcp, suit_lengths):
    """Helper to create test hands."""
    cards = []
    suits = ['♠', '♥', '♦', '♣']

    # Distribute cards to match suit_lengths and approximate HCP
    for i, suit in enumerate(suits):
        length = suit_lengths[suits[i]]
        # Add some high cards to get desired HCP
        for j in range(length):
            if hcp > 0 and j == 0:
                rank = 'A' if hcp >= 4 else 'K' if hcp >= 3 else 'Q' if hcp >= 2 else 'J'
                hcp -= {'A': 4, 'K': 3, 'Q': 2, 'J': 1}.get(rank, 0)
            else:
                rank = str(9 - j % 9)
            cards.append(Card(rank=rank, suit=suit))

    return Hand(cards)


class TestValidationPipeline:
    """Test the main validation pipeline."""

    def test_pass_always_valid(self):
        """Test that Pass bid is always valid."""
        pipeline = ValidationPipeline()
        hand = create_test_hand(5, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})

        is_valid, error = pipeline.validate("Pass", hand, {}, [])
        assert is_valid is True
        assert error is None

    def test_validation_runs_all_validators(self):
        """Test that validation runs through all validators."""
        pipeline = ValidationPipeline()
        assert len(pipeline.validators) == 4

    def test_can_disable_validation(self):
        """Test that validation can be disabled for testing."""
        pipeline = ValidationPipeline()
        pipeline.disable()

        # Invalid bid should pass when disabled
        hand = create_test_hand(5, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = pipeline.validate("7NT", hand, {}, [])
        assert is_valid is True


class TestHCPRequirementValidator:
    """Test HCP requirement validation."""

    def test_competitive_double_requires_8_hcp(self):
        """Test that competitive doubles require 8+ HCP."""
        validator = HCPRequirementValidator()

        # 5 HCP - should fail
        hand_weak = create_test_hand(5, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        features = {'competitive_auction': True}
        is_valid, error = validator.validate("X", hand_weak, features, [])
        assert is_valid is False
        assert "8" in error

        # 8 HCP - should pass
        hand_ok = create_test_hand(8, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("X", hand_ok, features, [])
        assert is_valid is True

    def test_three_level_requires_10_hcp(self):
        """Test that 3-level bids require 10+ HCP."""
        validator = HCPRequirementValidator()

        # 7 HCP - should fail
        hand_weak = create_test_hand(7, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("3♣", hand_weak, {}, [])
        assert is_valid is False
        assert "10" in error

        # 10 HCP - should pass
        hand_ok = create_test_hand(10, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("3♣", hand_ok, {}, [])
        assert is_valid is True

    def test_four_level_requires_12_hcp(self):
        """Test that 4-level bids require 12+ HCP."""
        validator = HCPRequirementValidator()

        # 10 HCP - should fail
        hand_weak = create_test_hand(10, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("4♠", hand_weak, {}, [])
        assert is_valid is False
        assert "12" in error

        # 12 HCP - should pass
        hand_ok = create_test_hand(12, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("4♠", hand_ok, {}, [])
        assert is_valid is True

    def test_five_level_requires_13_hcp(self):
        """Test that 5-level bids require 13+ HCP."""
        validator = HCPRequirementValidator()

        # 10 HCP - should fail
        hand_weak = create_test_hand(10, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("5♦", hand_weak, {}, [])
        assert is_valid is False
        assert "13" in error

        # 13 HCP - should pass
        hand_ok = create_test_hand(13, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("5♦", hand_ok, {}, [])
        assert is_valid is True


class TestSuitLengthValidator:
    """Test suit length validation."""

    def test_requires_minimum_suit_length(self):
        """Test that bids require minimum suit length."""
        validator = SuitLengthValidator()

        # Bid ♥ with only 2 cards - should fail
        hand_short = create_test_hand(12, {'♠': 5, '♥': 2, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("2♥", hand_short, {}, [])
        assert is_valid is False
        assert "2 cards" in error

        # Bid ♥ with 5 cards - should pass
        hand_long = create_test_hand(12, {'♠': 3, '♥': 5, '♦': 3, '♣': 2})
        is_valid, error = validator.validate("2♥", hand_long, {}, [])
        assert is_valid is True

    def test_nt_bids_skip_length_check(self):
        """Test that NT bids don't check suit length."""
        validator = SuitLengthValidator()

        hand = create_test_hand(15, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("1NT", hand, {}, [])
        assert is_valid is True


class TestBidLevelAppropriatenessValidator:
    """Test bid level appropriateness validation."""

    def test_three_level_with_weak_hand_fails(self):
        """Test that 3-level bid with 7 points fails."""
        validator = BidLevelAppropriatenessValidator()

        # Create hand with 7 total points
        hand = create_test_hand(6, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("3♣", hand, {}, [])
        assert is_valid is False
        assert "10+" in error

    def test_four_level_with_weak_hand_fails(self):
        """Test that 4-level bid with 10 points fails."""
        validator = BidLevelAppropriatenessValidator()

        hand = create_test_hand(10, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        is_valid, error = validator.validate("4♠", hand, {}, [])
        assert is_valid is False
        assert "12+" in error

    def test_preemptive_bids_allowed(self):
        """Test that preemptive bids (long suit, weak hand) are allowed."""
        validator = BidLevelAppropriatenessValidator()

        # 8 HCP with 7-card suit - preemptive, should pass
        hand = create_test_hand(8, {'♠': 2, '♥': 7, '♦': 2, '♣': 2})
        is_valid, error = validator.validate("3♥", hand, {}, [])
        assert is_valid is True


class TestLegalityValidator:
    """Test bid legality validation."""

    def test_higher_level_is_legal(self):
        """Test that higher level bid is legal."""
        validator = LegalityValidator()

        hand = create_test_hand(13, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        auction = ["1♥"]

        is_valid, error = validator.validate("2♠", hand, {}, auction)
        assert is_valid is True

    def test_same_level_higher_suit_is_legal(self):
        """Test that same level, higher suit is legal."""
        validator = LegalityValidator()

        hand = create_test_hand(13, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        auction = ["1♣"]

        is_valid, error = validator.validate("1♠", hand, {}, auction)
        assert is_valid is True

    def test_lower_bid_is_illegal(self):
        """Test that lower bid is illegal."""
        validator = LegalityValidator()

        hand = create_test_hand(13, {'♠': 5, '♥': 3, '♦': 3, '♣': 2})
        auction = ["2♠"]

        is_valid, error = validator.validate("1♥", hand, {}, auction)
        assert is_valid is False


class TestIntegration:
    """Integration tests for full validation pipeline."""

    def test_competitive_double_with_5_hcp_rejected(self):
        """
        Regression test for issue in hand_2025-10-29_15-12-17.json.
        South doubled with 5 HCP when 8+ required.
        """
        pipeline = ValidationPipeline()

        # South's hand: 5 HCP
        hand = create_test_hand(5, {'♠': 2, '♥': 2, '♦': 5, '♣': 4})
        features = {'competitive_auction': True}
        auction = ["1NT", "Pass", "2♠"]

        is_valid, error = pipeline.validate("X", hand, features, auction)
        assert is_valid is False
        assert "HCP" in error
        assert "8" in error

    def test_appropriate_competitive_double_accepted(self):
        """Test that competitive double with 8+ HCP is accepted."""
        pipeline = ValidationPipeline()

        hand = create_test_hand(8, {'♠': 2, '♥': 4, '♦': 4, '♣': 3})
        features = {'competitive_auction': True}
        auction = ["1♠", "Pass", "2♠"]

        is_valid, error = pipeline.validate("X", hand, features, auction)
        assert is_valid is True

    def test_three_level_with_7_hcp_rejected(self):
        """
        Regression test for baseline quality score issue.
        3-level bids with only 7 points should be rejected.
        """
        pipeline = ValidationPipeline()

        hand = create_test_hand(7, {'♠': 5, '♥': 2, '♦': 2, '♣': 4})
        is_valid, error = pipeline.validate("3♣", hand, {}, [])
        assert is_valid is False

    def test_five_level_with_adequate_hcp_accepted(self):
        """Test that 5-level bid with 13+ HCP is accepted."""
        pipeline = ValidationPipeline()

        hand = create_test_hand(13, {'♠': 2, '♥': 2, '♦': 5, '♣': 4})
        is_valid, error = pipeline.validate("5♦", hand, {}, [])
        assert is_valid is True
