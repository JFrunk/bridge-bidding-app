# Residual Issues to Address

This document tracks known bugs, inconsistencies, and potential improvements that need investigation and fixes.

---

## 🔴 CRITICAL: First Hand After Server Startup - Illegal Bidding Sequence

**Status:** Not Reproduced / Intermittent
**Priority:** HIGH
**Reported:** 2025-10-10
**Evidence:** `backend/review_requests/hand_2025-10-10_16-25-00.json`

### Problem Description

On the first hand dealt after server startup, all three AI players (North, East, South) bid **1NT** sequentially, which violates bridge bidding rules (cannot bid at same level unless higher denomination).

**Observed Behavior:**
```
Auction: [1NT, 1NT, 1NT, Pass]
- North: 1NT (correct - 17 HCP, balanced 2-4-3-4)
- East: 1NT (ILLEGAL - should Pass or overcall at 2-level)
- South: 1NT (ILLEGAL - same issue)
- West: Pass
```

### Root Cause Analysis

All three AI players received **North's hand** (17 HCP, 2-4-3-4 distribution) instead of their own hands:
- North had 17 HCP, balanced (correct to bid 1NT)
- East had 9 HCP, balanced (should Pass over 1NT)
- South had 8 HCP (should respond to partner's 1NT, not open 1NT)
- West had 6 HCP (correct to Pass)

**Evidence:**
- All three explanations show identical hand data: "HCP: 17 (requires 15-17), Distribution: 2-4-3-4"
- The review request file shows correct hands were dealt and saved
- Bug occurs during bidding, not during dealing

### Investigation Findings

**What's NOT the issue:**
1. ✅ Hand dealing logic works correctly (creates 4 different Hand objects)
2. ✅ Hands are correctly saved to `current_deal` dictionary
3. ✅ Bidding engine logic works when given correct hands
4. ✅ Legality checking exists and functions properly

**What IS the issue:**
- Backend's `/api/get-next-bid` endpoint returns North's hand for all players
- Likely caused by one of:
  1. **Race condition**: Multiple AI requests fire before state updates complete
  2. **State management bug**: `current_deal` global variable access issue
  3. **Parameter passing bug**: `current_player` not correctly sent/received
  4. **Frontend state capture**: `const currentPlayer = players[nextPlayerIndex]` captures stale values

### Reproduction Status

- ❌ Could not reliably reproduce in testing
- ❌ Appears to be intermittent/timing-dependent
- ✅ Happens specifically on first hand after server startup

### Proposed Solutions

#### Short-term (Defensive Programming):

1. **Add request logging in `/api/get-next-bid`:**
   ```python
   print(f"DEBUG: current_player={current_player}, hand_hcp={player_hand.hcp}")
   ```

2. **Add validation:**
   ```python
   if current_player not in ['North', 'East', 'South', 'West']:
       return jsonify({'error': f'Invalid player: {current_player}'}), 400

   if not player_hand:
       return jsonify({'error': f'No hand for {current_player}'}), 400
   ```

3. **Add request ID tracking** to detect duplicate/concurrent requests

4. **Add assertion in bidding engine:**
   ```python
   assert player_hand.hcp != current_deal['North'].hcp or current_player == 'North', \
          "Player received wrong hand!"
   ```

#### Long-term (Architectural):

1. **Refactor state management**: Move from global `current_deal` to session-based storage
2. **Add request queuing**: Ensure AI bids are processed sequentially, not concurrently
3. **Frontend debouncing**: Add delay/lock to prevent rapid-fire AI requests
4. **Add hand verification**: Include player position in Hand object for validation

### Files to Review

- `backend/server.py:135-153` - `/api/get-next-bid` endpoint
- `backend/server.py:24` - `current_deal` global initialization
- `frontend/src/App.js:413-435` - AI bidding loop
- `frontend/src/App.js:417-418` - State capture logic
- `backend/engine/bidding_engine.py:122-135` - Legality checking (why didn't it catch this?)

### Testing Checklist

- [ ] Add integration test that simulates rapid concurrent requests
- [ ] Add test for first hand after server restart
- [ ] Add logging to production to capture if bug occurs in the wild
- [ ] Test with frontend React.StrictMode (double-renders in dev)
- [ ] Test with network latency simulation

### Related Issues

- None currently

---

## 🟡 MODERATE: Convention Modules Have Incomplete Logic

**Status:** Documented / Partially Fixed
**Priority:** MEDIUM
**Reported:** 2025-10-10
**Evidence:** `CONVENTION_FIXES_PUNCHLIST.md`

### Problem Description

Many convention modules have incomplete or incorrect logic that results in suboptimal bidding. A comprehensive review identified **33 issues** across all convention modules.

### Critical Convention Issues (13 total)

From `CONVENTION_FIXES_PUNCHLIST.md`:

1. **Takeout Doubles** - HCP requirement too high (13+ instead of 12+)
2. **Takeout Doubles** - Missing ConventionModule interface
3. **Jacoby Transfers** - Missing post-transfer continuation logic
4. **Stayman** - Missing responder rebid after 2♦ response
5. **Stayman** - Missing responder rebid after finding fit
6. **Jacoby Transfers** - Incorrect super-accept logic (checks for doubleton instead of 4-card support!)
7. **Blackwood** - Insufficient trigger logic
8. **Blackwood** - Missing signoff logic after ace response
9. **Blackwood** - Missing 5NT king-asking logic
10. **Negative Doubles** - Incorrect applicability check
11. **Negative Doubles** - Point range not level-adjusted
12. **Preempts** - Missing response logic completeness
13. **Preempts** - No 3-level or 4-level preempts

### Impact

- Some conventions never trigger when they should
- Some trigger at wrong times
- Auctions stall or take incorrect paths
- Missing important bidding sequences

### Files to Review

- `backend/engine/ai/conventions/takeout_doubles.py`
- `backend/engine/ai/conventions/jacoby_transfers.py`
- `backend/engine/ai/conventions/stayman.py`
- `backend/engine/ai/conventions/blackwood.py`
- `backend/engine/ai/conventions/negative_doubles.py`
- `backend/engine/ai/conventions/preempts.py`
- `backend/engine/responses.py`
- `backend/engine/rebids.py`
- `backend/engine/overcalls.py`
- `backend/engine/advancer_bids.py`

### Progress

See detailed status in `CONVENTION_FIXES_PUNCHLIST.md`. Many issues marked with checkboxes showing completion status.

### Related Issues

- **Issue #1** (First Hand Bug) - May be related to convention module selection logic

---

## 🟢 MINOR: Card Play Phase Missing Features

**Status:** Documented
**Priority:** LOW
**Reported:** 2025-10-10
**Evidence:** `PHASE1_COMPLETE.md`

### Problem Description

Card play phase (Phase 1 MVP) is functional but missing several nice-to-have features for better user experience.

### Missing Features

From `PHASE1_COMPLETE.md` known issues section:

1. **Play History UI** - No visual display of completed tricks
2. **Undo/Redo** - Cannot undo last card play
3. **Claim Feature** - Cannot claim remaining tricks
4. **Play Analysis** - No feedback on card play decisions
5. **Visual Animations** - Cards don't animate moving to center
6. **Sound Effects** - No audio feedback for card play
7. **Save/Load** - Cannot save or load game state mid-play
8. **Legal Card Highlighting** - No visual indicator of playable cards
9. **Manual Play Trigger** - No button to manually start play phase (debugging)
10. **Better Error Messages** - Generic error messages for illegal plays

### Impact

Minimal - core functionality works, these are enhancements only.

### Related Issues

None

---

## 🟢 MINOR: Placeholder Convention Modules Not Implemented

**Status:** Not Started
**Priority:** LOW
**Reported:** 2025-10-10
**Evidence:** `CONVENTION_FIXES_PUNCHLIST.md`, empty convention files

### Problem Description

Four advanced convention modules exist as placeholder files with no implementation.

### Missing Conventions

1. **Michaels Cuebid** (`michaels_cuebid.py`) - Shows 5-5+ in two suits
2. **Unusual 2NT** (`unusual_2nt.py`) - Shows 5-5+ in both minors
3. **Splinter Bids** (`splinter_bids.py`) - Shows singleton/void with support
4. **Fourth Suit Forcing** (`fourth_suit_forcing.py`) - Artificial game force

### Impact

These are advanced conventions not essential for SAYC basic play. Most casual players won't miss them.

### Priority Rationale

LOW because:
- Core SAYC works without them
- They're advanced techniques
- Simpler conventions (Stayman, Jacoby, Blackwood) work and cover most needs
- Can be added incrementally as requested

### Files to Review

- `backend/engine/ai/conventions/michaels_cuebid.py`
- `backend/engine/ai/conventions/unusual_2nt.py`
- `backend/engine/ai/conventions/splinter_bids.py`
- `backend/engine/ai/conventions/fourth_suit_forcing.py`

---

## ✅ FIXED: Card Play Phase Failed to Start (KeyError)

**Status:** Fixed
**Priority:** ~~HIGH~~ RESOLVED
**Reported:** 2025-10-10 15:36:50
**Evidence:** `BUG_FIX_CARD_PLAY.md`, `backend/review_requests/hand_2025-10-10_15-36-50.json`

### Problem Description

When bidding completed, clicking to start card play phase resulted in HTTP 500 error with `KeyError: 'N'`.

### Root Cause

Key naming mismatch: `current_deal` uses full names ('North', 'East', etc.) but play phase code tried to access with single letters ('N', 'E', etc.).

### Solution Implemented

Added position name mapping in `server.py`:
```python
pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
```

### Files Changed

- `backend/server.py:365-372` - Added position mapping

### Status

✅ **FIXED** - Documented in `BUG_FIX_CARD_PLAY.md`

---

## ✅ FIXED: Weak Two Preempts with Voids

**Status:** Fixed
**Priority:** ~~HIGH~~ RESOLVED
**Reported:** 2025-10-10
**Evidence:** `BIDDING_FIXES_2025-10-10.md`

### Problem Description

System allowed weak 2-level preempts with voids and 4-card side majors, violating SAYC rules.

### Example

North opened 2♥ with: ♠AJ5 ♥QJ862 ♦J965 ♣void (VOID in clubs - should Pass)

### Solution Implemented

Added `_is_valid_weak_two()` method checking for:
- No voids
- No singleton aces
- No 4-card side major

### Files Changed

- `backend/engine/ai/conventions/preempts.py`

### Status

✅ **FIXED** - Documented in `BIDDING_FIXES_2025-10-10.md`

---

## ✅ FIXED: Strong Balanced Hands (19+ HCP) Passed Instead of Doubling

**Status:** Fixed
**Priority:** ~~HIGH~~ RESOLVED
**Reported:** 2025-10-10
**Evidence:** `BIDDING_FIXES_2025-10-10.md`

### Problem Description

With 19+ HCP balanced hands, system passed after opponent opened instead of competing.

### Example

West passed with: ♠Q982 ♥A7 ♦AKT ♣AQ76 (19 HCP, balanced - should Double)

### Solution Implemented

Updated `TakeoutDoubleConvention` to double with 19+ HCP balanced, planning to bid NT later.

### Files Changed

- `backend/engine/ai/conventions/takeout_doubles.py`

### Status

✅ **FIXED** - Documented in `BIDDING_FIXES_2025-10-10.md`

---

## 📝 Template for New Issues

### Issue Title

**Status:** [Not Started / In Progress / Fixed / Won't Fix]
**Priority:** [LOW / MEDIUM / HIGH / CRITICAL]
**Reported:** YYYY-MM-DD
**Evidence:** File paths or descriptions

#### Problem Description
What's wrong?

#### Root Cause Analysis
Why is it happening?

#### Proposed Solutions
How to fix it?

#### Files to Review
Relevant file paths

---

## 📊 Summary Statistics

**Total Issues Tracked:** 8

**By Status:**
- 🔴 Critical/Open: 1
- 🟡 Moderate/Open: 1
- 🟢 Minor/Open: 2
- ✅ Fixed/Closed: 3
- 📝 Documented: 1

**By Priority:**
- HIGH: 1
- MEDIUM: 1
- LOW: 3
- RESOLVED: 3

**Top Priority Items:**
1. First Hand After Server Startup bug (intermittent, hard to reproduce)
2. Convention module improvements (documented, partially addressed)
3. Card play enhancements (nice-to-have)

---

*Last Updated: 2025-10-10*
