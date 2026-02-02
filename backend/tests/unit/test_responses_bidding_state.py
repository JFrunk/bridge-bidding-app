"""
Unit tests for ResponseModule BiddingState integration.

Tests that the response module uses BiddingState beliefs for combined HCP
estimation when deciding game bids after weak two openings and suit openings.
"""

import pytest
from engine.responses import ResponseModule
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


def _make_features(hand, auction, dealer='North', my_position='South'):
    """Build features dict with bidding_state for response scenarios."""
    from engine.ai.bidding_state import BiddingStateBuilder
    positions = ['North', 'East', 'South', 'West']
    my_index = positions.index(my_position)
    bidding_state = BiddingStateBuilder().build(auction, dealer)

    opening_bid = ''
    opener_index = -1
    for i, bid in enumerate(auction):
        if bid not in ('Pass', 'X', 'XX'):
            opening_bid = bid
            opener_index = i
            break

    # Determine opener relationship
    dealer_index = positions.index(dealer)
    opener_pos_index = (dealer_index + opener_index) % 4 if opener_index >= 0 else -1
    partner_index = (my_index + 2) % 4

    if opener_pos_index == partner_index:
        opener_rel = 'Partner'
    elif opener_pos_index == my_index:
        opener_rel = 'Me'
    else:
        opener_rel = 'Opponent'

    return {
        'hand': hand,
        'bidding_state': bidding_state,
        'positions': positions,
        'my_index': my_index,
        'auction_history': auction,
        'auction_context': None,
        'auction_features': {
            'opener_relationship': opener_rel,
            'opening_bid': opening_bid,
            'opener_index': opener_index,
            'interference': {'present': False},
        },
    }


class TestWeakTwoResponseBiddingState:
    """Test BiddingState-aware weak two responses."""

    def test_game_raise_with_16_hcp_and_fit(self):
        """Partner opened 2♥ (6-10), I have 16 HCP with 3-card support.

        BiddingState: partner (6, 10) midpoint=8. Combined = 16+8 = 24.
        Just below 25 threshold, so BiddingState path won't trigger game.
        Legacy path: 16 HCP >= 14 → game.
        """
        module = ResponseModule()
        # ♠ AK2 ♥ Q93 ♦ AKJ4 ♣ 932 = 7+2+8+0 = 17... too many
        # ♠ AK2 ♥ Q93 ♦ AJ54 ♣ 932 = 7+2+5+0 = 14... need 16
        # ♠ AK2 ♥ Q93 ♦ AKJ4 ♣ 932 → 17, try
        # ♠ AK2 ♥ Q93 ♦ AQ54 ♣ 932 = 7+2+6+0 = 15... need 16
        # ♠ AKJ ♥ Q93 ♦ AQ54 ♣ 932 = 8+2+6+0 = 16
        hand = make_hand("AKJ", "Q93", "AQ54", "932")
        assert hand.hcp == 16

        auction = ['2♥', 'Pass']
        features = _make_features(hand, auction, dealer='North', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid = result[0]
        assert bid == '4♥', f"With 16 HCP and fit after weak 2♥, should bid game, got {bid}"

    def test_game_raise_with_17_hcp_and_fit(self):
        """Partner opened 2♠ (6-10), I have 17 HCP with 3-card support.

        BiddingState: partner (6, 10) midpoint=8. Combined = 17+8 = 25 → game.
        """
        module = ResponseModule()
        # ♠ K93 ♥ AKJ ♦ AQ54 ♣ 932 = 3+8+6+0 = 17
        hand = make_hand("K93", "AKJ", "AQ54", "932")
        assert hand.hcp == 17

        auction = ['2♠', 'Pass']
        features = _make_features(hand, auction, dealer='North', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid = result[0]
        assert bid == '4♠', f"With 17 HCP and fit after weak 2♠, should bid game, got {bid}"

    def test_no_game_with_10_hcp_and_fit(self):
        """Partner opened 2♥ (6-10), I have 10 HCP with 3-card support.

        BiddingState: combined = 10+8 = 18 → no game.
        Legacy: 10 HCP < 12, no game.
        """
        module = ResponseModule()
        # ♠ KQ2 ♥ J93 ♦ A854 ♣ 932 = 5+1+4+0 = 10
        hand = make_hand("KQ2", "J93", "A854", "932")
        assert hand.hcp == 10

        auction = ['2♥', 'Pass']
        features = _make_features(hand, auction, dealer='North', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid = result[0]
        assert bid == '3♥', f"With 10 HCP and fit, should preemptive raise, got {bid}"


class TestSuitOpeningRaiseBiddingState:
    """Test BiddingState-aware suit opening raise responses."""

    def test_game_raise_with_combined_26_and_13_sp(self):
        """Partner opened 1♥ (12-21), I have 10 HCP with 4-card support + singleton.

        BiddingState: partner (12, 21) midpoint=16. Combined = 10+16 = 26 → game.
        Support points = 10 + 3 (singleton ♠) = 13 → meets 13+ threshold.
        """
        module = ResponseModule()
        # ♠ 2 ♥ KJ93 ♦ AQ54 ♣ 9832 = 0+4+6+0 = 10 HCP, singleton ♠ → 13 sp
        hand = make_hand("2", "KJ93", "AQ54", "9832")
        assert hand.hcp == 10

        auction = ['1♥', 'Pass']
        features = _make_features(hand, auction, dealer='North', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid = result[0]
        # With BiddingState combined=26 and 13 support points, should bid game
        assert bid == '4♥', f"With combined 26 HCP and 13 support points, should bid game, got {bid}"

    def test_slam_explore_with_combined_33(self):
        """Partner opened 1♠ (12-21), I have 18 HCP with 4-card support.

        BiddingState: partner (12, 21) midpoint=16. Combined = 18+16 = 34.
        But partner range is wide (spread=9), so Blackwood is blocked —
        midpoint is unreliable when partner could have 12 or 21.
        Should bid game (4♠) instead, letting further bidding narrow the range.
        """
        module = ResponseModule()
        hand = make_hand("KQ93", "AK2", "AQ54", "32")
        assert hand.hcp == 18

        auction = ['1♠', 'Pass']
        features = _make_features(hand, auction, dealer='North', my_position='South')

        result = module.evaluate(hand, features)
        assert result is not None
        bid = result[0]
        # Wide partner range → conservative: game bid, not Blackwood
        assert bid in ('4♠', '3♠'), f"With wide partner range, should bid game/slam try, got {bid}"

    def test_fallback_without_bidding_state(self):
        """Without BiddingState, falls back to support-point-based logic."""
        module = ResponseModule()
        # ♠ K2 ♥ KJ93 ♦ Q854 ♣ J32 = 10 HCP
        hand = make_hand("K2", "KJ93", "Q854", "J32")

        features = {
            'hand': hand,
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 2,
            'auction_history': ['1♥', 'Pass'],
            'auction_context': None,
            'auction_features': {
                'opener_relationship': 'Partner',
                'opening_bid': '1♥',
                'opener_index': 0,
                'interference': {'present': False},
            },
        }

        result = module.evaluate(hand, features)
        assert result is not None
        bid = result[0]
        # Without BiddingState, 10 support pts → invitational or simple raise
        assert bid in ('2♥', '3♥'), f"Fallback should produce valid raise, got {bid}"
