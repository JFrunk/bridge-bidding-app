"""
Google OAuth API — Sign in with Google.

Per AUTH_PRD §3.2:
- POST /api/auth/v2/google — exchange Google ID token for JWT session

Uses Google Identity Services (One Tap / Sign In With Google button).
The frontend sends the ID token; we verify it server-side.
"""

import os
from datetime import datetime, timezone

from flask import request, jsonify, make_response

from auth.jwt_service import JWTService
from auth.token_api import (
    _store_refresh_token,
    _set_refresh_cookie,
    _revoke_all_user_tokens,
)
from utils.error_logger import log_error

_jwt_svc = JWTService()

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')


def _get_user_manager():
    """Lazy import to avoid module-level DATABASE_URL dependency."""
    from engine.learning.user_manager import get_user_manager
    return get_user_manager()


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


def _add_auth_provider(user_id, provider, provider_id=None):
    """Record a linked auth provider for a user."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO auth_providers (user_id, provider, provider_id)
                   VALUES (%s, %s, %s)""",
                (user_id, provider, provider_id),
            )
        except Exception as e:
            if 'duplicate' not in str(e).lower():
                raise


def _set_email_verified(user_id):
    """Mark user's email as verified."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET email_verified = true WHERE id = %s",
            (user_id,),
        )


def _update_profile_picture(user_id, picture_url):
    """Store Google profile picture URL."""
    if not picture_url:
        return
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET profile_picture_url = %s WHERE id = %s",
            (picture_url, user_id),
        )


def _verify_google_token(id_token):
    """
    Verify a Google ID token and return the payload.

    Returns dict with: sub, email, email_verified, name, picture
    or None if verification fails.
    """
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        payload = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )

        # Verify issuer
        if payload.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
            return None

        return payload

    except Exception as e:
        log_error(e, context={'action': 'verify_google_token'})
        return None


def _migrate_guest_data(new_user_id, guest_id):
    """Migrate guest data to registered user (same as auth_api.py)."""
    from db import get_connection
    if not guest_id or not isinstance(guest_id, int) or guest_id >= 0:
        return {}

    migrated = {}
    with get_connection() as conn:
        cursor = conn.cursor()
        for table in ['game_sessions', 'bidding_decisions', 'hand_analyses']:
            cursor.execute(
                f'UPDATE {table} SET user_id = %s WHERE user_id = %s',
                (new_user_id, guest_id),
            )
            if cursor.rowcount:
                migrated[table] = cursor.rowcount

        for table in [
            'user_convention_progress', 'user_skill_progress',
            'skill_practice_history', 'convention_practice_history',
            'user_play_progress', 'play_practice_history',
            'practice_history', 'practice_sessions',
            'user_settings', 'user_gamification',
        ]:
            try:
                cursor.execute(
                    f'UPDATE {table} SET user_id = %s WHERE user_id = %s',
                    (new_user_id, guest_id),
                )
                if cursor.rowcount:
                    migrated[table] = cursor.rowcount
            except Exception:
                pass

    return migrated


def _issue_tokens_response(user_id, status_code=200, extra_data=None):
    """Create response with JWT access token + refresh cookie."""
    access_token = _jwt_svc.create_access_token(user_id=user_id)
    raw_refresh, refresh_hash = _jwt_svc.create_refresh_token()
    refresh_expiry = _jwt_svc.get_refresh_expiry()
    _store_refresh_token(user_id, refresh_hash, refresh_expiry)

    # Include user profile so frontend can display identity
    try:
        profile = _get_user_manager().get_user(user_id)
    except Exception:
        profile = None

    body = {
        'access_token': access_token,
        'user_id': user_id,
        'email': (profile.email or '') if profile else '',
        'display_name': (profile.display_name or '') if profile else '',
    }
    if extra_data:
        body.update(extra_data)

    response = make_response(jsonify(body))
    response.status_code = status_code
    _set_refresh_cookie(response, raw_refresh, refresh_expiry)
    return response


# ─── Endpoint ─────────────────────────────────────────────────


def google_auth():
    """
    POST /api/auth/v2/google

    Body: {"id_token": "...", "guest_id": -123456  (optional)}

    Verifies Google ID token, creates or links account, issues JWT.
    """
    if not GOOGLE_CLIENT_ID:
        return jsonify({'error': 'Google sign-in is not configured'}), 503

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    id_token_str = data.get('id_token', '')
    guest_id = data.get('guest_id')

    if not id_token_str:
        return jsonify({'error': 'Google ID token required'}), 400

    try:
        # Verify the Google token
        payload = _verify_google_token(id_token_str)
        if not payload:
            return jsonify({'error': 'Invalid Google token'}), 401

        google_email = payload.get('email', '').lower()
        google_name = payload.get('name', '')
        google_picture = payload.get('picture', '')
        google_sub = payload.get('sub', '')  # Google's user ID

        if not google_email:
            return jsonify({'error': 'Google account has no email'}), 400

        user = _get_user_by_email(google_email)
        user_manager = _get_user_manager()

        if user:
            # Existing account — check if we can link Google
            if not user.get('email_verified'):
                # PRD §3.2: prevent squatter attack
                return jsonify({
                    'error': 'An account exists with this email but is not verified. '
                             'Please verify your email first, then link Google sign-in.',
                }), 403

            user_id = user['id']

            # Link Google provider if not already linked
            _add_auth_provider(user_id, 'google', google_sub)

            # Update profile picture from Google
            _update_profile_picture(user_id, google_picture)

            # Update login timestamp
            user_manager.update_last_login(user_id)

            return _issue_tokens_response(user_id, extra_data={'auth_provider': 'google'})

        else:
            # New account — create with Google-verified email
            username = google_email.split('@')[0]
            counter = 1
            original = username
            while user_manager.user_exists(username):
                username = f"{original}{counter}"
                counter += 1

            user_id = user_manager.create_user(
                username=username,
                email=google_email,
                display_name=google_name or username.title(),
            )

            # Google emails are pre-verified
            _set_email_verified(user_id)
            _add_auth_provider(user_id, 'google', google_sub)
            _update_profile_picture(user_id, google_picture)

            # Migrate guest data if provided
            migrated = {}
            if guest_id:
                migrated = _migrate_guest_data(user_id, guest_id)

            user_manager.update_last_login(user_id)

            extra = {
                'is_new_user': True,
                'email_verified': True,
                'auth_provider': 'google',
            }
            if migrated:
                extra['migrated_from_guest'] = True
                extra['migrated_data'] = migrated

            return _issue_tokens_response(user_id, status_code=201, extra_data=extra)

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/google')
        return jsonify({'error': 'Google sign-in failed'}), 500


def register_google_auth_endpoints(app):
    """Register Google OAuth endpoints with Flask app."""
    if GOOGLE_CLIENT_ID:
        app.route('/api/auth/v2/google', methods=['POST'])(google_auth)
        print("✓ Google OAuth endpoint registered")
    else:
        # Still register the endpoint so it returns a helpful error
        app.route('/api/auth/v2/google', methods=['POST'])(google_auth)
        print("⚠ Google OAuth endpoint registered (GOOGLE_CLIENT_ID not set — will return 503)")
