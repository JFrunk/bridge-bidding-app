# DDS Position Key Mismatch Fix

**Date:** 2025-11-03
**Last Updated:** 2025-11-03
**Component:** Play Quality Testing (test_play_quality_integrated.py)
**Severity:** Critical (blocked DDS testing)
**Status:** Fixed

## Problem

DDS (Double Dummy Solver) testing in GitHub Actions was failing with 100% fallback rate to SimplePlayAI. Every card play attempt threw a `KeyError: 'N'` error, resulting in impossible timing (0.001s per hand instead of 15-30s).

## Root Cause

**Position key format mismatch** in `test_play_quality_integrated.py`:

```python
# Line 118-123: Hands dictionary created with single-letter keys
hands = {
    'N': generate_random_hand(),
    'S': generate_random_hand(),
    'E': generate_random_hand(),
    'W': generate_random_hand()
}

# Line 144-145: _simulate_bidding() used full names
positions = ['North', 'East', 'South', 'West']  # ❌ Wrong!
dealer_idx = positions.index(dealer)

# Line 154: KeyError thrown here
hand = hands[position]  # position='North', but hands only has 'N'
```

The `_simulate_bidding()` method used full position names ('North', 'East', 'South', 'West') while the hands dictionary used single-letter keys ('N', 'E', 'S', 'W').

## Impact

- **DDS testing:** Completely broken - 100% fallback to SimplePlayAI
- **Test results:** Invalid (showing 40% success instead of expected 85-95%)
- **CI/CD:** GitHub Actions DDS workflow unusable
- **Production verification:** Unable to validate DDS before deployment

## Fix

Changed `_simulate_bidding()` to use single-letter position keys to match the hands dictionary format:

```python
# Line 144: Use single-letter positions
positions = ['N', 'E', 'S', 'W']  # ✅ Correct!
dealer_idx = positions.index(dealer)
```

**File:** `backend/test_play_quality_integrated.py`
**Lines Changed:** 144
**Commit:** [commit hash will be added after push]

## Verification

After fix, DDS should:
- ✅ Successfully access hands with single-letter keys
- ✅ Complete card play without KeyError exceptions
- ✅ Show realistic timing (15-30s per hand, not 0.001s)
- ✅ Achieve 85-95% success rate (not 40% SimplePlayAI rate)

**Test command:**
```bash
# Trigger GitHub Actions workflow: .github/workflows/dds_baseline.yml
# Or run locally on Linux:
cd backend
python3 test_play_quality_integrated.py --hands 10 --ai dds
```

## Related Issues

This bug was introduced when refactoring the test script to support DDS. The original version used full position names throughout, but the fix to support DDS changed the hands dictionary to single-letter keys (required by PlayEngine and DDS) without updating `_simulate_bidding()`.

## Prevention

**Code review checklist:**
- [ ] Verify position key format consistency across all test code
- [ ] Check that hands dictionary keys match position variable format
- [ ] Test bidding simulation before testing play simulation
- [ ] Add type hints to catch key format mismatches

**Architecture note:** The codebase should standardize on single-letter position keys ('N', 'E', 'S', 'W') throughout, as this is the format used by PlayEngine, DDS, and all production code.

## Documentation Updated

- [x] Bug fix documentation created
- [x] Related test documentation updated (if applicable)
- [x] Commit message includes detailed explanation

## See Also

- DDS Testing Philosophy: `DDS_TESTING_PHILOSOPHY.md` (project root)
- Play Quality Score Protocol: `.claude/CODING_GUIDELINES.md` (lines 667-1027)
- DDS Testing Without Shell Access: `DDS_TESTING_WITHOUT_SHELL_ACCESS.md` (project root)
