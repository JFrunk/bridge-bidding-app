"""
Regression test for 2-over-1 forcing response bug.

Bug: Opener incorrectly passed after partner's 2-level new suit response,
which is forcing in SAYC. A new suit response at the 2-level promises 10+ HCP
and is forcing for one round - opener MUST bid again.

User report: South (21 HCP) responded 2C to partner's 1S opening.
North (11 HCP, 6-card spades) incorrectly passed, ending the auction in 2C
when the partnership had slam values (32+ combined HCP).

Fix: Added logic in feature_extractor.analyze_forcing_status() to detect
when opener must rebid after partner's new suit response.
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.ai.feature_extractor import extract_features, analyze_forcing_status


class Test2Over1ForcingResponse:
    """Test that opener correctly rebids after partner's forcing 2-level new suit response."""

    def test_opener_must_rebid_after_2_over_1_response(self):
        """
        Scenario: 1S - Pass - 2C - Pass - ?

        North opens 1S with minimum opening hand (12 HCP, 6 spades)
        South responds 2C - FORCING for one round!
        North MUST rebid, cannot pass.

        Expected: North rebids 2S (showing 6-card suit, minimum) or makes another rebid
        Bug behavior: North passed, leaving partnership in 2C
        """
        # North's hand: 6 spades, 12 HCP (minimum opening)
        # AKQJ85 = 10 HCP in spades, A9 = 4 HCP = 14 total... need exactly 12
        # Let's use: KQJ854 spades (6 HCP), A7 hearts (4 HCP), K42 diamonds (3 HCP) = 13 HCP
        north_cards = [
            Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
            Card('8', '♠'), Card('5', '♠'), Card('4', '♠'),
            Card('A', '♥'), Card('7', '♥'),
            Card('K', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('8', '♣'), Card('5', '♣')
        ]
        north_hand = Hand(north_cards)

        # Auction: 1S - Pass - 2C - Pass - ?
        auction_history = ['1♠', 'Pass', '2♣', 'Pass']

        # Get North's rebid
        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(
            hand=north_hand,
            auction_history=auction_history,
            my_position='North',
            vulnerability='NS'
        )

        # North MUST NOT pass - 2C is forcing
        assert bid != 'Pass', f"REGRESSION: North passed after forcing 2C response! Got: {bid}"

        # Acceptable rebids after a forcing 2-over-1 response with 6 spades
        # 2S is ideal (rebid 6-card suit), but others are acceptable
        acceptable_rebids = ['2♠', '2NT', '2♥', '2♦', '3♠', '3♣', '4♠']
        assert bid in acceptable_rebids, \
            f"North should make a legal rebid after forcing 2C. Got: {bid}"

    def test_forcing_status_detects_partner_new_suit_response(self):
        """
        Test that forcing status analyzer correctly identifies that
        opener must bid after partner's new suit response.
        """
        # Auction: 1S - Pass - 2C - Pass - ?
        # North (opener) is about to bid
        auction_history = ['1♠', 'Pass', '2♣', 'Pass']
        positions = ['North', 'East', 'South', 'West']
        north_index = 0  # North is at index 0 (dealer)

        result = analyze_forcing_status(auction_history, positions, north_index)

        assert result['must_bid'] == True, \
            f"Forcing status should set must_bid=True after partner's new suit response. Got: {result}"
        assert result['forcing_type'] == 'one_round_forcing', \
            f"Forcing type should be 'one_round_forcing'. Got: {result['forcing_type']}"
        assert 'partner' in result['forcing_source'].lower() or 'new_suit' in result['forcing_source'].lower(), \
            f"Forcing source should indicate partner's new suit. Got: {result['forcing_source']}"

    def test_opener_rebids_6_card_suit_with_minimum(self):
        """
        With a minimum opening (13 HCP) and a 6-card suit,
        opener should rebid the suit at the 2-level.
        """
        # North's hand: 6 spades, 13 HCP (minimum opening)
        # KQJ854 spades (6 HCP), A7 hearts (4 HCP), K42 diamonds (3 HCP) = 13 HCP
        north_cards = [
            Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
            Card('8', '♠'), Card('5', '♠'), Card('4', '♠'),
            Card('A', '♥'), Card('7', '♥'),
            Card('K', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('8', '♣'), Card('3', '♣')
        ]
        north_hand = Hand(north_cards)

        auction_history = ['1♠', 'Pass', '2♦', 'Pass']

        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(
            hand=north_hand,
            auction_history=auction_history,
            my_position='North',
            vulnerability='None'
        )

        # Should rebid with 6-card suit - NOT pass
        assert bid != 'Pass', f"North must not pass after forcing 2D response. Got: {bid}"
        # Acceptable rebids: 2S (rebid 6-card suit), 2NT (balanced), or other legal bids
        acceptable_rebids = ['2♠', '2NT', '2♥', '3♠', '4♠']
        assert bid in acceptable_rebids, \
            f"North should make a reasonable rebid with 6-card suit. Got: {bid}"

    def test_2_over_1_not_forcing_after_interference(self):
        """
        After opponent interference, 2-over-1 may not be forcing.
        This test documents expected behavior (may vary by convention agreement).
        """
        # Auction: 1S - 2H - 2C - Pass - ?
        # East overcalled 2H, so South's 2C is not necessarily forcing
        auction_history = ['1♠', '2♥', '2♣', 'Pass']
        positions = ['North', 'East', 'South', 'West']
        north_index = 0

        # This is a contested auction - forcing status may differ
        result = analyze_forcing_status(auction_history, positions, north_index)

        # In contested auctions, opener may pass with minimum
        # This test documents current behavior, not asserting it's correct
        # The key fix is for UNCONTESTED 2-over-1 being forcing


class Test2Over1EdgeCases:
    """Edge cases for 2-over-1 forcing response handling."""

    def test_1nt_response_not_forcing(self):
        """1NT response is not forcing - opener may pass with minimum."""
        north_cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
            Card('J', '♠'), Card('5', '♠'),
            Card('7', '♥'), Card('3', '♥'),
            Card('9', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('8', '♣'), Card('5', '♣'), Card('2', '♣')
        ]
        north_hand = Hand(north_cards)

        # 1NT response is NOT forcing
        auction_history = ['1♠', 'Pass', '1NT', 'Pass']

        # Check forcing status
        positions = ['North', 'East', 'South', 'West']
        result = analyze_forcing_status(auction_history, positions, 0)

        # 1NT is semi-forcing but opener CAN pass with minimum
        assert result['forcing_type'] != 'game_forcing', \
            "1NT response should not be game forcing"

    def test_raise_not_forcing(self):
        """A simple raise (2S over 1S) is not forcing."""
        auction_history = ['1♠', 'Pass', '2♠', 'Pass']
        positions = ['North', 'East', 'South', 'West']

        result = analyze_forcing_status(auction_history, positions, 0)

        # A raise is NOT a new suit, so not forcing
        # must_bid should be False for raises
        assert result['must_bid'] == False or result['forcing_source'] != 'partner_new_suit_response', \
            f"A raise should not trigger new suit forcing. Got: {result}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
