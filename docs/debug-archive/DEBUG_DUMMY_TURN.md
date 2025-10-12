# Debug - Cards Disabled When Dummy's Turn (Declarer Controlling)

## Issue Reported
"OK I see the cards now, but both North and South cards indicate a red circle with a cross through it when I try to play them. The system does not appear to recognize that it is North's turn to play or does not release the hand to be played."

## Current Game State (Verified)

From backend:
```
Next to play: N (North)
Dummy: N (North is dummy)
Declarer: S (You are declarer)
Dummy revealed: True
Trick size: 1 (West played opening lead)
```

## Expected Behavior

Since:
- You are declarer (S)
- It's dummy's turn (N)
- You control dummy

**North's cards should be clickable** for you to play from dummy's hand.

## Why Cards Are Disabled

### Card Disability Logic

**PlayComponents.js Line 222 (North dummy):**
```javascript
<PlayableCard
  card={card}
  onClick={userIsDeclarer ? onDummyCardPlay : () => {}}
  disabled={userIsDeclarer ? !isDummyTurn : true}
/>
```

**Translation:**
- If you're declarer: `disabled={!isDummyTurn}`
- If you're NOT declarer: `disabled={true}` (always disabled)

**So cards are disabled when `isDummyTurn === false`**

### isDummyTurn Calculation

**App.js Line 880:**
```javascript
isDummyTurn={playState.next_to_play === playState.dummy && !isPlayingCard && playState.contract.declarer === 'S'}
```

**Breaking it down:**
1. `playState.next_to_play === playState.dummy` → `'N' === 'N'` → **TRUE** ✅
2. `!isPlayingCard` → depends on state → **TRUE or FALSE?** ❓
3. `playState.contract.declarer === 'S'` → `'S' === 'S'` → **TRUE** ✅

**Result:** `isDummyTurn = true && ?isPlayingCard && true`

**If `isPlayingCard === true`, then `isDummyTurn === false`, cards disabled** ❌

## Root Cause: isPlayingCard Stuck at True

The AI play loop controls `isPlayingCard`:
- Set to `true` when AI should play
- Set to `false` when user's turn

**AI Play Loop Logic (App.js Lines 733-737):**
```javascript
// If it's dummy's turn and user is declarer, stop and wait for user to play dummy's card
if (nextPlayer === state.dummy && userIsDeclarer) {
  console.log('⏸️ Stopping - User is declarer, dummy\'s turn');
  setIsPlayingCard(false);
  setDisplayedMessage("Your turn to play from dummy's hand!");
  return;
}
```

**This SHOULD work:**
- `nextPlayer === state.dummy` → `'N' === 'N'` → TRUE
- `userIsDeclarer` → `declarerPos === 'S'` → TRUE

**So the loop should stop and set `isPlayingCard(false)`**

## Possible Issues

### Issue 1: AI Loop Never Ran
If the AI loop (`useEffect` at line 646) never ran after opening lead, it never checked the turn and never set `isPlayingCard(false)`.

**Check console for:**
- "🎬 AI play loop RUNNING..." - Loop started
- "🤔 Turn check: ..." - Turn evaluation
- "⏸️ Stopping - User is declarer, dummy's turn" - Loop stopped

**If these logs are missing:** Loop didn't run.

**Why it might not run:**
- `gamePhase !== 'playing'` - Wrong phase
- `!isPlayingCard` - Already false (loop won't start)

### Issue 2: isPlayingCard Was Never Set to True
If `isPlayingCard` was never set to `true` after the opening lead, the loop wouldn't run.

**Check:** After West plays, was `isPlayingCard` set to `true`?

**In backend play logic (server.py:655-720), after AI plays:**
Frontend should call `/api/get-ai-play` and then set `isPlayingCard(true)` to continue loop.

### Issue 3: Race Condition
The state update might not have triggered a re-render.

### Issue 4: Loop Ran But Stopped at Wrong Condition
The loop might have stopped at a different condition before reaching line 733.

**Check lines before 733:**
- Line 693-697: Play complete (13 tricks) - Should be FALSE
- Line 725-729: South's turn (not dummy) - Should be FALSE
- Line 741-745: Declarer's turn (user is dummy) - Should be FALSE

## Enhanced Debugging Added

**App.js Lines 859-876** now log:
```javascript
{
  next_to_play: "N",
  isPlayingCard: true/false,  // KEY DIAGNOSTIC
  dummy: "N",
  declarer: "S",
  userIsDeclarer: true,
  isDummyTurn: true/false,    // KEY DIAGNOSTIC
  isDummyTurn_calculation: {
    next_is_dummy: true,
    not_playing: true/false,  // KEY DIAGNOSTIC
    user_is_declarer: true,
    result: true/false
  }
}
```

## Diagnostic Steps

### Step 1: Check Console Logs

Look for the `🎯 PlayTable render:` log and note:

1. **`isPlayingCard`:** Should be **FALSE**
   - If TRUE → Loop didn't stop
   - If FALSE → Check isDummyTurn

2. **`isDummyTurn`:** Should be **TRUE**
   - If FALSE → Check isDummyTurn_calculation breakdown

3. **`isDummyTurn_calculation`:**
   - `next_is_dummy`: Should be TRUE
   - `not_playing`: Should be TRUE (if isPlayingCard is false)
   - `user_is_declarer`: Should be TRUE
   - `result`: Should be TRUE

### Step 2: Check AI Loop Logs

Look for these in order:
1. "🔄 AI play loop triggered: { gamePhase: 'playing', isPlayingCard: true }"
2. "🎬 AI play loop RUNNING..."
3. "🎮 Play State: { next_to_play: 'N', ... }"
4. "🤔 Turn check: { nextPlayer: 'N', userIsDeclarer: true, ... }"
5. "⏸️ Stopping - User is declarer, dummy's turn"

**If you DON'T see log #5:** The loop didn't stop at the right place.

**If you DON'T see logs #1-4:** The loop never ran.

### Step 3: Manual State Check

In browser console, type:
```javascript
// Check if React state is accessible (it's not, but we can check rendered output)
// Look at the console logs for isPlayingCard value
```

## Expected Console Output (Working)

```javascript
// After West plays opening lead:

🔄 AI play loop triggered: { gamePhase: "playing", isPlayingCard: true }
🎬 AI play loop RUNNING...
🎮 Play State: { next_to_play: "N", dummy: "N", declarer: "S", trick_size: 1 }
🤔 Turn check: { nextPlayer: "N", userIsDummy: false, userIsDeclarer: true, dummy: "N", declarerPos: "S" }
⏸️ Stopping - User is declarer, dummy's turn

// Then on re-render:

🎯 PlayTable render: {
  next_to_play: "N",
  isPlayingCard: false,         // ✅ FALSE - Loop stopped
  dummy: "N",
  declarer: "S",
  userIsDeclarer: true,
  isDummyTurn: true,            // ✅ TRUE - Cards should be enabled
  isDummyTurn_calculation: {
    next_is_dummy: true,
    not_playing: true,          // ✅ TRUE - isPlayingCard is false
    user_is_declarer: true,
    result: true                // ✅ TRUE - All conditions met
  }
}
```

## Likely Scenarios

### Scenario A: isPlayingCard is TRUE
**Console shows:**
```javascript
isPlayingCard: true
isDummyTurn: false
```

**Problem:** AI loop didn't stop or didn't run at all.

**Solution:** Check why loop didn't run/stop.

### Scenario B: Loop Never Ran
**Console shows NO AI loop logs**

**Problem:** Loop trigger conditions not met.

**Solution:** Check `gamePhase === 'playing'` and initial `isPlayingCard` state.

### Scenario C: Loop Stopped at Wrong Place
**Console shows:** "⏸️ Stopping - ..." but wrong message

**Problem:** Loop stopped at line 725 or 741 instead of 733.

**Solution:** Check turn detection logic.

## Quick Fix to Test

If the issue is `isPlayingCard` stuck at `true`, try this in browser console:

```javascript
// This won't work directly, but the user can refresh and try again
// OR we can add a manual override button
```

## Testing Instructions

1. **Refresh browser** (Cmd+Shift+R)
2. **Open Console** (F12)
3. **Deal hand** and complete bidding (you should be declarer)
4. **Wait for opening lead** (West plays first card)
5. **Immediately check console** for:
   - AI loop logs
   - PlayTable render log
6. **Note values of:**
   - `isPlayingCard`
   - `isDummyTurn`
   - `isDummyTurn_calculation.not_playing`

7. **Try hovering over North's cards:**
   - Should see pointer cursor (if enabled)
   - Should see "not-allowed" cursor (if disabled)

8. **Share console output** showing the values above

## Files Modified

**frontend/src/App.js:**
- Lines 859-876: Enhanced diagnostic logging

## Next Steps

Based on console output, we'll identify:
1. Whether AI loop ran
2. Whether it stopped correctly
3. Whether `isPlayingCard` is the issue
4. Why cards are disabled

**Most likely cause:** AI loop didn't run or `isPlayingCard` is stuck at `true`.
