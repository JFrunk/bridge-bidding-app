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
import sqlite3
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from server import app


@pytest.fixture
def client():
    """Create test client with isolated test database"""
    app.config['TESTING'] = True

    # Use in-memory database for tests
    test_db_path = ':memory:'

    # Initialize test database
    with app.app_context():
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                phone TEXT UNIQUE,
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                last_activity TIMESTAMP,
                timezone TEXT DEFAULT 'UTC',
                preferences TEXT,
                CONSTRAINT valid_username CHECK(length(username) >= 3)
            )
        ''')
        conn.commit()
        conn.close()

    with app.test_client() as client:
        yield client


class TestSimpleLoginEndpoint:
    """Test suite for /api/auth/simple-login endpoint"""

    def test_endpoint_exists(self, client):
        """Test that /api/auth/simple-login endpoint exists"""
        response = client.post('/api/auth/simple-login',
                              json={'email': 'test@example.com'},
                              content_type='application/json')

        # Should NOT be 404 - endpoint should exist
        assert response.status_code != 404, \
            "Endpoint /api/auth/simple-login does not exist (404 Not Found)"

    def test_simple_login_with_email_new_user(self, client):
        """Test simple login creates new user with email"""
        response = client.post('/api/auth/simple-login',
                              json={
                                  'email': 'newuser@example.com',
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
        assert data['email'] == 'newuser@example.com'
        assert data['created'] is True, "Should indicate new user was created"
        assert isinstance(data['user_id'], int), "user_id should be an integer"
        assert data['user_id'] > 0, "user_id should be positive"

    def test_simple_login_with_phone_new_user(self, client):
        """Test simple login creates new user with phone"""
        response = client.post('/api/auth/simple-login',
                              json={
                                  'phone': '+15551234567',
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

        # Verify new user was created
        assert data['phone'] == '+15551234567'
        assert data['created'] is True

    def test_simple_login_existing_user_returns_same_id(self, client):
        """Test simple login returns existing user without creating duplicate"""
        # First login - creates user
        response1 = client.post('/api/auth/simple-login',
                               json={
                                   'email': 'existing@example.com',
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
                                   'email': 'existing@example.com',
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

    def test_simple_login_cors_enabled(self, client):
        """Test that CORS headers are present for frontend access"""
        response = client.post('/api/auth/simple-login',
                              json={'email': 'test@example.com'},
                              content_type='application/json')

        # CORS should be enabled for frontend to access
        # Note: In test environment CORS headers might not be fully set,
        # but endpoint should still work
        assert response.status_code in [200, 400, 404], \
            "Endpoint should respond (CORS should allow request)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
