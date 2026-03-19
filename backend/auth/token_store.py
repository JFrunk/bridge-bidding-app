"""
Auth Token Store — CRUD for the auth_tokens table.

Handles email verification, magic link, and password reset tokens.
All tokens are stored as SHA-256 hashes; raw tokens are never persisted.
"""

import json
from datetime import datetime, timezone


def store_auth_token(user_id, token_hash, token_type, expires_at, metadata=None):
    """Insert a new auth token hash into the database."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO auth_tokens (user_id, token_hash, token_type, expires_at, metadata)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, token_hash, token_type, expires_at,
             json.dumps(metadata) if metadata else None),
        )


def lookup_auth_token(token_hash, token_type):
    """
    Find a valid (not expired, not used) auth token.

    Returns dict with id, user_id, expires_at or None.
    """
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, user_id, expires_at
               FROM auth_tokens
               WHERE token_hash = %s
                 AND token_type = %s
                 AND used_at IS NULL
                 AND expires_at > %s""",
            (token_hash, token_type, datetime.now(timezone.utc)),
        )
        return cursor.fetchone()


def consume_auth_token(token_hash):
    """Mark a token as used (single-use enforcement)."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE auth_tokens
               SET used_at = %s
               WHERE token_hash = %s AND used_at IS NULL""",
            (datetime.now(timezone.utc), token_hash),
        )


def invalidate_tokens_for_user(user_id, token_type):
    """
    Mark all outstanding tokens of a given type as used for a user.

    Called before issuing a new token so only the latest is valid.
    """
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE auth_tokens
               SET used_at = %s
               WHERE user_id = %s AND token_type = %s AND used_at IS NULL""",
            (datetime.now(timezone.utc), user_id, token_type),
        )
