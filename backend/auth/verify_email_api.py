"""
Email Verification API — Verify email ownership after registration.

Per AUTH_PRD §3.4:
- POST /api/auth/v2/verify-email — validate verification token
- POST /api/auth/v2/resend-verification — resend verification email

Verification tokens are stored as SHA-256 hashes in the auth_tokens table.
"""

from datetime import datetime, timedelta, timezone

from flask import request, jsonify

from auth.auth_service import AuthService
from auth.token_store import (
    store_auth_token,
    lookup_auth_token,
    consume_auth_token,
    invalidate_tokens_for_user,
)
from auth.email_templates import verification_email
from utils.error_logger import log_error

_auth_svc = AuthService()

VERIFICATION_EXPIRY_HOURS = 24


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


def _get_user_by_id(user_id):
    """Fetch user row by ID. Returns dict or None."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,),
        )
        return cursor.fetchone()


def send_verification_email(user_id, email, display_name=''):
    """
    Generate a verification token and send the verification email.

    Called after registration (from auth_api.py) and from
    the resend-verification endpoint.

    Returns True if email was sent, False otherwise.
    """
    try:
        # Invalidate any existing verification tokens
        invalidate_tokens_for_user(user_id, 'email_verify')

        # Generate and store token
        raw_token = _auth_svc.generate_token()
        token_hash = _auth_svc.hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_EXPIRY_HOURS)

        store_auth_token(user_id, token_hash, 'email_verify', expires_at)

        # Send email
        svc = _get_email_service()
        app_url = svc.get_app_url()
        email_data = verification_email(app_url, raw_token, display_name)
        return svc.send_email(email, email_data['subject'], email_data['html'], email_data['text'])

    except Exception as e:
        log_error(e, context={'action': 'send_verification_email', 'user_id': user_id})
        return False


# ─── Endpoints ────────────────────────────────────────────────


def verify_email():
    """
    POST /api/auth/v2/verify-email

    Body: {"token": "raw_token_from_email"}

    Validates the token, sets email_verified = true.
    Returns 200 on success, 401 on invalid/expired token.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    raw_token = data.get('token', '')
    if not raw_token:
        return jsonify({'error': 'Token required'}), 400

    try:
        token_hash = _auth_svc.hash_token(raw_token)
        row = lookup_auth_token(token_hash, 'email_verify')

        if not row:
            return jsonify({'error': 'Invalid or expired verification link'}), 401

        user_id = row['user_id']

        # Consume the token
        consume_auth_token(token_hash)

        # Set email_verified = true
        from db import get_connection
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET email_verified = true WHERE id = %s",
                (user_id,),
            )

        return jsonify({'message': 'Email verified successfully', 'user_id': user_id}), 200

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/verify-email')
        return jsonify({'error': 'Verification failed'}), 500


def resend_verification():
    """
    POST /api/auth/v2/resend-verification

    Body: {"email": "user@example.com"}

    Resends the verification email. Rate limited: 1/min, 5/hour (via PRD).
    Returns generic success message regardless of whether email exists
    (no enumeration).
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = (data.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email address required'}), 400

    success_msg = {'message': 'If an account exists, a verification email has been sent.'}

    try:
        user = _get_user_by_email(email)
        if not user:
            return jsonify(success_msg), 200

        # Already verified — no need to resend
        if user.get('email_verified'):
            return jsonify({'message': 'Email is already verified.'}), 200

        display_name = user.get('display_name') or ''
        send_verification_email(user['id'], email, display_name)

        return jsonify(success_msg), 200

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/resend-verification')
        return jsonify(success_msg), 200


def register_verify_email_endpoints(app):
    """Register email verification endpoints with Flask app."""
    app.route('/api/auth/v2/verify-email', methods=['POST'])(verify_email)
    app.route('/api/auth/v2/resend-verification', methods=['POST'])(resend_verification)
    print("✓ Email verification endpoints registered (verify + resend)")
