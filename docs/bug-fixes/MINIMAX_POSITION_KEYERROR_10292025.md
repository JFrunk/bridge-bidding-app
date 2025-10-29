# Minimax AI Position KeyError Bug Fix

**Date:** 2025-10-29
**Bug Report:** backend/review_requests/hand_2025-10-29_14-26-11.json
**Severity:** Critical - AI play completely broken for certain positions
**Status:** ✅ FIXED

---

## Summary

The minimax AI crashed with `KeyError: 'West'` when trying to make opening lead from West position. This occurred because the minimax AI incorrectly converted position strings from short format ('W') to full names ('West'), but the `PlayState.hands` dictionary uses short keys.

---

## Bug Symptoms

**User-Facing Error:**
```
AI play failed for W: Error with AI play: 'West'
```

**Backend Error:**
```python
KeyError: 'West'
  File "backend/engine/play/ai/minimax_ai.py", line 372, in _simulate_play
  File "backend/engine/play/ai/minimax_ai.py", line 320, in _get_legal_cards
```

**Affected Scenarios:**
- Any contract where West is opening leader
- Minimax AI (levels 7-8) completely non-functional for affected positions
- Bug could potentially affect any of the 4 positions depending on declarer

---

## Root Cause Analysis

### Systematic Debug Protocol (4 Steps)

**1. Identify & Search (2 minutes)**

From error logs:
```python
# minimax_ai.py line 372
position_map = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
full_position = position_map[position]  # Converts 'W' to 'West'
new_state.hands[full_position].cards.remove(card)  # ❌ KeyError: 'West'
```

**Why This Failed:**
- `PlayState.hands` dictionary uses SHORT keys: `{'N': Hand(...), 'E': Hand(...), 'S': Hand(...), 'W': Hand(...)}`
- Minimax AI converted 'W' to 'West', then tried `state.hands['West']` which doesn't exist
- Position mapping was completely unnecessary - positions are ALWAYS short format throughout the codebase

**Search for Similar Patterns:**
```bash
grep -r "position_map.*North.*South.*East.*West" backend/engine/play/ai/
```

**Results:**
- `minimax_ai.py` line 307-310 (in `_simulate_play`)
- `minimax_ai.py` line 359-360 (in `_get_legal_cards`)
- `evaluation.py` line 47-49 (in `__init__` and `_get_hand`)

**2. Document Scope (1 minute)**

- **Immediate issue:** West position cannot make opening lead
- **Pattern found in:** 3 locations across 2 files
- **Actually affected:** All 3 locations - minimax AI completely broken
- **Preventatively fix:** Removed position mapping entirely

**3. Solution Design (1 minute)**

Since this pattern appeared in 3 locations with the SAME incorrect assumption, the solution was to:
1. Remove position mapping entirely
2. Use position strings directly (they're already in short format)
3. Add regression test to prevent recurrence

**4. User Validation**

User requested verification that DDS service wouldn't break. After reviewing `dds_ai.py`, confirmed:
- DDS also uses SHORT keys ('N', 'E', 'S', 'W')
- DDS converts to endplay format in `_convert_position()` method
- No compatibility issues with fixing minimax AI

---

## The Fix

### Files Modified

1. **backend/engine/play/ai/minimax_ai.py** (3 locations)
2. **backend/engine/play/ai/evaluation.py** (2 locations)

### Changes in minimax_ai.py

**Location 1: _simulate_play method (line 307-310)**

```python
# BEFORE (BROKEN):
position_map = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
short_position = position  # Already short!
full_position = position_map[short_position]  # Converts 'W' to 'West'

new_state.current_trick.append((card, short_position))
new_state.hands[full_position].cards.remove(card)  # ❌ KeyError: 'West'

# AFTER (FIXED):
# Position is already in correct format (N/S/E/W for both trick and hands dict)
new_state.current_trick.append((card, position))
new_state.hands[position].cards.remove(card)  # ✅ Works with 'W'
```

**Location 2: _simulate_play method (line 340)**

```python
# BEFORE (BROKEN):
new_state.next_to_play = PlayEngine.next_player(short_position)

# AFTER (FIXED):
# Position is already in short format (N/S/E/W)
new_state.next_to_play = PlayEngine.next_player(position)
```

**Location 3: _get_legal_cards method (line 359-360)**

```python
# BEFORE (BROKEN):
position_map = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
full_position = position_map.get(position, position)
hand = state.hands[full_position]  # ❌ KeyError: 'West'

# AFTER (FIXED):
# Position is already in correct format (N/S/E/W)
hand = state.hands[position]  # ✅ Works correctly
```

### Changes in evaluation.py

**Location 1: __init__ method (line 47)**

```python
# BEFORE (BROKEN):
self.position_map = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}

# AFTER (FIXED):
# Removed - position mapping not needed
```

**Location 2: _get_hand method (line 47-49)**

```python
# BEFORE (BROKEN):
def _get_hand(self, state: PlayState, position: str):
    full_position = self.position_map.get(position, position)
    return state.hands[full_position]  # ❌ KeyError

# AFTER (FIXED):
def _get_hand(self, state: PlayState, position: str):
    """Get hand for position (always short form: N/S/E/W)"""
    return state.hands[position]  # ✅ Works correctly
```

---

## Regression Test

**File:** `backend/tests/regression/test_minimax_position_keyerror_10292025.py`

**Test Coverage:**

1. **test_minimax_ai_handles_all_positions()**
   - Tests all 4 positions as opening leader
   - Verifies minimax AI can select a card without KeyError
   - Confirms selected card is from correct player's hand

2. **test_minimax_ai_with_real_bug_scenario()**
   - Reproduces exact bug scenario from report
   - Contract: 5♦ by South
   - Opening leader: West
   - Verifies no KeyError when West plays

**Test Results:**
```
✅ Minimax AI successfully played from E (declarer=N): 2♥
✅ Minimax AI successfully played from S (declarer=E): 2♦
✅ Minimax AI successfully played from W (declarer=S): 2♣
✅ Minimax AI successfully played from N (declarer=W): 2♠
✅ Minimax AI opening lead from West: J♦
   Contract: 5♦ by South
   Bug FIXED: No KeyError on position 'W'
✅ ALL TESTS PASSED - Minimax AI position bug is FIXED
```

---

## Verification with DDS Compatibility

**User Concern:** "Please review the DDS code as I recall that it requires full names and not single letters."

**DDS Review Results:**

Reviewed `backend/engine/play/ai/dds_ai.py`:

1. **DDS uses SHORT keys** throughout:
   - Line 95, 153, 275, 298: `state.hands[position]` with SHORT keys
   - Line 152: Iterates with `for pos in ['N', 'E', 'S', 'W']`

2. **DDS conversion happens in dedicated method:**
```python
def _convert_position(self, position: str) -> EndplayPlayer:
    """Convert position string to endplay Player"""
    mapping = {'N': EndplayPlayer.north, 'E': EndplayPlayer.east,
              'S': EndplayPlayer.south, 'W': EndplayPlayer.west}
    return mapping[position]
```

3. **Conclusion:** DDS is compatible with fix - no issues detected

---

## Impact Assessment

### Before Fix
- ❌ Minimax AI completely broken for West opening leads
- ❌ KeyError crashes entire play session
- ❌ User sees cryptic error message
- ❌ No fallback - game unplayable

### After Fix
- ✅ Minimax AI works for all 4 positions
- ✅ No KeyError crashes
- ✅ All play sessions complete successfully
- ✅ Regression test prevents recurrence

---

## Key Learnings

### 1. Position Format Consistency

**Standard:** ALL position references in the codebase use SHORT format ('N', 'E', 'S', 'W')

**Why:**
- PlayState.hands uses short keys
- PlayEngine.next_player expects short format
- Contract.declarer uses short format
- Trick tuples use short format: `(card, position)`

**Exception:** Endplay library requires its own enum type, but conversion happens in dedicated `_convert_position()` method

### 2. Unnecessary Abstraction

The position mapping was:
- Not needed (positions already in correct format)
- Inconsistent (only in minimax AI, not other AIs)
- Error-prone (introduced bugs)

**Better Approach:** Use positions as-is, add docstring to clarify format

### 3. Systematic Debug Protocol Works

Following the 4-step protocol:
1. Prevented incomplete fixes (found all 3 occurrences)
2. Identified architectural issue (position format consistency)
3. Enabled preventative fixes (removed pattern entirely)
4. Caught compatibility concerns (DDS review)

---

## Testing Checklist

- [x] Regression test passes (all 4 positions)
- [x] Real bug scenario test passes (West opening lead)
- [x] Backend server restarted with fix
- [x] DDS compatibility verified
- [x] No new errors in logs
- [x] Documentation complete

---

## Related Files

- **Bug Report:** backend/review_requests/hand_2025-10-29_14-26-11.json
- **Regression Test:** backend/tests/regression/test_minimax_position_keyerror_10292025.py
- **Fixed Files:**
  - backend/engine/play/ai/minimax_ai.py
  - backend/engine/play/ai/evaluation.py
- **Verification:**
  - backend/engine/play/ai/dds_ai.py (reviewed, no changes needed)

---

## Prevention

**To Prevent Similar Bugs:**

1. **Use consistent position format** - Always use short keys ('N', 'E', 'S', 'W')
2. **Avoid unnecessary mapping** - Don't convert unless required by external library
3. **Add position format docstrings** - Make format explicit in method signatures
4. **Systematic search** - When fixing position bugs, search entire codebase for similar patterns

**Code Review Checklist:**
- [ ] Position format matches PlayState.hands keys
- [ ] No unnecessary position mapping
- [ ] Position format documented in docstrings
- [ ] Regression test added for position-related logic
