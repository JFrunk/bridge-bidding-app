# Render PostgreSQL Setup Guide

## Overview

The Bridge Bidding App uses a database abstraction layer that supports both SQLite (local development) and PostgreSQL (production on Render). This enables persistent data storage in production.

## How It Works

### Database Abstraction Layer

The `backend/db.py` module automatically detects the environment:
- **Local development**: Uses SQLite (`backend/bridge.db`)
- **Production (Render)**: Uses PostgreSQL via `DATABASE_URL` environment variable

Key features:
- Automatic SQL placeholder conversion (`?` → `%s` for PostgreSQL)
- Row factory wrapper for consistent dict-like row access
- Connection wrapper for unified interface

### Files Modified

1. **backend/db.py** - Database abstraction layer (NEW)
2. **backend/requirements.txt** - Added `psycopg2-binary>=2.9.9`
3. **backend/database/schema_postgresql.sql** - PostgreSQL schema (NEW)
4. **render.yaml** - PostgreSQL database configuration
5. **backend/server.py** - Uses `get_connection()` instead of `sqlite3.connect()`
6. Multiple engine files - Updated to use abstraction layer

## Deployment Steps

### 1. First-Time Setup on Render

The `render.yaml` blueprint automatically:
- Creates a PostgreSQL database (`bridge-bidding-db`, Starter plan, $7/month)
- Passes `DATABASE_URL` to the backend service
- Runs database initialization before starting gunicorn

### 2. Deploy via Git Push

```bash
# Commit all changes
git add .
git commit -m "Add PostgreSQL support for Render deployment"

# Push to trigger deployment
git push origin main
```

### 3. Verify Deployment

After deployment, check the Render dashboard:
1. Verify the database service is running
2. Check backend logs for: `Database: PostgreSQL (from DATABASE_URL)`
3. Test the app to ensure data persists across deploys

## Local Development

Local development continues to use SQLite:

```bash
cd backend
source venv/bin/activate
python server.py
# Output: Database: SQLite (backend/bridge.db)
```

## Database Schema

The PostgreSQL schema is in `backend/database/schema_postgresql.sql`. It includes:
- All user management tables
- Game session and scoring tables
- Convention learning tables
- Bidding feedback tables
- Seed data for error categories and celebration templates

## Troubleshooting

### Import Errors
If you see `NameError: name 'sqlite3' is not defined`, a file is still using `sqlite3.Cursor` or `sqlite3.Row` type hints. Replace with `Any` from typing.

### Database Connection Issues
Check the `DATABASE_URL` environment variable in Render settings. It should be automatically populated from the database reference.

### Missing Tables
The schema is initialized on first deploy via the start command:
```
python -c 'from db import init_database; init_database()'
```

## Cost

- PostgreSQL Starter plan: $7/month
- Includes 1GB storage, automatic backups
