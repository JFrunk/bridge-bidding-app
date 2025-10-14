"""
Simple Auth API - MVP Version
Email-only authentication, no passwords
Easy upgrade path to full security later

Features:
- Email-only login (no password required)
- Auto-account creation on first login
- Session token management
- Guest mode support
"""

from flask import request, jsonify
import secrets
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.learning.user_manager import get_user_manager

# Simple in-memory session store
# TODO: Upgrade to Redis or database for production
active_sessions = {}

def generate_session_token():
    """Generate a cryptographically secure session token"""
    return secrets.token_urlsafe(32)

def login_with_email():
    """
    POST /api/auth/login

    Body:
        {
            "email": "user@example.com",  (OR)
            "phone": "+1234567890",
            "display_name": "John Doe" (optional)
        }

    Returns:
        {
            "success": true,
            "session_token": "...",
            "user": {...},
            "is_new_user": true/false
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = data.get('email', '').strip().lower() if data.get('email') else None
    phone = data.get('phone', '').strip() if data.get('phone') else None
    display_name = data.get('display_name', '').strip()

    # Must provide either email or phone
    if not email and not phone:
        return jsonify({'error': 'Email or phone number required'}), 400

    # Validate email format if provided
    if email:
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({'error': 'Invalid email format'}), 400

    # Validate phone format if provided
    if phone:
        # Remove common formatting characters
        clean_phone = phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        if not clean_phone.startswith('+'):
            return jsonify({'error': 'Phone must include country code (e.g., +1234567890)'}), 400
        if not clean_phone[1:].isdigit():
            return jsonify({'error': 'Invalid phone number format'}), 400
        phone = clean_phone  # Use cleaned version

    try:
        user_manager = get_user_manager()

        # Check if user exists (by email or phone)
        existing_user = None
        if email:
            existing_user = user_manager.get_user_by_email(email)
        elif phone:
            existing_user = user_manager.get_user_by_phone(phone)

        is_new_user = existing_user is None

        if existing_user:
            user = existing_user
            # Update last login
            user_manager.update_last_login(user.id)
        else:
            # Create new user
            # Generate username from email or phone
            if email:
                username = email.split('@')[0]
            else:
                # For phone, use last 4 digits plus random suffix
                username = f"user{phone[-4:]}"

            # Handle username conflicts by appending number
            counter = 1
            original_username = username
            while user_manager.user_exists(username):
                username = f"{original_username}{counter}"
                counter += 1

            # Use display_name if provided, otherwise use username
            final_display_name = display_name if display_name else username.title()

            user_id = user_manager.create_user(
                username=username,
                email=email,
                display_name=final_display_name,
                phone=phone
            )
            user = user_manager.get_user(user_id)

        # Generate session token
        session_token = generate_session_token()
        active_sessions[session_token] = {
            'user_id': user.id,
            'email': user.email,
            'phone': getattr(user, 'phone', None),
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat()
        }

        return jsonify({
            'success': True,
            'session_token': session_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'display_name': user.display_name,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'timezone': user.timezone
            },
            'is_new_user': is_new_user
        })

    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

def validate_session():
    """
    GET /api/auth/session

    Headers:
        Authorization: Bearer <token>

    Returns user info if session is valid
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No session token provided'}), 401

    token = auth_header.split(' ')[1]

    if token not in active_sessions:
        return jsonify({'error': 'Invalid or expired session'}), 401

    session = active_sessions[token]

    # Check if session expired
    expires_at = datetime.fromisoformat(session['expires_at'])
    if datetime.now() > expires_at:
        del active_sessions[token]
        return jsonify({'error': 'Session expired'}), 401

    try:
        user_manager = get_user_manager()
        user = user_manager.get_user(session['user_id'])

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Update activity
        user_manager.update_user_activity(user.id)

        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'display_name': user.display_name,
                'timezone': user.timezone
            }
        })

    except Exception as e:
        print(f"Session validation error: {e}")
        return jsonify({'error': 'Session validation failed'}), 500

def logout():
    """
    POST /api/auth/logout

    Headers:
        Authorization: Bearer <token>

    Invalidates the session token
    """
    auth_header = request.headers.get('Authorization')

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        if token in active_sessions:
            del active_sessions[token]

    return jsonify({'success': True, 'message': 'Logged out successfully'})

def get_session_info():
    """
    GET /api/auth/session-info

    Returns information about active sessions (for debugging)
    Admin only in production
    """
    return jsonify({
        'active_sessions': len(active_sessions),
        'sessions': [
            {
                'user_id': session['user_id'],
                'email': session['email'],
                'created_at': session['created_at']
            }
            for session in active_sessions.values()
        ]
    })

def register_simple_auth_endpoints(app):
    """
    Register simplified auth endpoints with Flask app

    Endpoints:
        POST /api/auth/login - Login with email
        GET  /api/auth/session - Validate session
        POST /api/auth/logout - Logout
        GET  /api/auth/session-info - Debug info
    """
    app.route('/api/auth/login', methods=['POST'])(login_with_email)
    app.route('/api/auth/session', methods=['GET'])(validate_session)
    app.route('/api/auth/logout', methods=['POST'])(logout)
    app.route('/api/auth/session-info', methods=['GET'])(get_session_info)

    print("✓ Simple Auth API endpoints registered (MVP - email only)")
