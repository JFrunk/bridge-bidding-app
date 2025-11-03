# Bridge Gameplay State Machine (Single-Player Mode)

## Overview
In single-player mode, the human user (South) plays against AI. The NS partnership behavior depends on who is declarer.

## Core Rules

### Control Rules
1. **User (South) ALWAYS controls**: South's hand
2. **User controls North ONLY when**: North or South is declarer (NS is declaring side)
3. **AI ALWAYS controls**: East + West
4. **AI controls North ONLY when**: East or West is declarer (EW is declaring side)

### Visibility Rules
1. **User ALWAYS sees**: South's hand
2. **Dummy revealed ONLY AFTER**: Opening lead (first card played)
3. **User sees North when**: North or South is declarer (after opening lead)
4. **User sees dummy (E/W) when**: East or West is declarer (after opening lead)

---

## State Diagrams

### Scenario 1: North is Declarer (Current Bug Case)
```
Contract: 4♠ by North
Declarer: North
Dummy: South (user's hand - already visible)

BEFORE Opening Lead:
┌─────────────────────────────────────────────────────┐
│ Opening Leader: East (LHO of declarer)              │
│ User Controls: Nothing yet (waiting for lead)       │
│ User Sees: South only (dummy - own hand)            │
│ AI Controls: East (makes opening lead)              │
│ North's hand: Hidden (declarer not yet revealed)    │
└─────────────────────────────────────────────────────┘
                      ↓ East plays opening lead
┌─────────────────────────────────────────────────────┐
│ AFTER Opening Lead (North/Declarer Revealed):       │
│ User Controls: North + South                         │
│ User Sees: North + South (both visible)             │
│ AI Controls: East + West                             │
│                                                      │
│ What was revealed: NORTH (declarer's hand)          │
│ Already visible: SOUTH (dummy/user's own hand)      │
│                                                      │
│ Play Sequence:                                       │
│ East (AI) → South (USER) → West (AI) → North (USER) │
│                                                      │
│ ✓ User clicks South's cards when it's South's turn  │
│ ✓ User clicks North's cards when it's North's turn  │
└─────────────────────────────────────────────────────┘
```

### Scenario 2: South is Declarer
```
Contract: 4♠ by South
Declarer: South
Dummy: North

BEFORE Opening Lead:
┌─────────────────────────────────────────────────────┐
│ Opening Leader: West (LHO of declarer)              │
│ User Controls: Nothing yet (waiting for lead)       │
│ User Sees: South only                               │
│ AI Controls: West (makes opening lead)              │
└─────────────────────────────────────────────────────┘
                      ↓ West plays opening lead
┌─────────────────────────────────────────────────────┐
│ AFTER Opening Lead (Dummy Revealed):                 │
│ User Controls: South + North                         │
│ User Sees: South + North (both visible)             │
│ AI Controls: East + West                             │
│                                                      │
│ Play Sequence:                                       │
│ West (AI) → North (USER) → East (AI) → South (USER) │
│                                                      │
│ ✓ User clicks North's cards when it's North's turn  │
│ ✓ User clicks South's cards when it's South's turn  │
└─────────────────────────────────────────────────────┘
```

### Scenario 3: East is Declarer
```
Contract: 4♠ by East
Declarer: East
Dummy: West

BEFORE Opening Lead:
┌─────────────────────────────────────────────────────┐
│ Opening Leader: South (LHO of declarer)             │
│ User Controls: South (makes opening lead)            │
│ User Sees: South only                               │
│ AI Controls: Nothing yet (waiting for user lead)    │
└─────────────────────────────────────────────────────┘
                      ↓ South plays opening lead
┌─────────────────────────────────────────────────────┐
│ AFTER Opening Lead (Dummy Revealed):                 │
│ User Controls: South only                            │
│ User Sees: South + West (dummy revealed)            │
│ AI Controls: North + East + West                     │
│                                                      │
│ Play Sequence:                                       │
│ South (USER) → West (AI) → North (AI) → East (AI)   │
│                                                      │
│ ✓ User clicks South's cards when it's South's turn  │
│ ✗ AI plays North (defense), West (dummy), East      │
└─────────────────────────────────────────────────────┘
```

### Scenario 4: West is Declarer
```
Contract: 4♠ by West
Declarer: West
Dummy: East

BEFORE Opening Lead:
┌─────────────────────────────────────────────────────┐
│ Opening Leader: North (LHO of declarer)             │
│ User Controls: Nothing (AI plays North's lead)      │
│ User Sees: South only                               │
│ AI Controls: North (makes opening lead)             │
└─────────────────────────────────────────────────────┘
                      ↓ North plays opening lead
┌─────────────────────────────────────────────────────┐
│ AFTER Opening Lead (Dummy Revealed):                 │
│ User Controls: South only                            │
│ User Sees: South + East (dummy revealed)            │
│ AI Controls: North + East + West                     │
│                                                      │
│ Play Sequence:                                       │
│ North (AI) → East (AI) → South (USER) → West (AI)   │
│                                                      │
│ ✓ User clicks South's cards when it's South's turn  │
│ ✗ AI plays North (defense), East (dummy), West      │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Logic

### Function: `get_controllable_positions(state)`
```python
def get_controllable_positions(state: GameState) -> Set[str]:
    """
    Single-player mode: User controls NS when NS is declaring, S only otherwise
    """
    declarer = state.declarer
    user_position = 'S'

    # NS is declaring side (North or South is declarer)
    if declarer in ['N', 'S']:
        # User controls both North and South after opening lead
        if state.opening_lead_made:
            return {'N', 'S'}
        else:
            # Before opening lead, only opening leader can act
            opening_leader = get_opening_leader(declarer)
            if opening_leader in ['N', 'S']:
                return {opening_leader}
            else:
                return set()  # Wait for AI to lead

    # EW is declaring side (East or West is declarer)
    else:
        # User controls only South (defense)
        return {'S'}
```

### Function: `get_visible_hands(state)`
```python
def get_visible_hands(state: GameState) -> Set[str]:
    """
    Single-player mode visibility rules
    """
    declarer = state.declarer
    dummy = state.dummy
    user_position = 'S'

    visible = {user_position}  # Always see South

    # After opening lead, dummy is visible
    if state.opening_lead_made or state.dummy_revealed:
        visible.add(dummy)

    # If NS is declaring, user sees both N and S after opening lead
    if declarer in ['N', 'S'] and state.opening_lead_made:
        visible.add('N')
        visible.add('S')

    return visible
```

---

## Current Bug (hand_2025-10-16_20-31-53.json)

**Scenario**: 4♠ by North (NS declaring)
**Status**: After opening lead (3 tricks played)
**Next to play**: South

### Expected Behavior:
- ✓ User sees: North + South
- ✓ User controls: North + South
- ✓ User can click South's cards to play
- ✓ When North's turn, user can click North's cards

### Reported Bug:
- ✗ "Declarer's cards are not showing" → North not visible to user
- ✗ "AI is playing all hands and then stops" → AI taking control when it shouldn't

### Root Cause:
`BridgeRulesEngine` is implementing 4-player human rules instead of single-player mode rules.
