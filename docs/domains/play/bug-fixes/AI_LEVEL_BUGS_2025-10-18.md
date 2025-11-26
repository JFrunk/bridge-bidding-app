# AI Level Bugs - Critical Issues Report
**Date:** 2025-10-18
**Priority:** HIGH - Pre-Launch Critical
**Status:** Investigation Complete, Fixes Pending

## Overview
Multiple critical bugs discovered in AI level selection and display system that could confuse users and cause incorrect AI behavior.

## Bug #1: AI Level Mismatch - Selected vs Active (PRIORITY 1)
**Severity:** CRITICAL
**Status:** Root cause identified

### Issue
- User has "Intermediate" (7.5/10) selected in the AI Level dropdown button
- DDS Status Indicator shows "DDS Expert AI Active" (9/10)
- Actual behavior shows DDS is active (Python crashed due to DDS on macOS)

### Root Cause Analysis
The system has TWO separate AI selection mechanisms that are not synchronized:

1. **AIDifficultySelector** ([frontend/src/components/AIDifficultySelector.jsx](frontend/src/components/AIDifficultySelector.jsx))
   - Default state: `'intermediate'` (hardcoded line 38)
   - Fetches current difficulty on mount via `/api/ai/status`
   - User can change difficulty via `/api/set-ai-difficulty`

2. **Session State Default** ([backend/core/session_state.py](backend/core/session_state.py))
   - Smart default based on DDS availability (lines 47-72)
   - **Production (DDS available):** Defaults to `'expert'` (9/10)
   - **Development (DDS unavailable):** Defaults to `'advanced'` (8/10)

### The Problem
When the frontend loads:
1. Frontend component initializes with `currentDifficulty = 'intermediate'`
2. Backend session has `ai_difficulty = 'expert'` (because DDS is available in session state check)
3. Frontend fetches current difficulty via `/api/ai/status` which returns `'expert'`
4. **BUT:** There's a race condition or the state update isn't being reflected in the UI button

### Impact
- User thinks they're playing against Intermediate AI (7.5/10)
- System is actually using Expert AI with DDS (9/10)
- This caused Python crash on macOS (known DDS issue)
- Misleading user experience and incorrect difficulty expectations

### Testing Evidence
From screenshot:
- Button shows: "Intermediate 7.5/10"
- DDS Status shows: "DDS Expert AI Active"
- Error shows: "Python quit unexpectedly" (DDS crash signature)

---

## Bug #2: DDS Status Display Order Mismatch
**Severity:** MEDIUM
**Status:** Identified

### Issue
AI difficulty levels shown in DDS Status Indicator dropdown don't match the order in the AI Difficulty Selector button.

**Button Order (desired standard):**
1. 🌱 Beginner (6/10)
2. 📚 Intermediate (7.5/10)
3. 🎯 Advanced (8/10)
4. 🏆 Expert (9/10)

**DDS Status Order (current - uses Object.entries):**
- Varies based on JavaScript object key order (not guaranteed)
- Should be: B, I, A, E (alphabetical or rating order)

### Root Cause
[frontend/src/components/DDSStatusIndicator.jsx:111](frontend/src/components/DDSStatusIndicator.jsx#L111)
```javascript
{Object.entries(aiStatus.difficulties || {}).map(([level, info]) => (
  <div key={level} className="difficulty-row">
    <span className="difficulty-name">{level}:</span>
    <span className="difficulty-rating">{info.rating}</span>
  </div>
))}
```

Object.entries() doesn't guarantee order. Should use explicit ordering array.

### Impact
- Confusing UX when comparing difficulty levels
- Inconsistent presentation across UI components

---

## Bug #3: No AI Level Validation/Testing
**Severity:** MEDIUM
**Status:** Gap identified

### Issue
No automated tests to verify:
1. Each AI level (Beginner, Intermediate, Advanced, Expert) is actually working
2. AI levels produce different quality of play
3. DDS fallback works correctly when DDS unavailable
4. AI level changes persist correctly across hands

### Impact
- Cannot verify AI levels are functioning as advertised
- No way to validate play quality matches ratings (6/10, 7.5/10, 8/10, 9/10)
- Potential for silent failures where AI doesn't actually change behavior

---

## Fixes Required

### Fix #1: Synchronize AI Level State (PRIORITY 1)
**Files to modify:**
- [frontend/src/components/AIDifficultySelector.jsx](frontend/src/components/AIDifficultySelector.jsx)
- [frontend/src/components/DDSStatusIndicator.jsx](frontend/src/components/DDSStatusIndicator.jsx)

**Changes:**
1. Remove hardcoded default `'intermediate'` from AIDifficultySelector
2. Wait for `/api/ai/status` response before rendering initial state
3. Show loading spinner until actual difficulty is fetched
4. Add state refresh mechanism for DDSStatusIndicator to poll current difficulty
5. Ensure both components poll and display the same `current_difficulty` from backend

**Verification:**
- Button selection should always match DDS Status display
- Button selection should match actual AI behavior
- After page refresh, selected button should match backend session state

### Fix #2: Standardize Display Order
**Files to modify:**
- [frontend/src/components/DDSStatusIndicator.jsx:109-117](frontend/src/components/DDSStatusIndicator.jsx#L109-L117)

**Changes:**
```javascript
const DIFFICULTY_ORDER = ['beginner', 'intermediate', 'advanced', 'expert'];

<div className="status-detail-section all-difficulties">
  <h4>All Difficulty Levels</h4>
  {DIFFICULTY_ORDER
    .filter(level => aiStatus.difficulties?.[level])
    .map(level => {
      const info = aiStatus.difficulties[level];
      return (
        <div key={level} className="difficulty-row">
          <span className="difficulty-name">{info.name}:</span>
          <span className="difficulty-rating">{info.rating}</span>
        </div>
      );
    })}
</div>
```

### Fix #3: Create AI Level Testing Framework
**New file:** `backend/tests/test_ai_levels.py`

**Test coverage:**
1. Verify all 4 AI levels initialize correctly
2. Test AI level switching via `/api/set-ai-difficulty`
3. Verify difficulty persists across multiple hands
4. Test DDS fallback behavior
5. Compare play quality between levels (using test positions)

**Test positions to use:**
- Simple finesse position (test tactical awareness)
- Trump promotion position (test advanced technique)
- Endplay position (test expert-level play)

---

## Workaround (Current)

For macOS development:
1. Set environment variable: `DEFAULT_AI_DIFFICULTY=advanced`
2. This prevents DDS auto-selection and Python crashes
3. User can still manually select Expert if they want to test DDS

For production (Linux with working DDS):
1. Default to Expert AI is correct behavior
2. Just need to fix UI sync issue

---

## Timeline

**Immediate (before next hand):**
- [ ] Fix #1: Synchronize AI level state between frontend and backend
- [ ] Verify fix with manual testing

**Pre-Launch (required):**
- [ ] Fix #2: Standardize display order in DDS Status
- [ ] Fix #3: Create AI level testing framework
- [ ] Run full test suite on all 4 AI levels

**Post-Launch (nice to have):**
- [ ] Add AI difficulty selector to bidding phase
- [ ] Add visual confirmation when difficulty changes
- [ ] Add analytics to track which difficulty levels users prefer

---

## Related Files

### Frontend
- [frontend/src/components/AIDifficultySelector.jsx](frontend/src/components/AIDifficultySelector.jsx) - Main difficulty selector
- [frontend/src/components/DDSStatusIndicator.jsx](frontend/src/components/DDSStatusIndicator.jsx) - Status display
- [frontend/src/App.js:1512-1528](frontend/src/App.js#L1512-L1528) - Where selector is rendered

### Backend
- [backend/server.py:352-404](backend/server.py#L352-L404) - `/api/ai/status` endpoint
- [backend/server.py:510-540](backend/server.py#L510-L540) - `/api/set-ai-difficulty` endpoint
- [backend/core/session_state.py:47-100](backend/core/session_state.py#L47-L100) - Default AI selection logic

### AI Implementations
- [backend/engine/play/ai/simple_ai.py](backend/engine/play/ai/simple_ai.py) - Beginner (6/10)
- [backend/engine/play/ai/minimax_ai.py](backend/engine/play/ai/minimax_ai.py) - Intermediate/Advanced/Expert fallback
- [backend/engine/play/ai/dds_ai.py](backend/engine/play/ai/dds_ai.py) - Expert with DDS (9/10)

---

## Notes

- The smart default logic in [session_state.py](backend/core/session_state.py) is actually good design
- The problem is frontend doesn't properly initialize from backend state
- DDS crash on macOS is expected and documented - not a bug, just platform limitation
- Need to ensure UI always shows truth: what AI level is ACTUALLY active
