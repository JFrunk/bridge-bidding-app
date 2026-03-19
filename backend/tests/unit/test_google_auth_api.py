"""Tests for auth.google_auth_api — Google OAuth sign-in."""

import os
from unittest.mock import patch, MagicMock

import pytest
from flask import Flask

os.environ.setdefault('JWT_SECRET', 'test-secret-do-not-use-in-production-1234')
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

# Set a test client ID so the endpoint doesn't return 503
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test-google-client-id.apps.googleusercontent.com')

# Must set env var before importing the module
from auth.google_auth_api import register_google_auth_endpoints


@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    register_google_auth_endpoints(test_app)
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


class TestGoogleAuth:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/google',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_id_token(self, client):
        resp = client.post('/api/auth/v2/google', json={})
        assert resp.status_code == 400

    @patch('auth.google_auth_api._verify_google_token')
    def test_invalid_token_returns_401(self, mock_verify, client):
        mock_verify.return_value = None
        resp = client.post('/api/auth/v2/google', json={
            'id_token': 'invalid-token',
        })
        assert resp.status_code == 401

    @patch('auth.google_auth_api._verify_google_token')
    def test_no_email_returns_400(self, mock_verify, client):
        mock_verify.return_value = {
            'sub': 'google-123',
            'email': '',
            'name': 'Test User',
        }
        resp = client.post('/api/auth/v2/google', json={
            'id_token': 'valid-token',
        })
        assert resp.status_code == 400

    @patch('auth.google_auth_api._issue_tokens_response')
    @patch('auth.google_auth_api._update_profile_picture')
    @patch('auth.google_auth_api._add_auth_provider')
    @patch('auth.google_auth_api._get_user_manager')
    @patch('auth.google_auth_api._get_user_by_email')
    @patch('auth.google_auth_api._verify_google_token')
    def test_existing_verified_user_logs_in(self, mock_verify, mock_get_user,
                                             mock_mgr_fn, mock_add_prov,
                                             mock_pic, mock_issue, client):
        mock_verify.return_value = {
            'sub': 'google-123',
            'email': 'user@example.com',
            'name': 'Test User',
            'picture': 'https://photo.url/pic.jpg',
        }
        mock_get_user.return_value = {
            'id': 42,
            'email': 'user@example.com',
            'email_verified': True,
        }
        mock_mgr = MagicMock()
        mock_mgr_fn.return_value = mock_mgr

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_issue.return_value = mock_response

        resp = client.post('/api/auth/v2/google', json={
            'id_token': 'valid-token',
        })

        # Auth provider linked
        mock_add_prov.assert_called_once_with(42, 'google', 'google-123')

        # Profile picture updated
        mock_pic.assert_called_once_with(42, 'https://photo.url/pic.jpg')

        # Login timestamp updated
        mock_mgr.update_last_login.assert_called_once_with(42)

    @patch('auth.google_auth_api._get_user_by_email')
    @patch('auth.google_auth_api._verify_google_token')
    def test_unverified_existing_user_blocked(self, mock_verify,
                                               mock_get_user, client):
        """PRD §3.2: prevent squatter attack on unverified accounts."""
        mock_verify.return_value = {
            'sub': 'google-123',
            'email': 'user@example.com',
            'name': 'Test User',
        }
        mock_get_user.return_value = {
            'id': 42,
            'email': 'user@example.com',
            'email_verified': False,
        }

        resp = client.post('/api/auth/v2/google', json={
            'id_token': 'valid-token',
        })
        assert resp.status_code == 403
        assert 'not verified' in resp.get_json()['error'].lower()

    @patch('auth.google_auth_api._issue_tokens_response')
    @patch('auth.google_auth_api._update_profile_picture')
    @patch('auth.google_auth_api._add_auth_provider')
    @patch('auth.google_auth_api._set_email_verified')
    @patch('auth.google_auth_api._get_user_manager')
    @patch('auth.google_auth_api._get_user_by_email')
    @patch('auth.google_auth_api._verify_google_token')
    def test_new_user_creates_account(self, mock_verify, mock_get_user,
                                       mock_mgr_fn, mock_set_verified,
                                       mock_add_prov, mock_pic,
                                       mock_issue, client):
        mock_verify.return_value = {
            'sub': 'google-456',
            'email': 'newuser@gmail.com',
            'name': 'New User',
            'picture': 'https://photo.url/new.jpg',
        }
        mock_get_user.return_value = None  # No existing account

        mock_mgr = MagicMock()
        mock_mgr.user_exists.return_value = False
        mock_mgr.create_user.return_value = 99
        mock_mgr_fn.return_value = mock_mgr

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_issue.return_value = mock_response

        resp = client.post('/api/auth/v2/google', json={
            'id_token': 'valid-token',
        })

        # User created
        mock_mgr.create_user.assert_called_once_with(
            username='newuser',
            email='newuser@gmail.com',
            display_name='New User',
        )

        # Email marked verified (Google pre-verifies)
        mock_set_verified.assert_called_once_with(99)

        # Google provider linked
        mock_add_prov.assert_called_once_with(99, 'google', 'google-456')

        # Tokens issued with is_new_user flag
        mock_issue.assert_called_once()
        call_kwargs = mock_issue.call_args
        assert call_kwargs[1]['extra_data']['is_new_user'] is True
        assert call_kwargs[1]['extra_data']['email_verified'] is True
