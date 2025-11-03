# Quick Fix: Production Database Error

## The Problem
```
Failed to load dashboard: no such table: bidding_decisions
```

## The Solution (5 minutes)

### Step 1: Access Production Server
```bash
# Option A: SSH
ssh your-production-server

# Option B: Render.com
# Go to Render Dashboard → Your Service → Shell
```

### Step 2: Run Database Migration
```bash
cd /path/to/bridge_bidding_app/backend
python3 database/init_all_tables.py
```

### Step 3: Verify Success
Look for this output:
```
✅ Tables (18):
   - bidding_decisions              (0 rows)
   ...
🔍 Verifying critical tables...
   ✅ bidding_decisions

✅ Database initialization complete!
```

### Step 4: Restart Service
```bash
# Render: Use dashboard to restart
# SSH: Restart your service (systemd, supervisor, etc.)
```

### Step 5: Test
- Login to your app
- Play a hand
- Click "My Progress"
- Should load without errors ✅

---

## Files Created

1. **`/backend/database/init_all_tables.py`** - Main migration script
2. **`PRODUCTION_DATABASE_FIX.md`** - Full documentation
3. This quick guide

## What It Does

Safely adds missing database tables:
- `bidding_decisions` (main table for dashboard)
- `hand_analyses` (future use)
- 3 views for statistics

**Safe to run multiple times** - uses `CREATE IF NOT EXISTS`

---

## Need Help?

See [PRODUCTION_DATABASE_FIX.md](PRODUCTION_DATABASE_FIX.md) for:
- Detailed troubleshooting
- Alternative deployment methods
- Rollback instructions
- Testing procedures

---

**Status:** Ready to deploy
**Time to fix:** ~5 minutes
**Risk level:** Low (backward compatible, no data changes)
