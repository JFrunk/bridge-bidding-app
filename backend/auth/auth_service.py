"""
Auth Service — Core authentication utilities.

Phase 1: Password hashing with argon2id.
Future phases will add JWT, Google OAuth, and Magic Link.

Usage:
    from auth.auth_service import AuthService

    service = AuthService()
    hashed = service.hash_password("user_password")
    is_valid = service.verify_password("user_password", hashed)
"""

import hashlib
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError


# Argon2id with argon2-cffi defaults (RFC 9106 recommendations):
#   time_cost=3, memory_cost=65536 (64 MiB), parallelism=4
_hasher = PasswordHasher()

# Top-10k common passwords — reject these server-side.
# Loaded lazily on first check to avoid startup cost.
_common_passwords: set | None = None
_COMMON_PASSWORDS_PATH = None  # Set via configure() or falls back to bundled list

# Minimum password requirements (per PRD §3.1)
MIN_PASSWORD_LENGTH = 8


class PasswordTooShortError(ValueError):
    pass


class PasswordTooCommonError(ValueError):
    pass


class PasswordMissingLetterError(ValueError):
    pass


class PasswordMissingDigitError(ValueError):
    pass


class AuthService:
    """Core authentication service. Stateless — safe to use as a singleton."""

    def hash_password(self, password: str) -> str:
        """
        Hash a password using argon2id.

        Args:
            password: Plaintext password (must pass validate_password first).

        Returns:
            Argon2id hash string (includes algorithm, salt, and params).
        """
        return _hasher.hash(password)

    def verify_password(self, password: str, hash: str) -> bool:
        """
        Verify a password against a stored argon2id hash.

        Returns True if the password matches, False otherwise.
        Never raises on mismatch — callers get a bool.
        """
        try:
            return _hasher.verify(hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, hash: str) -> bool:
        """
        Check if a hash was created with outdated parameters.

        Call after successful verification. If True, re-hash and store
        the new hash to keep security parameters current.
        """
        return _hasher.check_needs_rehash(hash)

    def validate_password(self, password: str) -> None:
        """
        Validate password strength per PRD requirements.

        Raises:
            PasswordTooShortError: Less than 8 characters.
            PasswordMissingLetterError: No letter.
            PasswordMissingDigitError: No digit.
            PasswordTooCommonError: In top-10k common passwords.
        """
        if len(password) < MIN_PASSWORD_LENGTH:
            raise PasswordTooShortError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
            )
        if not any(c.isalpha() for c in password):
            raise PasswordMissingLetterError(
                "Password must contain at least one letter"
            )
        if not any(c.isdigit() for c in password):
            raise PasswordMissingDigitError(
                "Password must contain at least one number"
            )
        if self._is_common_password(password):
            raise PasswordTooCommonError(
                "This password is too common. Please choose a different one"
            )

    def hash_token(self, token: str) -> str:
        """
        Hash a token (magic link, reset, verification) with SHA-256.

        Tokens are single-use and short-lived, so SHA-256 is appropriate
        (no need for slow hashing like argon2). Stored in auth_tokens table.
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def generate_token(self) -> str:
        """
        Generate a cryptographically secure random token (64 chars).

        Used for magic links, email verification, and password reset.
        The raw token is sent to the user; only the SHA-256 hash is stored.
        """
        return secrets.token_urlsafe(48)  # 48 bytes = 64 chars base64url

    @staticmethod
    def _is_common_password(password: str) -> bool:
        """Check password against top-10k common passwords list."""
        global _common_passwords
        if _common_passwords is None:
            _common_passwords = _load_common_passwords()
        return password.lower() in _common_passwords


def _load_common_passwords() -> set:
    """
    Load common passwords set. Falls back to a minimal built-in set
    if no external file is configured.
    """
    if _COMMON_PASSWORDS_PATH:
        try:
            with open(_COMMON_PASSWORDS_PATH, 'r') as f:
                return {line.strip().lower() for line in f if line.strip()}
        except FileNotFoundError:
            pass

    # Minimal built-in set covering the absolute worst offenders.
    # Replace with a full 10k list file for production.
    return {
        'password', 'password1', '123456', '12345678', '123456789',
        '1234567890', 'qwerty', 'abc123', 'monkey', 'letmein',
        'dragon', 'master', 'login', 'princess', 'welcome',
        'shadow', 'sunshine', 'trustno1', 'iloveyou', 'batman',
        'football', 'baseball', 'soccer', 'hockey', 'jordan',
        'ranger', 'buster', 'thomas', 'robert', 'tigger',
        'passw0rd', 'qwerty123', 'password123', 'admin', 'admin123',
        '123123', '111111', '654321', 'abcdef', 'access',
    }
