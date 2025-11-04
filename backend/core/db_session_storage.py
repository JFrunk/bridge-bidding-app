"""
Database Session Storage
========================

Provides persistent storage for play session state using PostgreSQL or SQLite.

This module works alongside the in-memory SessionStateManager to provide:
1. Session state persistence across server restarts
2. Automatic recovery when in-memory state is lost
3. Session expiration and cleanup

Architecture:
- Primary: In-memory dict (fast, but lost on restart)
- Fallback: Database table (slower, but survives restarts)
- On every card play: Save to both memory and database
- On session load: Try memory first, fall back to database

Database Table: active_play_states
- session_id (PK)
- play_state_json (JSONB/TEXT) - Complete serialized PlayState
- Quick access fields (contract_string, declarer, tricks_taken, etc.)
- Timestamps (created_at, last_updated, expires_at)
- Status (is_complete)
"""

from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from core.database_adapter import get_adapter
from core.play_state_serializer import PlayStateSerializer
import json


class DBSessionStorage:
    """
    Database-backed session state storage.

    Provides:
    - save_session(session_id, play_state): Persist session to database
    - load_session(session_id): Restore session from database
    - delete_session(session_id): Remove session from database
    - cleanup_expired(): Remove old/completed sessions
    - list_active_sessions(user_id): Get all active sessions for user
    """

    def __init__(self):
        self.db = get_adapter()
        self.serializer = PlayStateSerializer()

        # Ensure tables exist
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create active_play_states table if it doesn't exist."""
        if not self.db.table_exists('active_play_states'):
            print("[DBSessionStorage] Creating active_play_states table...")
            self.db.create_tables_if_needed()

    def save_session(
        self,
        session_id: str,
        play_state,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Save play session state to database.

        Args:
            session_id: Unique session identifier
            play_state: PlayState object to save
            user_id: Optional user ID for multi-user tracking

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Serialize PlayState to JSON
            play_state_json = self.serializer.serialize(play_state)

            # Extract quick access fields
            quick_fields = self.serializer.extract_quick_access_fields(play_state)

            # Check if session already exists
            existing = self.db.execute_query(
                "SELECT session_id FROM active_play_states WHERE session_id = ?",
                (session_id,),
                fetch='one'
            )

            if existing:
                # Update existing session
                query = """
                    UPDATE active_play_states
                    SET play_state_json = ?,
                        contract_string = ?,
                        declarer = ?,
                        dummy = ?,
                        next_to_play = ?,
                        tricks_taken_ns = ?,
                        tricks_taken_ew = ?,
                        vulnerability = ?,
                        ai_difficulty = ?,
                        dealer = ?,
                        is_complete = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """

                self.db.execute_update(query, (
                    self.db.serialize_json(play_state_json),
                    quick_fields['contract_string'],
                    quick_fields['declarer'],
                    quick_fields['dummy'],
                    quick_fields['next_to_play'],
                    quick_fields['tricks_taken_ns'],
                    quick_fields['tricks_taken_ew'],
                    quick_fields['vulnerability'],
                    quick_fields['ai_difficulty'],
                    quick_fields['dealer'],
                    quick_fields['is_complete'],
                    session_id
                ))
            else:
                # Insert new session
                query = """
                    INSERT INTO active_play_states (
                        session_id, user_id, play_state_json,
                        contract_string, declarer, dummy, next_to_play,
                        tricks_taken_ns, tricks_taken_ew,
                        vulnerability, ai_difficulty, dealer, is_complete
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                self.db.execute_insert(query, (
                    session_id,
                    user_id,
                    self.db.serialize_json(play_state_json),
                    quick_fields['contract_string'],
                    quick_fields['declarer'],
                    quick_fields['dummy'],
                    quick_fields['next_to_play'],
                    quick_fields['tricks_taken_ns'],
                    quick_fields['tricks_taken_ew'],
                    quick_fields['vulnerability'],
                    quick_fields['ai_difficulty'],
                    quick_fields['dealer'],
                    quick_fields['is_complete']
                ))

            return True

        except Exception as e:
            print(f"[DBSessionStorage] Error saving session {session_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_session(self, session_id: str):
        """
        Load play session state from database.

        Args:
            session_id: Session identifier to load

        Returns:
            PlayState object if found and valid, None otherwise
        """
        try:
            query = """
                SELECT play_state_json, is_complete, expires_at
                FROM active_play_states
                WHERE session_id = ?
            """

            result = self.db.execute_query(query, (session_id,), fetch='one')

            if not result:
                print(f"[DBSessionStorage] Session {session_id} not found in database")
                return None

            # Check expiration
            expires_at = result.get('expires_at')
            if expires_at:
                # Handle both datetime objects and strings
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))

                if datetime.now() > expires_at:
                    print(f"[DBSessionStorage] Session {session_id} expired at {expires_at}")
                    self.delete_session(session_id)
                    return None

            # Deserialize PlayState
            play_state_json = self.db.deserialize_json(result['play_state_json'])
            play_state = self.serializer.deserialize(play_state_json)

            print(f"[DBSessionStorage] Loaded session {session_id} from database")
            return play_state

        except Exception as e:
            print(f"[DBSessionStorage] Error loading session {session_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from database.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            query = "DELETE FROM active_play_states WHERE session_id = ?"
            rows_affected = self.db.execute_update(query, (session_id,))
            return rows_affected > 0

        except Exception as e:
            print(f"[DBSessionStorage] Error deleting session {session_id}: {e}")
            return False

    def cleanup_expired(self) -> int:
        """
        Remove expired and completed sessions from database.

        Removes:
        - Sessions past expires_at timestamp
        - Completed sessions older than 1 hour

        Returns:
            Number of sessions deleted
        """
        try:
            # Different SQL for SQLite vs PostgreSQL
            if self.db.db_type == 'postgresql':
                query = """
                    DELETE FROM active_play_states
                    WHERE expires_at < CURRENT_TIMESTAMP
                    OR (is_complete = TRUE AND last_updated < CURRENT_TIMESTAMP - INTERVAL '1 hour')
                """
            else:
                query = """
                    DELETE FROM active_play_states
                    WHERE expires_at < datetime('now')
                    OR (is_complete = 1 AND last_updated < datetime('now', '-1 hour'))
                """

            rows_deleted = self.db.execute_update(query)
            if rows_deleted > 0:
                print(f"[DBSessionStorage] Cleaned up {rows_deleted} expired sessions")
            return rows_deleted

        except Exception as e:
            print(f"[DBSessionStorage] Error during cleanup: {e}")
            return 0

    def list_active_sessions(self, user_id: Optional[int] = None) -> list:
        """
        List all active (non-expired, non-completed) sessions.

        Args:
            user_id: Optional filter by user_id

        Returns:
            List of session info dicts
        """
        try:
            if user_id:
                query = """
                    SELECT session_id, contract_string, created_at, last_updated,
                           tricks_taken_ns, tricks_taken_ew, is_complete
                    FROM active_play_states
                    WHERE user_id = ? AND is_complete = ? AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY last_updated DESC
                """
                params = (user_id, False)
            else:
                query = """
                    SELECT session_id, contract_string, created_at, last_updated,
                           tricks_taken_ns, tricks_taken_ew, is_complete
                    FROM active_play_states
                    WHERE is_complete = ? AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY last_updated DESC
                """
                params = (False,)

            # Convert SQLite boolean parameter
            if self.db.db_type == 'sqlite':
                params = tuple(0 if p is False else 1 if p is True else p for p in params)

            # Adjust query for SQLite datetime comparison
            if self.db.db_type == 'sqlite':
                query = query.replace("CURRENT_TIMESTAMP", "datetime('now')")

            results = self.db.execute_query(query, params, fetch='all')
            return results if results else []

        except Exception as e:
            print(f"[DBSessionStorage] Error listing sessions: {e}")
            return []

    def extend_expiration(self, session_id: str, hours: int = 24) -> bool:
        """
        Extend the expiration time for a session.

        Useful when user is actively playing to prevent timeout.

        Args:
            session_id: Session to extend
            hours: Number of hours to extend from now

        Returns:
            True if updated successfully
        """
        try:
            if self.db.db_type == 'postgresql':
                query = """
                    UPDATE active_play_states
                    SET expires_at = CURRENT_TIMESTAMP + INTERVAL '%s hours'
                    WHERE session_id = ?
                """
                query = query.replace('%s', str(hours))
            else:
                query = f"""
                    UPDATE active_play_states
                    SET expires_at = datetime('now', '+{hours} hours')
                    WHERE session_id = ?
                """

            rows_affected = self.db.execute_update(query, (session_id,))
            return rows_affected > 0

        except Exception as e:
            print(f"[DBSessionStorage] Error extending expiration for {session_id}: {e}")
            return False


# Global storage instance
_storage = None

def get_db_storage() -> DBSessionStorage:
    """Get or create the global DBSessionStorage instance."""
    global _storage
    if _storage is None:
        _storage = DBSessionStorage()
    return _storage
