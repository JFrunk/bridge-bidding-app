# Bug Testing Checklist - Manual Testing Guide
**Date:** 2025-10-18
**Purpose:** Print-friendly checklist for manual bug verification

---

## 🔴 CRITICAL BUGS - Test First

**No critical bugs remaining - all resolved!**

---

## 🔵 FEATURE UPDATE REQUESTS

### ☐ FEATURE-001: Update Gameplay Statistics
**What to implement:** Update the gameplay statistics system to track additional metrics
**Expected:** Comprehensive statistics tracking for user performance and progress

**Implementation Notes:**
- Enhance existing statistics tracking in the database
- Add new metrics for bidding accuracy, play performance, and learning progress
- Integrate with dashboard display
- Consider historical tracking and trend analysis

**Status:** PENDING IMPLEMENTATION

---

## 🟡 HIGH PRIORITY BUGS - Test Next

### ☐ BUG-H001: AI Level Display Mismatch
**What to test:** AI difficulty selector matches actual AI behavior
**Expected:** Button and status indicator show same difficulty level

**Test Steps:**
1. ☐ Start application (backend + frontend running)

2. ☐ Load page and start play phase
   - Open http://localhost:3000
   - Click "Play Random Hand"

3. ☐ Check AI difficulty displays
   - Look at **AI Difficulty Selector button** (left side)
   - Look at **DDS Status Indicator** (expandable on right)
   - Note what each shows: ___________________

4. ☐ Refresh page (press F5)
   - Check button after reload
   - Does it match what backend has stored?

**PASS Criteria:**
- ✅ AI Difficulty Selector button shows same level as DDS Status
- ✅ After refresh, button shows same difficulty as before
- ✅ Both displays update when you change difficulty

**FAIL Criteria:**
- ❌ Button shows "Intermediate" but Status shows "Expert"
- ❌ Button resets to default after refresh despite backend having different value
- ❌ Displays don't match each other

**Status:** __________ (PASS / FAIL)
**Notes:** _________________________________________________

---

### ☐ BUG-H002: Expert AI Discards High Cards
**What to test:** Expert AI (8/10, 9/10) makes smart discards
**Expected:** AI discards low cards (2-7), not high cards (K, Q, J, A)

**Automated Test:**
1. ☐ Run test script
   ```bash
   cd backend
   python3 test_discard_fix.py
   ```

**Expected Output:**
```
✅ ALL TESTS PASSED - AI correctly discards low cards
AI chose: ♣2 (or other low card)
```

**PASS Criteria:**
- ✅ Test script passes with "✅ ALL TESTS PASSED"
- ✅ AI chose low card (2-7)

**FAIL Criteria:**
- ❌ Test fails with AI choosing King or other high card
- ❌ Error during test execution

**Manual Test (Optional - if you want to be thorough):**
1. ☐ Play 5-10 hands at Expert level (9/10)
2. ☐ Watch for discard situations (when AI is void in led suit)
3. ☐ Record what AI discards:
   - Hand 1: _______________
   - Hand 2: _______________
   - Hand 3: _______________
4. ☐ Count: How many times did AI discard low cards (2-7)? ____
5. ☐ Count: How many times did AI discard honors (J, Q, K, A)? ____

**PASS Criteria:**
- ✅ 90%+ discards are low cards
- ✅ No Kings or Aces discarded when low cards available

**Status:** __________ (PASS / FAIL)
**Notes:** _________________________________________________

---

### ☐ BUG-H003: First Hand After Restart - Illegal Bidding
**What to test:** First hand after server restart has legal bids
**Expected:** Each AI player bids according to their own hand, not all the same

**Test Steps:**
1. ☐ Stop backend server
   ```bash
   pkill -f "python.*server.py"
   ```

2. ☐ Start backend server fresh
   ```bash
   cd backend
   python3 server.py
   ```

3. ☐ Reload frontend (F5 or restart)

4. ☐ Deal FIRST hand after restart
   - Click "Deal New Hand"
   - Watch first 4 bids carefully
   - Record auction: ___________________

5. ☐ Check if bids are legal
   - Do all three AI players bid the same thing? YES / NO
   - Are the bids legal given standard bridge rules? YES / NO

6. ☐ Repeat test 3 more times (it's intermittent)
   - Trial 1: __________ (LEGAL / ILLEGAL)
   - Trial 2: __________ (LEGAL / ILLEGAL)
   - Trial 3: __________ (LEGAL / ILLEGAL)

**PASS Criteria:**
- ✅ Each player bids according to their own hand
- ✅ No duplicate bids at same level (unless legal overcalls)
- ✅ Bids make sense given standard SAYC
- ✅ 4/4 trials have legal bidding sequences

**FAIL Criteria:**
- ❌ All three AI players bid the same (e.g., all 1NT)
- ❌ Bids are illegal given hand strength
- ❌ Any trial shows illegal bidding

**Status:** __________ (PASS / FAIL)
**Notes:** _________________________________________________

---

## 🟢 MEDIUM PRIORITY BUGS - Test When You Have Time

### ☐ BUG-M001: Declarer's Hand Not Visible When User is Dummy
**What to test:** Declarer's hand displays when user is dummy
**Expected:** User sees both declarer's hand and dummy hand

**Test Steps:**
1. ☐ Start app (backend + frontend)

2. ☐ Play hands until you get scenario where North declares
   - Goal: Contract where North or East/West is declarer
   - User (South) should be dummy

3. ☐ When you find North as declarer and South as dummy:
   - Can you see North's hand at top of screen? YES / NO
   - Can you see South's hand at bottom? YES / NO
   - Can you click cards in North's hand? YES / NO

**PASS Criteria:**
- ✅ Both North's hand (top) and South's hand (bottom) are visible
- ✅ You can click cards in North's hand to play them
- ✅ Both hands update as cards are played

**FAIL Criteria:**
- ❌ North's hand is missing/blank
- ❌ Cannot control North's cards

**Status:** __________ (PASS / FAIL)
**Notes:** _________________________________________________

---

### ☐ BUG-M002: Replay Hand Button Crashes
**What to test:** Replay hand functionality works
**Expected:** Can replay same hand multiple times without errors

**Test Steps:**
1. ☐ Start app and play a complete hand
   - Let AI play all positions for speed
   - Or play yourself through all 13 tricks

2. ☐ After hand completes, click "Replay Hand" button

3. ☐ Check if replay works
   - Does hand restart with all 13 cards? YES / NO
   - Can you play through it again? YES / NO
   - Any error messages? YES / NO

4. ☐ Try replaying 2-3 times
   - Trial 1: __________ (WORKS / CRASHES)
   - Trial 2: __________ (WORKS / CRASHES)
   - Trial 3: __________ (WORKS / CRASHES)

**PASS Criteria:**
- ✅ Hand restarts with all 13 cards in each position
- ✅ Can play through entire hand again
- ✅ Can replay multiple times without errors

**FAIL Criteria:**
- ❌ Error: "Position W has no cards"
- ❌ Crash or blank screen
- ❌ Players have fewer than 13 cards

**Status:** __________ (PASS / FAIL)
**Notes:** _________________________________________________

---

### ☐ BUG-M003: Hand Display Data Presentation Confusion
**What to test:** Review data clearly shows original vs current hand
**Expected:** Can tell which cards were played vs still in hand

**Test Steps:**
1. ☐ Play a hand partway through (e.g., 5-6 tricks)

2. ☐ Request hand review/analysis (if feature exists)
   - Or look at hand display during play

3. ☐ Check if it's clear:
   - Which cards are in hand now? YES / NO
   - Which cards were played? YES / NO
   - Is HCP explained as "original deal"? YES / NO

**PASS Criteria:**
- ✅ Clear separation of original vs current vs played cards
- ✅ Note explaining HCP reflects original deal
- ✅ Not confusing which cards were played

**FAIL Criteria:**
- ❌ Can't tell which cards were played
- ❌ HCP doesn't match current cards (without explanation)
- ❌ Appears like cards are "missing"

**Status:** __________ (PASS / FAIL)
**Notes:** _________________________________________________

---

## 🟢 LOW PRIORITY BUGS - Test If You Want

### ☐ BUG-L001: 5 Play Tests Failing
**What to test:** All play tests pass
**Expected:** 45/45 tests passing

**Test Steps:**
```bash
cd backend
python3 -m pytest tests/play/ -v
```

**PASS Criteria:**
- ✅ Output shows "45 passed" or "45/45"
- ✅ No errors about 14-card hands

**FAIL Criteria:**
- ❌ Shows "40 passed, 5 failed"
- ❌ Errors about hand parsing

**Status:** __________ (PASS / FAIL)
**Notes:** _________________________________________________

---

### ☐ BUG-L002: DDS Status Display Order Mismatch
**What to test:** Difficulty levels appear in consistent order
**Expected:** Beginner → Intermediate → Advanced → Expert

**Test Steps:**
1. ☐ Open app and start play phase
2. ☐ Click DDS Status Indicator to expand dropdown
3. ☐ Look at order of difficulty levels listed
4. ☐ Record order: ___________________

**PASS Criteria:**
- ✅ Levels appear in order: Beginner, Intermediate, Advanced, Expert
- ✅ Same order as in AI Difficulty Selector button

**FAIL Criteria:**
- ❌ Levels in different order
- ❌ Random order

**Status:** __________ (PASS / FAIL)
**Notes:** _________________________________________________

---

## ✅ VERIFIED BUGS - Already Fixed (Quick Verification)

### ☐ BUG-V001: Login "Failed to Fetch" Error (Verified Fixed 2025-10-18)
**Quick Test:**
1. ☐ Start backend server (cd backend && python3 server.py)
2. ☐ Check frontend .env has REACT_APP_API_URL=http://localhost:5000
3. ☐ Start frontend (cd frontend && npm start)
4. ☐ Try to login with test@example.com
5. ☐ Check: Does login succeed without "Failed to fetch" error? YES / NO

**PASS:** ✅ Login succeeds, no connection errors
**FAIL:** ❌ "Failed to fetch" error appears

**Status:** __________ (PASS / FAIL - should PASS)

---

### ☐ BUG-V002: AI Auto-Bidding for User (Verified Fixed 2025-10-17)
**Quick Test:**
1. ☐ Start new hand with North as dealer
2. ☐ Watch North bid (AI)
3. ☐ Watch East bid (AI)
4. ☐ Check: Does bidding box appear for South? YES / NO

**PASS:** ✅ Bidding box appears, user can bid
**FAIL:** ❌ AI bids automatically for South

**Status:** __________ (PASS / FAIL - should PASS)

---

### ☐ BUG-V003: Automatic Play Phase Transition (Verified Fixed 2025-10-17)
**Quick Test:**
1. ☐ Complete bidding sequence (any contract)
2. ☐ Verify 3 passes end auction
3. ☐ Check: Does "Play This Hand" button appear? YES / NO
4. ☐ Check: Does play start automatically after 3 seconds? YES / NO

**PASS:** ✅ Button appears, no auto-start
**FAIL:** ❌ Play starts automatically

**Status:** __________ (PASS / FAIL - should PASS)

---

### ☐ BUG-V004: AI Card Validation (Verified Fixed 2025-10-18)
**Quick Test:**
1. ☐ Play several random hands
2. ☐ Watch for any "impossible card" errors
3. ☐ Check: Any errors about cards not in hand? YES / NO

**PASS:** ✅ No validation errors, game runs smoothly
**FAIL:** ❌ Errors about impossible cards

**Status:** __________ (PASS / FAIL - should PASS)

---

### ☐ BUG-V005: Minimax Inverted Logic (Verified Fixed 2025-10-18)
**Quick Test:**
1. ☐ Play a few hands and watch defender play
2. ☐ Check: Do defenders make reasonable plays? YES / NO
3. ☐ Check: Any obviously wrong plays (playing 2 when holding 7 wins)? YES / NO

**PASS:** ✅ Defenders make reasonable plays
**FAIL:** ❌ Defenders make obviously wrong plays

**Status:** __________ (PASS / FAIL - should PASS)

---

### ☐ BUG-V006: Master Trump Detection (Verified Fixed 2025-10-18)
**Quick Test:**
1. ☐ Play some trump contracts
2. ☐ Watch when AI has remaining trumps
3. ☐ Check: Does AI recognize when they have winning trumps? YES / NO

**PASS:** ✅ AI plays winning trumps appropriately
**FAIL:** ❌ AI doesn't recognize master trumps

**Status:** __________ (PASS / FAIL - should PASS)

---

### ☐ BUG-V007: Scoring System Reversed Penalties (Verified Fixed 2025-10-18)
**Quick Test:**
1. ☐ Play a session with multiple hands
2. ☐ Note a hand where someone goes down (fails contract)
3. ☐ Check: Did the DEFENDING side get positive points? YES / NO
4. ☐ Example: NS declares 3NT, goes down 1 → EW should get +50

**Automated Test:**
```bash
cd backend
python3 test_session_scoring.py
# Should see: "=== All Tests Passed! ==="
```

**PASS:** ✅ Defenders get positive points when setting contracts
**FAIL:** ❌ Declaring side gets negative points when going down

**Status:** __________ (PASS / FAIL - should PASS)

---

### ☐ BUG-V008: Dashboard Does Not Show Up (Verified Fixed 2025-10-18)
**Quick Test:**
1. ☐ Start app and login
2. ☐ Navigate to dashboard page
3. ☐ Check: Does dashboard render properly? YES / NO
4. ☐ Check: Are statistics visible? YES / NO

**PASS:** ✅ Dashboard renders correctly with statistics
**FAIL:** ❌ Dashboard is blank or doesn't appear

**Status:** ✅ RESOLVED (PASS / FAIL - should PASS)

---

## 📊 TESTING SUMMARY

**Date Tested:** __________
**Tester:** __________

### Results by Priority

**🔴 CRITICAL (0 bugs):**
- All critical bugs resolved!

**🟡 HIGH (3 bugs):**
- BUG-H001 AI Level Mismatch: __________ (PASS / FAIL)
- BUG-H002 AI Discards: __________ (PASS / FAIL)
- BUG-H003 First Hand Illegal Bids: __________ (PASS / FAIL)

**🟢 MEDIUM (3 bugs):**
- BUG-M001 Declarer Hand Visible: __________ (PASS / FAIL)
- BUG-M002 Replay Hand: __________ (PASS / FAIL)
- BUG-M003 Hand Display: __________ (PASS / FAIL)

**🟢 LOW (2 bugs):**
- BUG-L001 Test Failures: __________ (PASS / FAIL)
- BUG-L002 Display Order: __________ (PASS / FAIL)

**✅ VERIFIED (8 bugs - should all PASS):**
- BUG-V001 Login Error: __________ (PASS / FAIL)
- BUG-V002 Auto-Bidding: __________ (PASS / FAIL)
- BUG-V003 Auto-Transition: __________ (PASS / FAIL)
- BUG-V004 Card Validation: __________ (PASS / FAIL)
- BUG-V005 Minimax Logic: __________ (PASS / FAIL)
- BUG-V006 Master Trump: __________ (PASS / FAIL)
- BUG-V007 Scoring Penalties: __________ (PASS / FAIL)
- BUG-V008 Dashboard Display: ✅ RESOLVED (PASS / FAIL)

### Overall Assessment

**Total Bugs Tested:** ______ / 15
**Bugs Passing:** ______
**Bugs Failing:** ______
**Pass Rate:** ______%

**Production Ready?** YES / NO / NEEDS WORK

**Critical Blockers Remaining:** ______

**Notes/Observations:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

**Recommended Next Steps:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

**Print this checklist and use it for systematic testing!**

Each bug has:
- ☐ Checkbox to mark when tested
- Clear test steps
- PASS/FAIL criteria
- Space for notes

Test in order: CRITICAL → HIGH → MEDIUM → LOW → VERIFIED
