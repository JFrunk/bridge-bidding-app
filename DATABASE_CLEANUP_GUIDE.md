# Database Cleanup Guide

**Date:** 2025-10-24
**Purpose:** Remove test data to provide fresh user experience

---

## Problem Statement

When a new user opens the dashboard, they see **old test data** from development:
- 6 bidding decisions from Oct 17, 2025 (test data)
- 1 bidding decision from Oct 23, 2025 (test data)
- AI play logs from testing sessions

**User Experience Issue:** New users should see an **empty dashboard** initially, not data they didn't generate.

---

## Current Database State

```
Table                        Records  Date Range
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
bidding_decisions                 7  2025-10-17 to 2025-10-23
session_hands                     1  2025-10-24 (today)
game_sessions                     1  2025-10-14 (old)
ai_play_log                      65  2025-10-23 to 2025-10-24
hand_analyses                     0  N/A
```

### Test Data (Should be removed)
- **6 bidding decisions** from Oct 17 (positions, bids, scores)
- **1 bidding decision** from Oct 23
- **39 AI play logs** from Oct 23
- **Game session** from Oct 14 (old session reused)

### Fresh Data (From today's session)
- **1 session_hands** record (Oct 24 13:02:39) - Real gameplay!
- **26 AI play logs** from Oct 24 - Today's actual hand

---

## Cleanup Options

### Option 1: Complete Database Reset ✅ **RECOMMENDED FOR DEVELOPMENT**

**What it does:**
- Deletes ALL user data
- Provides completely fresh start
- User sees empty dashboard initially

**When to use:**
- Development/testing environment
- You want to start completely fresh
- You're okay losing today's test hand data

**How to run:**
```bash
cd backend
python3 cleanup_database.py
# Choose option 1
```

**Result:**
```
Dashboard:
  - HANDS PRACTICED: 0
  - All stats: Empty/zero
  - Recent decisions: None
```

---

### Option 2: Selective Cleanup ⚠️ **KEEPS TODAY'S DATA**

**What it does:**
- Deletes only data from before Oct 24, 2025
- Keeps today's session_hands record
- Keeps today's AI play logs (26 records)

**When to use:**
- You want to keep today's real gameplay data
- Remove only obvious test data
- More conservative approach

**How to run:**
```bash
cd backend
python3 cleanup_database.py
# Choose option 2
```

**Result:**
```
Deletes:
  - 6 bidding decisions from Oct 17
  - 1 bidding decision from Oct 23
  - 39 AI play logs from Oct 23

Keeps:
  - 1 session_hands from today
  - 26 AI play logs from today
  - Current game session
```

**Dashboard shows:**
```
HANDS PRACTICED: 1 (today's hand)
Bidding quality: No decisions (needs new bids)
```

---

### Option 3: User ID Separation 👤 **BEST FOR PRODUCTION**

**What it does:**
- Keeps ALL existing data under `user_id=1` (test user)
- Creates fresh `user_id=2` for actual gameplay
- Requires frontend change to use new user ID

**When to use:**
- Production environment
- Want to preserve test data for debugging
- Implementing multi-user support

**How to run:**
```bash
cd backend
python3 cleanup_database.py
# Choose option 3
# Then update frontend to use user_id=2
```

**Frontend change required:**
```javascript
// In frontend/src/App.js
// Find all instances of:
user_id: 1

// Change to:
user_id: 2
```

**Result:**
- Test data remains under user_id=1
- New gameplay under user_id=2 shows empty dashboard
- Can switch between users for testing

---

## Recommended Approach

### For Local Development
**Use Option 1: Complete Reset**

This gives you the cleanest user experience and you can replay hands to test the dashboard properly.

```bash
cd backend
python3 cleanup_database.py
# Type: 1
# Type: YES
```

### For Production
**Use Option 3: User Separation**

This allows you to keep test data separate from real users.

```bash
# 1. Run cleanup script
cd backend
python3 cleanup_database.py
# Type: 3
# Type: yes

# 2. Update frontend
# Edit frontend/src/App.js
# Change user_id: 1 → user_id: 2

# 3. Restart frontend
cd frontend
npm start
```

---

## What Gets Deleted vs Kept

### Complete Reset (Option 1)

| Table | Before | After |
|-------|--------|-------|
| bidding_decisions | 7 | 0 |
| session_hands | 1 | 0 |
| game_sessions | 1 | 0 |
| ai_play_log | 65 | 0 |

### Selective Cleanup (Option 2)

| Table | Before | After | Reason |
|-------|--------|-------|--------|
| bidding_decisions | 7 | 0 | All are from Oct 17-23 (old) |
| session_hands | 1 | 1 | Oct 24 (keep) |
| game_sessions | 1 | 1 | Has hands played (keep) |
| ai_play_log | 65 | 26 | Keep Oct 24 only |

### User Separation (Option 3)

| Table | user_id=1 | user_id=2 |
|-------|-----------|-----------|
| bidding_decisions | 7 (test) | 0 (fresh) |
| session_hands | 1 (test) | 0 (fresh) |
| game_sessions | 1 (test) | 0 (fresh) |
| ai_play_log | 65 (test) | 0 (fresh) |

---

## Running the Cleanup Script

### Step 1: Preview Current State
```bash
cd backend
python3 cleanup_database.py
```

The script will show you:
1. Current database state (record counts)
2. Data preview (what will be deleted)
3. Options to choose from

### Step 2: Choose Option
```
Choose an option (1-4):
  1. Complete Reset
  2. Selective Cleanup
  3. User Separation
  4. Cancel
```

### Step 3: Confirm
- **Option 1** requires typing `YES` (all caps)
- **Option 2 & 3** require typing `yes` (lowercase)
- This prevents accidental deletion

### Step 4: Verify
The script shows the final database state after cleanup.

---

## After Cleanup

### If you chose Option 1 or 2:
1. **Refresh the dashboard** in your browser
2. Should see **HANDS PRACTICED: 0** (or 1 if Option 2)
3. **Play a new hand** to generate fresh data
4. **Check dashboard updates** with real data

### If you chose Option 3:
1. **Update frontend** to use `user_id: 2`
2. **Restart frontend** server
3. **Refresh browser**
4. Dashboard should show **empty state**
5. **Play hands** to populate with fresh data

---

## Troubleshooting

### Script shows "Permission denied"
```bash
chmod +x backend/cleanup_database.py
```

### Database is locked
- Stop the backend server first
- Run cleanup script
- Restart backend server

### Want to undo cleanup
**You can't undo!** The data is permanently deleted.

**Prevention:**
```bash
# Backup database before cleanup
cp backend/bridge.db backend/bridge.db.backup
```

**Restore from backup:**
```bash
cp backend/bridge.db.backup backend/bridge.db
```

---

## Long-Term Solution

### Implement User Authentication

Instead of cleanup scripts, implement proper user management:

1. **User Login System**
   - Each real user gets unique user_id
   - Test data uses user_id=0 or user_id=999

2. **Data Isolation**
   - Dashboard queries filtered by logged-in user
   - No cross-contamination of data

3. **Test Mode Flag**
   - Environment variable: `TEST_MODE=true`
   - Uses separate test database
   - Never mixes with production data

---

## Summary

**Quick Decision Guide:**

| Situation | Recommended Option |
|-----------|-------------------|
| Local dev, want fresh start | Option 1: Complete Reset |
| Local dev, keep today's data | Option 2: Selective Cleanup |
| Production deployment | Option 3: User Separation |
| Just testing the script | Option 4: Cancel |

**Next Steps:**
1. Choose an option based on your needs
2. Run `python3 cleanup_database.py`
3. Verify dashboard shows correct state
4. Play hands to test fresh data generation

---

**Created:** 2025-10-24
**Script Location:** `backend/cleanup_database.py`
**Database:** `backend/bridge.db`
