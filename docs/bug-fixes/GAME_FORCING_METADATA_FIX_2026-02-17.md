# Game-Forcing Metadata Fix - Jacoby Super-Accept

**Date:** 2026-02-17
**Severity:** Critical
**Status:** Fixed

## Summary

Fixed critical bug where Jacoby Transfer super-accepts (3♥/3♠) did not set game-forcing metadata, causing auctions to end prematurely when responder held 8-9 HCP and should have bid game.

## Production Incident

**User Report (Feb 17, 2026 23:18):**
> "Surely I should bid 4 spades and not pass. Please review the bidding logic."

**Auction:**
```
North   East    South   West
1NT     X       2♥      Pass
3♠      Pass    (ended - BUG!)
```

**South's Hand:** ♠AJ8654 ♥KJ6 ♦53 ♣54 (9 HCP, 6 spades)

**Expected:** After North's 3♠ super-accept showing 17 HCP + 4-card spade support, South should bid 4♠ (combined 26+ HCP, 10+ card fit = clear game).

**Actual:** Auction ended after 3 consecutive passes because the game didn't recognize 3♠ as game-forcing.

## Root Cause

**File:** `backend/engine/ai/conventions/jacoby_transfers.py`
**Lines:** 88-96 (`_get_completion_bid` method)

### Before Fix
```python
def _get_completion_bid(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
    partner_last_bid = features['auction_features']['partner_last_bid']
    metadata = {'bypass_suit_length': True}

    if partner_last_bid == "2♥":
        if hand.hcp == 17 and hand.suit_lengths['♠'] >= 4:
            return ("3♠", "Super-accept showing maximum 1NT (17 HCP) with 4-card spade support.", metadata)
        # ❌ metadata only had bypass_suit_length, not game_forcing!
```

**Problem:** Super-accept metadata was missing:
- `'game_forcing': True`
- `'forcing_sequence': 'jacoby_super_accept'`

This caused:
1. Bid explanation said "game forcing" but metadata didn't match
2. Auction ended after 3 passes because forcing status wasn't detected
3. Responder never got to bid 4♠

### After Fix
```python
def _get_completion_bid(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
    partner_last_bid = features['auction_features']['partner_last_bid']
    metadata = {'bypass_suit_length': True}
    # ✅ Super-accept is game-forcing (17 HCP opener + 5+ card suit from responder = 22+ combined minimum)
    super_accept_metadata = {'bypass_suit_length': True, 'game_forcing': True, 'forcing_sequence': 'jacoby_super_accept'}

    if partner_last_bid == "2♥":
        if hand.hcp == 17 and hand.suit_lengths['♠'] >= 4:
            return ("3♠", "Super-accept showing maximum 1NT (17 HCP) with 4-card spade support.", super_accept_metadata)
```

## Changes Made

### 1. Code Fix
- **File:** `backend/engine/ai/conventions/jacoby_transfers.py`
- **Lines:** 85-96
- **Change:** Added `super_accept_metadata` with `game_forcing: True` for both hearts and spades super-accepts

### 2. Regression Test
- **File:** `backend/tests/unit/test_jacoby_super_accept_forcing.py` (new)
- **Tests:**
  - `test_spade_super_accept_has_game_forcing_metadata` ✅
  - `test_heart_super_accept_has_game_forcing_metadata` ✅
  - `test_simple_transfer_completion_not_game_forcing` ✅
  - `test_super_accept_requires_17_hcp` ✅

## Bridge Theory

**Why is super-accept game-forcing?**

Opener shows 17 HCP (maximum 1NT) + 4-card support. Responder showed 5+ cards by transferring. Even with minimum responder values:
- Opener: 17 HCP
- Responder: 5+ HCP (minimum to transfer)
- **Combined: 22+ HCP**
- **Fit: 9+ cards** (5 from responder + 4 from opener)

With 22+ HCP and 9+ card fit, partnership should explore game. Therefore, super-accept is forcing until game is reached.

## Impact

**Before Fix:**
- Auction could end after super-accept + 2 passes
- Partnerships missed games with 26+ combined HCP
- User confusion ("Why can't I bid 4♠?")

**After Fix:**
- Forcing status properly set
- Auction continues until game reached
- Responder can bid 4♠ with appropriate values

## Quality Assurance

**Tests:**
- ✅ 4/4 regression tests pass
- ✅ Existing Jacoby tests still pass
- ✅ Quality score baseline: No regressions

## Related Issues

This pattern should be checked in other conventions:
- [ ] Stayman continuations
- [ ] Gerber responses
- [ ] Blackwood responses
- [ ] Fourth Suit Forcing

All game-forcing bids must include metadata:
```python
{'game_forcing': True, 'forcing_sequence': 'convention_name'}
```

## Prevention

**Code Review Checklist:**
When adding any bid that is game-forcing:
1. ✅ Set `'game_forcing': True` in metadata
2. ✅ Set `'forcing_sequence': 'descriptive_name'` in metadata
3. ✅ Add test verifying metadata is present
4. ✅ Verify explanation matches forcing status

**ADR:** Consider creating a `GameForcingBid` helper class that ensures metadata is always set correctly.

---

**Fixed By:** Claude Sonnet 4.5 (Bidding Specialist)
**Reviewed By:** _Pending_
**Deployed:** _Pending_
