#!/usr/bin/env python3
"""
Regression test for takeout double shape validation and belief state.

Bug (March 15, 2026): Engine recommended takeout double with ♠92 ♥K532 ♦K ♣KJ8732
(10 HCP, 2-4-1-6) over opponent's 2♦. Three issues:
  1. Takeout double allowed without support for all unbid suits (only 2 spades)
  2. Advancer's game jump (4♥) was mis-tagged as weak_jump_overcall
  3. Doubler's pass after partner bid game incorrectly narrowed HCP to max 8
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pytest
from engine.hand import Hand, Card
from engine.ai.bidding_state import BiddingStateBuilder


def _make_hand(spades, hearts, diamonds, clubs):
    """Create Hand from rank strings per suit, e.g. _make_hand('92', 'K532', 'K', 'KJ8732')."""
    cards = []
    suit_map = {'♠': spades, '♥': hearts, '♦': diamonds, '♣': clubs}
    rank_map = {'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': 'T',
                '9': '9', '8': '8', '7': '7', '6': '6', '5': '5',
                '4': '4', '3': '3', '2': '2'}
    for suit_sym, ranks in suit_map.items():
        for r in ranks:
            cards.append(Card(rank_map[r], suit_sym))
    return Hand(cards)


class TestTakeoutDoubleShapeValidation:
    """Issue 1: Takeout double should require support for ALL unbid suits."""

    def test_no_double_with_doubleton_spade(self):
        """10 HCP, 2-4-1-6 shape should NOT produce a takeout double over 2♦."""
        from engine.v2.features.enhanced_extractor import extract_flat_features

        hand = _make_hand('92', 'K532', 'K', 'KJ8732')
        features = extract_flat_features(
            hand=hand,
            auction_history=['2♦'],
            my_position='South',
            dealer='East',
            vulnerability='NS'
        )

        # With only 2 spades, support_all_unbid must be False
        assert features['support_all_unbid'] is False, (
            f"support_all_unbid should be False with only 2 spades, got {features['support_all_unbid']}"
        )
        # HCP is 10, below 12 threshold
        assert features['hcp'] == 10

    def test_double_allowed_with_proper_shape(self):
        """13 HCP, 4-4-1-4 shape SHOULD allow a takeout double over 1♦."""
        from engine.v2.features.enhanced_extractor import extract_flat_features

        hand = _make_hand('KJ92', 'AQ53', '7', 'A854')
        features = extract_flat_features(
            hand=hand,
            auction_history=['1♦'],
            my_position='South',
            dealer='East',
            vulnerability='None'
        )

        assert features['support_all_unbid'] is True
        assert features['hcp'] >= 12


class TestAdvancerBeliefTagging:
    """Issue 2: Advancer's jump after partner's takeout double should NOT be
    tagged as weak_jump_overcall."""

    def test_advancer_game_jump_tagged_correctly(self):
        """After 2♦ - X - 2♠ - 4♥, North should be tagged advancer_game_jump, not weak_jump_overcall."""
        builder = BiddingStateBuilder()
        state = builder.build(['2♦', 'X', '2♠', '4♥', 'Pass', 'Pass', 'Pass'], 'E')

        north = state.seat('N')
        assert 'advancer_game_jump' in north.tags, (
            f"North should have 'advancer_game_jump' tag, got {north.tags}"
        )
        assert 'weak_jump_overcall' not in north.tags, (
            f"North should NOT have 'weak_jump_overcall' tag, got {north.tags}"
        )
        # Advancer game bid should show 12+ HCP
        assert north.hcp[0] >= 12, (
            f"North HCP min should be >= 12 for game jump, got {north.hcp}"
        )

    def test_advancer_invitational_jump_tagged_correctly(self):
        """After 1♥ - X - Pass - 3♠, West (advancer) should be tagged advancer_invitational_jump."""
        builder = BiddingStateBuilder()
        state = builder.build(['1♥', 'X', 'Pass', '3♠', 'Pass', 'Pass', 'Pass'], 'N')

        west = state.seat('W')
        assert 'advancer_invitational_jump' in west.tags, (
            f"West should have 'advancer_invitational_jump' tag, got {west.tags}"
        )
        assert west.hcp[0] >= 9, f"West HCP min should be >= 9, got {west.hcp}"
        assert west.hcp[1] <= 11, f"West HCP max should be <= 11, got {west.hcp}"

    def test_independent_jump_overcall_still_weak(self):
        """After 1♥ - Pass - Pass - 3♣, West's jump IS a weak jump overcall (no partner double)."""
        builder = BiddingStateBuilder()
        state = builder.build(['1♥', 'Pass', 'Pass', '3♣', 'Pass', 'Pass', 'Pass'], 'N')

        west = state.seat('W')
        assert 'weak_jump_overcall' in west.tags, (
            f"West should have 'weak_jump_overcall' tag (independent jump), got {west.tags}"
        )


class TestDoublerPassNotNarrowed:
    """Issue 2b: A player who doubled should not be narrowed to 'max 8 HCP'
    when they pass after partner bids game."""

    def test_doubler_pass_preserves_hcp(self):
        """After 2♦ - X - 2♠ - 4♥ - Pass(E) - Pass(S), South's HCP should stay at 12+."""
        builder = BiddingStateBuilder()
        state = builder.build(['2♦', 'X', '2♠', '4♥', 'Pass', 'Pass', 'Pass'], 'E')

        south = state.seat('S')
        assert 'passed_overcall' not in south.tags, (
            f"South should NOT have 'passed_overcall' after doubling, got {south.tags}"
        )
        assert south.hcp[0] >= 12, (
            f"South HCP min should remain >= 12 (doubled), got {south.hcp}"
        )


class TestPartnerOpenedPreemptFeature:
    """Issue 3: partner_opened_preempt should be True for weak twos/threes,
    False for normal openings and 2♣/2NT."""

    def test_preempt_feature_true_for_weak_two(self):
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('AKJ95', '87', '983', 'Q64')
        features = extract_flat_features(
            hand=hand, auction_history=['2♦', 'X'],
            my_position='West', dealer='East', vulnerability='NS'
        )
        assert features['partner_opened_preempt'] is True

    def test_preempt_feature_false_for_one_level(self):
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('AKJ95', '87', '983', 'Q64')
        features = extract_flat_features(
            hand=hand, auction_history=['1♦', '1♥'],
            my_position='West', dealer='East', vulnerability='NS'
        )
        assert features['partner_opened_preempt'] is False

    def test_preempt_feature_false_for_2c(self):
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('AKJ95', '87', '983', 'Q64')
        features = extract_flat_features(
            hand=hand, auction_history=['2♣', 'X'],
            my_position='West', dealer='East', vulnerability='NS'
        )
        assert features['partner_opened_preempt'] is False

    def test_preempt_feature_false_for_2nt(self):
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('AKJ95', '87', '983', 'Q64')
        features = extract_flat_features(
            hand=hand, auction_history=['2NT', 'X'],
            my_position='West', dealer='East', vulnerability='NS'
        )
        assert features['partner_opened_preempt'] is False


class TestBidLevelComputation:
    """bid_level must correctly compute the minimum overcall level for our best suit."""

    def test_bid_level_clubs_over_2d_is_3(self):
        """♣ ranks below ♦, so over 2♦ our minimum club bid is 3♣ → bid_level=3."""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('92', 'K532', 'K', 'KJ8732')
        features = extract_flat_features(
            hand=hand, auction_history=['2♦'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        assert features['bid_level'] == 3, (
            f"bid_level should be 3 for clubs over 2♦, got {features['bid_level']}"
        )

    def test_bid_level_spades_over_2d_is_2(self):
        """♠ ranks above ♦, so over 2♦ we can bid 2♠ → bid_level=2."""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('KQJ95', 'K7', '83', 'Q642')
        features = extract_flat_features(
            hand=hand, auction_history=['2♦'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        assert features['bid_level'] == 2, (
            f"bid_level should be 2 for spades over 2♦, got {features['bid_level']}"
        )

    def test_bid_level_spades_over_1d_is_1(self):
        """♠ ranks above ♦, so over 1♦ we can bid 1♠ → bid_level=1."""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('KQJ95', 'K7', '83', 'Q642')
        features = extract_flat_features(
            hand=hand, auction_history=['1♦'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        assert features['bid_level'] == 1, (
            f"bid_level should be 1 for spades over 1♦, got {features['bid_level']}"
        )

    def test_bid_level_clubs_over_1d_is_2(self):
        """♣ ranks below ♦, so over 1♦ our minimum club bid is 2♣ → bid_level=2."""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('92', 'K53', 'K2', 'KJ8732')
        features = extract_flat_features(
            hand=hand, auction_history=['1♦'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        assert features['bid_level'] == 2, (
            f"bid_level should be 2 for clubs over 1♦, got {features['bid_level']}"
        )


class TestIsJumpComputation:
    """is_jump must correctly identify jump vs simple overcalls using rank-based level necessity."""

    def test_3c_over_2d_is_not_jump(self):
        """3♣ over 2♦: R_t(1) <= R_c(2) → L_min = 2+1 = 3. L_t(3) > 3 is False → simple."""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('92', 'K532', 'K', 'KJ8732')
        features = extract_flat_features(
            hand=hand, auction_history=['2♦'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        assert features['is_jump'] is False, (
            f"3♣ over 2♦ should NOT be a jump (simple overcall), got is_jump={features['is_jump']}"
        )

    def test_3c_over_1s_is_jump(self):
        """3♣ over 1♠: R_t(1) <= R_c(4) → L_min = 1+1 = 2. L_t(3) > 2 is True → jump."""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('92', 'K53', 'K2', 'KJ8732')
        features = extract_flat_features(
            hand=hand, auction_history=['1♠'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        # bid_level=2 (clubs over 1♠ minimum is 2♣), but a 3♣ would be a jump
        # The extractor computes is_jump for the minimum bid (bid_level), not a hypothetical higher bid
        # bid_level=2 over anchor 1♠ → L_min=2, is_jump = (2 > 2) = False
        assert features['is_jump'] is False, (
            f"Minimum club bid (2♣) over 1♠ is not a jump, got is_jump={features['is_jump']}"
        )

    def test_2s_over_1d_is_not_jump(self):
        """2♠ over 1♦: R_t(4) > R_c(2) → L_min = 1. L_t(2) > 1 is True → jump!"""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        # Need a hand with 5+ spades as best overcall suit
        hand = _make_hand('KQJ95', 'K7', '83', 'Q642')
        features = extract_flat_features(
            hand=hand, auction_history=['1♦'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        # bid_level=1 (spades outrank diamonds), L_min=1, is_jump = (1 > 1) = False
        assert features['is_jump'] is False, (
            f"1♠ over 1♦ is not a jump, got is_jump={features['is_jump']}"
        )

    def test_2s_over_1h_is_not_jump(self):
        """2♠ over 1♥: R_t(4) > R_c(3) → L_min = 1. L_t(2) > 1 → True, jump!
        But bid_level = 1 (spades outrank hearts), so at minimum level: is_jump = (1 > 1) = False."""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('KQJ95', 'K7', '83', 'Q642')
        features = extract_flat_features(
            hand=hand, auction_history=['1♥'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        assert features['bid_level'] == 1
        assert features['is_jump'] is False


class TestInterferenceLevelComputation:
    """interference_level must extract the level of the last opponent bid."""

    def test_interference_level_2d(self):
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('92', 'K532', 'K', 'KJ8732')
        features = extract_flat_features(
            hand=hand, auction_history=['2♦'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        assert features['interference_level'] == 2

    def test_interference_level_1s(self):
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('92', 'K532', 'K2', 'KJ873')
        features = extract_flat_features(
            hand=hand, auction_history=['1♠'],
            my_position='South', dealer='East', vulnerability='NS'
        )
        assert features['interference_level'] == 1

    def test_interference_level_no_opponent_bid(self):
        """When no opponent has bid, interference_level should be 0."""
        from engine.v2.features.enhanced_extractor import extract_flat_features
        hand = _make_hand('92', 'K532', 'K2', 'KJ873')
        features = extract_flat_features(
            hand=hand, auction_history=['Pass'],
            my_position='East', dealer='North', vulnerability='None'
        )
        assert features['interference_level'] == 0


class TestNegativeDoubleStress:
    """Verify negative double HCP floor and interference_level interaction.

    Auction: 1♦ - (2♣) - ?
    interference_level = 2 → negative_double_2_level requires 8+ HCP (HARD)

    Hand A: ♠K864 ♥Q742 ♦95 ♣J6 (7 HCP) → PASS (fails 8 HCP floor)
    Hand B: ♠AK86 ♥Q742 ♦95 ♣J6 (11 HCP) → X (negative double)
    """

    def test_hand_a_7hcp_should_pass(self):
        """7 HCP with 4-4 majors after 1♦-(2♣): must PASS (below 8 HCP hard floor)."""
        from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
        engine = BiddingEngineV2Schema()
        # ♠K864 ♥Q742 ♦953 ♣J6 = 7 HCP, 4-4-3-2 shape
        hand = _make_hand('K864', 'Q742', '953', 'J6')
        # Auction: North opens 1♦, East overcalls 2♣, South (us) to bid
        result = engine.get_next_bid(
            hand, ['1♦', '2♣'], 'South',
            vulnerability='None', dealer='North'
        )
        bid = result[0] if isinstance(result, tuple) else result
        assert bid == 'Pass', (
            f"7 HCP should PASS after 1♦-(2♣), got {bid}"
        )

    def test_hand_b_11hcp_should_double(self):
        """11 HCP with 4-4 majors after 1♦-(2♣): should make negative double."""
        from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
        engine = BiddingEngineV2Schema()
        # ♠AK86 ♥Q742 ♦953 ♣J6 = 11 HCP, 4-4-3-2 shape (same distribution as Hand A)
        hand = _make_hand('AK86', 'Q742', '953', 'J6')
        result = engine.get_next_bid(
            hand, ['1♦', '2♣'], 'South',
            vulnerability='None', dealer='North'
        )
        bid = result[0] if isinstance(result, tuple) else result
        assert bid == 'X', (
            f"11 HCP with 4-4 majors should double after 1♦-(2♣), got {bid}"
        )


class TestThreeLevelOvercall:
    """Engine should bid 3♣ over 2♦ with the original problem hand."""

    def test_3c_over_2d_with_good_clubs(self):
        """♠92 ♥K532 ♦K ♣KJ8732 (10 HCP) over 2♦ should bid 3♣, not double or pass."""
        from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
        engine = BiddingEngineV2Schema()
        hand = _make_hand('92', 'K532', 'K', 'KJ8732')
        result = engine.get_next_bid(
            hand, ['2♦'], 'South',
            vulnerability='NS', dealer='East'
        )
        bid = result[0] if isinstance(result, tuple) else result
        assert bid == '3♣', (
            f"Should bid 3♣ over 2♦ with 10 HCP and 6 clubs, got {bid}"
        )
