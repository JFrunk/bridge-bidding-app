"""Tests for auth.auth_api — register and login endpoints."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from flask import Flask

os.environ.setdefault('JWT_SECRET', 'test-secret-do-not-use-in-production-1234')

from auth.auth_api import register_auth_v2_endpoints


@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    register_auth_v2_endpoints(test_app)
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


# ─── Mocks ──────────────────────────────────────────────────

def _mock_user_manager():
    """Return a mock UserManager with standard behavior."""
    mgr = MagicMock()
    mgr.user_exists.return_value = False
    mgr.create_user.return_value = 42
    mgr.update_last_login.return_value = None
    return mgr


def _make_user_row(overrides=None):
    """Build a realistic user dict as returned by psycopg2 RealDictCursor."""
    base = {
        'id': 42,
        'username': 'testuser',
        'email': 'test@example.com',
        'display_name': 'Test User',
        'password_hash': None,  # Will be set per test
        'email_verified': False,
        'failed_login_attempts': 0,
        'locked_until': None,
    }
    if overrides:
        base.update(overrides)
    return base


# ─── Check Email Tests ──────────────────────────────────────


class TestCheckEmail:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/check-email',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_email(self, client):
        resp = client.post('/api/auth/v2/check-email', json={})
        assert resp.status_code == 400
        assert 'email' in resp.get_json()['error'].lower()

    def test_invalid_email(self, client):
        resp = client.post('/api/auth/v2/check-email', json={
            'email': 'not-an-email',
        })
        assert resp.status_code == 400

    @patch('auth.auth_api._get_user_by_email')
    def test_email_exists(self, mock_get, client):
        mock_get.return_value = _make_user_row()
        resp = client.post('/api/auth/v2/check-email', json={
            'email': 'test@example.com',
        })
        assert resp.status_code == 200
        assert resp.get_json() == {'exists': True}

    @patch('auth.auth_api._get_user_by_email')
    def test_email_does_not_exist(self, mock_get, client):
        mock_get.return_value = None
        resp = client.post('/api/auth/v2/check-email', json={
            'email': 'new@example.com',
        })
        assert resp.status_code == 200
        assert resp.get_json() == {'exists': False}


# ─── Registration Tests ─────────────────────────────────────
class TestRegister:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/register',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_email(self, client):
        resp = client.post('/api/auth/v2/register', json={
            'password': 'GoodPass1',
        })
        assert resp.status_code == 400
        assert 'email' in resp.get_json()['error'].lower()

    def test_invalid_email(self, client):
        resp = client.post('/api/auth/v2/register', json={
            'email': 'not-an-email',
            'password': 'GoodPass1',
        })
        assert resp.status_code == 400

    def test_weak_password_too_short(self, client):
        resp = client.post('/api/auth/v2/register', json={
            'email': 'user@example.com',
            'password': 'Short1',
        })
        assert resp.status_code == 400
        assert 'at least' in resp.get_json()['error'].lower()

    def test_weak_password_no_digit(self, client):
        resp = client.post('/api/auth/v2/register', json={
            'email': 'user@example.com',
            'password': 'NoDigitsHere',
        })
        assert resp.status_code == 400

    def test_common_password(self, client):
        resp = client.post('/api/auth/v2/register', json={
            'email': 'user@example.com',
            'password': 'password1',
        })
        assert resp.status_code == 400
        assert 'common' in resp.get_json()['error'].lower()

    @patch('auth.auth_api._get_user_by_email')
    def test_duplicate_email_returns_409(self, mock_get, client):
        mock_get.return_value = _make_user_row()
        resp = client.post('/api/auth/v2/register', json={
            'email': 'taken@example.com',
            'password': 'GoodPass1',
        })
        assert resp.status_code == 409
        assert 'already exists' in resp.get_json()['error'].lower()

    @patch('auth.auth_api._add_auth_provider')
    @patch('auth.auth_api._set_password_hash')
    @patch('auth.auth_api._store_refresh_token')
    @patch('auth.auth_api._get_user_by_email')
    @patch('auth.auth_api._get_user_manager')
    def test_successful_registration(self, mock_mgr_fn, mock_get,
                                     mock_store, mock_set_pw, mock_add_prov, client):
        mock_get.return_value = None  # No existing user
        mgr = _mock_user_manager()
        mock_mgr_fn.return_value = mgr

        resp = client.post('/api/auth/v2/register', json={
            'email': 'new@example.com',
            'password': 'GoodPass1',
            'display_name': 'New User',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'access_token' in data
        assert data['user_id'] == 42
        assert data['is_new_user'] is True

        # Password was hashed and stored
        mock_set_pw.assert_called_once()
        mock_add_prov.assert_called_once_with(42, 'password')

    @patch('auth.auth_api._migrate_guest_data')
    @patch('auth.auth_api._add_auth_provider')
    @patch('auth.auth_api._set_password_hash')
    @patch('auth.auth_api._store_refresh_token')
    @patch('auth.auth_api._get_user_by_email')
    @patch('auth.auth_api._get_user_manager')
    def test_register_with_guest_promotion(self, mock_mgr_fn, mock_get,
                                           mock_store, mock_set_pw,
                                           mock_add_prov, mock_migrate, client):
        mock_get.return_value = None
        mgr = _mock_user_manager()
        mock_mgr_fn.return_value = mgr
        mock_migrate.return_value = {'game_sessions': 3, 'bidding_decisions': 12}

        resp = client.post('/api/auth/v2/register', json={
            'email': 'guest@example.com',
            'password': 'GoodPass1',
            'guest_id': -987654321,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['migrated_from_guest'] is True
        assert data['migrated_data']['game_sessions'] == 3
        mock_migrate.assert_called_once_with(42, -987654321)


# ─── Login Tests ─────────────────────────────────────────────


class TestLogin:
    def test_missing_body(self, client):
        resp = client.post('/api/auth/v2/login',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_missing_email(self, client):
        resp = client.post('/api/auth/v2/login', json={
            'password': 'GoodPass1',
        })
        assert resp.status_code == 401

    def test_missing_password(self, client):
        resp = client.post('/api/auth/v2/login', json={
            'email': 'test@example.com',
        })
        assert resp.status_code == 401

    @patch('auth.auth_api._get_user_by_email')
    def test_nonexistent_email_returns_401(self, mock_get, client):
        """No user enumeration — same error for missing and wrong password."""
        mock_get.return_value = None
        resp = client.post('/api/auth/v2/login', json={
            'email': 'nobody@example.com',
            'password': 'GoodPass1',
        })
        assert resp.status_code == 401
        assert 'Invalid email or password' in resp.get_json()['error']

    @patch('auth.auth_api._record_failed_login')
    @patch('auth.auth_api._get_user_by_email')
    def test_wrong_password_returns_401(self, mock_get, mock_record, client):
        from auth.auth_service import AuthService
        svc = AuthService()
        user = _make_user_row({
            'password_hash': svc.hash_password('CorrectPass1'),
        })
        mock_get.return_value = user

        resp = client.post('/api/auth/v2/login', json={
            'email': 'test@example.com',
            'password': 'WrongPass1',
        })
        assert resp.status_code == 401
        assert 'Invalid email or password' in resp.get_json()['error']
        mock_record.assert_called_once_with(42)

    @patch('auth.auth_api._get_user_by_email')
    def test_locked_account_returns_429(self, mock_get, client):
        user = _make_user_row({
            'password_hash': 'some_hash',
            'locked_until': datetime.now(timezone.utc) + timedelta(minutes=10),
        })
        mock_get.return_value = user

        resp = client.post('/api/auth/v2/login', json={
            'email': 'test@example.com',
            'password': 'GoodPass1',
        })
        assert resp.status_code == 429
        assert 'locked' in resp.get_json()['error'].lower()

    @patch('auth.auth_api._get_user_by_email')
    def test_expired_lockout_allows_login_attempt(self, mock_get, client):
        """Lockout that expired should not block — but wrong password still fails."""
        from auth.auth_service import AuthService
        user = _make_user_row({
            'password_hash': AuthService().hash_password('CorrectPass1'),
            'locked_until': datetime.now(timezone.utc) - timedelta(minutes=1),
            'failed_login_attempts': 5,
        })
        mock_get.return_value = user

        with patch('auth.auth_api._record_failed_login'):
            resp = client.post('/api/auth/v2/login', json={
                'email': 'test@example.com',
                'password': 'WrongPass1',
            })
            # Not 429 — lockout expired, so attempt proceeds (and fails on wrong pw)
            assert resp.status_code == 401

    @patch('auth.auth_api._get_user_by_email')
    def test_legacy_user_no_password(self, mock_get, client):
        """Users from simple-login era have no password_hash."""
        user = _make_user_row({'password_hash': None})
        mock_get.return_value = user

        resp = client.post('/api/auth/v2/login', json={
            'email': 'test@example.com',
            'password': 'GoodPass1',
        })
        assert resp.status_code == 401
        assert 'magic link' in resp.get_json()['error'].lower()

    @patch('auth.auth_api._get_user_manager')
    @patch('auth.auth_api._clear_failed_logins')
    @patch('auth.auth_api._store_refresh_token')
    @patch('auth.auth_api._get_user_by_email')
    def test_successful_login(self, mock_get, mock_store,
                              mock_clear, mock_mgr_fn, client):
        from auth.auth_service import AuthService
        svc = AuthService()
        user = _make_user_row({
            'password_hash': svc.hash_password('CorrectPass1'),
        })
        mock_get.return_value = user
        mock_mgr_fn.return_value = _mock_user_manager()

        resp = client.post('/api/auth/v2/login', json={
            'email': 'test@example.com',
            'password': 'CorrectPass1',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'access_token' in data
        assert data['user_id'] == 42
        mock_clear.assert_called_once_with(42)


class TestLoginLockoutOrder:
    """Verify lockout check happens BEFORE argon2 verify."""

    @patch('auth.auth_api._auth_svc')
    @patch('auth.auth_api._get_user_by_email')
    def test_locked_account_skips_hash_verify(self, mock_get, mock_svc, client):
        user = _make_user_row({
            'password_hash': 'some_hash',
            'locked_until': datetime.now(timezone.utc) + timedelta(minutes=10),
        })
        mock_get.return_value = user

        resp = client.post('/api/auth/v2/login', json={
            'email': 'test@example.com',
            'password': 'anything',
        })
        assert resp.status_code == 429
        # verify_password should NOT have been called
        mock_svc.verify_password.assert_not_called()
