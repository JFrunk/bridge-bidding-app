"""
Auth API V2 — Password-based registration and login.

Per AUTH_PRD §3.1 (Phase 2):
- POST /api/auth/v2/register — create account with password
- POST /api/auth/v2/login — password login with lockout

Endpoints are namespaced under /v2/ to coexist with the existing
simple-login system during migration (PRD §8).
"""

from datetime import datetime, timedelta, timezone

from flask import request, jsonify, make_response

from auth.auth_service import (
    AuthService,
    PasswordTooShortError,
    PasswordTooCommonError,
    PasswordMissingLetterError,
    PasswordMissingDigitError,
)
from auth.jwt_service import JWTService
from auth.token_api import (
    _store_refresh_token,
    _set_refresh_cookie,
    _revoke_all_user_tokens,
)
from utils.error_logger import log_error

_auth_svc = AuthService()
_jwt_svc = JWTService()


def _get_user_manager():
    """Lazy import to avoid module-level DATABASE_URL dependency."""
    from engine.learning.user_manager import get_user_manager
    return get_user_manager()

# Lockout constants per PRD §3.1
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


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


def _has_google_provider(user_id):
    """Check if user has linked Google as an auth provider."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM auth_providers WHERE user_id = %s AND provider = 'google'",
            (user_id,),
        )
        return cursor.fetchone() is not None


def _add_auth_provider(user_id, provider):
    """Record a linked auth provider for a user."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO auth_providers (user_id, provider)
                   VALUES (%s, %s)""",
                (user_id, provider),
            )
        except Exception as e:
            # Ignore duplicate (already linked)
            if 'duplicate' not in str(e).lower():
                raise


def _record_failed_login(user_id):
    """Increment failed_login_attempts. Lock if threshold reached."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE users
               SET failed_login_attempts = failed_login_attempts + 1
               WHERE id = %s
               RETURNING failed_login_attempts""",
            (user_id,),
        )
        row = cursor.fetchone()
        attempts = row['failed_login_attempts'] if row else 0

        if attempts >= MAX_FAILED_ATTEMPTS:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            cursor.execute(
                "UPDATE users SET locked_until = %s WHERE id = %s",
                (locked_until, user_id),
            )


def _clear_failed_logins(user_id):
    """Reset failed attempts on successful login."""
    from db import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE users
               SET failed_login_attempts = 0, locked_until = NULL
               WHERE id = %s""",
            (user_id,),
        )


def _is_locked(user):
    """Check if a user account is currently locked."""
    locked_until = user.get('locked_until')
    if not locked_until:
        return False
    if isinstance(locked_until, str):
        locked_until = datetime.fromisoformat(locked_until)
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < locked_until


def _migrate_guest_data(new_user_id, guest_id):
    """
    Migrate all guest data from a negative guest_id to the new user.

    Mirrors the migration logic in server.py /api/auth/simple-login.
    """
    from db import get_connection
    if not guest_id or not isinstance(guest_id, int) or guest_id >= 0:
        return {}

    migrated = {}
    with get_connection() as conn:
        cursor = conn.cursor()

        # Core tables
        for table in ['game_sessions', 'bidding_decisions', 'hand_analyses']:
            cursor.execute(
                f'UPDATE {table} SET user_id = %s WHERE user_id = %s',
                (new_user_id, guest_id),
            )
            if cursor.rowcount:
                migrated[table] = cursor.rowcount

        # Learning/progress tables (may not all exist)
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
                pass  # Table may not exist

    return migrated


def _issue_tokens_response(user_id, extra_data=None):
    """
    Create a response with JWT access token in body and
    refresh token in HttpOnly cookie.
    """
    access_token = _jwt_svc.create_access_token(user_id=user_id)
    raw_refresh, refresh_hash = _jwt_svc.create_refresh_token()
    refresh_expiry = _jwt_svc.get_refresh_expiry()
    _store_refresh_token(user_id, refresh_hash, refresh_expiry)

    # Include user profile so frontend can display identity
    try:
        from engine.learning.user_manager import get_user_manager
        profile = get_user_manager().get_user(user_id)
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
    _set_refresh_cookie(response, raw_refresh, refresh_expiry)
    return response


# ─── Endpoints ────────────────────────────────────────────────


def register():
    """
    POST /api/auth/v2/register

    Body:
        {
            "email": "user@example.com",
            "password": "SecurePass1",
            "display_name": "Jane Doe",   // optional
            "guest_id": -123456789        // optional — migrate guest data
        }

    Returns 201 on success, 400 on validation failure, 409 on duplicate email.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')
    display_name = (data.get('display_name') or '').strip()
    guest_id = data.get('guest_id')

    # Validate email
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'error': 'Valid email address required'}), 400

    # Validate password
    try:
        _auth_svc.validate_password(password)
    except (PasswordTooShortError, PasswordMissingLetterError,
            PasswordMissingDigitError, PasswordTooCommonError) as e:
        return jsonify({'error': str(e)}), 400

    # Check for existing email — registration rejects duplicates (not no-enum)
    existing = _get_user_by_email(email)
    if existing:
        return jsonify({'error': 'An account with this email already exists'}), 409

    try:
        user_manager = _get_user_manager()

        # Generate username from email
        username = email.split('@')[0]
        counter = 1
        original = username
        while user_manager.user_exists(username):
            username = f"{original}{counter}"
            counter += 1

        user_id = user_manager.create_user(
            username=username,
            email=email,
            display_name=display_name or username.title(),
        )

        # Set password hash
        password_hash = _auth_svc.hash_password(password)
        _set_password_hash(user_id, password_hash)
        _add_auth_provider(user_id, 'password')

        # Migrate guest data if provided
        migrated = {}
        if guest_id:
            migrated = _migrate_guest_data(user_id, guest_id)

        # Update login timestamp
        user_manager.update_last_login(user_id)

        # Send verification email (non-blocking — don't fail registration)
        try:
            from auth.verify_email_api import send_verification_email
            send_verification_email(user_id, email, display_name or username.title())
        except Exception:
            pass  # Email failure shouldn't block registration

        extra = {'is_new_user': True, 'email_verified': False}
        if migrated:
            extra['migrated_from_guest'] = True
            extra['migrated_data'] = migrated

        response = _issue_tokens_response(user_id, extra_data=extra)
        response.status_code = 201
        return response

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/register')
        return jsonify({'error': 'Registration failed'}), 500


def login():
    """
    POST /api/auth/v2/login

    Body:
        {
            "email": "user@example.com",
            "password": "SecurePass1"
        }

    Returns 200 on success, 401 on all failures (no enumeration).
    Locks account after 5 failed attempts within 15 minutes.
    """
    GENERIC_ERROR = 'Invalid email or password'

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': GENERIC_ERROR}), 401

    try:
        user = _get_user_by_email(email)

        # No user found — generic error, no enumeration
        if not user:
            return jsonify({'error': GENERIC_ERROR}), 401

        # Check lockout BEFORE argon2 verify (save CPU)
        if _is_locked(user):
            return jsonify({
                'error': 'Account temporarily locked. Try again in 15 minutes.',
            }), 429

        # No password set — check if they signed up via Google
        if not user.get('password_hash'):
            if _has_google_provider(user['id']):
                return jsonify({
                    'error': 'This account uses Google sign-in. '
                             'Please use the "Continue with Google" button instead.',
                }), 401
            return jsonify({
                'error': 'This account was created before passwords were required. '
                         'Use a magic link or set a password via the reset flow.',
            }), 401

        # Verify password
        if not _auth_svc.verify_password(password, user['password_hash']):
            _record_failed_login(user['id'])
            return jsonify({'error': GENERIC_ERROR}), 401

        # Success — clear any failed attempts
        _clear_failed_logins(user['id'])

        # Check if hash needs rehashing (security param upgrade)
        if _auth_svc.needs_rehash(user['password_hash']):
            new_hash = _auth_svc.hash_password(password)
            _set_password_hash(user['id'], new_hash)

        # Update login timestamp
        _get_user_manager().update_last_login(user['id'])

        return _issue_tokens_response(user['id'])

    except Exception as e:
        log_error(e, endpoint='/api/auth/v2/login')
        return jsonify({'error': 'Login failed'}), 500


def register_auth_v2_endpoints(app):
    """Register Auth V2 password endpoints with Flask app."""
    app.route('/api/auth/v2/register', methods=['POST'])(register)
    app.route('/api/auth/v2/login', methods=['POST'])(login)
    print("✓ Auth V2 endpoints registered (register + login)")
