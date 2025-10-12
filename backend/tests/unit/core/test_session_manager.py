"""
Unit tests for SessionManager.

Tests session creation, retrieval, updates, deletion, and cleanup.
"""

import pytest
from datetime import datetime, timedelta
from core.session_manager import SessionManager


class TestSessionManager:
    """Test SessionManager functionality."""

    def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()
        session_id = manager.create_session('bidding')

        assert session_id is not None
        assert session_id.startswith('bidding_')
        assert manager.get_session_count() == 1

    def test_create_session_with_user(self):
        """Test creating session with user ID."""
        manager = SessionManager()
        session_id = manager.create_session('play', user_id='user123')

        session = manager.get_session(session_id)
        assert session is not None
        assert session['user_id'] == 'user123'
        assert session['type'] == 'play'

    def test_get_session(self):
        """Test retrieving a session."""
        manager = SessionManager()
        session_id = manager.create_session('bidding')

        session = manager.get_session(session_id)
        assert session is not None
        assert session['type'] == 'bidding'
        assert 'created_at' in session
        assert 'last_accessed' in session

    def test_get_nonexistent_session(self):
        """Test retrieving non-existent session returns None."""
        manager = SessionManager()
        session = manager.get_session('nonexistent')
        assert session is None

    def test_update_session(self):
        """Test updating session data."""
        manager = SessionManager()
        session_id = manager.create_session('bidding')

        data = {'deal': {'N': [], 'E': [], 'S': [], 'W': []}}
        result = manager.update_session(session_id, data)

        assert result is True
        session = manager.get_session(session_id)
        assert session['data'] == data

    def test_update_nonexistent_session(self):
        """Test updating non-existent session returns False."""
        manager = SessionManager()
        result = manager.update_session('nonexistent', {'data': 'test'})
        assert result is False

    def test_delete_session(self):
        """Test deleting a session."""
        manager = SessionManager()
        session_id = manager.create_session('bidding')

        assert manager.get_session_count() == 1
        result = manager.delete_session(session_id)

        assert result is True
        assert manager.get_session_count() == 0
        assert manager.get_session(session_id) is None

    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session returns False."""
        manager = SessionManager()
        result = manager.delete_session('nonexistent')
        assert result is False

    def test_multiple_sessions(self):
        """Test managing multiple sessions."""
        manager = SessionManager()

        bid_id = manager.create_session('bidding')
        play_id = manager.create_session('play')
        game_id = manager.create_session('game')

        assert manager.get_session_count() == 3
        assert manager.get_session(bid_id)['type'] == 'bidding'
        assert manager.get_session(play_id)['type'] == 'play'
        assert manager.get_session(game_id)['type'] == 'game'

    def test_get_sessions_by_type(self):
        """Test retrieving sessions by type."""
        manager = SessionManager()

        bid_id1 = manager.create_session('bidding')
        bid_id2 = manager.create_session('bidding')
        play_id = manager.create_session('play')

        bidding_sessions = manager.get_sessions_by_type('bidding')
        play_sessions = manager.get_sessions_by_type('play')

        assert len(bidding_sessions) == 2
        assert bid_id1 in bidding_sessions
        assert bid_id2 in bidding_sessions
        assert len(play_sessions) == 1
        assert play_id in play_sessions

    def test_get_sessions_by_user(self):
        """Test retrieving sessions by user ID."""
        manager = SessionManager()

        user1_bid = manager.create_session('bidding', user_id='user1')
        user1_play = manager.create_session('play', user_id='user1')
        user2_bid = manager.create_session('bidding', user_id='user2')

        user1_sessions = manager.get_sessions_by_user('user1')
        user2_sessions = manager.get_sessions_by_user('user2')

        assert len(user1_sessions) == 2
        assert user1_bid in user1_sessions
        assert user1_play in user1_sessions
        assert len(user2_sessions) == 1
        assert user2_bid in user2_sessions

    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        manager = SessionManager(session_timeout_hours=0)  # Immediate expiry

        session_id = manager.create_session('bidding')
        assert manager.get_session_count() == 1

        # Manually set last_accessed to past
        session = manager.sessions[session_id]
        session['last_accessed'] = datetime.now() - timedelta(hours=1)

        cleaned = manager.cleanup_expired_sessions()
        assert cleaned == 1
        assert manager.get_session_count() == 0

    def test_cleanup_keeps_active_sessions(self):
        """Test cleanup keeps active sessions."""
        manager = SessionManager(session_timeout_hours=24)

        session_id = manager.create_session('bidding')
        assert manager.get_session_count() == 1

        cleaned = manager.cleanup_expired_sessions()
        assert cleaned == 0
        assert manager.get_session_count() == 1

    def test_last_accessed_updates(self):
        """Test that last_accessed updates on get_session."""
        manager = SessionManager()
        session_id = manager.create_session('bidding')

        session1 = manager.get_session(session_id)
        first_access = session1['last_accessed']

        # Small delay
        import time
        time.sleep(0.01)

        session2 = manager.get_session(session_id)
        second_access = session2['last_accessed']

        assert second_access >= first_access

    def test_session_isolation(self):
        """Test that sessions are isolated from each other."""
        manager = SessionManager()

        bid_id = manager.create_session('bidding')
        play_id = manager.create_session('play')

        manager.update_session(bid_id, {'data': 'bidding_data'})
        manager.update_session(play_id, {'data': 'play_data'})

        bid_session = manager.get_session(bid_id)
        play_session = manager.get_session(play_id)

        assert bid_session['data'] == {'data': 'bidding_data'}
        assert play_session['data'] == {'data': 'play_data'}

        # Modifying one shouldn't affect the other
        manager.update_session(bid_id, {'data': 'modified'})

        bid_session = manager.get_session(bid_id)
        play_session = manager.get_session(play_id)

        assert bid_session['data'] == {'data': 'modified'}
        assert play_session['data'] == {'data': 'play_data'}


def test_get_session_manager_singleton():
    """Test singleton pattern for global session manager."""
    from core.session_manager import get_session_manager

    manager1 = get_session_manager()
    manager2 = get_session_manager()

    assert manager1 is manager2

    # Test that state is shared
    session_id = manager1.create_session('bidding')
    assert manager2.get_session(session_id) is not None
