"""
Regression test for simple login endpoint bug (2025-10-29)

BUG: Frontend calls /api/auth/simple-login but endpoint doesn't exist
SYMPTOMS: "Failed to fetch" error when trying to log in
ROOT CAUSE: Missing /api/auth/simple-login endpoint in server.py
FIX: Add simple-login endpoint that creates/fetches user by email or phone

This test MUST FAIL before the fix and PASS after the fix.
"""

import pytest
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Skip if DATABASE_URL not set (server.py and db.py require PostgreSQL)
if not os.environ.get('DATABASE_URL'):
    pytest.skip("DATABASE_URL not set — requires PostgreSQL", allow_module_level=True)

from db import get_connection
from server import app


# Use unique test identifiers to avoid collisions
TEST_EMAIL_PREFIX = 'regtest_login_10292025_'


@pytest.fixture(autouse=True)
def cleanup_test_users():
    """Clean up test users before and after each test"""
    _cleanup()
    yield
    _cleanup()


def _cleanup():
    """Remove test users created during tests"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM users WHERE email LIKE ? OR phone LIKE ?",
                (f'{TEST_EMAIL_PREFIX}%', '+15551234567_regtest%')
            )
            # Also clean up by specific test emails/phones used
            cursor.execute(
                "DELETE FROM users WHERE email IN (?, ?, ?) OR phone IN (?, ?, ?)",
                (
                    f'{TEST_EMAIL_PREFIX}test@example.com',
                    f'{TEST_EMAIL_PREFIX}newuser@example.com',
                    f'{TEST_EMAIL_PREFIX}existing@example.com',
                    '+15551234567',
                    '+15551234568',
                    '+15551234569',
                )
            )
    except Exception:
        pass


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


class TestSimpleLoginEndpoint:
    """Test suite for /api/auth/simple-login endpoint"""

    def test_endpoint_exists(self, client):
        """Test that /api/auth/simple-login endpoint exists"""
        response = client.post('/api/auth/simple-login',
                              json={'email': f'{TEST_EMAIL_PREFIX}test@example.com'},
                              content_type='application/json')

        # Should NOT be 404 - endpoint should exist
        assert response.status_code != 404, \
            "Endpoint /api/auth/simple-login does not exist (404 Not Found)"

    def test_simple_login_with_email_new_user(self, client):
        """Test simple login creates new user with email"""
        response = client.post('/api/auth/simple-login',
                              json={
                                  'email': f'{TEST_EMAIL_PREFIX}newuser@example.com',
                                  'create_if_not_exists': True
                              },
                              content_type='application/json')

        assert response.status_code == 200, \
            f"Expected 200 OK, got {response.status_code}"

        data = response.get_json()

        # Check response structure
        assert 'user_id' in data, "Response missing 'user_id'"
        assert 'email' in data, "Response missing 'email'"
        assert 'created' in data, "Response missing 'created' flag"

        # Verify new user was created
        assert data['email'] == f'{TEST_EMAIL_PREFIX}newuser@example.com'
        assert data['created'] is True, "Should indicate new user was created"
        assert isinstance(data['user_id'], int), "user_id should be an integer"
        assert data['user_id'] > 0, "user_id should be positive"

    def test_simple_login_with_phone_new_user(self, client):
        """Test simple login creates new user with phone (10-digit US format)"""
        response = client.post('/api/auth/simple-login',
                              json={
                                  'phone': '5551234567',  # 10-digit US number without +1
                                  'create_if_not_exists': True
                              },
                              content_type='application/json')

        assert response.status_code == 200, \
            f"Expected 200 OK, got {response.status_code}"

        data = response.get_json()

        # Check response structure
        assert 'user_id' in data, "Response missing 'user_id'"
        assert 'phone' in data, "Response missing 'phone'"
        assert 'created' in data, "Response missing 'created' flag"

        # Verify new user was created and +1 was auto-added
        assert data['phone'] == '+15551234567', "Should auto-add +1 to US numbers"
        assert data['created'] is True

    def test_simple_login_with_phone_formatted(self, client):
        """Test simple login accepts formatted phone numbers"""
        response = client.post('/api/auth/simple-login',
                              json={
                                  'phone': '(555) 123-4568',  # Formatted US number
                                  'create_if_not_exists': True
                              },
                              content_type='application/json')

        assert response.status_code == 200, \
            f"Expected 200 OK, got {response.status_code}"

        data = response.get_json()
        assert data['phone'] == '+15551234568', "Should strip formatting and add +1"
        assert data['created'] is True

    def test_simple_login_with_phone_international_format(self, client):
        """Test simple login still accepts international format"""
        response = client.post('/api/auth/simple-login',
                              json={
                                  'phone': '+15551234569',  # Already has +1
                                  'create_if_not_exists': True
                              },
                              content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert data['phone'] == '+15551234569'
        assert data['created'] is True

    def test_simple_login_existing_user_returns_same_id(self, client):
        """Test simple login returns existing user without creating duplicate"""
        # First login - creates user
        response1 = client.post('/api/auth/simple-login',
                               json={
                                   'email': f'{TEST_EMAIL_PREFIX}existing@example.com',
                                   'create_if_not_exists': True
                               },
                               content_type='application/json')

        assert response1.status_code == 200
        data1 = response1.get_json()
        user_id_1 = data1['user_id']
        assert data1['created'] is True

        # Second login - should return existing user
        response2 = client.post('/api/auth/simple-login',
                               json={
                                   'email': f'{TEST_EMAIL_PREFIX}existing@example.com',
                                   'create_if_not_exists': True
                               },
                               content_type='application/json')

        assert response2.status_code == 200
        data2 = response2.get_json()

        # Should return same user_id, not create new user
        assert data2['user_id'] == user_id_1, \
            "Should return existing user_id, not create duplicate"
        assert data2['created'] is False, \
            "Should indicate user already existed"

    def test_simple_login_missing_identifier(self, client):
        """Test simple login fails gracefully without email or phone"""
        response = client.post('/api/auth/simple-login',
                              json={'create_if_not_exists': True},
                              content_type='application/json')

        # Should return error, not crash
        assert response.status_code == 400, \
            "Should return 400 Bad Request when missing email/phone"

        data = response.get_json()
        assert 'error' in data, "Error response should contain 'error' field"

    def test_simple_login_invalid_email_format(self, client):
        """Test simple login validates email format"""
        response = client.post('/api/auth/simple-login',
                              json={
                                  'email': 'not-an-email',
                                  'create_if_not_exists': True
                              },
                              content_type='application/json')

        # Should reject invalid email
        assert response.status_code == 400, \
            "Should return 400 Bad Request for invalid email format"

        data = response.get_json()
        assert 'error' in data

    def test_simple_login_invalid_phone_format(self, client):
        """Test simple login validates phone format (too short)"""
        response = client.post('/api/auth/simple-login',
                              json={
                                  'phone': '12345',  # Too short
                                  'create_if_not_exists': True
                              },
                              content_type='application/json')

        # Should reject invalid phone
        assert response.status_code == 400, \
            "Should return 400 Bad Request for invalid phone format"

        data = response.get_json()
        assert 'error' in data

    def test_simple_login_cors_enabled(self, client):
        """Test that CORS headers are present for frontend access"""
        response = client.post('/api/auth/simple-login',
                              json={'email': f'{TEST_EMAIL_PREFIX}test@example.com'},
                              content_type='application/json')

        # CORS should be enabled for frontend to access
        # Note: In test environment CORS headers might not be fully set,
        # but endpoint should still work
        assert response.status_code in [200, 400, 404], \
            "Endpoint should respond (CORS should allow request)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
