"""
JWT Service — Access and refresh token management.

Per AUTH_PRD §3.1:
- Access token: JWT, 15-minute expiry, stored in memory (not localStorage)
- Refresh token: opaque, 30-day expiry, HttpOnly secure cookie
- Refresh tokens are SHA-256 hashed before storage in refresh_tokens table

Usage:
    from auth.jwt_service import JWTService

    jwt_svc = JWTService()
    access = jwt_svc.create_access_token(user_id=42)
    payload = jwt_svc.verify_access_token(access)

    raw, hashed = jwt_svc.create_refresh_token()
    # Store `hashed` in DB, send `raw` as HttpOnly cookie
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt

# Defaults per PRD — override via environment variables
ACCESS_TOKEN_EXPIRY_MINUTES = int(os.environ.get('JWT_ACCESS_EXPIRY_MINUTES', '15'))
REFRESH_TOKEN_EXPIRY_DAYS = int(os.environ.get('JWT_REFRESH_EXPIRY_DAYS', '30'))
JWT_ALGORITHM = 'HS256'


def _get_secret() -> str:
    """Load JWT secret from environment. Fails fast if missing."""
    secret = os.environ.get('JWT_SECRET')
    if not secret:
        raise RuntimeError(
            'JWT_SECRET environment variable is required. '
            'Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"'
        )
    return secret


class JWTService:
    """Stateless JWT service. Safe to use as a singleton."""

    def create_access_token(self, user_id: int, extra_claims: dict | None = None) -> str:
        """
        Create a short-lived JWT access token.

        Args:
            user_id: The authenticated user's ID.
            extra_claims: Optional additional claims (e.g. email_verified).

        Returns:
            Encoded JWT string.
        """
        now = datetime.now(timezone.utc)
        payload = {
            'sub': str(user_id),
            'iat': now,
            'exp': now + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES),
            'type': 'access',
        }
        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)

    def verify_access_token(self, token: str) -> dict | None:
        """
        Decode and verify a JWT access token.

        Returns:
            The decoded payload dict if valid, None if invalid/expired.
        """
        try:
            payload = jwt.decode(
                token, _get_secret(), algorithms=[JWT_ALGORITHM]
            )
            if payload.get('type') != 'access':
                return None
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    def create_refresh_token(self) -> tuple[str, str]:
        """
        Generate a cryptographically secure refresh token.

        Returns:
            Tuple of (raw_token, token_hash).
            - raw_token: sent to client as HttpOnly cookie
            - token_hash: stored in refresh_tokens table (SHA-256)
        """
        raw = secrets.token_urlsafe(48)  # 64 chars base64url
        hashed = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        return raw, hashed

    def hash_refresh_token(self, raw_token: str) -> str:
        """Hash a raw refresh token for DB lookup."""
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    def get_refresh_expiry(self) -> datetime:
        """Return the expiry datetime for a new refresh token."""
        return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
