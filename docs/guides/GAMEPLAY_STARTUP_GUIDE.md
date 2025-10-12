# Gameplay Application Startup Guide

**Purpose:** Step-by-step instructions for starting and testing the Bridge Bidding App with the new UI improvements
**Last Updated:** 2025-10-12
**Audience:** Users and developers testing the gameplay features

---

## 🚀 Quick Start (3 Steps)

### 1. Start the Backend Server

```bash
# Open Terminal 1
cd /Users/simonroy/Desktop/bridge_bidding_app/backend

# Activate virtual environment
source venv/bin/activate

# Start Flask server
python server.py
```

**Expected output:**
```
 * Serving Flask app 'server'
 * Debug mode: on
WARNING: This is a development server...
 * Running on http://127.0.0.1:5001
Press CTRL+C to quit
```

✅ **Success indicator:** You see "Running on http://127.0.0.1:5001"

---

### 2. Start the Frontend React App

```bash
# Open Terminal 2 (new terminal window/tab)
cd /Users/simonroy/Desktop/bridge_bidding_app/frontend

# Install dependencies (if first time)
npm install

# Start React development server
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view bridge-bidding-app in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

webpack compiled with 0 warnings
```

✅ **Success indicator:** Browser automatically opens to http://localhost:3000

---

### 3. Test the Application

Your browser should automatically open. If not, navigate to:
```
http://localhost:3000
```

You should see the Bridge Bidding App interface!

---

## 🎮 Testing the New Turn Indicator

### What to Look For:

**1. Start a New Hand:**
- Click "New Hand" or "Start Game" button
- Bidding phase begins

**2. During Bidding:**
- Watch for the **Turn Indicator** at the top
- When it's your turn (South), you'll see:
  ```
  ┌──────────────────────────────────┐
  │   ⏰  YOUR TURN!  ⏰              │
  │   (Select a bid)                 │
  └──────────────────────────────────┘
  ```
  - Cyan/blue pulsing border
  - Large text
  - Action hint below

- When it's AI's turn:
  ```
  ┌──────────────────────────────────┐
  │      North's Turn                │
  │   (Waiting for North...)         │
  └──────────────────────────────────┘
  ```
  - Gray border
  - Player name
  - Waiting message

**3. During Card Play:**
- After bidding completes, play phase begins
- Same turn indicator, but says "Select a card to play"
- Position labels show animated arrow (◀) next to active player:
  ```
  North ◀ (Dummy)
  East
  South (You) ◀
  West
  ```

**4. Responsive Testing:**
- Resize browser window
- Mobile view (< 768px): Compact version, no clock icons
- Tablet (768-900px): Medium size
- Desktop (> 900px): Full size with all features

**5. Accessibility Testing:**
- Tab through interface with keyboard
- Turn indicator should be announced by screen readers
- Animations should be smooth (60fps)

---

## 🔧 Troubleshooting

### Backend Won't Start

**Problem:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

---

**Problem:** Port 5001 already in use

**Solution:**
```bash
# Find process using port 5001
lsof -ti:5001

# Kill the process (replace PID with actual number)
kill -9 <PID>

# Or use different port by editing server.py:
# Change: app.run(debug=True, port=5001)
# To: app.run(debug=True, port=5002)
```

---

### Frontend Won't Start

**Problem:** `npm: command not found`

**Solution:**
Install Node.js and npm:
```bash
# Check if Node.js is installed
node --version
npm --version

# If not installed, download from https://nodejs.org/
# Or use Homebrew:
brew install node
```

---

**Problem:** Dependency errors

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

---

**Problem:** Port 3000 already in use

**Solution:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or run on different port
PORT=3001 npm start
```

---

### Turn Indicator Not Showing

**Problem:** Component doesn't appear

**Check:**
```bash
# Verify files exist
ls frontend/src/components/play/TurnIndicator.js
ls frontend/src/components/play/TurnIndicator.css

# Check browser console for errors (F12 or Cmd+Option+I)
# Look for import/module errors
```

**Solution:**
- Ensure components directory exists:
  ```bash
  mkdir -p frontend/src/components/play
  ```
- Restart frontend dev server (Ctrl+C, then `npm start`)
- Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)

---

**Problem:** CSS not applying (no pulsing animation)

**Check:**
```bash
# Verify CSS file exists
ls frontend/src/components/play/TurnIndicator.css

# Check if CSS variables are defined
grep "color-info" frontend/src/PlayComponents.css
```

**Solution:**
- Hard refresh browser (Cmd+Shift+R)
- Check browser console for CSS errors
- Verify CSS import in TurnIndicator.js

---

### API Connection Issues

**Problem:** Frontend can't reach backend

**Symptoms:**
- Bidding doesn't work
- Error messages in browser console
- "Failed to fetch" errors

**Solution:**
```bash
# Check backend is running
curl http://localhost:5001/api/deal

# Should return JSON with hand data
# If not, backend isn't running or has crashed

# Check backend logs in Terminal 1
# Look for error messages
```

**Fix CORS issues (if needed):**
```python
# In backend/server.py, ensure CORS is configured:
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Should be present
```

---

## 📱 Testing on Different Devices

### Desktop (Recommended First)
- Full features visible
- Easiest to debug
- Best performance

**Browser:** Chrome, Firefox, Safari, or Edge
**Screen size:** 1200px+ width

---

### Tablet
- Medium-sized UI
- Touch-friendly

**Testing:**
1. Resize browser window to ~768-900px width
2. Or use browser dev tools:
   - Chrome: F12 → Toggle device toolbar → Select iPad
   - Safari: Develop → Enter Responsive Design Mode

---

### Mobile Phone
- Compact UI
- Icons hidden on small screens
- Touch targets optimized

**Testing:**
1. Resize browser to ~375-480px width
2. Or use dev tools device emulation:
   - Select iPhone 12/13/14
   - Test both portrait and landscape

**Real device testing:**
1. Get your local IP:
   ```bash
   ipconfig getifaddr en0  # macOS
   # or
   ifconfig | grep inet    # Linux
   ```

2. On your phone's browser, navigate to:
   ```
   http://YOUR_IP_ADDRESS:3000
   ```
   Example: `http://192.168.1.100:3000`

---

## 🎯 Step-by-Step Gameplay Test

### Full Test Scenario:

**1. Start Application** (see Quick Start above)

**2. Begin New Hand:**
- Click "New Hand" button
- Hand is dealt
- Bidding phase begins

**3. Bidding Phase:**
- [ ] Turn indicator shows at top
- [ ] When your turn: "YOUR TURN!" with pulsing border
- [ ] When AI turn: "{Player}'s Turn" with static border
- [ ] Make a bid (e.g., "1♠")
- [ ] Watch AI players bid
- [ ] Continue until auction completes (3 passes)

**4. Play Phase Begins:**
- [ ] Turn indicator changes to "Select a card to play"
- [ ] Opening leader (left of declarer) plays first card
- [ ] Dummy's hand is revealed
- [ ] Turn indicator updates

**5. Card Play:**
- [ ] When your turn, indicator pulses
- [ ] Click a card to play
- [ ] Watch AI players play
- [ ] Turn indicator updates for each player
- [ ] Complete all 13 tricks

**6. Hand Complete:**
- [ ] Score modal appears
- [ ] Shows final result
- [ ] Can start new hand

---

## 🐛 Known Issues & Workarounds

### Issue: React Hot Reload Breaks After Changes

**Symptoms:** Changes don't appear, need full restart

**Workaround:**
```bash
# Stop frontend (Ctrl+C)
npm start
```

---

### Issue: Backend Crashes During Play

**Symptoms:** 500 errors, backend terminal shows traceback

**Workaround:**
```bash
# Check backend/server_log.txt for errors
tail -f backend/server_log.txt

# Restart backend
cd backend
source venv/bin/activate
python server.py
```

---

### Issue: Animations Stuttering

**Symptoms:** Choppy pulsing animation

**Causes:**
- Browser performance
- Too many tabs open
- CPU intensive tasks running

**Solutions:**
- Close other tabs
- Use Chrome (best performance)
- Check Activity Monitor/Task Manager

---

## 📊 Performance Monitoring

### Browser DevTools:

**Open DevTools:**
- Chrome/Edge: F12 or Cmd+Option+I
- Safari: Cmd+Option+I (enable in Develop menu first)

**Performance Tab:**
1. Click Record
2. Play a few hands
3. Stop recording
4. Look for:
   - FPS (should be 60)
   - Long tasks (should be < 50ms)
   - Memory leaks (RAM should stabilize)

**Console Tab:**
- Check for errors (red)
- Check for warnings (yellow)
- Look for React warnings

**Network Tab:**
- API calls should be < 200ms
- No failed requests (red)

---

## 🎨 Visual Checklist

When testing, verify:

### Turn Indicator (Main)
- [ ] Appears at top of screen
- [ ] Text is large and readable
- [ ] Border pulses smoothly when your turn
- [ ] Shows correct player name
- [ ] Action hint is appropriate ("Select a bid" or "Select a card")
- [ ] Clock icons appear on desktop
- [ ] Clock icons disappear on mobile

### Compact Indicators (Position Labels)
- [ ] Arrow (◀) appears next to active player
- [ ] Arrow animates (pulses/moves)
- [ ] Arrow disappears when player inactive
- [ ] Works for all 4 positions (N, E, S, W)

### CSS Variables
- [ ] Colors match design system (cyan for info, green for success, red for errors)
- [ ] Spacing is consistent (8px grid)
- [ ] Typography is sized correctly
- [ ] No hardcoded colors visible

### Responsive Design
- [ ] Desktop: Full size, all features
- [ ] Tablet: Scaled down appropriately
- [ ] Mobile: Compact, readable
- [ ] Landscape orientation works

### Accessibility
- [ ] Screen reader announces turns (test with VoiceOver/NVDA)
- [ ] Tab key navigates properly
- [ ] Focus indicators visible
- [ ] Sufficient color contrast
- [ ] Text is readable at all sizes

---

## 📝 Logging & Debugging

### Enable Verbose Logging:

**Frontend (React):**
```javascript
// In browser console (F12)
localStorage.setItem('debug', 'true')

// Reload page
location.reload()

// Check console for detailed logs
```

**Backend (Flask):**
```python
# In server.py, debug mode already enabled:
app.run(debug=True, port=5001)

# Check terminal for request logs
# Check backend/server_log.txt for detailed logs
```

### Console Debugging:

**Useful commands in browser console:**
```javascript
// Check if TurnIndicator is rendering
document.querySelector('.turn-indicator')

// Check CSS variables
getComputedStyle(document.documentElement).getPropertyValue('--color-info')

// Check React component tree (if React DevTools installed)
// Chrome extension: React Developer Tools
```

---

## 🔄 Restart Everything (Clean Slate)

If things are broken and you want to start fresh:

```bash
# Terminal 1: Stop backend (Ctrl+C)

# Terminal 2: Stop frontend (Ctrl+C)

# Clean restart backend:
cd backend
source venv/bin/activate
python server.py

# Clean restart frontend (in new terminal):
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start

# Clear browser cache
# Chrome: Cmd+Shift+Delete → Clear cached images and files
# Safari: Cmd+Option+E
```

---

## 📖 Related Documentation

- **UI/UX Standards:** `.claude/UI_UX_DESIGN_STANDARDS.md`
- **Implementation Plan:** `docs/features/INTERFACE_IMPROVEMENTS_PLAN.md`
- **Turn Indicator Docs:** `TURN_INDICATOR_IMPLEMENTATION_COMPLETE.md`
- **Local Testing Guide:** `docs/guides/GAMEPLAY_LOCAL_TESTING_GUIDE.md`
- **Project Context:** `.claude/PROJECT_CONTEXT.md`

---

## ✅ Success Checklist

Before reporting success, verify:

- [ ] Backend starts without errors
- [ ] Frontend compiles without warnings
- [ ] Browser opens to http://localhost:3000
- [ ] New hand can be started
- [ ] Bidding works (can make bids)
- [ ] Turn indicator appears
- [ ] Turn indicator pulses when your turn
- [ ] Turn indicator shows AI player names
- [ ] Compact arrows appear next to active players
- [ ] Card play works (can play cards)
- [ ] Hand completes successfully
- [ ] Can start multiple hands in succession
- [ ] No console errors
- [ ] Responsive design works (resize window)

---

## 🆘 Getting Help

### Check These First:
1. Browser console (F12) for errors
2. Backend terminal for Python errors
3. Frontend terminal for React errors
4. This guide's Troubleshooting section

### Common Error Messages:

**"Module not found"**
→ Run `npm install` (frontend) or `pip install -r requirements.txt` (backend)

**"Port already in use"**
→ Kill process on that port (see Troubleshooting)

**"Failed to fetch"**
→ Backend not running or CORS issue

**"Cannot read property of undefined"**
→ React error, check browser console for stack trace

---

## 🎉 You're Ready!

If you've followed this guide and verified the success checklist, you should now have:

✅ Backend server running on http://localhost:5001
✅ Frontend app running on http://localhost:3000
✅ Turn Indicator showing whose turn it is
✅ Smooth pulsing animations
✅ Responsive design working
✅ Full bidding and card play functionality

**Enjoy testing the new UI improvements!** 🃏♠️♥️♣️♦️

---

**Next Steps:**
- Test different bidding scenarios
- Try playing on mobile device
- Test accessibility features
- Provide feedback on user experience
- Continue to Contract Goal Tracker implementation

---

**Last Updated:** 2025-10-12
**Version:** 1.0
**Tested On:** macOS, Chrome 120+, Safari 17+, Firefox 120+
