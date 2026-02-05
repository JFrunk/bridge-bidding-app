"""
Unit tests for RebidModule BiddingState integration.

Tests that the rebid module uses BiddingState beliefs for combined HCP
estimation when deciding whether to accept/decline raises.
"""

import pytest
from engine.rebids import RebidModule
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


def _make_features(hand, auction, dealer='South', my_position='South'):
    """Build features dict with bidding_state for rebid scenarios."""
    from engine.ai.bidding_state import BiddingStateBuilder
    positions = ['North', 'East', 'South', 'West']
    # Adjust positions so dealer is first in rotation for seat calculation
    my_index = positions.index(my_position)
    bidding_state = BiddingStateBuilder().build(auction, dealer)

    # Extract opening bid and partner's last bid
    opening_bid = ''
    partner_last_bid = ''
    partner_position = positions[(my_index + 2) % 4]

    for i, bid in enumerate(auction):
        if bid not in ('Pass', 'X', 'XX') and not opening_bid:
            opening_bid = bid
        bidder = positions[i % 4] if dealer == positions[0] else None

    # Partner's last bid (partner is 2 seats away)
    for i in range(len(auction) - 1, -1, -1):
        bidder_index = i % 4
        # Determine who bid based on dealer
        dealer_index = positions.index(dealer)
        actual_bidder_index = (dealer_index + i) % 4
        if positions[actual_bidder_index] == partner_position:
            partner_last_bid = auction[i]
            if partner_last_bid not in ('Pass', 'X', 'XX'):
                break
            # Keep looking for non-pass
            if i == 0:
                break

    return {
        'hand': hand,
        'bidding_state': bidding_state,
        'positions': positions,
        'my_index': my_index,
        'auction_history': auction,
        'auction_context': None,
        'auction_features': {
            'opener': my_position,
            'opener_relationship': 'Me',
            'opening_bid': opening_bid,
            'partner_last_bid': partner_last_bid,
        },
    }


class TestRebidBiddingStateIntegration:
    """Test rebid module's use of BiddingState for combined HCP estimation."""

    def test_accept_limit_raise_with_14_hcp(self):
        """After 1♠-3♠ (limit raise 10-12), opener with 14 HCP should bid game.

        BiddingState: partner (10,12) midpoint=11. Combined = 14+11 = 25 → game.
        Legacy: partner_hcp_midpoint=10. Combined = 14+10 = 24 → borderline.
        """
        module = RebidModule()
        # ♠ AK932 ♥ Q32 ♦ A54 ♣ 32 = A(4)+K(3)+Q(2)+A(4)+1(J missing)=14? No.
        # AK932=7, Q32=2, A54=4, 32=0 → 13. Need +1.
        # ♠ AK932 ♥ Q32 ♦ AJ4 ♣ 32 = 7+2+5+0 = 14
        hand = make_hand("AK932", "Q32", "AJ4", "32")
        assert hand.hcp == 14

        # I opened 1♠ (South), partner (North) bid 3♠
        auction = ['1♠', 'Pass', '3♠', 'Pass']
        features = _make_features(hand, auction, dealer='South', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid, explanation = result[0], result[1]
        assert bid == '4♠', f"With 14 HCP after limit raise, should bid game, got {bid}: {explanation}"

    def test_decline_limit_raise_with_12_hcp(self):
        """After 1♠-3♠ (limit raise 10-12), opener with 12 HCP should pass.

        BiddingState: partner (10,12) midpoint=11. Combined = 12+11 = 23 → decline.
        """
        module = RebidModule()
        # ♠ AQ932 ♥ J32 ♦ K54 ♣ 32 = 4+2+1+3 = 10... need 12
        # ♠ AQ932 ♥ K32 ♦ Q54 ♣ 32 = 4+2+3+2 = 11... need 12
        # ♠ AQ932 ♥ KJ2 ♦ Q54 ♣ 32 = 6+4+2 = 12
        hand = make_hand("AQ932", "KJ2", "Q54", "32")
        assert hand.hcp == 12

        auction = ['1♠', 'Pass', '3♠', 'Pass']
        features = _make_features(hand, auction, dealer='South', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid, explanation = result[0], result[1]
        assert bid == 'Pass', f"With 12 HCP after limit raise, should pass, got {bid}: {explanation}"

    def test_accept_limit_raise_with_15_hcp(self):
        """After 1♠-3♠, opener with 15 HCP should clearly bid game.

        BiddingState: partner (10,12) midpoint=11. Combined = 15+11 = 26 → game.
        """
        module = RebidModule()
        # ♠ AK932 ♥ K32 ♦ AJ4 ♣ 32 = 7+3+5 = 15
        hand = make_hand("AK932", "K32", "AJ4", "32")
        assert hand.hcp == 15

        auction = ['1♠', 'Pass', '3♠', 'Pass']
        features = _make_features(hand, auction, dealer='South', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid, explanation = result[0], result[1]
        assert bid == '4♠', f"With 15 HCP after limit raise, should bid game, got {bid}: {explanation}"

    def test_simple_raise_minimum_pass(self):
        """After 1♠-2♠ (simple raise 6-10), opener with 13 HCP should pass.

        BiddingState: partner (6,10) midpoint=8. Combined = 13+8 = 21 → pass.
        """
        module = RebidModule()
        # ♠ AQ932 ♥ K32 ♦ A54 ♣ 32 = 6+3+4 = 13
        hand = make_hand("AQ932", "K32", "A54", "32")
        assert hand.hcp == 13

        auction = ['1♠', 'Pass', '2♠', 'Pass']
        features = _make_features(hand, auction, dealer='South', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid, explanation = result[0], result[1]
        assert bid == 'Pass', f"With 13 HCP after simple raise, should pass, got {bid}: {explanation}"

    def test_fallback_without_bidding_state(self):
        """Without BiddingState, falls back to hardcoded partner midpoints."""
        module = RebidModule()
        # ♠ AK932 ♥ Q32 ♦ AJ4 ♣ 32 = 14 HCP
        hand = make_hand("AK932", "Q32", "AJ4", "32")

        # Build features WITHOUT bidding_state
        features = {
            'hand': hand,
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 2,
            'auction_history': ['1♠', 'Pass', '3♠', 'Pass'],
            'auction_context': None,
            'auction_features': {
                'opener': 'South',
                'opener_relationship': 'Me',
                'opening_bid': '1♠',
                'partner_last_bid': '3♠',
            },
        }

        result = module.evaluate(hand, features)
        assert result is not None
        bid, explanation = result[0], result[1]
        # Without BiddingState: 14 + 10 (hardcoded) = 24, borderline
        # Should still work (accept or decline based on legacy logic)
        assert bid in ('4♠', 'Pass'), f"Fallback should still produce valid bid, got {bid}"

    def test_hearts_limit_raise_game(self):
        """After 1♥-3♥ (limit raise), opener with 14 HCP bids game."""
        module = RebidModule()
        # ♠ Q32 ♥ AK932 ♦ AJ4 ♣ 32 = 2+7+5 = 14
        hand = make_hand("Q32", "AK932", "AJ4", "32")
        assert hand.hcp == 14

        auction = ['1♥', 'Pass', '3♥', 'Pass']
        features = _make_features(hand, auction, dealer='South', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid, explanation = result[0], result[1]
        assert bid == '4♥', f"With 14 HCP after hearts limit raise, should bid game, got {bid}: {explanation}"
