# Frontend Session State Migration Guide

**Date:** October 14, 2025
**Purpose:** Integrate frontend with new backend session state management
**Impact:** Enables true multi-user support with session isolation

---

## Overview

The backend has been refactored to use per-session state instead of global variables. The frontend needs to include session IDs in all API requests to maintain isolated game state for each user.

## What's New

### Created Files
1. **`src/services/api.js`** - Centralized API service with session management
   - Automatic session ID generation and storage
   - Helper functions for all API endpoints
   - Consistent error handling
   - Session header injection

### Benefits
✅ **Session Isolation** - Each user/tab gets independent game state
✅ **Cleaner Code** - Centralized API logic instead of scattered fetch calls
✅ **Type Safety** - Consistent API interfaces
✅ **Error Handling** - Unified error management
✅ **Debugging** - Session tracking and logging

---

## Migration Options

### Option 1: Full Migration (Recommended)

Replace all `fetch()` calls with the new API service. This provides the best long-term maintainability.

**Effort:** 2-3 hours
**Benefits:** Clean code, easy debugging, future-proof

### Option 2: Minimal Integration (Quick Fix)

Add session headers to existing fetch calls without full refactoring.

**Effort:** 30 minutes
**Benefits:** Quick fix, minimal changes
**Downside:** Less maintainable, duplicate code

---

## Option 1: Full Migration (Step-by-Step)

### Step 1: Import the API Service

**Location:** `src/App.js` (top of file)

**Add:**
```javascript
import api, { sessionManager } from './services/api';
```

### Step 2: Replace Fetch Calls

Replace each `fetch()` call with the corresponding `api` method.

#### Example 1: Deal Hands

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/deal-hands`);
const data = await response.json();
```

**AFTER:**
```javascript
const data = await api.dealHands();
```

#### Example 2: Get Next Bid

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/get-next-bid`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    auction_history: auction,
    current_player: player,
    explanation_level: 'detailed'
  })
});
const data = await response.json();
```

**AFTER:**
```javascript
const data = await api.getNextBid(auction, player, 'detailed');
```

#### Example 3: Start Play

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/start-play`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    auction_history: auctionHistory,
    vulnerability: vulnerability,
    hands: handsData
  })
});
const data = await response.json();
```

**AFTER:**
```javascript
const data = await api.startPlay(auctionHistory, vulnerability, handsData);
```

### Step 3: Update All API Calls

Here's a complete mapping of fetch calls to API methods:

| Fetch Endpoint | API Method | Parameters |
|---------------|------------|------------|
| `GET /api/scenarios` | `api.getScenarios()` | - |
| `POST /api/load-scenario` | `api.loadScenario(name)` | name |
| `GET /api/deal-hands` | `api.dealHands()` | - |
| `POST /api/get-next-bid` | `api.getNextBid(auction, player, level)` | auction, player, level |
| `POST /api/get-next-bid-structured` | `api.getNextBidStructured(auction, player)` | auction, player |
| `POST /api/get-feedback` | `api.getFeedback(auction, level)` | auction, level |
| `GET /api/get-all-hands` | `api.getAllHands()` | - |
| `POST /api/request-review` | `api.requestReview(data)` | reviewData |
| `GET /api/convention-info` | `api.getConventionInfo(name)` | name (optional) |
| `POST /api/start-play` | `api.startPlay(auction, vuln, hands)` | auction, vuln, hands |
| `POST /api/play-card` | `api.playCard(card, position)` | card, position |
| `POST /api/get-ai-play` | `api.getAiPlay()` | - |
| `GET /api/get-play-state` | `api.getPlayState()` | - |
| `POST /api/clear-trick` | `api.clearTrick()` | - |
| `GET /api/complete-play` | `api.completePlay(vuln)` | vuln (optional) |
| `POST /api/session/start` | `api.startSession(params)` | params |
| `GET /api/session/status` | `api.getSessionStatus()` | - |
| `POST /api/session/complete-hand` | `api.completeSessionHand(scoreData)` | scoreData |
| `GET /api/session/history` | `api.getSessionHistory()` | - |
| `POST /api/session/abandon` | `api.abandonSession()` | - |
| `GET /api/ai/status` | `api.getAiStatus()` | - |
| `GET /api/ai-difficulties` | `api.getAiDifficulties()` | - |
| `POST /api/set-ai-difficulty` | `api.setAiDifficulty(difficulty)` | difficulty |

### Step 4: Error Handling

The API service throws errors that you can catch:

**BEFORE:**
```javascript
try {
  const response = await fetch(`${API_URL}/api/deal-hands`);
  if (!response.ok) {
    throw new Error('Failed to deal');
  }
  const data = await response.json();
  // handle data
} catch (error) {
  console.error(error);
  setError('Failed to deal hands');
}
```

**AFTER:**
```javascript
try {
  const data = await api.dealHands();
  // handle data
} catch (error) {
  console.error(error);
  setError(error.message || 'Failed to deal hands');
}
```

### Step 5: Session Management UI (Optional)

Add session info display for debugging:

```javascript
import { sessionManager } from './services/api';

function App() {
  const [sessionInfo, setSessionInfo] = useState(null);

  useEffect(() => {
    setSessionInfo(sessionManager.getSessionInfo());
  }, []);

  return (
    <div className="App">
      {/* Debug info - remove in production */}
      <div style={{fontSize: '10px', color: '#666', padding: '5px'}}>
        Session: {sessionInfo?.sessionId?.substring(0, 20)}...
      </div>

      {/* Rest of your app */}
    </div>
  );
}
```

---

## Option 2: Minimal Integration (Quick Fix)

If you want to keep existing code and just add session headers:

### Step 1: Add Session ID Helper

**Location:** `src/App.js` (near top, before App component)

**Add:**
```javascript
// Session ID management
const getSessionId = () => {
  let sessionId = localStorage.getItem('bridge_session_id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    localStorage.setItem('bridge_session_id', sessionId);
    console.log('Generated session ID:', sessionId);
  }
  return sessionId;
};

// Get session ID once at startup
const SESSION_ID = getSessionId();
```

### Step 2: Add Header to All Fetch Calls

Find every `fetch()` call and add the session header:

**BEFORE:**
```javascript
const response = await fetch(`${API_URL}/api/deal-hands`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
});
```

**AFTER:**
```javascript
const response = await fetch(`${API_URL}/api/deal-hands`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'X-Session-ID': SESSION_ID  // ADD THIS LINE
  }
});
```

**Repeat for ALL fetch calls** (approximately 20-30 locations in App.js)

---

## Testing Checklist

After migration, test these scenarios:

### Single User Testing
- [ ] Deal hands - shows correct cards
- [ ] Make bids - AI responds correctly
- [ ] Play cards - card play works
- [ ] Complete hand - scoring works
- [ ] Start new hand - state resets properly

### Multi-User Testing
- [ ] Open app in 2 browser tabs
- [ ] Deal hands in both tabs
- [ ] Verify each tab shows DIFFERENT hands
- [ ] Make bids in both tabs
- [ ] Verify bids don't interfere
- [ ] Play cards in both tabs
- [ ] Verify play state is isolated

### Session Persistence
- [ ] Deal hands
- [ ] Refresh page
- [ ] Verify session ID persists (check console)
- [ ] Make a bid
- [ ] Verify state continues correctly

### Error Scenarios
- [ ] Server restart - should create new session
- [ ] Invalid bid - error handling works
- [ ] Network error - shows appropriate message

---

## Debugging

### Check Session ID

Open browser console and run:
```javascript
localStorage.getItem('bridge_session_id')
```

Should show something like: `session_1697234567890_abc123xyz`

### Clear Session (Force New Session)

```javascript
localStorage.removeItem('bridge_session_id');
location.reload();
```

### Monitor API Calls

Open browser DevTools → Network tab:
- Look for requests to `/api/*`
- Click on a request
- Check Headers tab
- Verify `X-Session-ID` header is present

### Backend Logs

Check backend console for session info:
```
🆔 Using existing session ID: session_1697234567890_abc123xyz
```

---

## Rollback Plan

If issues occur:

### Option 1 Migration Rollback
```bash
# Revert App.js changes
git checkout HEAD -- src/App.js

# Remove API service
rm src/services/api.js

# Restart dev server
npm start
```

### Option 2 Migration Rollback
```bash
# Just remove the SESSION_ID lines from App.js
# Server will fall back to user_id based sessions
```

---

## Example: Complete Migration of One Function

Here's a complete before/after example:

### BEFORE (Old fetch code)
```javascript
const handleDealHands = async () => {
  try {
    const response = await fetch(`${API_URL}/api/deal-hands`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to deal hands');
    }

    const data = await response.json();
    setHand(data.hand);
    setHandPoints(data.points);
    setVulnerability(data.vulnerability);
    setError('');
  } catch (err) {
    console.error('Error dealing hands:', err);
    setError('Failed to deal hands. Please try again.');
  }
};
```

### AFTER (New API service)
```javascript
import api from './services/api';

const handleDealHands = async () => {
  try {
    const data = await api.dealHands();
    setHand(data.hand);
    setHandPoints(data.points);
    setVulnerability(data.vulnerability);
    setError('');
  } catch (err) {
    console.error('Error dealing hands:', err);
    setError(err.message || 'Failed to deal hands. Please try again.');
  }
};
```

**Lines of code:** 21 → 11 (48% reduction!)
**Complexity:** Lower
**Maintainability:** Higher

---

## Performance Impact

- **Session ID generation:** <1ms (one-time on first load)
- **localStorage access:** <1ms per request
- **Header overhead:** ~50 bytes per request
- **Overall impact:** Negligible (<1% latency increase)

---

## FAQ

### Q: What happens to existing users?
**A:** Their localStorage will be empty, so a new session ID will be generated automatically. No action needed.

### Q: Can multiple tabs share a session?
**A:** Yes, by default they share the same localStorage session ID. If you want separate sessions per tab, use `sessionStorage` instead of `localStorage`.

### Q: What if the server restarts?
**A:** The backend loses session data (until Redis migration). The frontend keeps the session ID, so just deal new hands.

### Q: How do I test with multiple users?
**A:** Use incognito mode or different browsers. Each will get a unique session ID.

### Q: Can I see active sessions?
**A:** Not yet. Session monitoring UI is planned for future development.

---

## Next Steps After Migration

1. **Test thoroughly** - Use the checklist above
2. **Monitor for issues** - Check console for errors
3. **Deploy to staging** - Test in production-like environment
4. **Get user feedback** - Verify multi-user scenarios work
5. **Plan Redis migration** - For persistent sessions across restarts

---

## Support

- **Backend docs:** `backend/GLOBAL_STATE_FIX_COMPLETED.md`
- **API service code:** `frontend/src/services/api.js`
- **Session state code:** `backend/core/session_state.py`

**Estimated Time:**
- Option 1 (Full): 2-3 hours
- Option 2 (Minimal): 30 minutes

**Recommended:** Option 1 for better long-term maintainability.
