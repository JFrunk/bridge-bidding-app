# Tactical Signal Overlay for DDS Play

**Date:** 2025-01-05
**Status:** Implemented
**Component:** Play Engine / AI

## Overview

The Tactical Signal Overlay transforms the Double Dummy Solver (DDS) from a "perfect knowledge" engine into a "process-oriented teacher" that plays like a knowledgeable human partner.

## Problem Solved

DDS assumes all equal-rank cards are identical (e.g., discarding ♠2 vs ♠4 from length of 5). However, human players use these choices to signal information to partner:

- **Before:** DDS picks randomly from equivalence sets, confusing users
- **After:** DDS follows standard bridge conventions and explains WHY

## Architecture

```
[DDS Move Generator]
       |
       v
[Equivalence Set Identified] -> {♠2, ♠4, ♠7} all yield 10 tricks
       |
       v
[TacticalPlayFilter]
       |-- 2nd Hand Low Logic
       |-- 3rd Hand High Logic
       |-- Attitude/Count Signals
       |
       v
[Selected Play] -> ♠2 + signal_reason
```

## Signal Categories

| Context | Heuristic | Reason |
|---------|-----------|--------|
| Second Hand Follow | MIN_OF_EQUALS | "2nd Hand Low: Preserving higher honors." |
| Third Hand Follow | MAX_OF_EQUALS | "3rd Hand High: Forcing declarer's resources." |
| Third Hand Sequence | BOTTOM_OF_SEQUENCE | "Playing Q from KQJ signals the K." |
| Opening Lead Sequence | TOP_OF_SEQUENCE | "Leading K from KQJ promises the cards below." |
| Fourth Hand | CHEAPEST_WINNER | "Win with lowest winning card." |
| First Discard | ATTITUDE_SIGNAL | "High encourages, low discourages." |
| Subsequent Discard | COUNT_SIGNAL | "High-low = even count." |

## Files

| File | Purpose |
|------|---------|
| `backend/engine/play/ai/play_signal_overlay.py` | TacticalPlayFilter class |
| `backend/engine/play/ai/play_signals.json` | Signal configuration |
| `backend/engine/play/ai/dds_ai.py` | Integration point |
| `backend/engine/feedback/play_feedback.py` | PlayFeedback dataclass |
| `backend/migrations/013_add_signal_columns.sql` | Database migration |

## API Changes

### PlayFeedback Dataclass

New fields added:
```python
signal_reason: Optional[str]       # Why this card was chosen
signal_heuristic: Optional[str]    # e.g., "MIN_OF_EQUALS"
signal_context: Optional[str]      # e.g., "SECOND_HAND_FOLLOW"
is_signal_optimal: bool            # True if follows conventions
```

### Analytics API

`/api/hand-detail` now returns signal fields in `all_decisions`:
```json
{
  "signal_reason": "2nd Hand Low: Preserving higher honors.",
  "signal_heuristic": "MIN_OF_EQUALS",
  "signal_context": "SECOND_HAND_FOLLOW",
  "is_signal_optimal": true
}
```

## UI Integration

### HandReviewModal (TrickFeedbackPanel)

Displays signal reasoning:
- **Green box:** "Signal Logic: [reason]" for optimal signals
- **Orange box:** "Signal Note: [reason]" for suboptimal signals
- **Signal badge:** Appears for signal-related issues

### DecayChart

- Orange diamond markers for signal warnings
- Stats show signal count: "DD: 10 | Actual: 10 ✓ | 2 signals"

## Testing

```bash
# Run signal overlay tests (23 tests)
cd backend && PYTHONPATH=. pytest tests/play/test_tactical_signal_overlay.py -v
```

## Database Migration

Run on production:
```sql
-- Migration 013
ALTER TABLE play_decisions ADD COLUMN signal_reason TEXT;
ALTER TABLE play_decisions ADD COLUMN signal_heuristic TEXT;
ALTER TABLE play_decisions ADD COLUMN signal_context TEXT;
ALTER TABLE play_decisions ADD COLUMN is_signal_optimal BOOLEAN DEFAULT 1;
```

## Future Enhancements

1. **User signal evaluation:** Evaluate user plays against signal conventions (not just DDS optimal)
2. **Signal_warnings array:** Generate for DecayChart from play decisions with `is_signal_optimal=false`
3. **Defensive signal systems:** Support UPSIDE-DOWN, Odd-Even conventions
