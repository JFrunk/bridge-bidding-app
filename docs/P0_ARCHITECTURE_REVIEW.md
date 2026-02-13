# P0 Architecture Review

## Status Summary

| Requirement | Status | Notes |
|-------------|--------|-------|
| 3-tier zone CSS | ✅ Done | Classes added to App.css, need App.js integration |
| CompassBar | ✅ Satisfied | RoomStatusBar already implements spec |
| Privacy/About/Footer | ✅ Done | Pushed to main |
| robots.txt | ✅ Done | Allow rules added |
| Room persistence | ⚠️ Gap | Uses in-memory, not database |

---

## 1. CompassBar vs RoomStatusBar

**Finding:** RoomStatusBar already implements the P0 CompassBar specification.

**Location:** `frontend/src/components/room/RoomStatusBar.jsx` (lines 153-160)

**Current output:**
```
You: SOUTH (Host) | Partner: NORTH | Opponents: AI (E/W)
```

**P0 spec required:**
```
You: [SEAT] | Room: [CODE] | Status
```

**Assessment:** The existing implementation exceeds the spec by including partner seat and opponent info. Room code is shown in the status bar above. No changes needed.

---

## 2. 3-Tier Zone Architecture

**CSS classes added to App.css:**
```css
.app-root-container { height: 100vh; display: flex; flex-direction: column; }
.zone-header { flex: 0 0 60px; z-index: 100; }
.zone-game-stage { flex: 1; overflow-y: auto; }
.zone-south-affordance { height: 35vh; min-height: 320px; z-index: 100; }
```

**Integration needed:** App.js needs to wrap content in these zone containers for the architecture to take effect. Current App.js uses `.app-container` without the zone hierarchy.

**Recommended next step:** Wrap App.js return JSX in zone structure:
```jsx
<div className="app-root-container">
  <div className="zone-header">
    <TopNavigation />
    {inRoom && <RoomStatusBar />}
  </div>
  <div className="zone-game-stage">
    {/* Game content */}
  </div>
  <div className="zone-south-affordance">
    {/* South hand, bidding box */}
  </div>
</div>
```

---

## 3. Room Persistence Architecture Gap

**Current:** In-memory room state (`core/room_state.py`)
- RoomStateManager stores rooms in a Python dict
- Lost on server restart
- Cannot scale horizontally

**P0 Spec:** Database-backed rooms (`migrations/019_add_room_tables.sql`)
- `rooms` table with room_code, host_id, guest_id, room_state
- `room_play_history` table for action sync
- Supports server restarts, horizontal scaling

**Trade-offs:**

| Aspect | In-Memory (Current) | Database (P0 Spec) |
|--------|---------------------|-------------------|
| Complexity | Simple | More complex |
| Latency | ~0ms | ~1-5ms per query |
| Persistence | Lost on restart | Survives restart |
| Scaling | Single server only | Multi-server ready |
| Real-time | Polling works | Polling works |

**Recommendation:** For MVP/single-server deployment, in-memory is acceptable. Add database persistence when:
1. Server restarts should preserve active games
2. Multiple server instances are needed
3. Game history needs to be stored

---

## Files Changed

**This session:**
- `frontend/src/App.css` - Added zone CSS classes
- `frontend/src/components/legal/*` - Privacy/About pages
- `frontend/src/components/navigation/Footer.*` - Footer component
- `frontend/public/robots.txt` - Allow rules

**Pre-existing (satisfies spec):**
- `frontend/src/components/room/RoomStatusBar.jsx` - CompassBar equivalent
- `frontend/src/contexts/RoomContext.jsx` - Room state management
- `backend/core/room_state.py` - In-memory room manager
- `backend/routes/room_api.py` - Room API endpoints
