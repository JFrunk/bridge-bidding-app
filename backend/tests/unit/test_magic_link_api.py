"""Tests for auth.magic_link_api — magic link request and verification."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from flask import Flask

os.environ.setdefault('JWT_SECRET', 'test-secret-do-not-use-in-production-1234')
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

from auth.magic_link_api import register_magic_link_endpoints


@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    register_magic_link_endpoints(test_app)
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


# ─── Request Endpoint Tests ──────────────────────────────────


class TestMagicLinkRequest:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/magic-link/request',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_email(self, client):
        resp = client.post('/api/auth/v2/magic-link/request', json={})
        assert resp.status_code == 400

    def test_invalid_email(self, client):
        resp = client.post('/api/auth/v2/magic-link/request', json={
            'email': 'not-valid',
        })
        assert resp.status_code == 400

    @patch('auth.magic_link_api._get_user_by_email')
    def test_nonexistent_email_returns_200_no_enumeration(self, mock_get, client):
        """Must return 200 even when email doesn't exist."""
        mock_get.return_value = None
        resp = client.post('/api/auth/v2/magic-link/request', json={
            'email': 'nobody@example.com',
        })
        assert resp.status_code == 200
        assert 'if an account exists' in resp.get_json()['message'].lower()

    @patch('auth.magic_link_api._get_email_service')
    @patch('auth.magic_link_api.store_auth_token')
    @patch('auth.magic_link_api.invalidate_tokens_for_user')
    @patch('auth.magic_link_api._get_user_by_email')
    def test_existing_email_sends_link(self, mock_get, mock_invalidate,
                                       mock_store, mock_svc_fn, client):
        mock_get.return_value = {'id': 42, 'email': 'user@example.com'}

        mock_svc = MagicMock()
        mock_svc.get_app_url.return_value = 'https://app.mybridgebuddy.com'
        mock_svc.send_email.return_value = True
        mock_svc_fn.return_value = mock_svc

        resp = client.post('/api/auth/v2/magic-link/request', json={
            'email': 'user@example.com',
        })
        assert resp.status_code == 200

        # Token was stored
        mock_store.assert_called_once()
        args = mock_store.call_args
        assert args[0][0] == 42  # user_id
        assert args[0][2] == 'magic_link'  # token_type

        # Old tokens invalidated
        mock_invalidate.assert_called_once_with(42, 'magic_link')

        # Email was sent
        mock_svc.send_email.assert_called_once()
        call_args = mock_svc.send_email.call_args
        assert call_args[0][0] == 'user@example.com'
        assert 'login link' in call_args[0][1].lower()


# ─── Verify Endpoint Tests ───────────────────────────────────


class TestMagicLinkVerify:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/magic-link/verify',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_token(self, client):
        resp = client.post('/api/auth/v2/magic-link/verify', json={})
        assert resp.status_code == 400

    @patch('auth.magic_link_api.lookup_auth_token')
    def test_invalid_token_returns_401(self, mock_lookup, client):
        mock_lookup.return_value = None
        resp = client.post('/api/auth/v2/magic-link/verify', json={
            'token': 'bad-token',
        })
        assert resp.status_code == 401
        assert 'invalid' in resp.get_json()['error'].lower()

    @patch('auth.magic_link_api._get_user_manager')
    @patch('auth.auth_api._add_auth_provider')
    @patch('auth.magic_link_api.consume_auth_token')
    @patch('auth.magic_link_api.lookup_auth_token')
    def test_valid_token_issues_jwt(self, mock_lookup, mock_consume,
                                    mock_add_prov, mock_mgr_fn, client):
        mock_lookup.return_value = {
            'id': 1,
            'user_id': 42,
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=10),
        }
        mock_mgr = MagicMock()
        mock_mgr_fn.return_value = mock_mgr

        # Mock the DB update for email_verified
        with patch('db.get_connection') as mock_conn:
            mock_ctx = MagicMock()
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_ctx)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)

            # Also mock _store_refresh_token
            with patch('auth.magic_link_api._store_refresh_token'):
                resp = client.post('/api/auth/v2/magic-link/verify', json={
                    'token': 'valid-token',
                })

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'access_token' in data
        assert data['user_id'] == 42

        # Token was consumed
        mock_consume.assert_called_once()

        # Auth provider added
        mock_add_prov.assert_called_once_with(42, 'magic_link')

    @patch('auth.magic_link_api.lookup_auth_token')
    def test_expired_token_returns_401(self, mock_lookup, client):
        """Expired tokens should not be returned by lookup."""
        mock_lookup.return_value = None  # lookup filters expired
        resp = client.post('/api/auth/v2/magic-link/verify', json={
            'token': 'expired-token',
        })
        assert resp.status_code == 401
