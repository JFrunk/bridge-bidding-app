"""
Room State Management - Redis-backed room storage for Team Practice Lobby

This module provides room-based state management for two human partners
to play together against AI opponents, using Redis for cross-process
state sharing and optimistic concurrency control.

Room Architecture:
- Host (creator): Always plays South position
- Guest (joiner): Always plays North position
- AI: Controls East and West positions

Redis Key Schema:
- room:{room_code}         -> JSON-serialized RoomState (TTL: 3600s)
- session:{session_id}     -> room_code string (TTL: 3600s)

Usage:
    # Initialize at app startup
    room_manager = RoomStateManager(redis_url='redis://localhost:6379/0')

    # Create a room
    room_code = room_manager.create_room(host_session_id, settings)

    # Atomic mutation with OCC
    with room_manager.mutate_room_by_session(session_id) as room:
        room.auction_history.append(bid)
"""

import json
import os
import random
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import redis

from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract, Trick, GamePhase
from utils.seats import (
    partner as seats_partner, normalize, active_seat_bidding, SEAT_NAMES
)

# TTL for all room and session keys (seconds)
ROOM_TTL = 3600

# Max OCC retries before raising conflict
MAX_OCC_RETRIES = 3


@dataclass
class RoomSettings:
    """Room configuration settings (controlled by host)"""
    deal_type: str = 'random'
    convention_filter: Optional[str] = None
    ai_difficulty: str = 'advanced'

    def to_dict(self) -> dict:
        return {
            'deal_type': self.deal_type,
            'convention_filter': self.convention_filter,
            'ai_difficulty': self.ai_difficulty,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'RoomSettings':
        return cls(
            deal_type=d.get('deal_type', 'random'),
            convention_filter=d.get('convention_filter'),
            ai_difficulty=d.get('ai_difficulty', 'advanced'),
        )


@dataclass
class RoomState:
    """
    Shared state for a practice room with two human partners

    Position mapping:
    - Host (creator): South position
    - Guest (joiner): North position
    - AI: East and West positions
    """
    room_code: str
    host_session_id: str
    guest_session_id: Optional[str] = None

    # User IDs (server-validated, for partnership tracking)
    host_user_id: Optional[str] = None
    guest_user_id: Optional[str] = None

    # Partnership ID (looked up/created when guest joins)
    partnership_id: Optional[int] = None

    # Position assignments (fixed for Team Practice)
    host_position: str = 'S'
    guest_position: str = 'N'

    # Shared game state
    deal: Dict[str, Any] = field(default_factory=lambda: {
        'North': None, 'East': None, 'South': None, 'West': None
    })
    original_deal: Optional[Dict[str, Any]] = None
    dealer: str = 'North'
    auction_history: List[str] = field(default_factory=list)
    vulnerability: str = 'None'
    play_state: Optional[PlayState] = None

    # Room phase: 'waiting' | 'bidding' | 'playing' | 'complete'
    game_phase: str = 'waiting'

    # Settings (either peer can update)
    settings: RoomSettings = field(default_factory=RoomSettings)

    # Mutual readiness tracking (peer model)
    ready_state: Dict[str, bool] = field(default_factory=dict)

    # Chat messages (ephemeral — destroyed on session end)
    chat_messages: List[Dict[str, Any]] = field(default_factory=list)

    # Bid feedback accumulated during auction (per human bid)
    bid_feedback: List[Dict[str, Any]] = field(default_factory=list)

    # Version tracking for efficient polling
    version: int = 0

    # Per-player last-seen timestamps (heartbeat via polling)
    last_seen: Dict[str, str] = field(default_factory=dict)

    # Timestamps (stored as ISO strings for JSON serialization)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())

    # Disconnect timeout in seconds
    DISCONNECT_TIMEOUT: int = 300

    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now().isoformat()

    def record_heartbeat(self, session_id: str):
        """Record that a player is still connected (called on each poll)"""
        self.last_seen[session_id] = datetime.now().isoformat()
        self.last_activity = datetime.now().isoformat()

    def is_partner_disconnected(self, session_id: str) -> bool:
        """Check if the other player has timed out"""
        partner_id = self.guest_session_id if session_id == self.host_session_id else self.host_session_id
        if not partner_id:
            return False
        last = self.last_seen.get(partner_id)
        if not last:
            return False
        last_dt = datetime.fromisoformat(last)
        return (datetime.now() - last_dt) > timedelta(seconds=self.DISCONNECT_TIMEOUT)

    def increment_version(self):
        """Increment version number (call after any state change)"""
        self.version += 1
        self.touch()

    def is_full(self) -> bool:
        """Check if room has both players"""
        return self.guest_session_id is not None

    def get_position_for_session(self, session_id: str) -> Optional[str]:
        """Get the position (S/N) for a given session ID"""
        if session_id == self.host_session_id:
            return self.host_position
        elif session_id == self.guest_session_id:
            return self.guest_position
        return None

    def is_session_in_room(self, session_id: str) -> bool:
        """Check if a session ID belongs to this room"""
        return session_id in (self.host_session_id, self.guest_session_id)

    def set_ready(self, session_id: str, ready: bool = True):
        """Set a player's ready state"""
        self.ready_state[session_id] = ready
        self.increment_version()

    def are_both_ready(self) -> bool:
        """Check if both players have signaled ready"""
        if not self.is_full():
            return False
        return (self.ready_state.get(self.host_session_id, False) and
                self.ready_state.get(self.guest_session_id, False))

    def clear_ready(self):
        """Reset both players' ready state (after state transition)"""
        self.ready_state = {}

    def get_current_bidder(self) -> Optional[str]:
        """Get current bidder position based on auction state"""
        if self.game_phase != 'bidding':
            return None
        dealer_short = normalize(self.dealer)
        return active_seat_bidding(dealer_short, len(self.auction_history))

    def is_session_turn(self, session_id: str) -> bool:
        """Check if it's this session's turn to act (includes declarer controlling dummy)"""
        position = self.get_position_for_session(session_id)
        if not position:
            return False

        if self.game_phase == 'bidding':
            return self.get_current_bidder() == position
        elif self.game_phase == 'playing' and self.play_state:
            next_player = self.play_state.next_to_play
            declarer = self.play_state.contract.declarer
            dummy = seats_partner(declarer)
            if position == dummy:
                return False
            if next_player == position:
                return True
            if position == declarer and next_player == dummy:
                return True
            return False
        return False

    def reset_hand(self):
        """Reset for a new hand"""
        self.deal = {'North': None, 'East': None, 'South': None, 'West': None}
        self.original_deal = None
        self.auction_history = []
        self.play_state = None
        self.bid_feedback = []
        self.game_phase = 'waiting' if not self.is_full() else 'bidding'
        self.increment_version()

    # =========================================================================
    # Storage serialization (Redis persistence — full state, no filtering)
    # =========================================================================

    def to_storage_dict(self) -> dict:
        """Serialize full RoomState for Redis storage"""
        deal_dict = {}
        for pos, hand in self.deal.items():
            if hand is None:
                deal_dict[pos] = None
            else:
                deal_dict[pos] = self._hand_to_cards(hand)

        original_deal_dict = None
        if self.original_deal:
            original_deal_dict = {}
            for pos, hand in self.original_deal.items():
                if hand is None:
                    original_deal_dict[pos] = None
                else:
                    original_deal_dict[pos] = self._hand_to_cards(hand)

        return {
            'room_code': self.room_code,
            'host_session_id': self.host_session_id,
            'guest_session_id': self.guest_session_id,
            'host_user_id': self.host_user_id,
            'guest_user_id': self.guest_user_id,
            'partnership_id': self.partnership_id,
            'host_position': self.host_position,
            'guest_position': self.guest_position,
            'deal': deal_dict,
            'original_deal': original_deal_dict,
            'dealer': self.dealer,
            'auction_history': self.auction_history,
            'vulnerability': self.vulnerability,
            'play_state': self.play_state.to_dict() if self.play_state else None,
            'game_phase': self.game_phase,
            'settings': self.settings.to_dict(),
            'ready_state': self.ready_state,
            'chat_messages': self.chat_messages,
            'bid_feedback': self.bid_feedback,
            'version': self.version,
            'last_seen': self.last_seen,
            'created_at': self.created_at,
            'last_activity': self.last_activity,
        }

    @classmethod
    def from_storage_dict(cls, d: dict) -> 'RoomState':
        """Deserialize RoomState from Redis storage"""
        deal = {}
        for pos, cards in d.get('deal', {}).items():
            if cards is None:
                deal[pos] = None
            else:
                deal[pos] = Hand(
                    [Card(rank=c['rank'], suit=c['suit']) for c in cards],
                    _skip_validation=True
                )

        original_deal = None
        if d.get('original_deal'):
            original_deal = {}
            for pos, cards in d['original_deal'].items():
                if cards is None:
                    original_deal[pos] = None
                else:
                    original_deal[pos] = Hand(
                        [Card(rank=c['rank'], suit=c['suit']) for c in cards],
                        _skip_validation=True
                    )

        play_state = None
        if d.get('play_state'):
            play_state = PlayState.from_dict(d['play_state'])

        return cls(
            room_code=d['room_code'],
            host_session_id=d['host_session_id'],
            guest_session_id=d.get('guest_session_id'),
            host_user_id=d.get('host_user_id'),
            guest_user_id=d.get('guest_user_id'),
            partnership_id=d.get('partnership_id'),
            host_position=d.get('host_position', 'S'),
            guest_position=d.get('guest_position', 'N'),
            deal=deal,
            original_deal=original_deal,
            dealer=d.get('dealer', 'North'),
            auction_history=d.get('auction_history', []),
            vulnerability=d.get('vulnerability', 'None'),
            play_state=play_state,
            game_phase=d.get('game_phase', 'waiting'),
            settings=RoomSettings.from_dict(d.get('settings', {})),
            ready_state=d.get('ready_state', {}),
            chat_messages=d.get('chat_messages', []),
            bid_feedback=d.get('bid_feedback', []),
            version=d.get('version', 0),
            last_seen=d.get('last_seen', {}),
            created_at=d.get('created_at', datetime.now().isoformat()),
            last_activity=d.get('last_activity', datetime.now().isoformat()),
        )

    # =========================================================================
    # View serialization (API response — filtered by session)
    # =========================================================================

    def to_dict(self, for_session: Optional[str] = None) -> dict:
        """
        Serialize room state for API response

        Args:
            for_session: If provided, includes position-specific info
        """
        result = {
            'room_code': self.room_code,
            'game_phase': self.game_phase,
            'partner_connected': self.is_full(),
            'dealer': self.dealer,
            'vulnerability': self.vulnerability,
            'auction_history': self.auction_history,
            'version': self.version,
            'settings': self.settings.to_dict(),
            'created_at': self.created_at,
        }

        if for_session:
            position = self.get_position_for_session(for_session)
            result['my_position'] = position
            result['is_host'] = (for_session == self.host_session_id)
            result['is_my_turn'] = self.is_session_turn(for_session)
            result['i_am_ready'] = self.ready_state.get(for_session, False)
            result['partner_ready'] = self.ready_state.get(
                self.guest_session_id if for_session == self.host_session_id else self.host_session_id,
                False
            )
            result['both_ready'] = self.are_both_ready()
            result['partner_disconnected'] = self.is_partner_disconnected(for_session)

            # Include hand for this position
            if position and self.deal.get(SEAT_NAMES.get(position, position)):
                hand = self.deal[SEAT_NAMES[position]]
                result['my_hand'] = self._serialize_hand(hand)

            # Hand review: reveal partner's hand when auction is complete
            if self.game_phase == 'complete':
                partner_pos = seats_partner(position)
                partner_hand = self.deal.get(SEAT_NAMES[partner_pos])
                if partner_hand:
                    result['partner_hand'] = self._serialize_hand(partner_hand)
                    result['partner_position'] = partner_pos

                # Include bid feedback for review
                if self.bid_feedback:
                    my_feedback = [f for f in self.bid_feedback if f.get('position') == position]
                    result['bid_feedback'] = my_feedback

            # Include current bidder info
            current_bidder = self.get_current_bidder()
            result['current_bidder'] = current_bidder
            if current_bidder:
                result['waiting_for'] = 'partner' if current_bidder in ('N', 'S') and current_bidder != position else 'ai'

        # Include play state if in playing phase
        if self.game_phase == 'playing' and self.play_state:
            result['play_state'] = self._serialize_play_state(for_session)

        # Include chat messages
        result['chat_messages'] = self.chat_messages

        return result

    def _serialize_play_state(self, for_session: Optional[str] = None) -> dict:
        """Serialize play state matching solo /api/get-play-state format"""
        if not self.play_state:
            return None

        ps = self.play_state
        position = self.get_position_for_session(for_session) if for_session else None

        declarer = ps.contract.declarer
        dummy = seats_partner(declarer)

        visible_hands = {}
        if position and position in ps.hands:
            visible_hands[position] = {
                'cards': self._serialize_hand(ps.hands[position]),
                'position': position
            }
        if ps.dummy_revealed and dummy in ps.hands:
            visible_hands[dummy] = {
                'cards': self._serialize_hand(ps.hands[dummy]),
                'position': dummy
            }
        if position == declarer and dummy in ps.hands:
            visible_hands[dummy] = {
                'cards': self._serialize_hand(ps.hands[dummy]),
                'position': dummy
            }

        trick_complete = len(ps.current_trick) == 4
        trick_winner = None
        if trick_complete and ps.trick_history:
            trick_winner = ps.trick_history[-1].winner

        dummy_hand = None
        opening_lead_made = len(ps.current_trick) >= 1 or len(ps.trick_history) >= 1
        if ps.dummy_revealed and opening_lead_made and dummy in ps.hands:
            dummy_hand = {
                'cards': self._serialize_hand(ps.hands[dummy]),
                'position': dummy
            }

        is_user_turn = self.is_session_turn(for_session) if for_session else False
        controllable_positions = []
        if position:
            if position in ('N', 'S'):
                controllable_positions.append(position)
            if position == declarer:
                controllable_positions.append(dummy)

        return {
            'contract': {
                'level': ps.contract.level,
                'strain': ps.contract.strain,
                'declarer': declarer,
                'doubled': getattr(ps.contract, 'doubled', 0),
            },
            'next_to_play': ps.next_to_play,
            'dummy': dummy,
            'dummy_revealed': ps.dummy_revealed,
            'dummy_hand': dummy_hand,
            'current_trick': [
                {'card': {'rank': c.rank, 'suit': c.suit}, 'position': p}
                for c, p in ps.current_trick
            ],
            'trick_complete': trick_complete,
            'trick_winner': trick_winner,
            'trick_history': [
                {
                    'cards': [{'card': {'rank': c.rank, 'suit': c.suit}, 'position': p} for c, p in t.cards],
                    'leader': getattr(t, 'leader', None),
                    'winner': t.winner
                }
                for t in ps.trick_history
            ],
            'tricks_won': dict(ps.tricks_won),
            'visible_hands': visible_hands,
            'is_user_turn': is_user_turn,
            'controllable_positions': controllable_positions,
        }

    def _full_position_name(self, short: str) -> str:
        """Convert S/N/E/W to full position name"""
        return SEAT_NAMES.get(short, short)

    def _serialize_hand(self, hand) -> Optional[List[dict]]:
        """Serialize a Hand object to list of card dicts"""
        if hand is None:
            return None
        try:
            return [{'rank': c.rank, 'suit': c.suit} for c in hand.cards]
        except AttributeError:
            if isinstance(hand, list):
                return hand
            return None

    @staticmethod
    def _hand_to_cards(hand) -> Optional[list]:
        """Convert Hand object to card dict list for storage"""
        if hand is None:
            return None
        try:
            return [{'rank': c.rank, 'suit': c.suit} for c in hand.cards]
        except AttributeError:
            if isinstance(hand, list):
                return hand
            return None


def generate_room_code(length: int = 6) -> str:
    """
    Generate a random room code

    Uses uppercase letters and digits, excluding ambiguous characters (0, O, I, L, 1)
    """
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(length))


class RoomConflictError(Exception):
    """Raised when an OCC WATCH/MULTI transaction fails after max retries"""
    pass


class RoomStateManager:
    """
    Redis-backed manager for room state with optimistic concurrency control.

    All state-mutating operations use Redis WATCH/MULTI pipelines to prevent
    race conditions across Gunicorn workers. Read operations use standard
    GET with automatic TTL refresh.

    Key schema:
        room:{room_code}       -> JSON RoomState (TTL: 3600s)
        session:{session_id}   -> room_code string (TTL: 3600s)
    """

    def __init__(self, redis_url: Optional[str] = None, redis_client=None):
        """
        Args:
            redis_url: Redis connection URL (default: from REDIS_URL env or localhost)
            redis_client: Pre-built Redis client (for testing with fakeredis)
        """
        if redis_client is not None:
            self._redis = redis_client
        else:
            url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self._pool = redis.ConnectionPool.from_url(url, decode_responses=True)
            self._redis = redis.Redis(connection_pool=self._pool)

    # =========================================================================
    # Key helpers
    # =========================================================================

    @staticmethod
    def _room_key(room_code: str) -> str:
        return f'room:{room_code.upper().strip()}'

    @staticmethod
    def _session_key(session_id: str) -> str:
        return f'session:{session_id}'

    # =========================================================================
    # Low-level Redis operations
    # =========================================================================

    def _load_room(self, room_code: str) -> Optional[RoomState]:
        """Load and deserialize a room from Redis"""
        data = self._redis.get(self._room_key(room_code))
        if data is None:
            return None
        return RoomState.from_storage_dict(json.loads(data))

    def _save_room(self, room: RoomState, pipe=None):
        """Serialize and save a room to Redis (with TTL refresh)"""
        r = pipe or self._redis
        key = self._room_key(room.room_code)
        r.set(key, json.dumps(room.to_storage_dict()), ex=ROOM_TTL)

    def _save_session(self, session_id: str, room_code: str, pipe=None):
        """Map session -> room_code in Redis (with TTL refresh)"""
        r = pipe or self._redis
        r.set(self._session_key(session_id), room_code.upper().strip(), ex=ROOM_TTL)

    def _delete_session(self, session_id: str, pipe=None):
        """Remove session mapping"""
        r = pipe or self._redis
        r.delete(self._session_key(session_id))

    def _delete_room(self, room_code: str, pipe=None):
        """Remove room key"""
        r = pipe or self._redis
        r.delete(self._room_key(room_code))

    def _get_room_code_for_session(self, session_id: str) -> Optional[str]:
        """Look up which room a session belongs to"""
        return self._redis.get(self._session_key(session_id))

    # =========================================================================
    # OCC mutation
    # =========================================================================

    def _occ_execute(self, room_code: str, mutation_fn):
        """
        Execute a mutation function with Redis WATCH/MULTI/EXEC retry loop.

        The mutation_fn receives a RoomState, mutates it in place, and may
        return a value. If another writer modified the key between WATCH and
        EXEC, the entire function is retried with a fresh snapshot.

        Args:
            room_code: Normalized room code
            mutation_fn: callable(RoomState) -> Any

        Returns:
            Tuple of (room_after_mutation, return_value_from_fn)

        Raises:
            KeyError: If room does not exist
            RoomConflictError: After MAX_OCC_RETRIES failed attempts
        """
        room_key = self._room_key(room_code)

        for attempt in range(MAX_OCC_RETRIES):
            pipe = self._redis.pipeline()
            try:
                pipe.watch(room_key)
                raw = pipe.get(room_key)
                if raw is None:
                    pipe.unwatch()
                    raise KeyError(f'Room {room_code} not found')

                room = RoomState.from_storage_dict(json.loads(raw))

                # Run the caller's mutation
                result = mutation_fn(room)

                # Commit atomically
                pipe.multi()
                pipe.set(room_key, json.dumps(room.to_storage_dict()), ex=ROOM_TTL)

                # Refresh session TTLs
                if room.host_session_id:
                    pipe.set(
                        self._session_key(room.host_session_id),
                        room.room_code, ex=ROOM_TTL
                    )
                if room.guest_session_id:
                    pipe.set(
                        self._session_key(room.guest_session_id),
                        room.room_code, ex=ROOM_TTL
                    )

                pipe.execute()
                return room, result  # Success
            except redis.WatchError:
                continue
            finally:
                pipe.reset()

        raise RoomConflictError(
            f'Room {room_code} was modified concurrently after {MAX_OCC_RETRIES} retries'
        )

    @contextmanager
    def mutate_room(self, room_code: str):
        """
        Atomic room mutation via Redis WATCH/MULTI (context manager API).

        Usage:
            with room_manager.mutate_room(code) as room:
                room.auction_history.append(bid)
                room.increment_version()
            # room is saved atomically on successful exit

        Note: The context manager does NOT retry on WatchError — the caller's
        mutations run once. For automatic retry semantics, use _occ_execute()
        directly with a pure function. This context manager uses a single
        WATCH/yield/EXEC pass; if a concurrent write occurs during the yield,
        RoomConflictError is raised.

        Raises:
            RoomConflictError: If a concurrent write occurred
            KeyError: If room does not exist
        """
        room_code = room_code.upper().strip()
        room_key = self._room_key(room_code)

        pipe = self._redis.pipeline()
        try:
            pipe.watch(room_key)
            raw = pipe.get(room_key)
            if raw is None:
                pipe.unwatch()
                raise KeyError(f'Room {room_code} not found')

            room = RoomState.from_storage_dict(json.loads(raw))

            yield room

            # Commit the mutation atomically
            pipe.multi()
            pipe.set(room_key, json.dumps(room.to_storage_dict()), ex=ROOM_TTL)

            if room.host_session_id:
                pipe.set(
                    self._session_key(room.host_session_id),
                    room.room_code, ex=ROOM_TTL
                )
            if room.guest_session_id:
                pipe.set(
                    self._session_key(room.guest_session_id),
                    room.room_code, ex=ROOM_TTL
                )

            pipe.execute()
        except redis.WatchError:
            raise RoomConflictError(
                f'Room {room_code} was modified concurrently'
            )
        finally:
            pipe.reset()

    @contextmanager
    def mutate_room_by_session(self, session_id: str):
        """
        Convenience wrapper: look up room by session, then mutate atomically.

        Raises:
            KeyError: If session is not in any room
            RoomConflictError: If a concurrent write occurred
        """
        room_code = self._get_room_code_for_session(session_id)
        if not room_code:
            raise KeyError(f'Session {session_id} is not in any room')
        with self.mutate_room(room_code) as room:
            yield room

    # =========================================================================
    # Room lifecycle (create / join / leave)
    # =========================================================================

    def create_room(self, host_session_id: str, settings: Optional[RoomSettings] = None) -> str:
        """
        Create a new room.

        If the host is already in a room, leaves it first.

        Returns:
            Room code (6-character string)
        """
        # Leave existing room if any
        existing_code = self._get_room_code_for_session(host_session_id)
        if existing_code:
            self.leave_room(host_session_id)

        # Generate unique room code
        room_code = generate_room_code()
        while self._redis.exists(self._room_key(room_code)):
            room_code = generate_room_code()

        room = RoomState(
            room_code=room_code,
            host_session_id=host_session_id,
            settings=settings or RoomSettings(),
        )

        # Atomic write: room + session mapping
        pipe = self._redis.pipeline()
        pipe.set(self._room_key(room_code), json.dumps(room.to_storage_dict()), ex=ROOM_TTL)
        pipe.set(self._session_key(host_session_id), room_code, ex=ROOM_TTL)
        pipe.execute()

        return room_code

    def join_room(self, room_code: str, guest_session_id: str) -> tuple:
        """
        Join an existing room.

        Uses OCC to atomically check + update the room.

        Returns:
            Tuple of (success: bool, message: str)
        """
        room_code = room_code.upper().strip()
        room_key = self._room_key(room_code)

        for attempt in range(MAX_OCC_RETRIES):
            pipe = self._redis.pipeline()
            try:
                pipe.watch(room_key)
                raw = pipe.get(room_key)
                if raw is None:
                    pipe.unwatch()
                    return False, 'Room not found'

                room = RoomState.from_storage_dict(json.loads(raw))

                if guest_session_id == room.host_session_id:
                    pipe.unwatch()
                    return False, 'Cannot join your own room'

                if room.is_full():
                    pipe.unwatch()
                    return False, 'Room is full'

                # Leave existing room if guest is elsewhere
                existing_code = self._get_room_code_for_session(guest_session_id)
                if existing_code:
                    pipe.unwatch()
                    self.leave_room(guest_session_id)
                    # Restart the watch since we released
                    continue

                # Apply mutation
                room.guest_session_id = guest_session_id
                room.game_phase = 'waiting'
                room.increment_version()

                pipe.multi()
                pipe.set(room_key, json.dumps(room.to_storage_dict()), ex=ROOM_TTL)
                pipe.set(self._session_key(guest_session_id), room_code, ex=ROOM_TTL)
                # Refresh host session TTL
                pipe.set(
                    self._session_key(room.host_session_id),
                    room_code, ex=ROOM_TTL
                )
                pipe.execute()
                return True, 'Joined successfully'
            except redis.WatchError:
                continue
            finally:
                pipe.reset()

        return False, 'Room was modified concurrently, please try again'

    def leave_room(self, session_id: str) -> bool:
        """
        Leave current room.

        Host leaving destroys the room. Guest leaving reverts to waiting state.
        """
        room_code = self._get_room_code_for_session(session_id)
        if not room_code:
            return False

        room_key = self._room_key(room_code)

        for attempt in range(MAX_OCC_RETRIES):
            pipe = self._redis.pipeline()
            try:
                pipe.watch(room_key)
                raw = pipe.get(room_key)
                if raw is None:
                    pipe.unwatch()
                    # Room already gone — just clean up session
                    self._delete_session(session_id)
                    return False

                room = RoomState.from_storage_dict(json.loads(raw))

                pipe.multi()

                if session_id == room.host_session_id:
                    # Host leaving — destroy room
                    pipe.delete(room_key)
                    pipe.delete(self._session_key(session_id))
                    if room.guest_session_id:
                        pipe.delete(self._session_key(room.guest_session_id))
                else:
                    # Guest leaving — keep room, reset to waiting
                    room.guest_session_id = None
                    room.game_phase = 'waiting'
                    room.increment_version()
                    pipe.set(room_key, json.dumps(room.to_storage_dict()), ex=ROOM_TTL)
                    pipe.delete(self._session_key(session_id))

                pipe.execute()
                return True
            except redis.WatchError:
                continue
            finally:
                pipe.reset()

        return False

    # =========================================================================
    # Read operations (no OCC needed)
    # =========================================================================

    def get_room(self, room_code: str) -> Optional[RoomState]:
        """Get room by code (read-only snapshot)"""
        room_code = room_code.upper().strip()
        room = self._load_room(room_code)
        if room:
            # Refresh TTL on read
            self._redis.expire(self._room_key(room_code), ROOM_TTL)
        return room

    def get_room_by_session(self, session_id: str) -> Optional[RoomState]:
        """Get room that a session belongs to (read-only snapshot)"""
        room_code = self._get_room_code_for_session(session_id)
        if not room_code:
            return None
        room = self._load_room(room_code)
        if room:
            self._redis.expire(self._room_key(room_code), ROOM_TTL)
        return room

    def update_room(self, room_code: str, **changes) -> bool:
        """
        Update room state fields atomically.

        For complex mutations, prefer mutate_room() context manager.
        """
        try:
            with self.mutate_room(room_code) as room:
                for key, value in changes.items():
                    if hasattr(room, key):
                        setattr(room, key, value)
                room.increment_version()
            return True
        except (KeyError, RoomConflictError):
            return False

    def get_room_count(self) -> int:
        """Get number of active rooms (approximate — uses Redis SCAN)"""
        count = 0
        for _ in self._redis.scan_iter(match='room:*', count=100):
            count += 1
        return count

    def get_all_rooms_info(self) -> list:
        """Get info about all rooms (for debugging/monitoring)"""
        rooms = []
        for key in self._redis.scan_iter(match='room:*', count=100):
            raw = self._redis.get(key)
            if raw:
                room = RoomState.from_storage_dict(json.loads(raw))
                rooms.append(room.to_dict())
        return rooms


# Helper function to get room from request
def get_room_from_request(request, room_manager: RoomStateManager) -> Optional[RoomState]:
    """
    Extract room from request based on session ID

    Args:
        request: Flask request object
        room_manager: RoomStateManager instance

    Returns:
        RoomState if session is in a room, None otherwise
    """
    from core.session_state import get_session_id_from_request

    session_id = get_session_id_from_request(request)
    if not session_id:
        return None

    return room_manager.get_room_by_session(session_id)
