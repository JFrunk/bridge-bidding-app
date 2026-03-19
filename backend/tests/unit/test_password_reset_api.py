"""Tests for auth.password_reset_api — forgot password and reset flows."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from flask import Flask

os.environ.setdefault('JWT_SECRET', 'test-secret-do-not-use-in-production-1234')
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

from auth.password_reset_api import register_password_reset_endpoints


@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    register_password_reset_endpoints(test_app)
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


# ─── Forgot Password Tests ──────────────────────────────────


class TestForgotPassword:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/forgot-password',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_email(self, client):
        resp = client.post('/api/auth/v2/forgot-password', json={})
        assert resp.status_code == 400

    def test_invalid_email(self, client):
        resp = client.post('/api/auth/v2/forgot-password', json={
            'email': 'not-valid',
        })
        assert resp.status_code == 400

    @patch('auth.password_reset_api._get_user_by_email')
    def test_nonexistent_email_returns_200(self, mock_get, client):
        """No enumeration — always returns success."""
        mock_get.return_value = None
        resp = client.post('/api/auth/v2/forgot-password', json={
            'email': 'nobody@example.com',
        })
        assert resp.status_code == 200
        assert 'if an account exists' in resp.get_json()['message'].lower()

    @patch('auth.password_reset_api._get_user_by_email')
    def test_unverified_email_returns_200_no_send(self, mock_get, client):
        """Unverified email — return success but don't send."""
        mock_get.return_value = {'id': 42, 'email_verified': False}
        resp = client.post('/api/auth/v2/forgot-password', json={
            'email': 'user@example.com',
        })
        assert resp.status_code == 200

    @patch('auth.password_reset_api._get_email_service')
    @patch('auth.password_reset_api.store_auth_token')
    @patch('auth.password_reset_api.invalidate_tokens_for_user')
    @patch('auth.password_reset_api._get_user_by_email')
    def test_verified_email_sends_reset(self, mock_get, mock_invalidate,
                                         mock_store, mock_svc_fn, client):
        mock_get.return_value = {
            'id': 42,
            'email': 'user@example.com',
            'email_verified': True,
        }

        mock_svc = MagicMock()
        mock_svc.get_app_url.return_value = 'https://app.mybridgebuddy.com'
        mock_svc.send_email.return_value = True
        mock_svc_fn.return_value = mock_svc

        resp = client.post('/api/auth/v2/forgot-password', json={
            'email': 'user@example.com',
        })
        assert resp.status_code == 200

        # Token stored
        mock_store.assert_called_once()
        args = mock_store.call_args
        assert args[0][0] == 42
        assert args[0][2] == 'password_reset'

        # Old tokens invalidated
        mock_invalidate.assert_called_once_with(42, 'password_reset')

        # Email sent
        mock_svc.send_email.assert_called_once()
        call_args = mock_svc.send_email.call_args
        assert call_args[0][0] == 'user@example.com'
        assert 'reset' in call_args[0][1].lower()


# ─── Reset Password Tests ───────────────────────────────────


class TestResetPassword:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/reset-password',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_token(self, client):
        resp = client.post('/api/auth/v2/reset-password', json={
            'password': 'NewSecure1',
        })
        assert resp.status_code == 400

    def test_missing_password(self, client):
        resp = client.post('/api/auth/v2/reset-password', json={
            'token': 'some-token',
        })
        assert resp.status_code == 400

    def test_weak_password_rejected(self, client):
        resp = client.post('/api/auth/v2/reset-password', json={
            'token': 'some-token',
            'password': 'short',
        })
        assert resp.status_code == 400

    @patch('auth.password_reset_api.lookup_auth_token')
    @patch('auth.password_reset_api._auth_svc')
    def test_invalid_token_returns_401(self, mock_svc, mock_lookup, client):
        mock_svc.validate_password.return_value = None
        mock_svc.hash_token.return_value = 'hashed'
        mock_lookup.return_value = None
        resp = client.post('/api/auth/v2/reset-password', json={
            'token': 'bad-token',
            'password': 'NewSecure1',
        })
        assert resp.status_code == 401

    @patch('auth.password_reset_api._get_email_service')
    @patch('auth.password_reset_api._revoke_all_user_tokens')
    @patch('auth.password_reset_api._set_password_hash')
    @patch('auth.password_reset_api.consume_auth_token')
    @patch('auth.password_reset_api._get_user_by_email_or_id')
    @patch('auth.password_reset_api.lookup_auth_token')
    @patch('auth.password_reset_api._auth_svc')
    def test_valid_token_resets_password(self, mock_svc, mock_lookup,
                                         mock_get_user, mock_consume,
                                         mock_set_hash, mock_revoke,
                                         mock_email_svc_fn, client):
        mock_svc.validate_password.return_value = None
        mock_svc.hash_token.return_value = 'hashed'
        mock_svc.hash_password.return_value = 'new-argon2-hash'
        mock_svc.verify_password.return_value = False  # Different password

        mock_lookup.return_value = {
            'id': 1,
            'user_id': 42,
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        mock_get_user.return_value = {
            'id': 42,
            'email': 'user@example.com',
            'password_hash': 'old-hash',
        }

        mock_email_svc = MagicMock()
        mock_email_svc.send_email.return_value = True
        mock_email_svc_fn.return_value = mock_email_svc

        resp = client.post('/api/auth/v2/reset-password', json={
            'token': 'valid-token',
            'password': 'NewSecure1',
        })

        assert resp.status_code == 200
        assert 'reset successfully' in resp.get_json()['message'].lower()

        # Token consumed
        mock_consume.assert_called_once_with('hashed')

        # Password updated
        mock_set_hash.assert_called_once_with(42, 'new-argon2-hash')

        # All refresh tokens revoked
        mock_revoke.assert_called_once_with(42)

        # Password changed notification sent
        mock_email_svc.send_email.assert_called_once()

    @patch('auth.password_reset_api._get_user_by_email_or_id')
    @patch('auth.password_reset_api.lookup_auth_token')
    @patch('auth.password_reset_api._auth_svc')
    def test_same_password_rejected(self, mock_svc, mock_lookup,
                                     mock_get_user, client):
        mock_svc.validate_password.return_value = None
        mock_svc.hash_token.return_value = 'hashed'
        mock_svc.verify_password.return_value = True  # Same password

        mock_lookup.return_value = {
            'id': 1,
            'user_id': 42,
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        mock_get_user.return_value = {
            'id': 42,
            'password_hash': 'existing-hash',
        }

        resp = client.post('/api/auth/v2/reset-password', json={
            'token': 'valid-token',
            'password': 'SamePassword1',
        })

        assert resp.status_code == 400
        assert 'different' in resp.get_json()['error'].lower()
