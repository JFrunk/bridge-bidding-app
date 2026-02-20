# Forcing Bid Enforcement Fix - V2 Schema Interpreter

**Date:** 2026-02-17
**Severity:** Critical
**Status:** Fixed

## Summary

Fixed critical bug where forcing bids (one-round forcing and game-forcing) were not enforced in the V2 schema bidding engine. The system showed warnings like "Cannot Pass: Partner's bid is forcing for one round" but still allowed the pass to go through.

## Production Incident

**User Report (Feb 17, 2026 18:32):**
> "How can my partner ignore my double."

**Auction:**
```
North: 3♦ (preempt - partner)
East:  Pass
South: X (USER - doubling own partner's bid - UI error)
West:  Pass
North: Pass - Warning: "Cannot Pass: Partner's bid is forcing for one round"
East:  Pass
```

**South's Hand:** ♠AQ109 ♥Q743 ♦4 ♣AQ52 (14 HCP)

**Multiple Issues:**
1. User was able to double their own partner's bid (UI validation issue - Frontend)
2. **System showed forcing warning but allowed pass anyway** (Backend bug - this fix)
3. User confusion about forcing bid mechanics (Learning issue)

## Root Cause

**File:** `backend/engine/v2/interpreters/schema_interpreter.py`

The `validate_bid_against_forcing()` method existed and correctly identified illegal passes, returning `BidValidationResult(is_valid=False)`, but **this method was never called** by the `evaluate()` method.

### Before Fix
```python
def evaluate(self, features: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    candidates = []
    for category, schema in self.schemas.items():
        category_candidates = self._evaluate_schema(schema, features, category)
        candidates.extend(category_candidates)

    if not candidates:
        return None

    candidates.sort(key=lambda c: c.priority, reverse=True)

    # Return best match - NO VALIDATION!
    best = candidates[0]
    return (best.bid, best.explanation)
```

**Problem:** The method returned the best bid without checking if it violated forcing constraints.

### After Fix
```python
def evaluate(self, features: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    candidates = []
    for category, schema in self.schemas.items():
        category_candidates = self._evaluate_schema(schema, features, category)
        candidates.extend(category_candidates)

    if not candidates:
        return None

    candidates.sort(key=lambda c: c.priority, reverse=True)

    # Validate Pass bids against forcing constraints
    best = candidates[0]
    if best.bid == "Pass":
        last_contract_level = features.get('auction_level', 0)
        last_contract_suit = features.get('last_contract_suit', '')
        validation = self.validate_bid_against_forcing("Pass", last_contract_level, last_contract_suit)

        if not validation.is_valid:
            logger.warning(f"Pass bid rejected: {validation.reason}")
            non_pass_candidates = [c for c in candidates if c.bid != "Pass"]
            if non_pass_candidates:
                best = non_pass_candidates[0]
                logger.info(f"Selected alternative bid: {best.bid}")
            else:
                logger.error("No valid bids - all candidates are Pass but forcing is active")
                return None

    return (best.bid, best.explanation)
```

## Changes Made

### 1. Code Fix
- **File:** `backend/engine/v2/interpreters/schema_interpreter.py`
- **Lines:** 236-256 (`evaluate()` method)
- **Lines:** 330-350 (`evaluate_all_candidates()` method - soft matching version)
- **Change:** Added forcing bid validation before returning best bid
  - Validates Pass bids using existing `validate_bid_against_forcing()` method
  - Filters out illegal Pass candidates
  - Selects next best non-Pass bid
  - Returns None if no valid bids available

### 2. Regression Tests (5 tests, all passing ✅)
- **File:** `backend/tests/unit/test_forcing_bid_enforcement.py` (new)
- Tests verify:
  - `FORCING_1_ROUND` prevents passing when partner's bid is forcing
  - `GAME_FORCE` prevents passing below game level
  - `GAME_FORCE` allows passing once game is reached
  - `evaluate()` method rejects illegal Pass and selects alternative
  - `NON_FORCING` allows passing normally

## Testing

✅ **All regression tests pass:**
```
test_forcing_one_round_prevents_pass PASSED
test_game_force_prevents_pass PASSED
test_game_force_allows_pass_at_game PASSED
test_evaluate_rejects_illegal_pass PASSED
test_non_forcing_allows_pass PASSED
```

## Bridge Theory

**One-Round Forcing:**
- Partner's takeout double is forcing for one round
- Responder MUST bid (cannot pass)
- Forcing expires after partner bids again

**Game Forcing:**
- Certain sequences (2/1, jump shifts) are game-forcing
- Neither partner can pass until game level is reached
- Game = 3NT, 4♥, 4♠, 5♣, 5♦, or higher

**Why This Matters:**
Without enforcement, auctions end prematurely, causing:
- Missed games with 25+ combined HCP
- Lost slam opportunities
- User confusion about bidding rules

## Impact

**Before Fix:**
- Forcing bids showed warnings but were not enforced
- System allowed illegal passes
- Auctions ended prematurely
- Users confused about why warnings appeared but didn't prevent action

**After Fix:**
- Forcing constraints actively enforced
- Illegal passes rejected, alternative bids selected
- Auctions continue properly until forcing is satisfied
- Warnings actually prevent illegal actions

## Related Issues

**Other bugs identified in same incident:**
1. **UI Validation (Frontend):** User should not be able to double their own partner's bid
   - Bidding box should disable X/XX when last bid was by partner
   - Priority: P0 (blocking illegal actions)

2. **Educational Content (Learning):** Users need guidance on forcing bids
   - Add tooltip: "Doubles are for opponent's bids only"
   - Explain when partner's bid is forcing
   - Priority: P1 (user education)

## Files Changed

- `backend/engine/v2/interpreters/schema_interpreter.py` (22 lines added)
- `backend/tests/unit/test_forcing_bid_enforcement.py` (151 lines added)
- `docs/bug-fixes/FORCING_BID_ENFORCEMENT_FIX_2026-02-17.md` (this file)

**Total:** 3 files changed, 173 insertions(+)

## Checklist

- [x] Code fix implemented
- [x] Regression tests added (5 tests, all passing)
- [x] Existing tests still pass
- [x] Documentation complete
- [x] Bridge theory validated
- [ ] Frontend UI validation (separate PR - Frontend Specialist)
- [ ] Educational content (separate PR - Learning Specialist)

---

**Fixed By:** Claude Sonnet 4.5 (Bidding Specialist)
**Reviewed By:** _Pending_
**Deployed:** _Pending_
