# How to View Convention Levels in the UI

## Quick Start (2 minutes)

### Step 1: Start the Backend Server

Open a terminal and run:

```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
python3 server.py
```

You should see:
```
✓ Learning path API endpoints registered
 * Running on http://127.0.0.1:5001
```

### Step 2: Open the Test Page

Open your web browser and go to:

**File URL:**
```
file:///Users/simonroy/Desktop/bridge_bidding_app/backend/test_conventions.html
```

**Or double-click the file:**
- Navigate to: `/Users/simonroy/Desktop/bridge_bidding_app/backend/`
- Double-click: `test_conventions.html`

---

## What You'll See

### Beautiful Convention Levels Page

The test page shows all 15 conventions organized into 3 levels:

#### ⭐ **Essential Conventions** (Green)
- Stayman
- Jacoby Transfers
- Weak Two Bids
- Takeout Doubles

#### 🎯 **Intermediate Conventions** (Blue)
- Blackwood (4NT)
- Negative Doubles
- Michaels Cuebid
- Unusual 2NT
- Strong 2♣

#### 👑 **Advanced Conventions** (Purple)
- Fourth Suit Forcing
- Splinter Bids
- New Minor Forcing
- Responsive Doubles
- Lebensohl
- Gerber (4♣)

### Each Convention Card Shows:
- **Name** - Convention name
- **Frequency Badge** - How often it's used (Very High, High, Medium, Low)
- **Complexity Badge** - Difficulty level (Low, Medium, High, Very High)
- **Category Badge** - Type (1NT System, Competitive Bidding, Slam Bidding, etc.)
- **Short Description** - Quick summary
- **Practice Requirements** - Number of hands needed to master
- **Passing Threshold** - Accuracy required (80% or 85%)
- **Learning Time** - Estimated minutes to learn

---

## Test the API Directly

You can also test the API endpoints directly in your browser:

### View All Conventions by Level:
```
http://localhost:5001/api/conventions/by-level
```

### View Specific Convention:
```
http://localhost:5001/api/conventions/stayman
```

### View Skill Tree:
```
http://localhost:5001/api/skill-tree
```

### Check What's Unlocked (for test user):
```
http://localhost:5001/api/conventions/unlocked?user_id=1
```

---

## Troubleshooting

### "Cannot GET /api/conventions/by-level"

**Problem:** Server not running or endpoints not registered

**Solution:**
1. Make sure you're in the backend directory
2. Check that server.py has the import and registration:
   ```python
   from engine.learning.learning_path_api import register_learning_endpoints
   register_learning_endpoints(app)
   ```
3. Restart the server

### "Error loading conventions" in browser

**Problem:** CORS or server not accessible

**Solution:**
1. Make sure server is running on port 5001
2. Check browser console (F12) for detailed error
3. Try accessing API URL directly: http://localhost:5001/api/conventions/by-level

### Database not initialized

**Problem:** Tables don't exist

**Solution:**
```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
python3 database/init_convention_data.py
```

---

## Next: Integrate with React Frontend

To see this in your actual React app, you'll need to:

1. **Create React Components** (see CONVENTION_LEVELS_QUICKSTART.md)
   - ConventionLearningPath.js
   - ConventionLevelView.js
   - ConventionCard.js

2. **Add Route to App.js**
   ```javascript
   <Route path="/learn-conventions">
     <ConventionLearningPath />
   </Route>
   ```

3. **Add Navigation Link**
   ```javascript
   <Link to="/learn-conventions">Learn Conventions</Link>
   ```

For now, the HTML test page lets you see all the data working perfectly!

---

## Quick Demo Script

Want to show someone? Here's a 30-second demo:

1. **Start server:** `python3 server.py` in backend folder
2. **Open test page:** Double-click `test_conventions.html`
3. **Point out:**
   - "Here are all 15 conventions organized by difficulty"
   - "Essential (green) are must-learn basics"
   - "Intermediate (blue) add competitive tools"
   - "Advanced (purple) are expert techniques"
   - "Each card shows frequency, complexity, and practice requirements"
4. **Open API in browser:** Show http://localhost:5001/api/conventions/by-level
   - "This is the raw JSON data the frontend will use"

---

**Created:** October 11, 2025
**Test Page:** `/backend/test_conventions.html`
**Server:** http://localhost:5001
