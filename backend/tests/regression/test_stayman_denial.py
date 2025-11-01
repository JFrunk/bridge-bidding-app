"""
Regression test for Stayman 2♦ denial bid.

BUG: ValidationPipeline was blocking Stayman 2♦ denial because
opener doesn't have 5+ diamonds (it's an artificial bid).

FIXED: Added metadata bypass system to allow conventions to skip suit length validation.

Date: 2025-10-31
Related: ADR-0002 Phase 2 (ValidationPipeline)
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


class TestStaymanDenial:
    """Test that Stayman denial bid (2♦) works despite suit length validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_2diamond_denial_with_only_2_diamonds(self):
        """Test 2♦ denial when opener has only 2 diamonds (no 4-card major)."""
        # Create opener with no 4-card major, only 2 diamonds
        opener_hand = Hand([
            Card('K', '♠'), Card('Q', '♠'), Card('4', '♠'),
            Card('K', '♥'), Card('9', '♥'), Card('2', '♥'),
            Card('8', '♦'), Card('2', '♦'),
            Card('A', '♣'), Card('Q', '♣'), Card('J', '♣'), Card('8', '♣'), Card('6', '♣')
        ])

        auction = ['1NT', 'Pass', '2♣', 'Pass']  # Partner asks Stayman
        bid, explanation = self.engine.get_next_bid(
            opener_hand, auction, 'North', 'None'
        )

        assert bid == '2♦', f"Expected 2♦ denial, got {bid}"
        assert "deny" in explanation.lower() or "no" in explanation.lower()

    def test_2diamond_denial_with_3_diamonds(self):
        """Test 2♦ denial when opener has 3 diamonds (no 4-card major)."""
        opener_hand = Hand([
            Card('K', '♠'), Card('Q', '♠'), Card('4', '♠'),
            Card('K', '♥'), Card('9', '♥'), Card('2', '♥'),
            Card('A', '♦'), Card('8', '♦'), Card('2', '♦'),
            Card('Q', '♣'), Card('J', '♣'), Card('8', '♣'), Card('6', '♣')
        ])

        auction = ['1NT', 'Pass', '2♣', 'Pass']
        bid, explanation = self.engine.get_next_bid(
            opener_hand, auction, 'North', 'None'
        )

        assert bid == '2♦', f"Expected 2♦ denial, got {bid}"

    def test_2heart_response_with_4_hearts(self):
        """Test that opener shows 4-card heart suit (not denial)."""
        opener_hand = Hand([
            Card('K', '♠'), Card('Q', '♠'), Card('4', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('9', '♥'), Card('2', '♥'),
            Card('8', '♦'), Card('2', '♦'),
            Card('A', '♣'), Card('Q', '♣'), Card('J', '♣'), Card('6', '♣')
        ])

        auction = ['1NT', 'Pass', '2♣', 'Pass']
        bid, explanation = self.engine.get_next_bid(
            opener_hand, auction, 'North', 'None'
        )

        assert bid == '2♥', f"Expected 2♥ showing hearts, got {bid}"
        assert "4" in explanation or "heart" in explanation.lower()

    def test_2spade_response_with_4_spades(self):
        """Test that opener shows 4-card spade suit (not denial)."""
        opener_hand = Hand([
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('4', '♠'),
            Card('K', '♥'), Card('9', '♥'), Card('2', '♥'),
            Card('8', '♦'), Card('2', '♦'),
            Card('A', '♣'), Card('Q', '♣'), Card('J', '♣'), Card('6', '♣')
        ])

        auction = ['1NT', 'Pass', '2♣', 'Pass']
        bid, explanation = self.engine.get_next_bid(
            opener_hand, auction, 'North', 'None'
        )

        assert bid == '2♠', f"Expected 2♠ showing spades, got {bid}"
        assert "4" in explanation or "spade" in explanation.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
