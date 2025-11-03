# Production Database Fix - Missing `bidding_decisions` Table

**Issue:** Production error when clicking "My Progress" button after gameplay:
```
Failed to load dashboard: no such table: bidding_decisions
```

**Root Cause:** The production database was not updated with the Phase 1 bidding feedback migration that adds the `bidding_decisions` table and related views.

**Status:** ⚠️ NEEDS DEPLOYMENT

---

## Quick Fix (For Production)

### Option 1: Run Database Initialization Script (Recommended)

This script is safe to run on existing databases - it uses `CREATE IF NOT EXISTS`.

```bash
# SSH into production server
ssh your-production-server

# Navigate to app directory
cd /path/to/bridge_bidding_app/backend

# Run database initialization
python3 database/init_all_tables.py

# Verify tables were created
sqlite3 bridge.db ".tables" | grep bidding_decisions
```

**Expected output:**
```
✅ Tables (18):
   - bidding_decisions              (0 rows)
   - hand_analyses                  (0 rows)
   ...
   ✅ bidding_decisions
```

### Option 2: Manual SQL Migration

If you prefer to run the migration manually:

```bash
# SSH into production server
ssh your-production-server

# Navigate to backend directory
cd /path/to/bridge_bidding_app/backend

# Apply migration
sqlite3 bridge.db < migrations/001_add_bidding_feedback_tables.sql

# Verify
sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE name='bidding_decisions';"
```

### Option 3: Using Render.com Shell (If deployed on Render)

```bash
# From Render dashboard, open Shell for your service

cd backend

# Run initialization script
python3 database/init_all_tables.py

# Restart the service
# (Use Render dashboard to restart)
```

---

## What Gets Created

The migration adds these tables and views:

### Tables
1. **`bidding_decisions`** - Stores detailed feedback for every bidding decision
   - Tracks user bids vs optimal bids
   - Records correctness, score, error categories
   - Links to sessions for dashboard display

2. **`hand_analyses`** - Placeholder for future post-hand analysis
   - Stores comprehensive hand analysis
   - Links to bidding decisions

### Views
1. **`v_bidding_feedback_stats`** - Aggregate statistics for dashboard
2. **`v_recent_bidding_decisions`** - Recent decisions for display
3. **`v_concept_mastery`** - Concept-level tracking

### Indexes
- Performance indexes on user_id, timestamp, correctness, categories

---

## Verification Steps

After running the migration, verify it worked:

```bash
# 1. Check table exists
sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE name='bidding_decisions';"

# 2. Check table structure
sqlite3 bridge.db "PRAGMA table_info(bidding_decisions);"

# 3. Check views exist
sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%bidding%';"

# 4. Test query (should return 0 initially)
sqlite3 bridge.db "SELECT COUNT(*) FROM bidding_decisions;"
```

---

## Testing After Deployment

1. **Backend Test:**
   ```bash
   curl http://your-production-url/api/analytics/dashboard
   ```
   Should return JSON without errors (may be empty initially)

2. **Frontend Test:**
   - Login to the app
   - Play a hand
   - Click "My Progress" button
   - Dashboard should load without errors

---

## Files Involved

### Created
- `/backend/database/init_all_tables.py` - **NEW** comprehensive database initialization script
- This document

### Existing
- `/backend/migrations/001_add_bidding_feedback_tables.sql` - The migration SQL
- `/backend/database/schema_user_management.sql` - User tables
- `/backend/database/schema_game_sessions.sql` - Session tables
- `/backend/database/schema_convention_levels.sql` - Convention tables

---

## Production Deployment Checklist

- [ ] SSH into production server (or open Render shell)
- [ ] Navigate to backend directory
- [ ] Run `python3 database/init_all_tables.py`
- [ ] Verify output shows ✅ for all critical tables
- [ ] Verify `bidding_decisions` table exists
- [ ] Restart backend service
- [ ] Test "My Progress" button in production
- [ ] Verify no "no such table" errors

---

## Prevention (For Future Deployments)

### Add to Deployment Script

Add this to your deployment process:

```bash
#!/bin/bash
# deploy.sh

echo "Deploying Bridge Bidding App..."

# Pull latest code
git pull origin main

# Run database migrations
cd backend
python3 database/init_all_tables.py

# Install dependencies
pip install -r requirements.txt

# Restart services
# (Your restart command here)
```

### Render.com Build Command

If using Render, update your build command:

```bash
pip install -r backend/requirements.txt && python3 backend/database/init_all_tables.py
```

### Docker Support

If using Docker, add to your Dockerfile:

```dockerfile
# After copying files
COPY backend/ /app/backend/

# Initialize database on container start
RUN python3 /app/backend/database/init_all_tables.py
```

---

## Rollback Plan

If something goes wrong, the migration is safe to rollback:

```bash
# Backup database first
cp bridge.db bridge.db.backup

# If needed, drop the new tables
sqlite3 bridge.db "DROP TABLE IF EXISTS bidding_decisions;"
sqlite3 bridge.db "DROP TABLE IF EXISTS hand_analyses;"
sqlite3 bridge.db "DROP VIEW IF EXISTS v_bidding_feedback_stats;"
sqlite3 bridge.db "DROP VIEW IF EXISTS v_recent_bidding_decisions;"
sqlite3 bridge.db "DROP VIEW IF EXISTS v_concept_mastery;"

# Restore from backup
cp bridge.db.backup bridge.db
```

---

## Notes

- The migration is **backward compatible** - it doesn't modify existing tables
- Safe to run multiple times (uses `CREATE IF NOT EXISTS`)
- No data will be lost
- The `bidding_decisions` table will be empty initially and populate as users play hands

---

## Related Issues

- **BUG-V008:** Dashboard Does Not Show Up - Resolved with this fix
- **FEATURE-001:** Update Gameplay Statistics - Depends on this migration

---

## Support

If you encounter issues:

1. Check the logs for specific SQL errors
2. Verify the migration file is present in production
3. Ensure SQLite is accessible and writable
4. Check file permissions on bridge.db

**Created:** 2025-10-18
**Status:** Ready for production deployment
