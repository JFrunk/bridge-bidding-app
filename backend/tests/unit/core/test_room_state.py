"""
Unit tests for room state management (partner practice).

Tests RoomState logic: seat math, turn detection, bidder calculation,
partner resolution, and RoomStateManager lifecycle with Redis (fakeredis).

No database or Flask required — uses fakeredis for in-memory Redis emulation.
"""
import sys
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import fakeredis

sys.path.insert(0, 'backend')

from core.room_state import (
    RoomState, RoomStateManager, RoomSettings, RoomConflictError,
    generate_room_code, ROOM_TTL
)
from engine.play_engine import PlayState, Contract, Trick, GamePhase
from engine.hand import Hand, Card


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
    """RoomStateManager backed by fakeredis (isolated per test)."""
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    return RoomStateManager(redis_client=fake_redis)


@pytest.fixture
def fake_redis():
    """Raw fakeredis instance for low-level assertions."""
    return fakeredis.FakeRedis(decode_responses=True)


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


def _make_hand():
    """Create a valid 13-card hand for serialization tests."""
    ranks = '23456789TJQKA'
    cards = [Card(rank=r, suit='♠') for r in ranks]
    return Hand(cards)


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
        ('North', 1, 'E'),
        ('North', 2, 'S'),
        ('North', 3, 'W'),
        ('North', 4, 'N'),
        ('South', 1, 'W'),
        ('South', 2, 'N'),
        ('East', 1, 'S'),
        ('West', 1, 'N'),
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
        assert room.is_session_turn('host-1') is True
        assert room.is_session_turn('guest-1') is False

    def test_guest_turn_when_north_deals(self, room):
        room.dealer = 'North'
        room.game_phase = 'bidding'
        room.auction_history = []
        assert room.is_session_turn('guest-1') is True
        assert room.is_session_turn('host-1') is False

    def test_ai_turn_no_human_session(self, room):
        room.dealer = 'North'
        room.game_phase = 'bidding'
        room.auction_history = ['Pass']
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
        assert room.is_session_turn('host-1') is True
        assert room.is_session_turn('guest-1') is False

    def test_declarer_south_controls_dummy_north(self, room):
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='S', next_to_play='N')
        assert room.is_session_turn('host-1') is True

    def test_declarer_north_controls_dummy_south(self, room):
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='N', next_to_play='S')
        assert room.is_session_turn('guest-1') is True
        assert room.is_session_turn('host-1') is False

    def test_ai_turn_no_human_control(self, room):
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='S', next_to_play='E')
        assert room.is_session_turn('host-1') is False
        assert room.is_session_turn('guest-1') is False

    def test_ai_declarer_no_human_turn(self, room):
        room.game_phase = 'playing'
        room.play_state = _make_play_state(declarer='E', next_to_play='W')
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
        room = RoomState(
            room_code='XYZ789',
            host_session_id='host-1',
            guest_session_id='guest-1',
            game_phase='complete',
        )
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
        old_time = datetime.now() - timedelta(seconds=room.DISCONNECT_TIMEOUT + 10)
        room.last_seen['guest-1'] = old_time.isoformat()
        assert room.is_partner_disconnected('host-1')

    def test_partner_not_disconnected_within_timeout(self, room):
        room.record_heartbeat('guest-1')
        recent_time = datetime.now() - timedelta(seconds=room.DISCONNECT_TIMEOUT - 10)
        room.last_seen['guest-1'] = recent_time.isoformat()
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
# RoomState — Storage serialization round-trip
# ===========================================================================

class TestStorageSerialization:

    def test_basic_round_trip(self, room):
        """RoomState survives to_storage_dict -> from_storage_dict"""
        room.game_phase = 'bidding'
        room.auction_history = ['1♣', 'Pass']
        room.vulnerability = 'NS'
        room.version = 5

        d = room.to_storage_dict()
        restored = RoomState.from_storage_dict(d)

        assert restored.room_code == room.room_code
        assert restored.host_session_id == room.host_session_id
        assert restored.guest_session_id == room.guest_session_id
        assert restored.game_phase == room.game_phase
        assert restored.auction_history == room.auction_history
        assert restored.vulnerability == room.vulnerability
        assert restored.version == room.version

    def test_round_trip_with_hands(self):
        """Hand objects survive serialization"""
        ranks = '23456789TJQKA'
        south_cards = [Card(rank=r, suit='♠') for r in ranks]
        north_cards = [Card(rank=r, suit='♥') for r in ranks]

        room = RoomState(
            room_code='TEST',
            host_session_id='host-1',
            deal={
                'South': Hand(south_cards),
                'North': Hand(north_cards),
                'East': None,
                'West': None,
            }
        )

        d = room.to_storage_dict()
        restored = RoomState.from_storage_dict(d)

        assert restored.deal['South'] is not None
        assert len(restored.deal['South'].cards) == 13
        assert restored.deal['East'] is None

    def test_round_trip_with_play_state(self):
        """PlayState survives serialization"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        ranks = '23456789TJQKA'
        hands = {
            'S': Hand([Card(rank=r, suit='♠') for r in ranks]),
            'N': Hand([Card(rank=r, suit='♥') for r in ranks]),
            'E': Hand([Card(rank=r, suit='♦') for r in ranks]),
            'W': Hand([Card(rank=r, suit='♣') for r in ranks]),
        }

        trick = Trick(
            cards=[(Card('A', '♠'), 'S'), (Card('K', '♥'), 'W')],
            leader='S',
            winner='S',
        )

        ps = PlayState(
            contract=contract,
            hands=hands,
            current_trick=[(Card('Q', '♠'), 'S')],
            tricks_won={'N': 2, 'S': 1, 'E': 0, 'W': 0},
            trick_history=[trick],
            next_to_play='W',
            dummy_revealed=True,
            current_trick_leader='S',
            phase=GamePhase.PLAY_IN_PROGRESS,
        )

        room = RoomState(
            room_code='PLAY1',
            host_session_id='host-1',
            play_state=ps,
            game_phase='playing',
        )

        d = room.to_storage_dict()
        json_str = json.dumps(d)  # Must be JSON-serializable
        restored = RoomState.from_storage_dict(json.loads(json_str))

        assert restored.play_state is not None
        assert restored.play_state.contract.level == 3
        assert restored.play_state.contract.strain == 'NT'
        assert restored.play_state.contract.doubled == 1
        assert restored.play_state.next_to_play == 'W'
        assert restored.play_state.dummy_revealed is True
        assert len(restored.play_state.trick_history) == 1
        assert restored.play_state.trick_history[0].winner == 'S'
        assert len(restored.play_state.current_trick) == 1
        assert restored.play_state.phase == GamePhase.PLAY_IN_PROGRESS

    def test_settings_round_trip(self):
        """RoomSettings survives serialization"""
        settings = RoomSettings(deal_type='convention', convention_filter='stayman', ai_difficulty='expert')
        room = RoomState(
            room_code='SET1',
            host_session_id='host-1',
            settings=settings,
        )

        d = room.to_storage_dict()
        restored = RoomState.from_storage_dict(d)

        assert restored.settings.deal_type == 'convention'
        assert restored.settings.convention_filter == 'stayman'
        assert restored.settings.ai_difficulty == 'expert'


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
        ambiguous = set('0OIL1')
        for _ in range(100):
            code = generate_room_code()
            assert ambiguous.isdisjoint(set(code)), f"Code {code} contains ambiguous character"


# ===========================================================================
# RoomStateManager — Redis-backed Lifecycle
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


# ===========================================================================
# RoomStateManager — Redis key schema and TTL
# ===========================================================================

class TestRedisKeySchema:

    def test_room_key_created(self, fake_redis):
        mgr = RoomStateManager(redis_client=fake_redis)
        code = mgr.create_room('host-1')
        assert fake_redis.exists(f'room:{code}') == 1

    def test_session_key_created(self, fake_redis):
        mgr = RoomStateManager(redis_client=fake_redis)
        code = mgr.create_room('host-1')
        assert fake_redis.get('session:host-1') == code

    def test_ttl_applied(self, fake_redis):
        mgr = RoomStateManager(redis_client=fake_redis)
        code = mgr.create_room('host-1')
        ttl = fake_redis.ttl(f'room:{code}')
        assert ttl > 0
        assert ttl <= ROOM_TTL

    def test_session_ttl_applied(self, fake_redis):
        mgr = RoomStateManager(redis_client=fake_redis)
        code = mgr.create_room('host-1')
        ttl = fake_redis.ttl('session:host-1')
        assert ttl > 0
        assert ttl <= ROOM_TTL

    def test_host_leave_deletes_keys(self, fake_redis):
        mgr = RoomStateManager(redis_client=fake_redis)
        code = mgr.create_room('host-1')
        mgr.join_room(code, 'guest-1')
        mgr.leave_room('host-1')

        assert fake_redis.exists(f'room:{code}') == 0
        assert fake_redis.exists('session:host-1') == 0
        assert fake_redis.exists('session:guest-1') == 0


# ===========================================================================
# RoomStateManager — OCC (mutate_room context manager)
# ===========================================================================

class TestOCCMutateRoom:

    def test_basic_mutation(self, manager):
        """mutate_room atomically updates state"""
        code = manager.create_room('host-1')

        with manager.mutate_room(code) as room:
            room.game_phase = 'bidding'
            room.increment_version()

        reloaded = manager.get_room(code)
        assert reloaded.game_phase == 'bidding'
        assert reloaded.version == 1

    def test_mutate_by_session(self, manager):
        """mutate_room_by_session resolves session -> room"""
        code = manager.create_room('host-1')
        manager.join_room(code, 'guest-1')

        with manager.mutate_room_by_session('guest-1') as room:
            room.set_ready('guest-1')

        reloaded = manager.get_room(code)
        assert reloaded.ready_state.get('guest-1') is True

    def test_mutate_nonexistent_raises_keyerror(self, manager):
        with pytest.raises(KeyError):
            with manager.mutate_room('NOTREAL') as room:
                pass

    def test_mutate_session_not_in_room_raises_keyerror(self, manager):
        with pytest.raises(KeyError):
            with manager.mutate_room_by_session('nobody') as room:
                pass

    def test_occ_execute_retries_on_watch_error(self, fake_redis):
        """_occ_execute retries mutation_fn on WatchError up to MAX_OCC_RETRIES"""
        import redis as redis_lib
        mgr = RoomStateManager(redis_client=fake_redis)
        code = mgr.create_room('host-1')

        call_count = 0
        original_pipeline = fake_redis.pipeline

        def counting_pipeline(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            pipe = original_pipeline(*args, **kwargs)
            if call_count <= 2:
                # First two attempts: simulate concurrent modification
                original_execute = pipe.execute
                def raise_watch(*a, **kw):
                    raise redis_lib.WatchError("Simulated conflict")
                pipe.execute = raise_watch
            return pipe

        fake_redis.pipeline = counting_pipeline

        # Third attempt should succeed
        room, _ = mgr._occ_execute(code, lambda r: setattr(r, 'game_phase', 'bidding'))
        assert room.game_phase == 'bidding'
        assert call_count == 3  # Two failures + one success

    def test_occ_execute_raises_after_max_retries(self, fake_redis):
        """_occ_execute raises RoomConflictError after MAX_OCC_RETRIES failures"""
        import redis as redis_lib
        mgr = RoomStateManager(redis_client=fake_redis)
        code = mgr.create_room('host-1')

        original_pipeline = fake_redis.pipeline

        def always_conflict_pipeline(*args, **kwargs):
            pipe = original_pipeline(*args, **kwargs)
            original_execute = pipe.execute
            def raise_watch(*a, **kw):
                raise redis_lib.WatchError("Simulated conflict")
            pipe.execute = raise_watch
            return pipe

        fake_redis.pipeline = always_conflict_pipeline

        with pytest.raises(RoomConflictError):
            mgr._occ_execute(code, lambda r: setattr(r, 'game_phase', 'bidding'))

    def test_context_manager_raises_on_watch_error(self, fake_redis):
        """mutate_room context manager raises RoomConflictError on single WatchError"""
        import redis as redis_lib
        mgr = RoomStateManager(redis_client=fake_redis)
        code = mgr.create_room('host-1')

        original_pipeline = fake_redis.pipeline

        def conflict_pipeline(*args, **kwargs):
            pipe = original_pipeline(*args, **kwargs)
            original_execute = pipe.execute
            def raise_watch(*a, **kw):
                raise redis_lib.WatchError("Simulated conflict")
            pipe.execute = raise_watch
            return pipe

        fake_redis.pipeline = conflict_pipeline

        with pytest.raises(RoomConflictError):
            with mgr.mutate_room(code) as room:
                room.game_phase = 'bidding'


# ===========================================================================
# RoomState — to_dict waiting_for logic
# ===========================================================================

class TestWaitingForLogic:

    def test_waiting_for_partner_when_north_bids(self, room):
        room.dealer = 'North'
        room.game_phase = 'bidding'
        room.auction_history = []
        result = room.to_dict(for_session='host-1')
        assert result['current_bidder'] == 'N'
        assert result['waiting_for'] == 'partner'

    def test_waiting_for_ai_when_east_bids(self, room):
        room.dealer = 'North'
        room.game_phase = 'bidding'
        room.auction_history = ['Pass']
        result = room.to_dict(for_session='host-1')
        assert result['current_bidder'] == 'E'
        assert result['waiting_for'] == 'ai'

    def test_my_turn_when_south_bids(self, room):
        room.dealer = 'South'
        room.game_phase = 'bidding'
        room.auction_history = []
        result = room.to_dict(for_session='host-1')
        assert result['is_my_turn'] is True
