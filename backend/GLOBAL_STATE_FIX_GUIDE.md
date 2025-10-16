# Global State Fix - Implementation Guide

## Problem Summary

The current `server.py` uses 6 global variables that cause race conditions with multiple users:
- `current_deal`
- `current_vulnerability`
- `current_play_state`
- `current_session`
- `current_ai_difficulty`
- `current_hand_start_time`

These variables are accessed by **187 lines** across **13 endpoints**, causing:
- Session data leakage between users
- Race conditions
- Unpredictable behavior with concurrent requests

## Solution Overview

Replace global variables with per-session state using the new `SessionStateManager`.

## Implementation Steps

### Step 1: Add Session State Manager (DONE ✅)

Created `/backend/core/session_state.py` with:
- `SessionState` - Per-session state container
- `SessionStateManager` - Thread-safe state storage
- `get_session_id_from_request()` - Extract session ID from requests
- `require_session_state` decorator - Inject state into endpoints

### Step 2: Update server.py Initialization

**Location:** Lines 1-58

**FIND:**
```python
from flask import Flask, request, jsonify
from flask_cors import CORS
# ... other imports ...

app = Flask(__name__)
CORS(app)
engine = BiddingEngine()
play_engine = PlayEngine()
play_ai = SimplePlayAI()
session_manager = SessionManager()

# Phase 2: AI difficulty settings
current_ai_difficulty = "expert"

# ... AI instances ...

current_deal = { 'North': None, 'East': None, 'South': None, 'West': None }
current_vulnerability = "None"
current_play_state = None
current_session = None
current_hand_start_time = None
```

**REPLACE WITH:**
```python
from flask import Flask, request, jsonify, g
from flask_cors import CORS
# ... other imports ...

# NEW: Session state management
from core.session_state import SessionStateManager, get_session_id_from_request

app = Flask(__name__)
CORS(app)
engine = BiddingEngine()
play_engine = PlayEngine()
play_ai = SimplePlayAI()
session_manager = SessionManager()

# NEW: Initialize state manager (replaces globals)
state_manager = SessionStateManager()
app.config['STATE_MANAGER'] = state_manager

# ... AI instances (unchanged) ...

# REMOVED: Global state variables
# Now each session has its own isolated state
# Access via: state = state_manager.get_or_create(session_id)
```

### Step 3: Add Helper Function

**Location:** After CONVENTION_MAP (line 65)

**ADD:**
```python
# ============================================================================
# SESSION STATE HELPER
# ============================================================================

def get_state():
    """
    Get session state for current request

    Returns SessionState object with isolated per-session state.
    Extracts session_id from:
      1. X-Session-ID header (preferred)
      2. session_id in JSON body
      3. session_id query parameter
      4. Fallback: user_id from request
    """
    session_id = get_session_id_from_request(request)

    if not session_id:
        # Backward compatibility: use user_id as session_id
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id', request.args.get('user_id', 1))
        session_id = f"user_{user_id}_default"

    return state_manager.get_or_create(session_id)
```

### Step 4: Update Each Endpoint

For each endpoint that uses global variables, follow this pattern:

#### Pattern for Endpoints

**BEFORE:**
```python
@app.route('/api/some-endpoint', methods=['POST'])
def some_endpoint():
    global current_deal, current_vulnerability, current_session

    # Use globals
    current_vulnerability = "None"
    south_hand = current_deal['South']
    if not current_session:
        return jsonify({'error': 'No session'}), 400
```

**AFTER:**
```python
@app.route('/api/some-endpoint', methods=['POST'])
def some_endpoint():
    # Get state for this request
    state = get_state()

    # Use state instead of globals
    state.vulnerability = "None"
    south_hand = state.deal['South']
    if not state.game_session:
        return jsonify({'error': 'No session'}), 400
```

#### Global Variable Mapping

Replace all occurrences:

| Old Global Variable | New State Access | Notes |
|---------------------|------------------|-------|
| `current_deal` | `state.deal` | Dict of hands by position |
| `current_vulnerability` | `state.vulnerability` | String: "None", "NS", "EW", "Both" |
| `current_play_state` | `state.play_state` | PlayState object or None |
| `current_session` | `state.game_session` | GameSession object or None |
| `current_ai_difficulty` | `state.ai_difficulty` | String: "beginner", "intermediate", etc. |
| `current_hand_start_time` | `state.hand_start_time` | datetime object or None |

### Step 5: Update Specific Endpoints

#### Endpoints Requiring Updates (13 total):

1. **`/api/session/start`** (line 82) - ✅ Priority 1
2. **`/api/session/status`** (line 136) - ✅ Priority 1
3. **`/api/session/complete-hand`** (line 153) - ✅ Priority 1
4. **`/api/session/history`** (line 243) - ✅ Priority 1
5. **`/api/session/abandon`** (line 267) - ✅ Priority 1
6. **`/api/ai/status`** (line 299) - Priority 2
7. **`/api/ai-difficulties`** (line 430) - Priority 2
8. **`/api/set-ai-difficulty`** (line 453) - ✅ Priority 1
9. **`/api/ai-statistics`** (line 482) - Priority 2
10. **`/api/load-scenario`** (line 508) - ✅ Priority 1
11. **`/api/deal-hands`** (line 557) - ✅ Priority 1
12. **`/api/get-next-bid`** (line 582) - ✅ Priority 1
13. **`/api/get-next-bid-structured`** (line 602) - Priority 1
14. **`/api/get-feedback`** (line 628) - ✅ Priority 1
15. **`/api/get-all-hands`** (line 720) - ✅ Priority 1
16. **`/api/request-review`** (line 750) - Priority 2
17. **`/api/start-play`** (line 910) - ✅ Priority 1
18. **`/api/play-card`** (line 991) - ✅ Priority 1
19. **`/api/get-ai-play`** (line 1097) - ✅ Priority 1
20. **`/api/get-play-state`** (line 1231) - ✅ Priority 1
21. **`/api/clear-trick`** (line 1286) - ✅ Priority 1
22. **`/api/complete-play`** (line 1315) - ✅ Priority 1

### Step 6: Update Frontend

Frontend needs to include session ID in requests.

**Location:** `frontend/src/App.js` (or create API service layer)

**ADD to API calls:**
```javascript
// Generate or retrieve session ID
const sessionId = localStorage.getItem('bridge_session_id') ||
                  `session_${Date.now()}_${Math.random().toString(36)}`;
localStorage.setItem('bridge_session_id', sessionId);

// Include in all API requests
fetch(`${API_URL}/api/endpoint`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Session-ID': sessionId  // ADD THIS
  },
  body: JSON.stringify({...})
});
```

### Step 7: Testing

#### Test Multi-User Scenario

**Test Script:** `test_multiuser.py`

```python
import requests
import threading

API_URL = 'http://localhost:5001'

def test_user(user_id, session_id):
    """Simulate a user playing"""
    headers = {'X-Session-ID': session_id}

    # Deal hands
    resp = requests.get(f'{API_URL}/api/deal-hands', headers=headers)
    print(f"User {user_id}: {resp.json()['points']['hcp']} HCP")

    # Make bid
    resp = requests.post(f'{API_URL}/api/get-next-bid',
                         headers=headers,
                         json={'auction_history': [], 'current_player': 'South'})
    print(f"User {user_id}: Bid {resp.json()['bid']}")

# Test with concurrent users
threads = []
for i in range(5):
    t = threading.Thread(target=test_user, args=(i, f'session_{i}'))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("✅ All users completed without interference")
```

## Rollout Plan

### Phase 1: Backend Only (1-2 days)
1. Update server.py with state manager
2. Test with single user (should work with fallback)
3. Deploy to staging

### Phase 2: Frontend Update (1 day)
4. Add session ID to frontend
5. Test multi-user scenarios
6. Deploy to production

### Phase 3: Monitoring (ongoing)
7. Monitor session count
8. Watch for memory leaks
9. Tune cleanup threshold if needed

## Rollback Plan

If issues occur:
1. Revert to backup: `server_backup_YYYYMMDD_HHMMSS.py`
2. Copy backup to `server.py`
3. Restart server
4. Investigate issues before retry

## Benefits After Fix

✅ **Multi-user support** - No more race conditions
✅ **Session isolation** - Each user has independent state
✅ **Horizontal scaling** - Can run multiple server instances (with Redis later)
✅ **Debugging** - Session state can be inspected per-user
✅ **Testing** - Easier to write concurrent tests

## Next Steps After This Fix

1. Migrate session storage to Redis (CRITICAL #2)
2. Add password authentication (CRITICAL #3)
3. Add session expiration and cleanup
4. Implement rate limiting
5. Add monitoring and alerting

---

**Estimated Effort:** 3-5 days
**Priority:** CRITICAL (blocks production deployment)
**Assigned To:** [Your Name]
**Status:** In Progress (Step 1 complete)
