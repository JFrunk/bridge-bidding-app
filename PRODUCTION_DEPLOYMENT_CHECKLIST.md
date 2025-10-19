# Production Deployment Checklist
**Date:** 2025-10-19
**Issue:** BUG-V008 - Dashboard Database Error
**Deployments:** Database Migration + Code Update

---

## Quick Reference

**What's Being Fixed:**
- Missing `bidding_decisions` table in production
- Dashboard "no such table" error
- Deploying latest bug fixes and dealer rotation

**Estimated Time:** 30-40 minutes
**Risk Level:** LOW

---

## Checklist

### Phase 1: Database Migration ⚙️

- [ ] **Access Production Environment**
  - [ ] Open Render.com dashboard OR SSH to production server
  - [ ] Navigate to backend directory

- [ ] **Backup Database (Optional but Recommended)**
  ```bash
  cp bridge.db bridge.db.backup-$(date +%Y%m%d-%H%M%S)
  ```

- [ ] **Run Migration Script**
  ```bash
  python3 database/init_all_tables.py
  ```

- [ ] **Verify Success Output**
  - [ ] See "✅ Applied: 001_add_bidding_feedback_tables.sql"
  - [ ] See "✅ bidding_decisions" in critical tables list
  - [ ] See "✅ Database initialization complete!"

- [ ] **Verify Table Exists**
  ```bash
  sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE name='bidding_decisions';"
  ```
  Expected output: `bidding_decisions`

- [ ] **Test Backend API**
  ```bash
  curl https://your-production-url/api/analytics/dashboard
  ```
  Expected: JSON response (no "table not found" error)

- [ ] **Test Frontend Dashboard**
  - [ ] Open production app
  - [ ] Play a hand
  - [ ] Click "My Progress" button
  - [ ] Dashboard loads without error ✅

---

### Phase 2: Code Deployment 🚀

- [ ] **Merge Development to Main**
  ```bash
  git checkout main
  git pull origin main
  git merge development
  ```

- [ ] **Review Merge**
  ```bash
  git log --oneline -5
  ```
  - [ ] Should show commit `55fd0e8` (Critical bug fixes)
  - [ ] Should show commit `41aca99` (Phase 1 bidding feedback)

- [ ] **Push to Production**
  ```bash
  git push origin main
  ```

- [ ] **Monitor Deployment**
  - [ ] Watch Render deployment logs (if using Render)
  - [ ] Wait for successful build
  - [ ] Wait for service restart
  - [ ] Service shows "Live" status

---

### Phase 3: Verification ✅

- [ ] **Basic Functionality**
  - [ ] Homepage loads
  - [ ] Can login/play as guest
  - [ ] Can deal new hand
  - [ ] Bidding works
  - [ ] Play phase works
  - [ ] Game completes successfully

- [ ] **Database Fix Verification**
  - [ ] "My Progress" button appears
  - [ ] Dashboard loads without errors
  - [ ] No "no such table" errors in logs
  - [ ] Analytics data structure present (may be empty)

- [ ] **Dealer Rotation Feature**
  - [ ] Start new session
  - [ ] Bidding table shows dealer indicator "(D)"
  - [ ] Play hand #1 (North dealer)
  - [ ] Play hand #2 (East dealer) - verify rotation
  - [ ] Dealer rotates: N → E → S → W

- [ ] **Check Error Logs**
  - [ ] No SQL errors
  - [ ] No "table not found" errors
  - [ ] No 500 errors
  - [ ] No new unexpected errors

---

### Phase 4: Monitoring 👀

**First Hour:**
- [ ] Check error logs every 15 minutes
- [ ] Monitor for user reports
- [ ] Watch for database errors

**First 24 Hours:**
- [ ] Review error logs once more
- [ ] Verify bidding decisions being recorded
- [ ] Check dashboard stats populate
- [ ] Confirm no regression reports

---

## Rollback Plan 🔄

### If Database Migration Fails

```bash
# Restore backup
cp bridge.db.backup-YYYYMMDD-HHMMSS bridge.db

# Restart service (use your restart command)
```

### If Code Deployment Breaks

```bash
# Revert to previous commit
git checkout main
git reset --hard 41aca99
git push origin main --force

# Trigger redeploy in Render dashboard
```

---

## Success Criteria 🎯

All must be true:
- ✅ `bidding_decisions` table exists in production
- ✅ Dashboard loads without "no such table" error
- ✅ Latest code (commit 55fd0e8) deployed
- ✅ Dealer rotation working (shows "(D)" indicator)
- ✅ Users can play hands successfully
- ✅ No new errors in production logs

---

## Quick Commands Reference

### Check Table Exists
```bash
sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE name='bidding_decisions';"
```

### Test Dashboard API
```bash
curl https://your-production-url/api/analytics/dashboard
```

### Check Database Tables
```bash
sqlite3 bridge.db ".tables"
```

### View Recent Logs (if using systemd)
```bash
journalctl -u bridge-bidding-app -n 50 --no-pager
```

### Restart Service
```bash
# Render: Use dashboard "Manual Deploy"
# OR systemd:
sudo systemctl restart bridge-bidding-app
# OR pm2:
pm2 restart bridge-bidding-app
```

---

## Notes Section

**Deployment Start Time:** _______________

**Database Migration Result:** _______________

**Code Deployment Result:** _______________

**Issues Encountered:** _______________

**Resolution:** _______________

**Deployment Complete Time:** _______________

---

## Sign-Off

- [ ] Database migration completed successfully
- [ ] Code deployed successfully
- [ ] All tests passed
- [ ] No critical errors
- [ ] Ready for production use

**Deployed By:** _______________

**Date:** _______________

**Time:** _______________

---

**For detailed instructions, see:** [DEPLOY_TO_PRODUCTION.md](DEPLOY_TO_PRODUCTION.md)
