"""
Token API — JWT refresh token rotation endpoint.

Per AUTH_PRD §3.1:
- POST /api/auth/refresh: exchange valid refresh token for new access + refresh tokens
- POST /api/auth/logout: revoke refresh token

Refresh tokens are stored as SHA-256 hashes in the refresh_tokens table.
The raw token lives only in an HttpOnly secure cookie.
"""

from datetime import datetime, timezone

from flask import request, jsonify, make_response

from auth.jwt_service import JWTService

_jwt_svc = JWTService()

# Cookie settings per PRD §10 (Security Requirements)
REFRESH_COOKIE_NAME = 'refresh_token'
REFRESH_COOKIE_PATH = '/api/auth'
REFRESH_COOKIE_SAMESITE = 'Strict'


def _set_refresh_cookie(response, raw_token, expires):
    """Set the refresh token as an HttpOnly secure cookie."""
    is_production = request.host and 'localhost' not in request.host
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        raw_token,
        httponly=True,
        secure=is_production,
        samesite=REFRESH_COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
        expires=expires,
    )


def _clear_refresh_cookie(response):
    """Clear the refresh token cookie."""
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        '',
        httponly=True,
        secure=True,
        samesite=REFRESH_COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
        max_age=0,
    )


def _store_refresh_token(user_id, token_hash, expires_at):
    """Insert a new refresh token hash into the database."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
               VALUES (%s, %s, %s)""",
            (user_id, token_hash, expires_at),
        )


def _lookup_refresh_token(token_hash):
    """Find a valid (not expired, not revoked) refresh token row."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, user_id, expires_at
               FROM refresh_tokens
               WHERE token_hash = %s
                 AND revoked_at IS NULL
                 AND expires_at > %s""",
            (token_hash, datetime.now(timezone.utc)),
        )
        return cursor.fetchone()


def _revoke_refresh_token(token_hash):
    """Mark a single refresh token as revoked."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE refresh_tokens
               SET revoked_at = %s
               WHERE token_hash = %s AND revoked_at IS NULL""",
            (datetime.now(timezone.utc), token_hash),
        )


def _revoke_all_user_tokens(user_id):
    """Revoke every refresh token for a user (e.g. password reset)."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE refresh_tokens
               SET revoked_at = %s
               WHERE user_id = %s AND revoked_at IS NULL""",
            (datetime.now(timezone.utc), user_id),
        )


def refresh_access_token():
    """
    POST /api/auth/refresh

    Reads refresh token from HttpOnly cookie, validates it, then:
    1. Revokes the old refresh token (rotation).
    2. Issues a new access token + new refresh token.
    3. Sets the new refresh token cookie.

    Returns 401 if cookie is missing, token is invalid/expired/revoked.
    """
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        return jsonify({'error': 'No refresh token'}), 401

    token_hash = _jwt_svc.hash_refresh_token(raw_token)
    row = _lookup_refresh_token(token_hash)

    if not row:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401

    user_id = row['user_id']

    # Rotate: revoke old, issue new
    _revoke_refresh_token(token_hash)

    new_raw, new_hash = _jwt_svc.create_refresh_token()
    new_expiry = _jwt_svc.get_refresh_expiry()
    _store_refresh_token(user_id, new_hash, new_expiry)

    access_token = _jwt_svc.create_access_token(user_id=user_id)

    response = make_response(jsonify({
        'access_token': access_token,
        'user_id': user_id,
    }))
    _set_refresh_cookie(response, new_raw, new_expiry)
    return response


def logout_v2():
    """
    POST /api/auth/logout-v2

    Revokes the refresh token from the cookie and clears the cookie.
    Temporary name to avoid collision with existing /api/auth/logout.
    Will be renamed to /api/auth/logout once simple-login is deprecated.
    """
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        token_hash = _jwt_svc.hash_refresh_token(raw_token)
        _revoke_refresh_token(token_hash)

    response = make_response(jsonify({'success': True}))
    _clear_refresh_cookie(response)
    return response


def register_token_endpoints(app):
    """Register JWT token management endpoints with Flask app."""
    app.route('/api/auth/refresh', methods=['POST'])(refresh_access_token)
    app.route('/api/auth/logout-v2', methods=['POST'])(logout_v2)
    print("✓ Token API endpoints registered (JWT refresh + logout)")
