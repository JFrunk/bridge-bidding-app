# App.js Minimal Patch for Session Support

This document shows the **minimal changes** needed to add session support to App.js without a full refactor.

## Step 1: Add Import

**Location:** Top of `src/App.js` (around line 13-14)

**Add this line:**
```javascript
import { getSessionHeaders } from './utils/sessionHelper';
```

**Context:**
```javascript
import DDSStatusIndicator from './components/DDSStatusIndicator';
import AIDifficultySelector from './components/AIDifficultySelector';
import { getSessionHeaders } from './utils/sessionHelper';  // ADD THIS

// API URL configuration - uses environment variable in production
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';
```

---

## Step 2: Update Fetch Calls

Search for every `fetch(` in App.js and add `...getSessionHeaders()` to the headers.

### Pattern to Find:
```javascript
headers: {
  'Content-Type': 'application/json'
}
```

### Replace With:
```javascript
headers: {
  'Content-Type': 'application/json',
  ...getSessionHeaders()
}
```

---

## Specific Changes Needed

### Change 1: fetchScenarios (around line 126)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/scenarios`);
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/scenarios`, {
  headers: { ...getSessionHeaders() }
});
```

---

### Change 2: loadScenarioRequest (around line 182)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/load-scenario`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: scenarioName })
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/load-scenario`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify({ name: scenarioName })
});
```

---

### Change 3: dealNewHands (around line 219)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/deal-hands`);
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/deal-hands`, {
  headers: { ...getSessionHeaders() }
});
```

---

### Change 4: handleBidClick (around line 246)

**BEFORE:**
```javascript
const feedbackResponse = await fetch(`${API_URL}/api/get-feedback`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    auction_history: auctionWithUserBid,
    explanation_level: explanationLevel
  })
});
```

**AFTER:**
```javascript
const feedbackResponse = await fetch(`${API_URL}/api/get-feedback`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify({
    auction_history: auctionWithUserBid,
    explanation_level: explanationLevel
  })
});
```

---

### Change 5: performAiBid (around line 350)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/get-next-bid`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    auction_history: auction,
    current_player: players[nextPlayerIndex],
    explanation_level: explanationLevel
  })
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/get-next-bid`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify({
    auction_history: auction,
    current_player: players[nextPlayerIndex],
    explanation_level: explanationLevel
  })
});
```

---

### Change 6: startPlayPhase (around line 420)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/start-play`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    auction_history: auction,
    vulnerability: vulnerability
  })
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/start-play`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify({
    auction_history: auction,
    vulnerability: vulnerability
  })
});
```

---

### Change 7: handleCardPlay (around line 513)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/play-card`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    card: { rank, suit },
    position: playerPosition
  })
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/play-card`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify({
    card: { rank, suit },
    position: playerPosition
  })
});
```

---

### Change 8: performAiPlay (around line 620)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/get-ai-play`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/get-ai-play`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify({})
});
```

---

### Change 9: clearTrickAndContinue (around line 713)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/clear-trick`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/clear-trick`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify({})
});
```

---

### Change 10: handlePlayComplete (around line 755)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/complete-play`);
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/complete-play`, {
  headers: { ...getSessionHeaders() }
});
```

---

### Change 11: handleShowAllHands (around line 905)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/get-all-hands`);
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/get-all-hands`, {
  headers: { ...getSessionHeaders() }
});
```

---

### Change 12: handleRequestReview (around line 933)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/request-review`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(reviewData)
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/request-review`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify(reviewData)
});
```

---

### Change 13: fetchConventionInfo (around line 1000)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/convention-info?name=${encodeURIComponent(name)}`);
```

**AFTER:**
```javascript
const response = await fetch(
  `${API_URL}/api/convention-info?name=${encodeURIComponent(name)}`,
  { headers: { ...getSessionHeaders() } }
);
```

---

### Change 14: fetchSessionData (around line 1045)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/session/status`);
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/session/status`, {
  headers: { ...getSessionHeaders() }
});
```

---

### Change 15: startNewSession (around line 1073)

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/session/start`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 1,
    session_type: 'chicago',
    player_position: 'S',
    ai_difficulty: aiDifficulty
  })
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/session/start`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()
  },
  body: JSON.stringify({
    user_id: 1,
    session_type: 'chicago',
    player_position: 'S',
    ai_difficulty: aiDifficulty
  })
});
```

---

## Quick Search & Replace Method

You can use your editor's search and replace:

### Replace Pattern 1:
**Find:** `headers: { 'Content-Type': 'application/json' }`
**Replace:** `headers: { 'Content-Type': 'application/json', ...getSessionHeaders() }`

### Replace Pattern 2:
**Find:** `fetch(\`\${API_URL}/api/([^`]+)\`\);`
**Replace:** `fetch(\`\${API_URL}/api/$1\`, { headers: { ...getSessionHeaders() } });`

**⚠️ Warning:** Test carefully after bulk replacements!

---

## Verification

After making changes:

1. **Check syntax:**
   ```bash
   npm run build
   ```

2. **Test in browser:**
   - Open DevTools → Network tab
   - Deal hands
   - Check request headers for `X-Session-ID`

3. **Test multi-user:**
   - Open app in 2 tabs
   - Deal in both tabs
   - Verify different hands

---

## Complete Summary

**Total Changes:**
- 1 import statement added
- ~15-20 fetch calls updated
- 0 logic changes
- Backward compatible (backend has fallback)

**Estimated Time:** 30 minutes

**Risk Level:** Low (additive changes only)

**Rollback:** Remove import, remove `...getSessionHeaders()` from fetch calls

---

## Automated Script Option

If you prefer, here's a bash script to do it automatically:

```bash
#!/bin/bash
# WARNING: Backup App.js first!

cd frontend/src

# Backup
cp App.js App.js.backup

# Add import (after line with AIDifficultySelector)
sed -i '' '/AIDifficultySelector/a\
import { getSessionHeaders } from '\''./utils/sessionHelper'\'';
' App.js

# Replace fetch calls (simple pattern)
sed -i '' "s/headers: { 'Content-Type': 'application\/json' }/headers: { 'Content-Type': 'application\/json', ...getSessionHeaders() }/g" App.js

echo "✅ App.js updated! Check git diff to review changes."
echo "   Backup saved as App.js.backup"
```

**Usage:**
```bash
chmod +x update_app_session.sh
./update_app_session.sh
git diff src/App.js  # Review changes
```

---

## Support

If you get stuck:
1. Check `frontend/FRONTEND_SESSION_MIGRATION.md` for full guide
2. Check `frontend/src/services/api.js` for reference implementation
3. Check browser console for session ID logs
4. Check Network tab for `X-Session-ID` header

**Estimated completion time:** 30 minutes for experienced developer.
