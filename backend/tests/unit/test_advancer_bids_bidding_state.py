"""
Unit tests for AdvancerBidsModule BiddingState integration.

Tests that the advancer uses BiddingState combined HCP to make
better game/invite decisions, especially distinguishing sound
overcalls from weak jumps.

Seat layout for all tests:
  dealer=East, me=South, partner=North, opponents=East/West
  East opens → North overcalls → South advances
"""

import pytest
from engine.advancer_bids import AdvancerBidsModule
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


def _make_features(auction, dealer='East', my_position='South'):
    """
    Build features dict with bidding_state.

    Default layout: dealer=East opens, North (partner) overcalls,
    South (me) advances.
    """
    from engine.ai.bidding_state import BiddingStateBuilder
    positions = ['North', 'East', 'South', 'West']
    my_index = positions.index(my_position)
    partner_index = (my_index + 2) % 4
    bidding_state = BiddingStateBuilder().build(auction, dealer)

    # Find opening bid and partner's last bid
    opening_bid = ''
    partner_last_bid = None
    dealer_idx = positions.index(dealer)

    for i, bid in enumerate(auction):
        bidder_idx = (dealer_idx + i) % 4
        if bid not in ('Pass', 'X', 'XX') and not opening_bid:
            opening_bid = bid
        if bidder_idx == partner_index and bid not in ('Pass',):
            partner_last_bid = bid

    return {
        'bidding_state': bidding_state,
        'positions': positions,
        'my_index': my_index,
        'auction_history': auction,
        'hand': None,
        'auction_features': {
            'opener_relationship': 'Opponent',
            'opening_bid': opening_bid,
            'partner_last_bid': partner_last_bid,
            'partner_bids': [],
            'balancing': {},
            'bid_counts': {'my_bid_count': 0, 'partner_bid_count': 0},
        },
    }


class TestAdvancerBiddingStateIntegration:
    """Test advancer's use of BiddingState for combined HCP decisions."""

    def test_combined_hcp_helper_with_overcall(self):
        """Verify _estimate_combined_with_partner for 1-level overcall."""
        module = AdvancerBidsModule()
        hand = create_test_hand(10, {'♠': 3, '♥': 3, '♦': 4, '♣': 3})
        # E opens 1♥, S passes, W passes, N overcalls 1♠, E passes
        auction = ['1♥', 'Pass', 'Pass', '1♠', 'Pass']
        features = _make_features(auction, dealer='East', my_position='South')

        combined = module._estimate_combined_with_partner(hand, features)
        # Partner (N) overcalled 1♠: (8, 16), midpoint = 12. Combined = 10+12 = 22
        assert combined == 22

    def test_combined_hcp_helper_with_weak_jump(self):
        """Verify combined HCP for weak jump overcall."""
        module = AdvancerBidsModule()
        hand = create_test_hand(10, {'♠': 3, '♥': 3, '♦': 4, '♣': 3})
        # E opens 1♥, S passes, W passes, N weak-jumps 2♠, E passes
        auction = ['1♥', 'Pass', 'Pass', '2♠', 'Pass']
        features = _make_features(auction, dealer='East', my_position='South')

        combined = module._estimate_combined_with_partner(hand, features)
        # Partner (N) weak-jumped 2♠: (6, 10), midpoint = 8. Combined = 10+8 = 18
        assert combined == 18

    def test_combined_hcp_helper_with_takeout_double(self):
        """Takeout double gives (12, 40), spread > 25, returns None."""
        module = AdvancerBidsModule()
        hand = create_test_hand(8, {'♠': 4, '♥': 3, '♦': 3, '♣': 3})
        # E opens 1♦, S passes, W passes, N doubles, E passes
        auction = ['1♦', 'Pass', 'Pass', 'X', 'Pass']
        features = _make_features(auction, dealer='East', my_position='South')

        combined = module._estimate_combined_with_partner(hand, features)
        # Partner doubled: (12, 40), spread=28 > 25, too wide
        assert combined is None

    def test_no_game_after_weak_jump_overcall(self):
        """Partner weak-jumped 2♠ (6-10 HCP), I have 12 HCP → no game."""
        module = AdvancerBidsModule()
        hand = create_test_hand(12, {'♠': 3, '♥': 3, '♦': 4, '♣': 3})
        # E opens 1♥, S passes, W passes, N weak-jumps 2♠, E passes
        auction = ['1♥', 'Pass', 'Pass', '2♠', 'Pass']
        features = _make_features(auction, dealer='East', my_position='South')
        features['hand'] = hand

        result = module._advance_suit_overcall(hand, '2♠', '1♥', features)
        # Partner (6-10 HCP), midpoint=8. Combined = 12+8 = 20. Not game.
        assert result is not None
        bid = result[0]
        assert bid != '4♠', f"Should not bid game with combined ~20 HCP, got {bid}"

    def test_game_after_sound_overcall(self):
        """Partner overcalled 1♠ (8-16 HCP), I have 14 HCP → bid game."""
        module = AdvancerBidsModule()
        hand = create_test_hand(14, {'♠': 3, '♥': 3, '♦': 4, '♣': 3})
        # E opens 1♥, S passes, W passes, N overcalls 1♠, E passes
        auction = ['1♥', 'Pass', 'Pass', '1♠', 'Pass']
        features = _make_features(auction, dealer='East', my_position='South')
        features['hand'] = hand

        result = module._advance_suit_overcall(hand, '1♠', '1♥', features)
        # Partner (8-16 HCP), midpoint=12. Combined = 14+12 = 26. Game!
        assert result is not None
        bid = result[0]
        assert bid == '4♠', f"Should bid game with combined ~26 HCP, got {bid}"

    def test_invite_in_middle_range(self):
        """Combined ~23 HCP: should invite, not bid game."""
        module = AdvancerBidsModule()
        hand = create_test_hand(11, {'♠': 3, '♥': 3, '♦': 4, '♣': 3})
        # E opens 1♥, S passes, W passes, N overcalls 1♠, E passes
        auction = ['1♥', 'Pass', 'Pass', '1♠', 'Pass']
        features = _make_features(auction, dealer='East', my_position='South')
        features['hand'] = hand

        result = module._advance_suit_overcall(hand, '1♠', '1♥', features)
        # Partner midpoint=12. Combined = 11+12 = 23. Invitational range.
        assert result is not None
        bid = result[0]
        assert bid == '3♠', f"Should invite with combined ~23, got {bid}"

    def test_fallback_when_no_bidding_state(self):
        """Without BiddingState, falls back to None (legacy path)."""
        module = AdvancerBidsModule()
        hand = create_test_hand(12, {'♠': 3, '♥': 3, '♦': 4, '♣': 3})
        features = {
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 2,
            'auction_history': [],
        }

        combined = module._estimate_combined_with_partner(hand, features)
        assert combined is None
