"""
Session State Management - Thread-safe per-user state storage

This module replaces global state variables with per-session state storage.
Each user session maintains its own isolated state to prevent race conditions
and data leakage between concurrent users.

Usage:
    # Initialize at app startup
    state_manager = SessionStateManager()

    # Get state for current request
    state = state_manager.get_or_create(session_id)

    # Access state
    state.deal = {'North': hand_n, ...}
    state.vulnerability = "Both"
    state.play_state = play_state_obj

Environment Variables:
    DEFAULT_AI_DIFFICULTY: Set default AI difficulty level
        - Options: beginner, intermediate, advanced, expert
        - Default (dev): intermediate
        - Recommended (production): expert
"""

import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from engine.play_engine import PlayState
from engine.session_manager import GameSession

# Get default AI difficulty from environment variable
#
# AI Difficulty Strategy:
# - PRODUCTION (Linux - DDS available): Auto-default to 'expert' (DDS, 9/10)
# - DEVELOPMENT (macOS M1/M2 - DDS crashes): Default to 'advanced' (Minimax depth 3, 8/10)
# - Can be overridden with DEFAULT_AI_DIFFICULTY environment variable
#
# Why 'advanced' instead of 'intermediate' for development?
# - Minimax depth 3 (advanced) provides competent 8/10 gameplay without DDS crashes
# - Still strong enough for good user experience
#
# Smart Default: Check if DDS is available, use expert if it is
def _get_smart_default_ai():
    """
    Smart default AI selection with platform-based safety:
    - macOS/Windows: ALWAYS use 'advanced' (DDS unstable, crashes with Error -14)
    - Linux with DDS: use 'expert' for 9/10 play
    - Linux without DDS: use 'advanced' for 8/10 play
    - Can be overridden with DEFAULT_AI_DIFFICULTY env var

    See: BUG_DDS_CRASH_2025-10-18.md for macOS DDS crash details
    """
    import platform

    # Check for explicit environment variable first
    env_setting = os.environ.get('DEFAULT_AI_DIFFICULTY')
    if env_setting:
        return env_setting

    # CRITICAL: Force 'advanced' on macOS regardless of DDS availability
    # DDS crashes on macOS M1/M2 with Error Code -14, segmentation faults
    # See: DDS_MACOS_INSTABILITY_REPORT.md, BUG_DDS_CRASH_2025-10-18.md
    if platform.system() == 'Darwin':  # macOS
        return 'advanced'

    # Linux/Windows: Auto-detect based on DDS availability
    try:
        from engine.play.ai.dds_ai import DDS_AVAILABLE
        if DDS_AVAILABLE and platform.system() == 'Linux':
            # Production Linux with DDS - use expert (9/10)
            return 'expert'
        else:
            # DDS not available or non-Linux platform - use advanced (8/10)
            return 'advanced'
    except ImportError:
        # DDS library not installed - use advanced (8/10)
        return 'advanced'

DEFAULT_AI_DIFFICULTY = _get_smart_default_ai()


@dataclass
class SessionState:
    """
    Per-session state container

    Replaces global variables:
    - current_deal -> state.deal
    - current_vulnerability -> state.vulnerability
    - current_play_state -> state.play_state
    - current_session -> state.game_session
    - current_ai_difficulty -> state.ai_difficulty
    - current_hand_start_time -> state.hand_start_time
    """
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)

    # Game state
    deal: Dict[str, Any] = field(default_factory=lambda: {
        'North': None, 'East': None, 'South': None, 'West': None
    })
    original_deal: Optional[Dict[str, Any]] = None  # Preserved copy before play begins
    vulnerability: str = "None"
    play_state: Optional[PlayState] = None
    game_session: Optional[GameSession] = None
    ai_difficulty: str = field(default_factory=lambda: DEFAULT_AI_DIFFICULTY)
    hand_start_time: Optional[datetime] = None

    # Bidding state — backend is source of truth for whose turn it is
    dealer: str = 'North'
    auction_history: list = field(default_factory=list)  # List of bid strings

    def touch(self):
        """Update last accessed time"""
        self.last_accessed = datetime.now()

    def reset_hand(self):
        """Reset hand-specific state"""
        self.deal = {'North': None, 'East': None, 'South': None, 'West': None}
        self.original_deal = None
        self.play_state = None
        self.hand_start_time = None
        self.auction_history = []

    def to_dict(self) -> dict:
        """Serialize state for debugging"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'vulnerability': self.vulnerability,
            'ai_difficulty': self.ai_difficulty,
            'has_deal': any(self.deal.values()),
            'has_play_state': self.play_state is not None,
            'has_game_session': self.game_session is not None,
        }


class SessionStateManager:
    """
    Thread-safe manager for per-session state

    Provides isolated state for each user session to prevent
    race conditions and data leakage between concurrent requests.
    """

    def __init__(self):
        self._states: Dict[str, SessionState] = {}
        self._lock = threading.RLock()
        self._cleanup_threshold = 1000  # Clean up when we hit this many sessions

    def get_or_create(self, session_id: str) -> SessionState:
        """
        Get existing state or create new one for session

        Args:
            session_id: Unique session identifier

        Returns:
            SessionState instance for this session
        """
        with self._lock:
            if session_id not in self._states:
                self._states[session_id] = SessionState(session_id=session_id)

                # Periodic cleanup
                if len(self._states) > self._cleanup_threshold:
                    self._cleanup_old_sessions()

            state = self._states[session_id]
            state.touch()
            return state

    def get(self, session_id: str) -> Optional[SessionState]:
        """Get state if it exists, otherwise None"""
        with self._lock:
            state = self._states.get(session_id)
            if state:
                state.touch()
            return state

    def delete(self, session_id: str):
        """Remove state for session"""
        with self._lock:
            self._states.pop(session_id, None)

    def exists(self, session_id: str) -> bool:
        """Check if session state exists"""
        with self._lock:
            return session_id in self._states

    def get_session_count(self) -> int:
        """Get number of active sessions"""
        with self._lock:
            return len(self._states)

    def _cleanup_old_sessions(self):
        """
        Remove sessions not accessed in 24 hours

        Called automatically when session count exceeds threshold.
        """
        cutoff = datetime.now()
        cutoff = cutoff.replace(hour=cutoff.hour - 24)  # 24 hours ago

        to_remove = [
            sid for sid, state in self._states.items()
            if state.last_accessed < cutoff
        ]

        for sid in to_remove:
            del self._states[sid]

        if to_remove:
            print(f"🧹 Cleaned up {len(to_remove)} old sessions")

    def cleanup_inactive(self, hours: int = 24):
        """
        Manually trigger cleanup of inactive sessions

        Args:
            hours: Remove sessions inactive for this many hours
        """
        with self._lock:
            cutoff = datetime.now()
            cutoff = cutoff.replace(hour=max(0, cutoff.hour - hours))

            to_remove = [
                sid for sid, state in self._states.items()
                if state.last_accessed < cutoff
            ]

            for sid in to_remove:
                del self._states[sid]

            return len(to_remove)

    def get_all_session_info(self) -> list:
        """Get info about all sessions (for debugging/monitoring)"""
        with self._lock:
            return [state.to_dict() for state in self._states.values()]


# Helper function to extract session ID from request
def get_session_id_from_request(request) -> Optional[str]:
    """
    Extract session ID from request

    Checks in order:
    1. X-Session-ID header
    2. session_id in JSON body
    3. session_id query parameter

    Args:
        request: Flask request object

    Returns:
        Session ID string or None
    """
    # Check header first (preferred)
    session_id = request.headers.get('X-Session-ID')
    if session_id:
        return session_id

    # Check JSON body
    if request.is_json:
        data = request.get_json(silent=True)
        if data and 'session_id' in data:
            return data['session_id']

    # Check query parameter
    session_id = request.args.get('session_id')
    if session_id:
        return session_id

    return None


# Decorator for endpoints that require session state
def require_session_state(f):
    """
    Decorator to inject session state into endpoint

    Usage:
        @app.route('/api/endpoint')
        @require_session_state
        def my_endpoint(state):
            state.deal = {...}
            return jsonify({'success': True})

    The state parameter is automatically injected based on the
    session ID in the request (header, body, or query param).
    """
    from functools import wraps
    from flask import jsonify

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, current_app

        # Get session ID from request
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'error': 'No session ID provided',
                'help': 'Include X-Session-ID header or session_id in request'
            }), 400

        # Get or create state
        state_manager = current_app.config.get('STATE_MANAGER')
        if not state_manager:
            return jsonify({'error': 'State manager not initialized'}), 500

        state = state_manager.get_or_create(session_id)

        # Inject state into function
        return f(*args, state=state, **kwargs)

    return decorated_function
