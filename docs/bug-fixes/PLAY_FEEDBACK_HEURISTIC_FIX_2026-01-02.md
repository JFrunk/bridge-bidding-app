# Play Feedback Heuristic Mode Fix

**Date:** 2026-01-02
**Status:** Fixed
**Impact:** High - Play evaluation accuracy on development/macOS

## Problem

The play feedback system was providing inaccurate feedback when DDS (Double Dummy Solver) was unavailable (macOS development environment):

1. **Hardcoded trick values**: `_analyze_with_minimax()` always returned `user_tricks=8, optimal_tricks=10`, causing every non-optimal play to falsely claim "costs 2 tricks"

2. **Inflated play counts**: 78 plays were being counted for a single hand because `play_decisions` table lacked a `hand_number` column - all plays in a session were grouped together

3. **False precision in messages**: Feedback text claimed specific trick costs even when using heuristic analysis that cannot determine exact counts

## Root Cause Analysis

### Issue 1: Hardcoded Values
```python
# OLD CODE (broken)
def _analyze_with_minimax(self, ...):
    # ...
    user_tricks = 8  # WRONG: Always 8
    optimal_tricks = 10  # WRONG: Always 10
    return [optimal_card], user_tricks, optimal_tricks
```

The Minimax AI can only determine which card is "better" via heuristic evaluation, but cannot calculate exact trick counts. The hardcoded 8/10 values were placeholder code that was never replaced.

### Issue 2: Missing hand_number Filter
```sql
-- OLD QUERY (grouped all plays in session)
SELECT ... FROM play_decisions
WHERE session_id = ? AND user_id = ?

-- Should filter by specific hand
SELECT ... FROM play_decisions
WHERE session_id = ? AND user_id = ? AND hand_number = ?
```

### Issue 3: False Precision
The `to_user_message()` method claimed specific trick counts without checking if the data came from DDS (exact) or Minimax (heuristic).

## Solution

### 1. Honest Heuristic Mode
```python
def _analyze_with_minimax(self, ...):
    optimal_card = self._minimax_ai.choose_card(state, position)

    # If user played the same as Minimax, it's optimal
    if user_card == optimal_card:
        return [optimal_card], 0, 0, "heuristic"

    # Non-optimal: return -1 to indicate unknown trick cost
    return [optimal_card], -1, -1, "heuristic"
```

### 2. Analysis Source Tracking
Added `analysis_source` field to `PlayFeedback` dataclass:
- `"dds"` = Exact DDS analysis (production/Linux)
- `"heuristic"` = Minimax estimation (development/macOS)

### 3. Conditional Messaging
```python
def to_user_message(self, verbosity="normal"):
    is_heuristic = self.analysis_source == "heuristic" or self.tricks_cost < 0

    if correctness == PlayCorrectnessLevel.SUBOPTIMAL:
        if not is_heuristic and self.tricks_cost > 0:
            msg = f"{optimal_str} saves {self.tricks_cost} tricks"
        else:
            msg = f"{optimal_str} is likely better"  # No false precision
```

### 4. Hand Number Filtering
- Added `hand_number` column to `play_decisions` table
- Updated `evaluate_and_store()` to accept and store `hand_number`
- Updated `get_hand_play_quality_summary()` to filter by `hand_number`

## Files Modified

1. `backend/engine/feedback/play_feedback.py`
   - `_analyze_with_minimax()`: Returns -1 for unknown trick counts
   - `PlayFeedback`: Added `analysis_source` field
   - `to_user_message()`: Checks `is_heuristic` before claiming trick counts
   - `_generate_reasoning()`: Conditional messaging
   - `_calculate_score()`: Handles -1 tricks_cost
   - `evaluate_and_store()`: Added `hand_number` parameter
   - `_store_feedback()`: Stores `hand_number`

2. `backend/engine/learning/analytics_api.py`
   - `get_hand_play_quality_summary()`: Filters by `hand_number`

3. `backend/server.py`
   - Play card endpoints: Pass `hand_number` to feedback generator

4. `backend/migrations/008_add_hand_number_to_play_decisions.sql`
   - Adds `hand_number` column and index

## Testing

All 67 play-related unit tests pass:
```bash
pytest tests/unit -k "play" -v
# 67 passed, 368 deselected
```

Verified:
- Unknown tricks_cost (-1) gives score of 6.0 (benefit of doubt)
- Unknown tricks_cost gives correctness: SUBOPTIMAL (non-judgmental)
- Messages don't claim specific trick counts in heuristic mode

## Deployment Notes

1. Run migration on production:
   ```sql
   ALTER TABLE play_decisions ADD COLUMN hand_number INTEGER;
   CREATE INDEX idx_play_decisions_session_hand ON play_decisions(session_id, hand_number);
   ```

2. DDS is available on production (Linux) - these fixes primarily affect development environment display

## Related

- DDS platform detection: `PLATFORM_ALLOWS_DDS = platform.system() == 'Linux'`
- DDS crashes on macOS M1/M2: See `BUG_DDS_CRASH_2025-10-18.md`
