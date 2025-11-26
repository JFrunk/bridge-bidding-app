# Jacoby Transfer and Stayman Validation Bypass Fix

**Date:** 2025-11-26
**Status:** Fixed
**Severity:** High (prevented correct bids from being made)

## Problem

Jacoby Transfer and Stayman initiation bids were being incorrectly rejected by the `SuitLengthValidator`.

### User Report
> With a 1NT bid by my partner and with 10 points how can pass be the appropriate call?

The user had:
- 5 spades (JT985)
- 1 heart
- 10 total points (9 HCP + 1 distribution)

The AI was recommending **Pass** instead of **2♥** (Jacoby Transfer to spades).

### Root Cause

The `SuitLengthValidator` in `validation_pipeline.py` was checking if the bid suit met length requirements:

```python
# Extract suit from bid (e.g., "2♥" → "♥")
suit = bid[1:]
suit_length = hand.suit_lengths.get(suit, 0)

# Check if hand has enough cards in that suit
if suit_length < min_length:
    return False, f"Bid {suit} with only {suit_length} cards (need {min_length}+)"
```

This works for natural bids, but **Jacoby Transfers and Stayman are artificial bids**:
- **2♦** = Transfer to **hearts** (doesn't promise diamonds)
- **2♥** = Transfer to **spades** (doesn't promise hearts)
- **2♣** = Stayman asking about **majors** (doesn't promise clubs)

When South bid 2♥ with only 1 heart, the validator rejected it as "Bid ♥ with only 1 cards (need 5+)".

## Solution

Added `bypass_suit_length: True` metadata to all artificial convention bids:

### jacoby_transfers.py

```python
def _get_transfer_bid(self, hand: Hand) -> Optional[Tuple[str, str, dict]]:
    # Metadata to bypass suit length validation for artificial transfer bids
    # The bid suit (♦/♥) is NOT the target suit (♥/♠)
    metadata = {'bypass_suit_length': True}

    if hand.suit_lengths['♥'] >= 5:
        return ("2♦", "Jacoby Transfer showing 5+ Hearts.", metadata)
    if hand.suit_lengths['♠'] >= 5:
        return ("2♥", "Jacoby Transfer showing 5+ Spades.", metadata)
    return None
```

### stayman.py

```python
def _initiate_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
    """Bid 2♣ Stayman."""
    # Metadata to bypass suit length validation for artificial Stayman bid
    # 2♣ is asking about majors, not showing clubs
    metadata = {'bypass_suit_length': True}
    return ("2♣", f"Stayman. Asks partner for a 4-card major...", metadata)
```

The `ValidationPipeline` already supported this bypass via metadata:

```python
if isinstance(validator, SuitLengthValidator) and metadata.get('bypass_suit_length'):
    logger.debug(f"Bypassing SuitLengthValidator for artificial bid: {bid}")
    continue
```

## Files Changed

1. `backend/engine/ai/conventions/jacoby_transfers.py`
   - Changed `_get_transfer_bid()` to return 3-tuple with metadata

2. `backend/engine/ai/conventions/stayman.py`
   - Changed `_initiate_stayman()` to return 3-tuple with metadata

## Testing

### Regression Tests Added
`tests/regression/test_jacoby_transfer_validation_bypass.py`:
- `test_transfer_to_spades_with_short_hearts` - Main bug reproduction
- `test_transfer_to_hearts_with_short_diamonds` - Hearts transfer case
- `test_stayman_with_short_clubs` - Stayman case

### Quality Score
```
Before: Jacoby transfers failing validation
After:  95.7% composite score (Grade A)
        100% Legality
        100% Appropriateness
```

## Related Issues

- This was the same pattern already fixed for:
  - `_get_completion_bid()` in Jacoby (opener completing transfer)
  - `_respond_to_stayman()` in Stayman (opener's 2♦/2♥/2♠ response)

The fix ensures consistency across all artificial bids in these conventions.

## Lessons Learned

1. **Artificial bids need special handling** - Convention bids that don't show the suit they bid require validation bypass
2. **Check all return paths** - Initiation and completion bids are both artificial in transfer conventions
3. **Metadata bypass pattern works well** - The existing infrastructure handled this correctly once the metadata was provided
