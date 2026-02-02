"""
Unit tests for the BiddingState-powered slam exploration safety net.

Tests that the slam safety net in bidding_engine.py correctly intercepts
game bids when slam values exist (33+ combined HCP using BiddingState),
and correctly stays silent when conditions aren't met.
"""

import pytest
from engine.bidding_engine import BiddingEngine
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


def _make_features(auction, dealer='North', my_position='South'):
    """Build features dict with bidding_state for slam scenarios."""
    from engine.ai.bidding_state import BiddingStateBuilder
    positions = ['North', 'East', 'South', 'West']
    my_index = positions.index(my_position)
    bidding_state = BiddingStateBuilder().build(auction, dealer)

    opening_bid = ''
    for bid in auction:
        if bid not in ('Pass', 'X', 'XX'):
            opening_bid = bid
            break

    # Determine opener relationship
    dealer_index = positions.index(dealer)
    opener_index = None
    for i, bid in enumerate(auction):
        if bid not in ('Pass', 'X', 'XX'):
            opener_index = (dealer_index + i) % 4
            break

    if opener_index is not None:
        opener_pos = positions[opener_index]
        partner_index = (my_index + 2) % 4
        partner_pos = positions[partner_index]
        if opener_pos == my_position:
            opener_rel = 'Me'
        elif opener_pos == partner_pos:
            opener_rel = 'Partner'
        else:
            opener_rel = 'Opponent'
    else:
        opener_rel = None

    return {
        'bidding_state': bidding_state,
        'positions': positions,
        'my_index': my_index,
        'auction_history': auction,
        'auction_context': None,
        'auction_features': {
            'opener_relationship': opener_rel,
            'opening_bid': opening_bid,
        },
    }


class TestSlamSafetyNetTriggers:
    """Test cases where slam safety net SHOULD trigger."""

    def test_intercept_3nt_with_slam_values_after_1nt(self):
        """Partner opened 1NT (15-17), I have 18 HCP → combined ~34, intercept 3NT."""
        engine = BiddingEngine()
        # ♠ AKJ2 ♥ AQ3 ♦ KJ4 ♣ 932 = 4+3+1+4+2+3+1 = 18
        hand = make_hand("AKJ2", "AQ3", "KJ4", "932")
        assert hand.hcp == 18

        auction = ['1NT', 'Pass', '3NT']  # I'm about to bid 3NT
        features = _make_features(auction, dealer='North', my_position='South')

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, auction, '3NT'
        )
        assert should_explore is True
        assert bid == '4NT'
        assert 'slam' in explanation.lower()

    def test_intercept_4h_with_slam_values(self):
        """Partner opened 1♥ (12-21), I have 18 HCP → combined ~34, intercept 4♥."""
        engine = BiddingEngine()
        # ♠ AK2 ♥ KQ93 ♦ AJ4 ♣ 932 = 7+5+5+0 = 17... need 18
        # ♠ AK2 ♥ KQ93 ♦ AQ4 ♣ 932 = 7+5+6+0 = 18
        hand = make_hand("AK2", "KQ93", "AQ4", "932")
        assert hand.hcp == 18

        auction = ['1♥', 'Pass', '2♥', 'Pass', '3♥', 'Pass']
        features = _make_features(auction, dealer='North', my_position='South')

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, auction, '4♥'
        )
        assert should_explore is True
        assert bid == '4NT'


class TestSlamSafetyNetNoTrigger:
    """Test cases where slam safety net should NOT trigger."""

    def test_no_trigger_below_33_combined(self):
        """Partner opened 1♥ (12-21 midpoint=16), I have 16 HCP → combined ~32, don't trigger."""
        engine = BiddingEngine()
        # ♠ AK2 ♥ Q932 ♦ AJ4 ♣ 932 = 7+2+5+0 = 14... need 16
        # ♠ AKQ ♥ J932 ♦ AJ4 ♣ 932 = 9+1+5+0 = 15... need 16
        # ♠ AKQ ♥ J932 ♦ AQ4 ♣ 932 = 9+1+6+0 = 16
        hand = make_hand("AKQ", "J932", "AQ4", "932")
        assert hand.hcp == 16

        auction = ['1♥', 'Pass', '2♥', 'Pass', '3♥', 'Pass']
        features = _make_features(auction, dealer='North', my_position='South')

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, auction, '4♥'
        )
        # Combined = 16 + 16 = 32, below 33 threshold
        assert should_explore is False

    def test_no_trigger_with_weak_own_hand(self):
        """I have only 14 HCP (below 16 threshold), don't trigger."""
        engine = BiddingEngine()
        # ♠ AK2 ♥ Q932 ♦ K54 ♣ 932 = 7+2+3+0 = 12... need 14
        # ♠ AK2 ♥ Q932 ♦ KJ4 ♣ 932 = 7+2+4+0 = 13... need 14
        # ♠ AK2 ♥ QJ32 ♦ KJ4 ♣ 932 = 7+3+4+0 = 14
        hand = make_hand("AK2", "QJ32", "KJ4", "932")
        assert hand.hcp == 14

        # Even with 2NT opener (20-21), combined = 14+20 = 34, but own HCP < 16
        auction = ['2NT', 'Pass']
        features = _make_features(auction, dealer='North', my_position='South')

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, auction, '3NT'
        )
        assert should_explore is False

    def test_no_trigger_when_partner_weak(self):
        """Partner made simple raise (6-10), don't trigger even with strong hand."""
        engine = BiddingEngine()
        # ♠ AKQJ2 ♥ AK3 ♦ AQ4 ♣ 32 = 10+7+6+0 = 23... too many
        # ♠ AKQJ2 ♥ AK3 ♦ Q54 ♣ 32 = 10+7+2+0 = 19
        hand = make_hand("AKQJ2", "AK3", "Q54", "32")
        assert hand.hcp == 19

        # I opened 1♠, partner raised to 2♠ (6-10 HCP)
        auction = ['1♠', 'Pass', '2♠', 'Pass']
        features = _make_features(auction, dealer='South', my_position='South')

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, auction, '4♠'
        )
        # Partner min HCP = 6, below 10 threshold
        assert should_explore is False

    def test_no_trigger_competitive_auction(self):
        """Opponent opened, don't trigger slam safety net."""
        engine = BiddingEngine()
        hand = make_hand("AKQ2", "AQ32", "AJ4", "32")

        auction = ['1♣', '1♠', '2♣', '3♠']
        features = _make_features(auction, dealer='North', my_position='East')

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, auction, '4♠'
        )
        assert should_explore is False

    def test_no_trigger_without_bidding_state(self):
        """Without BiddingState, safety net stays silent."""
        engine = BiddingEngine()
        hand = make_hand("AKQ2", "AQ32", "AJ4", "32")

        features = {
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 2,
            'auction_features': {
                'opener_relationship': 'Partner',
                'opening_bid': '1NT',
            },
        }

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, ['1NT', 'Pass'], '3NT'
        )
        assert should_explore is False

    def test_no_trigger_when_blackwood_already_used(self):
        """If 4NT already in auction, don't trigger again."""
        engine = BiddingEngine()
        hand = make_hand("AKJ2", "AQ3", "KJ4", "932")

        auction = ['1NT', 'Pass', '4NT', 'Pass', '5♦', 'Pass']
        features = _make_features(auction, dealer='North', my_position='South')

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, auction, '6NT'
        )
        assert should_explore is False

    def test_no_trigger_when_already_at_slam(self):
        """If a 6-level bid already in auction, don't trigger."""
        engine = BiddingEngine()
        hand = make_hand("AKJ2", "AQ3", "KJ4", "932")

        auction = ['1NT', 'Pass', '4NT', 'Pass', '5♦', 'Pass', '6♥', 'Pass']
        features = _make_features(auction, dealer='North', my_position='South')

        should_explore, bid, explanation = engine._slam_exploration_safety_net(
            hand, features, auction, '6NT'
        )
        assert should_explore is False


class TestMaxBidLevelsSlam:
    """Test that MAX_BID_LEVELS table allows slam bids with sufficient HCP."""

    def _lookup_max_level(self, combined_hcp):
        """Look up max level from MAX_BID_LEVELS table directly."""
        from engine.ai.sanity_checker import SanityChecker
        for (min_hcp, max_hcp), max_level in SanityChecker.MAX_BID_LEVELS.items():
            if min_hcp <= combined_hcp <= max_hcp:
                return max_level
        return 2

    def test_33_hcp_allows_6_level(self):
        """33 combined HCP should allow 6-level bids (small slam)."""
        assert self._lookup_max_level(33) == 6

    def test_36_hcp_allows_6_level(self):
        """36 combined HCP should allow 6-level bids."""
        assert self._lookup_max_level(36) == 6

    def test_37_hcp_allows_7_level(self):
        """37 combined HCP should allow 7-level bids (grand slam)."""
        assert self._lookup_max_level(37) == 7

    def test_32_hcp_still_capped_at_4(self):
        """32 combined HCP should still cap at 4-level (game)."""
        assert self._lookup_max_level(32) == 4

    def test_24_hcp_allows_game(self):
        """24 combined HCP should allow 4-level (game)."""
        assert self._lookup_max_level(24) == 4
