# Overcall Module Bidding Crash Fix

**Date:** 2026-01-03
**Severity:** Critical
**Status:** Fixed

## Summary

Fixed a critical bug where bidding would completely stop during gameplay when the AI needed to make an overcall. The bug was caused by a method signature mismatch in `OvercallModule._get_overcall_bid()`.

## Symptoms

- Bidding freezes completely mid-auction
- User feedback reports: "South is still highlighted and being asked to bid" after auction should have ended
- Error in logs: `TypeError: OvercallModule._get_overcall_bid() takes 4 positional arguments but 5 were given`
- Multiple user feedback reports about bidding stopping

## Root Cause

In `backend/engine/overcalls.py`:

- **Line 34 (caller):** `self._get_overcall_bid(hand, features, is_balancing, hcp_adjustment)`
- **Line 67 (definition):** `def _get_overcall_bid(self, hand, features, is_balancing)`

The `evaluate()` method was passing 4 arguments including `hcp_adjustment`, but the method signature only accepted 3 parameters. The `hcp_adjustment` parameter (used for balancing seat HCP adjustments) was missing from the method definition.

## Fix Applied

Added the missing `hcp_adjustment` parameter to the method signature:

```python
# Before
def _get_overcall_bid(self, hand: Hand, features: Dict, is_balancing: bool) -> Optional[Tuple[str, str]]:

# After
def _get_overcall_bid(self, hand: Hand, features: Dict, is_balancing: bool, hcp_adjustment: int = 0) -> Optional[Tuple[str, str]]:
```

## Error Log Evidence

From production error logs:
- 2025-12-30: `TypeError: object of type 'NoneType' has no len()`
- 2025-12-29: `TypeError: unhashable type: 'dict'`
- 2025-12-25: `TypeError: unhashable type: 'dict'`
- 2025-12-24: `AttributeError: 'dict' object has no attribute 'endswith'`

Error hash: `12d68444d5ac`

## Testing

- 18 regression tests pass (`test_auction_history_format_bug_12302025.py`)
- 34 overcall-specific tests pass
- 432 unit tests pass

## Files Changed

- `backend/engine/overcalls.py`

## User Feedback Addressed

Multiple feedback reports from users experiencing bidding freezes, particularly after opponents made 3-level preemptive bids or when AI needed to make overcalls.
