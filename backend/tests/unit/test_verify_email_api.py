"""Tests for auth.verify_email_api — email verification and resend."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from flask import Flask

os.environ.setdefault('JWT_SECRET', 'test-secret-do-not-use-in-production-1234')
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

from auth.verify_email_api import register_verify_email_endpoints


@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    register_verify_email_endpoints(test_app)
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


# ─── Verify Email Tests ─────────────────────────────────────


class TestVerifyEmail:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/verify-email',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_token(self, client):
        resp = client.post('/api/auth/v2/verify-email', json={})
        assert resp.status_code == 400

    @patch('auth.verify_email_api.lookup_auth_token')
    @patch('auth.verify_email_api._auth_svc')
    def test_invalid_token_returns_401(self, mock_svc, mock_lookup, client):
        mock_svc.hash_token.return_value = 'hashed'
        mock_lookup.return_value = None
        resp = client.post('/api/auth/v2/verify-email', json={
            'token': 'bad-token',
        })
        assert resp.status_code == 401
        assert 'invalid' in resp.get_json()['error'].lower()

    @patch('db.get_connection')
    @patch('auth.verify_email_api.consume_auth_token')
    @patch('auth.verify_email_api.lookup_auth_token')
    @patch('auth.verify_email_api._auth_svc')
    def test_valid_token_verifies_email(self, mock_svc, mock_lookup,
                                        mock_consume, mock_conn, client):
        mock_svc.hash_token.return_value = 'hashed'
        mock_lookup.return_value = {
            'id': 1,
            'user_id': 42,
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=12),
        }

        mock_ctx = MagicMock()
        mock_conn.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)

        resp = client.post('/api/auth/v2/verify-email', json={
            'token': 'valid-token',
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['user_id'] == 42
        assert 'verified' in data['message'].lower()

        # Token was consumed
        mock_consume.assert_called_once_with('hashed')

    @patch('auth.verify_email_api.lookup_auth_token')
    @patch('auth.verify_email_api._auth_svc')
    def test_expired_token_returns_401(self, mock_svc, mock_lookup, client):
        mock_svc.hash_token.return_value = 'hashed'
        mock_lookup.return_value = None  # lookup filters expired
        resp = client.post('/api/auth/v2/verify-email', json={
            'token': 'expired-token',
        })
        assert resp.status_code == 401


# ─── Resend Verification Tests ──────────────────────────────


class TestResendVerification:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/resend-verification',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_email(self, client):
        resp = client.post('/api/auth/v2/resend-verification', json={})
        assert resp.status_code == 400

    def test_invalid_email(self, client):
        resp = client.post('/api/auth/v2/resend-verification', json={
            'email': 'not-valid',
        })
        assert resp.status_code == 400

    @patch('auth.verify_email_api._get_user_by_email')
    def test_nonexistent_email_returns_200(self, mock_get, client):
        """No enumeration — always returns success."""
        mock_get.return_value = None
        resp = client.post('/api/auth/v2/resend-verification', json={
            'email': 'nobody@example.com',
        })
        assert resp.status_code == 200
        assert 'if an account exists' in resp.get_json()['message'].lower()

    @patch('auth.verify_email_api._get_user_by_email')
    def test_already_verified_returns_200(self, mock_get, client):
        mock_get.return_value = {'id': 42, 'email_verified': True}
        resp = client.post('/api/auth/v2/resend-verification', json={
            'email': 'user@example.com',
        })
        assert resp.status_code == 200
        assert 'already verified' in resp.get_json()['message'].lower()

    @patch('auth.verify_email_api.send_verification_email')
    @patch('auth.verify_email_api._get_user_by_email')
    def test_unverified_user_resends(self, mock_get, mock_send, client):
        mock_get.return_value = {
            'id': 42,
            'email': 'user@example.com',
            'email_verified': False,
            'display_name': 'Jane',
        }
        mock_send.return_value = True

        resp = client.post('/api/auth/v2/resend-verification', json={
            'email': 'user@example.com',
        })
        assert resp.status_code == 200
        mock_send.assert_called_once_with(42, 'user@example.com', 'Jane')
