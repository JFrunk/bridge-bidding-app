"""
Room State Management - Thread-safe room storage for Team Practice Lobby

This module provides room-based state management for two human partners
to play together against AI opponents.

Room Architecture:
- Host (creator): Always plays South position
- Guest (joiner): Always plays North position
- AI: Controls East and West positions

Usage:
    # Initialize at app startup
    room_manager = RoomStateManager()

    # Create a room
    room_code = room_manager.create_room(host_session_id, settings)

    # Join a room
    success = room_manager.join_room(room_code, guest_session_id)

    # Get room by code or session
    room = room_manager.get_room(room_code)
    room = room_manager.get_room_by_session(session_id)
"""

import os
import random
import string
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from engine.play_engine import PlayState


@dataclass
class RoomSettings:
    """
    Room configuration settings (controlled by host)
    """
    deal_type: str = 'random'  # 'random' | 'convention'
    convention_filter: Optional[str] = None  # Convention name if deal_type == 'convention'
    ai_difficulty: str = 'advanced'  # 'beginner' | 'intermediate' | 'advanced' | 'expert'


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

    # Position assignments (fixed for Team Practice)
    host_position: str = 'S'  # Host always South
    guest_position: str = 'N'  # Guest always North

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

    # Settings (host-controlled)
    settings: RoomSettings = field(default_factory=RoomSettings)

    # Version tracking for efficient polling
    version: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

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

    def get_current_bidder(self) -> Optional[str]:
        """Get current bidder position based on auction state"""
        if self.game_phase != 'bidding':
            return None
        # Dealer position determines first bidder
        dealer_positions = ['N', 'E', 'S', 'W']
        dealer_idx = dealer_positions.index(self.dealer[0].upper())
        current_idx = (dealer_idx + len(self.auction_history)) % 4
        return dealer_positions[current_idx]

    def is_session_turn(self, session_id: str) -> bool:
        """Check if it's this session's turn to act"""
        position = self.get_position_for_session(session_id)
        if not position:
            return False

        if self.game_phase == 'bidding':
            return self.get_current_bidder() == position
        elif self.game_phase == 'playing' and self.play_state:
            return self.play_state.next_to_play == position
        return False

    def reset_hand(self):
        """Reset for a new hand"""
        self.deal = {'North': None, 'East': None, 'South': None, 'West': None}
        self.original_deal = None
        self.auction_history = []
        self.play_state = None
        self.game_phase = 'waiting' if not self.is_full() else 'bidding'
        self.increment_version()

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
            'settings': {
                'deal_type': self.settings.deal_type,
                'convention_filter': self.settings.convention_filter,
                'ai_difficulty': self.settings.ai_difficulty,
            },
            'created_at': self.created_at.isoformat(),
        }

        if for_session:
            position = self.get_position_for_session(for_session)
            result['my_position'] = position
            result['is_host'] = (for_session == self.host_session_id)
            result['is_my_turn'] = self.is_session_turn(for_session)

            # Include hand for this position
            if position and self.deal.get(self._full_position_name(position)):
                hand = self.deal[self._full_position_name(position)]
                result['my_hand'] = self._serialize_hand(hand)

            # Include current bidder info
            current_bidder = self.get_current_bidder()
            if current_bidder:
                result['current_bidder'] = current_bidder
                result['waiting_for'] = 'partner' if current_bidder in ('N', 'S') and current_bidder != position else 'ai'

        # Include play state if in playing phase
        if self.game_phase == 'playing' and self.play_state:
            result['play_state'] = self._serialize_play_state(for_session)

        return result

    def _serialize_play_state(self, for_session: Optional[str] = None) -> dict:
        """Serialize play state for API response"""
        if not self.play_state:
            return None

        ps = self.play_state
        position = self.get_position_for_session(for_session) if for_session else None

        # Determine declarer and dummy
        declarer = ps.contract.declarer
        from engine.play_engine import PlayEngine
        dummy = PlayEngine.partner(declarer)

        # Build visible hands based on position
        visible_hands = {}

        # Always see your own hand
        if position and position in ps.hands:
            visible_hands[position] = self._serialize_hand(ps.hands[position])

        # Dummy is visible after opening lead
        if ps.dummy_revealed and dummy in ps.hands:
            visible_hands[dummy] = self._serialize_hand(ps.hands[dummy])

        # Declarer always sees dummy
        if position == declarer and dummy in ps.hands:
            visible_hands[dummy] = self._serialize_hand(ps.hands[dummy])

        return {
            'contract': str(ps.contract),
            'declarer': declarer,
            'dummy': dummy,
            'next_to_play': ps.next_to_play,
            'current_trick': [
                {'rank': c.rank, 'suit': c.suit, 'player': p}
                for c, p in ps.current_trick
            ],
            'trick_history': [
                {
                    'cards': [{'rank': c.rank, 'suit': c.suit, 'player': p} for c, p in t.cards],
                    'winner': t.winner
                }
                for t in ps.trick_history
            ],
            'tricks_ns': ps.tricks_won.get('N', 0) + ps.tricks_won.get('S', 0),
            'tricks_ew': ps.tricks_won.get('E', 0) + ps.tricks_won.get('W', 0),
            'visible_hands': visible_hands,
            'dummy_revealed': ps.dummy_revealed,
        }

    def _full_position_name(self, short: str) -> str:
        """Convert S/N/E/W to full position name"""
        mapping = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
        return mapping.get(short, short)

    def _serialize_hand(self, hand) -> Optional[List[dict]]:
        """Serialize a Hand object to list of card dicts"""
        if hand is None:
            return None
        try:
            return [{'rank': c.rank, 'suit': c.suit} for c in hand.cards]
        except AttributeError:
            # Handle case where hand is already serialized
            if isinstance(hand, list):
                return hand
            return None


def generate_room_code(length: int = 6) -> str:
    """
    Generate a random room code

    Uses uppercase letters and digits, excluding ambiguous characters (0, O, I, L, 1)
    """
    # Exclude ambiguous characters
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(length))


class RoomStateManager:
    """
    Thread-safe manager for room state

    Provides room creation, joining, and state management for
    Team Practice Lobby feature.
    """

    def __init__(self):
        self._rooms: Dict[str, RoomState] = {}  # room_code -> RoomState
        self._session_to_room: Dict[str, str] = {}  # session_id -> room_code
        self._lock = threading.RLock()
        self._cleanup_threshold = 100  # Clean up when we hit this many rooms

    def create_room(self, host_session_id: str, settings: Optional[RoomSettings] = None) -> str:
        """
        Create a new room

        Args:
            host_session_id: Session ID of the room creator (will be South)
            settings: Optional room settings

        Returns:
            Room code (6-character string)
        """
        with self._lock:
            # Check if session is already in a room
            if host_session_id in self._session_to_room:
                existing_code = self._session_to_room[host_session_id]
                # Leave existing room first
                self.leave_room(host_session_id)

            # Generate unique room code
            room_code = generate_room_code()
            while room_code in self._rooms:
                room_code = generate_room_code()

            # Create room state
            room = RoomState(
                room_code=room_code,
                host_session_id=host_session_id,
                settings=settings or RoomSettings(),
            )

            self._rooms[room_code] = room
            self._session_to_room[host_session_id] = room_code

            # Periodic cleanup
            if len(self._rooms) > self._cleanup_threshold:
                self._cleanup_inactive_rooms()

            return room_code

    def join_room(self, room_code: str, guest_session_id: str) -> tuple[bool, str]:
        """
        Join an existing room

        Args:
            room_code: 6-character room code (case-insensitive)
            guest_session_id: Session ID of the joining player (will be North)

        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            # Normalize room code to uppercase
            room_code = room_code.upper().strip()

            # Check if room exists
            if room_code not in self._rooms:
                return False, 'Room not found'

            room = self._rooms[room_code]

            # Check if session is trying to join their own room
            if guest_session_id == room.host_session_id:
                return False, 'Cannot join your own room'

            # Check if room is already full
            if room.is_full():
                return False, 'Room is full'

            # Check if guest is already in another room
            if guest_session_id in self._session_to_room:
                self.leave_room(guest_session_id)

            # Join the room
            room.guest_session_id = guest_session_id
            room.game_phase = 'waiting'  # Still waiting for host to start game
            room.increment_version()

            self._session_to_room[guest_session_id] = room_code

            return True, 'Joined successfully'

    def leave_room(self, session_id: str) -> bool:
        """
        Leave current room

        Args:
            session_id: Session ID of the leaving player

        Returns:
            True if successfully left a room
        """
        with self._lock:
            if session_id not in self._session_to_room:
                return False

            room_code = self._session_to_room[session_id]
            room = self._rooms.get(room_code)

            if not room:
                del self._session_to_room[session_id]
                return False

            if session_id == room.host_session_id:
                # Host leaving - close the room entirely
                if room.guest_session_id:
                    del self._session_to_room[room.guest_session_id]
                del self._session_to_room[session_id]
                del self._rooms[room_code]
            else:
                # Guest leaving - remove from room
                room.guest_session_id = None
                room.game_phase = 'waiting'
                room.increment_version()
                del self._session_to_room[session_id]

            return True

    def get_room(self, room_code: str) -> Optional[RoomState]:
        """Get room by code"""
        with self._lock:
            room = self._rooms.get(room_code.upper().strip())
            if room:
                room.touch()
            return room

    def get_room_by_session(self, session_id: str) -> Optional[RoomState]:
        """Get room that a session belongs to"""
        with self._lock:
            room_code = self._session_to_room.get(session_id)
            if room_code:
                room = self._rooms.get(room_code)
                if room:
                    room.touch()
                return room
            return None

    def update_room(self, room_code: str, **changes) -> bool:
        """
        Update room state

        Args:
            room_code: Room code
            **changes: Key-value pairs to update

        Returns:
            True if room was updated
        """
        with self._lock:
            room = self._rooms.get(room_code.upper().strip())
            if not room:
                return False

            for key, value in changes.items():
                if hasattr(room, key):
                    setattr(room, key, value)

            room.increment_version()
            return True

    def get_room_count(self) -> int:
        """Get number of active rooms"""
        with self._lock:
            return len(self._rooms)

    def _cleanup_inactive_rooms(self, max_age_hours: int = 1):
        """
        Remove rooms not accessed in specified hours

        Called automatically when room count exceeds threshold.
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        to_remove = [
            code for code, room in self._rooms.items()
            if room.last_activity < cutoff
        ]

        for code in to_remove:
            room = self._rooms[code]
            # Clean up session mappings
            if room.host_session_id in self._session_to_room:
                del self._session_to_room[room.host_session_id]
            if room.guest_session_id and room.guest_session_id in self._session_to_room:
                del self._session_to_room[room.guest_session_id]
            del self._rooms[code]

        if to_remove:
            print(f"🧹 Cleaned up {len(to_remove)} inactive rooms")

    def cleanup_inactive(self, hours: int = 1) -> int:
        """
        Manually trigger cleanup of inactive rooms

        Args:
            hours: Remove rooms inactive for this many hours

        Returns:
            Number of rooms removed
        """
        with self._lock:
            initial_count = len(self._rooms)
            self._cleanup_inactive_rooms(max_age_hours=hours)
            return initial_count - len(self._rooms)

    def get_all_rooms_info(self) -> list:
        """Get info about all rooms (for debugging/monitoring)"""
        with self._lock:
            return [room.to_dict() for room in self._rooms.values()]


# Helper function to get room from request
def get_room_from_request(request, room_manager: RoomStateManager) -> Optional[RoomState]:
    """
    Extract room from request based on session ID

    Checks if the requesting session is in a room and returns that room.

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
