# Declarer/Dummy Test Plan

## Test Scenarios

### Scenario 1: South Declarer, North Dummy (Most Common)

**Setup:**
1. Deal new hand
2. South opens 1NT
3. North raises to 3NT
4. All pass

**Expected Contract:** 3NT by South

**Expected Behavior:**

| Phase | Expected |
|-------|----------|
| Opening Lead | West leads first card |
| After Opening Lead | North's cards become visible face-up as dummy |
| South's Turn | User can click South's cards to play |
| North's Turn | User can click North's (dummy) cards to play |
| East's Turn | AI plays East's card automatically |
| West's Turn | AI plays West's card automatically |

**Critical Checks:**
- ✅ North's hand is visible after opening lead
- ✅ User can play from North's hand when it's North's turn
- ✅ AI NEVER plays South's cards
- ✅ AI NEVER plays North's cards
- ✅ User controls BOTH South and North

### Scenario 2: North Declarer, South Dummy

**Setup:**
1. Deal new hand
2. North opens 1NT (force via scenario or multiple deals)
3. South raises to 3NT
4. All pass

**Expected Contract:** 3NT by North

**Expected Behavior:**

| Phase | Expected |
|-------|----------|
| Opening Lead | East leads first card |
| After Opening Lead | South's cards become visible as dummy |
| North's Turn | AI plays North's card automatically |
| South's Turn | AI plays South's (dummy) card automatically |
| East's Turn | AI plays East's card automatically |
| West's Turn | AI plays West's card automatically |

**Critical Checks:**
- ✅ South's hand is visible as dummy (cards face-up)
- ✅ User CANNOT play any cards (all controlled by AI)
- ✅ AI plays both North (declarer) and South (dummy)
- ✅ Display shows "AI is playing" or similar message

### Scenario 3: East Declarer, West Dummy

**Setup:**
1. Deal new hand
2. East opens (via scenario or multiple deals)
3. East becomes declarer
4. All pass

**Expected Contract:** Some contract by East

**Expected Behavior:**

| Phase | Expected |
|-------|----------|
| Opening Lead | South leads first card (user) |
| After Opening Lead | West's cards visible as dummy |
| South's Turn | User plays South's card (defender) |
| West's Turn | AI plays West's (dummy) card |
| North's Turn | AI plays North's card (defender) |
| East's Turn | AI plays East's (declarer) card |

**Critical Checks:**
- ✅ West's hand is visible as dummy
- ✅ User only controls South (as defender)
- ✅ AI controls East (declarer) and West (dummy)
- ✅ User can play South's cards on South's turn only

### Scenario 4: West Declarer, East Dummy

**Setup:**
1. Deal new hand
2. West opens (via scenario or multiple deals)
3. West becomes declarer
4. All pass

**Expected Contract:** Some contract by West

**Expected Behavior:**

| Phase | Expected |
|-------|----------|
| Opening Lead | North leads first card (AI) |
| After Opening Lead | East's cards visible as dummy |
| North's Turn | AI plays North's card (defender) |
| East's Turn | AI plays East's (dummy) card |
| South's Turn | User plays South's card (defender) |
| West's Turn | AI plays West's (declarer) card |

**Critical Checks:**
- ✅ East's hand is visible as dummy
- ✅ User only controls South (as defender)
- ✅ AI controls West (declarer) and East (dummy)
- ✅ User can play South's cards on South's turn only

## Testing Steps

### Manual Testing

1. **Start Application**
   ```bash
   cd frontend && npm start
   cd backend && python server.py
   ```

2. **For Each Scenario:**
   - Deal hands until desired declarer is achieved
   - OR use specific scenarios if available
   - Complete bidding as specified
   - Observe play phase behavior
   - Verify all critical checks

3. **Console Logging**
   - Open browser DevTools
   - Watch for console logs with emojis:
     - 🔄 AI play loop triggered
     - ⏸️ Stopping - User controls
     - ▶️ AI player's turn
     - 🃏 Setting dummy hand
     - 🎴 Actual Rendering

### Automated Testing (Future)

```javascript
describe('Declarer/Dummy Control', () => {
  test('South declarer controls both South and North dummy', async () => {
    // Setup: South opens 1NT, North raises to 3NT
    const contract = { declarer: 'S', dummy: 'N', strain: 'NT', level: 3 };
    // Verify user controls both positions
  });

  test('AI declarer controls both declarer and dummy', async () => {
    // Setup: North opens 1NT, South raises to 3NT
    const contract = { declarer: 'N', dummy: 'S', strain: 'NT', level: 3 };
    // Verify AI controls both positions
  });
});
```

## Debug Checklist

If issues persist:

1. **Check Console Logs:**
   - Look for "⏸️ STOPPING - User controls this play"
   - Verify userShouldControl is true when expected
   - Check dummy hand state is set correctly

2. **Check Network Tab:**
   - Verify `/api/get-play-state` returns `dummy_hand` when `dummy_revealed: true`
   - Check `dummy_hand.cards` array has correct cards
   - Verify `dummy` field shows correct position

3. **Check React State:**
   - Use React DevTools
   - Check `dummyHand` state in App component
   - Verify `playState.dummy_hand` prop passed to PlayTable
   - Check `isDummyTurn` prop calculation

4. **Check Play Logic:**
   - Verify `userShouldControl` logic in AI play loop
   - Check `isDummyTurn` calculation in render
   - Verify onClick handlers are connected correctly

## Known Issues (Before Fix)

- ❌ AI plays declarer cards when user is declarer
- ❌ North dummy hand not visible
- ❌ AI plays dummy cards when user is declarer
- ❌ Race conditions in play loop

## Expected After Fix

- ✅ User controls both declarer and dummy when user is declarer
- ✅ Dummy hand always visible after opening lead
- ✅ AI never plays cards that user should control
- ✅ No race conditions - clean state checks
