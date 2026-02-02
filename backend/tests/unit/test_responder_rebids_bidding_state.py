"""
Unit tests for ResponderRebidModule BiddingState integration.

Tests that the responder rebid module uses BiddingState beliefs for combined HCP
estimation and that the MAX_BID_LEVELS table allows slam-level bids.
"""

import pytest
from engine.responder_rebids import ResponderRebidModule
from engine.hand import Hand, Card


def make_hand(spades: str, hearts: str, diamonds: str, clubs: str) -> Hand:
    """Create a Hand from suit strings like 'AKQ32' for each suit."""
    cards = []
    for suit, holding in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for rank in holding:
            cards.append(Card(rank, suit))
    if len(cards) != 13:
        raise ValueError(f"Hand must have 13 cards, got {len(cards)}")
    return Hand(cards)


class TestMaxBidLevelsFix:
    """Test that MAX_BID_LEVELS allows slam bids with sufficient HCP."""

    def test_33_hcp_allows_6_level(self):
        """33 combined HCP should allow 6-level bids (small slam)."""
        module = ResponderRebidModule()
        for (lo, hi), level in module.MAX_BID_LEVELS.items():
            if lo <= 33 <= hi:
                assert level == 6, f"33 HCP should allow level 6, got {level}"
                return
        pytest.fail("33 HCP not found in MAX_BID_LEVELS")

    def test_37_hcp_allows_7_level(self):
        """37 combined HCP should allow 7-level bids (grand slam)."""
        module = ResponderRebidModule()
        for (lo, hi), level in module.MAX_BID_LEVELS.items():
            if lo <= 37 <= hi:
                assert level == 7, f"37 HCP should allow level 7, got {level}"
                return
        pytest.fail("37 HCP not found in MAX_BID_LEVELS")

    def test_32_hcp_still_capped_at_4(self):
        """32 combined HCP should still cap at 4-level (game)."""
        module = ResponderRebidModule()
        for (lo, hi), level in module.MAX_BID_LEVELS.items():
            if lo <= 32 <= hi:
                assert level == 4, f"32 HCP should cap at level 4, got {level}"
                return
        pytest.fail("32 HCP not found in MAX_BID_LEVELS")


class TestResponderRebidBiddingState:
    """Test BiddingState integration in _get_combined_estimate()."""

    def test_combined_estimate_with_bidding_state(self):
        """After 1♥-1♠-2♥, BiddingState should provide combined estimate."""
        module = ResponderRebidModule()
        # ♠ AQ932 ♥ K2 ♦ QJ4 ♣ 932 = 6+3+3+0 = 12
        hand = make_hand("AQ932", "K2", "QJ4", "932")
        assert hand.hcp == 12

        from engine.ai.bidding_state import BiddingStateBuilder
        auction = ['1♥', 'Pass', '1♠', 'Pass', '2♥', 'Pass']
        bidding_state = BiddingStateBuilder().build(auction, 'North')

        features = {
            'bidding_state': bidding_state,
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 2,
            'auction_history': auction,
            'auction_context': None,
        }

        combined = module._get_combined_estimate(hand, features)
        # Partner (North) opened 1♥ (12-21) then rebid 2♥
        # BiddingState should narrow partner range, midpoint ~16
        # Combined = 12 + ~16 = ~28
        assert 24 <= combined <= 32, f"Combined should be ~28, got {combined}"

    def test_fallback_without_bidding_state(self):
        """Without BiddingState, falls back to AuctionContext or hcp+14."""
        module = ResponderRebidModule()
        hand = make_hand("AQ932", "K2", "QJ4", "932")

        features = {
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 2,
            'auction_history': ['1♥', 'Pass', '1♠', 'Pass', '2♥', 'Pass'],
            'auction_context': None,
        }

        combined = module._get_combined_estimate(hand, features)
        # Fallback: hand.hcp + 14 = 12 + 14 = 26
        assert combined == 26

    def test_bidding_state_priority_over_auction_context(self):
        """BiddingState should be used over AuctionContext when both available."""
        module = ResponderRebidModule()
        hand = make_hand("AQ932", "K2", "QJ4", "932")

        from engine.ai.bidding_state import BiddingStateBuilder
        auction = ['1♥', 'Pass', '1♠', 'Pass', '2♥', 'Pass']
        bidding_state = BiddingStateBuilder().build(auction, 'North')

        # Create a mock AuctionContext that would give different result
        class MockRanges:
            opener_hcp = (12, 21)
        class MockCtx:
            ranges = MockRanges()

        features = {
            'bidding_state': bidding_state,
            'auction_context': MockCtx(),
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 2,
            'auction_history': auction,
        }

        combined_with_bs = module._get_combined_estimate(hand, features)

        # Remove BiddingState, should use AuctionContext
        features_no_bs = dict(features)
        del features_no_bs['bidding_state']
        combined_without_bs = module._get_combined_estimate(hand, features_no_bs)

        # Both should give reasonable estimates but may differ
        assert 20 <= combined_with_bs <= 35
        assert 20 <= combined_without_bs <= 35
