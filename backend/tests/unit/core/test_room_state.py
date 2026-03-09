"""
Unit tests for room state management (partner practice).

Tests RoomState logic: seat math, turn detection, bidder calculation,
partner resolution, and RoomStateManager lifecycle.

No database or Flask required — pure in-memory logic.
"""
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

sys.path.insert(0, 'backend')

from core.room_state import RoomState, RoomStateManager, RoomSettings, generate_room_code
from engine.play_engine import PlayState, Contract


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def room():
    """Basic room with host and guest joined."""
    r = RoomState(
        room_code='ABC123',
        host_session_id='host-1',
        guest_session_id='guest-1',
    )
    return r


@pytest.fixture
def manager():
    return RoomStateManager()


def _make_play_state(declarer='S', next_to_play='W', dummy_revealed=True):
    """Helper to create a minimal PlayState for testing."""
    contract = Contract(level=1, strain='NT', declarer=declarer)
    ps = PlayState(
        contract=contract,
        hands={},
        next_to_play=next_to_play,
        dummy_revealed=dummy_revealed,
        current_trick=[],
        trick_history=[],
        tricks_won={'NS': 0, 'EW': 0},
    )
    return ps


# ===========================================================================
# RoomState — Position mapping
# ===========================================================================

class TestPositionMapping:

    def test_host_is_south(self, room):
        assert room.get_position_for_session('host-1') == 'S'

    def test_guest_is_north(self, room):
        assert room.get_position_for_session('guest-1') == 'N'

    def test_unknown_session_returns_none(self, room):
        assert room.get_position_for_session('stranger') is None

    def test_is_session_in_room(self, room):
        assert room.is_session_in_room('host-1')
        assert room.is_session_in_room('guest-1')
        assert not room.is_session_in_room('stranger')


# ===========================================================================
# RoomState — get_current_bidder (uses seats utility)
# ===========================================================================

class TestGetCurrentBidder:

    @pytest.mark.parametrize("dealer,expected_first", [
        ('North', 'N'),
        ('East', 'E'),
        ('South', 'S'),
        ('West', 'W'),
    ])
    def test_first_bidder_is_dealer(self, room, dealer, expected_first):
        room.dealer = dealer
        room.game_phase = 'bidding'
        room.auction_history = []
        assert room.get_current_bidder() == expected_first

    @pytest.mark.parametrize("dealer,num_bids,expected", [
        ('North', 1, 'E'),   # N dealt, 1 bid made → E's turn
        ('North', 2, 'S'),   # N dealt, 2 bids → S's turn
        ('North', 3, 'W'),   # N dealt, 3 bids → W's turn
        ('North', 4, 'N'),   # Full round → back to N
        ('South', 1, 'W'),   # S dealt, 1 bid → W
        ('South', 2, 'N'),   # S dealt, 2 bids → N
        ('East', 1, 'S'),    # E dealt, 1 bid → S
        ('West', 1, 'N'),    # W dealt, 1 bid → N
    ])
    def test_bidder_rotation(self, room, dealer, num_bids, expected):
        room.dealer = dealer
        room.game_phase = 'bidding'
        room.auction_history = ['Pass'] * num_bids
        assert room.get_current_bidder() == expected

    def test_returns_none_when_not_bidding(self, room):
        room.game_phase = 'waiting'
        assert room.get_current_bidder() is None

        room.game_phase = 'playing'
        assert room.get_current_bidder() is None

        room.game_phase = 'complete'
        assert room.get_current_bidder() is None


# ===========================================================================
# RoomState — is_session_turn (bidding phase)
# ===========================================================================

class TestIsSessionTurnBidding:

    def test_host_turn_when_south_deals(self, room):
        room.dealer = 'South'
        room.game_phase = 'bidding'
        room.auction_history = []
        # South (host) is dealer, so it's host's turn
        assert room.is_session_turn('host-1') is True
        assert room.is_session_turn('guest-1') is False

    def test_guest_turn_when_north_deals(self, room):
        room.dealer = 'North'
        room.game_phase = 'bidding'
        room.auction_history = []
        # North (guest) is dealer
        assert room.is_session_turn('guest-1') is True
        assert room.is_session_turn('host-1') is False

    def test_ai_turn_no_human_session(self, room):
        room.dealer = 'North'
        room.game_phase = 'bidding'
        room.auction_history = ['Pass']  # N bid, now E's turn (AI)
        assert room.is_session_turn('host-1') is False
        assert room.is_session_turn('guest-1') is False


# ===========================================================================
# RoomState — is_session_turn (play phase, declarer controls dummy)
# ===========================================================================

class TestIsSessionTurnPlaying:

    def test_host_turn_when_next_is_south(self, room):
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='S', next_to_play='S')
        assert room.is_session_turn('host-1') is True
        assert room.is_session_turn('guest-1') is False

    def test_guest_turn_when_next_is_north(self, room):
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='S', next_to_play='N')
        # N is dummy, S is declarer — declarer (host) controls dummy
        assert room.is_session_turn('host-1') is True
        assert room.is_session_turn('guest-1') is False

    def test_declarer_south_controls_dummy_north(self, room):
        """When South declares, South controls North (dummy)."""
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='S', next_to_play='N')
        # Host (South=declarer) should have turn when dummy (North) is next
        assert room.is_session_turn('host-1') is True

    def test_declarer_north_controls_dummy_south(self, room):
        """When North declares, North controls South (dummy)."""
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='N', next_to_play='S')
        # Guest (North=declarer) should have turn when dummy (South) is next
        assert room.is_session_turn('guest-1') is True
        assert room.is_session_turn('host-1') is False

    def test_ai_turn_no_human_control(self, room):
        """When East or West is next to play, no human has the turn."""
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='S', next_to_play='E')
        assert room.is_session_turn('host-1') is False
        assert room.is_session_turn('guest-1') is False

    def test_ai_declarer_no_human_turn(self, room):
        """If AI is declarer (E/W), no human controls dummy either."""
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='E', next_to_play='W')
        # W is dummy of E declarer — both AI, no human turn
        assert room.is_session_turn('host-1') is False
        assert room.is_session_turn('guest-1') is False

    def test_unknown_session_never_has_turn(self, room):
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='S', next_to_play='S')
        assert room.is_session_turn('stranger') is False


# ===========================================================================
# RoomState — to_dict partner hand resolution
# ===========================================================================

class TestToDictPartnerResolution:

    def _room_with_hands(self):
        """Room in 'complete' phase with mock hands."""
        room = RoomState(
            room_code='XYZ789',
            host_session_id='host-1',
            guest_session_id='guest-1',
            game_phase='complete',
        )
        # Mock Hand objects with .cards attribute
        south_hand = MagicMock()
        south_hand.cards = [MagicMock(rank='A', suit='♠')]
        north_hand = MagicMock()
        north_hand.cards = [MagicMock(rank='K', suit='♥')]

        room.deal = {
            'North': north_hand,
            'East': None,
            'South': south_hand,
            'West': None,
        }
        return room

    def test_host_sees_own_hand_as_south(self):
        room = self._room_with_hands()
        result = room.to_dict(for_session='host-1')
        assert result['my_position'] == 'S'
        assert result['my_hand'] is not None
        assert result['my_hand'][0]['rank'] == 'A'
        assert result['my_hand'][0]['suit'] == '♠'

    def test_host_sees_partner_hand_in_complete_phase(self):
        room = self._room_with_hands()
        result = room.to_dict(for_session='host-1')
        assert result['partner_position'] == 'N'
        assert result['partner_hand'] is not None
        assert result['partner_hand'][0]['rank'] == 'K'

    def test_guest_sees_partner_hand_in_complete_phase(self):
        room = self._room_with_hands()
        result = room.to_dict(for_session='guest-1')
        assert result['my_position'] == 'N'
        assert result['partner_position'] == 'S'
        assert result['partner_hand'][0]['rank'] == 'A'

    def test_no_partner_hand_during_bidding(self):
        room = self._room_with_hands()
        room.game_phase = 'bidding'
        result = room.to_dict(for_session='host-1')
        assert 'partner_hand' not in result


# ===========================================================================
# RoomState — Ready state and phase transitions
# ===========================================================================

class TestReadyState:

    def test_not_ready_by_default(self, room):
        assert not room.are_both_ready()

    def test_one_ready_not_sufficient(self, room):
        room.set_ready('host-1')
        assert not room.are_both_ready()

    def test_both_ready(self, room):
        room.set_ready('host-1')
        room.set_ready('guest-1')
        assert room.are_both_ready()

    def test_clear_ready_resets(self, room):
        room.set_ready('host-1')
        room.set_ready('guest-1')
        room.clear_ready()
        assert not room.are_both_ready()

    def test_not_ready_without_guest(self):
        room = RoomState(room_code='TEST', host_session_id='host-1')
        room.set_ready('host-1')
        assert not room.are_both_ready()


# ===========================================================================
# RoomState — Reset hand
# ===========================================================================

class TestResetHand:

    def test_reset_clears_auction(self, room):
        room.auction_history = ['1♣', 'Pass', '1♠', 'Pass']
        room.game_phase = 'playing'
        room.reset_hand()
        assert room.auction_history == []
        assert room.play_state is None
        assert room.bid_feedback == []

    def test_reset_goes_to_bidding_if_full(self, room):
        room.game_phase = 'complete'
        room.reset_hand()
        assert room.game_phase == 'bidding'

    def test_reset_goes_to_waiting_if_no_guest(self):
        room = RoomState(room_code='TEST', host_session_id='host-1')
        room.game_phase = 'complete'
        room.reset_hand()
        assert room.game_phase == 'waiting'


# ===========================================================================
# RoomState — Heartbeat and disconnect
# ===========================================================================

class TestHeartbeat:

    def test_heartbeat_records_time(self, room):
        room.record_heartbeat('host-1')
        assert 'host-1' in room.last_seen

    def test_partner_not_disconnected_initially(self, room):
        assert not room.is_partner_disconnected('host-1')

    def test_partner_disconnected_after_timeout(self, room):
        room.record_heartbeat('guest-1')
        # Fake the timestamp to be old
        room.last_seen['guest-1'] = datetime.now() - timedelta(seconds=room.DISCONNECT_TIMEOUT + 10)
        assert room.is_partner_disconnected('host-1')

    def test_partner_not_disconnected_within_timeout(self, room):
        room.record_heartbeat('guest-1')
        room.last_seen['guest-1'] = datetime.now() - timedelta(seconds=room.DISCONNECT_TIMEOUT - 10)
        assert not room.is_partner_disconnected('host-1')


# ===========================================================================
# RoomState — Version tracking
# ===========================================================================

class TestVersionTracking:

    def test_version_starts_at_zero(self, room):
        assert room.version == 0

    def test_increment_version(self, room):
        room.increment_version()
        assert room.version == 1

    def test_set_ready_increments_version(self, room):
        room.set_ready('host-1')
        assert room.version == 1


# ===========================================================================
# generate_room_code
# ===========================================================================

class TestGenerateRoomCode:

    def test_length(self):
        code = generate_room_code()
        assert len(code) == 6

    def test_custom_length(self):
        code = generate_room_code(length=4)
        assert len(code) == 4

    def test_no_ambiguous_characters(self):
        # Generate many codes and check none contain ambiguous chars
        ambiguous = set('0OIL1')
        for _ in range(100):
            code = generate_room_code()
            assert ambiguous.isdisjoint(set(code)), f"Code {code} contains ambiguous character"


# ===========================================================================
# RoomStateManager — Lifecycle
# ===========================================================================

class TestRoomStateManagerLifecycle:

    def test_create_room(self, manager):
        code = manager.create_room('host-1')
        assert len(code) == 6
        room = manager.get_room(code)
        assert room is not None
        assert room.host_session_id == 'host-1'

    def test_create_room_with_settings(self, manager):
        settings = RoomSettings(deal_type='convention', convention_filter='stayman')
        code = manager.create_room('host-1', settings=settings)
        room = manager.get_room(code)
        assert room.settings.deal_type == 'convention'
        assert room.settings.convention_filter == 'stayman'

    def test_join_room(self, manager):
        code = manager.create_room('host-1')
        success, msg = manager.join_room(code, 'guest-1')
        assert success
        room = manager.get_room(code)
        assert room.guest_session_id == 'guest-1'

    def test_join_nonexistent_room(self, manager):
        success, msg = manager.join_room('XXXXXX', 'guest-1')
        assert not success
        assert 'not found' in msg.lower()

    def test_join_own_room(self, manager):
        code = manager.create_room('host-1')
        success, msg = manager.join_room(code, 'host-1')
        assert not success
        assert 'own room' in msg.lower()

    def test_join_full_room(self, manager):
        code = manager.create_room('host-1')
        manager.join_room(code, 'guest-1')
        success, msg = manager.join_room(code, 'guest-2')
        assert not success
        assert 'full' in msg.lower()

    def test_join_case_insensitive(self, manager):
        code = manager.create_room('host-1')
        success, _ = manager.join_room(code.lower(), 'guest-1')
        assert success

    def test_get_room_by_session(self, manager):
        code = manager.create_room('host-1')
        manager.join_room(code, 'guest-1')
        assert manager.get_room_by_session('host-1').room_code == code
        assert manager.get_room_by_session('guest-1').room_code == code
        assert manager.get_room_by_session('stranger') is None

    def test_leave_room_host_destroys(self, manager):
        code = manager.create_room('host-1')
        manager.join_room(code, 'guest-1')
        manager.leave_room('host-1')
        assert manager.get_room(code) is None
        assert manager.get_room_by_session('guest-1') is None

    def test_leave_room_guest_keeps_room(self, manager):
        code = manager.create_room('host-1')
        manager.join_room(code, 'guest-1')
        manager.leave_room('guest-1')
        room = manager.get_room(code)
        assert room is not None
        assert room.guest_session_id is None
        assert room.game_phase == 'waiting'

    def test_creating_new_room_leaves_old(self, manager):
        code1 = manager.create_room('host-1')
        code2 = manager.create_room('host-1')
        assert code1 != code2
        assert manager.get_room(code1) is None
        assert manager.get_room(code2) is not None

    def test_room_count(self, manager):
        assert manager.get_room_count() == 0
        manager.create_room('host-1')
        assert manager.get_room_count() == 1
        manager.create_room('host-2')
        assert manager.get_room_count() == 2

    def test_update_room(self, manager):
        code = manager.create_room('host-1')
        manager.update_room(code, game_phase='bidding', dealer='East')
        room = manager.get_room(code)
        assert room.game_phase == 'bidding'
        assert room.dealer == 'East'

    def test_cleanup_inactive(self, manager):
        code = manager.create_room('host-1')
        room = manager.get_room(code)
        # Fake old activity
        room.last_activity = datetime.now() - timedelta(hours=2)
        removed = manager.cleanup_inactive(hours=1)
        assert removed == 1
        assert manager.get_room_count() == 0


# ===========================================================================
# RoomState — to_dict waiting_for logic
# ===========================================================================

class TestWaitingForLogic:

    def test_waiting_for_partner_when_north_bids(self, room):
        room.dealer = 'North'
        room.game_phase = 'bidding'
        room.auction_history = []
        # Guest (N) is current bidder, host (S) sees "waiting for partner"
        result = room.to_dict(for_session='host-1')
        assert result['current_bidder'] == 'N'
        assert result['waiting_for'] == 'partner'

    def test_waiting_for_ai_when_east_bids(self, room):
        room.dealer = 'North'
        room.game_phase = 'bidding'
        room.auction_history = ['Pass']  # N bid, now E
        result = room.to_dict(for_session='host-1')
        assert result['current_bidder'] == 'E'
        assert result['waiting_for'] == 'ai'

    def test_my_turn_when_south_bids(self, room):
        room.dealer = 'South'
        room.game_phase = 'bidding'
        room.auction_history = []
        result = room.to_dict(for_session='host-1')
        assert result['is_my_turn'] is True
