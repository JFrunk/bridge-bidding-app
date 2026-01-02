# User Feedback Tracking

This document tracks active user-reported issues from the feedback form and review requests.

**Last Updated:** 2026-01-01
**Focus:** Last 3 days (Dec 28, 2025 - Jan 1, 2026)

---

## 📋 Summary

### Active Issues (Last 3 Days)
| Severity | Open | Fixed | Total |
|----------|------|-------|-------|
| 🔴 Critical | 0 | 1 | 1 |
| 🟡 Moderate | 0 | 0 | 0 |
| 🟢 Minor/Education | 1 | 0 | 1 |
| **Total** | **1** | **1** | **2** |

### By Application Area
| Area | Open | Fixed | Type |
|------|------|-------|------|
| Blackwood Convention | 0 | 1 | Bug (Fixed) |
| Bidding Logic | 1 | 0 | User Education |

---

## 🟢 ACTIVE ISSUES (Last 3 Days)

### Issue #1: Bidding Decision Clarification - 1NT vs Double

**Status:** Open (User Education Request)
**Severity:** 🟢 Minor
**Area:** Bidding Logic
**Reported:** 2025-12-28
**Evidence:** `hand_2025-12-28_08-35-49.json`

**User Concern:**
> "Should I bid 1nt or double in this hand. Only provide a commentary relative to sayc"

**Hand Context:**
- South: ♠J32 ♥AK7 ♦Q3 ♣KQT54 (15 HCP, 5 clubs)
- Auction: Pass (North) - 1♦ (East) - ? (South)

**Analysis:**
This is a legitimate bidding question, not a system bug. With 15 HCP and a balanced hand after East opens 1♦:
- **1NT Overcall**: Shows 15-18 HCP with stopper in opponent's suit (♦Q3). Valid choice.
- **Takeout Double**: Shows support for unbid suits. South has only 3 spades and 3 hearts - marginal for takeout double.

**Correct Answer per SAYC:** 1NT overcall is preferred with balanced hand, stopper, and 15 HCP.

**Action Required:**
- [ ] Consider adding "Why" explanations to feedback system
- [x] System correctly allows both bids as legal

---

### Issue #2: Blackwood Response After 1NT Opening - ✅ FIXED

**Status:** ✅ FIXED (2026-01-01)
**Severity:** 🔴 Critical → Fixed
**Area:** Blackwood Convention
**Reported:** 2025-12-28
**Fixed:** 2026-01-01
**Evidence:** `hand_2025-12-28_17-18-05.json`

**User Concern:**
> "Why would a pass be correct there with 6 spades."

**Hand Context:**
- South: ♠AKT972 ♥JT76 ♦T9 ♣- (8 HCP, 6 spades, void in clubs)
- Auction: 1NT (North) - Pass (East) - 2♥ (South, Jacoby Transfer) - Pass (West) - 2♠ (North) - Pass (East) - 4♠ (South) - Pass (West) - 4NT (North, Blackwood) - Pass (East) - ?

**Root Cause:**
The bug was in `backend/engine/ai/conventions/blackwood.py` in the `_is_ace_answering_applicable` method. The check for "partner opened NT → quantitative 4NT" was happening BEFORE checking for suit agreement. This meant when partner opened 1NT, even with suit agreement (via Jacoby Transfer), the system treated 4NT as quantitative and returned no Blackwood response.

**Fix Applied:**
Reordered the checks in `_is_ace_answering_applicable` so that:
1. **FIRST** check for suit agreement (takes priority over NT opening)
2. **THEN** check for quantitative NT auction (only if no suit agreement)

**Files Modified:**
- `backend/engine/ai/conventions/blackwood.py:206-241` (`_is_ace_answering_applicable` method)

**Regression Test Added:**
- `backend/tests/regression/test_blackwood_after_1nt_transfer.py`
- 4 test cases covering:
  - Jacoby Transfer → 4♠ → 4NT (original bug scenario)
  - Stayman → 4♥ → 4NT
  - Transfer to hearts → 4♥ → 4NT
  - Direct suit bid after 1NT → 4♠ → 4NT

**Verification:**
```bash
pytest tests/regression/test_blackwood_after_1nt_transfer.py -v
# 4 passed
```

---

## 📊 Recent Feedback Summary

### Last 3 Days (Dec 28 - Jan 1)

**Review Requests:**
| Date | Concern | Type | Status |
|------|---------|------|--------|
| 2025-12-28 | 1NT vs Double question | Education | Open |
| 2025-12-28 | Blackwood response question | Bug | ✅ Fixed |
| 2025-12-30 | Template question | N/A | Skip |

**Feedback Form Submissions:**
| Date | Type | Description | Status |
|------|------|-------------|--------|
| 2025-12-28 | Test | "Test feedback" | N/A |
| 2025-12-28 | Joke | Developer comment | N/A |
| 2026-01-01 | Test | "test" | N/A |

---

## 📝 Action Items

### ✅ Completed
1. **Fixed Issue #2 - Blackwood Response Bug** (2026-01-01)
   - Modified `backend/engine/ai/conventions/blackwood.py`
   - Added regression test `test_blackwood_after_1nt_transfer.py`
   - All tests passing

### Medium Priority
2. Consider adding "Why" explanations to bid feedback for user education

### Low Priority
3. Continue monitoring for new user feedback

---

## 🗂️ Archive Note

All issues from October-November 2025 have been resolved. See git history for:
- Convention fixes (13 critical issues)
- Card play fixes (8 issues)
- UI/Display fixes (7 issues)
- State management fixes (5 issues)
- Scoring fixes (2 issues)

For historical reference, see:
- `docs/features/CONVENTION_FIXES_PUNCHLIST.md`
- `docs/bug-fixes/` directory

---

*Last Updated: 2026-01-01*
