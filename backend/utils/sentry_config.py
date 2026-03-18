"""Sentry error tracking configuration for Flask backend.

Initializes Sentry with filtering to stay within free tier limits:
- 5,000 errors/month, 10,000 performance spans/month
- Filters out noise: 404s, rate limits, client disconnects, health checks
"""
import os
import sentry_sdk


# Errors to drop (noise, not bugs)
IGNORED_EXCEPTIONS = (
    ConnectionResetError,
    BrokenPipeError,
    ConnectionAbortedError,
    KeyboardInterrupt,
)

# Endpoints that generate transactions but aren't worth tracking
IGNORED_TRANSACTION_PATTERNS = (
    '/health',
    '/api/dds-health',
    '/api/dds-test',
    '/api/ai/status',
    '/favicon.ico',
)


def _before_send(event, hint):
    """Filter out noisy errors before sending to Sentry."""
    if 'exc_info' in hint:
        exc_type = hint['exc_info'][0]

        # Drop client disconnect / keyboard interrupt noise
        if exc_type in IGNORED_EXCEPTIONS:
            return None

        # Drop 404s (bots, scanners)
        from werkzeug.exceptions import NotFound
        if issubclass(exc_type, NotFound):
            return None

        # Drop rate limit exceeded (working as intended)
        from werkzeug.exceptions import TooManyRequests
        if issubclass(exc_type, TooManyRequests):
            return None

    return event


def _before_send_transaction(event, hint):
    """Filter out health check and monitoring transactions."""
    transaction_name = event.get('transaction', '')
    for pattern in IGNORED_TRANSACTION_PATTERNS:
        if pattern in transaction_name:
            return None
    return event


def init_sentry():
    """Initialize Sentry SDK. Call before Flask app creation."""
    dsn = os.environ.get('SENTRY_DSN_BACKEND')
    if not dsn:
        print("ℹ️  Sentry DSN not configured — error tracking disabled")
        print("   Set SENTRY_DSN_BACKEND in .env to enable")
        return

    sentry_sdk.init(
        dsn=dsn,
        # Performance: 10% sampling to stay within 10K spans/month
        traces_sample_rate=0.1,
        # Capture all errors (5K/month is plenty for our traffic)
        # Reduce to 0.5 if quota is exceeded
        sample_rate=1.0,
        # Filter noise
        before_send=_before_send,
        before_send_transaction=_before_send_transaction,
        # Send request headers and IP for debugging context
        send_default_pii=True,
        # Tag release for tracking deploys
        release=os.environ.get('SENTRY_RELEASE'),
        environment=os.environ.get('FLASK_ENV', 'development'),
    )
    print("✅ Sentry error tracking initialized")
