# Debug: "Waiting for Cards" Issue

## The Problem

After bidding completes, the game shows "waiting for cards" instead of starting the play phase.

## Root Causes

1. **Frontend not calling `/api/start-play`** after bidding completes
2. **Hands data mismatch** between bidding and play phases
3. **JavaScript error** preventing state transition
4. **CORS or network issue** blocking the API call

## Debugging Steps

### Step 1: Open Browser Developer Console

1. Open the app in browser (http://localhost:3000)
2. Press `F12` or `Cmd+Option+I` (Mac) to open DevTools
3. Click on **Console** tab
4. Look for errors (red text)

**Common errors:**
- `Failed to fetch` - API call failed
- `Hand data not found` - Hands not available
- `Cannot read property` - JavaScript error

### Step 2: Check Network Tab

1. In DevTools, click **Network** tab
2. Deal a hand and complete bidding
3. Watch for `/api/start-play` call
4. Click on the call to see details

**What to check:**
- Is `/api/start-play` being called? (should appear after 3 passes)
- Status code: Should be 200 (green)
- Response: Should have `"success": true`
- If 400/500 error, check response body for error message

### Step 3: Check Backend Logs

In the terminal running the backend server:

```bash
tail -f /tmp/backend_server.log
```

Watch for:
- `/api/start-play` POST requests
- Any Python errors or tracebacks
- "Hand data not found" errors

### Step 4: Manual API Test

Test the start-play endpoint manually:

```bash
# First, deal a hand in the browser
# Then run this:

curl -X POST http://localhost:5001/api/start-play \
  -H 'Content-Type: application/json' \
  -d '{
    "auction_history": ["1NT", "Pass", "Pass", "Pass"],
    "vulnerability": "None"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "contract": "1NT by N",
  "opening_leader": "E",
  ...
}
```

**If error:**
```json
{
  "error": "Hand data not found for North. Please deal a new hand."
}
```

This means the hands from bidding phase weren't available.

## Common Fixes

### Fix 1: Restart Everything

```bash
# Kill servers
kill 23841  # backend
kill 23889  # frontend

# Clear any cached state
rm -f /tmp/backend_server.log /tmp/frontend_server.log

# Restart backend
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
source venv/bin/activate
python server.py

# In another terminal, restart frontend
cd /Users/simonroy/Desktop/bridge_bidding_app/frontend
npm start
```

### Fix 2: Check gamePhase State

Add this temporary logging to see what's happening.

In browser console, after bidding:
```javascript
// Check current game phase
console.log('Game phase:', gamePhase);
console.log('Auction:', auction);
console.log('Is auction over?', isAuctionOver(auction));
```

If `gamePhase` is still "bidding" after 3 passes, the transition isn't happening.

### Fix 3: Force Transition (Temporary Debug)

In browser console:
```javascript
// Force transition to playing phase
fetch('http://localhost:5001/api/start-play', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    auction_history: ['1NT', 'Pass', 'Pass', 'Pass'],
    vulnerability: 'None'
  })
})
.then(r => r.json())
.then(d => console.log(d));
```

If this works, the issue is in the frontend automatic transition.

## Likely Solution

Based on the code, the most likely issue is that the `current_deal` global variable in the backend doesn't have the hands when `/api/start-play` is called.

### Quick Fix: Ensure Hands are Dealt

1. **In the browser:**
   - Click "Deal New Hand" button (important!)
   - Or load a scenario from dropdown
   - Complete the bidding
   - Watch console for errors

2. **Verify hands were dealt:**
```bash
curl http://localhost:5001/api/get-all-hands | python3 -m json.tool
```

Should show 4 hands (North, East, South, West).

If empty or error, the deal wasn't created properly.

## Step-by-Step Test Procedure

1. **Start fresh:**
   - Reload browser (Cmd+R or Ctrl+R)
   - Should see empty bidding table

2. **Deal hand:**
   - Click "Deal New Hand" button
   - Should see your hand (South) appear
   - Should see "Your Hand" with 13 cards

3. **Complete bidding:**
   - Make bids (or Pass)
   - AI bids automatically
   - Continue until 3 consecutive passes
   - Should see final contract (e.g., "Contract: 3NT by South")

4. **Check console:**
   - Should see "Play started: ..." message
   - Should transition to playing phase
   - Should see opening lead

5. **If stuck at "waiting for cards":**
   - Check console for errors (F12)
   - Check Network tab for failed /api/start-play call
   - Check backend logs for errors

## Workaround: Use Standalone Play Testing

If the integrated bidding → play transition isn't working, you can test play directly:

```bash
cd backend
source venv/bin/activate

# Run standalone play tests
PYTHONPATH=. python3 -m pytest tests/play/ -v

# Or test specific scenario
python3 << 'EOF'
from tests.play_test_helpers import *
from engine.play.ai.minimax_ai import MinimaxPlayAI

# Create test deal
deal = create_test_deal(
    north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
    east="♠543 ♥543 ♦543 ♣5432",
    south="♠876 ♥876 ♦8762 ♣876",
    west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
)

state = create_play_scenario("3NT by N", deal, "None")

# Test AI
ai = MinimaxPlayAI(max_depth=3)

# Play a few cards
for i in range(4):
    pos = state.next_to_play
    card = ai.choose_card(state, pos)
    print(f"{pos} plays {card.rank}{card.suit}")

    state.current_trick.append((card, pos))
    state.hands[pos].cards.remove(card)

    if len(state.current_trick) == 4:
        print("Trick complete!")
        break

    state.next_to_play = PlayEngine.next_player(pos)
EOF
```

This tests the play engine directly without the frontend.

## Next Steps if Still Not Working

If you're still seeing "waiting for cards":

1. **Take a screenshot** of:
   - The browser window
   - The browser console (F12 → Console tab)
   - The Network tab showing the /api/start-play call (or lack thereof)

2. **Share backend logs:**
   ```bash
   cat /tmp/backend_server.log
   ```

3. **Check frontend state:**
   In browser console:
   ```javascript
   // Log current state
   console.log({
     gamePhase: gamePhase,
     auction: auction,
     hand: hand,
     nextPlayerIndex: nextPlayerIndex
   });
   ```

Then I can help identify the specific issue!

## Expected Behavior (When Working)

1. Deal hand → See 13 cards
2. Bid → AI bids automatically
3. Three passes → Contract announced
4. **Automatic transition** (1 second delay)
5. Opening lead made by AI
6. Dummy revealed
7. Play continues...

If you're not seeing step 4-7, that's the issue to fix.
