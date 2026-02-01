"""
Unit tests for BiddingState per-seat belief model.

Tests narrowing rules for:
- SeatBelief operations
- Pass inferences
- Opening bids
- Responses to openings
- Rebids
- Opponent bids (overcalls, doubles)
- Convention narrowing (Stayman, Jacoby, Blackwood)
"""

import pytest
from engine.ai.bidding_state import SeatBelief, BiddingState, BiddingStateBuilder


# ──────────────────────────────────────────────────────────────
# SeatBelief unit tests
# ──────────────────────────────────────────────────────────────

class TestSeatBelief:
    def test_initial_ranges(self):
        b = SeatBelief(seat='N')
        assert b.hcp == (0, 40)
        assert b.suits['♠'] == (0, 13)
        assert b.suits['♥'] == (0, 13)

    def test_narrow_hcp_min(self):
        b = SeatBelief(seat='N')
        b.narrow_hcp(new_min=12)
        assert b.hcp == (12, 40)

    def test_narrow_hcp_max(self):
        b = SeatBelief(seat='N')
        b.narrow_hcp(new_max=17)
        assert b.hcp == (0, 17)

    def test_narrow_hcp_both(self):
        b = SeatBelief(seat='N')
        b.narrow_hcp(new_min=15, new_max=17)
        assert b.hcp == (15, 17)

    def test_narrow_hcp_intersection(self):
        b = SeatBelief(seat='N')
        b.narrow_hcp(new_min=12, new_max=21)
        b.narrow_hcp(new_min=15, new_max=17)
        assert b.hcp == (15, 17)

    def test_narrow_hcp_inversion_caps(self):
        b = SeatBelief(seat='N')
        b.narrow_hcp(new_min=15, new_max=17)
        b.narrow_hcp(new_min=20)  # Would invert: (20, 17)
        assert b.hcp[0] == b.hcp[1]  # Capped: min == max

    def test_narrow_suit(self):
        b = SeatBelief(seat='N')
        b.narrow_suit('♠', new_min=5)
        assert b.suits['♠'] == (5, 13)

    def test_narrow_suit_max(self):
        b = SeatBelief(seat='N')
        b.narrow_suit('♥', new_max=4)
        assert b.suits['♥'] == (0, 4)

    def test_narrow_suit_intersection(self):
        b = SeatBelief(seat='N')
        b.narrow_suit('♠', new_min=3)
        b.narrow_suit('♠', new_min=5)
        assert b.suits['♠'] == (5, 13)

    def test_tags(self):
        b = SeatBelief(seat='N')
        assert not b.has_tag('opened_major')
        b.add_tag('opened_major')
        assert b.has_tag('opened_major')

    def test_tag_no_duplicates(self):
        b = SeatBelief(seat='N')
        b.add_tag('x')
        b.add_tag('x')
        assert b.tags.count('x') == 1

    def test_hcp_midpoint(self):
        b = SeatBelief(seat='N')
        b.narrow_hcp(new_min=15, new_max=17)
        assert b.hcp_midpoint == 16.0


# ──────────────────────────────────────────────────────────────
# BiddingState tests
# ──────────────────────────────────────────────────────────────

class TestBiddingState:
    def test_seat_access(self):
        bs = BiddingState()
        n = bs.seat('N')
        assert n.seat == 'N'
        assert bs.seat('North').seat == 'N'

    def test_partner_of(self):
        bs = BiddingState()
        assert bs.partner_of('N').seat == 'S'
        assert bs.partner_of('E').seat == 'W'

    def test_combined_hcp(self):
        bs = BiddingState()
        bs.seat('N').narrow_hcp(new_min=15, new_max=17)
        bs.seat('S').narrow_hcp(new_min=6, new_max=10)
        combined = bs.combined_hcp('N', 'S')
        assert combined == (21, 27)

    def test_partnership_hcp(self):
        bs = BiddingState()
        bs.seat('N').narrow_hcp(new_min=15, new_max=17)
        bs.seat('S').narrow_hcp(new_min=6, new_max=10)
        assert bs.partnership_hcp('N') == (21, 27)
        assert bs.partnership_hcp('S') == (21, 27)


# ──────────────────────────────────────────────────────────────
# Builder: helper
# ──────────────────────────────────────────────────────────────

def build(auction, dealer='N'):
    return BiddingStateBuilder().build(auction, dealer)


# ──────────────────────────────────────────────────────────────
# Pass inferences
# ──────────────────────────────────────────────────────────────

class TestPassInferences:
    def test_first_seat_pass(self):
        state = build(['Pass'], dealer='N')
        n = state.seat('N')
        assert n.hcp[1] <= 11
        assert n.passed_opening
        assert n.has_tag('passed_opening')

    def test_second_seat_pass(self):
        state = build(['Pass', 'Pass'], dealer='N')
        e = state.seat('E')
        assert e.hcp[1] <= 11
        assert e.has_tag('passed_opening')

    def test_third_seat_pass(self):
        state = build(['Pass', 'Pass', 'Pass'], dealer='N')
        s = state.seat('S')
        assert s.hcp[1] <= 13
        assert s.has_tag('passed_late')

    def test_pass_as_responder(self):
        """Pass over partner's opening with no interference."""
        state = build(['1♠', 'Pass', 'Pass'], dealer='N')
        s = state.seat('S')
        assert s.hcp[1] <= 5
        assert s.limited
        assert s.has_tag('passed_response')

    def test_pass_over_interference(self):
        """Pass over interference after partner opened."""
        # N opens 1♠, E overcalls 2♣, S passes
        state = build(['1♠', '2♣', 'Pass'], dealer='N')
        s = state.seat('S')
        assert s.hcp[1] <= 8
        assert s.has_tag('passed_over_interference')


# ──────────────────────────────────────────────────────────────
# Opening bids
# ──────────────────────────────────────────────────────────────

class TestOpeningBids:
    def test_1nt_opening(self):
        state = build(['1NT'], dealer='N')
        n = state.seat('N')
        assert n.hcp == (15, 17)
        assert n.suits['♥'][1] <= 4
        assert n.suits['♠'][1] <= 4
        assert n.has_tag('opened_1nt')
        assert n.has_tag('balanced')

    def test_2nt_opening(self):
        state = build(['2NT'], dealer='N')
        n = state.seat('N')
        assert n.hcp == (20, 21)
        assert n.has_tag('opened_2nt')

    def test_1_major_opening(self):
        state = build(['1♠'], dealer='N')
        n = state.seat('N')
        assert n.hcp == (12, 21)
        assert n.suits['♠'][0] >= 5
        assert n.has_tag('opened_major')

    def test_1_heart_opening(self):
        state = build(['1♥'], dealer='N')
        n = state.seat('N')
        assert n.hcp[0] >= 12
        assert n.suits['♥'][0] >= 5

    def test_1_minor_opening(self):
        state = build(['1♣'], dealer='N')
        n = state.seat('N')
        assert n.hcp == (12, 21)
        assert n.suits['♣'][0] >= 3
        assert n.has_tag('opened_minor')

    def test_1_diamond_opening(self):
        state = build(['1♦'], dealer='N')
        n = state.seat('N')
        assert n.suits['♦'][0] >= 3

    def test_strong_2c(self):
        state = build(['2♣'], dealer='N')
        n = state.seat('N')
        assert n.hcp[0] >= 22
        assert n.has_tag('strong_2c')
        assert state.forcing['NS'] == 'game'

    def test_weak_two(self):
        state = build(['2♥'], dealer='N')
        n = state.seat('N')
        assert n.hcp == (6, 10)
        assert n.suits['♥'] == (6, 6)
        assert n.limited
        assert n.has_tag('weak_two')

    def test_weak_two_spades(self):
        state = build(['2♠'], dealer='N')
        n = state.seat('N')
        assert n.suits['♠'] == (6, 6)

    def test_preempt_3_level(self):
        state = build(['3♦'], dealer='N')
        n = state.seat('N')
        assert n.hcp == (6, 10)
        assert n.suits['♦'][0] >= 7
        assert n.limited
        assert n.has_tag('preempt')

    def test_preempt_4_level(self):
        state = build(['4♠'], dealer='N')
        n = state.seat('N')
        assert n.suits['♠'][0] >= 7
        assert n.has_tag('preempt')

    def test_opening_by_non_dealer(self):
        """First seat passes, second seat opens."""
        state = build(['Pass', '1♠'], dealer='N')
        n = state.seat('N')
        e = state.seat('E')
        assert n.hcp[1] <= 11
        assert e.hcp[0] >= 12
        assert e.suits['♠'][0] >= 5


# ──────────────────────────────────────────────────────────────
# Responses
# ──────────────────────────────────────────────────────────────

class TestResponses:
    def test_1nt_response(self):
        state = build(['1♠', 'Pass', '1NT'], dealer='N')
        s = state.seat('S')
        assert s.hcp == (6, 10)
        assert s.limited
        assert s.has_tag('responded_1nt')

    def test_2nt_response(self):
        state = build(['1♠', 'Pass', '2NT'], dealer='N')
        s = state.seat('S')
        assert s.hcp == (13, 15)

    def test_3nt_response(self):
        state = build(['1♠', 'Pass', '3NT'], dealer='N')
        s = state.seat('S')
        assert s.hcp == (16, 18)

    def test_new_suit_1_level(self):
        state = build(['1♦', 'Pass', '1♠'], dealer='N')
        s = state.seat('S')
        assert s.hcp[0] >= 6
        assert s.suits['♠'][0] >= 4
        assert s.has_tag('new_suit_1_level')

    def test_new_suit_2_level(self):
        state = build(['1♠', 'Pass', '2♦'], dealer='N')
        s = state.seat('S')
        assert s.hcp[0] >= 10
        assert s.suits['♦'][0] >= 5
        assert s.has_tag('new_suit_2_level')

    def test_2_over_1_game_forcing(self):
        """2-level new suit over 1M opening is game forcing."""
        state = build(['1♥', 'Pass', '2♣'], dealer='N')
        s = state.seat('S')
        assert s.has_tag('two_over_one_gf')
        assert state.forcing['NS'] == 'game'

    def test_simple_raise(self):
        state = build(['1♠', 'Pass', '2♠'], dealer='N')
        s = state.seat('S')
        assert s.hcp == (6, 10)
        assert s.suits['♠'][0] >= 3
        assert s.limited
        assert s.has_tag('simple_raise')
        assert state.agreed_suits['NS'] == '♠'

    def test_jump_raise(self):
        state = build(['1♠', 'Pass', '3♠'], dealer='N')
        s = state.seat('S')
        assert s.hcp == (6, 10)
        assert s.suits['♠'][0] >= 4
        assert s.has_tag('preemptive_raise')
        assert state.agreed_suits['NS'] == '♠'


# ──────────────────────────────────────────────────────────────
# Rebids
# ──────────────────────────────────────────────────────────────

class TestRebids:
    def test_rebid_own_suit(self):
        """Opener rebids their suit → 6+ cards."""
        state = build(['1♥', 'Pass', '1♠', 'Pass', '2♥'], dealer='N')
        n = state.seat('N')
        assert n.suits['♥'][0] >= 6
        assert n.has_tag('rebid_own_suit')

    def test_rebid_1nt(self):
        state = build(['1♣', 'Pass', '1♠', 'Pass', '1NT'], dealer='N')
        n = state.seat('N')
        assert n.hcp == (12, 14)
        assert n.limited
        assert n.has_tag('rebid_1nt')

    def test_rebid_2nt(self):
        state = build(['1♣', 'Pass', '1♠', 'Pass', '2NT'], dealer='N')
        n = state.seat('N')
        assert n.hcp[0] >= 18
        assert n.hcp[1] <= 19


# ──────────────────────────────────────────────────────────────
# Opponent bids
# ──────────────────────────────────────────────────────────────

class TestOpponentBids:
    def test_1_level_overcall(self):
        state = build(['1♣', '1♠'], dealer='N')
        e = state.seat('E')
        assert e.hcp == (8, 16)
        assert e.suits['♠'][0] >= 5
        assert e.has_tag('overcall_1_level')

    def test_2_level_overcall(self):
        state = build(['1♠', '2♦'], dealer='N')
        e = state.seat('E')
        assert e.hcp == (11, 16)
        assert e.suits['♦'][0] >= 5
        assert e.has_tag('overcall_2_level')

    def test_weak_jump_overcall(self):
        """Jump overcall is weak."""
        state = build(['1♣', '2♥'], dealer='N')
        e = state.seat('E')
        # 2♥ over 1♣ is a jump (1-level to 2-level, skipping cheapest)
        assert e.suits['♥'][0] >= 5  # At least 5 in suit

    def test_takeout_double(self):
        state = build(['1♠', 'X'], dealer='N')
        e = state.seat('E')
        assert e.hcp[0] >= 12
        assert e.has_tag('takeout_double')
        # Short in opener's suit (♠)
        assert e.suits['♠'][1] <= 2

    def test_takeout_double_support_unbid(self):
        """Takeout double implies support for unbid suits."""
        state = build(['1♠', 'X'], dealer='N')
        e = state.seat('E')
        # Unbid suits (♥, ♦, ♣) should have min 3
        assert e.suits['♥'][0] >= 3
        assert e.suits['♦'][0] >= 3
        assert e.suits['♣'][0] >= 3


# ──────────────────────────────────────────────────────────────
# Convention narrowing: Stayman
# ──────────────────────────────────────────────────────────────

class TestStayman:
    def test_stayman_ask(self):
        state = build(['1NT', 'Pass', '2♣'], dealer='N')
        s = state.seat('S')
        assert s.hcp[0] >= 8
        assert s.has_tag('stayman_asked')

    def test_stayman_no_major(self):
        state = build(['1NT', 'Pass', '2♣', 'Pass', '2♦'], dealer='N')
        n = state.seat('N')
        assert n.suits['♥'][1] <= 3
        assert n.suits['♠'][1] <= 3
        assert n.has_tag('stayman_no_major')

    def test_stayman_hearts(self):
        state = build(['1NT', 'Pass', '2♣', 'Pass', '2♥'], dealer='N')
        n = state.seat('N')
        assert n.suits['♥'][0] >= 4
        assert n.has_tag('stayman_hearts')

    def test_stayman_spades(self):
        state = build(['1NT', 'Pass', '2♣', 'Pass', '2♠'], dealer='N')
        n = state.seat('N')
        assert n.suits['♠'][0] >= 4
        assert n.has_tag('stayman_spades')


# ──────────────────────────────────────────────────────────────
# Convention narrowing: Jacoby Transfers
# ──────────────────────────────────────────────────────────────

class TestJacobyTransfers:
    def test_jacoby_hearts(self):
        """2♦ over 1NT = transfer to hearts."""
        state = build(['1NT', 'Pass', '2♦'], dealer='N')
        s = state.seat('S')
        assert s.suits['♥'][0] >= 5
        assert s.has_tag('jacoby_hearts')

    def test_jacoby_spades(self):
        """2♥ over 1NT = transfer to spades."""
        state = build(['1NT', 'Pass', '2♥'], dealer='N')
        s = state.seat('S')
        assert s.suits['♠'][0] >= 5
        assert s.has_tag('jacoby_spades')

    def test_transfer_completion(self):
        """Opener completes the transfer."""
        state = build(['1NT', 'Pass', '2♦', 'Pass', '2♥'], dealer='N')
        n = state.seat('N')
        assert n.has_tag('transfer_completed')

    def test_transfer_spades_completion(self):
        state = build(['1NT', 'Pass', '2♥', 'Pass', '2♠'], dealer='N')
        n = state.seat('N')
        assert n.has_tag('transfer_completed')


# ──────────────────────────────────────────────────────────────
# Convention narrowing: Blackwood
# ──────────────────────────────────────────────────────────────

class TestBlackwood:
    def test_blackwood_after_agreed_suit(self):
        """4NT after suit agreement = Blackwood."""
        state = build(['1♠', 'Pass', '2♠', 'Pass', '4NT'], dealer='N')
        n = state.seat('N')
        assert n.has_tag('blackwood_asked')

    def test_blackwood_response(self):
        """5♦ response to Blackwood = 1 ace."""
        state = build(['1♠', 'Pass', '2♠', 'Pass', '4NT', 'Pass', '5♦'], dealer='N')
        s = state.seat('S')
        assert s.has_tag('blackwood_response')
        assert s.has_tag('blackwood_1_aces')

    def test_blackwood_0_aces(self):
        state = build(['1♠', 'Pass', '2♠', 'Pass', '4NT', 'Pass', '5♣'], dealer='N')
        s = state.seat('S')
        assert s.has_tag('blackwood_0_aces')

    def test_blackwood_2_aces(self):
        state = build(['1♠', 'Pass', '2♠', 'Pass', '4NT', 'Pass', '5♥'], dealer='N')
        s = state.seat('S')
        assert s.has_tag('blackwood_2_aces')


# ──────────────────────────────────────────────────────────────
# Full auction sequences
# ──────────────────────────────────────────────────────────────

class TestFullAuctions:
    def test_standard_1nt_game(self):
        """1NT - Pass - 3NT - Pass - Pass - Pass."""
        state = build(['1NT', 'Pass', '3NT', 'Pass', 'Pass', 'Pass'], dealer='N')
        n = state.seat('N')
        s = state.seat('S')
        assert n.hcp == (15, 17)
        assert s.hcp == (16, 18)
        ns_hcp = state.partnership_hcp('N')
        assert ns_hcp[0] >= 31

    def test_contested_auction(self):
        """N opens 1♥, E overcalls 1♠, S raises to 2♥."""
        state = build(['1♥', '1♠', '2♥'], dealer='N')
        n = state.seat('N')
        e = state.seat('E')
        s = state.seat('S')
        assert n.hcp[0] >= 12
        assert n.suits['♥'][0] >= 5
        assert e.hcp[0] >= 8
        assert e.suits['♠'][0] >= 5
        assert s.suits['♥'][0] >= 3
        assert state.agreed_suits['NS'] == '♥'

    def test_all_pass(self):
        """All four seats pass."""
        state = build(['Pass', 'Pass', 'Pass', 'Pass'], dealer='N')
        for s in ['N', 'E', 'S', 'W']:
            assert state.seat(s).passed_opening

    def test_passed_hand_then_open(self):
        """Two passes, then 3rd seat opens."""
        state = build(['Pass', 'Pass', '1♠'], dealer='N')
        n = state.seat('N')
        e = state.seat('E')
        s = state.seat('S')
        assert n.hcp[1] <= 11
        assert e.hcp[1] <= 11
        assert s.hcp[0] >= 12

    def test_dealer_east(self):
        """Verify correct seat assignment when dealer is East."""
        state = build(['1♠', 'Pass', '2♠'], dealer='E')
        e = state.seat('E')
        s = state.seat('S')
        w = state.seat('W')
        assert e.hcp[0] >= 12
        assert e.suits['♠'][0] >= 5
        # S passed after E opened — pass over partner's opening is not "passed opening"
        # S is opponent of opener E, pass doesn't narrow much
        assert w.suits['♠'][0] >= 3  # W raised to 2♠
        assert w.has_tag('simple_raise')

    def test_stayman_full_sequence(self):
        """Full Stayman auction: 1NT - 2♣ - 2♥ - 3NT."""
        state = build(['1NT', 'Pass', '2♣', 'Pass', '2♥', 'Pass', '3NT'], dealer='N')
        n = state.seat('N')
        s = state.seat('S')
        # Note: opener's HCP may be narrowed further by rebid processing
        assert n.hcp[0] >= 15
        assert n.suits['♥'][0] >= 4
        assert s.has_tag('stayman_asked')
        assert n.has_tag('stayman_hearts')
