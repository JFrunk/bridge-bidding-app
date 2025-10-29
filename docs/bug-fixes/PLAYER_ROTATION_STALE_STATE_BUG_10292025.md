# Player Rotation Stale State Bug - Fixed 2025-10-29

**Last Updated:** 2025-10-29

## Summary

**Bug:** Same player (North) bid 4 times consecutively instead of rotating through East → South → West
**Root Cause:** Frontend useEffect captured stale `nextPlayerIndex` state before React re-render
**Impact:** Critical - Users unable to bid, AI made multiple consecutive bids
**Status:** ✅ FIXED

## Symptoms

User reported: "I was mid responding to a two level bid when the system presented a new hand for me to bid."

**Observed Behavior:**
- North opened 1NT (correct)
- North bid 1NT again (WRONG - should be East)
- North bid 1NT again (WRONG - should be South)
- North bid 1NT again (WRONG - should be West)
- East passed
- South never got to bid

**Evidence:** [backend/review_requests/hand_2025-10-29_13-49-57.json](../../backend/review_requests/hand_2025-10-29_13-49-57.json)

## Root Cause Analysis

### Technical Explanation

The frontend AI bidding loop uses a `useEffect` hook that depends on `[auction, nextPlayerIndex, ...]`:

```javascript
useEffect(() => {
  if (isAiBidding && !isAuctionOver(auction)) {
    const runAiTurn = async () => {
      // BUG: This captures STALE nextPlayerIndex!
      const currentPlayer = players[nextPlayerIndex];

      // Send to backend
      const response = await fetch('/api/get-next-bid', {
        body: JSON.stringify({
          current_player: currentPlayer  // WRONG player sent!
        })
      });

      // Update state
      setAuction([...auction, data]);
      setNextPlayerIndex((prev) => (prev + 1) % 4);
    };
    runAiTurn();
  }
}, [auction, nextPlayerIndex, isAiBidding, ...]);
```

### The Race Condition

1. **North bids:** `nextPlayerIndex = 0`
2. **State updates:** `setAuction()` and `setNextPlayerIndex(1)` called
3. **useEffect re-runs immediately** (because `auction` changed)
4. **BUT:** React hasn't re-rendered yet, so `nextPlayerIndex` is still `0`
5. **Result:** `players[0]` = 'North' is sent to backend AGAIN
6. **Repeat:** This continues until auction ends or user intervenes

### Why It Happened

React state updates are **asynchronous** and **batched**. When `setAuction()` triggers the useEffect to re-run, the new `nextPlayerIndex` value hasn't been committed to the component's state yet. The useEffect closure captures the **old value** from the previous render.

## The Fix

### Change Made

**File:** [frontend/src/App.js:1344](../../frontend/src/App.js)

**Before (WRONG):**
```javascript
const currentPlayer = players[nextPlayerIndex];  // Stale state!
```

**After (CORRECT):**
```javascript
// Calculate current player from auction length and dealer
// This is always correct regardless of state update timing
const currentPlayer = calculateExpectedBidder(dealer, auction.length);
```

### Why This Works

The `calculateExpectedBidder` function derives the current player from **immutable inputs**:
- `dealer` - never changes during a hand
- `auction.length` - always reflects the latest auction state

```javascript
const calculateExpectedBidder = (currentDealer, auctionLength) => {
  const dealerIndex = players.indexOf(currentDealer);
  return players[(dealerIndex + auctionLength) % 4];
};
```

This calculation is **deterministic** and **state-independent**, so it never suffers from stale state issues.

## Testing

### Regression Test

**File:** [backend/tests/regression/test_player_rotation_bug_10292025.py](../../backend/tests/regression/test_player_rotation_bug_10292025.py)

**Test Strategy:**
1. Recreate exact hands from bug report
2. Simulate proper rotation using `calculateExpectedBidder` logic
3. Verify each player bids in correct order: North → East → South → West
4. Assert no player bids twice consecutively

**Test Results:**
```
✅ test_player_rotation_advances_correctly PASSED
✅ test_player_calculation_function PASSED
```

### Manual Testing

Verified fix by:
1. Starting new hand with North as dealer
2. Observing AI bidding sequence
3. Confirming proper rotation through all 4 players
4. Verifying South gets opportunity to bid

## Related Issues

### Systematic Analysis

Searched codebase for similar patterns:
```bash
grep -r "players\[nextPlayerIndex\]" frontend/src/
grep -r "useEffect.*auction.*nextPlayerIndex" frontend/src/
```

**Result:** Only one location (AI bidding loop) exhibited this bug pattern.

### Other useEffect Dependencies

Reviewed all useEffect hooks that depend on auction or player state:
- ✅ Play phase AI loop - uses proper state management
- ✅ Initialization effects - no rotation dependency
- ✅ Dashboard refresh - no player rotation involved

**Conclusion:** Bug was isolated to AI bidding loop only.

## Prevention

### Best Practices Added

1. **Derive, don't store:** Calculate values from source of truth (auction.length + dealer)
2. **Avoid state dependencies in useEffect:** Prefer deriving from props/immutable state
3. **Add debug logging:** Log both calculated and state-based values for comparison

### Code Review Checklist

When reviewing React state updates in useEffect:
- [ ] Does useEffect depend on state that gets updated inside it?
- [ ] Could the state be stale when the effect runs?
- [ ] Can the value be derived from immutable/stable sources?
- [ ] Are there debug logs to detect stale state?

## Files Changed

**Frontend:**
- ✅ [frontend/src/App.js](../../frontend/src/App.js) - Fix AI bidding loop (lines 1341-1344)

**Tests:**
- ✅ [backend/tests/regression/test_player_rotation_bug_10292025.py](../../backend/tests/regression/test_player_rotation_bug_10292025.py) - New regression test

**Documentation:**
- ✅ [docs/bug-fixes/PLAYER_ROTATION_STALE_STATE_BUG_10292025.md](./PLAYER_ROTATION_STALE_STATE_BUG_10292025.md) - This file

## References

- **Bug Report:** [backend/review_requests/hand_2025-10-29_13-49-57.json](../../backend/review_requests/hand_2025-10-29_13-49-57.json)
- **React Docs:** [State Updates May Be Asynchronous](https://react.dev/learn/state-as-a-snapshot)
- **TDD Workflow:** [.claude/CODING_GUIDELINES.md](../../.claude/CODING_GUIDELINES.md)

---

**Tested:** ✅ Manual testing + regression test
**Documented:** ✅ This file + code comments
**Committed:** ✅ Test and fix committed together
**Status:** **RESOLVED**
