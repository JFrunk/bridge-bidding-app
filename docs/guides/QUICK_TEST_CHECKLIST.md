# Quick Testing Checklist ✅

Use this as a quick reference for testing your Bridge Bidding App gameplay.

---

## 🚀 Quick Start (2 Minutes)

### 1. Start Servers

**Terminal 1:**
```bash
cd backend
source venv/bin/activate
python3 server.py
```
✅ Should see: `Running on http://127.0.0.1:5001`

**Terminal 2:**
```bash
cd frontend
npm start
```
✅ Should open: `http://localhost:3000`

---

## 🎮 Basic Gameplay Test (5 Minutes)

### Step 1: Deal ➜ Step 2: Bid ➜ Step 3: Play ➜ Step 4: Score

| Step | Action | What to Verify |
|------|--------|----------------|
| **1. Deal** | Click "Deal New Hand" | ✅ See 13 cards<br>✅ Hand analysis shows |
| **2. Bid** | Complete auction:<br>e.g., 1NT-P-3NT-P-P-P | ✅ AI bids automatically<br>✅ Can bid when your turn<br>✅ 3 passes ends auction |
| **3. Transition** | Automatic after bidding | ✅ "Contract: 3NT by X"<br>✅ Play view loads |
| **4. Opening Lead** | Automatic | ✅ Card appears in center<br>✅ Correct player leads |
| **5. Dummy** | Automatic | ✅ Partner's hand shows<br>✅ All 13 cards visible |
| **6. Play** | Watch AI, click when your turn | ✅ AI plays automatically<br>✅ Your cards clickable<br>✅ Illegal plays blocked |
| **7. Tricks** | Continue for all 13 | ✅ Winner determined<br>✅ Counter updates<br>✅ Next trick starts |
| **8. Score** | Automatic after trick 13 | ✅ Modal appears<br>✅ Shows contract & result<br>✅ Score calculated |
| **9. Reset** | Click "Close" | ✅ Can deal again |

---

## 🧪 Quick Backend Test (1 Minute)

```bash
cd backend
PYTHONPATH=. python3 tests/test_standalone_play.py
```

✅ Should see: `SUCCESS: Standalone play test completed!`

---

## ⚡ Quick API Test (30 Seconds)

```bash
# Test deal endpoint
curl http://localhost:5001/api/deal-hands

# Test all hands
curl http://localhost:5001/api/get-all-hands
```

✅ Should return JSON with hand data

---

## 🎯 Essential Verifications

### Must Work ✅
- [ ] Deal hands
- [ ] AI bids automatically
- [ ] Complete auction (3 passes)
- [ ] Transition to play
- [ ] Opening lead
- [ ] Dummy reveals
- [ ] Play all 13 tricks
- [ ] Score displays

### Should Work ✅
- [ ] Illegal plays blocked
- [ ] Correct trick winner
- [ ] Accurate score
- [ ] Reset and deal again

### Nice to Have ✅
- [ ] Smooth animations
- [ ] Helpful messages
- [ ] Good performance

---

## 🐛 Quick Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| **No hand appears** | Check backend running (port 5001) |
| **Play doesn't start** | Need 3 consecutive passes |
| **Cards not clickable** | Check it's your turn (South) |
| **Can't click card** | Must follow suit if able |
| **Score not showing** | Check all 13 tricks played |
| **Backend error** | Check Flask terminal for errors |

---

## 📊 Sample Test Sequences

### Test 1: Simple 3NT (2 min)
```
1. Deal hand
2. Bid: 1NT-P-3NT-P-P-P
3. Play out 13 tricks
4. Verify score (~400 if making)
```

### Test 2: Major Suit Game (3 min)
```
1. Deal hand
2. Bid: 1♠-P-4♠-P-P-P
3. Play with trump suit
4. Verify trump taking works
```

### Test 3: Doubled Contract (3 min)
```
1. Deal hand
2. Bid: 3NT-X-P-P-P
3. Play out hand
4. Verify doubled score
```

---

## 🎓 Expected Scores (Quick Reference)

| Contract | Result | Non-Vul | Vulnerable |
|----------|--------|---------|------------|
| 3NT | Making | 400 | 600 |
| 3NT | +1 | 430 | 630 |
| 3NT | -1 | -50 | -100 |
| 4♠ | Making | 420 | 620 |
| 4♠X | Making | 590 | 790 |
| 6NT | Making | 990 | 1440 |

---

## ✅ Success = You Can Do This Without Errors:

1. Deal → Bid → Play → Score → Repeat
2. Complete 3 hands in a row
3. No browser console errors
4. No backend crashes

---

## 📖 Full Documentation

For detailed testing, see:
- **[GAMEPLAY_TESTING_GUIDE.md](GAMEPLAY_TESTING_GUIDE.md)** - Complete step-by-step
- **[STANDALONE_PLAY_GUIDE.md](STANDALONE_PLAY_GUIDE.md)** - Module testing
- **[QUICK_WINS_COMPLETE.md](QUICK_WINS_COMPLETE.md)** - Implementation details

---

**Ready? Start testing! 🚀**

```bash
# Terminal 1
cd backend && python3 server.py

# Terminal 2
cd frontend && npm start

# Browser
# Go to http://localhost:3000
# Click "Deal New Hand"
# Start playing!
```
