"""Tests for auth.token_api — refresh token rotation endpoint."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from flask import Flask

os.environ.setdefault('JWT_SECRET', 'test-secret-do-not-use-in-production-1234')

from auth.token_api import register_token_endpoints, REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH


@pytest.fixture
def app():
    """Minimal Flask app with token endpoints registered."""
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    register_token_endpoints(test_app)
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


class TestRefreshEndpoint:
    def test_no_cookie_returns_401(self, client):
        resp = client.post('/api/auth/refresh')
        assert resp.status_code == 401
        assert 'No refresh token' in resp.get_json()['error']

    @patch('auth.token_api._lookup_refresh_token')
    def test_invalid_token_returns_401(self, mock_lookup, client):
        mock_lookup.return_value = None
        client.set_cookie(
            REFRESH_COOKIE_NAME, 'bad-token',
            domain='localhost', path=REFRESH_COOKIE_PATH,
        )
        resp = client.post('/api/auth/refresh')
        assert resp.status_code == 401

    @patch('auth.token_api._store_refresh_token')
    @patch('auth.token_api._revoke_refresh_token')
    @patch('auth.token_api._lookup_refresh_token')
    def test_valid_token_rotates(self, mock_lookup, mock_revoke, mock_store, client):
        """Valid refresh token returns new access token and rotates refresh."""
        mock_lookup.return_value = {
            'id': 1,
            'user_id': 42,
            'expires_at': datetime.now(timezone.utc) + timedelta(days=10),
        }

        client.set_cookie(
            REFRESH_COOKIE_NAME, 'valid-refresh-token',
            domain='localhost', path=REFRESH_COOKIE_PATH,
        )
        resp = client.post('/api/auth/refresh')
        assert resp.status_code == 200

        data = resp.get_json()
        assert 'access_token' in data
        assert data['user_id'] == 42

        # Old token revoked
        mock_revoke.assert_called_once()
        # New token stored
        mock_store.assert_called_once()

    @patch('auth.token_api._store_refresh_token')
    @patch('auth.token_api._revoke_refresh_token')
    @patch('auth.token_api._lookup_refresh_token')
    def test_response_sets_new_cookie(self, mock_lookup, mock_revoke, mock_store, client):
        mock_lookup.return_value = {
            'id': 1, 'user_id': 7,
            'expires_at': datetime.now(timezone.utc) + timedelta(days=10),
        }
        client.set_cookie(
            REFRESH_COOKIE_NAME, 'old-token',
            domain='localhost', path=REFRESH_COOKIE_PATH,
        )
        resp = client.post('/api/auth/refresh')
        # Check that a Set-Cookie header is present for the refresh token
        cookie_headers = [
            h for h in resp.headers.getlist('Set-Cookie')
            if REFRESH_COOKIE_NAME in h
        ]
        assert len(cookie_headers) == 1
        assert 'HttpOnly' in cookie_headers[0]


class TestLogoutEndpoint:
    @patch('auth.token_api._revoke_refresh_token')
    def test_logout_revokes_and_clears(self, mock_revoke, client):
        client.set_cookie(
            REFRESH_COOKIE_NAME, 'some-token',
            domain='localhost', path=REFRESH_COOKIE_PATH,
        )
        resp = client.post('/api/auth/logout-v2')
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        mock_revoke.assert_called_once()

    def test_logout_without_cookie_succeeds(self, client):
        """Logout without a cookie is a no-op, not an error."""
        resp = client.post('/api/auth/logout-v2')
        assert resp.status_code == 200
