# Fix: 2♣ Forcing-to-Game Auction Bug

## Issue
After opening 2♣ (strong artificial, 21+ HCP) and receiving partner's 2♦ artificial waiting response, the responder was incorrectly passing below game level. This violates a fundamental SAYC rule: **2♣ auctions are forcing to game**.

## Example from Review Request
In hand `hand_2025-10-11_14-57-32.json`:
- North (7 HCP) correctly responded 2♦ to South's 2♣ opening
- South rebid 2♠ showing 6+ spades with 21+ HCP
- **North incorrectly passed** at 2♠ (BUG!)
- Should have bid 3♠ or 4♠ to reach game

## Root Causes Found and Fixed

### 1. Bug in Bid Counting Logic ([responses.py:16](backend/engine/responses.py#L16))
**Problem:** The code compared a string position name to an integer index:
```python
my_bids = [bid for i, bid in enumerate(features['auction_history'])
           if features['positions'][i % 4] == features['my_index']]
```
- `features['positions'][i % 4]` returns `'North'` (string)
- `features['my_index']` is `0` (integer)
- They never match, so `my_bids` was always empty!

**Fix:** Compare indices directly:
```python
my_bids_after_opening = [bid for i, bid in enumerate(features['auction_history'])
                        if (i % 4) == features['my_index'] and i > opener_index]
```

### 2. Missing Forcing-to-Game Logic ([responses.py:286-321](backend/engine/responses.py#L286-L321))
**Problem:** The responder's rebid logic didn't check if we're in a forcing 2♣ auction.

**Fix:** Added special case handling:
- After 2♣ opening and 2♦ waiting response, responder **must** bid until game
- With 2+ card support for partner's major suit → bid 4 of the suit
- With 3+ card support for any suit → bid game (4M or 3NT/5m)
- Without support → bid 5+ card suit at 3-level or 3NT
- Cannot pass until 3NT, 4♥, 4♠, 5♣, or 5♦ is reached

## Files Modified
- [backend/engine/responses.py](backend/engine/responses.py)
  - Fixed bid counting logic in `evaluate()` method
  - Added forcing-to-game constraint in `_get_responder_rebid()` method

## Test Results
Created test file `test_2club_forcing_fix.py` with the exact hand from the review request.

**Before fix:**
- North: Pass (after 2♣ - 2♦ - 2♠) ❌ FAIL

**After fix:**
- North: 4♠ (after 2♣ - 2♦ - 2♠) ✓ PASS
- Auction correctly reached game level ✓

## SAYC Convention Reference
From Standard American Yellow Card:
> **2♣ Opening**: Artificial, strong (22+ points), game-forcing. After responder's 2♦ waiting bid, the auction is forcing to game. Responder cannot pass below game (3NT, 4♥, 4♠, 5♣, or 5♦).
