# Server Crash Fixes - January 2, 2026

## Issue Summary

Multiple server crashes were causing session data loss and corrupted "Show All Hands" responses in the Hand Review modal.

## Root Causes Identified

### 1. Suit Symbol Conversion Bug (analytics_api.py)

**Location:** `backend/engine/learning/analytics_api.py`

**Problem:** When creating Hand objects for DD analysis, suit symbols were being converted in the wrong direction:
- Code converted Unicode symbols (♠♥♦♣) to DDS format (S,H,D,C)
- Then passed to `Hand()` which expects Unicode symbols
- This caused `KeyError: 'S'` crashes

**Fix:** Reversed the mapping to convert TO Unicode instead of FROM:
```python
# Before (broken):
suit_map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}

# After (fixed):
suit_to_unicode = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
```

**Files Changed:** 3 locations in analytics_api.py (~lines 2120, 2195, 2430)

### 2. Void Suit Handling (dds_ai.py)

**Location:** `backend/engine/play/ai/dds_ai.py`

**Problem:** When generating PBN strings for the endplay library, void suits used '-' character:
```python
hand_str = '.'.join([
    ''.join(suits['♠']) or '-',  # '-' for void
    ...
])
```
The endplay library throws "could not convert '-' to Rank" error.

**Fix:** Use empty string for void suits (correct PBN format):
```python
hand_str = '.'.join([
    ''.join(suits['♠']),  # Empty string for void
    ...
])
```

### 3. Partial Hand Validation (hand.py, server.py)

**Location:** `backend/engine/hand.py`, `backend/server.py`

**Problem:** The `Hand` class requires exactly 13 cards:
```python
if len(cards) != 13:
    raise ValueError("A hand must contain exactly 13 cards.")
```
During play, hands have fewer cards as cards are played. Reconstructing play state caused crashes.

**Fix:** Added `_skip_validation` parameter to Hand class:
```python
def __init__(self, cards, _skip_validation=False):
    if not _skip_validation and len(cards) != 13:
        raise ValueError("A hand must contain exactly 13 cards.")
```

And use it in server.py when reconstructing play state:
```python
hands[pos] = Hand(cards, _skip_validation=True)
```

## Impact

- **Before:** Server crashes caused by these issues led to:
  - Session data loss
  - "Show All Hands" returning empty/partial data
  - Incorrect HCP metadata displayed

- **After:** Server stability restored, Hand Review modal works correctly

## Testing

1. Verified analytics_api.py fix with unit test for DD analysis
2. Verified dds_ai.py fix handles void suits correctly
3. Verified hand.py allows partial hands with skip flag
4. Deployed analytics_api.py fix to production successfully

## Deployment

- analytics_api.py: Deployed 2026-01-02
- dds_ai.py, hand.py, server.py: To be deployed together
