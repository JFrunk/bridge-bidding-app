# Ruff Feedback Terminology Fix

**Last Updated:** 2026-01-09
**Date:** 2026-01-09
**Status:** Fixed
**Files Changed:**
- `backend/engine/feedback/play_feedback.py`
- `backend/tests/unit/test_play_feedback.py`

## Issue

Play feedback incorrectly used "ruff" terminology in situations where it didn't apply:

1. **Leading trump called a "ruff"** - When a player led a trump card, the feedback said "Ruffing with X wins this trick optimally" even though leading trump is not a ruff (a ruff is playing trump when void in the led suit)

2. **Claiming "wins this trick" prematurely** - The feedback claimed the ruff would "win" the trick before knowing if it actually would (e.g., 2nd or 3rd hand could be overruffed by 4th hand)

## Root Cause

In `_explain_optimal_play()`, the `PlayCategory.TRUMPING` case had a single hardcoded message that didn't distinguish between:
- Leading trump (not a ruff)
- Actually ruffing (playing trump while void in led suit)
- Position in the trick (2nd, 3rd, or 4th hand)

## Fix

Updated `_explain_optimal_play()` to:

1. **Check if leading trump** - If `current_trick` is empty, use "Leading X is the correct play" instead of claiming a ruff

2. **Check trick position for win claims**:
   - **4th hand**: Can claim "wins" if no higher trump was played
   - **2nd/3rd hand**: Use "is the right play" since opponent could overruff

3. **Detect overruffs** - When existing trumps are in the trick, acknowledge overruffing

Also updated `_generate_hint()` to provide appropriate hints based on whether leading trump or ruffing.

## Test Coverage

Added 13 new tests in `TestFeedbackMessageAccuracy`:

- `test_leading_trump_not_called_ruff` - Leading trump shouldn't say "ruff"
- `test_ruff_second_hand_no_win_claim` - 2nd hand ruff shouldn't claim win
- `test_ruff_third_hand_no_win_claim` - 3rd hand ruff shouldn't claim win
- `test_ruff_fourth_hand_can_claim_win` - 4th hand ruff CAN claim win
- `test_ruff_fourth_hand_higher_trump_already_played` - No win claim if outtrumped
- `test_overruff_message` - Overruff categorization
- `test_categorize_opening_lead` - Opening lead detection
- `test_categorize_subsequent_lead_not_opening` - 2nd+ trick lead isn't opening
- `test_categorize_following_suit` - Following suit detection
- `test_categorize_discarding_no_trump` - NT discard detection
- `test_categorize_sluffing_could_trump` - Sluffing detection
- `test_hint_for_leading_trump` - Trump lead hints
- `test_hint_for_ruffing` - Ruff hints

## Verification

Run tests:
```bash
cd backend
source venv/bin/activate
pytest tests/unit/test_play_feedback.py::TestFeedbackMessageAccuracy -v
```

All 13 tests pass.
