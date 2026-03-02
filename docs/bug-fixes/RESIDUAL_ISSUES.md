# Residual Issues to Address

This document tracks known bugs, inconsistencies, and potential improvements that need investigation and fixes.

**Last Updated:** 2026-01-01

---

## 📋 Issue Summary

### By Severity
| Severity | Open | Monitoring | Resolved | Total |
|----------|------|------------|----------|-------|
| 🔴 Critical | 0 | 1 | 0 | 1 |
| 🟡 Moderate | 0 | 0 | 1 | 1 |
| 🟢 Minor | 0 | 0 | 2 | 2 |
| ✅ Fixed | - | - | 3 | 3 |
| **Total** | **0** | **1** | **6** | **7** |

### By Application Area
| Area | Open | Monitoring | Resolved | Total |
|------|------|------------|----------|-------|
| Bidding Engine | 0 | 0 | 3 | 3 |
| Conventions | 0 | 0 | 2 | 2 |
| Card Play | 0 | 0 | 1 | 1 |
| Server/API | 0 | 1 | 0 | 1 |
| Frontend | 0 | 0 | 0 | 0 |

---

## 🟡 MONITORING: First Hand After Server Startup - Illegal Bidding Sequence

**Status:** Monitoring - Not reproduced since October 2025
**Severity:** 🟡 Moderate (downgraded from Critical)
**Priority:** MEDIUM (downgraded from HIGH)
**Area:** Server/API
**Reported:** 2025-10-10
**Last Review:** 2026-01-01
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
- ❌ Not observed since October 2025
- ✅ Happens specifically on first hand after server startup (when it occurs)

### Current Status (2026-01-01)

This issue has not been reproduced in over 2 months. Downgrading to **Monitoring** status. If it recurs:
1. Check server logs for the specific request sequence
2. Review AI bidding race condition fix (see `AI_BIDDING_RACE_CONDITION_FIX.md`)
3. Escalate to Critical if observed again

### Files to Review

- `backend/server.py` - `/api/get-next-bid` endpoint
- `backend/server.py` - `current_deal` global initialization
- `frontend/src/App.js` - AI bidding loop
- `backend/engine/bidding_engine.py` - Legality checking

### Related Issues

- `AI_BIDDING_RACE_CONDITION_FIX.md` - Related fix that may have addressed root cause

---

## ✅ RESOLVED: Convention Modules Have Incomplete Logic

**Status:** ✅ Resolved (94% complete)
**Severity:** 🟡 Moderate
**Priority:** ~~MEDIUM~~ RESOLVED
**Area:** Conventions
**Reported:** 2025-10-10
**Resolved:** 2025-10-12
**Evidence:** `docs/features/CONVENTION_FIXES_PUNCHLIST.md`

### Problem Description

Many convention modules had incomplete or incorrect logic that resulted in suboptimal bidding. A comprehensive review identified **33 issues** across all convention modules.

### Resolution Summary

**All Critical Issues Fixed (13/13 - 100%):**
1. ✅ **Takeout Doubles** - HCP requirement corrected (12+ instead of 13+)
2. ✅ **Takeout Doubles** - ConventionModule interface added
3. ✅ **Jacoby Transfers** - Post-transfer continuation logic added
4. ✅ **Stayman** - Responder rebid after 2♦ response implemented
5. ✅ **Stayman** - Responder rebid after finding fit implemented
6. ✅ **Jacoby Transfers** - Super-accept logic corrected (4+ card support)
7. ✅ **Blackwood** - Trigger logic improved
8. ✅ **Blackwood** - Signoff logic after ace response added
9. ✅ **Blackwood** - 5NT king-asking logic implemented
10. ✅ **Negative Doubles** - Applicability check corrected
11. ✅ **Negative Doubles** - Point range level-adjusted
12. ✅ **Preempts** - Response logic completed
13. ✅ **Preempts** - 3-level and 4-level preempts implemented

**Moderate Issues (10/12 - 83%):**
- ✅ Jump shifts and 2NT responses
- ✅ Rebids: reverses, 2NT, 3NT improvements
- ✅ Weak jump overcalls
- ✅ Advancer bidding expansion
- ⚠️ Gambling 3NT: Deferred (rare bid)
- ⚠️ Inverted Minors: Optional convention, skipped

**Placeholder Modules Implemented (4/4 - 100%):**
- ✅ **Michaels Cuebid** - 205 lines, fully functional
- ✅ **Unusual 2NT** - 160 lines, fully functional
- ✅ **Splinter Bids** - 150 lines, fully functional
- ✅ **Fourth Suit Forcing** - 210 lines, fully functional

**Minor Improvements (4/4 - 100%):**
- ✅ Tie-breaking for 4-4 minors
- ✅ Preempt defense
- ✅ Support doubles
- ✅ Responsive doubles

### Overall Progress: 31/33 issues complete (94%)

See detailed status in `docs/features/CONVENTION_FIXES_PUNCHLIST.md`.

---

## ✅ RESOLVED: Card Play Phase Missing Features

**Status:** ✅ Partially Resolved
**Severity:** 🟢 Minor
**Priority:** ~~LOW~~ RESOLVED (most items)
**Area:** Card Play
**Reported:** 2025-10-10
**Evidence:** Various implementation commits

### Original Missing Features

From original report:

1. ✅ **Play History UI** - Implemented (trick history display)
2. ⏳ **Undo/Redo** - Not implemented (future enhancement)
3. ⏳ **Claim Feature** - Not implemented (future enhancement)
4. ✅ **Play Analysis** - DDS analysis implemented for optimal play comparison
5. ⏳ **Visual Animations** - Not implemented (future enhancement)
6. ⏳ **Sound Effects** - Not implemented (future enhancement)
7. ⏳ **Save/Load** - Hand history with replay implemented
8. ✅ **Legal Card Highlighting** - Implemented
9. ✅ **Manual Play Trigger** - Debugging tools added
10. ✅ **Better Error Messages** - Improved messaging

### Current Status

Core card play functionality is complete. Remaining items (Undo/Redo, Claim, Animations, Sound) are nice-to-have enhancements tracked separately.

---

## ✅ RESOLVED: Placeholder Convention Modules Not Implemented

**Status:** ✅ Resolved
**Severity:** 🟢 Minor
**Priority:** ~~LOW~~ RESOLVED
**Area:** Conventions
**Reported:** 2025-10-10
**Resolved:** 2025-10-12 (Phase 3)
**Evidence:** `docs/features/CONVENTION_FIXES_PUNCHLIST.md`

### Problem Description (Original)

Four advanced convention modules existed as placeholder files with no implementation.

### Resolution

All four conventions have been fully implemented:

1. ✅ **Michaels Cuebid** (`michaels_cuebid.py`) - 205 lines
   - After 1♣/1♦: 2♣/2♦ shows both majors (5-5+)
   - After 1♥: 2♥ shows spades + minor (5-5+)
   - After 1♠: 2♠ shows hearts + minor (5-5+)
   - 8-16 HCP range
   - Partner response logic implemented

2. ✅ **Unusual 2NT** (`unusual_2nt.py`) - 160 lines
   - After major opening: 2NT shows both minors (5-5+)
   - 6-11 HCP (weak) or 17+ HCP (strong)
   - Partner response logic implemented

3. ✅ **Splinter Bids** (`splinter_bids.py`) - 150 lines
   - Double jump showing shortness + support
   - 12-15 HCP, 4+ card support
   - Singleton/void detection

4. ✅ **Fourth Suit Forcing** (`fourth_suit_forcing.py`) - 210 lines
   - 4th suit artificial game force
   - 12+ HCP requirement
   - Checks for alternatives before using

---

## ✅ FIXED: Card Play Phase Failed to Start (KeyError)

**Status:** ✅ Fixed
**Severity:** ~~🔴 Critical~~ Fixed
**Priority:** ~~HIGH~~ RESOLVED
**Area:** Server/API
**Reported:** 2025-10-10 15:36:50
**Evidence:** `docs/bug-fixes/BUG_FIX_CARD_PLAY.md`

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

- `backend/server.py` - Added position mapping

---

## ✅ FIXED: Weak Two Preempts with Voids

**Status:** ✅ Fixed
**Severity:** ~~🟡 Moderate~~ Fixed
**Priority:** ~~HIGH~~ RESOLVED
**Area:** Bidding Engine
**Reported:** 2025-10-10
**Evidence:** `docs/bug-fixes/BIDDING_FIXES_2025-10-10.md`

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

---

## ✅ FIXED: Strong Balanced Hands (19+ HCP) Passed Instead of Doubling

**Status:** ✅ Fixed
**Severity:** ~~🟡 Moderate~~ Fixed
**Priority:** ~~HIGH~~ RESOLVED
**Area:** Bidding Engine
**Reported:** 2025-10-10
**Evidence:** `docs/bug-fixes/BIDDING_FIXES_2025-10-10.md`

### Problem Description

With 19+ HCP balanced hands, system passed after opponent opened instead of competing.

### Example

West passed with: ♠Q982 ♥A7 ♦AKT ♣AQ76 (19 HCP, balanced - should Double)

### Solution Implemented

Updated `TakeoutDoubleConvention` to double with 19+ HCP balanced, planning to bid NT later.

### Files Changed

- `backend/engine/ai/conventions/takeout_doubles.py`

---

## 🔵 ENHANCEMENT: Skill Practice Generators Should Use Bidding Engine

**Status:** Not Started
**Severity:** 🟡 Moderate (correctness risk)
**Priority:** MEDIUM
**Area:** Learning / Bidding Engine
**Reported:** 2026-03-02
**Evidence:** User feedback 2026-03-02 15:19 — "New Suit Response" skill told user 1♠ was correct when 1♥ was right (6H-4S responding to 1♦)

### Problem Description

The 24 `get_expected_response()` methods in `skill_hand_generators.py` each hardcode their own bidding rules independently of the bidding engine (`responses.py`, `opening_bids.py`, etc.). When engine logic is updated, skill generators silently drift out of sync.

### Proposed Solution

Refactor skill generators to call the bidding engine for bid evaluation:
1. Generators handle only **hand generation** (constraints, variants)
2. Correct bid determined by calling `BiddingEngine.get_next_bid()` with the generated hand + auction
3. `get_expected_response()` becomes a thin wrapper around the engine call
4. Generators still provide skill-specific **explanations** for pedagogical value

### Benefits
- Single source of truth for bidding rules
- No more drift between engine and learning system
- Reduced maintenance burden (24 implementations → 1)

### Risks
- Engine may return bids that don't match the skill's pedagogical intent (e.g., a convention module intercepting)
- Need to handle engine failures gracefully in skill context

### Files to Review
- `backend/engine/learning/skill_hand_generators.py` (24 generators)
- `backend/engine/bidding_engine.py` (engine entry point)

---

## 📝 Template for New Issues

### Issue Title

**Status:** [Not Started / In Progress / Monitoring / Resolved / Won't Fix]
**Severity:** [🔴 Critical / 🟡 Moderate / 🟢 Minor]
**Priority:** [LOW / MEDIUM / HIGH / CRITICAL]
**Area:** [Bidding Engine / Conventions / Card Play / Server/API / Frontend / Database]
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

**Total Issues Tracked:** 7
**Open Issues:** 0
**Monitoring:** 1
**Resolved:** 6

### Status Breakdown
| Status | Count |
|--------|-------|
| 🔴 Open/Critical | 0 |
| 🟡 Monitoring | 1 |
| 🟢 Minor/Open | 0 |
| ✅ Resolved | 6 |

### Priority Items
1. **Monitoring:** First Hand After Server Startup bug (intermittent, not reproduced since Oct 2025)

### Recent Fixes (2025-10 to 2025-12)
- All 13 critical convention issues fixed
- Michaels Cuebid, Unusual 2NT, Splinter Bids, Fourth Suit Forcing implemented
- Card play features added (history, analysis, legal highlighting)
- Multiple bidding engine improvements

---

*Last Updated: 2026-01-01*
