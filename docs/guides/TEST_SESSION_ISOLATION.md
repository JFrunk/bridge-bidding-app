# How to Test Session Isolation

**Purpose:** Verify that multiple users can play simultaneously without interfering with each other's games.

**Why This Matters:** Session isolation is the #1 critical fix from the CTO review (ADR-001). We replaced global variables with session-based state to enable multi-user support.

---

## 🎯 What We're Testing

**Session isolation means:**
- ✅ Each browser window has its own independent game
- ✅ Cards in Window A don't appear in Window B
- ✅ Playing a card in Window A doesn't affect Window B
- ✅ Different vulnerability settings per session
- ✅ Different AI difficulty per session
- ✅ No "card stealing" or state corruption

---

## 📋 Quick Test (5 minutes)

### **Step 1: Open Two Browser Windows**

**Option A: Two Different Browsers**
- Window 1: Chrome → http://localhost:3000
- Window 2: Firefox → http://localhost:3000

**Option B: Same Browser (Incognito/Private)**
- Window 1: Chrome (normal) → http://localhost:3000
- Window 2: Chrome (Incognito) → http://localhost:3000

**Option C: Same Browser (Different Windows)**
- Window 1: Chrome → http://localhost:3000
- Window 2: Chrome (new window) → http://localhost:3000

**Note:** Option A or B is best because they guarantee different sessions.

---

### **Step 2: Start a Game in BOTH Windows**

**Window 1:**
1. Click "Deal New Hand" or "Start Practice"
2. Note the cards you received (e.g., "I have ♠AKQ...")
3. Note the vulnerability (e.g., "None")

**Window 2:**
1. Click "Deal New Hand" or "Start Practice"
2. Note the cards you received
3. Note the vulnerability

**✅ PASS Criteria:**
- Window 1 and Window 2 have **different cards**
- If they have the same cards, that's a bug (session isolation failed)

---

### **Step 3: Play Cards Simultaneously**

**Window 1:**
1. Complete bidding (or skip to play phase)
2. Play a card (e.g., ♠A)
3. Leave it there (don't complete the trick)

**Window 2:**
1. Complete bidding (or skip to play phase)
2. Check if Window 2's cards changed
3. Play a card in Window 2

**✅ PASS Criteria:**
- Playing a card in Window 1 does **NOT** affect Window 2
- Window 2 still has its original cards
- No cards disappeared or changed

---

### **Step 4: Verify Session Persistence**

**Window 1:**
1. Note your current game state (tricks won, current trick)
2. Refresh the page (Cmd+R or F5)
3. Check if your game state persisted

**✅ PASS Criteria:**
- After refresh, you return to the same game
- Your session ID persists (stored in localStorage)
- Cards and game state are the same

---

## 🔬 Detailed Test (15 minutes)

### **Test 1: Different Hands**

**Setup:**
- Open 2 browser windows
- Both on http://localhost:3000

**Steps:**
1. Window 1: Click "Deal New Hand"
2. Window 2: Click "Deal New Hand"
3. Take screenshots of both hands

**Expected:**
- ✅ Different cards in each window
- ✅ Each window has 13 cards in South's hand
- ✅ Different vulnerability settings

**Failure Example:**
- ❌ Both windows show identical hands
- ❌ Window 2 shows Window 1's cards

---

### **Test 2: Independent Bidding**

**Setup:**
- 2 windows, both with hands dealt

**Steps:**
1. **Window 1:** Bid "1♠"
2. **Window 2:** Check what bids appear
3. **Window 2:** Bid "1NT"
4. **Window 1:** Check what bids appear

**Expected:**
- ✅ Window 1 shows only its own auction (1♠, Pass, Pass, Pass)
- ✅ Window 2 shows only its own auction (1NT, Pass, Pass, Pass)
- ✅ Bidding in one window doesn't appear in the other

**Failure Example:**
- ❌ Window 2 shows "1♠" from Window 1
- ❌ Auctions get mixed together

---

### **Test 3: Independent Card Play**

**Setup:**
- 2 windows, both in play phase

**Steps:**
1. **Window 1:** Play ♠A
2. **Window 2:** Check if ♠A disappeared from your hand
3. **Window 2:** Play ♥K
4. **Window 1:** Check if ♥K disappeared from your hand

**Expected:**
- ✅ Playing ♠A in Window 1 doesn't remove it from Window 2
- ✅ Each window tracks its own tricks independently
- ✅ Trick counts are different

**Failure Example:**
- ❌ Playing a card in Window 1 removes it from Window 2
- ❌ Trick winner in Window 1 affects Window 2

---

### **Test 4: Different AI Difficulty**

**Setup:**
- 2 windows, no hands dealt yet

**Steps:**
1. **Window 1:** Set AI to "Beginner"
2. **Window 1:** Deal a hand, complete bidding, note AI behavior
3. **Window 2:** Set AI to "Expert"
4. **Window 2:** Deal a hand, complete bidding, note AI behavior

**Expected:**
- ✅ Window 1 AI plays simpler (beginner level)
- ✅ Window 2 AI plays better (expert level)
- ✅ Different AI decisions

**Failure Example:**
- ❌ Both windows use the same AI difficulty
- ❌ Changing AI in Window 1 affects Window 2

---

### **Test 5: Vulnerability Independence**

**Setup:**
- 2 windows

**Steps:**
1. **Window 1:** Deal a hand, note vulnerability (e.g., "None")
2. **Window 2:** Deal a hand, note vulnerability
3. Repeat 3-4 times in each window

**Expected:**
- ✅ Different vulnerability settings in each window
- ✅ Vulnerability randomizes independently

**Failure Example:**
- ❌ Both windows always have same vulnerability
- ❌ Vulnerability in Window 2 matches Window 1

---

## 🧪 Advanced Tests (Technical Review)

### **Test 6: Session ID Verification**

**Check Session IDs:**

1. **Window 1:** Open browser DevTools (F12)
2. Go to Console tab
3. Type: `localStorage.getItem('bridge_session_id')`
4. Note the session ID (e.g., `session_1697123456_abc123`)

5. **Window 2:** Open browser DevTools
6. Type: `localStorage.getItem('bridge_session_id')`
7. Note the session ID

**Expected:**
- ✅ Window 1 and Window 2 have **different session IDs**
- ✅ Session IDs follow format: `session_<timestamp>_<random>`

**Failure Example:**
- ❌ Both windows have the same session ID

---

### **Test 7: Session Header Verification**

**Check API Calls:**

1. **Window 1:** Open DevTools → Network tab
2. Deal a hand
3. Find the `/api/deal-hands` request
4. Click it → Headers tab
5. Look for "X-Session-ID" in Request Headers
6. Note the value

7. **Window 2:** Repeat steps 1-6

**Expected:**
- ✅ Both windows send different X-Session-ID headers
- ✅ Headers match the localStorage session IDs

**Failure Example:**
- ❌ Missing X-Session-ID header
- ❌ Both windows send same session ID

---

### **Test 8: Concurrent Play (Stress Test)**

**Setup:**
- 3-4 browser windows

**Steps:**
1. Open 4 windows (Chrome, Firefox, Safari, Chrome Incognito)
2. Deal hands in all windows simultaneously
3. Play cards in random order across all windows
4. Complete full hands in each window

**Expected:**
- ✅ No crashes or errors
- ✅ Each window completes independently
- ✅ No state corruption
- ✅ Trick counts are correct in each window

**Failure Example:**
- ❌ Browser crashes
- ❌ Cards disappear
- ❌ Tricks count incorrectly
- ❌ Game state gets confused

---

## 🚨 Common Issues & Fixes

### **Issue: Both Windows Show Same Cards**

**Symptoms:**
- Window 1 and Window 2 have identical hands

**Cause:**
- Session isolation not working
- Likely using same session ID

**Fix:**
1. Clear localStorage in both windows:
   - DevTools → Application → Local Storage → Clear
2. Refresh both windows (Cmd+R)
3. Deal new hands

**If still broken:**
- Check backend logs for session ID usage
- Verify `X-Session-ID` headers are different

---

### **Issue: Cards Disappear Across Windows**

**Symptoms:**
- Playing a card in Window 1 removes it from Window 2

**Cause:**
- Backend using global state (session isolation failed)

**Fix:**
1. Check backend server.py uses `get_state()` not global variables
2. Restart backend server
3. Clear frontend cache

**This is a CRITICAL bug** - report immediately if found!

---

### **Issue: Session Lost After Refresh**

**Symptoms:**
- Refreshing page starts a new game

**Cause:**
- Session ID not persisting in localStorage

**Fix:**
1. Check localStorage has `bridge_session_id`
2. Verify sessionHelper.js is working
3. Check browser isn't in private/incognito mode

---

## ✅ Pass/Fail Criteria

### **✅ PASS - Session Isolation Works**

- Different cards in each window
- Playing cards doesn't affect other windows
- Different session IDs in each window
- X-Session-ID headers are sent and unique
- No crashes with multiple concurrent users
- Session persists after refresh

### **❌ FAIL - Session Isolation Broken**

- Same cards appear in multiple windows
- Playing a card in one window affects another
- Missing X-Session-ID headers
- Same session ID in multiple windows
- Crashes or errors with concurrent users
- Random state corruption

---

## 📊 Testing Checklist

Print this checklist and check off during testing:

```
[ ] Test 1: Different Hands - Both windows have different cards
[ ] Test 2: Independent Bidding - Auctions don't mix
[ ] Test 3: Independent Card Play - Cards don't disappear
[ ] Test 4: Different AI Difficulty - AI behaves differently
[ ] Test 5: Vulnerability Independence - Random per session
[ ] Test 6: Session ID Verification - Different IDs
[ ] Test 7: Session Headers - X-Session-ID sent
[ ] Test 8: Concurrent Play - No crashes with 4 windows

OVERALL RESULT: [ ] PASS  [ ] FAIL
```

---

## 🎯 For Your Technical Review

**How to demonstrate session isolation:**

1. **Before demo:** Test with 2 browsers (Chrome + Firefox)
2. **During demo:**
   - Open 2 browser windows side-by-side
   - Deal hands in both
   - Point out different cards
   - Play cards simultaneously
   - Show they don't interfere

3. **Talking points:**
   - "We implemented session-based state (ADR-001)"
   - "Each user gets isolated game state via session IDs"
   - "Thread-safe with RLock for concurrent access"
   - "Ready for production multi-user deployment"

4. **Show in DevTools:**
   - localStorage session IDs (different)
   - Network tab X-Session-ID headers (unique)
   - No errors in console

---

## 📝 Quick Reference Commands

**Clear session (force new game):**
```javascript
// In browser DevTools console
localStorage.removeItem('bridge_session_id');
location.reload();
```

**Check session ID:**
```javascript
// In browser DevTools console
localStorage.getItem('bridge_session_id');
```

**Monitor API calls:**
```javascript
// In browser DevTools console
// Network tab → filter by "api" → watch X-Session-ID headers
```

---

**Last Updated:** 2025-10-16
**Related:** ADR-001 (Session State Management)
**Status:** Ready for Testing
**Estimated Test Time:** 5-15 minutes depending on depth
