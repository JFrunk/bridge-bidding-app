"""Tests for auth.auth_service — password hashing and validation."""

import pytest
from auth.auth_service import (
    AuthService,
    PasswordTooShortError,
    PasswordTooCommonError,
    PasswordMissingLetterError,
    PasswordMissingDigitError,
)


@pytest.fixture
def svc():
    return AuthService()


class TestPasswordHashing:
    def test_hash_returns_argon2_string(self, svc):
        h = svc.hash_password("SecurePass1")
        assert h.startswith("$argon2id$")

    def test_same_password_different_hashes(self, svc):
        """Argon2 uses a random salt — hashes must differ."""
        h1 = svc.hash_password("SecurePass1")
        h2 = svc.hash_password("SecurePass1")
        assert h1 != h2

    def test_verify_correct_password(self, svc):
        h = svc.hash_password("SecurePass1")
        assert svc.verify_password("SecurePass1", h) is True

    def test_verify_wrong_password(self, svc):
        h = svc.hash_password("SecurePass1")
        assert svc.verify_password("WrongPass1", h) is False

    def test_verify_invalid_hash(self, svc):
        assert svc.verify_password("anything", "not_a_real_hash") is False

    def test_needs_rehash_fresh_hash(self, svc):
        h = svc.hash_password("SecurePass1")
        assert svc.needs_rehash(h) is False


class TestPasswordValidation:
    def test_valid_password(self, svc):
        svc.validate_password("GoodPass42")  # Should not raise

    def test_too_short(self, svc):
        with pytest.raises(PasswordTooShortError):
            svc.validate_password("Short1")

    def test_no_letter(self, svc):
        with pytest.raises(PasswordMissingLetterError):
            svc.validate_password("12345678")

    def test_no_digit(self, svc):
        with pytest.raises(PasswordMissingDigitError):
            svc.validate_password("NoDigitsHere")

    def test_common_password(self, svc):
        with pytest.raises(PasswordTooCommonError):
            svc.validate_password("password1")

    def test_common_password_case_insensitive(self, svc):
        with pytest.raises(PasswordTooCommonError):
            svc.validate_password("Password1")

    def test_exactly_8_chars_valid(self, svc):
        svc.validate_password("Valid1ab")  # Exactly min length


class TestTokenUtilities:
    def test_generate_token_length(self, svc):
        token = svc.generate_token()
        assert len(token) == 64

    def test_generate_token_unique(self, svc):
        tokens = {svc.generate_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_hash_token_deterministic(self, svc):
        token = "test_token_value"
        h1 = svc.hash_token(token)
        h2 = svc.hash_token(token)
        assert h1 == h2

    def test_hash_token_is_hex(self, svc):
        h = svc.hash_token("test")
        assert len(h) == 64  # SHA-256 hex digest
        assert all(c in '0123456789abcdef' for c in h)
