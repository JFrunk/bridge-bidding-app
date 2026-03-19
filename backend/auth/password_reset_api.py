"""
Password Reset API — Forgot password and reset flows.

Per AUTH_PRD §3.5:
- POST /api/auth/v2/forgot-password — send reset email (no enumeration)
- POST /api/auth/v2/reset-password — validate token + set new password

Reset tokens are stored as SHA-256 hashes in the auth_tokens table.
"""

from datetime import datetime, timedelta, timezone

from flask import request, jsonify

from auth.auth_service import (
    AuthService,
    PasswordTooShortError,
    PasswordTooCommonError,
    PasswordMissingLetterError,
    PasswordMissingDigitError,
)
from auth.token_store import (
    store_auth_token,
    lookup_auth_token,
    consume_auth_token,
    invalidate_tokens_for_user,
)
from auth.email_templates import password_reset_email, password_changed_email
from auth.token_api import _revoke_all_user_tokens
from utils.error_logger import log_error

_auth_svc = AuthService()

PASSWORD_RESET_EXPIRY_HOURS = 1


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


def _set_password_hash(user_id, password_hash):
    """Set the password_hash column on a user record."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user_id),
        )


# ─── Endpoints ────────────────────────────────────────────────


def forgot_password():
    """
    POST /api/auth/v2/forgot-password

    Body: {"email": "user@example.com"}

    Always returns 200 with generic message (no enumeration).
    Only sends reset email if account exists and email is verified.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = (data.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email address required'}), 400

    success_msg = {'message': 'If an account exists with that email, a reset link has been sent.'}

    try:
        user = _get_user_by_email(email)
        if not user:
            return jsonify(success_msg), 200

        # Only allow reset for verified emails (PRD §3.5)
        if not user.get('email_verified'):
            return jsonify(success_msg), 200

        user_id = user['id']

        # Invalidate any existing reset tokens
        invalidate_tokens_for_user(user_id, 'password_reset')

        # Generate and store token
        raw_token = _auth_svc.generate_token()
        token_hash = _auth_svc.hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)

        metadata = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')[:200],
        }
        store_auth_token(user_id, token_hash, 'password_reset', expires_at, metadata)

        # Send email
        svc = _get_email_service()
        app_url = svc.get_app_url()
        email_data = password_reset_email(app_url, raw_token)
        svc.send_email(email, email_data['subject'], email_data['html'], email_data['text'])

        return jsonify(success_msg), 200

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/forgot-password')
        return jsonify(success_msg), 200


def reset_password():
    """
    POST /api/auth/v2/reset-password

    Body: {"token": "raw_token", "password": "NewSecure1"}

    Validates the reset token, sets the new password, revokes all
    refresh tokens (force re-login on all devices).
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    raw_token = data.get('token', '')
    new_password = data.get('password', '')

    if not raw_token:
        return jsonify({'error': 'Token required'}), 400

    if not new_password:
        return jsonify({'error': 'New password required'}), 400

    # Validate password strength
    try:
        _auth_svc.validate_password(new_password)
    except (PasswordTooShortError, PasswordMissingLetterError,
            PasswordMissingDigitError, PasswordTooCommonError) as e:
        return jsonify({'error': str(e)}), 400

    try:
        token_hash = _auth_svc.hash_token(raw_token)
        row = lookup_auth_token(token_hash, 'password_reset')

        if not row:
            return jsonify({'error': 'Invalid or expired reset link'}), 401

        user_id = row['user_id']

        # Check new password isn't the same as current
        user = _get_user_by_email_or_id(user_id)
        if user and user.get('password_hash'):
            if _auth_svc.verify_password(new_password, user['password_hash']):
                return jsonify({'error': 'New password must be different from your current password'}), 400

        # Consume the token
        consume_auth_token(token_hash)

        # Set new password
        new_hash = _auth_svc.hash_password(new_password)
        _set_password_hash(user_id, new_hash)

        # Revoke all refresh tokens (force re-login everywhere)
        _revoke_all_user_tokens(user_id)

        # Send password changed notification
        if user and user.get('email'):
            try:
                svc = _get_email_service()
                email_data = password_changed_email()
                svc.send_email(user['email'], email_data['subject'],
                               email_data['html'], email_data['text'])
            except Exception:
                pass  # Notification failure shouldn't block reset

        return jsonify({'message': 'Password reset successfully. Please log in with your new password.'}), 200

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/reset-password')
        return jsonify({'error': 'Password reset failed'}), 500


def _get_user_by_email_or_id(user_id):
    """Fetch user row by ID. Returns dict or None."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()


def register_password_reset_endpoints(app):
    """Register password reset endpoints with Flask app."""
    app.route('/api/auth/v2/forgot-password', methods=['POST'])(forgot_password)
    app.route('/api/auth/v2/reset-password', methods=['POST'])(reset_password)
    print("✓ Password reset endpoints registered (forgot + reset)")
