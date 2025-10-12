# How to Check If AI Loop is Running

## Visual Indicator (ADDED)

I've added a **colored indicator** in the top-right corner of the screen that shows the AI loop status:

### What You'll See:

**🟢 Green Box: "AI Loop: RUNNING ▶️"**
- AI is actively playing
- Loop is processing
- Cards should be playing automatically

**🔴 Red Box: "AI Loop: STOPPED ⏸️"**
- AI is waiting
- Either it's your turn OR
- Loop is stuck/not continuing

## How to Use This Indicator

### Scenario 1: AI Loop STOPPED (Red) - Normal
**When it's your turn:**
- ✅ Red box shows "STOPPED"
- ✅ Your cards should be clickable (pointer cursor)
- ✅ This is CORRECT behavior

**What to do:** Play your card, then box should turn green.

### Scenario 2: AI Loop STOPPED (Red) - Problem
**When it's NOT your turn:**
- ❌ Red box shows "STOPPED"
- ❌ AI should be playing but isn't
- ❌ This is the BUG

**What to check:**
1. Look at the position labels - whose turn is it?
2. If it says "North (Dummy)" and you're declarer → Should be your turn (red is OK)
3. If it says "East" or "West" and they're AI → Red is WRONG, loop should be running

### Scenario 3: AI Loop RUNNING (Green)
**Normal behavior:**
- ✅ Green box shows "RUNNING"
- ✅ AI is thinking/playing
- ✅ Wait for AI to complete

**What happens:**
- AI plays a card (1 second delay)
- State updates
- If more AI turns → stays green
- If your turn → turns red and stops

## How to Open Browser Console

### On Mac:
1. **Option 1:** Press `Cmd + Option + I`
2. **Option 2:** Press `Cmd + Option + J`
3. **Option 3:** Right-click anywhere → "Inspect" → Click "Console" tab

### On Windows/Linux:
1. **Option 1:** Press `F12`
2. **Option 2:** Press `Ctrl + Shift + I`
3. **Option 3:** Press `Ctrl + Shift + J`

## What to Look For in Console

Once console is open, you'll see logs like:

### Good (Working):
```
🔄 AI play loop triggered: { gamePhase: "playing", isPlayingCard: true }
🎬 AI play loop RUNNING...
🎮 Play State: { next_to_play: "N", dummy: "N", ... }
🤔 Turn check: { nextPlayer: "N", userIsDeclarer: true, ... }
⏸️ Stopping - User is declarer, dummy's turn
```

### Problem (Loop Stuck):
```
🔄 AI play loop triggered: { gamePhase: "playing", isPlayingCard: false }
⏭️ AI play loop skipped: { gamePhase: "playing", isPlayingCard: false }
```

This means `isPlayingCard` is `false` when it should be `true`.

## Finding isPlayingCard Value

### Method 1: Visual Indicator (Easiest)
Just look at the **top-right corner** of the screen:
- 🟢 Green = `isPlayingCard: true`
- 🔴 Red = `isPlayingCard: false`

### Method 2: Console Log
Look for this line in console:
```
🎯 PlayTable render: {
  next_to_play: "N",
  isPlayingCard: false,    ← HERE IT IS!
  ...
}
```

### Method 3: Manual Check (Advanced)
In browser console, type:
```javascript
// This won't work because React state isn't globally accessible
// Use Method 1 or 2 instead
```

## Quick Troubleshooting

### Problem: Red "STOPPED" when AI should play

**Step 1:** Check whose turn it is
- Look at position labels
- Which one has the arrow ⬅️?

**Step 2:** Identify role
- Are you declarer? (contract says "by S")
- Is it dummy's turn? (label says "Dummy")

**Step 3:** Determine if it's correct to stop
- **Your turn (not dummy):** Red is CORRECT
- **Dummy's turn & you're declarer:** Red is CORRECT
- **AI's turn (not dummy):** Red is WRONG

### Problem: Cards show "no-go" sign (🚫)

**This means cards are disabled.**

**Check:**
1. **Visual indicator** - Is it red or green?
2. **isDummyTurn in console** - Should be `true` when dummy's turn and you're declarer

**Console log shows:**
```
isDummyTurn: false    ← Cards disabled
isDummyTurn_calculation: {
  next_is_dummy: true,
  not_playing: false,   ← isPlayingCard is TRUE (should be FALSE!)
  user_is_declarer: true,
  result: false
}
```

**If `not_playing: false`** (meaning isPlayingCard is TRUE), that's the problem!

## What the Colors Mean

| Visual | isPlayingCard | When This is Correct |
|--------|---------------|---------------------|
| 🟢 Green RUNNING | true | AI is playing |
| 🔴 Red STOPPED | false | It's your turn to play |

| Visual | isPlayingCard | When This is WRONG |
|--------|---------------|-------------------|
| 🔴 Red STOPPED | false | AI should be playing but isn't |
| 🟢 Green RUNNING | true | Your turn but cards disabled |

## Current Issue Diagnosis

**Symptom:** "North's turn to play (dummy) but cards are inactive with red no-go sign"

**Analysis:**
- North is dummy
- You are declarer (South)
- It's North's turn
- **You should be able to play North's cards**

**Check:**
1. **Visual indicator:** Should be 🔴 RED (stopped, waiting for you)
2. **North's cards:** Should have pointer cursor (clickable)
3. **Console isDummyTurn:** Should be `true`

**If:**
- ✅ Indicator is RED
- ❌ Cards show no-go sign
- ❌ isDummyTurn is `false`

**Then:** Problem is `isPlayingCard` is `true` when it should be `false`.

## Taking a Screenshot

To share with me:
1. **Show both:**
   - Top-right indicator (green/red box)
   - The cards with the no-go cursor
2. **Open console** (F12 or Cmd+Option+I)
3. **Take screenshot** showing console logs
4. **Share:** I can see exactly what's happening

## Next Steps

1. **Refresh browser** (Cmd+Shift+R)
2. **Play until it's North's (dummy) turn**
3. **Look at top-right corner:**
   - If GREEN → Wrong, should be RED
   - If RED → Check isDummyTurn in console
4. **Report:**
   - What color is the indicator?
   - What does console say for `isPlayingCard`?
   - What does console say for `isDummyTurn`?

---

**The visual indicator makes it easy!** Just look at top-right:
- Green = AI playing
- Red = Waiting for you

If it's red when AI should play, or green when you should play, that's the bug!
