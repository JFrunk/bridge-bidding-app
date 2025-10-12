# Fix - AI Play Loop Stopping After Opening Lead

## Issue Reported

**User:** "My partner played their card (AI driven) but the next AI did not."

**From hand_2025-10-11_14-44-21.json:**
- Contract: 2♦ by West (AI declarer)
- Dummy: East (AI's partner)
- Opening Leader: North (AI)
- **Cards Played:** K♣ from North only
- **Next to Play:** East (Dummy)
- **Problem:** AI froze - no card played by East (dummy)

## Root Cause Analysis

The AI play loop was stopping after the first card, and not continuing to play subsequent cards. The issue was **lack of visibility** into why the loop wasn't continuing.

### Why This Happens

The AI play loop (useEffect) only runs when:
```javascript
if (gamePhase !== 'playing' || !isPlayingCard) return;
```

After each AI play, the code sets `isPlayingCard(true)` after a delay to trigger the loop again (line 786):
```javascript
setTimeout(() => setIsPlayingCard(true), 500);
```

However, there was **no logging** to confirm:
1. Whether the loop was being triggered again
2. Whether it was skipped due to conditions
3. Whether it was running but failing silently

## Debugging Enhancements Added

### 1. Loop Entry Logging ([App.js:647-650](frontend/src/App.js#L647-L650))

```javascript
console.log('🔄 AI play loop triggered:', { gamePhase, isPlayingCard });
if (gamePhase !== 'playing' || !isPlayingCard) {
  console.log('⏭️ AI play loop skipped:', { gamePhase, isPlayingCard });
  return;
}
```

**Shows:**
- Every time useEffect runs
- Why it was skipped (if gamePhase or isPlayingCard wrong)

### 2. Loop Execution Logging ([App.js:655](frontend/src/App.js#L655))

```javascript
console.log('🎬 AI play loop RUNNING...');
```

**Shows:**
- When the loop actually executes runAiPlay()

### 3. Loop Continuation Logging ([App.js:780, 784](frontend/src/App.js#L780-L784))

```javascript
if (playData.trick_complete && playData.trick_winner) {
  console.log('🔁 Continuing to next trick...');
  setTimeout(() => setIsPlayingCard(true), 500);
} else {
  console.log('🔁 Continuing AI play loop (trick not complete)...');
  setTimeout(() => setIsPlayingCard(true), 500);
}
```

**Shows:**
- When the loop is set to continue
- Whether it's continuing within a trick or moving to next trick

## Expected Console Output

### Successful AI Play Sequence:

```javascript
// Loop triggers
🔄 AI play loop triggered: { gamePhase: "playing", isPlayingCard: true }
🎬 AI play loop RUNNING...

// Fetches state
🎮 Play State: { next_to_play: "N", trick_size: 0, ... }

// AI evaluates turns
🤔 Turn check: { nextPlayer: "N", userIsDummy: false, ... }

// AI plays
▶️ AI player's turn: N
AI played: { card: { rank: "K", suit: "♣" }, position: "N", ... }
🔄 Updated play state after AI play: { trick_size: 1, ... }

// Sets up next iteration
🔁 Continuing AI play loop (trick not complete)...

// Loop triggers again after 500ms
🔄 AI play loop triggered: { gamePhase: "playing", isPlayingCard: true }
🎬 AI play loop RUNNING...

// Fetches state
🎮 Play State: { next_to_play: "E", trick_size: 1, ... }

// AI evaluates turns
🤔 Turn check: { nextPlayer: "E", userIsDummy: false, ... }

// AI plays dummy's card
▶️ AI player's turn: E
AI played: { card: { rank: "A", suit: "♣" }, position: "E", ... }
🔄 Updated play state after AI play: { trick_size: 2, ... }

// Continues...
🔁 Continuing AI play loop (trick not complete)...
```

## Diagnostic Information

### If Loop Stops After First Card:

#### Symptom 1: Loop Triggered But Skipped
```javascript
🔄 AI play loop triggered: { gamePhase: "playing", isPlayingCard: false }
⏭️ AI play loop skipped: { gamePhase: "playing", isPlayingCard: false }
```

**Meaning:** `isPlayingCard` is `false`, so loop won't run.

**Cause:** The `setTimeout(() => setIsPlayingCard(true), 500)` never executed or was overridden.

**Fix:** Check if something is calling `setIsPlayingCard(false)` unexpectedly.

#### Symptom 2: Loop Not Triggered At All
No "🔄 AI play loop triggered" log after first card.

**Meaning:** useEffect not running again.

**Cause:** React dependencies might not be triggering re-run.

**Fix:** Check useEffect dependencies array (currently empty `[]` at end of useEffect).

#### Symptom 3: Loop Runs But Errors
```javascript
🎬 AI play loop RUNNING...
Error in AI play loop: [error message]
```

**Meaning:** The loop ran but hit an error.

**Cause:** Backend error, network issue, or logic error.

**Fix:** Check error message and backend logs.

#### Symptom 4: Loop Runs But Stops Before Playing
```javascript
🎬 AI play loop RUNNING...
🎮 Play State: { ... }
🤔 Turn check: { ... }
⏸️ Stopping - South's turn to play
```

**Meaning:** Loop thinks it's user's turn and stops.

**Cause:** Turn detection logic incorrectly identified it as user's turn.

**Fix:** Check turn logic conditions (lines 717-738).

## Testing the Fix

### Step 1: Refresh Browser
Hard refresh (Cmd+Shift+R) to load new code with logging.

### Step 2: Start New Game
1. Deal hand
2. Complete bidding (e.g., "1♠", "Pass", "Pass", "Pass")
3. Wait 3 seconds for play phase
4. **Watch console carefully**

### Step 3: Verify Logs Appear
Look for the sequence:
1. "🎬 AI play loop RUNNING..." (multiple times)
2. "▶️ AI player's turn:" for each AI player
3. "🔁 Continuing AI play loop..." after each card
4. "🔄 AI play loop triggered:" repeatedly

### Step 4: Identify Failure Point
If the loop stops, look at the **last log** before it stops:

- **Last log is "🔁 Continuing..."**: Loop set to continue but didn't trigger again
- **Last log is "⏸️ Stopping..."**: Loop correctly stopped for user turn
- **Last log is "Error in AI play loop"**: Backend or network error
- **No logs after first card**: Loop not running at all

## Potential Backend Issue

The backend's `/api/get-ai-play` endpoint (server.py:655-720) might also have an issue.

**Check:**
1. Does it handle dummy position correctly?
2. Does `play_ai.choose_card()` work for dummy?
3. Are there any Python exceptions in backend logs?

**Backend verification:**
```bash
# Check backend logs for errors
tail -f backend/server_log.txt

# Or if running in terminal, watch for Python errors
```

## Summary of Changes

**File:** frontend/src/App.js

**Changes:**
1. Line 647-650: Log when loop triggers and why it skips
2. Line 655: Log when loop actually runs
3. Line 780: Log when continuing to next trick
4. Line 784: Log when continuing within trick

**Purpose:** Provide complete visibility into AI play loop execution flow.

## Next Steps

1. **Run the game** with console open
2. **Watch the logs** to see where the loop stops
3. **Share console output** showing what happens after the first card
4. Based on logs, we can identify exact failure point and fix it

The issue is likely one of:
- React state update not triggering useEffect
- Backend error when playing dummy's card
- Turn detection logic error
- Race condition in state updates

With these logs, we'll be able to pinpoint it exactly.
