# Future Development: Seats Utility Migration

**Created:** 2026-01-05
**Last Updated:** 2026-01-05
**Status:** Phase 1 Complete
**Priority:** Medium (after current feature work)

## Overview

The seats utility modules (`backend/utils/seats.py` and `frontend/src/utils/seats.js`) were created to provide a single source of truth for all seat/position calculations. Currently, many files still have duplicate inline seat logic that should be migrated.

## Completed

- [x] Created `backend/utils/seats.py` with full seat calculation utilities
- [x] Created `frontend/src/utils/seats.js` (mirrors Python)
- [x] Added unit tests (50 Python, 54 JavaScript - all passing)
- [x] Fixed DecayChart NS/EW perspective bug using `nsSuccess()`
- [x] Fixed BidReviewModal partnership display bug using `bidderRole()`
- [x] Added documentation to CLAUDE.md

## Phase 1: Critical Backend Files ✅ COMPLETE

All 4 critical backend files have been migrated with named constants for clarity:

### 1. `backend/engine/analysis/decay_curve.py` ✅
- **Migrated:** Removed duplicate constants, now imports from `utils.seats`
- **Constants imported:** `SEATS`, `PARTNERS`, `NEXT_PLAYER`, `NS_SIDE`, `EW_SIDE`, `partner`
- **Verified:** All tests pass

### 2. `backend/engine/learning/analytics_api.py` ✅
- **Migrated:** Removed duplicate `get_partner()` function
- **Now imports:** `partner` from `utils.seats`
- **Replaced:** `get_partner(position)` → `partner(position)` (2 usages)
- **Verified:** All tests pass

### 3. `backend/engine/ai/feature_extractor.py` ✅
- **Migrated:** Added `PARTNER_OFFSET`, `LHO_OFFSET`, `RHO_OFFSET` named constants
- **Now imports:** `seat_index`, `seat_from_index`, `SEATS` from `utils.seats`
- **Replaced:** `(my_index + 2) % 4` → `(my_index + PARTNER_OFFSET) % 4` (5 usages)
- **Replaced:** `(partner_index + 1) % 4` → `(partner_index + LHO_OFFSET) % 4`
- **Replaced:** `(partner_index + 3) % 4` → `(partner_index + RHO_OFFSET) % 4`
- **Note:** Kept integer indices for efficient auction iteration
- **Verified:** All tests pass

### 4. `backend/engine/ai/auction_context.py` ✅
- **Migrated:** Added `PARTNER_OFFSET` named constant
- **Now imports:** `SEATS` from `utils.seats`
- **Replaced:** `(opener_index + 2) % 4` → `(opener_index + PARTNER_OFFSET) % 4`
- **Verified:** All tests pass

## Phase 2: Supporting Backend Files (MEDIUM PRIORITY)

### 5. `backend/engine/play_engine.py`
- **Issue:** Inline `% 4` modulo for seat rotation (lines 273, 278, 366, 373)
- **Migration:** Use `active_seat_play()`, `lho()`, `partner()`
- **Impact:** 5+ lines

### 6. `backend/server.py`
- **Issue:** Dealer rotation modulo (lines 918, 948, 2466, 2779)
- **Migration:** Use `lho()` for next player, consider `active_seat_bidding()`
- **Impact:** ~10 lines

## Phase 3: Frontend Components (LOW PRIORITY)

These are mostly display logic and lower risk:

### 7. `frontend/src/components/play/ContractHeader.jsx`
- **Issue:** Dealer/auction position modulo (line 98)
- **Migration:** Import from `utils/seats`

### 8. `frontend/src/PlayComponents.js`
- **Issue:** Partnership logic using hardcoded checks (lines 241-244)
- **Migration:** Use `partnershipStr()` or `NS_SIDE.has()`

### 9. `frontend/src/components/play/ScoreModal.jsx`
- **Issue:** Partnership checks (lines 37-43)
- **Migration:** Use `sameSide()` or `NS_SIDE.has()`

### 10. `frontend/src/components/play/CurrentTrickDisplay.jsx`
- **Issue:** Position name mapping (lines 13-15)
- **Migration:** Import `SEAT_NAMES` from utility

## Testing Strategy

After each file migration:
1. Run unit tests: `pytest tests/unit/test_seats.py -v`
2. Run related integration tests
3. Manual smoke test of affected feature

## Benefits

- **Consistency:** Single source of truth for seat calculations
- **Maintainability:** Bug fixes apply everywhere
- **Readability:** `partner('S')` clearer than `(seat_index + 2) % 4`
- **Error prevention:** No more off-by-one modulo bugs

## Notes

- Do NOT migrate test files or one-off scripts (lower priority)
- Always preserve existing behavior - these are refactors, not fixes
- Run baseline tests before/after to verify no regressions
