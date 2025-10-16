# 🚀 Quick Start - Bridge Bidding App

## Start in 3 Steps:

### 1️⃣ Backend (Terminal 1)
```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
source venv/bin/activate
python server.py
```
✅ Should see: `Running on http://127.0.0.1:5001`

---

### 2️⃣ Frontend (Terminal 2)
```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/frontend
npm start
```
✅ Should see: Browser opens to `http://localhost:3000`

---

### 3️⃣ Test!
- Browser opens automatically
- Click "New Hand" to start
- Watch for **Turn Indicator** at top with pulsing animation
- Your turn shows: ⏰ **YOUR TURN!** ⏰

---

## 🐛 Quick Fixes

**Backend won't start?**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

**Frontend won't start?**
```bash
cd frontend
npm install
npm start
```

**Port in use?**
```bash
lsof -ti:5001 | xargs kill -9  # Kill backend port
lsof -ti:3000 | xargs kill -9  # Kill frontend port
```

---

## 📚 Full Guide

See: [`docs/guides/GAMEPLAY_STARTUP_GUIDE.md`](docs/guides/GAMEPLAY_STARTUP_GUIDE.md)

---

## ✨ New Features to Test

- **Turn Indicator:** Large banner showing whose turn (pulsing when yours!)
- **Compact Arrows:** Animated ◀ next to active player
- **Action Hints:** "Select a card to play" / "Select a bid"
- **Responsive Design:** Resize window to test mobile/tablet views
- **Accessibility:** Tab navigation, screen reader support

---

**Need help?** Check the full startup guide above!
