"""Tests for auth.jwt_service — JWT access tokens and refresh token utilities."""

import os
import time

import pytest

# Set JWT_SECRET before importing the module
os.environ.setdefault('JWT_SECRET', 'test-secret-do-not-use-in-production-1234')

from auth.jwt_service import JWTService


@pytest.fixture
def svc():
    return JWTService()


class TestAccessToken:
    def test_create_and_verify(self, svc):
        token = svc.create_access_token(user_id=42)
        payload = svc.verify_access_token(token)
        assert payload is not None
        assert payload['sub'] == '42'
        assert payload['type'] == 'access'

    def test_user_id_stored_as_string(self, svc):
        """sub claim is always a string per JWT convention."""
        token = svc.create_access_token(user_id=999)
        payload = svc.verify_access_token(token)
        assert payload['sub'] == '999'

    def test_extra_claims_included(self, svc):
        token = svc.create_access_token(
            user_id=1, extra_claims={'email_verified': True}
        )
        payload = svc.verify_access_token(token)
        assert payload['email_verified'] is True

    def test_invalid_token_returns_none(self, svc):
        assert svc.verify_access_token('garbage.token.here') is None

    def test_tampered_token_returns_none(self, svc):
        token = svc.create_access_token(user_id=1)
        # Flip a character in the signature
        tampered = token[:-1] + ('A' if token[-1] != 'A' else 'B')
        assert svc.verify_access_token(tampered) is None

    def test_wrong_type_rejected(self, svc):
        """A token with type != 'access' should be rejected."""
        import jwt as pyjwt
        payload = {'sub': '1', 'type': 'refresh', 'exp': 9999999999}
        token = pyjwt.encode(
            payload,
            os.environ['JWT_SECRET'],
            algorithm='HS256',
        )
        assert svc.verify_access_token(token) is None

    def test_has_iat_and_exp(self, svc):
        token = svc.create_access_token(user_id=1)
        payload = svc.verify_access_token(token)
        assert 'iat' in payload
        assert 'exp' in payload
        assert payload['exp'] > payload['iat']


class TestRefreshToken:
    def test_create_returns_raw_and_hash(self, svc):
        raw, hashed = svc.create_refresh_token()
        assert len(raw) == 64
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_raw_and_hash_differ(self, svc):
        raw, hashed = svc.create_refresh_token()
        assert raw != hashed

    def test_hash_is_deterministic(self, svc):
        raw, hashed = svc.create_refresh_token()
        assert svc.hash_refresh_token(raw) == hashed

    def test_tokens_are_unique(self, svc):
        tokens = {svc.create_refresh_token()[0] for _ in range(100)}
        assert len(tokens) == 100

    def test_get_refresh_expiry_is_future(self, svc):
        from datetime import datetime, timezone
        expiry = svc.get_refresh_expiry()
        assert expiry > datetime.now(timezone.utc)


class TestMissingSecret:
    def test_raises_without_jwt_secret(self):
        """JWT operations must fail if JWT_SECRET is unset."""
        original = os.environ.pop('JWT_SECRET', None)
        try:
            svc = JWTService()
            with pytest.raises(RuntimeError, match='JWT_SECRET'):
                svc.create_access_token(user_id=1)
        finally:
            if original:
                os.environ['JWT_SECRET'] = original
