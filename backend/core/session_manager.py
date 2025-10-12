"""
SessionManager - Shared session management for bidding and play modules.

Provides session-based state management to replace global variables,
eliminating state conflicts between bidding and play sessions.
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import threading


class SessionManager:
    """
    Manage active sessions across all modules.

    Features:
    - Session-based state (no global variables)
    - Automatic cleanup of expired sessions
    - Thread-safe operations
    - Support for user identification (future)

    Usage:
        manager = SessionManager()
        session_id = manager.create_session('bidding')
        manager.update_session(session_id, {'deal': {...}})
        data = manager.get_session(session_id)
    """

    def __init__(self, session_timeout_hours: int = 24):
        """
        Initialize session manager.

        Args:
            session_timeout_hours: Hours before inactive sessions expire
        """
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self._lock = threading.Lock()  # Thread safety

    def create_session(
        self,
        session_type: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Create a new session.

        Args:
            session_type: 'bidding', 'play', or 'game'
            user_id: Optional user identifier (for future use)

        Returns:
            session_id: Unique session identifier
        """
        with self._lock:
            # Generate unique session ID
            session_id = f"{session_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            self.sessions[session_id] = {
                'type': session_type,
                'user_id': user_id,
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'data': None  # Module-specific data stored here
            }

            return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data and update last_accessed timestamp.

        Args:
            session_id: Session identifier

        Returns:
            Session dict or None if not found
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session['last_accessed'] = datetime.now()
            return session

    def update_session(self, session_id: str, data: Any) -> bool:
        """
        Update session data.

        Args:
            session_id: Session identifier
            data: Data to store in session

        Returns:
            True if successful, False if session not found
        """
        with self._lock:
            if session_id not in self.sessions:
                return False

            self.sessions[session_id]['data'] = data
            self.sessions[session_id]['last_accessed'] = datetime.now()
            return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove sessions older than timeout.

        Returns:
            Number of sessions cleaned up
        """
        with self._lock:
            now = datetime.now()
            expired = [
                sid for sid, sess in self.sessions.items()
                if now - sess['last_accessed'] > self.session_timeout
            ]

            for sid in expired:
                del self.sessions[sid]

            return len(expired)

    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        with self._lock:
            return len(self.sessions)

    def get_sessions_by_type(self, session_type: str) -> list:
        """
        Get all sessions of a specific type.

        Args:
            session_type: 'bidding', 'play', or 'game'

        Returns:
            List of session IDs
        """
        with self._lock:
            return [
                sid for sid, sess in self.sessions.items()
                if sess['type'] == session_type
            ]

    def get_sessions_by_user(self, user_id: str) -> list:
        """
        Get all sessions for a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of session IDs
        """
        with self._lock:
            return [
                sid for sid, sess in self.sessions.items()
                if sess['user_id'] == user_id
            ]


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance (singleton pattern).

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
