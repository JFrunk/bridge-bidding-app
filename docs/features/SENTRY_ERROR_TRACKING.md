# Sentry Error Tracking

**Added:** 2026-03-18
**Plan:** Free (Developer) tier
**Dashboard:** https://sentry.io

## Overview

Sentry captures production errors in real-time from both the Flask backend and React frontend. Errors appear in the Sentry dashboard with full stack traces, request context, and user session data. Email alerts notify when new errors occur.

The existing `error_logger` (local JSONL logs) is retained as a local audit trail. Sentry is for real-time alerting and aggregation.

## Architecture

```
Backend (Flask)                    Frontend (React)
  sentry-sdk[flask]                  @sentry/react
       │                                  │
       ├─ Auto-captures Flask errors  ├─ Unhandled JS errors
       ├─ ValueError, TypeError       ├─ React ErrorBoundary crashes
       ├─ DB constraint violations     ├─ API fetch failures (5xx)
       └─ 10% perf traces             └─ 10% perf traces
       │                                  │
       └───────── sentry.io ──────────────┘
              (2 projects: Flask + React)
```

## Configuration

### Backend
- Config: `backend/utils/sentry_config.py`
- Init: Called in `server.py` before Flask app creation
- DSN env var: `SENTRY_DSN_BACKEND`

### Frontend
- Config: `frontend/src/utils/sentryConfig.js`
- Init: Called in `index.js` before React renders
- Error Boundary: Wraps `<App />` in `App.js` via `Sentry.ErrorBoundary`
- DSN env var: `REACT_APP_SENTRY_DSN`
- Production DSN: Set in `frontend/.env.production`

## Free Tier Limits

| Resource | Limit | Our Usage |
|----------|-------|-----------|
| Errors | 5,000/month | Low traffic — well within limit |
| Performance spans | 10,000/month | 10% sampling keeps this low |
| Session replays | 50/month | Only recorded on error |
| Data retention | ~30 days | Sufficient for debugging |

## Filtering (Staying Within Quota)

### Backend (`before_send`)
Drops:
- `ConnectionResetError`, `BrokenPipeError` (client disconnects)
- 404s (bots/scanners)
- Rate limit exceeded (429 — working as intended)

### Backend (`before_send_transaction`)
Drops transactions for:
- `/health`, `/api/dds-health`, `/api/dds-test`, `/api/ai/status`, `/favicon.ico`

### Frontend (`ignoreErrors`)
Drops:
- `ResizeObserver loop limit exceeded`
- `Failed to fetch`, `NetworkError`, `Load failed`
- Chunk loading failures (stale cache)

### Frontend (`denyUrls`)
Ignores errors from browser extensions (`chrome-extension://`, `moz-extension://`).

## Sampling Rates

| Type | Rate | Rationale |
|------|------|-----------|
| Errors | 100% | Capture all real bugs (5K/month is plenty) |
| Performance traces | 10% | Conserve 10K span budget |
| Session replays (normal) | 0% | Don't waste replay budget |
| Session replays (on error) | 100% | Record session when error occurs |

## Environment Variables

### Backend (`backend/.env`)
```
SENTRY_DSN_BACKEND=https://...@o123.ingest.us.sentry.io/456
```

### Frontend (`frontend/.env.production`)
```
REACT_APP_SENTRY_DSN=https://...@o123.ingest.us.sentry.io/789
```

Leaving either DSN unset disables Sentry for that layer (graceful degradation).

## Sentry Dashboard Tips

- **Set per-key rate limits** in Settings > Client Keys > Rate Limiting (e.g., 500 errors/hour) to prevent a bad deploy from exhausting the monthly quota
- **Check Usage Stats** weekly during initial rollout
- **Enable email alerts** for new issues (on by default)
