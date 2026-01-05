"""
Unit tests for seats utility module.

Tests the modulo-4 clock arithmetic and all helper functions
to ensure consistent seat calculations across the application.
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.seats import (
    # Constants
    NORTH, EAST, SOUTH, WEST, NS, EW,
    SEATS, SEAT_NAMES, PARTNERS, NS_SIDE, EW_SIDE,
    # Functions
    normalize, seat_index, seat_from_index,
    partner, lho, rho,
    partnership, partnership_str, is_partner, is_opponent, same_side,
    relative_position, display_name, bidder_role,
    dummy, opening_leader, is_declaring_side, is_defending_side,
    active_seat_bidding, active_seat_play
)


class TestConstants:
    """Test that constants are correctly defined."""

    def test_seat_indices(self):
        assert NORTH == 0
        assert EAST == 1
        assert SOUTH == 2
        assert WEST == 3

    def test_partnership_indices(self):
        assert NS == 0
        assert EW == 1

    def test_seats_list(self):
        assert SEATS == ['N', 'E', 'S', 'W']

    def test_partners_map(self):
        assert PARTNERS == {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

    def test_ns_side(self):
        assert NS_SIDE == {'N', 'S'}

    def test_ew_side(self):
        assert EW_SIDE == {'E', 'W'}


class TestNormalization:
    """Test position normalization."""

    def test_single_letter(self):
        assert normalize('N') == 'N'
        assert normalize('E') == 'E'
        assert normalize('S') == 'S'
        assert normalize('W') == 'W'

    def test_lowercase(self):
        assert normalize('n') == 'N'
        assert normalize('e') == 'E'
        assert normalize('s') == 'S'
        assert normalize('w') == 'W'

    def test_full_name(self):
        assert normalize('North') == 'N'
        assert normalize('East') == 'E'
        assert normalize('South') == 'S'
        assert normalize('West') == 'W'

    def test_full_name_uppercase(self):
        assert normalize('NORTH') == 'N'
        assert normalize('SOUTH') == 'S'

    def test_null_defaults_to_north(self):
        assert normalize(None) == 'N'
        assert normalize('') == 'N'

    def test_whitespace(self):
        assert normalize('  N  ') == 'N'
        assert normalize(' South ') == 'S'


class TestSeatIndex:
    """Test seat index conversions."""

    def test_seat_to_index(self):
        assert seat_index('N') == 0
        assert seat_index('E') == 1
        assert seat_index('S') == 2
        assert seat_index('W') == 3

    def test_full_name_to_index(self):
        assert seat_index('North') == 0
        assert seat_index('South') == 2

    def test_index_to_seat(self):
        assert seat_from_index(0) == 'N'
        assert seat_from_index(1) == 'E'
        assert seat_from_index(2) == 'S'
        assert seat_from_index(3) == 'W'

    def test_index_wrapping(self):
        # Test modulo wrapping
        assert seat_from_index(4) == 'N'
        assert seat_from_index(5) == 'E'
        assert seat_from_index(6) == 'S'
        assert seat_from_index(7) == 'W'
        assert seat_from_index(8) == 'N'

    def test_negative_index(self):
        # Negative indices should also wrap correctly
        assert seat_from_index(-1) == 'W'
        assert seat_from_index(-2) == 'S'
        assert seat_from_index(-3) == 'E'
        assert seat_from_index(-4) == 'N'


class TestPartner:
    """Test partner calculations."""

    def test_partner_symmetry(self):
        # Partner of partner is self
        for seat in SEATS:
            assert partner(partner(seat)) == seat

    def test_partner_values(self):
        assert partner('N') == 'S'
        assert partner('S') == 'N'
        assert partner('E') == 'W'
        assert partner('W') == 'E'

    def test_partner_with_full_names(self):
        assert partner('North') == 'S'
        assert partner('South') == 'N'


class TestLhoRho:
    """Test LHO and RHO calculations."""

    def test_lho_clockwise(self):
        # LHO is next player clockwise
        assert lho('N') == 'E'
        assert lho('E') == 'S'
        assert lho('S') == 'W'
        assert lho('W') == 'N'

    def test_rho_counterclockwise(self):
        # RHO is previous player clockwise
        assert rho('N') == 'W'
        assert rho('E') == 'N'
        assert rho('S') == 'E'
        assert rho('W') == 'S'

    def test_lho_rho_inverse(self):
        # LHO of RHO is self, RHO of LHO is self
        for seat in SEATS:
            assert lho(rho(seat)) == seat
            assert rho(lho(seat)) == seat


class TestPartnership:
    """Test partnership calculations."""

    def test_partnership_ns(self):
        assert partnership('N') == NS
        assert partnership('S') == NS

    def test_partnership_ew(self):
        assert partnership('E') == EW
        assert partnership('W') == EW

    def test_partnership_str(self):
        assert partnership_str('N') == 'NS'
        assert partnership_str('S') == 'NS'
        assert partnership_str('E') == 'EW'
        assert partnership_str('W') == 'EW'

    def test_is_partner(self):
        assert is_partner('N', 'S') is True
        assert is_partner('S', 'N') is True
        assert is_partner('E', 'W') is True
        assert is_partner('W', 'E') is True
        assert is_partner('N', 'E') is False
        assert is_partner('N', 'W') is False

    def test_is_opponent(self):
        assert is_opponent('N', 'E') is True
        assert is_opponent('N', 'W') is True
        assert is_opponent('S', 'E') is True
        assert is_opponent('N', 'S') is False

    def test_same_side(self):
        assert same_side('N', 'S') is True
        assert same_side('E', 'W') is True
        assert same_side('N', 'E') is False


class TestRelativePosition:
    """Test relative position calculations (the modulo-4 clock)."""

    def test_self_is_zero(self):
        # Relative position of self is 0
        for seat in SEATS:
            assert relative_position(seat, seat) == 0

    def test_partner_is_two(self):
        # Partner is always position 2
        for seat in SEATS:
            assert relative_position(partner(seat), seat) == 2

    def test_lho_is_one(self):
        # LHO is always position 1
        for seat in SEATS:
            assert relative_position(lho(seat), seat) == 1

    def test_rho_is_three(self):
        # RHO is always position 3
        for seat in SEATS:
            assert relative_position(rho(seat), seat) == 3

    def test_from_south_perspective(self):
        # Standard user perspective
        assert relative_position('S', 'S') == 0  # Self
        assert relative_position('W', 'S') == 1  # LHO
        assert relative_position('N', 'S') == 2  # Partner
        assert relative_position('E', 'S') == 3  # RHO

    def test_from_north_perspective(self):
        assert relative_position('N', 'N') == 0  # Self
        assert relative_position('E', 'N') == 1  # LHO
        assert relative_position('S', 'N') == 2  # Partner
        assert relative_position('W', 'N') == 3  # RHO


class TestDisplayName:
    """Test display name generation."""

    def test_relative_from_south(self):
        assert display_name('S', 'S') == 'You'
        assert display_name('W', 'S') == 'LHO'
        assert display_name('N', 'S') == 'Partner'
        assert display_name('E', 'S') == 'RHO'

    def test_relative_from_north(self):
        assert display_name('N', 'N') == 'You'
        assert display_name('E', 'N') == 'LHO'
        assert display_name('S', 'N') == 'Partner'
        assert display_name('W', 'N') == 'RHO'

    def test_absolute_names(self):
        assert display_name('N', 'S', relative=False) == 'North'
        assert display_name('E', 'S', relative=False) == 'East'
        assert display_name('S', 'S', relative=False) == 'South'
        assert display_name('W', 'S', relative=False) == 'West'


class TestBidderRole:
    """Test bidder role descriptions."""

    def test_from_south_perspective(self):
        assert bidder_role('S', 'S') == 'South (You)'
        assert bidder_role('N', 'S') == 'North (Partner)'
        assert bidder_role('E', 'S') == 'East (Opponent)'
        assert bidder_role('W', 'S') == 'West (Opponent)'

    def test_from_east_perspective(self):
        # If user is East
        assert bidder_role('E', 'E') == 'East (You)'
        assert bidder_role('W', 'E') == 'West (Partner)'
        assert bidder_role('N', 'E') == 'North (Opponent)'
        assert bidder_role('S', 'E') == 'South (Opponent)'


class TestPlayPhaseHelpers:
    """Test play phase utility functions."""

    def test_dummy_is_partner(self):
        assert dummy('S') == 'N'
        assert dummy('N') == 'S'
        assert dummy('E') == 'W'
        assert dummy('W') == 'E'

    def test_opening_leader_is_lho(self):
        assert opening_leader('S') == 'W'
        assert opening_leader('N') == 'E'
        assert opening_leader('E') == 'S'
        assert opening_leader('W') == 'N'

    def test_is_declaring_side(self):
        # If South declares
        assert is_declaring_side('S', 'S') is True  # Declarer
        assert is_declaring_side('N', 'S') is True  # Dummy
        assert is_declaring_side('E', 'S') is False  # Defender
        assert is_declaring_side('W', 'S') is False  # Defender

    def test_is_defending_side(self):
        # If South declares
        assert is_defending_side('E', 'S') is True
        assert is_defending_side('W', 'S') is True
        assert is_defending_side('S', 'S') is False
        assert is_defending_side('N', 'S') is False


class TestBiddingPhaseHelpers:
    """Test bidding phase utility functions."""

    def test_active_seat_bidding_from_north(self):
        # North deals
        assert active_seat_bidding('N', 0) == 'N'  # North's turn
        assert active_seat_bidding('N', 1) == 'E'  # East's turn
        assert active_seat_bidding('N', 2) == 'S'  # South's turn
        assert active_seat_bidding('N', 3) == 'W'  # West's turn
        assert active_seat_bidding('N', 4) == 'N'  # Back to North

    def test_active_seat_bidding_from_east(self):
        # East deals
        assert active_seat_bidding('E', 0) == 'E'
        assert active_seat_bidding('E', 1) == 'S'
        assert active_seat_bidding('E', 2) == 'W'
        assert active_seat_bidding('E', 3) == 'N'

    def test_active_seat_play(self):
        # West leads
        assert active_seat_play('W', 0) == 'W'  # Leader
        assert active_seat_play('W', 1) == 'N'  # Second
        assert active_seat_play('W', 2) == 'E'  # Third
        assert active_seat_play('W', 3) == 'S'  # Fourth


class TestModulo4Properties:
    """Test mathematical properties of the modulo-4 system."""

    def test_full_rotation(self):
        # Going around the table returns to start
        seat = 'S'
        for _ in range(4):
            seat = lho(seat)
        assert seat == 'S'

    def test_all_positions_reachable(self):
        # From any seat, can reach all others via LHO
        for start in SEATS:
            visited = set()
            current = start
            for _ in range(4):
                visited.add(current)
                current = lho(current)
            assert visited == set(SEATS)

    def test_relative_position_sum(self):
        # Sum of relative positions from any hero should be 0+1+2+3 = 6
        for hero in SEATS:
            total = sum(relative_position(target, hero) for target in SEATS)
            assert total == 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
