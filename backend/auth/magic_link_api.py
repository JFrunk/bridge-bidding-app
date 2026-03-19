"""
Magic Link API — Passwordless login via email.

Per AUTH_PRD §3.3:
- POST /api/auth/v2/magic-link/request — send magic link email
- POST /api/auth/v2/magic-link/verify — validate token, issue JWT

Tokens are stored as SHA-256 hashes in the auth_tokens table.
The raw token is sent via email only.
"""

from datetime import datetime, timedelta, timezone

from flask import request, jsonify

from auth.auth_service import AuthService
from auth.jwt_service import JWTService
from auth.token_store import (
    store_auth_token,
    lookup_auth_token,
    consume_auth_token,
    invalidate_tokens_for_user,
)
from auth.email_templates import magic_link_email
from auth.token_api import _store_refresh_token, _set_refresh_cookie
from utils.error_logger import log_error

_auth_svc = AuthService()
_jwt_svc = JWTService()

MAGIC_LINK_EXPIRY_MINUTES = 15


def _get_email_service():
    """Lazy import to avoid module-level dependency."""
    from engine.notifications.email_service import get_email_service
    return get_email_service()


def _get_user_by_email(email):
    """Fetch user row by email. Returns dict or None."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,),
        )
        return cursor.fetchone()


def _get_user_manager():
    """Lazy import for UserManager."""
    from engine.learning.user_manager import get_user_manager
    return get_user_manager()


def _issue_tokens_response(user_id, status_code=200, extra_data=None):
    """Create response with JWT access token + refresh cookie."""
    from flask import make_response

    access_token = _jwt_svc.create_access_token(user_id=user_id)
    raw_refresh, refresh_hash = _jwt_svc.create_refresh_token()
    refresh_expiry = _jwt_svc.get_refresh_expiry()
    _store_refresh_token(user_id, refresh_hash, refresh_expiry)

    body = {
        'access_token': access_token,
        'user_id': user_id,
    }
    if extra_data:
        body.update(extra_data)

    response = make_response(jsonify(body))
    response.status_code = status_code
    _set_refresh_cookie(response, raw_refresh, refresh_expiry)
    return response


# ─── Endpoints ────────────────────────────────────────────────


def magic_link_request():
    """
    POST /api/auth/v2/magic-link/request

    Body: {"email": "user@example.com"}

    Always returns 200 with generic message (no enumeration).
    If email exists, sends a magic link. If not, does nothing.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = (data.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email address required'}), 400

    # Always return success (no enumeration)
    success_msg = {'message': 'If an account exists, a login link has been sent.'}

    try:
        user = _get_user_by_email(email)
        if not user:
            return jsonify(success_msg), 200

        user_id = user['id']

        # Invalidate any existing magic link tokens for this user
        invalidate_tokens_for_user(user_id, 'magic_link')

        # Generate and store token
        raw_token = _auth_svc.generate_token()
        token_hash = _auth_svc.hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRY_MINUTES)

        metadata = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')[:200],
        }
        store_auth_token(user_id, token_hash, 'magic_link', expires_at, metadata)

        # Send email
        svc = _get_email_service()
        app_url = svc.get_app_url()
        email_data = magic_link_email(app_url, raw_token)
        svc.send_email(email, email_data['subject'], email_data['html'], email_data['text'])

        return jsonify(success_msg), 200

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/magic-link/request')
        # Still return success to avoid leaking info
        return jsonify(success_msg), 200


def magic_link_verify():
    """
    POST /api/auth/v2/magic-link/verify

    Body: {"token": "raw_token_from_email"}

    Validates the token, marks it used, issues JWT.
    Returns 200 with access_token on success, 401 on failure.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    raw_token = data.get('token', '')
    if not raw_token:
        return jsonify({'error': 'Token required'}), 400

    try:
        token_hash = _auth_svc.hash_token(raw_token)
        row = lookup_auth_token(token_hash, 'magic_link')

        if not row:
            return jsonify({'error': 'Invalid or expired link'}), 401

        user_id = row['user_id']

        # Consume the token (single-use)
        consume_auth_token(token_hash)

        # Mark email as verified (magic link proves ownership)
        from db import get_connection
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET email_verified = true WHERE id = %s",
                (user_id,),
            )

        # Add magic_link as auth provider if not already present
        from auth.auth_api import _add_auth_provider
        _add_auth_provider(user_id, 'magic_link')

        # Update login timestamp
        _get_user_manager().update_last_login(user_id)

        return _issue_tokens_response(user_id)

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/magic-link/verify')
        return jsonify({'error': 'Verification failed'}), 500


def register_magic_link_endpoints(app):
    """Register magic link endpoints with Flask app."""
    app.route('/api/auth/v2/magic-link/request', methods=['POST'])(magic_link_request)
    app.route('/api/auth/v2/magic-link/verify', methods=['POST'])(magic_link_verify)
    print("✓ Magic link endpoints registered (request + verify)")
