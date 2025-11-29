# Server Domain Documentation

**Specialist:** `/server-specialist`
**Code:** `backend/server.py`, `backend/core/`, `backend/database/`
**CLAUDE.md:** `backend/CLAUDE.md`

## Overview

This domain covers the Flask server and infrastructure including:
- Flask REST API (server.py ~2,600 lines)
- Session management and state isolation
- Authentication (email/phone login)
- Database management (SQLite)
- Testing infrastructure
- Deployment to Render

## Quick Links

- [Backend CLAUDE.md](../../../backend/CLAUDE.md) - Architecture overview
- [Deployment Guide](features/DEPLOYMENT_GUIDE.md) - Deployment instructions
- [Session Isolation](features/TEST_SESSION_ISOLATION.md) - Session testing

## Features

### Deployment
- [DEPLOYMENT.md](features/DEPLOYMENT.md) - Main deployment docs
- [DEPLOYMENT_GUIDE.md](features/DEPLOYMENT_GUIDE.md) - Step-by-step guide
- [DEPLOYMENT_CONTEXT.md](features/DEPLOYMENT_CONTEXT.md) - Context and requirements
- [DEPLOYMENT_NOTES.md](features/DEPLOYMENT_NOTES.md) - Deployment notes
- [PRODUCTION_DEPLOYMENT_GUIDE.md](features/PRODUCTION_DEPLOYMENT_GUIDE.md) - Production guide
- [DEPLOY_TO_PRODUCTION.md](features/DEPLOY_TO_PRODUCTION.md) - Deploy checklist
- [DEPLOY_FRONTEND_NOW.md](features/DEPLOY_FRONTEND_NOW.md) - Frontend deployment
- [RENDER_POSTGRESQL_SETUP.md](features/RENDER_POSTGRESQL_SETUP.md) - PostgreSQL setup

### Server Operations
- [START_APP.md](features/START_APP.md) - Starting the application
- [ERROR_LOGGING_PRODUCTION.md](features/ERROR_LOGGING_PRODUCTION.md) - Production logging
- [TEST_SESSION_ISOLATION.md](features/TEST_SESSION_ISOLATION.md) - Session isolation testing

### Security
- [PASSWORD_PROTECTION_OPTIONS.md](features/PASSWORD_PROTECTION_OPTIONS.md) - Auth options

## Bug Fixes

### Session Issues
- [DECLARER_DETERMINATION_BUG_2025-11-28.md](bug-fixes/DECLARER_DETERMINATION_BUG_2025-11-28.md) - **NEW** Jacoby Transfer declarer bug
- [SESSION_PERSISTENCE_FIX_2025-10-23.md](bug-fixes/SESSION_PERSISTENCE_FIX_2025-10-23.md) - Persistence fix
- [MULTI_USER_SESSION_FIXES_COMPLETE.md](bug-fixes/MULTI_USER_SESSION_FIXES_COMPLETE.md) - Multi-user fixes
- [STALE_DEALER_CLOSURE_FIX.md](bug-fixes/STALE_DEALER_CLOSURE_FIX.md) - Stale closure fix
- [PLAYER_ROTATION_STALE_STATE_BUG_10292025.md](bug-fixes/PLAYER_ROTATION_STALE_STATE_BUG_10292025.md) - Rotation state
- [QUICK_START_SESSION_FIX.md](bug-fixes/QUICK_START_SESSION_FIX.md) - Quick fix guide

### Production Issues
- [PRODUCTION_ISSUES_FIX_2025-10-23.md](bug-fixes/PRODUCTION_ISSUES_FIX_2025-10-23.md) - October fixes
- [PRODUCTION_BUGS_AND_TEST_PLAN.md](bug-fixes/PRODUCTION_BUGS_AND_TEST_PLAN.md) - Bug tracking
- [PRODUCTION_CONNECTION_FIX.md](bug-fixes/PRODUCTION_CONNECTION_FIX.md) - Connection fix
- [PRODUCTION_DATABASE_FIX.md](bug-fixes/PRODUCTION_DATABASE_FIX.md) - Database fix
- [PRODUCTION_FIX_QUICK_GUIDE.md](bug-fixes/PRODUCTION_FIX_QUICK_GUIDE.md) - Quick guide
- [LOCAL_VS_PRODUCTION_FIX.md](bug-fixes/LOCAL_VS_PRODUCTION_FIX.md) - Environment issues

### Deployment Issues
- [RENDER_DEPLOY_FIX_2025-10-24.md](bug-fixes/RENDER_DEPLOY_FIX_2025-10-24.md) - Render fix
- [DEBUG_CONNECTION_ISSUE.md](bug-fixes/DEBUG_CONNECTION_ISSUE.md) - Connection debugging

### Authentication
- [SIMPLELOGIN_IMPORT_FIX.md](bug-fixes/SIMPLELOGIN_IMPORT_FIX.md) - Import fix
- [SIMPLE_LOGIN_ENDPOINT_MISSING.md](bug-fixes/SIMPLE_LOGIN_ENDPOINT_MISSING.md) - Missing endpoint

### Performance
- [PERFORMANCE_BUG_FIX_2025-11-01.md](bug-fixes/PERFORMANCE_BUG_FIX_2025-11-01.md) - Performance fix

## Related Domains

- **Bidding:** Server calls BiddingEngine for AI bids and evaluation
- **Play:** Server calls PlayEngine for card play execution
- **Learning:** Server queries analytics for dashboard data
- **Frontend:** Server provides REST API endpoints

## Adding Documentation

All new server documentation MUST be placed in this directory:
- **Features/enhancements:** `docs/domains/server/features/`
- **Bug fixes:** `docs/domains/server/bug-fixes/`
- **Architecture decisions:** `docs/domains/server/architecture/`
