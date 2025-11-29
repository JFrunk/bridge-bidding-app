# Declarer Determination Bug Fix (2025-11-28)

## Summary

Fixed a critical bug where the declarer was incorrectly assigned after a Jacoby Transfer auction. The system assigned East as declarer instead of North for a 4♠ contract.

## Bug Report

**User's Experience:**
- User did a Jacoby transfer: 1NT (North) → 2♥ (South, transfer) → 2♠ (North, complete) → 4♠ (South)
- Expected: North to be declarer (first to bid spades naturally)
- Actual: System showed "4♠ by East" - East never even bid!

## Root Cause

**State synchronization mismatch between frontend and backend dealer.**

The issue was in `/api/start-play`:

```python
# BEFORE (buggy)
dealer_str = data.get("dealer", "North")
if state.game_session:
    dealer_str = state.game_session.get_current_dealer()  # <-- ALWAYS overrides!
```

**Problem:** Even though the frontend correctly sent `dealer: "North"` (the actual dealer during bidding), the backend **always** overrode it with `state.game_session.get_current_dealer()`.

If the session's `current_hand_number` was different from when the hand was dealt, or if there was any state desync, the backend would use the wrong dealer index to parse the auction.

**Why this causes wrong declarer:**

The auction `['1NT', 'Pass', '2♥', 'Pass', '2♠', ...]` is just a list of bids. The positions are calculated as:
- Position[i] = (dealer_index + i) % 4

With dealer=North (index 0):
- Position 0 = North → bid 1NT ✓
- Position 4 = North → bid 2♠ (first spade) ✓
- Declarer = North ✓

With dealer=East (index 1) - **wrong**:
- Position 0 = East → bid 1NT (but East passed!)
- Position 4 = East → bid 2♠ (first spade on "EW side")
- Declarer = East ✗

## Fix Applied

### Backend Changes (`server.py`)

**`/api/start-play`:**
```python
# AFTER (fixed)
dealer_str = data.get("dealer")  # Trust frontend's dealer
if not dealer_str:
    # Fallback only if frontend doesn't provide dealer
    if state.game_session:
        dealer_str = state.game_session.get_current_dealer()
    else:
        dealer_str = "North"
```

**`/api/request-review`:**
Same pattern - trust frontend's dealer for review data.

### Frontend Changes (`App.js`)

Added `dealer` to the `/api/request-review` request body to ensure review data captures the correct dealer.

## Files Changed

- `backend/server.py`:
  - `/api/start-play`: Trust frontend dealer, fallback to session only if not provided
  - `/api/request-review`: Same pattern
- `frontend/src/App.js`:
  - `handleRequestReview`: Added `dealer` to request body
- `backend/tests/regression/test_jacoby_transfer_declarer_bug.py`: New regression test

## Testing

### New Regression Test

`test_jacoby_transfer_declarer_bug.py` contains 6 test cases:
1. Jacoby Transfer with North dealer
2. Jacoby Transfer with East dealer (exact bug scenario)
3. Jacoby Transfer with South dealer
4. Jacoby Transfer with West dealer
5. **Bug demonstration**: Shows mismatched dealer causes wrong declarer
6. Hearts Jacoby Transfer

### Run Tests

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/regression/test_jacoby_transfer_declarer_bug.py -v
```

All 6 tests pass.

## Why Trust Frontend Dealer?

The frontend knows the **actual dealer** that was used when the auction was built:
1. When a hand is dealt, backend sends `dealer` (from Chicago rotation)
2. Frontend stores `dealer` in state
3. Bidding proceeds based on this `dealer`
4. Auction array is built assuming this `dealer`
5. When play starts, frontend sends back the same `dealer`

The backend's session state can become desynchronized (e.g., server restart, session changes). The auction + dealer pair must stay consistent.

## Related Documentation

- Domain: Server
- Related: `docs/domains/play/bug-fixes/` (declarer affects play)
- Regression test: `backend/tests/regression/test_jacoby_transfer_declarer_bug.py`

## Verification Steps

1. Start a new hand with dealer != North (e.g., hand 2 = East dealer)
2. Bid using Jacoby Transfer: 1NT → 2♥ → 2♠ → 4♠
3. Click "Play This Hand"
4. Verify declarer is shown correctly (1NT opener who completed transfer)
