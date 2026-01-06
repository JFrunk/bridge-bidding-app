# Bug Fix: Opener Must Rebid After 2-Over-1 New Suit Response

**Date Fixed:** 2026-01-06
**Severity:** High
**Component:** Bidding Engine (feature_extractor.py)

## Bug Description

When partner responded with a 2-level new suit (e.g., auction 1♠-Pass-2♣-Pass-?), the opener was incorrectly allowed to pass. In SAYC, a new suit response by an unpassed hand at the 2-level is **ONE ROUND FORCING** - opener must bid again.

## User Report

User feedback from 2026-01-06:
> "Why would my partner pass me when I respond with two club and previously 1 spade. Should that not signal points. I have 22 points. What is the right bid."

User had 21 HCP and responded 2♣ to partner's 1♠ opening. Partner (North) incorrectly passed, leaving them in 2♣ when they had slam values (32+ combined HCP).

## Root Cause

The forcing status analyzer in `backend/engine/ai/feature_extractor.py` function `analyze_forcing_status()` only detected forcing status from the **responder's perspective**. It correctly identified that "my new suit response is forcing" but did NOT identify when "partner's new suit response forces me to bid again."

The logic was:
```python
# This only detects forcing from responder's view
if opener_index == partner_index and len(my_bids) >= 1:
    # Check if MY bid was a new suit...
```

Missing was the **opener's perspective**:
```python
# What if I am opener and PARTNER bid a new suit?
```

## Fix Applied

Added new detection block in `analyze_forcing_status()`:

```python
# CRITICAL: Check if I am opener and partner responded with a new suit
# A new suit response by partner is FORCING - opener MUST rebid
if opener_index == my_index and len(partner_bids) >= 1:
    partner_response = partner_bids[0][1]
    partner_response_suit = get_suit_from_bid(partner_response)
    opening_suit = get_suit_from_bid(opening_bid)

    if partner_response_suit and opening_suit and partner_response_suit != opening_suit:
        result['forcing_type'] = 'one_round_forcing'
        result['forcing_source'] = 'partner_new_suit_response'
        result['must_bid'] = True
        return result
```

## Files Changed

- `backend/engine/ai/feature_extractor.py` - Added forcing detection for opener
- `backend/tests/regression/test_2over1_forcing_response.py` - New regression test

## Testing

### Regression Tests Added
- `test_opener_must_rebid_after_2_over_1_response` - Core bug fix verification
- `test_forcing_status_detects_partner_new_suit_response` - Unit test for forcing detection
- `test_opener_rebids_6_card_suit_with_minimum` - Rebid behavior verification
- `test_2_over_1_not_forcing_after_interference` - Edge case: contested auctions
- `test_1nt_response_not_forcing` - Edge case: 1NT is not forcing
- `test_raise_not_forcing` - Edge case: raises are not new suits

### Quality Score
- Bidding quality score: 94.4% (Grade B) - no regression

## SAYC Reference

From Standard American Yellow Card:
- A new suit response at the 2-level (2-over-1) promises 10+ HCP
- New suit responses are forcing for one round
- Opener MUST rebid after a forcing response
- Only after both partners have had a chance to pass is the auction non-forcing

## Verification

To verify the fix is working:
```bash
cd backend
python -m pytest tests/regression/test_2over1_forcing_response.py -v
```

All 6 tests should pass.
