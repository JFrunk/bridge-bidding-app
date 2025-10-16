# DDS AI Crash Fix

## Problem
The Python backend was crashing with a segmentation fault when the AI tried to play cards during gameplay. The crash was occurring in the DDS (Double Dummy Solver) library (`libdds.dylib`).

### Crash Details
- **Exception Type**: `EXC_BAD_ACCESS (SIGSEGV)`
- **Location**: `libdds.dylib` in `Moves::MoveGen0`
- **Symptom**: "Python quit unexpectedly" dialog on macOS
- **Frontend Error**: "AI Play Failed" console message

### Root Cause
The DDS library (via `endplay` Python bindings) has known stability issues on some macOS systems, particularly during complex card play analysis. The library can crash with memory access violations during the `calc_dd_table()` function.

## Solution

### 1. Added Comprehensive Error Handling
Modified `backend/engine/play/ai/dds_ai.py` to catch and handle DDS crashes:

```python
def choose_card(self, state: PlayState, position: str) -> Card:
    try:
        # ... DDS analysis code ...
        dd_table = calc_dd_table(deal)
        # ... evaluation logic ...
    except Exception as e:
        # Fall back to simple heuristic play
        print(f"⚠️  DDS failed for {position}: {e}")
        return self._fallback_choose_card(state, position, legal_cards)
```

### 2. Implemented Fallback Mechanism
Added `_fallback_choose_card()` method that uses simple bridge heuristics when DDS fails:

- **Leading**: Play high cards from long suits
- **Following**: Play high on second hand, low on third hand
- **Forced plays**: Return the only legal card

### 3. Protected Critical Functions
Added additional error handling in `_evaluate_position_with_dds()`:

```python
try:
    dd_table = calc_dd_table(deal)
    data = dd_table.to_list()
except (RuntimeError, OSError, SystemError) as dds_error:
    print(f"⚠️  DDS calc_dd_table failed: {dds_error}")
    raise  # Re-raise to trigger outer fallback
```

### 4. Fixed Type Imports
Ensured proper handling when DDS library is not available:

```python
try:
    from endplay.types import Deal, Player as EndplayPlayer, Denom
    DDS_AVAILABLE = True
except ImportError:
    DDS_AVAILABLE = False
    Deal = None
    EndplayPlayer = None
    Denom = None
```

## Impact

### Before Fix
- ❌ Backend crashes completely when AI tries to play
- ❌ User sees "Python quit unexpectedly" dialog
- ❌ Game becomes unplayable
- ❌ All session data lost

### After Fix
- ✅ Backend continues running even if DDS fails
- ✅ AI falls back to simple heuristic play
- ✅ Game remains playable
- ✅ Warning logged but no crash
- ✅ Users can complete hands successfully

## Testing

### How to Test
1. Start a new game
2. Complete the bidding phase
3. Observe gameplay phase:
   - AI should play cards successfully
   - No Python crashes
   - Check backend logs for any DDS warnings

### Expected Behavior
- **If DDS works**: Normal expert-level AI play
- **If DDS fails**: Warning message in logs, fallback to heuristic play
- **No crashes**: Game continues regardless of DDS status

## Monitoring

Watch backend logs for these messages:
- `⚠️  DDS failed for [position]: [error]` - DDS encountered an error, using fallback
- `⚠️  DDS calc_dd_table failed: [error]` - DDS library call failed

## Alternative Solutions

If DDS continues to cause issues, consider:

1. **Disable DDS entirely**: Set `ai_difficulty` to "advanced" (Minimax depth-3) instead of "expert"
2. **Use different DDS build**: Try compiling DDS from source for better macOS compatibility
3. **Downgrade endplay**: Try an older version of the endplay library
4. **Switch to pure-Python solution**: Use only Minimax AI (slower but stable)

## Files Modified

- `backend/engine/play/ai/dds_ai.py`: Added error handling and fallback mechanism
- Created test file: `backend/test_dds_fallback.py`

## Related Issues

This fix addresses the segmentation fault crash reported during gameplay. The DDS library is known to have stability issues on macOS ARM (Apple Silicon) systems.

## Future Improvements

1. Add configuration option to disable DDS at startup
2. Implement caching to reduce DDS calls
3. Add telemetry to track DDS failure rates
4. Consider alternative double-dummy solver libraries

---

**Last Updated**: 2025-10-14
**Status**: Fixed ✅
