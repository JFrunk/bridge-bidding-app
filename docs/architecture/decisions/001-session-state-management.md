# ADR 001: Session-Based State Management

**Date:** 2025-10-14
**Status:** ✅ Implemented
**Deciders:** CTO Review, Engineering Team
**Tags:** #critical #architecture #multi-user #state-management

---

## Context and Problem Statement

The bridge bidding application was initially built with global variables to store game state (`current_deal`, `current_vulnerability`, `current_play_state`, etc.). This created **Critical Bug #1**: race conditions causing multi-user interference.

**Symptoms:**
- User A's cards appearing in User B's game
- Vulnerability settings changing mid-game
- AI difficulty switching unexpectedly
- Game state corruption with concurrent users

**Root Cause:**
```python
# BROKEN: Global state (thread-unsafe)
current_deal = {'North': None, 'East': None, 'South': None, 'West': None}
current_vulnerability = "None"
current_play_state = None

@app.route('/api/deal-hands')
def deal_hands():
    global current_deal  # ❌ Shared across ALL users!
    current_deal['South'] = Hand(...)
```

This architecture was **fundamentally incompatible** with multi-user deployments.

---

## Decision Drivers

1. **Critical Bug**: Active user frustration with game state corruption
2. **Multi-user Support**: Need to support concurrent users without interference
3. **Thread Safety**: Flask uses multiple threads for concurrent requests
4. **Scalability**: Prepare for horizontal scaling with Redis
5. **Maintainability**: Clear separation of concerns, easier to debug
6. **Production Readiness**: Current code not deployable to Render/production

---

## Considered Options

### Option 1: Session-Based State (Thread-Safe Dictionary) ✅ **SELECTED**
- **Approach**: SessionStateManager with thread-safe RLock
- **State Storage**: In-memory dictionary keyed by session ID
- **Session Identification**: X-Session-ID HTTP header
- **Frontend**: localStorage-based session persistence

### Option 2: Database-Based State
- **Approach**: Store all game state in SQLite/PostgreSQL
- **Pros**: Persistent, scalable, survives server restarts
- **Cons**: Much slower (DB I/O on every request), complex, overkill for ephemeral game state

### Option 3: Flask-Session with Server-Side Storage
- **Approach**: Use Flask-Session extension with filesystem/Redis backend
- **Pros**: Built-in solution, well-tested
- **Cons**: Adds dependency, less control, harder to debug

### Option 4: Redis-Based State (Future Recommendation)
- **Approach**: Store session state in Redis
- **Pros**: Fast, scalable, supports horizontal scaling
- **Cons**: Requires Redis infrastructure, more complex deployment
- **Note**: Recommended as **Critical Fix #2** after this implementation

---

## Decision Outcome

**Chosen Option:** Option 1 - Session-Based State with Thread-Safe Dictionary

### Implementation Details

#### Backend: `backend/core/session_state.py`

```python
@dataclass
class SessionState:
    """Isolated state for a single user session"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)

    # Game state (replaces globals)
    deal: Dict[str, Any] = field(default_factory=lambda: {
        'North': None, 'East': None, 'South': None, 'West': None
    })
    vulnerability: str = "None"
    play_state: Optional[PlayState] = None
    game_session: Optional[GameSession] = None
    ai_difficulty: str = "expert"
    hand_start_time: Optional[datetime] = None

class SessionStateManager:
    """Thread-safe manager for user session states"""
    def __init__(self):
        self._states: Dict[str, SessionState] = {}
        self._lock = threading.RLock()

    def get_or_create(self, session_id: str) -> SessionState:
        """Get or create session state (thread-safe)"""
        with self._lock:
            if session_id not in self._states:
                self._states[session_id] = SessionState(session_id=session_id)
            state = self._states[session_id]
            state.touch()
            return state
```

#### Backend: Endpoint Pattern

```python
# Every endpoint MUST follow this pattern
@app.route('/api/deal-hands')
def deal_hands():
    state = get_state()  # Get isolated session state
    state.vulnerability = "None"
    state.deal['South'] = Hand(...)
    return jsonify({'success': True})
```

#### Frontend: Session Headers

```javascript
// frontend/src/utils/sessionHelper.js
export function getSessionId() {
  let sessionId = localStorage.getItem('bridge_session_id');

  if (!sessionId) {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 11);
    sessionId = `session_${timestamp}_${random}`;
    localStorage.setItem('bridge_session_id', sessionId);
  }

  return sessionId;
}

export function getSessionHeaders() {
  return {
    'X-Session-ID': getSessionId()
  };
}
```

```javascript
// All API calls MUST include session headers
fetch(`${API_URL}/api/deal-hands`, {
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()  // ✅ Always include!
  }
})
```

---

## Consequences

### Positive ✅

1. **Multi-user Support**: Each user gets isolated game state
2. **Thread Safety**: RLock prevents race conditions
3. **No State Corruption**: Users can't interfere with each other
4. **Session Persistence**: localStorage keeps session across page reloads
5. **Backward Compatible**: Fallback to user_id-based sessions
6. **Debugging**: Each session traceable via session_id
7. **Scalability**: Ready for Redis migration (Critical #2)
8. **Clean Architecture**: Clear separation of concerns

### Negative ⚠️

1. **Memory Usage**: Sessions stored in RAM (mitigated by cleanup)
2. **Not Persistent**: Server restart loses sessions (acceptable for game state)
3. **Not Horizontally Scalable**: Single-server limitation (fix with Redis)
4. **Manual Session Management**: Frontend must include headers (documented)

### Neutral 🔄

1. **Migration Effort**: 98 global variable references replaced
2. **Testing Required**: All endpoints need session state verification
3. **Documentation Needed**: Developers must understand pattern

---

## Compliance and Guidelines

### For Backend Developers

**CRITICAL RULES:**

🚫 **NEVER use global variables for user-specific state**

```python
# ❌ WRONG - DO NOT DO THIS
current_deal = {}
current_vulnerability = "None"

@app.route('/api/endpoint')
def my_endpoint():
    global current_deal  # ❌ WRONG!
    current_deal['South'] = ...
```

✅ **ALWAYS use session state**

```python
# ✅ CORRECT - DO THIS
@app.route('/api/endpoint')
def my_endpoint():
    state = get_state()  # ✅ Get isolated state
    state.deal['South'] = ...
    return jsonify({'success': True})
```

**Required Pattern:**
1. Call `state = get_state()` at start of every endpoint
2. Access state via `state.deal`, `state.vulnerability`, `state.play_state`, etc.
3. Never use `global` keyword for game state

### For Frontend Developers

**CRITICAL RULES:**

🚫 **NEVER make API calls without session headers**

```javascript
// ❌ WRONG - DO NOT DO THIS
fetch(`${API_URL}/api/deal-hands`)
```

✅ **ALWAYS include session headers**

```javascript
// ✅ CORRECT - DO THIS
import { getSessionHeaders } from './utils/sessionHelper';

fetch(`${API_URL}/api/deal-hands`, {
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()  // ✅ Always include!
  }
})
```

**Required Pattern:**
1. Import `getSessionHeaders()` from `utils/sessionHelper.js`
2. Include `...getSessionHeaders()` in ALL fetch calls
3. Never hardcode session IDs

---

## Verification

### Automated Tests

**Backend Tests:**
```bash
cd backend
python3 test_simple.py  # 8/8 tests passing ✅
```

**Test Coverage:**
- ✅ Session isolation (different sessions don't interfere)
- ✅ Thread safety (RLock prevents races)
- ✅ Session creation and retrieval
- ✅ Session cleanup
- ✅ Header extraction
- ✅ Fallback mechanism
- ✅ Endpoint integration
- ✅ Multi-request workflows

### Manual Verification

**Multi-User Test:**
1. Open two browser windows (different sessions)
2. Start a game in each window
3. Verify hands are different
4. Play cards in both games simultaneously
5. Verify no state interference

**Expected Behavior:**
- Each window has independent game state
- Cards don't appear in the other window
- Vulnerability settings are isolated
- AI difficulty is per-session

---

## Migration Path

### Completed (Oct 2025)
- ✅ Created `backend/core/session_state.py`
- ✅ Refactored `backend/server.py` (98 global references eliminated)
- ✅ Updated 22 API endpoints
- ✅ Created `frontend/src/utils/sessionHelper.js`
- ✅ Updated `frontend/src/App.js` (36 fetch calls)
- ✅ Automated testing implemented
- ✅ Build verification passed
- ✅ Documentation created

### Future Recommendations

**Critical #2: Migrate to Redis**
- Replace in-memory dictionary with Redis
- Enables horizontal scaling
- Session persistence across server restarts
- Priority: HIGH (required for production scaling)

**Critical #3: Add Authentication**
- Implement password-based user accounts
- Secure session management
- User profile storage
- Priority: HIGH (required for production security)

---

## References

- **Implementation Guide:** `backend/GLOBAL_STATE_FIX_GUIDE.md`
- **Completion Report:** `CRITICAL_BUG_FIX_COMPLETE.md`
- **Frontend Migration:** `frontend/FRONTEND_SESSION_MIGRATION.md`
- **Test Results:** `TEST_RESULTS.md`
- **CTO Review:** `CTO_TECHNICAL_REVIEW.md`

---

## Notes

- This fix addresses the #1 critical issue from CTO review
- Implementation completed in single session (Oct 14, 2025)
- All tests passing, build verified
- Ready for deployment with session-based architecture
- Future scaling requires Redis migration (Critical #2)

**Decision Status:** ✅ **IMPLEMENTED AND VERIFIED**
