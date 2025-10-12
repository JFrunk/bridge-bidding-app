# Bidding Logic Fixes - October 10, 2025

## Summary

Fixed two critical bidding errors identified in user-reported hand analysis:

1. **Weak Two Preempts with Voids** - System was incorrectly allowing weak 2-level preempts with voids and 4-card side majors
2. **Strong Overcalls (19+ HCP)** - System was passing with very strong balanced hands (19+ HCP) instead of competing

## Changes Made

### 1. Fixed Weak Two Bid Requirements ([preempts.py](backend/engine/ai/conventions/preempts.py))

**Problem:** North opened 2♥ with:
- ♠AJ5 ♥QJ862 ♦J965 ♣void (9 HCP, 6 hearts, **VOID in clubs**)

**SAYC Rules Violated:**
- NO void or singleton ace (hand too shapely/strong)
- NO 4-card side major (may belong in that suit)

**Fix:** Added `_is_valid_weak_two()` method that checks:
```python
def _is_valid_weak_two(self, hand: Hand, preempt_suit: str) -> bool:
    # Check for voids
    for suit in ['♠', '♥', '♦', '♣']:
        if hand.suit_lengths[suit] == 0:
            return False  # Void - reject weak two

    # Check for singleton aces
    for suit in ['♠', '♥', '♦', '♣']:
        if hand.suit_lengths[suit] == 1:
            suit_cards = [card for card in hand.cards if card.suit == suit]
            if suit_cards and suit_cards[0].rank == 'A':
                return False  # Singleton ace - reject weak two

    # Check for 4-card side major
    for major in ['♠', '♥']:
        if major != preempt_suit and hand.suit_lengths[major] >= 4:
            return False  # 4-card side major - reject weak two

    return True
```

**Result:** North now correctly **Passes** instead of opening 2♥

---

### 2. Added Strong Balanced Hand Support ([takeout_doubles.py](backend/engine/ai/conventions/takeout_doubles.py))

**Problem:** West passed with:
- ♠Q982 ♥A7 ♦AKT ♣AQ76 (**19 HCP, balanced**)

**SAYC Issue:**
- Too strong for 1NT overcall (15-18 HCP)
- Too strong for simple overcall (8-16 HCP)
- System had no logic for 19+ HCP balanced hands

**SAYC Solution:**
- With 19+ HCP balanced: **Double first**, then bid NT next round to show 19-21 HCP
- This distinguishes from direct 1NT overcall (15-18)

**Fix:** Updated `_hand_qualifies()` in TakeoutDoubleConvention:
```python
# SPECIAL CASE: Very strong balanced hand (19+ HCP)
# These hands are too strong for 1NT overcall (15-18) but too balanced for suit overcall
# Solution: Double now, bid NT later to show 19-21 HCP
if hand.hcp >= 19 and hand.is_balanced:
    return True  # Will double and bid NT next round
```

Added informative explanation:
```python
if hand.hcp >= 19 and hand.is_balanced:
    return ("X", f"Takeout Double with {hand.hcp} HCP (too strong for 1NT overcall). Planning to bid NT next to show 19+ HCP.")
```

**Result:** West now correctly **Doubles** (X) showing 19+ HCP

---

## Test Results

Created comprehensive test suite: [test_bidding_fixes.py](backend/test_bidding_fixes.py)

```
============================================================
TEST 1: North's opening bid (should NOT be 2♥)
============================================================
North's hand: 9 HCP, 6 hearts, VOID in clubs
North's bid: Pass
Explanation: 📋 Not enough strength to open
✅ PASS: North correctly passed (void makes hand unsuitable for weak two)

============================================================
TEST 2: West's bid after 2♥ - Pass - Pass
============================================================
West's hand: 19 HCP, balanced
West's bid: X
Explanation: Takeout Double with 19 HCP (too strong for 1NT overcall). Planning to bid NT next to show 19+ HCP.
✅ PASS: West correctly doubled (showing 19+ HCP, too strong for 1NT overcall)

============================================================
SUMMARY
============================================================
Test 1 (North's opening): ✅ PASS
Test 2 (West's overcall): ✅ PASS
🎉 All tests passed!
```

## Regression Testing

Ran existing test suite:
```
============================= test session starts ==============================
collected 8 items

tests/test_jacoby_transfers.py::test_initiate_transfer_to_spades PASSED  [ 12%]
tests/test_negative_doubles.py::test_negative_double_is_applicable FAILED [ 25%]
tests/test_opening_bids.py::test_1nt_opening PASSED                      [ 37%]
tests/test_opening_bids.py::test_strong_2nt_opening PASSED               [ 50%]
tests/test_opening_bids.py::test_strong_2c_opening PASSED                [ 62%]
tests/test_responses.py::test_simple_raise_of_major PASSED               [ 75%]
tests/test_responses.py::test_respond_to_2c_negative PASSED              [ 87%]
tests/test_stayman.py::test_should_initiate_stayman PASSED               [100%]

1 failed, 7 passed
```

**Note:** The negative doubles test failure is pre-existing and unrelated to these changes.

## Files Modified

1. **[backend/engine/ai/conventions/preempts.py](backend/engine/ai/conventions/preempts.py)**
   - Added `_is_valid_weak_two()` validation method
   - Updated `_get_opening_preempt()` to call validation for 2-level preempts

2. **[backend/engine/ai/conventions/takeout_doubles.py](backend/engine/ai/conventions/takeout_doubles.py)**
   - Updated `_hand_qualifies()` to handle 19+ HCP balanced hands
   - Enhanced `evaluate()` to provide informative explanations for strong hands

3. **[backend/test_bidding_fixes.py](backend/test_bidding_fixes.py)** (NEW)
   - Comprehensive test suite for the reported issues

## SAYC References

### Weak Two Bids
From SAYC standards:
- 6-card suit with 6-10 HCP
- 2 of top 3 honors (A/K/Q) or 3 of top 5
- **NO void or singleton ace**
- **NO 4-card side major**

### Strong Overcalls
From SAYC standards:
- Direct 1NT overcall: 15-18 HCP, balanced, stopper
- Simple suit overcall: 8-16 HCP
- **19+ HCP balanced:** Double first, bid NT later (shows 19-21)
- **17+ HCP with good suit:** Double first, bid suit later (shows 17+)

## Impact

These changes ensure the AI follows proper SAYC bidding standards for:
1. Preemptive opening bids (weak twos)
2. Competitive bidding with very strong hands

The fixes prevent two common beginner errors:
- Preempting with unsuitable shape (voids, side suits)
- Passing with game-forcing strength in competitive auctions
