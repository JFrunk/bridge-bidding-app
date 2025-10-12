# Gameplay Local Testing Guide

## Quick Start (5 Minutes)

### Option 1: VS Code Tasks (Easiest)

If you're in VS Code, you can use the built-in tasks:

1. **Press:** `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. **Type:** "Tasks: Run Task"
3. **Select:** "Start Gameplay Testing 🎲" (starts both backend and frontend)

Or start them separately:
- "Start Gameplay Backend 🎮" - Backend only
- "Start Gameplay Frontend 🎯" - Frontend only

### Option 2: Terminal Commands (Manual)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

**Access:** Open browser to http://localhost:3000

---

## Complete Testing Workflow

### Step 1: Start Backend Server

```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
source venv/bin/activate
python server.py
```

**Expected Output:**
```
 * Serving Flask app 'server'
 * Debug mode: on
WARNING: This is a development server.
 * Running on http://127.0.0.1:5001
```

**Verify Backend:**
```bash
# In another terminal
curl http://localhost:5001/api/ai-difficulties
```

Should return JSON with 4 AI difficulty levels.

---

### Step 2: Start Frontend

```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/frontend
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view bridge-bidding-app in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

**Browser opens automatically to:** http://localhost:3000

---

### Step 3: Test Bidding Phase

1. **Click "Deal New Hand"** or select a scenario
2. **Complete the bidding:**
   - South (you) makes bids
   - AI opponents bid automatically
   - Continue until 3 consecutive passes
3. **Final contract displays** (e.g., "4♠ by South")

---

### Step 4: Test Card Play Phase

Once bidding completes, card play begins:

#### 4.1 Opening Lead (Defender)
- AI makes opening lead automatically
- Card appears on table

#### 4.2 Dummy Revealed
- Dummy's hand (North if you're South) displays face-up
- You can now see partner's cards

#### 4.3 Play Cards
- **Your Turn:** Click a card from your hand
- **AI Turn:** AI plays automatically after short delay
- Continue for all 13 tricks

#### 4.4 Scoring
- Final score displays when all tricks played
- Shows tricks won by declarer vs defenders
- Indicates if contract made/defeated

---

## Testing Different AI Difficulties

### Method 1: Settings UI (When Implemented)

Once frontend integration is complete:
1. Go to Settings menu
2. Select AI Difficulty:
   - Beginner (fastest, basic)
   - Intermediate (tactical)
   - Advanced (recommended) ⭐
   - Expert (strongest, slower)

### Method 2: API Testing (Current)

Use curl to change AI before playing:

```bash
# Set to Advanced (recommended)
curl -X POST http://localhost:5001/api/set-ai-difficulty \
  -H "Content-Type: application/json" \
  -d '{"difficulty":"advanced"}'

# Verify change
curl http://localhost:5001/api/ai-difficulties
```

Then play a hand and observe AI quality difference.

### Method 3: Python Script

```bash
cd backend
source venv/bin/activate
python test_ai_integration.py
```

This tests all difficulty levels programmatically.

---

## Testing Specific Scenarios

### Test Scenario 1: Simple Notrump

```bash
# Start backend
cd backend && source venv/bin/activate && python server.py

# In another terminal, load specific deal
curl -X POST http://localhost:5001/api/load-scenario \
  -H "Content-Type: application/json" \
  -d '{"name":"Simple 3NT"}'
```

Then access frontend and play the hand.

### Test Scenario 2: Suit Contract

Load a suit contract scenario (4♠, 4♥, etc.) and test:
- Trump management
- Ruffing
- Drawing trumps
- Communication

### Test Scenario 3: Defensive Play

Test from defender's perspective:
- Opening leads
- Defensive signaling
- Setting contracts

---

## Testing Without Frontend (Backend Only)

### Option 1: Standalone Play Module

```bash
cd backend
source venv/bin/activate

# Test minimax AI directly
PYTHONPATH=. python3 engine/play/ai/minimax_ai.py

# Test evaluation function
PYTHONPATH=. python3 engine/play/ai/evaluation.py
```

### Option 2: Test Helpers

```python
# In Python interactive shell
cd backend
source venv/bin/activate
python3

from tests.play_test_helpers import *
from engine.play.ai.minimax_ai import MinimaxPlayAI

# Create a test deal
deal = create_test_deal(
    north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
    east="♠543 ♥543 ♦543 ♣5432",
    south="♠876 ♥876 ♦8762 ♣876",
    west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
)

# Create play state
state = create_play_scenario("3NT by N", deal, "None")

# Test AI
ai = MinimaxPlayAI(max_depth=3)
card = ai.choose_card(state, 'E')
print(f"AI chose: {card.rank}{card.suit}")

# Get statistics
stats = ai.get_statistics()
print(f"Nodes searched: {stats['nodes']}")
print(f"Time: {stats['time']}s")
```

### Option 3: Run Benchmarks

```bash
cd backend
source venv/bin/activate

# Quick test on beginner deals
PYTHONPATH=. python3 benchmarks/benchmark_ai.py --set beginner --depth 2 3

# Full benchmark (all deals)
PYTHONPATH=. python3 benchmarks/benchmark_ai.py --set all --depth 2 3

# Specific deal set
PYTHONPATH=. python3 benchmarks/benchmark_ai.py --set notrump_only --depth 3
```

---

## Testing Play Endpoints Directly

### 1. Start a Play Session

```bash
# After bidding completes, start play
curl -X POST http://localhost:5001/api/start-play \
  -H "Content-Type: application/json" \
  -d '{
    "contract": "3NT by S",
    "declarer": "S"
  }'
```

### 2. Get AI Play

```bash
curl -X POST http://localhost:5001/api/get-ai-play
```

**Response:**
```json
{
  "card": {"rank": "K", "suit": "♣"},
  "position": "W",
  "trick_complete": false,
  "next_to_play": "N",
  "explanation": "W played K♣"
}
```

### 3. Player Plays Card

```bash
curl -X POST http://localhost:5001/api/play-card \
  -H "Content-Type: application/json" \
  -d '{
    "card": {"rank": "A", "suit": "♣"},
    "position": "N"
  }'
```

### 4. Get Play State

```bash
curl http://localhost:5001/api/play-state
```

### 5. Get AI Statistics

```bash
curl http://localhost:5001/api/ai-statistics
```

---

## Common Testing Scenarios

### Scenario A: Complete Full Hand

1. Start backend and frontend
2. Deal a hand
3. Complete bidding (e.g., reach 3NT)
4. Play all 13 tricks
5. Check final score
6. Verify AI made reasonable plays

### Scenario B: Test Different Difficulties

1. Start backend
2. Set AI to "beginner"
3. Play a hand, note AI quality
4. Set AI to "advanced"
5. Play same/similar hand
6. Compare AI decision quality

### Scenario C: Test Performance

1. Set AI to "expert" (depth 4)
2. Play a hand
3. Check `/api/ai-statistics` after each move
4. Verify times are acceptable (<50ms)
5. Check nodes/second throughput

### Scenario D: Test Edge Cases

1. **Revoke (illegal play):** Try to play card not following suit
2. **Out of turn:** Try to play when not your turn
3. **Invalid card:** Try to play card not in hand
4. **All pass immediately:** Pass on opening bid
5. **Maximum bidding:** Bid to 7NT

---

## Troubleshooting

### Backend Won't Start

**Error:** `Address already in use`
```bash
# Find and kill process on port 5001
lsof -ti:5001 | xargs kill -9

# Or use a different port
FLASK_RUN_PORT=5002 python server.py
```

**Error:** `ModuleNotFoundError`
```bash
# Make sure venv is activated
source venv/bin/activate

# Check Python path
echo $PYTHONPATH

# Install dependencies
pip install -r requirements.txt
```

### Frontend Won't Start

**Error:** `Cannot find module`
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
```

**Error:** `Port 3000 already in use`
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
PORT=3001 npm start
```

### API Calls Failing

**Error:** `CORS policy`
- Make sure CORS is enabled in backend (should be by default)
- Check browser console for exact error

**Error:** `Connection refused`
- Verify backend is running on http://localhost:5001
- Check no firewall blocking

**Error:** `404 Not Found`
- Verify endpoint URL is correct
- Check server logs for errors

### AI Not Playing

**Check:**
1. Is play state initialized? (`/api/play-state` should return valid state)
2. Is it AI's turn? (`next_to_play` should not be user's position)
3. Any server errors? (check backend terminal output)

### Cards Not Visible

**Check:**
1. Is dummy revealed? (should reveal after opening lead)
2. Are you looking at correct position? (South is user)
3. Browser console errors?

---

## Performance Benchmarking

### Quick Performance Test

```bash
cd backend
source venv/bin/activate

# Test each difficulty level
for depth in 2 3 4; do
  echo "Testing depth $depth..."
  time PYTHONPATH=. python3 benchmarks/benchmark_ai.py \
    --set beginner \
    --depth $depth
done
```

### Detailed Performance Analysis

```bash
# Full benchmark with profiling
PYTHONPATH=. python3 -m cProfile -o profile.stats \
  benchmarks/benchmark_ai.py --set all --depth 3

# Analyze results
python3 -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

---

## Automated Testing

### Unit Tests

```bash
cd backend
source venv/bin/activate

# All play tests
PYTHONPATH=. python3 -m pytest tests/play/ -v

# Specific test file
PYTHONPATH=. python3 -m pytest tests/play/test_minimax_ai.py -v

# With coverage
PYTHONPATH=. python3 -m pytest tests/play/ --cov=engine/play/ai
```

### Integration Tests

```bash
cd backend
source venv/bin/activate

# Make sure server is running first
python server.py &

# Run integration tests
sleep 2  # Wait for server to start
python test_ai_integration.py

# Kill server
kill %1
```

---

## Development Workflow

### Typical Development Session

```bash
# Terminal 1 - Backend with auto-reload
cd backend
source venv/bin/activate
FLASK_DEBUG=1 python server.py

# Terminal 2 - Frontend with hot reload
cd frontend
npm start

# Terminal 3 - Testing
cd backend
source venv/bin/activate
# Run tests as needed
PYTHONPATH=. python3 -m pytest tests/play/ -v
```

### Making Changes

1. **Edit code** (e.g., improve evaluation function)
2. **Run unit tests** to verify no regression
3. **Run benchmarks** to measure improvement
4. **Test manually** in browser
5. **Check performance** hasn't degraded

---

## Testing Checklist

### Basic Functionality ✅
- [ ] Backend starts without errors
- [ ] Frontend starts and connects to backend
- [ ] Can deal a hand
- [ ] Can complete bidding
- [ ] Can play cards in play phase
- [ ] Tricks are counted correctly
- [ ] Final score displays

### AI Testing ✅
- [ ] Can get AI difficulties list
- [ ] Can set AI difficulty
- [ ] AI plays legal cards
- [ ] AI follows suit when required
- [ ] Different difficulties show different quality
- [ ] Statistics available for minimax AIs

### Edge Cases ✅
- [ ] Cannot play out of turn
- [ ] Cannot play illegal cards
- [ ] Cannot play cards not in hand
- [ ] Trick winner determined correctly
- [ ] Trump suits handled properly
- [ ] Scoring calculated correctly

### Performance ✅
- [ ] Beginner AI instant (<0.1ms)
- [ ] Intermediate AI fast (<5ms)
- [ ] Advanced AI responsive (<10ms)
- [ ] Expert AI acceptable (<30ms)
- [ ] No memory leaks over multiple hands
- [ ] Server handles concurrent requests

---

## VS Code Tasks Reference

Available tasks (press `Cmd+Shift+P` → "Tasks: Run Task"):

**Gameplay:**
- `Start Gameplay Backend 🎮` - Backend server
- `Start Gameplay Frontend 🎯` - React app
- `Start Gameplay Testing 🎲` - Both together
- `Test Standalone Play 🧪` - Run play tests
- `Test Contract Parser 📋` - Test utilities
- `Test Play Helpers 🛠️` - Test helpers

**Bidding (Original):**
- `Start Backend Bidding 🐍` - Bidding backend
- `Start Frontend Bidding 🖥️` - Bidding frontend
- `Start Bidding Project (All) 🎴` - Both together
- `Run All Tests 🧪` - Full test suite
- `Test Opening Bids 🃏` - Specific tests

---

## Quick Reference

### Essential Commands

```bash
# Start everything (in separate terminals)
cd backend && source venv/bin/activate && python server.py
cd frontend && npm start

# Test AI integration
cd backend && python test_ai_integration.py

# Run benchmarks
cd backend && PYTHONPATH=. python3 benchmarks/benchmark_ai.py --set all --depth 3

# Run unit tests
cd backend && PYTHONPATH=. python3 -m pytest tests/play/ -v
```

### Important URLs

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:5001
- **API Docs:** See PHASE2_API_INTEGRATION.md

### Key Files

- **Backend Server:** `backend/server.py`
- **Minimax AI:** `backend/engine/play/ai/minimax_ai.py`
- **Test Deals:** `backend/benchmarks/curated_deals.json`
- **Integration Tests:** `backend/test_ai_integration.py`

---

## Getting Help

### Documentation

- **Phase 2 Complete:** `PHASE2_COMPLETE.md`
- **API Reference:** `PHASE2_API_INTEGRATION.md`
- **Quick Start:** `QUICK_TEST_CHECKLIST.md`
- **Gameplay Guide:** `GAMEPLAY_TESTING_GUIDE.md`

### Debugging

1. **Check server logs** in terminal running `python server.py`
2. **Check browser console** for frontend errors (F12 → Console)
3. **Test API directly** with curl to isolate issues
4. **Run unit tests** to verify components work

### Common Issues

**Issue:** AI plays too slowly
**Solution:** Use lower difficulty (Intermediate or Beginner)

**Issue:** AI plays poorly
**Solution:** Use higher difficulty (Advanced or Expert)

**Issue:** Tests failing
**Solution:** Check hand card counts (must be exactly 13 each)

---

**Ready to test!** Start with the Quick Start section and work through the Complete Testing Workflow. 🚀
