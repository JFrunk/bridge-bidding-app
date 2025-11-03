# BUG-H002: AI Inappropriately Discards King in NT Contract (Trick 5)

**Date:** 2025-10-18
**Status:** 🔴 UNRESOLVED - Active Investigation
**Severity:** HIGH - AI appears broken, user trust lost
**Priority:** Immediate Fix Required

---

## Bug Description

During NoTrump (NT) gameplay, in **Trick 5**, the AI (East) inappropriately discarded a **King of Clubs (K♣)** when lower cards were available in hand. This represents poor bridge play for an expert-level AI.

### User Report
> "During gameplay phase in NT, In trick 5, the AI discards a K for East which is inappropriate. This is a high priority bug-hoo2 in the bug list."

---

## Root Cause Analysis

After investigating the AI discard logic, I've identified **multiple potential issues**:

### 1. **Communication Component Over-Values Kings (PRIMARY SUSPECT)**
**Location:** `backend/engine/play/ai/evaluation.py:360-361`

```python
# King is likely an entry if we have length
elif highest.rank == 'K':
    position_entries += 0.6
```

**Problem:**
- The evaluation function assigns 0.6 points to Kings as "likely entries"
- This bonus applies even in **discard situations** where the King cannot be used as an entry
- When East is void in the led suit and must discard, the evaluation incorrectly:
  1. Evaluates discarding K♣ as losing 0.6 "entry value"
  2. Evaluates discarding a low card (e.g., ♦6) as losing minimal value
  3. Chooses the King because the minimax search thinks keeping it preserves "communication"

**Why This Happens:**
- The communication component doesn't distinguish between:
  - **Active play**: King in a suit you can lead = potential entry
  - **Discard situation**: King in a suit being discarded ≠ entry value lost

### 2. **Danger Hand Component May Misfire**
**Location:** `backend/engine/play/ai/evaluation.py:518-597`

The danger hand component (lines 574-582) identifies Kings as "stoppers" in NT:
```python
elif top_card.rank == 'K' and len(our_cards) >= 2:
    has_stopper = True
    stopper_quality = 1
```

**Potential Issue:**
- If East has K♣ with 5+ clubs, it might think "K♣ is a stopper, don't discard it"
- But this logic should only apply when **defending against opponent's long suit**
- It should NOT apply when discarding from a suit partner/declarer is leading

### 3. **Minimax Tolerance-Based Tiebreaker May Not Trigger**
**Location:** `backend/engine/play/ai/minimax_ai.py:173-198`

The code has a tolerance-based tiebreaker (0.3 tricks) to prefer low cards:
```python
tolerance = 0.3  # Allow 0.3 trick difference
```

**Potential Issue:**
- If the evaluation function values K♣ at 0.6 "entry points" higher than ♦6
- The difference exceeds the 0.3 tolerance
- The tiebreaker never activates, so the King is chosen

---

## Evidence Trail

### Previous Fix Attempts (Partial Success)
According to `BUG_TRACKING_SYSTEM.md:228-276`, previous fixes included:
- ✅ AI card validation before playing
- ✅ Improved discard logic in Minimax AI
- ✅ Tolerance-based tiebreaker to prefer low cards
- ✅ DDS fallback heuristics improved

**However**, the bug still occurs, suggesting:
1. The fixes work for some cases but not all
2. The evaluation function's bonuses override the discard heuristics
3. The 0.3 tolerance is too small compared to 0.6 communication bonus

### Current Discard Heuristics (Appear Correct)

**DDS AI Heuristic** (`backend/engine/play/ai/dds_ai.py:383-401`):
```python
if not following_suit:
    # DISCARDING - ALWAYS play lowest card available
    # Find weakest suit (fewest high cards)
    weakest_suit = min(by_suit.values(), key=suit_weakness)
    # From weakest suit, play LOWEST card
    return min(weakest_suit, key=lambda c: self._rank_value(c.rank))
```
✅ This logic is **correct** - it should discard lowest from weakest suit.

**Minimax Move Ordering** (`backend/engine/play/ai/minimax_ai.py:416-439`):
```python
if is_discarding:
    # When discarding, LOW cards are best
    priority_score -= RANK_VALUES[card.rank] * 10

    # Strong penalty for discarding honors
    if card.rank == 'K':
        priority_score -= 150  # Examine last
```
✅ This logic is **correct** - Kings get lowest priority when discarding.

**The problem:** These heuristics guide the **search order** and **DDS fallback**, but the **evaluation function** still assigns positive value to keeping Kings, overriding the intent.

---

## Reproduction Steps

1. Start a NoTrump contract
2. Progress to Trick 5
3. Lead a suit where East is void
4. East holds cards including K♣ and low cards (e.g., ♦6, ♦7)
5. **Expected:** East discards lowest card (♦6 or ♦7)
6. **Actual:** East discards K♣

---

## Proposed Fix

### Option 1: Disable Communication Bonus for Non-Playable Suits (RECOMMENDED)

Modify `_communication_component()` to only count Kings as entries if they're in a **playable suit** (not being discarded):

```python
def _communication_component(self, state: PlayState, perspective: str) -> float:
    # ... existing code ...

    # Check if this is a discard situation
    is_discarding_from_suit = {}
    if state.current_trick:
        led_suit = state.current_trick[0][0].suit
        for pos in positions:
            hand = state.hands[pos]
            # If void in led suit, might be discarding
            if pos == state.next_to_play:
                has_led_suit = any(c.suit == led_suit for c in hand.cards)
                if not has_led_suit:
                    # Mark all suits as potential discard targets
                    for suit in ['♠', '♥', '♦', '♣']:
                        is_discarding_from_suit[suit] = True

    for pos in positions:
        for suit, cards in by_suit.items():
            # Skip entry value if we're discarding from this suit
            if is_discarding_from_suit.get(suit, False):
                continue  # Don't count King as entry in discard situation

            # ... existing entry counting logic ...
```

### Option 2: Increase Tolerance in Minimax

Increase the tolerance from 0.3 to 0.8 to overcome the 0.6 communication bonus:

```python
tolerance = 0.8  # Allow 0.8 trick difference (was 0.3)
```

**Downside:** May cause AI to miss subtle differences in play.

### Option 3: Add Discard Penalty to Evaluation (SIMPLEST)

Add explicit penalty for discarding honors when in a discard situation:

```python
def _discard_penalty_component(self, state: PlayState, perspective: str,
                                 card: Card = None) -> float:
    """
    Penalize discarding high cards when void in led suit

    Returns negative score if discarding honors unnecessarily
    """
    if not card or not state.current_trick:
        return 0.0

    led_suit = state.current_trick[0][0].suit

    # Check if this card is a discard (different suit than led)
    if card.suit != led_suit:
        # Penalize discarding honors
        if card.rank == 'A':
            return -2.0
        elif card.rank == 'K':
            return -1.5  # Strong penalty for discarding King
        elif card.rank == 'Q':
            return -1.0
        elif card.rank == 'J':
            return -0.5

    return 0.0
```

---

## Recommended Solution

**Implement Option 3 (Discard Penalty) FIRST** because:
1. ✅ Simplest to implement
2. ✅ Doesn't break existing logic
3. ✅ Directly addresses the symptom
4. ✅ Can be tested immediately

**Then consider Option 1** (context-aware communication) as a more sophisticated long-term fix.

---

## Testing Plan

### Automated Test
```bash
cd backend
python3 test_discard_fix.py
```

Expected: AI discards low card (♣2, ♦6, ♦7), NOT K♣

### Manual Test
1. Play 5-10 NT contracts
2. Watch for discard situations (East/West void in led suit)
3. Verify AI discards lowest from weakest suit
4. Count: High cards discarded = 0/10 (should be zero)

### Specific Scenario Test
Create a test case matching the user's exact scenario:
- NT contract, Trick 5
- East void in led suit
- East holds K♣ plus low diamonds
- Verify: AI discards ♦6 or ♦7, not K♣

---

## Files to Modify

1. **`backend/engine/play/ai/evaluation.py`**
   - Add `_discard_penalty_component()` method
   - Integrate penalty into main `evaluate()` function

2. **`backend/engine/play/ai/minimax_ai.py`**
   - Pass current card to evaluation function (may require signature changes)
   - OR: Apply discard penalty at move selection level

3. **`backend/test_discard_fix.py`**
   - Verify existing test still passes
   - Add new test for Trick 5 scenario

4. **`BUG_TRACKING_SYSTEM.md`**
   - Update status after fix is verified

---

## Next Steps

1. ✅ Mark BUG-H002 as UNRESOLVED ← DONE
2. ✅ Document root cause analysis ← DONE
3. ⏭️ Implement Option 3 (discard penalty)
4. ⏭️ Run automated tests
5. ⏭️ Manual testing with user's scenario
6. ⏭️ Update bug tracking system
7. ⏭️ Consider Option 1 for future refinement

---

## Technical Notes

### Why the Bug Persists Despite Previous Fixes

The previous fixes addressed:
- **Move ordering** ← Helps search efficiency but doesn't change evaluation
- **DDS heuristic** ← Only used when DDS fails/unavailable
- **Tolerance tiebreaker** ← Only works if difference < 0.3 tricks

They did NOT address:
- **Evaluation function bonuses** ← This is the actual problem
- Kings valued at +0.6 for communication in ALL contexts
- No context awareness for discard vs. active play

### Key Insight

The AI's minimax search is working correctly. The problem is that the **position evaluation tells it that keeping the King is worth 0.6 points**, which is a larger difference than the 0.3 tolerance, so the "prefer low cards" tiebreaker never activates.

**Fix:** Tell the evaluation function "Kings have NO value when you're discarding them."

---

**Status:** Ready for implementation
**Estimated Fix Time:** 30-60 minutes
**Testing Time:** 15-30 minutes
**Total:** ~1-2 hours
