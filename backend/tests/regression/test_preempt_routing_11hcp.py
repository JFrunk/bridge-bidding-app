"""
Regression Test: Opening Bid Routing for 11 HCP Hands with 6+ Card Suit

Bug Report: hand_2026-01-05_23-18-41.json
Reported: 2026-01-05
Fixed: 2026-02-01

Issue: Hands with 11 HCP and a 6+ card suit were routed to the preempts
module instead of opening_bids. The preempts module only accepts 6-10 HCP,
so it returned None, causing the engine to fall back to Pass.

Root Cause: _should_preempt() in bidding_engine_v2.py used `hand.hcp >= 12`
as the threshold to skip preempts, but the preempt module's actual HCP range
is 6-10. Hands with 11 HCP fell into a gap — too strong for preempts but
still routed there.

Fix: Changed threshold from `hand.hcp >= 12` to `hand.hcp > 10` to match
the preempt module's actual range.

Test Cases:
- 11 HCP with 6-card major (AKQxxx) should open 1-level, not Pass
- 11 HCP with 6-card minor should open 1-level, not Pass
- 10 HCP with 6-card suit should still route to preempts (weak two)
- 12 HCP with 6-card suit should open 1-level (unchanged behavior)
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine_v2 import BiddingEngineV2


class TestPreemptRouting11HCP:
    """Regression tests for preempt vs opening bid routing at 11 HCP boundary."""

    @pytest.fixture
    def engine(self):
        """Create bidding engine."""
        return BiddingEngineV2()

    def test_11hcp_6card_spade_suit_opens_1s(self, engine):
        """Original bug: AKQ742 Q5 942 43 (11 HCP, 6 spades) should open 1♠."""
        hand = Hand([
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
            Card('7', '♠'), Card('4', '♠'), Card('2', '♠'),
            Card('Q', '♥'), Card('5', '♥'),
            Card('9', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('4', '♣'), Card('3', '♣'),
        ])
        assert hand.hcp == 11
        assert hand.suit_lengths['♠'] == 6

        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=[],
            my_position='North',
            vulnerability='EW',
            dealer='North'
        )
        assert bid == '1♠', f"Expected 1♠, got {bid} ({explanation})"

    def test_11hcp_6card_heart_suit_opens_1h(self, engine):
        """11 HCP with 6-card heart suit should open 1♥."""
        # A♠=4, AQJ♥=4+2+1=7, total=11
        hand = Hand([
            Card('A', '♠'), Card('5', '♠'),
            Card('A', '♥'), Card('Q', '♥'), Card('J', '♥'),
            Card('8', '♥'), Card('6', '♥'), Card('3', '♥'),
            Card('9', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('4', '♣'), Card('3', '♣'),
        ])
        assert hand.hcp == 11
        assert hand.suit_lengths['♥'] == 6

        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=[],
            my_position='North',
            vulnerability='None',
            dealer='North'
        )
        assert bid == '1♥', f"Expected 1♥, got {bid} ({explanation})"

    def test_11hcp_6card_diamond_suit_opens_1d(self, engine):
        """11 HCP with 6-card diamond suit should open 1♦."""
        # K♠=3, Q♥=2, AQ♦=4+2=6, total=11
        hand = Hand([
            Card('K', '♠'), Card('5', '♠'),
            Card('Q', '♥'), Card('3', '♥'),
            Card('A', '♦'), Card('Q', '♦'), Card('T', '♦'),
            Card('8', '♦'), Card('6', '♦'), Card('3', '♦'),
            Card('4', '♣'), Card('3', '♣'), Card('2', '♣'),
        ])
        assert hand.hcp == 11
        assert hand.suit_lengths['♦'] == 6

        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=[],
            my_position='North',
            vulnerability='None',
            dealer='North'
        )
        assert bid == '1♦', f"Expected 1♦, got {bid} ({explanation})"

    def test_10hcp_6card_suit_still_preempts(self, engine):
        """10 HCP with 6-card suit should still route to preempts (weak two)."""
        # A♠=4, KQJ♥=3+2+1=6, total=10
        hand = Hand([
            Card('A', '♠'), Card('5', '♠'),
            Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'),
            Card('8', '♥'), Card('6', '♥'), Card('3', '♥'),
            Card('9', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('4', '♣'), Card('3', '♣'),
        ])
        assert hand.hcp == 10
        assert hand.suit_lengths['♥'] == 6

        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=[],
            my_position='North',
            vulnerability='None',
            dealer='North'
        )
        # Should preempt with 2♥ (or possibly pass if weak two restrictions
        # apply), but should NOT open at the 1-level
        assert bid != '1♥', f"10 HCP hand should not open 1♥, got {bid}"

    def test_12hcp_6card_suit_opens_normally(self, engine):
        """12 HCP with 6-card suit should open at 1-level (unchanged behavior)."""
        # A♠=4, AKJ♥=4+3+1=8, total=12
        hand = Hand([
            Card('A', '♠'), Card('5', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('J', '♥'),
            Card('8', '♥'), Card('6', '♥'), Card('3', '♥'),
            Card('9', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('4', '♣'), Card('3', '♣'),
        ])
        assert hand.hcp == 12
        assert hand.suit_lengths['♥'] == 6

        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=[],
            my_position='North',
            vulnerability='None',
            dealer='North'
        )
        assert bid == '1♥', f"Expected 1♥, got {bid} ({explanation})"
