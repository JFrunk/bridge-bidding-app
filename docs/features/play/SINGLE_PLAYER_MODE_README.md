# ⚠️ CRITICAL: SINGLE-PLAYER MODE IMPLEMENTATION

**Date**: 2025-10-16
**Status**: ✅ Active Implementation

---

## THIS APPLICATION IS SINGLE-PLAYER MODE

### ❌ DO NOT Implement Official 4-Player Bridge Rules

This application implements **SINGLE-PLAYER MODE** where:
- **User (South)** plays against **AI (East/West)**
- **User controls NS partnership** when NS is declaring
- **AI controls EW partnership** always

### Why This Matters

Official bridge rules state:
> "Dummy is passive and makes no decisions"

But in **single-player mode**, this rule **DOES NOT APPLY**.

**Example Bug** (DO NOT REVERT):
```
Scenario: 4♠ by North (North is declarer, South is dummy)

Before opening lead:
- User sees: South only (their own hand / dummy)
- North's hand: Hidden (declarer not yet revealed)

After opening lead by East:
- What is revealed: NORTH (declarer's hand)
- Already visible: SOUTH (user's own hand / dummy)
- User now sees: North + South

❌ WRONG (4-Player Rules):
- User controls: Nothing (South is passive dummy)
- AI plays for: North + South + East + West
- Result: AI plays all hands, user watches

✅ CORRECT (Single-Player Mode):
- User controls: North + South (NS partnership)
- User sees: North + South (declarer + dummy)
- AI plays for: East + West only
- Result: User plays for NS partnership, AI plays for EW
```

---

## Quick Reference

### User Controls

| Declarer | User Controls | AI Controls |
|----------|---------------|-------------|
| **North or South** | North + South | East + West |
| **East or West** | South only | North + East + West |

### User Visibility (After Opening Lead)

| Declarer | Dummy | User Sees | What Gets Revealed |
|----------|-------|-----------|-------------------|
| **North** | South | North + South | **North** (declarer's hand) |
| **South** | North | South + North | **North** (dummy's hand) |
| **East** | West | South + West | **West** (dummy's hand) |
| **West** | East | South + East | **East** (dummy's hand) |

**Key Point**: User always sees South (their own hand). After opening lead, the **other hand** in NS partnership or EW dummy becomes visible.

---

## Code References

### Primary Documentation
- **[BRIDGE_RULES_ENGINE.md](docs/architecture/BRIDGE_RULES_ENGINE.md)** - Single source of truth
- **[GAMEPLAY_STATE_MACHINE.md](GAMEPLAY_STATE_MACHINE.md)** - Visual state diagrams

### Implementation Files
- **Backend**: `backend/engine/bridge_rules_engine.py`
- **Frontend**: `frontend/src/App.js` (search for "SINGLE-PLAYER MODE")

### Key Functions

#### Backend: `get_controllable_positions()`
```python
# NS is declaring side (North or South is declarer)
if declarer in ['N', 'S']:
    if state.opening_lead_made:
        return {'N', 'S'}  # User controls both
```

#### Frontend: AI Play Loop
```javascript
const nsIsDeclaring = (declarerPos === 'N' || declarerPos === 'S');

if (nsIsDeclaring) {
  // User controls BOTH North and South
  if (nextPlayer === 'S' || nextPlayer === 'N') {
    userShouldControl = true;
  }
}
```

---

## If You See AI Playing for User's Partnership

### Symptoms
1. North is declarer, South is dummy
2. AI plays cards from both North AND South
3. User has no control during play
4. Message: "AI is playing all hands and then stops"

### Root Cause
Code was reverted to 4-player bridge rules where dummy is passive.

### Solution
1. Check `backend/engine/bridge_rules_engine.py`
2. Verify `get_controllable_positions()` returns `{'N', 'S'}` when NS declaring
3. Check `frontend/src/App.js` AI play loop
4. Verify it checks `declarerPos in ['N', 'S']` not user role

---

## Future: Four-Player Mode

If implementing 4-player mode in the future:

1. **Add game mode parameter**:
   ```python
   game_mode: str = "single_player"  # or "four_player"
   ```

2. **Conditional logic**:
   ```python
   if game_mode == "single_player":
       # Current implementation
       if declarer in ['N', 'S']:
           return {'N', 'S'}
   elif game_mode == "four_player":
       # Official bridge rules
       if user_role == PlayerRole.DUMMY:
           return set()
   ```

3. **Do NOT replace single-player mode** - add it as a separate mode.

---

## Testing Single-Player Mode

### Manual Test

1. Play until North or South is declarer
2. Verify you can click cards from BOTH North and South
3. Verify AI only plays for East and West
4. Check visibility: You should see both North and South hands

### Expected Console Logs

```
🎮 Play State: { next_to_play: 'S', declarer: 'N', dummy: 'S' }
🤔 Turn check: { nextPlayer: 'S', nsIsDeclaring: true }
⏸️ STOPPING - User controls this play: { nextPlayer: 'S' }
```

When AI plays:
```
▶️ AI playing for position E
▶️ AI playing for position W
```

---

## Related Issues

- **hand_2025-10-16_15-46-29.json**: AI playing for dummy when North is declarer
- **hand_2025-10-16_20-31-53.json**: Declarer's cards not showing, AI playing all hands

Both resolved by implementing single-player mode.

---

## Summary

**DO NOT**:
- ❌ Implement official 4-player dummy rules
- ❌ Make dummy position passive
- ❌ Reference official bridge laws without considering single-player mode

**DO**:
- ✅ Use `declarer in ['N', 'S']` to determine user control
- ✅ User controls NS partnership when NS declaring
- ✅ Reference BRIDGE_RULES_ENGINE.md as source of truth
- ✅ Check GAMEPLAY_STATE_MACHINE.md for visual diagrams

---

**Questions?** See:
- [BRIDGE_RULES_ENGINE.md](docs/architecture/BRIDGE_RULES_ENGINE.md)
- [GAMEPLAY_STATE_MACHINE.md](GAMEPLAY_STATE_MACHINE.md)
