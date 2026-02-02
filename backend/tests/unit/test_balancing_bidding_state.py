"""
Unit tests for BalancingModule BiddingState integration.

Tests that the balancing module uses BiddingState beliefs to compute
partner's likely HCP instead of the flat +3 (Borrowed King) offset.
"""

import pytest
from engine.balancing import BalancingModule
from engine.hand import Hand, Card


def create_test_hand(hcp, suit_lengths):
    """Helper to create test hands with approximate HCP."""
    cards = []
    suits = ['♠', '♥', '♦', '♣']
    remaining_hcp = hcp

    for suit in suits:
        length = suit_lengths[suit]
        for j in range(length):
            if remaining_hcp > 0 and j == 0:
                rank = 'A' if remaining_hcp >= 4 else 'K' if remaining_hcp >= 3 else 'Q' if remaining_hcp >= 2 else 'J'
                remaining_hcp -= {'A': 4, 'K': 3, 'Q': 2, 'J': 1}.get(rank, 0)
            else:
                rank = str(9 - j % 9)
            cards.append(Card(rank=rank, suit=suit))

    return Hand(cards)


def _make_features(auction, dealer='North', my_position='South'):
    """Build features dict with bidding_state for balancing scenarios."""
    from engine.ai.bidding_state import BiddingStateBuilder
    positions = ['North', 'East', 'South', 'West']
    my_index = positions.index(my_position)
    bidding_state = BiddingStateBuilder().build(auction, dealer)

    opening_bid = ''
    for bid in auction:
        if bid not in ('Pass', 'X', 'XX'):
            opening_bid = bid
            break

    return {
        'bidding_state': bidding_state,
        'positions': positions,
        'my_index': my_index,
        'auction_history': auction,
        'auction_features': {
            'opener_relationship': 'Opponent',
            'opening_bid': opening_bid,
            'balancing': {
                'is_balancing': True,
                'hcp_adjustment': -3,
                'reason': 'pass_out_seat_after_opponent_bid',
            },
        },
    }


class TestBalancingBiddingStateIntegration:
    """Test balancing module's use of BiddingState for partner estimation."""

    def test_partner_estimate_after_1_level_opening(self):
        """After 1♥ opening (12-21), responder passed (0-5): partner ~12 HCP."""
        module = BalancingModule()
        hand = create_test_hand(10, {'♠': 5, '♥': 2, '♦': 3, '♣': 3})
        # North opens 1♥, East passes, South passes, now West (me) balances
        auction = ['1♥', 'Pass', 'Pass']
        features = _make_features(auction, dealer='North', my_position='West')

        partner_est = module._estimate_partner_hcp(hand, features)
        # LHO (North) opened 1♥: (12, 21), midpoint=16
        # RHO (South) passed: (0, 5), midpoint=2
        # Partner est = 40 - 10 - 16 - 2 = 12
        assert partner_est == 12

    def test_partner_estimate_after_weak_two(self):
        """After weak 2♥ (6-10), responder passed: partner has more values."""
        module = BalancingModule()
        hand = create_test_hand(10, {'♠': 5, '♥': 2, '♦': 3, '♣': 3})
        # North opens 2♥ (weak), East passes, South passes
        auction = ['2♥', 'Pass', 'Pass']
        features = _make_features(auction, dealer='North', my_position='West')

        partner_est = module._estimate_partner_hcp(hand, features)
        # LHO opened 2♥: (6, 10), midpoint=8
        # RHO passed: (0, 5), midpoint=2
        # Partner est = 40 - 10 - 8 - 2 = 20
        assert partner_est == 20

    def test_partner_estimate_after_1nt_opening(self):
        """After 1NT (15-17), responder passed: partner ~11 HCP."""
        module = BalancingModule()
        hand = create_test_hand(10, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        # North opens 1NT, East passes, South passes
        auction = ['1NT', 'Pass', 'Pass']
        features = _make_features(auction, dealer='North', my_position='West')

        partner_est = module._estimate_partner_hcp(hand, features)
        # LHO opened 1NT: (15, 17), midpoint=16
        # RHO passed: (0, 5), midpoint=2
        # Partner est = 40 - 10 - 16 - 2 = 12
        assert partner_est == 12

    def test_fallback_without_bidding_state(self):
        """Without BiddingState, falls back to VIRTUAL_OFFSET (3)."""
        module = BalancingModule()
        hand = create_test_hand(10, {'♠': 5, '♥': 2, '♦': 3, '♣': 3})
        features = {
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 3,
            'auction_history': ['1♥', 'Pass', 'Pass'],
            'auction_features': {
                'opener_relationship': 'Opponent',
                'opening_bid': '1♥',
                'balancing': {'is_balancing': True},
            },
        }

        partner_est = module._estimate_partner_hcp(hand, features)
        assert partner_est == 3  # Default Borrowed King

    def test_more_aggressive_after_weak_opening(self):
        """After weak opening, partner_est is higher → more aggressive."""
        module = BalancingModule()
        hand = create_test_hand(10, {'♠': 5, '♥': 2, '♦': 3, '♣': 3})

        # Compare 1-level vs weak two
        auction_1level = ['1♥', 'Pass', 'Pass']
        features_1level = _make_features(auction_1level, dealer='North', my_position='West')
        est_1level = module._estimate_partner_hcp(hand, features_1level)

        auction_weak = ['2♥', 'Pass', 'Pass']
        features_weak = _make_features(auction_weak, dealer='North', my_position='West')
        est_weak = module._estimate_partner_hcp(hand, features_weak)

        # Against weak two, partner should have MORE values
        assert est_weak > est_1level
