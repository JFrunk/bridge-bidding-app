# Deploy to Production - Step-by-Step Guide
**Date:** 2025-10-19
**Purpose:** Deploy database fixes and latest code to production
**Status:** Ready to Execute

---

## Pre-Deployment Status

### Current State
- **Production (`origin/main`):** At commit `41aca99` (Oct 17)
  - Has Phase 1 bidding feedback CODE
  - MISSING bidding feedback DATABASE TABLES
  - Dashboard is broken ("no such table: bidding_decisions")

- **Development (`origin/development`):** At commit `55fd0e8` (Oct 18)
  - Has critical bug fixes and AI enhancements
  - Database migration exists but not applied to production
  - One commit ahead of production

### What's Being Deployed
1. Database migration (bidding_decisions table + views)
2. Latest code fixes from development branch
3. Dealer rotation fixes

---

## Step 1: Apply Database Migration to Production

### Option A: Render.com (If using Render)

1. **Open Render Dashboard**
   - Go to https://dashboard.render.com
   - Select your Bridge Bidding App service

2. **Open Shell**
   - Click "Shell" tab in the service dashboard
   - This gives you direct terminal access to production

3. **Navigate to Backend**
   ```bash
   cd backend
   ```

4. **Run Migration Script**
   ```bash
   python3 database/init_all_tables.py
   ```

5. **Verify Success**
   Look for this output:
   ```
   ✅ Tables (18):
      - bidding_decisions              (0 rows)
      ...
   🔍 Verifying critical tables...
      ✅ bidding_decisions
      ✅ hand_analyses

   ✅ Database initialization complete!
   ```

6. **Restart Service**
   - In Render Dashboard, click "Manual Deploy" → "Deploy latest commit"
   - OR: Service will auto-restart after shell session closes

### Option B: SSH Access (If you have direct server access)

1. **SSH into Production Server**
   ```bash
   ssh your-production-server
   ```

2. **Navigate to App Directory**
   ```bash
   cd /path/to/bridge_bidding_app/backend
   ```

3. **Backup Database (Safety First)**
   ```bash
   cp bridge.db bridge.db.backup-$(date +%Y%m%d-%H%M%S)
   ```

4. **Run Migration Script**
   ```bash
   python3 database/init_all_tables.py
   ```

5. **Verify Tables Created**
   ```bash
   sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE name='bidding_decisions';"
   # Should output: bidding_decisions
   ```

6. **Restart Application Service**
   ```bash
   # Depends on your setup, examples:
   sudo systemctl restart bridge-bidding-app
   # OR
   pm2 restart bridge-bidding-app
   # OR
   supervisorctl restart bridge-bidding-app
   ```

### Option C: Database Migration Only (Manual SQL)

If the Python script doesn't work for some reason:

```bash
cd backend
sqlite3 bridge.db < migrations/001_add_bidding_feedback_tables.sql

# Verify
sqlite3 bridge.db "SELECT COUNT(*) FROM bidding_decisions;"
# Should output: 0 (empty table, ready to use)
```

---

## Step 2: Test Database Fix in Production

### Backend API Test
```bash
curl https://your-production-url.com/api/analytics/dashboard
```

**Expected:** JSON response (may be empty data, but no errors)

**If you see an error:** Database migration didn't work, check logs

### Frontend Test

1. Open production app in browser
2. Login (or play as guest)
3. Play a complete hand
4. Click "My Progress" button
5. **Expected:** Dashboard loads without "no such table" error
6. May show empty/zero stats initially (will populate as users play)

---

## Step 3: Deploy Latest Code to Production

Now that the database is fixed, we can safely deploy the latest code.

### Merge Development to Main

```bash
# 1. Switch to main branch
git checkout main

# 2. Pull latest from remote
git pull origin main

# 3. Merge development branch
git merge development

# 4. Verify merge looks correct
git log --oneline -5
# Should show:
#   55fd0e8 fix: Critical bug fixes and AI system enhancements
#   41aca99 feat: Add Phase 1 bidding feedback system...
```

### Push to Production

```bash
# Push to GitHub (triggers deployment if auto-deploy enabled)
git push origin main

# If Render has auto-deploy disabled:
# Go to Render Dashboard → Manual Deploy → "Deploy latest commit"
```

### Monitor Deployment

- Watch Render deployment logs
- Look for successful build
- Wait for service to restart
- Check service health endpoint

---

## Step 4: Verify Production Deployment

### Quick Smoke Tests

1. **Homepage loads** ✅
2. **Can start new game** ✅
3. **Bidding works** ✅
4. **Play phase works** ✅
5. **Dashboard loads** ✅ (MAIN FIX)
6. **Dealer rotates properly** ✅ (NEW FEATURE)

### Check Dealer Rotation (New Feature)

1. Start a new session
2. Look at bidding table header
3. Should see "(D)" next to dealer's name
4. Play hand, start next hand
5. Dealer should rotate: North → East → South → West

### Check Console Logs (If Available)

Production logs should show:
```
🎲 Dealer for this hand: North
Database connection successful
Session started successfully
```

No errors about "no such table"

---

## Step 5: Monitor for Issues

### First 24 Hours

- Check error logs for new issues
- Monitor user feedback
- Watch for database errors
- Verify dashboard analytics populate as users play

### What to Watch For

**Good Signs:**
- Dashboard loads without errors
- Bidding decisions being recorded
- Stats updating after gameplay
- No "no such table" errors

**Warning Signs:**
- 500 errors when accessing dashboard
- Database write errors
- Empty analytics despite gameplay
- Session creation failures

---

## Rollback Plan (If Something Goes Wrong)

### If Database Migration Breaks Things

```bash
# Restore backup
cp bridge.db.backup-YYYYMMDD-HHMMSS bridge.db

# Restart service
# (Use your service restart command)
```

### If Code Deployment Breaks Things

```bash
# Revert to previous commit
git checkout main
git reset --hard 41aca99
git push origin main --force

# Redeploy via Render dashboard
```

---

## Success Criteria

- [ ] Database migration runs successfully
- [ ] `bidding_decisions` table exists in production
- [ ] Backend API returns dashboard data without errors
- [ ] Frontend "My Progress" button works
- [ ] Latest code (55fd0e8) deployed to production
- [ ] Dealer rotation working (shows "(D)" indicator)
- [ ] No new errors in production logs
- [ ] Users can play hands successfully

---

## Post-Deployment Tasks

### Update Documentation

- [ ] Update README with latest features
- [ ] Mark production database fix as complete
- [ ] Update bug tracking checklist

### Future Prevention

Add to deployment pipeline (Render build command):
```bash
pip install -r backend/requirements.txt && python3 backend/database/init_all_tables.py
```

This ensures database migrations run automatically on every deployment.

---

## Deployment Checklist

Use this checklist during deployment:

### Pre-Deployment
- [ ] Local database migration tested (✅ Done)
- [ ] All tests passing locally
- [ ] Documentation updated
- [ ] Backup plan ready

### Database Migration
- [ ] Access production server/shell
- [ ] Navigate to backend directory
- [ ] (Optional) Backup database
- [ ] Run `python3 database/init_all_tables.py`
- [ ] Verify success output
- [ ] Test dashboard API endpoint
- [ ] Test frontend "My Progress" button

### Code Deployment
- [ ] Merge development to main
- [ ] Push to origin/main
- [ ] Monitor deployment logs
- [ ] Wait for service restart
- [ ] Run smoke tests

### Verification
- [ ] Homepage loads
- [ ] Can play a hand
- [ ] Dashboard works
- [ ] Dealer rotation shows
- [ ] No errors in logs

### Monitoring
- [ ] Check error logs (first hour)
- [ ] Monitor user sessions
- [ ] Verify analytics populate
- [ ] Watch for issues (first 24h)

---

## Support & Troubleshooting

### If Migration Script Fails

Check:
1. Python version: `python3 --version` (should be 3.8+)
2. File permissions: `ls -la backend/database/`
3. Database file exists: `ls -la backend/bridge.db`
4. SQLite accessible: `sqlite3 --version`

### If Dashboard Still Broken After Migration

1. Check table exists:
   ```bash
   sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE type='table' AND name='bidding_decisions';"
   ```

2. Check view exists:
   ```bash
   sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE type='view' AND name='v_bidding_feedback_stats';"
   ```

3. Check backend logs for SQL errors

4. Verify API endpoint works:
   ```bash
   curl https://your-url.com/api/analytics/dashboard
   ```

### If You Need Help

1. Check full error message in logs
2. Verify which step failed
3. Check database state with SQLite commands
4. Review PRODUCTION_DATABASE_FIX.md for detailed troubleshooting

---

## Files to Include in Deployment

Already in repository (no action needed):
- ✅ `backend/database/init_all_tables.py`
- ✅ `backend/migrations/001_add_bidding_feedback_tables.sql`
- ✅ All schema files
- ✅ Latest code changes (commit 55fd0e8)

---

## Timeline Estimate

- **Database Migration:** 5-10 minutes
- **Testing Database:** 5 minutes
- **Code Deployment:** 10-15 minutes
- **Verification:** 10 minutes
- **Total:** 30-40 minutes

---

## Contact Information

**Issue:** BUG-V008 - Dashboard Database Error
**Created:** 2025-10-18
**Deployed:** [Date when you run this]
**Related Commits:**
- `41aca99` - Phase 1 bidding feedback (has bug)
- `55fd0e8` - Critical bug fixes (waiting for this)

---

**Status:** 📋 READY TO EXECUTE
**Risk Level:** 🟢 LOW (backward compatible, well-tested)
**Estimated Time:** 30-40 minutes
**Recommended Time:** During low-traffic period (if possible)
