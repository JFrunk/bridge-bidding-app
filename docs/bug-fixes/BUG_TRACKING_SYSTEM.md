# Bug Tracking System - Bridge Bidding Application
**Created:** 2025-10-18
**Purpose:** Centralized bug tracking with priority, status, and user testing instructions

---

## 📋 How to Use This Document

When you report a bug in chat:
1. I will add it to this document under the appropriate priority section
2. Assign it a unique bug ID (BUG-XXX)
3. Create a test plan so you can verify the fix
4. Track status: 🔴 Active → 🔄 In Progress → ✅ Fixed → ✔️ Verified

**Color Key:**
- 🔴 **CRITICAL** - Production blocking, must fix immediately
- 🟡 **HIGH** - Should fix before launch, major impact
- 🟢 **MEDIUM** - Fix soon, moderate impact
- 🟢 **LOW** - Nice to have, minor impact
- ✅ **FIXED** - Code fixed, awaiting verification
- ✔️ **VERIFIED** - User confirmed bug is resolved

---

## 🔴 CRITICAL BUGS (Production Blockers)

### BUG-C001: Login "Failed to Fetch" Error
**Status:** 🔴 Active
**Severity:** CRITICAL - Users cannot login
**Discovered:** 2025-10-18
**Area:** Authentication / Backend Connection
**Documentation:** [PRODUCTION_BUGS_AND_TEST_PLAN.md](PRODUCTION_BUGS_AND_TEST_PLAN.md#bug-010-login-screen-failed-to-fetch-error)

#### Problem
When users attempt to login via email authentication screen, they receive "Failed to fetch" error.

#### Symptoms
- Enter email → Click "Continue" → Error: "Failed to fetch"
- No network request reaches backend
- Cannot create accounts or login

#### Root Cause
Frontend expects backend on `http://localhost:5001` but backend may be running on `http://localhost:5000` (port mismatch).

#### How to Test if Bug is Fixed
```bash
# 1. Start backend
cd backend
python3 server.py
# Wait for: "Running on http://127.0.0.1:5000"

# 2. Check frontend .env file
cat frontend/.env
# Should show: REACT_APP_API_URL=http://localhost:5000

# 3. Start frontend
cd frontend
npm start

# 4. Try to login
# Open http://localhost:3000
# Click login button
# Enter email: test@example.com
# Click "Continue"
# ✅ PASS: Login succeeds, no "Failed to fetch" error
# ❌ FAIL: Still shows "Failed to fetch"
```

#### Files Involved
- `frontend/src/contexts/AuthContext.jsx` (line 5) - API URL config
- `frontend/src/components/auth/SimpleLogin.jsx` (lines 14-50) - Login handler
- `backend/server.py` (lines 120-122) - Auth endpoints

---

### BUG-C002: DDS Crashes on macOS During Gameplay (Error Code -14)
**Status:** 🔴 Active
**Severity:** CRITICAL - System crash during gameplay
**Discovered:** 2025-10-18 at 18:17
**Area:** Card Play AI / DDS Integration
**Documentation:** [BUG_DDS_CRASH_2025-10-18.md](BUG_DDS_CRASH_2025-10-18.md)

#### Problem
DDS (Double Dummy Solver) crashes during active gameplay on macOS with Error Code -14 ("Too few cards" or invalid deal structure). System generates dump.txt crash file and game becomes unusable.

#### Symptoms
- Playing hand with Expert AI mode active
- Mid-game crash with DDS Error Code -14
- dump.txt file created in project root
- Complete game failure, no recovery

#### Root Cause
**Triple failure:**
1. **DDS initialized on macOS despite known instability** - server.py creates DDSPlayAI() at startup if endplay installed
2. **User can manually select Expert mode** - UI allows switching to Expert which uses unstable DDS
3. **Smart default may enable Expert** - Auto-detection enables Expert if DDS_AVAILABLE=True, even on macOS

**Known issue:** DDS is fundamentally unstable on macOS M1/M2 (40-60% success rate, segmentation faults)

#### Evidence
**dump.txt created Oct 18, 2025 at 18:17:**
```
Error code=-14
trump=H
first=N
[Deal with 4 hands showing invalid structure]
```

#### How to Test if Bug is Fixed
```bash
# Test 1: Verify DDS blocked on macOS
PYTHONPATH=backend python3 -c "
import platform
print(f'Platform: {platform.system()}')
from core.session_state import DEFAULT_AI_DIFFICULTY
print(f'Default AI: {DEFAULT_AI_DIFFICULTY}')
from server import DDS_AVAILABLE, ai_instances
print(f'DDS Available: {DDS_AVAILABLE}')
print(f'Expert AI: {ai_instances[\"expert\"].get_name()}')
"
# ✅ PASS on macOS:
#    Platform: Darwin
#    Default AI: advanced
#    DDS Available: False
#    Expert AI: Minimax AI (depth 4)

# Test 2: Play 10 hands with Expert mode
# Click "Expert" in AI difficulty selector
# Play 10 complete hands
# ✅ PASS: All hands complete, no crashes, no dump.txt
# ❌ FAIL: Any DDS crash or dump.txt created

# Test 3: Verify production (Linux) still uses DDS
# Deploy to Linux staging
# Check Expert AI uses DDSPlayAI
# ✅ PASS: Expert AI = "Double Dummy Solver AI"
```

#### Files Involved
- `backend/server.py` (lines 27-38, 66-73) - DDS initialization, AI instances
- `backend/core/session_state.py` (lines 47-72) - Smart default logic
- `backend/engine/play/ai/dds_ai.py` - DDS implementation

#### Fix Required
1. **Add platform detection** - Block DDS initialization on macOS
2. **Force Advanced default on macOS** - Override smart default
3. **Safe AI instances** - Never create DDSPlayAI on macOS
4. **UI indicator** - Show why Expert uses Minimax fallback

**Status:** ✅ FIXED - Awaiting User Verification
**Fix Documentation:** [BUG_C002_FIX_SUMMARY.md](BUG_C002_FIX_SUMMARY.md)

#### Fix Implemented
1. ✅ Platform detection blocks DDS on macOS (server.py)
2. ✅ Force Advanced default on macOS (session_state.py)
3. ✅ Safe AI initialization - never creates DDSPlayAI on macOS
4. ✅ Clear logging explains why DDS disabled

#### Test Results (Automated)
```
✅ PASS: DDS correctly disabled on macOS
✅ PASS: Platform check correctly blocking DDS
✅ PASS: Default correctly set to advanced
✅ PASS: Expert using Minimax fallback (no DDS crashes)
```

#### User Verification Needed
Please test:
1. [ ] Restart backend server - verify "DDS DISABLED on Darwin" message
2. [ ] Check default AI is "advanced"
3. [ ] Select Expert mode and play 5-10 hands
4. [ ] Verify no crashes, no new dump.txt files
5. [ ] Mark as ✔️ VERIFIED if all tests pass

---

## 🟡 HIGH PRIORITY BUGS (Fix Before Launch)

### BUG-H001: AI Level Display Mismatch (Selected vs Active)
**Status:** 🔴 Active
**Severity:** HIGH - User sees wrong AI difficulty
**Discovered:** 2025-10-18
**Area:** Frontend State Management / AI Selection
**Documentation:** [AI_LEVEL_BUGS_2025-10-18.md](AI_LEVEL_BUGS_2025-10-18.md#bug-1-ai-level-mismatch---selected-vs-active-priority-1)

#### Problem
- User has "Intermediate" (7.5/10) selected in AI Level dropdown button
- DDS Status Indicator shows "DDS Expert AI Active" (9/10)
- Actual AI behavior matches Expert (9/10), not Intermediate

#### Symptoms
- Button shows one difficulty, DDS Status shows another
- After page refresh, selected button doesn't match backend state
- User thinks they're playing against weaker AI than they actually are

#### Root Cause
Frontend component initializes with hardcoded `'intermediate'` default before fetching actual difficulty from backend. Race condition or state update doesn't propagate to UI button.

#### How to Test if Bug is Fixed
```bash
# 1. Start application
cd backend && python3 server.py
cd frontend && npm start

# 2. Load page and start play phase
# Open http://localhost:3000
# Click "Play Random Hand"

# 3. Check AI difficulty displays
# Look at AI Difficulty Selector button
# Look at DDS Status Indicator
# ✅ PASS: Both show same difficulty level
# ❌ FAIL: Button shows "Intermediate" but Status shows "Expert"

# 4. Refresh page
# Press F5 to reload
# ✅ PASS: Button shows same difficulty as before refresh
# ❌ FAIL: Button resets to default despite backend having different value
```

#### Files Involved
- `frontend/src/components/AIDifficultySelector.jsx` (line 38) - Hardcoded default
- `frontend/src/components/DDSStatusIndicator.jsx` - Status display
- `backend/core/session_state.py` (lines 47-72) - Backend default logic

---

### BUG-H002: Expert AI Discards High Cards (Kings) When Low Cards Available
**Status:** ✅ RESOLVED - Fixed with discard penalty in minimax AI (2025-10-18)
**Severity:** HIGH - AI appears broken, user trust lost
**Discovered:** 2025-10-18
**Last Occurrence:** 2025-10-18 (Trick 5, NT contract, East discarded K♣)
**Fixed:** 2025-10-18 - Added explicit discard penalty for honor cards
**Area:** Card Play AI / Minimax Evaluation / NT Discard Logic
**Documentation:** [DISCARD_BUG_FIX_COMPLETE.md](DISCARD_BUG_FIX_COMPLETE.md), [BUG_ANALYSIS_AND_FIX_SUMMARY.md](BUG_ANALYSIS_AND_FIX_SUMMARY.md), [BUG_H002_KING_DISCARD_ANALYSIS.md](BUG_H002_KING_DISCARD_ANALYSIS.md)

#### Problem
Expert AI (8/10, 9/10) discarded high-value cards (Kings, Queens) when low cards from weak suits were available.

**Root Cause:** The evaluation function assigned +0.6 "communication bonus" to Kings (as potential entries), even in discard situations where they had no entry value. This caused minimax to prefer keeping Kings over low cards.

#### Example
- East (Expert AI) void in spades, must discard
- East holds: ♥QT8 ♦T76 ♣KJT963
- North leads ♠7 (opponent's winning trick)
- **Expected:** Discard ♦6 or ♦7
- **Actual (BUG):** Discarded ♣K ❌
- **Fixed:** Now discards ♣2 or low diamond ✅

#### User Quote
> "How do you explain an 8/10 AI playing a king in this situation. That is not 8/10 play but more like 4/10."

#### Solution Implemented
Added `_calculate_discard_penalty()` method to Minimax AI that applies strong penalties when discarding honors:
- King: -1.5 penalty
- Queen: -1.0 penalty
- Jack: -0.5 penalty
- Ten: -0.2 penalty
- Low cards (2-9): no penalty

This overrides the +0.6 communication bonus and ensures AI prefers discarding low cards.

#### Fixes Applied (All Versions)
✅ AI card validation before playing (previous fix)
✅ Improved discard logic in Minimax AI (previous fix)
✅ Tolerance-based tiebreaker to prefer low cards (previous fix)
✅ DDS fallback heuristics improved (previous fix)
✅ **NEW: Explicit discard penalty for honor cards** (2025-10-18)

#### How to Test if Bug is Fixed
```bash
# Run automated test (original scenario)
PYTHONPATH=backend python3 test_discard_fix.py
# ✅ PASS: Output shows "✅ ALL TESTS PASSED - AI correctly discards low cards"
# ✅ PASS: AI chose ♣2 (not ♣K)

# Run trick 5 NT test (user's specific scenario)
PYTHONPATH=backend python3 test_trick5_nt_discard.py
# ✅ PASS: AI chose 2♣ instead of K♣

# Manual test: Play 10 hands at Expert level
# 1. Start app, set AI to "Expert" (9/10)
# 2. Play 10 random hands
# 3. Watch for any discard situations (when AI is void in led suit)
# 4. ✅ PASS: AI discards low cards (2-7) in 100% of cases
```

#### Files Modified
- `backend/engine/play/ai/minimax_ai.py` (lines 153-157, 490-526) - **NEW: Discard penalty**
- `backend/engine/play/ai/minimax_ai.py` (lines 364-430, 167-208) - Previous fixes
- `backend/engine/play/ai/dds_ai.py` (lines 380-412) - Previous fixes
- `backend/server.py` (lines 1583-1615) - Validation (previous fix)

#### Tests Added
- `test_discard_fix.py` - Original test case (now passes)
- `test_trick5_nt_discard.py` - **NEW: User's specific trick 5 scenario** (passes)

---

### BUG-H003: First Hand After Server Restart - Illegal Bidding Sequence
**Status:** 🔴 Active (Intermittent)
**Severity:** HIGH - First impression is broken game
**Discovered:** 2025-10-10
**Area:** Bidding Engine / State Management
**Documentation:** [PRODUCTION_BUGS_AND_TEST_PLAN.md](PRODUCTION_BUGS_AND_TEST_PLAN.md#bug-002-first-hand-after-server-startup---illegal-bidding-sequence)

#### Problem
On the **first hand dealt after server startup**, all three AI players sometimes bid identically (e.g., all bid 1NT), which violates bridge rules.

#### Example
```
Auction: [1NT, 1NT, 1NT, Pass]
- North: 1NT (17 HCP, balanced) ✅ Legal
- East: 1NT (9 HCP, balanced) ❌ ILLEGAL - should Pass
- South: 1NT (8 HCP) ❌ ILLEGAL - can't bid same level
- West: Pass ✅ Legal
```

#### Evidence
All three AI players received **North's hand data** instead of their own hands during bidding.

#### How to Test if Bug is Fixed
```bash
# Test requires server restart
# 1. Stop backend
pkill -f "python.*server.py"

# 2. Clear session data
rm backend/bridge.db  # Optional: clears session state

# 3. Start backend
cd backend
python3 server.py

# 4. Start frontend
cd frontend
npm start

# 5. Deal FIRST hand after restart
# Open http://localhost:3000
# Click "Deal New Hand"
# Watch first 4 bids carefully

# ✅ PASS: Each player bids according to their own hand
#          No duplicate bids at same level
#          Bids are legal given hand HCP
# ❌ FAIL: All three AI players bid the same thing (e.g., all 1NT)

# 6. Repeat test 10 times (it's intermittent)
# Stop server, restart, deal first hand, observe bidding
# ✅ PASS: 10/10 hands have legal bidding sequences
# ❌ FAIL: Any hand shows duplicate bids
```

#### Files Involved
- `backend/server.py` - `/api/get-next-bid` endpoint
- `frontend/src/App.js` - AI bidding loop
- `backend/core/session_state.py` - Deal storage

---

## 🟢 MEDIUM PRIORITY BUGS (Fix Soon)

### BUG-M001: Declarer's Hand Not Visible When User is Dummy
**Status:** ✅ Fixed (2025-10-18)
**Severity:** MEDIUM - Game breaking in specific scenario
**Discovered:** 2025-10-18
**Area:** Card Play Display
**Documentation:** [BUG_FIX_DECLARER_HAND_NOT_VISIBLE_2025-10-18.md](BUG_FIX_DECLARER_HAND_NOT_VISIBLE_2025-10-18.md)

#### Problem
When user (South) is dummy and another position (North) is declarer, the declarer's hand was not displaying on screen.

#### Scenario
- Contract: 3NT by North (North is declarer)
- South is dummy (user position)
- User should see AND control North's cards
- **Bug:** North's hand was not displaying at all

#### Fix Applied
Updated App.js to use `visible_hands` data structure that backend already provides. No longer makes separate API call that was failing.

#### How to Test if Bug is Fixed
```bash
# 1. Start app
cd backend && python3 server.py
cd frontend && npm start

# 2. Play hands until you get scenario where North declares
# (or force it by making North open strong and become declarer)

# When North is declarer and South is dummy:
# ✅ PASS: You see both North's hand (top) and South's hand (bottom)
# ✅ PASS: You can click cards in North's hand to play them
# ✅ PASS: Both hands update as cards are played
# ❌ FAIL: North's hand is missing/blank

# Edge case: Test when East or West declares
# ✅ PASS: Dummy hand still displays correctly
```

#### Files Modified
- `frontend/src/App.js` (4 locations: lines 347-372, 832-851, 888-907, 1095-1121)

**Status:** ✅ Code fixed, needs user verification

---

### BUG-M002: Replay Hand Button Crashes - "Position W has no cards"
**Status:** ✅ Fixed (2025-10-16)
**Severity:** MEDIUM - Replay feature broken
**Discovered:** 2025-10-16
**Area:** Replay Functionality / State Management
**Documentation:** [REPLAY_BUG_FIX_2025-10-16.md](REPLAY_BUG_FIX_2025-10-16.md)

#### Problem
When pressing "Replay Hand" button after completing a hand, the application crashes with error:
```
AI play failed: Position W has no cards in hand - possible state corruption
```

#### Root Cause
Review request captured hand state **after all 13 tricks completed**, resulting in all players having empty hands. Backend didn't preserve original 13-card deal before play began.

#### Fix Applied
Added `original_deal` field to SessionState that preserves original 13-card hands before play begins. Replay functionality now uses this preserved state.

#### How to Test if Bug is Fixed
```bash
# 1. Start app and play a complete hand
cd backend && python3 server.py
cd frontend && npm start

# 2. Play through all 13 tricks until hand is complete
# Let AI play all positions for speed, or play yourself

# 3. After hand completes, click "Replay Hand" button
# ✅ PASS: Hand restarts with all 13 cards in each position
# ✅ PASS: Can play through entire hand again
# ✅ PASS: Can replay multiple times
# ❌ FAIL: Error message "Position W has no cards"
# ❌ FAIL: Crash or blank screen

# 4. Test with "Play Random Hand" as well
# Click "Play Random Hand" → Complete hand → Click "Replay Hand"
# ✅ PASS: Replay works
```

#### Files Modified
- `backend/core/session_state.py` - Added `original_deal` field
- `backend/server.py` (lines 1003-1048, 1178-1184) - Preserve and restore logic
- `frontend/src/App.js` (lines 850-853) - Pass `replay: true` flag

**Status:** ✅ Code fixed, needs user verification

---

### BUG-M003: Hand Display Data Presentation Confusion
**Status:** 🔴 Active (Documentation improvement needed)
**Severity:** MEDIUM - Confusing but not broken
**Discovered:** 2025-10-18
**Area:** Review Data / Hand Display
**Documentation:** [BUG_REPORT_IMPOSSIBLE_CARD_PLAY_2025-10-18.md](BUG_REPORT_IMPOSSIBLE_CARD_PLAY_2025-10-18.md#secondary-issue-confusing-data-presentation)

#### Problem
Review request data is confusing because it shows hand state in two different ways:
1. **Hand.cards** - Current cards in hand (updated as cards played)
2. **Hand.suit_hcp** - HCP from original 13-card deal (immutable)

This makes it **appear** like a player played a card they didn't have.

#### Example
```
Trick 2: East discarded ♣K

Review Data (requested after trick):
  East's cards: ♠A5 ♥QT8 ♦T76 ♣JT963  ← No King!
  East's suit_hcp: ♣: 4  ← 4 HCP = K+J (suggests King exists)

User thinks: "East played ♣K but doesn't have it!"
Reality: East HAD ♣K originally, played it, now removed from cards list
```

#### How to Test if Bug is Fixed
After fix is implemented, review data should clearly show:
```
East's Hand Review:
  Original (13 cards): ♠A5 ♥QT8 ♦T76 ♣KJT9632
  Played so far (2 cards): ♣K, ♣2
  Current (11 cards): ♠A5 ♥QT8 ♦T76 ♣JT963
  HCP (original): 11

✅ PASS: Clear separation of original vs current vs played
✅ PASS: Note explaining HCP reflects original deal
❌ FAIL: Still confusing which cards were played
```

#### Proposed Fix
Add played cards tracking to Hand class and improve review display to show original/current/played cards separately.

---

## 🟢 LOW PRIORITY BUGS (Nice to Have)

### BUG-L001: 5 Play Tests Failing - Hand Parser Creates 14-Card Hands
**Status:** 🔴 Active
**Severity:** LOW - Test failures only, no production impact
**Discovered:** 2025-10-12
**Area:** Test Infrastructure
**Documentation:** [PRODUCTION_BUGS_AND_TEST_PLAN.md](PRODUCTION_BUGS_AND_TEST_PLAN.md#bug-004-5-play-tests-failing---hand-parser-issue)

#### Problem
5 play engine tests fail because test helper function creates 14-card hands instead of 13-card hands.

**Failing Tests:**
- Some in `tests/play/test_evaluation.py`
- Some in `tests/play/test_minimax_ai.py`

**Note:** This does NOT affect production gameplay, only test helpers.

#### How to Test if Bug is Fixed
```bash
# Run play tests
cd backend
python3 -m pytest tests/play/ -v

# ✅ PASS: 45/45 tests passing (100%)
# ❌ FAIL: Still shows 40/45 passing with hand parsing errors
```

#### Files Involved
- `tests/play_test_helpers.py` - `parse_hand()` function

---

### BUG-L002: DDS Status Display Order Mismatch
**Status:** 🔴 Active
**Severity:** LOW - Cosmetic inconsistency
**Discovered:** 2025-10-18
**Area:** Frontend UI Display
**Documentation:** [AI_LEVEL_BUGS_2025-10-18.md](AI_LEVEL_BUGS_2025-10-18.md#bug-2-dds-status-display-order-mismatch)

#### Problem
AI difficulty levels shown in DDS Status Indicator dropdown don't match the order in the AI Difficulty Selector button.

**Button Order (desired):**
1. 🌱 Beginner (6/10)
2. 📚 Intermediate (7.5/10)
3. 🎯 Advanced (8/10)
4. 🏆 Expert (9/10)

**DDS Status Order (current):**
- Uses `Object.entries()` which doesn't guarantee order
- May appear in random order

#### How to Test if Bug is Fixed
```bash
# 1. Open app and start play phase
# 2. Click DDS Status Indicator to expand dropdown
# 3. Look at difficulty levels listed

# ✅ PASS: Levels appear in order: Beginner, Intermediate, Advanced, Expert
# ✅ PASS: Same order as in AI Difficulty Selector button
# ❌ FAIL: Levels in different order or random order
```

#### Files Involved
- `frontend/src/components/DDSStatusIndicator.jsx` (line 111)

---

## ✔️ VERIFIED BUGS (Fixed and User Confirmed)

### BUG-V001: AI Auto-Bidding for User Position (Race Condition)
**Status:** ✔️ Verified
**Severity:** HIGH (was)
**Fixed:** 2025-10-17
**Verified:** 2025-10-17
**Area:** Bidding UI / AI Control
**Documentation:** [USER_CONTROL_FIXES_2025-10-17.md](USER_CONTROL_FIXES_2025-10-17.md#fix-1-ai-auto-bidding-for-user-position)

#### Problem
AI was occasionally making bids for South (user's position) due to race condition.

#### Fix
Two-layer defense in `App.js`:
1. Early exit check before AI bidding logic
2. Defense-in-depth inside async function

#### User Testing Confirmed
✅ User can now bid their own hand in all scenarios
✅ No AI auto-bidding for South position
✅ Works for all dealer positions

---

### BUG-V002: Automatic Play Phase Transition (Removed User Control)
**Status:** ✔️ Verified
**Severity:** MEDIUM (was)
**Fixed:** 2025-10-17
**Verified:** 2025-10-17
**Area:** User Control / UI Flow
**Documentation:** [USER_CONTROL_FIXES_2025-10-17.md](USER_CONTROL_FIXES_2025-10-17.md#fix-2-automatic-transition-from-bidding-to-playing)

#### Problem
After bidding completed, system automatically transitioned to play phase after 3 seconds, preventing users from reviewing contract.

#### Fix
Removed automatic transition. User must click "Play This Hand" button to start playing.

#### User Testing Confirmed
✅ "Play This Hand" button appears after bidding ends
✅ No automatic countdown to play phase
✅ User controls when to start playing

---

### BUG-V003: AI Card Play Validation Missing
**Status:** ✔️ Verified
**Severity:** CRITICAL (was)
**Fixed:** 2025-10-18
**Verified:** 2025-10-18
**Area:** Card Play Engine
**Documentation:** [BUG_REPORT_IMPOSSIBLE_CARD_PLAY_2025-10-18.md](BUG_REPORT_IMPOSSIBLE_CARD_PLAY_2025-10-18.md#fixes-implemented)

#### Problem
No validation that AI-chosen card was actually in hand before playing it. If AI had bug and returned invalid card, game state would become corrupted.

#### Fix
Added comprehensive validation in `server.py` (lines 1583-1615):
- Validates card is in hand
- Validates card is legal (follow suit rules)
- Only then plays card

#### User Testing Confirmed
✅ No more "impossible card" plays
✅ Clear error messages if AI has bugs
✅ Game state protected from corruption

---

### BUG-V004: Minimax AI Inverted Logic for Defenders
**Status:** ✔️ Verified
**Severity:** CRITICAL (was)
**Fixed:** 2025-10-18
**Verified:** 2025-10-18
**Area:** Card Play AI / Minimax
**Documentation:** [CRITICAL_BUG_FIX_2025-10-18.md](CRITICAL_BUG_FIX_2025-10-18.md)

#### Problem
Minimax maximization/minimization logic was inverted for defenders, causing them to choose losing plays over winning plays.

#### Example
- North to play: 7♣ (wins trick), 5♣, 2♣ (loses trick)
- Evaluation: 7♣ = -2.82, 2♣ = -4.83
- **Before Fix:** AI chose 2♣ (minimized, chose worse score)
- **After Fix:** AI chose 7♣ (maximized, chose better score)

#### User Testing Confirmed
✅ Defenders now correctly choose winning plays
✅ AI plays at intended 8/10 level
✅ No more "stupidly wrong" plays

---

### BUG-V005: Missing Master Trump Detection
**Status:** ✔️ Verified
**Severity:** CRITICAL (was)
**Fixed:** 2025-10-18
**Verified:** 2025-10-18
**Area:** Card Play AI / Evaluation
**Documentation:** [CRITICAL_BUG_FIX_2025-10-18.md](CRITICAL_BUG_FIX_2025-10-18.md#bug-report-2-missing-master-trump-detection)

#### Problem
AI didn't recognize master trumps - trump cards guaranteed to win when opponents void or don't have higher trumps.

#### Example
- East has A♠ (only trump left), opponents void in spades
- **Before Fix:** Sure winners = 0.50 (counted as "somewhat reliable")
- **After Fix:** Sure winners = 1.50 (recognized as master trump)

#### User Testing Confirmed
✅ AI recognizes master trumps correctly
✅ Doesn't waste high cards when holding masters
✅ Improved play quality in trump contracts

---

### BUG-V006: Scoring System Reversed Penalties (Negative vs Positive)
**Status:** ✔️ Verified
**Severity:** HIGH (was)
**Fixed:** 2025-10-18
**Verified:** 2025-10-18
**Area:** Scoring System / Session Management
**Documentation:** [SCORING_FIX_SUMMARY.md](SCORING_FIX_SUMMARY.md)

#### Problem
Session scoring system had positive/negative points reversed. When declaring side went down (failed to make contract), the negative penalty was incorrectly added to their score instead of giving positive penalty points to the defending side.

#### Example
- NS declares 3NT, goes down 1
- **Before Fix (WRONG):** NS gets -50, EW gets 0
- **After Fix (CORRECT):** NS gets 0, EW gets +50 (defenders' reward)

#### Root Cause
In `session_manager.py`, the `add_hand_score()` method was simply adding the score (positive or negative) to the declaring side without checking if the contract was made or defeated.

#### Fix Applied
Updated `add_hand_score()` to correctly assign points:
- If score >= 0 (contract made): Points go to declaring side
- If score < 0 (contract defeated): Penalty points go to defending side

#### User Testing Confirmed
✅ Positive points always mean "winning the hand"
✅ Setting opponents (defeating their contract) gives positive points
✅ Session totals correctly reflect who is winning
✅ All 6 session scoring tests pass
✅ All 43 existing scoring tests still pass

#### Files Modified
- `backend/engine/session_manager.py` (lines 52-93) - Fixed penalty assignment
- `backend/test_session_scoring.py` (NEW) - Comprehensive test suite

---

## 📊 Bug Summary Statistics

### By Status
- 🔴 Active: 5 bugs
- 🔄 In Progress: 1 bug (BUG-H002)
- ✅ Fixed (awaiting verification): 3 bugs (BUG-M001, BUG-M002, **BUG-C002** ⬅️ NEW FIX)
- ✔️ Verified (user confirmed): 6 bugs (includes BUG-V006 Scoring)

### By Severity
- 🔴 CRITICAL: 2 bugs (BUG-C001, **BUG-C002** ⬅️ NEW)
- 🟡 HIGH: 3 bugs (BUG-H001, H002, H003)
- 🟢 MEDIUM: 3 bugs (BUG-M001, M002, M003)
- 🟢 LOW: 2 bugs (BUG-L001, L002)

### By Area
- **Authentication:** 1 bug
- **AI Selection/Display:** 2 bugs
- **Card Play AI / DDS:** 3 bugs (**+1 NEW**: BUG-C002)
- **Bidding Engine:** 1 bug
- **Display/UI:** 3 bugs
- **State Management:** 2 bugs
- **Scoring System:** 1 bug (BUG-V006 - Verified Fixed)
- **Test Infrastructure:** 1 bug

---

## 🎯 Next Bug Reporting

When you report a bug in chat, I will:

1. **Assign unique ID** - BUG-[Severity][Number] (e.g., BUG-H004)
2. **Document thoroughly:**
   - Problem description
   - Symptoms user sees
   - Root cause analysis (if known)
   - Files involved
3. **Create test plan** - Step-by-step instructions to verify fix
4. **Track status** - From 🔴 Active → ✅ Fixed → ✔️ Verified
5. **Cross-reference** - Link to detailed bug report files

---

## 📝 Bug Reporting Template

```markdown
### BUG-[ID]: [Short Title]
**Status:** 🔴 Active
**Severity:** [CRITICAL/HIGH/MEDIUM/LOW]
**Discovered:** YYYY-MM-DD
**Area:** [Component/Feature]
**Documentation:** [Link to detailed doc if exists]

#### Problem
[What's broken from user perspective]

#### Symptoms
- [What user sees/experiences]
- [Error messages]
- [Incorrect behavior]

#### Root Cause
[Why it's happening - if known]

#### How to Test if Bug is Fixed
[Step-by-step user testing instructions]
✅ PASS criteria
❌ FAIL criteria

#### Files Involved
- `path/to/file.py` (line X) - Description
```

---

**Last Updated:** 2025-10-18
**Total Bugs Tracked:** 15 (14 original + BUG-C002 DDS Crash + BUG-V006 Scoring)
**Critical Blockers:** 2 (BUG-C001, **BUG-C002** ⬅️ NEW)
**Verified Fixed:** 6 bugs (including BUG-V006 Scoring)
**Production Ready:** ⚠️ After BUG-C001 and **BUG-C002** fixed
