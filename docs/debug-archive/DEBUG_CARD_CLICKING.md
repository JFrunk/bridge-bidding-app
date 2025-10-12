# Debug Guide - Cannot Click Cards to Play

## Issue
"The first AI played a card but there was no way for me or my partner to play a card. I could select one but there was no way to add it to the hand."

## Debugging Added

I've added extensive logging to identify why cards can't be clicked. Here's what to check:

### Step 1: Refresh Browser
1. Open http://localhost:3000
2. **Hard refresh** (Cmd+Shift+R or Ctrl+Shift+R)
3. Open **Developer Console** (F12)

### Step 2: Play Until It's Your Turn
1. Deal hand and complete bidding
2. Wait for play phase (10 second delay)
3. Watch AI play first card
4. **Wait for your turn**

### Step 3: Check Console Logs

When it's your turn, you should see:

```javascript
⏸️ Stopping - South's turn to play

🎯 PlayTable render: {
  next_to_play: "S",
  isPlayingCard: false,        // MUST BE FALSE
  dummy: "N",
  declarer: "S",
  isUserTurn: true,            // MUST BE TRUE
  isDeclarerTurn: false,
  isDummyTurn: false
}
```

### Step 4: Try Clicking a Card

When you click a card, you should see:

```javascript
🃏 handleCardPlay called: { card: {...}, isPlayingCard: false }
✅ Playing card: { rank: "A", suit: "♦" }
```

## Possible Issues

### Issue 1: isUserTurn is false
**Console shows:**
```javascript
🎯 PlayTable render: { isUserTurn: false, ... }
```

**Cause:** One of these conditions failed:
- `playState.next_to_play !== 'S'` (not South's turn)
- `isPlayingCard === true` (AI loop still running)
- `playState.dummy === 'S'` (you are dummy, use declarer controls)

**Check:**
- What is `next_to_play`? Should be "S"
- What is `isPlayingCard`? Should be `false`
- What is `dummy`? If "S", you're dummy and should see dummy's hand face-up

### Issue 2: isPlayingCard stuck at true
**Console shows:**
```javascript
🎯 PlayTable render: { isPlayingCard: true, ... }
```

**Cause:** The AI loop didn't stop properly

**Check:**
- Do you see "⏸️ Stopping - South's turn to play" log?
- If NO → AI loop logic is wrong
- If YES but isPlayingCard still true → State update timing issue

### Issue 3: handleCardPlay not called at all
**When you click:** No "🃏 handleCardPlay called" log appears

**Cause:** Click handler not attached or cards are disabled

**Check:**
- Inspect a card element in browser DevTools
- Look for class: `playable-card clickable` (good) or `playable-card disabled` (bad)
- Check if onClick handler exists in React DevTools

### Issue 4: handleCardPlay called but blocked
**Console shows:**
```javascript
🃏 handleCardPlay called: { card: {...}, isPlayingCard: true }
⚠️ Blocked: isPlayingCard is true
```

**Cause:** `isPlayingCard` was true when you clicked (race condition)

**Solution:** This should not happen if AI loop stopped properly

### Issue 5: You are dummy
**Console shows:**
```javascript
🎯 PlayTable render: { dummy: "S", ... }
```

**Meaning:** South (you) is dummy, so:
- Your cards are face-up on the table
- Declarer (your partner) controls BOTH hands
- If declarer is AI → They auto-play your cards
- If declarer is you → You should see TWO sets of controls (your hand + declarer's hand)

## Visual Checks

### When It's Your Turn:

✅ **Should see:**
- "Your turn to play!" message
- Cards with normal color (not grayed out)
- Cursor changes to pointer when hovering
- Position label "South (You) ⬅️ Your turn!"

❌ **Should NOT see:**
- Grayed out cards (opacity 0.6)
- "not-allowed" cursor
- No turn indicator

### Card Appearance:

**Clickable cards:**
- Full color
- `cursor: pointer`
- Class: `playable-card clickable`

**Disabled cards:**
- Faded (opacity 0.6)
- `cursor: not-allowed`
- Class: `playable-card disabled`

## Testing Scenarios

### Scenario 1: South is Declarer (Normal)
- Contract: "3♥ by S"
- Dummy: North (N)
- You control: Your own hand (South) + Dummy's hand (North)
- Expect: Two sets of clickable cards

### Scenario 2: South is Defender (Normal)
- Contract: "3♥ by N" or "3♥ by E" or "3♥ by W"
- Dummy: Not South
- You control: Only your own hand (South)
- Expect: One set of clickable cards

### Scenario 3: South is Dummy (Special)
- Contract: "3♥ by N" (your partner is declarer)
- Dummy: South (S)
- You control: Declarer's hand (North) + Your own hand (as dummy)
- Expect: Your cards face-up, you play both hands

## Quick Diagnosis

Run this check in console when it's your turn:

```javascript
// In browser console, type:
console.log({
  next_to_play: window.playState?.next_to_play,
  isPlayingCard: window.isPlayingCard,
  cards_enabled: document.querySelectorAll('.playable-card.clickable').length,
  cards_disabled: document.querySelectorAll('.playable-card.disabled').length
});
```

Expected output:
```javascript
{
  next_to_play: "S",
  isPlayingCard: false,
  cards_enabled: 13,  // Number of cards in your hand
  cards_disabled: 0
}
```

## Manual Test

1. **Refresh** browser (Cmd+Shift+R)
2. **Deal** hand
3. **Bid** "1♠", "Pass", "Pass", "Pass"
4. **Wait** 10 seconds for play to start
5. **Watch** console for "⏸️ Stopping - South's turn to play"
6. **Check** console for "🎯 PlayTable render" with `isUserTurn: true`
7. **Hover** over a card - should see pointer cursor
8. **Click** a card - should see "🃏 handleCardPlay called" log

If any step fails, note which one and check the corresponding issue above.

## Next Steps

After confirming the console output:
1. **Screenshot** the console logs when it's your turn
2. **Note** the values of:
   - `next_to_play`
   - `isPlayingCard`
   - `isUserTurn`
   - `dummy`
   - `declarer`

This will help identify exactly where the issue is.
