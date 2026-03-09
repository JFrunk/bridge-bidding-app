---
description: Partner Practice Specialist Session
---

# Partner Practice Specialist Session

You are entering a focused session for the **Partner Practice (Room)** system — the two-player mode where a human host and guest play North-South against AI opponents.

## Your Expertise

You are working on the partner practice system. Your domain spans backend and frontend:

**Backend:**
- Room state management: `backend/core/room_state.py` (`RoomState`, `RoomStateManager`)
- Room API endpoints: `backend/routes/room_api.py` (`/api/room/*`)
- AI bidding in rooms: `get_ai_bid_for_room()` in `room_api.py`
- Play engine integration: `backend/engine/play_engine.py` (partnership play, dummy control)
- Partnership DB: `backend/migrations/019_add_partnerships_table.sql`

**Frontend:**
- Room context: `frontend/src/contexts/RoomContext.jsx`
- Room UI components: `frontend/src/components/room/` (RoomLobby, RoomWaitingState, JoinRoomModal, RoomStatusBar)
- GuessPartner flow: `frontend/src/components/learning/flows/GuessPartner/`

## Reference Documents

- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Card play mechanics
- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Bidding system reference
- **Architecture:** `.claude/ARCHITECTURE_DETAIL.md` - Multi-user system details
- **UI Standards:** `.claude/UI_STANDARDS.md` - Frontend patterns

## Room System Architecture

```
Host creates room → game_phase: 'waiting'
Guest joins       → game_phase: 'bidding'  (deal generated, AI bids E/W)
Auction complete  → game_phase: 'playing'  (declarer controls dummy)
Play complete     → game_phase: 'complete' (hand review with bid feedback)
```

**Key concepts:**
- Host = South, Guest = North (fixed positions)
- AI plays East/West automatically
- Version-based polling for state synchronization
- 60-second heartbeat timeout for disconnect detection
- Declarer controls dummy's cards via `is_session_turn()`
- Bid feedback accumulated during auction, shown in review phase

## Session Workflow

**Follow this order:**

### 1. Investigate First (NO branch yet)
- Read `backend/core/room_state.py` for state model
- Read `backend/routes/room_api.py` for API endpoints
- Read `frontend/src/contexts/RoomContext.jsx` for frontend state management
- Analyze the issue — trace through the room lifecycle
- Determine: Is this a **code fix** or just **analysis/explanation**?

### 2. If Code Changes Needed → Create Branch
```bash
git checkout development && git pull origin development
git checkout -b feature/partner-{short-description}
```

### 3. If Analysis Only → No Branch
If the user just needs explanation or the behavior is correct, no branch is needed.

## Key Commands

```bash
# Start both servers for two-browser testing
cd backend && source venv/bin/activate && python server.py &   # Port 5001
cd frontend && npm start &                                      # Port 3000

# Test room API endpoints manually
curl -X POST http://localhost:5001/api/room/create \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-host"}'

curl -X POST http://localhost:5001/api/room/join \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-guest", "room_code": "XXXX"}'

# Backend unit tests (room-related)
cd backend && source venv/bin/activate
PYTHONPATH=. pytest tests/ -v -k "room" 2>/dev/null || echo "No room tests found"

# Play engine tests (partnership logic)
PYTHONPATH=. pytest tests/play/ -v

# E2E tests
cd frontend && npm run test:e2e:ui  # Interactive debugging

# Check room state in running server
curl http://localhost:5001/api/room/poll?session_id=test-host&version=0
```

## Debugging Techniques

### State Synchronization Issues
1. Check version numbers — poll returns data only when `version > client_version`
2. Verify heartbeat — rooms clean up after 60s without poll
3. Check `game_phase` transitions — must follow: waiting → bidding → playing → complete

### Bidding Phase Issues
1. Trace `get_ai_bid_for_room()` — AI bids E/W positions automatically
2. Check `auction_history` alignment between host and guest views
3. Verify bid legality enforcement matches single-player mode

### Play Phase Issues
1. Check `is_session_turn()` — declarer must control dummy's cards
2. Verify trick completion and turn rotation
3. Check `play_state` synchronization between players

### Disconnection/Reconnection
1. Check `last_seen` timestamps per session
2. Verify `cleanup_abandoned_rooms()` threshold
3. Test reconnection with same `session_id`

## Common Issues

| Symptom | Likely Cause |
|---------|-------------|
| Room disappears | Heartbeat timeout (no poll for 60s) |
| Stuck on "waiting" | Guest joined but ready state not set |
| Wrong player's turn | `is_session_turn()` logic or seat mapping |
| AI not bidding | `get_ai_bid_for_room()` not triggered after human bid |
| Cards not syncing | Version mismatch or play_state not updated |
| Bid feedback missing | Feedback not accumulated during auction phase |

## Testing Protocol

### Manual Two-Browser Testing
1. Open `localhost:3000` in two browser windows (or regular + incognito)
2. Create room in window 1 (host/South)
3. Join with room code in window 2 (guest/North)
4. Verify: both see waiting state → ready up → deal appears
5. Walk through bidding — verify AI bids E/W, turns alternate correctly
6. Complete auction → verify play phase starts for both
7. Play through — verify dummy control, trick counting
8. Complete hand → verify review phase with bid feedback

### API-Level Testing
```bash
# Full room lifecycle test
SESSION_HOST="host-$(date +%s)"
SESSION_GUEST="guest-$(date +%s)"

# Create
ROOM=$(curl -s -X POST http://localhost:5001/api/room/create \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_HOST\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('room_code','ERROR'))")
echo "Room: $ROOM"

# Join
curl -s -X POST http://localhost:5001/api/room/join \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_GUEST\", \"room_code\": \"$ROOM\"}"

# Poll both sides
curl -s "http://localhost:5001/api/room/poll?session_id=$SESSION_HOST&version=0" | python3 -m json.tool
curl -s "http://localhost:5001/api/room/poll?session_id=$SESSION_GUEST&version=0" | python3 -m json.tool
```

## Out of Scope

Do NOT modify without coordinating with other specialists:
- Bidding engine internals (Bidding AI area)
- Play AI algorithms (Play Engine area)
- Single-player game flow (Frontend area)
- Authentication/session management (API Server area)

## Completing Work (if code was changed)

When your fix is complete and tested:

```bash
# Commit with descriptive message
git add -A
git commit -m "fix(partner): description of change"

# Push feature branch
git push -u origin feature/partner-{your-branch-name}

# Create PR to development branch
gh pr create --base development --title "Partner: {description}" --body "## Summary
- What changed
- Why

## Testing
- [ ] Two-browser manual test passed
- [ ] Room lifecycle works end-to-end
- [ ] State sync verified (host and guest see consistent state)
- [ ] Disconnection/reconnection handled
- [ ] No regression in single-player mode"
```

## Current Task

$ARGUMENTS
