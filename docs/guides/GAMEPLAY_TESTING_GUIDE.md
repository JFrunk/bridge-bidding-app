# Step-by-Step Gameplay Testing Guide

## Overview

This guide will walk you through testing the complete bidding + card play workflow in your Bridge Bidding App, from dealing a hand through bidding to playing out all 13 tricks and seeing the final score.

---

## Prerequisites

Make sure you have both backend and frontend running:

### Terminal 1 - Backend Server
```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
source venv/bin/activate  # If using virtual environment
python3 server.py
```

**Expected output:**
```
 * Running on http://127.0.0.1:5001
```

### Terminal 2 - Frontend Server
```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/frontend
npm start
```

**Expected output:**
```
Compiled successfully!
You can now view frontend in the browser.

  Local:            http://localhost:3000
```

---

## Method 1: Full Workflow Test (Bidding → Playing)

This tests the complete integration from bidding through card play.

### Step 1: Open the Application

1. Open your browser to http://localhost:3000
2. You should see the Bridge Bidding App interface

### Step 2: Deal a Hand

**Action:** Click the **"Deal New Hand"** button

**What to verify:**
- ✅ You see your hand (South position) with 13 cards
- ✅ Hand Analysis panel shows HCP, distribution points, suit breakdown
- ✅ Vulnerability indicator shows (e.g., "Vuln: None")
- ✅ Bidding table is empty and ready
- ✅ Bidding box is enabled (level buttons 1-7 clickable)

**Troubleshooting:**
- If no hand appears, check browser console for errors (F12 → Console tab)
- Verify backend server is running on port 5001

### Step 3: Complete the Bidding

You need to reach a contract and then have 3 consecutive passes.

**Example Bidding Sequence (3NT contract):**

1. **North opens:**
   - AI automatically bids (watch bidding table)
   - Example: "1NT" (15-17 HCP balanced)

2. **East passes:**
   - AI automatically passes

3. **Your turn (South):**
   - Click level "3"
   - Click "NT"
   - Your bid "3NT" appears in the table

4. **West passes:**
   - AI automatically passes

5. **North passes:**
   - AI automatically passes

6. **East passes:**
   - AI automatically passes

**What to verify at this stage:**
- ✅ Bidding table shows all bids in 4 columns (N/E/S/W)
- ✅ Current player indicator (yellow highlight) moves correctly
- ✅ You can only bid when it's South's turn
- ✅ Bid legality is enforced (can't bid 1♠ after 3NT)
- ✅ After 3 consecutive passes, bidding is complete

**Common bidding sequences to try:**
- **1NT - Pass - 3NT - Pass - Pass - Pass** (Simple NT contract)
- **1♠ - Pass - 4♠ - Pass - Pass - Pass** (Major suit game)
- **1♣ - 1♠ - 2NT - Pass - 3NT - Pass - Pass - Pass** (Competitive)

### Step 4: Automatic Transition to Play Phase

**What happens automatically:**
After the 3rd consecutive pass, the app should:

1. **Detect bidding is complete**
2. **Display transition message:**
   - "Contract: 3NT by North. Opening leader: East"
   - (or whatever the contract and positions are)
3. **Switch to play view** (may take 1-2 seconds)

**What to verify:**
- ✅ Bidding table is replaced by play table
- ✅ Contract is displayed prominently (e.g., "3NT by N")
- ✅ Tricks won counters show: NS: 0, EW: 0
- ✅ Play area appears in center with 4 position labels

**Troubleshooting:**
- If transition doesn't happen, check browser console for errors
- Verify `/api/start-play` endpoint is responding (check Network tab in dev tools)

### Step 5: Opening Lead

**What happens:**
- The opening leader (LHO of declarer) automatically plays a card
- You'll see a message: "W played J♠" (or whatever card)
- The card appears in the center play area

**What to verify:**
- ✅ Opening leader is correct (LHO of declarer)
- ✅ Card appears in the center
- ✅ Position label shows who played it (N, E, S, or W)

### Step 6: Dummy Revealed

**What happens after opening lead:**
- Dummy hand (partner of declarer) is revealed
- You can see all 13 cards in dummy's hand
- Dummy's cards are displayed face-up

**What to verify:**
- ✅ Dummy position is correct (partner of declarer)
- ✅ All 13 dummy cards are visible
- ✅ Dummy cards are organized by suit
- ✅ Label shows "(Dummy)" next to position name

**Example:**
```
If contract is "3NT by South":
- Declarer: South (you)
- Dummy: North (partner)
- Opening leader: West (LHO of South)
- Defenders: East and West
```

### Step 7: Watch AI Players

**What happens:**
- AI players (North, East, West) automatically play cards in sequence
- Each card play is announced: "E played 5♠"
- Cards appear in center play area
- Short delay (~1 second) between each AI card

**What to verify:**
- ✅ AI players play in correct order (clockwise: W → N → E → S)
- ✅ Each card appears in the center
- ✅ Messages announce each play
- ✅ AI follows suit rules (plays same suit if they have it)

### Step 8: Your Turn to Play

**When it's your turn (South):**

**Visual cues:**
- Message: "Your turn to play!"
- Your cards should be clickable (cursor changes to pointer on hover)
- Position label shows "⬅️ Your turn!"

**Action:**
1. Hover over your cards - they should highlight or show hover effect
2. Click a card to play it

**What to verify:**
- ✅ Only legal cards are clickable (must follow suit if able)
- ✅ Clicking a card plays it to the center
- ✅ Card is removed from your hand
- ✅ Play continues automatically with next AI player

**Testing illegal plays:**
- Try clicking a card in a different suit when you have the led suit
- Should see error: "Must follow suit if able"

### Step 9: Trick Completion

**When 4 cards have been played:**

**What happens:**
1. **Winner determined** - Highest card in trump suit (or led suit if NT)
2. **Winner highlighted** - Card that won is marked with "Winner!" badge
3. **Winner announced** - "North wins the trick!"
4. **Tricks won updated** - Counter increments (e.g., NS: 1, EW: 0)
5. **Brief pause** (~2-3 seconds) to see the trick
6. **Trick cleared** - Cards removed from center
7. **Next trick starts** - Winner leads to next trick

**What to verify:**
- ✅ Correct card wins (highest trump, or highest in led suit)
- ✅ Winner is clearly indicated
- ✅ Tricks won counter updates correctly
- ✅ Next trick starts with winner leading

**Trick-taking rules to verify:**
- Highest card in led suit wins (if no trumps played)
- Any trump beats any non-trump
- Highest trump wins (if multiple trumps played)

### Step 10: Continue Playing

**Repeat steps 7-9 for all 13 tricks:**

Watch the trick count increment:
- After trick 1: NS: 1, EW: 0 (or whatever the result)
- After trick 2: NS: 1, EW: 1 (or whatever)
- Continue until all 13 tricks played...

**What to verify during play:**
- ✅ Hand counts decrease (you start with 13, end with 0)
- ✅ Dummy hand cards also decrease
- ✅ AI follows basic bridge strategy
- ✅ No crashes or freezes

**Progress milestones:**
- 📊 After 3 tricks: Game is flowing
- 📊 After 7 tricks: Contract status becoming clear
- 📊 After 10 tricks: Almost done
- 📊 After 13 tricks: Final score coming!

### Step 11: Final Score Display

**After 13 tricks are played:**

**What happens:**
- Score modal/overlay appears automatically
- Shows contract details and result

**Modal should display:**
```
Hand Complete!

Contract: 3NT by S
Tricks Taken: 9
Result: Made exactly
Score: +400
```

**What to verify:**
- ✅ Contract shown correctly
- ✅ Tricks taken is accurate
- ✅ Result is correct:
  - "Made exactly" (took exactly what needed)
  - "Made +1" (took 1 overtrick)
  - "Down 1" (failed by 1 trick)
- ✅ Score calculation is correct
- ✅ Close button is visible

**Score verification:**
Common scores for reference:
- 3NT making exactly (non-vul): +400
- 3NT +1 (non-vul): +430
- 3NT -1 (non-vul): -50
- 4♠ making exactly (non-vul): +420
- 4♠ doubled making (vul): +790

### Step 12: Close and Repeat

**Action:**
- Click "Close" button on score modal

**What happens:**
- Modal closes
- You return to the main screen
- Ready to deal a new hand

**What to verify:**
- ✅ Modal closes cleanly
- ✅ Can click "Deal New Hand" again
- ✅ New hand deals correctly
- ✅ State is properly reset

---

## Method 2: Testing Standalone Play (No Bidding)

This tests the play module independently using the new modular architecture.

### Step 1: Open Python Console

```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
source venv/bin/activate
python3
```

### Step 2: Run Complete Test Example

```python
from tests.play_test_helpers import create_test_deal, create_play_scenario, print_hand_diagram
from engine.simple_play_ai import SimplePlayAI
from engine.play_engine import PlayEngine

# Create a deal
deal = create_test_deal(
    north="♠AKQ2 ♥432 ♦KQJ ♣432",
    east="♠765 ♥765 ♦765 ♣7654",
    south="♠432 ♥AKQ ♦A32 ♣AKQ8",
    west="♠JT98 ♥JT98 ♦T98 ♣J9"
)

# Create play scenario
play_state = create_play_scenario("3NT by S", deal, "None")

# Show diagram
print_hand_diagram(deal, play_state.contract)

# Initialize AI
ai = SimplePlayAI()

# Play one trick
print("\n=== PLAYING TRICK 1 ===")

# West leads
print(f"\n{play_state.next_to_play} to play...")
card = ai.choose_card(play_state, play_state.next_to_play)
print(f"{play_state.next_to_play} plays {card.rank}{card.suit}")
play_state.current_trick.append((card, play_state.next_to_play))
play_state.hands[play_state.next_to_play].cards.remove(card)
play_state.next_to_play = PlayEngine.next_player(play_state.next_to_play)

# North plays
print(f"\n{play_state.next_to_play} to play...")
play_state.dummy_revealed = True
card = ai.choose_card(play_state, play_state.next_to_play)
print(f"{play_state.next_to_play} plays {card.rank}{card.suit}")
play_state.current_trick.append((card, play_state.next_to_play))
play_state.hands[play_state.next_to_play].cards.remove(card)
play_state.next_to_play = PlayEngine.next_player(play_state.next_to_play)

# East plays
print(f"\n{play_state.next_to_play} to play...")
card = ai.choose_card(play_state, play_state.next_to_play)
print(f"{play_state.next_to_play} plays {card.rank}{card.suit}")
play_state.current_trick.append((card, play_state.next_to_play))
play_state.hands[play_state.next_to_play].cards.remove(card)
play_state.next_to_play = PlayEngine.next_player(play_state.next_to_play)

# South plays
print(f"\n{play_state.next_to_play} to play...")
card = ai.choose_card(play_state, play_state.next_to_play)
print(f"{play_state.next_to_play} plays {card.rank}{card.suit}")
play_state.current_trick.append((card, play_state.next_to_play))
play_state.hands[play_state.next_to_play].cards.remove(card)

# Determine winner
winner = PlayEngine.determine_trick_winner(
    play_state.current_trick,
    play_state.contract.trump_suit
)
print(f"\n🏆 {winner} wins the trick!")

# Update state
play_state.tricks_won[winner] += 1
print(f"\nTricks won: NS={play_state.tricks_taken_ns}, EW={play_state.tricks_taken_ew}")
```

**What to verify:**
- ✅ Hand diagram displays correctly
- ✅ AI makes reasonable card choices
- ✅ Follow-suit rules are enforced
- ✅ Trick winner is determined correctly
- ✅ Tricks won counter updates

### Step 3: Run Automated Test Suite

```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
PYTHONPATH=. python3 tests/test_standalone_play.py
```

**Expected output:**
```
============================================================
COMPLETE STANDALONE PLAY TEST EXAMPLE
============================================================

1. Creating test deal...
✓ Deal created

2. Creating play scenario: 3NT by South...
✓ Contract: 3NT by S
✓ Opening leader: W
✓ Dummy: N

3. Hand diagram:
[ASCII diagram of all 4 hands]

4. Verifying setup...
✓ All assertions passed

============================================================
SUCCESS: Standalone play test completed!
============================================================
```

**What to verify:**
- ✅ All tests pass
- ✅ No errors in output
- ✅ Diagram renders correctly

---

## Method 3: API Endpoint Testing

Test the backend endpoints directly using curl or a REST client.

### Step 1: Deal Hands

```bash
curl http://localhost:5001/api/deal-hands
```

**Expected response:**
```json
{
  "hand": [
    {"rank": "A", "suit": "♠"},
    {"rank": "K", "suit": "♠"},
    ...
  ],
  "points": {
    "hcp": 13,
    "dist_points": 2,
    "total_points": 15,
    ...
  },
  "vulnerability": "None"
}
```

### Step 2: Get All Hands

```bash
curl http://localhost:5001/api/get-all-hands
```

**Expected response:**
```json
{
  "hands": {
    "North": {...},
    "East": {...},
    "South": {...},
    "West": {...}
  },
  "vulnerability": "None"
}
```

### Step 3: Start Play

```bash
curl -X POST http://localhost:5001/api/start-play \
  -H "Content-Type: application/json" \
  -d '{
    "auction_history": ["1NT", "Pass", "3NT", "Pass", "Pass", "Pass"],
    "vulnerability": "None"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "contract": "3NT by N",
  "contract_details": {
    "level": 3,
    "strain": "NT",
    "declarer": "N",
    "doubled": 0
  },
  "opening_leader": "E",
  "dummy": "S",
  "next_to_play": "E"
}
```

### Step 4: Get Play State

```bash
curl http://localhost:5001/api/get-play-state
```

**Expected response:**
```json
{
  "contract": {...},
  "current_trick": [],
  "trick_complete": false,
  "trick_winner": null,
  "tricks_won": {"N": 0, "E": 0, "S": 0, "W": 0},
  "next_to_play": "E",
  "dummy": "S",
  "dummy_revealed": false,
  "is_complete": false
}
```

### Step 5: AI Play

```bash
curl -X POST http://localhost:5001/api/get-ai-play \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected response:**
```json
{
  "card": {"rank": "J", "suit": "♠"},
  "position": "E",
  "trick_complete": false,
  "trick_winner": null,
  "next_to_play": "S",
  "tricks_won": {"N": 0, "E": 0, "S": 0, "W": 0},
  "explanation": "E played J♠"
}
```

---

## Common Issues and Troubleshooting

### Issue 1: Play Phase Doesn't Start

**Symptoms:**
- Bidding completes but nothing happens
- No transition to play view

**Check:**
1. Browser console for JavaScript errors
2. Network tab - is `/api/start-play` being called?
3. Backend logs - any errors in Flask output?

**Fix:**
- Ensure auction has exactly 3 consecutive passes
- Verify at least one real bid was made (not all passes)
- Check that `gamePhase` state changes to 'playing'

### Issue 2: Cards Not Clickable

**Symptoms:**
- Your turn but cards don't respond to clicks
- No hover effect on cards

**Check:**
1. Is `isUserTurn` prop true for PlayTable?
2. Is `isPlayingCard` state false?
3. Browser console for errors

**Fix:**
- Verify `playState.next_to_play === 'S'`
- Check that AI play loop isn't stuck
- Reload page and try again

### Issue 3: Illegal Play Error

**Symptoms:**
- Click card and get error message
- "Must follow suit if able"

**Check:**
- Do you have cards in the led suit?
- Are you trying to play wrong suit?

**Fix:**
- This is correct behavior!
- Play a card in the led suit
- Or verify you truly have a void in that suit

### Issue 4: Score Not Showing

**Symptoms:**
- All 13 tricks played but no score modal
- Game seems stuck

**Check:**
1. Browser console for errors
2. Network tab - is `/api/complete-play` being called?
3. Are all 13 tricks actually recorded?

**Fix:**
- Check `tricks_won` totals: N + E + S + W should equal 13
- Verify `totalTricks === 13` in code
- Check Flask logs for scoring calculation errors

### Issue 5: Backend Errors

**Symptoms:**
- HTTP 500 errors
- "Server error" messages

**Check:**
1. Flask terminal for Python traceback
2. Is `current_play_state` null?
3. Hand data available?

**Fix:**
- Restart Flask server
- Re-deal hands
- Check that `/api/start-play` was called successfully

---

## Testing Checklist

Use this checklist to verify full functionality:

### Bidding Phase
- [ ] Deal hands successfully
- [ ] Hand analysis displays correctly
- [ ] AI players bid automatically
- [ ] User can bid when it's their turn
- [ ] Bid legality is enforced
- [ ] Auction completes with 3 passes
- [ ] Feedback shows correct/recommended bids

### Play Transition
- [ ] Bidding completion detected automatically
- [ ] Transition message displays
- [ ] Play view loads within 2 seconds
- [ ] Contract displayed correctly

### Play Phase - Setup
- [ ] Opening leader is correct (LHO of declarer)
- [ ] Dummy position is correct (partner of declarer)
- [ ] Opening lead is made automatically
- [ ] Dummy hand revealed after opening lead
- [ ] Tricks won counters initialize to 0

### Play Phase - During
- [ ] AI players play automatically in sequence
- [ ] User can play when it's their turn
- [ ] Cards are clickable/hoverable
- [ ] Illegal plays are blocked
- [ ] Legal plays work correctly
- [ ] Cards removed from hand after playing
- [ ] Current trick displays all 4 cards
- [ ] Trick winner determined correctly
- [ ] Tricks won counter updates

### Play Phase - Completion
- [ ] All 13 tricks can be played
- [ ] Score modal appears automatically
- [ ] Contract shown correctly
- [ ] Tricks taken is accurate
- [ ] Result (made/down) is correct
- [ ] Score calculation is correct
- [ ] Close button works
- [ ] Can deal new hand after closing

### Edge Cases
- [ ] All passes (no contract) - should show message
- [ ] Doubled contracts work
- [ ] Vulnerable scoring correct
- [ ] Trump suit contracts work (not just NT)
- [ ] Slam contracts work (6 or 7 level)

---

## Performance Benchmarks

**Expected timings:**

- Deal hand: < 500ms
- AI bid: < 1s per bid
- Start play transition: < 2s
- AI card play: ~1s per card (with delay for visibility)
- Trick completion: < 100ms
- Score calculation: < 100ms
- Full game (bidding + 13 tricks): ~2-3 minutes

If you experience longer delays, check:
- Network connection
- Server performance (CPU/memory)
- Browser console for performance warnings

---

## Success Criteria

✅ **Gameplay is working correctly if:**

1. You can deal hands repeatedly without errors
2. Bidding completes and transitions to play automatically
3. All 13 tricks can be played without crashes
4. Score modal appears with correct results
5. You can repeat the cycle (deal, bid, play, score)

---

## Next Steps After Testing

Once gameplay is working:

1. **Test different scenarios:**
   - Various contracts (1NT, 3NT, 4♠, 6NT, etc.)
   - Doubled/redoubled contracts
   - All vulnerability conditions
   - Different declarers (N, E, S, W)

2. **Test edge cases:**
   - All passes (no contract)
   - Extremely unbalanced hands
   - Slam contracts
   - Long suits (8+ cards)

3. **Stress test:**
   - Play 10 hands in a row
   - Check for memory leaks
   - Verify state resets properly

4. **User experience:**
   - Is it fun to play?
   - Are explanations helpful?
   - Is the UI intuitive?
   - Any confusing moments?

---

## Getting Help

If you encounter issues:

1. **Check logs:**
   - Browser console (F12)
   - Flask server terminal
   - Network tab for failed requests

2. **Verify state:**
   - Use React DevTools to inspect state
   - Check `gamePhase`, `playState`, `isPlayingCard`

3. **Test standalone:**
   - Run `test_standalone_play.py` to verify backend
   - Use curl to test API endpoints directly

4. **Report issues:**
   - Note the exact steps to reproduce
   - Include error messages
   - Describe expected vs actual behavior

---

## 🎉 Enjoy Testing!

You now have a fully functional Bridge Bidding and Card Play application. Have fun testing and let me know if you encounter any issues!
