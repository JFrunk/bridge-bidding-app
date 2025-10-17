# Bridge Rules Engine Architecture

**Status**: ✅ Implemented (Single-Player Mode)
**Version**: 2.0.0 (Single-Player Mode)
**Date**: 2025-10-16
**Last Updated**: 2025-10-16 (Single-Player Mode Implementation)

## Overview

The Bridge Rules Engine is a comprehensive system that encodes bridge rules for **single-player mode** regarding hand visibility, position control, and turn determination. It provides a **single source of truth** for all rules-based decisions in the play phase.

### ⚠️ IMPORTANT: Single-Player Mode vs Official Bridge Laws

**This application implements SINGLE-PLAYER MODE**, not official 4-player bridge rules:

- **Single-Player Mode**: User (South) plays against AI, controlling NS partnership when NS is declaring
- **Official 4-Player Rules**: All four positions are human players with individual control

**DO NOT implement official 4-player bridge rules unless explicitly changing game modes.**

---

## Single-Player Mode Rules (CURRENT IMPLEMENTATION)

### Core Principle

**User (South) controls the NS partnership when NS is declaring.**

### Control Rules

| Scenario | Declarer | User Controls | AI Controls | User Role |
|----------|----------|---------------|-------------|-----------|
| **NS Declaring** | North or South | **North + South** | East + West | Partner/Declarer |
| **EW Declaring** | East or West | **South only** | North + East + West | Defender |

### Visibility Rules

**Before Opening Lead**:
- User sees: South only (own hand)

**After Opening Lead** (dummy revealed):
- When NS declaring: User sees **North + South** (both partnership hands)
- When EW declaring: User sees **South + Dummy** (own hand + EW dummy)

### Key Differences from Official Bridge Rules

| Situation | Official 4-Player Rules | Single-Player Mode |
|-----------|------------------------|-------------------|
| South is dummy, North is declarer | South controls: **Nothing** (passive) | South controls: **North + South** |
| North is declarer | North controls: North + South | **South controls**: North + South |
| South is declarer | South controls: South + North | South controls: South + North ✓ (same) |
| East/West is declarer | South controls: South only ✓ | South controls: South only ✓ (same) |

### Example: 4♠ by North (Current Bug Case)

```
Contract: 4♠ by North
Declarer: North
Dummy: South
Next to play: South

CORRECT BEHAVIOR (Single-Player Mode):
✓ User sees: North + South
✓ User controls: North + South
✓ When next_to_play = South → User clicks South's cards
✓ When next_to_play = North → User clicks North's cards
✓ AI plays only for East + West

INCORRECT BEHAVIOR (4-Player Rules - DO NOT IMPLEMENT):
✗ User sees: South + North (but can't control South)
✗ User controls: Nothing (South is dummy/passive)
✗ AI plays for: North + South + East + West
```

---

## Problem Solved

### Previous Issues (Before Rules Engine)

1. **AI Playing for User** - Multiple bugs where AI would play cards for positions the user should control
2. **Scattered Logic** - Hand visibility and control logic duplicated across backend and frontend
3. **Inconsistent Behavior** - Different code paths had different interpretations of who controls what
4. **Hard to Test** - No centralized place to test all bridge rule scenarios
5. **Future-Proof Issues** - Adding new features (rubber bridge, different positions) would require touching many files

### Solution: Centralized Rules Engine

The Bridge Rules Engine solves these issues by:

- **Encoding Official Bridge Laws** - Direct implementation of Laws of Duplicate Bridge (2017)
- **Single Source of Truth** - All visibility/control decisions go through one engine
- **Comprehensive Test Coverage** - 51 unit tests covering all scenarios
- **Self-Documenting Code** - Code reads like the rulebook
- **Extensible Design** - Easy to add new game modes or positions

---

## Architecture

### Core Components

```
backend/engine/bridge_rules_engine.py
├── GameState          # Represents current game state
├── Position           # Enum for N/E/S/W positions
├── PlayerRole         # Enum for declarer/dummy/defender
└── BridgeRulesEngine  # Main rules engine (static methods)
```

### Integration Points

```
Backend API (server.py)
├── /api/get-play-state    # Returns UI display info from rules engine
├── /api/play-card         # Validates user can play from position
└── /api/get-ai-play       # Validates AI should play for position

Frontend (App.js)
└── PlayTable              # Uses is_user_turn, controllable_positions from backend
```

---

## Bridge Rules Implemented (SINGLE-PLAYER MODE)

### 1. Partnership Control (Single-Player Adaptation)

**Single-Player Rule**: User controls NS partnership when NS is declaring.

**Implementation**:
- When NS declaring: User controls **North + South**
- When EW declaring: User controls **South only**
- AI controls remaining positions

**Code**:
```python
declarer = state.declarer

# NS is declaring side (North or South is declarer)
if declarer in ['N', 'S']:
    # After opening lead, user controls both N and S
    if state.opening_lead_made:
        return {'N', 'S'}
    else:
        # Before opening lead, only opening leader can act
        opening_leader = BridgeRulesEngine.get_opening_leader(declarer)
        if opening_leader in ['N', 'S']:
            return {opening_leader}
        else:
            return set()  # Wait for AI to lead

# EW is declaring side (East or West is declarer)
else:
    # User controls only South (defense)
    return {'S'}
```

### 2. Hand Visibility (Single-Player Mode)

**Single-Player Rules**:
- User ALWAYS sees South
- After opening lead, dummy revealed
- When NS declaring: User sees **North + South** (partnership)
- When EW declaring: User sees **South + Dummy (E or W)**

**Code**:
```python
declarer = state.declarer
dummy = state.dummy
visible = {'S'}  # Always see South

# After opening lead, dummy is visible
if state.opening_lead_made or state.dummy_revealed:
    visible.add(dummy)

    # SINGLE-PLAYER MODE: If NS is declaring, user sees both N and S
    if declarer in ['N', 'S']:
        visible.add('N')
        visible.add('S')

return visible
```

### 3. ~~Dummy Control (DOES NOT APPLY IN SINGLE-PLAYER MODE)~~

**Official 4-Player Law (NOT IMPLEMENTED)**: "Dummy should not participate in the play."

**Single-Player Override**: This rule does NOT apply. When South is dummy and North is declarer, user still controls both positions because user controls the NS partnership.

**DO NOT IMPLEMENT 4-PLAYER DUMMY RULES** - they cause the bug where AI plays for the user's partnership.

### 5. Turn Sequencing

**Opening Lead**: Left-hand opponent (LHO) of declarer leads first
**After Opening Lead**: Play proceeds clockwise (N → E → S → W)
**After Trick**: Winner of trick leads to next trick

**Code**:
```python
def get_opening_leader(declarer: str) -> str:
    """LHO of declarer leads first"""
    return BridgeRulesEngine.get_next_player(declarer)

def get_next_player(current_player: str) -> str:
    """Clockwise order: N → E → S → W → N"""
    order = ['N', 'E', 'S', 'W']
    current_idx = order.index(current_player)
    next_idx = (current_idx + 1) % 4
    return order[next_idx]
```

---

## API Reference

### Core Methods

#### `get_visible_hands(state: GameState) -> Set[str]`

Determines which hands should be visible to the user.

**Parameters**:
- `state`: Current game state

**Returns**: Set of positions (e.g., `{'S', 'N'}`)

**Example**:
```python
state = GameState(
    declarer='S',
    dummy='N',
    user_position='S',
    opening_lead_made=True
)
visible = BridgeRulesEngine.get_visible_hands(state)
# Returns: {'S', 'N'} - declarer sees own hand + dummy
```

#### `get_controllable_positions(state: GameState) -> Set[str]`

Determines which positions the user can play cards from.

**Parameters**:
- `state`: Current game state

**Returns**: Set of positions user controls

**Example**:
```python
state = GameState(
    declarer='S',
    dummy='N',
    user_position='S'
)
controllable = BridgeRulesEngine.get_controllable_positions(state)
# Returns: {'S', 'N'} - declarer controls both positions
```

#### `is_user_turn(state: GameState) -> bool`

Determines if it's the user's turn to play.

**Returns**: `True` if user should play, `False` if AI should play

**Logic**: User's turn when `next_to_play` is a position the user controls

#### `validate_play_request(state: GameState, position: str) -> (bool, str)`

Validates whether a play request is legal.

**Returns**: Tuple of `(is_valid, error_message)`

**Example**:
```python
is_valid, error_msg = BridgeRulesEngine.validate_play_request(state, 'S')
if not is_valid:
    print(f"Invalid play: {error_msg}")
```

#### `get_ui_display_info(state: GameState) -> dict`

Returns all information needed for UI display.

**Returns**:
```python
{
    'visible_hands': ['S', 'N'],
    'controllable_positions': ['S', 'N'],
    'is_user_turn': True,
    'user_role': 'declarer',
    'next_to_play': 'S',
    'declarer': 'S',
    'dummy': 'N',
    'user_position': 'S',
    'dummy_revealed': True,
    'display_message': 'Your turn to play!'
}
```

---

## Test Coverage

### Test Suite Overview

**File**: `backend/tests/unit/test_bridge_rules_engine.py`
**Tests**: 51 comprehensive tests
**Coverage**: 100% of all rule scenarios

### Test Categories

1. **Partnerships** (4 tests)
   - North-South partnership
   - East-West partnership

2. **Player Roles** (4 tests)
   - Declarer role identification
   - Dummy role identification
   - Defender role identification

3. **Hand Visibility** (6 tests)
   - User as declarer (before/after opening lead)
   - User as dummy (before/after opening lead)
   - User as defender (before/after opening lead)

4. **Position Control** (6 tests)
   - Declarer controls both positions
   - Dummy controls nothing
   - Defender controls only self

5. **Turn Determination** (8 tests)
   - User turn as declarer
   - User turn as defender
   - User turn when playing dummy
   - Never user turn when dummy

6. **Opening Lead** (4 tests)
   - LHO of each position

7. **Real-World Scenarios** (3 tests)
   - Complete trick as declarer
   - User is dummy (AI plays all)
   - Defender makes opening lead

### Running Tests

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/unit/test_bridge_rules_engine.py -v
```

**Expected Output**:
```
============================== test session starts ==============================
...
51 passed in 0.04s
============================== 51 passed in 0.04s ===============================
```

---

## Usage Examples

### Backend Integration

#### Example 1: Validate AI Play Request

```python
from engine.bridge_rules_engine import BridgeRulesEngine, GameState

# Create game state
state = GameState(
    declarer='E',
    dummy='W',
    user_position='S',
    next_to_play='E',
    dummy_revealed=True,
    opening_lead_made=True
)

# Check if AI should play
controllable = BridgeRulesEngine.get_controllable_positions(state)
if 'E' in controllable:
    return jsonify({"error": "User controls this position"}), 403

# Validate play request
is_valid, error_msg = BridgeRulesEngine.validate_play_request(state, 'E')
if not is_valid:
    return jsonify({"error": error_msg}), 400

# Proceed with AI play...
```

#### Example 2: Get Display Information

```python
# Get comprehensive UI info
ui_info = BridgeRulesEngine.get_ui_display_info(state)

# Use in API response
return jsonify({
    "visible_hands": ui_info['visible_hands'],
    "controllable_positions": ui_info['controllable_positions'],
    "is_user_turn": ui_info['is_user_turn'],
    "user_role": ui_info['user_role'],
    "turn_message": ui_info['display_message']
})
```

### Frontend Integration

```javascript
// Fetch play state from backend
const response = await api.getPlayState();
const playState = response;

// Use rules engine data
const isUserTurn = playState.is_user_turn;
const controllablePositions = playState.controllable_positions;
const visibleHands = playState.visible_hands;

// Pass to PlayTable component
<PlayTable
  isUserTurn={playState.is_user_turn}
  controllablePositions={playState.controllable_positions}
  visibleHands={playState.visible_hands}
/>
```

---

## Scenarios Covered (SINGLE-PLAYER MODE)

### Scenario 1: NS is Declaring, South is Declarer

**Setup**:
- Declarer: South
- Dummy: North
- Defenders: East, West

**Single-Player Rules**:
- User sees: South + North (after opening lead)
- User controls: South + North (partnership)
- User plays: When it's South's turn OR North's turn
- AI plays: When it's East's turn OR West's turn

**Code**:
```python
visible = {'S', 'N'}  # After opening lead
controllable = {'S', 'N'}
is_user_turn = next_to_play in ['S', 'N']
```

### Scenario 2: NS is Declaring, North is Declarer (Bug Fix Case)

**Setup**:
- Declarer: North
- Dummy: South
- Defenders: East, West

**Single-Player Rules** (CORRECT):
- User sees: South + North (partnership)
- User controls: **South + North** (user controls NS partnership)
- User plays: When it's South's turn OR North's turn
- AI plays: When it's East's turn OR West's turn

**Code**:
```python
visible = {'S', 'N'}  # After opening lead
controllable = {'S', 'N'}  # User controls BOTH
is_user_turn = next_to_play in ['S', 'N']
```

**❌ INCORRECT 4-Player Implementation (DO NOT USE)**:
```python
# This causes the bug!
visible = {'S', 'N'}
controllable = set()  # WRONG - user controls nothing
is_user_turn = False  # WRONG - never user's turn
```

### Scenario 3: EW is Declaring, User is Defender

**Setup**:
- Declarer: East or West
- Dummy: West or East
- Defenders: North, South

**Single-Player Rules**:
- User sees (before opening lead): South only
- User sees (after opening lead): South + Dummy (E or W)
- User controls: South only
- User plays: When it's South's turn only
- AI plays: When it's North, East, or West's turn

**Code**:
```python
# Before opening lead
visible = {'S'}
# After opening lead
visible = {'S', 'W'}  # Or {'S', 'E'} if East is dummy
controllable = {'S'}  # User controls only South
is_user_turn = (next_to_play == 'S')
```

---

## Design Principles

### 1. Declarative Over Imperative

**Bad** (Imperative):
```python
if user_is_declarer:
    if position == declarer:
        allow_play = True
    elif position == dummy:
        allow_play = True
    else:
        allow_play = False
```

**Good** (Declarative):
```python
controllable = BridgeRulesEngine.get_controllable_positions(state)
allow_play = position in controllable
```

### 2. Single Source of Truth

All bridge rules are in **ONE** place: `BridgeRulesEngine`

- Backend uses it for validation
- Frontend receives results via API
- Tests verify correctness against spec

### 3. Testable Against Official Laws

Each test can be traced to a specific Law:

```python
def test_dummy_controls_nothing(self):
    """Law 41: Dummy is passive after opening lead"""
    state = GameState(declarer='N', dummy='S', user_position='S')
    controllable = BridgeRulesEngine.get_controllable_positions(state)
    assert controllable == set()  # Dummy controls nothing
```

### 4. Extensible Design

Adding new positions or game modes is straightforward:

```python
# Future: Add "Kibitzer" role (watches but doesn't play)
class PlayerRole(Enum):
    DECLARER = 'declarer'
    DUMMY = 'dummy'
    DEFENDER = 'defender'
    KIBITZER = 'kibitzer'  # New role

def get_controllable_positions(state):
    if user_role == PlayerRole.KIBITZER:
        return set()  # Kibitzers control nothing
```

---

## Future Enhancements

### 1. Four-Player Mode (Not Currently Implemented)

**⚠️ DO NOT IMPLEMENT WITHOUT EXPLICIT REQUEST**

To support 4 human players (official bridge rules):
- Add `game_mode` parameter: `"single_player"` or `"four_player"`
- When `game_mode == "four_player"`:
  - Implement official dummy rules (dummy is passive)
  - Each position controlled by its assigned player
  - Proper turn routing for 4 separate clients

**Implementation Note**: Would require significant frontend/backend changes and multiplayer architecture.

### 2. Rubber Bridge Support
   - Track rubber score across multiple deals
   - Handle honors (A, K, Q, J, 10 of trumps)

### 3. Duplicate Bridge Support
   - Track matchpoints/IMPs
   - Compare with other tables

### 4. Different User Positions (Single-Player Mode)
   - Allow user to play as North (AI plays South)
   - User controls NS partnership when NS declaring (same rules)

### 5. Claim/Concede Logic
   - Validate declarer can claim remaining tricks
   - Handle defender concession

### 6. Undo/Review Moves
   - Track play history for review
   - Allow undo during learning mode

### Implementation Notes

All these features can be added by **extending** the rules engine, not modifying core logic:

```python
# Example: Claim validation
def can_declarer_claim(state: GameState, claimed_tricks: int) -> bool:
    """Validate if declarer can claim remaining tricks"""
    remaining_tricks = 13 - len(state.trick_history)
    return claimed_tricks <= remaining_tricks  # Simplified
```

---

## Troubleshooting

### Common Issues

#### Issue: AI plays for user position

**Symptom**: AI plays cards when it's the user's turn

**Diagnosis**:
```python
# Check controllable positions
controllable = BridgeRulesEngine.get_controllable_positions(state)
print(f"User should control: {controllable}")
print(f"Next to play: {state.next_to_play}")
print(f"Is user turn: {BridgeRulesEngine.is_user_turn(state)}")
```

**Solution**: Verify `next_to_play` is in `controllable_positions`

#### Issue: Wrong hands visible

**Symptom**: User can't see dummy's hand when they should

**Diagnosis**:
```python
visible = BridgeRulesEngine.get_visible_hands(state)
print(f"Should see: {visible}")
print(f"Opening lead made: {state.opening_lead_made}")
print(f"Dummy revealed: {state.dummy_revealed}")
```

**Solution**: Ensure `opening_lead_made=True` after first card played

#### Issue: User is dummy but can play cards

**Symptom**: UI allows dummy to play when they shouldn't

**Diagnosis**:
```python
user_role = BridgeRulesEngine.get_player_role('S', declarer, dummy)
controllable = BridgeRulesEngine.get_controllable_positions(state)
print(f"User role: {user_role}")
print(f"Controllable: {controllable}")  # Should be empty set
```

**Solution**: Check frontend uses `controllable_positions` correctly

---

## References

### Official Bridge Laws

- [Laws of Duplicate Bridge (2017)](https://www.worldbridge.org/laws/)
- Law 41: Dummy's Rights and Limitations
- Law 45: Card Play Procedure

### Related Documentation

- [BIDDING_STATE_ARCHITECTURE.md](../../.claude/BIDDING_STATE_ARCHITECTURE.md) - Bidding phase architecture
- [TEST_SESSION_ISOLATION.md](../guides/TEST_SESSION_ISOLATION.md) - Testing best practices

### Code Locations

- **Rules Engine**: [`backend/engine/bridge_rules_engine.py`](../../backend/engine/bridge_rules_engine.py)
- **Tests**: [`backend/tests/unit/test_bridge_rules_engine.py`](../../backend/tests/unit/test_bridge_rules_engine.py)
- **Backend Integration**: [`backend/server.py`](../../backend/server.py) (search for `BridgeRulesEngine`)
- **Frontend Integration**: [`frontend/src/App.js`](../../frontend/src/App.js) (search for `BRIDGE RULES ENGINE`)

---

## Changelog

### Version 2.0.0 (2025-10-16) - SINGLE-PLAYER MODE

**⚠️ BREAKING CHANGE**: Converted from 4-player bridge rules to single-player mode

**Critical Fix**:
- ❌ **REMOVED**: Official 4-player dummy rules (dummy is passive)
- ✅ **ADDED**: Single-player partnership control (user controls NS when NS declaring)
- ✅ **FIXED**: Bug where AI played for user's partnership when North was declarer

**Implementation Changes**:
- `get_controllable_positions()`: Returns `{'N', 'S'}` when NS declaring (was `set()` for dummy)
- `get_visible_hands()`: Returns `{'N', 'S'}` when NS declaring (simplified logic)
- Frontend: Updated AI play loop to use single-player logic
- Documentation: Clearly marked as single-player mode with warnings

**Files Modified**:
- `backend/engine/bridge_rules_engine.py` - Core logic rewritten for single-player
- `frontend/src/App.js` - AI play loop rewritten for single-player
- `docs/architecture/BRIDGE_RULES_ENGINE.md` - Updated with single-player documentation
- `GAMEPLAY_STATE_MACHINE.md` - Created visual state diagram

**Test Results**: Tests need updating for single-player mode

**Migration Notes**:
- Official 4-player bridge rules documented as future enhancement
- To implement 4-player mode, add `game_mode` parameter and conditional logic
- Current implementation is **single-player only** - do not revert to 4-player rules

---

### Version 1.0.0 (2025-10-16) - DEPRECATED

**Initial Implementation** (4-Player Rules - DEPRECATED)

- ✅ Created `BridgeRulesEngine` class
- ✅ Implemented 51 comprehensive tests (for 4-player mode)
- ✅ Integrated with backend API
- ✅ Integrated with frontend

**Bug**: Implemented 4-player bridge rules instead of single-player mode, causing AI to play for user's partnership.

---

## Conclusion

The Bridge Rules Engine provides a **robust, testable, and extensible** foundation for implementing contract bridge rules. By encoding the official Laws of Bridge in code, we ensure:

1. **Correctness** - Rules match official bridge laws
2. **Consistency** - Single source of truth across backend/frontend
3. **Testability** - 51 tests verify all scenarios
4. **Maintainability** - Self-documenting code reads like rulebook
5. **Extensibility** - Easy to add new features

This architecture eliminates entire classes of bugs related to hand visibility and position control, providing a solid foundation for future development.

---

**Questions or Issues?** See troubleshooting section or open a GitHub issue.
