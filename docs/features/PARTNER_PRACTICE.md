# Partner Practice — Product & Architecture Spec v1

**Status:** Phase 1 Complete (Bidding + Play + Chat + Hand Review)
**Last Updated:** 2026-03-08
**Phase:** 1 (Practice Bidding + Play)

---

## Overview

Synchronous partner bidding practice. Two players pair up, see their own hands, bid in real-time against AI opponents (E/W), review results together, and communicate via freeform chat. The partner system is fully containerized from the solo experience via an Orchestrator pattern.

---

## User Flow

```
Invite Partner -> Partner Lobby -> Practice Bidding -> Hand Review -> Next Hand / End
                  (both ready)    (sync, real-time)   (both hands)   (mutual ready)
```

---

## Pairing

- **Invite-only** via shareable code or link
- Either player can generate an invite
- Partnership persists across sessions (partner list in profile)
- No matchmaking, no public discovery

---

## Session Lifecycle

- Either partner creates a session, selects scenario type (random / curated)
- Other partner joins, confirms ready
- Session starts when **both** ready
- **Abort on disconnect** — no pause/resume, hand is discarded
- **Fresh start** — closing session destroys session state, next session is new
- Either player can leave at any time (confirmation prompt)
- If either player leaves, the session ends for both

---

## Peer Model — Mutual Readiness Gates

Bridge is a game of equals. There is no Host/Guest hierarchy during play. All state transitions require mutual readiness.

### Session Roles

| Role | Scope | Purpose |
|------|-------|---------|
| **Creator** | Session creation only | Selects initial scenario type when creating the session |
| **Peer** | All in-session activity | Both players are equal peers once the session starts |

### Mutual Readiness Gates

Every state transition requires both players to signal ready:

| Transition | Trigger | Gate |
|------------|---------|------|
| Lobby -> Dealing | Both click "Ready" | Mutual |
| Review -> Next Hand | Either clicks "Next Hand", other confirms "Ready" | Mutual |
| Any -> End Session | Either clicks "Leave" | Unilateral (ends for both) |

This prevents one player from snapping the other into a new deal mid-review. The UI shows the other player's ready state (e.g., "Partner is ready — click Next Hand when you are").

### Peer Permissions

| Action | Either Player |
|--------|---------------|
| Suggest scenario type | Yes |
| Click "Next Hand" | Yes (triggers ready gate) |
| End session | Yes (ends for both) |
| Bid own hand | Yes |
| Chat | Yes |
| Add post-hand notes | Yes |

---

## Containment Rules

### Mode Separation

```
[ TOP-LEVEL APP ROUTER ]
          |
    /-----+-----\
    |             |
[ SOLO MODE ]  [ PARTNER MODE ] <--- Entry via Invite/Join
    |             |
    |       [ SESSION GUARD ] <--- Locks Solo Nav
    |             |
    |       +-----+-------------------------------------+
    |       | PARTNER SESSION CONTAINER                  |
    |       |                                            |
    |       |  [ HEADER: Session Info | Leave Button ]   |
    |       |  +-----------------------+ +-----------+   |
    |       |  |       GAME AREA       | |   CHAT    |   |
    |       |  | (Bidding / Review)    | | (Sidebar) |   |
    |       |  +-----------------------+ +-----------+   |
    |       +--------------------------------------------+
    |             |
    \-------------/
          |
    [ SHARED DATABASE ]
    (Hand History + Partnership ID)
```

### Access Control in Partner Mode

| Feature | Available? | Reason |
|---------|-----------|--------|
| Practice Bidding | Yes | Core partner activity |
| Hand Review | Yes | Post-hand, both hands visible |
| Chat | Yes | Persistent sidebar during session |
| Learning Modules | No | Solo activity, breaks sync |
| Free Play (solo) | No | Conflicting session state |
| My Progress | No | Distraction, solo context |
| Settings | Limited | Sound/display only |
| Leave Session | Yes | Always available, with confirmation |

### Enforcement

- **Frontend:** `PartnerSessionProvider` context. Components check `isInPartnerSession` to hide/disable solo navigation. Nav bar transforms to partner-mode header.
- **Backend:** Partner session endpoints reject non-members. Solo endpoints reject users with active partner sessions.

---

## Bidding Flow

- Deal generated server-side; each player sees only their hand
- Bidding order follows standard rotation (dealer determined by deal)
- Player A = South, Player B = North (fixed for v1)
- E/W bid via AI (existing SAYC engine, invoked through Game Adapter)
- AI bids appear with standard 500ms delay
- Partner bids appear in real-time as they are made

---

## Hand Review

- After auction completes: both hands revealed, contract shown
- App provides SAYC-based feedback on each bid (existing feedback engine)
- Both players can add freeform notes on specific bids
- "Next Hand" triggers mutual readiness gate

---

## Chat

- Freeform text, visible only during active session
- Sidebar panel (collapsible)
- Stored in server-side ephemeral store (survives browser refresh, destroyed on session end)
- No media, no formatting — plain text only

---

## Architecture — Orchestrator Pattern

### Design Principle

The transition from single-player (linear/deterministic) to multiplayer (distributed/event-driven) requires strict modular separation. The partner system must not create dependencies on the core game engine.

**The Game View should not know which mode it is in.** It renders cards and bids from a data source. In solo mode, that source is local state + AI controller. In partner mode, that source is the Partner Orchestrator.

### Module Structure

```
[ UI LAYER ] <---- Injected via Provider
      |
[ PARTNER ORCHESTRATOR ]
      |
      +---- [ SESSION MANAGER ]   Heartbeats, presence, ready-state, abort-on-disconnect
      |
      +---- [ EVENT BUS ]         WebSocket transport for bids, chat, state changes
      |
      +---- [ GAME ADAPTER ]      Translates partner actions into game engine commands
      |
      +---- [ PERSISTENCE ]       Hand history writes with partnership tagging
```

### Module Responsibilities

| Module | Responsibility | Isolation Guarantee |
|--------|---------------|---------------------|
| **Session Manager** | Admissions, boundaries, heartbeats, mutual readiness, abort logic | Independent of bridge rules. A session bug cannot affect the bidding engine. |
| **Event Bus** | Transport only. Moves JSON payloads between players. | Does not interpret content. A bid and a chat message are both just events. |
| **Game Adapter** | Translates multiplayer events into existing engine commands | The bridge between networking and game logic. Allows swapping the bidding engine without touching networking. |
| **Persistence** | Writes hand results to each player's history with `partnership_id` tag | Uses existing hand history infrastructure with one additional FK. |

### Why This Matters

Without modular separation:
- **State contamination:** A chat bug could crash the bidding engine
- **Testing failure:** Can't test bidding logic without a fake second player connected
- **Future debt:** Adding Practice Play (Phase 2) would require rewriting the UI because bidding and networking logic are fused

---

## Data Model

### Database Tables

```
Partnership
  id              UUID PK
  player_a_id     FK -> users
  player_b_id     FK -> users
  invite_code     VARCHAR UNIQUE
  status          ENUM (pending, active, dissolved)
  created_at      TIMESTAMP

HandHistory (existing table, extended)
  ...existing fields...
  partnership_id  UUID NULLABLE FK -> Partnership
```

### Ephemeral Server-Side State (per session, not persisted to DB)

```
PartnerSession
  id              UUID
  partnership_id  FK -> Partnership
  player_a_id     UUID
  player_b_id     UUID
  status          ENUM (lobby, dealing, bidding, review)
  ready_state     { player_a: bool, player_b: bool }
  current_deal    { hands: {N, S}, ai_hands: {E, W}, dealer, vulnerability }
  bids            [{ seat, bid, timestamp }]
  chat_messages   [{ sender_id, text, timestamp }]
  bid_notes       [{ author_id, bid_index, text }]
```

---

## WebSocket Event Schema

All events use a common envelope for low overhead:

```json
{
  "type": "<event_type>",
  "session_id": "<uuid>",
  "sender_id": "<uuid>",
  "timestamp": "<iso8601>",
  "payload": {}
}
```

### Event Types

| Event | Direction | Payload | Purpose |
|-------|-----------|---------|---------|
| `ready` | Client -> Server | `{}` | Player signals readiness for next state |
| `unready` | Client -> Server | `{}` | Player retracts readiness |
| `ready_state` | Server -> Both | `{ player_a: bool, player_b: bool }` | Broadcasts current ready state |
| `deal` | Server -> Each | `{ hand: [...13 cards], dealer, vulnerability }` | Sends each player only their hand |
| `bid` | Client -> Server | `{ bid: "1NT" }` | Player submits a bid |
| `bid_made` | Server -> Both | `{ seat: "S", bid: "1NT", explanation: "..." }` | Broadcasts bid (human or AI) |
| `auction_complete` | Server -> Both | `{ contract, declarer, all_hands: {N, S, E, W} }` | Reveals all hands, enters review |
| `chat` | Client -> Server | `{ text: "..." }` | Chat message |
| `chat_broadcast` | Server -> Both | `{ sender_id, text, timestamp }` | Delivers chat to both players |
| `bid_note` | Client -> Server | `{ bid_index, text }` | Note on a specific bid |
| `bid_note_broadcast` | Server -> Both | `{ author_id, bid_index, text }` | Delivers note to both |
| `session_end` | Server -> Both | `{ reason: "player_left" \| "disconnect" }` | Session terminated |
| `heartbeat` | Bidirectional | `{}` | Presence detection (every 5s, timeout at 15s) |

### Resource Profile

- **Heartbeat:** 1 tiny JSON every 5s per client = ~200 bytes/5s
- **Bid events:** ~4-20 per hand = negligible
- **Chat:** User-driven, plain text, capped at 500 chars per message
- **Total per session:** < 1 KB/s sustained. Negligible server load.

---

## State Machine

```
LOBBY ──[both ready]──> DEALING ──[auto]──> BIDDING ──[auction complete]──> REVIEW
  ^                                            |                              |
  |                                       [disconnect/                  [both ready
  |                                        leave]                       for next]
  |                                            |                             |
  |                                            v                             v
  └──────────────────[session_end]─────── TERMINATED                    DEALING
```

All transitions except TERMINATED require mutual readiness. TERMINATED is reached by unilateral leave or disconnect timeout.

---

## Technical Feasibility

| Component | Mechanism | Status |
|-----------|-----------|--------|
| HTTP Polling (1s) | Bid sync + chat delivery via `/api/room/poll` | Implemented (WebSocket deferred) |
| Session Guard | `inRoom` flag hides solo nav + blocks navigation handler | Implemented |
| Heartbeat | Disconnect detection via poll 404 | Partial (no explicit heartbeat yet) |
| Ephemeral Store | In-memory `RoomStateManager` (thread-safe dict) | Implemented |
| Game Adapter | `room_api.py` translates room actions to engine calls | Implemented |

---

## Out of Scope (Future Phases)

| Phase | Feature |
|-------|---------|
| 2 | Card play after bidding |
| 2 | Signaling practice (attitude, count, suit preference) |
| 3 | Play against other pairs |
| Future | Convention customization per partnership |
| Future | Partnership hand history view (data tagged from Phase 1) |
| Future | Chat persistence beyond session |
| Future | Partner discovery / matchmaking |
| Future | Session pause/resume |

---

## Implementation Notes (2026-03-07)

### What Was Built

**Backend:**
- Room endpoints activated in `server.py` (16 total: create, join, leave, status, poll, ready, unready, chat, deal, start, bid, settings, start-play, play-card, play-state, chat GET)
- Peer model with mutual readiness gates (`/api/room/ready`, `/api/room/unready`)
- Chat via POST `/api/room/chat` + delivery via poll response (500 char limit)
- AI bid fix: `get_ai_bid_for_room()` now correctly maps short position names to full names for the bidding engine
- Host-only restrictions removed from deal, settings, and start-play endpoints
- `partnerships` table + `partnership_id` FK on `session_hands` (migration 019)

**Frontend:**
- `RoomContext.jsx` extended with: `iAmReady`, `partnerReady`, `bothReady`, `chatMessages`, `setReady()`, `setUnready()`, `sendChat()`
- Host-only checks removed from `dealHands()` and `updateSettings()`
- `leaveRoom()` clears readiness and chat state
- `TopNavigation` hides solo tabs when `inRoom=true`, shows "PARTNER PRACTICE" label
- `handleNavModuleSelect()` early-returns when in partner mode (defense in depth)

### Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Sync mechanism | 1s HTTP polling (not WebSocket) | Existing infrastructure, works now, < 1 KB/s per session. Upgrade to WebSocket when latency matters. |
| Chat storage | In-memory on `RoomState` | Ephemeral by spec. Survives browser refresh (server-side), destroyed on session end. |
| Readiness model | Both-ready gate on server | Prevents UI snapping. Server auto-deals when both ready. |
| Host/Guest removal | Peer model, session-creator only sets initial settings | Bridge partners are equals. Either can deal, change settings, leave. |
| Partnership persistence | DB table created, not yet wired to room flow | `partnership_id` FK ready for tagging. Wiring deferred to UI partner list implementation. |

### Pre-existing Code Leveraged

| Component | Lines | Already Existed |
|-----------|-------|----------------|
| `core/room_state.py` | 568 | Yes (extended with ready_state, chat_messages) |
| `routes/room_api.py` | 1129 | Yes (extended with ready, unready, chat endpoints; refactored peer model) |
| `RoomContext.jsx` | 622 | Yes (extended with readiness + chat state/actions) |
| Room UI components | ~600 | Yes (RoomLobby, RoomStatusBar, JoinRoomModal unchanged) |

### Completed (2026-03-08)

- [x] Chat sidebar UI component (ChatSidebar.jsx — collapsible, unread badge, auto-open)
- [x] Ready/Next Hand button in post-auction review (RoomStatusBar — peer model)
- [x] Fix bid synchronization race condition (removed duplicate AI bidding from poll handler)
- [x] Fix turn labels to distinguish partner vs AI turns
- [x] Increase disconnect timeout to 60s (was 15s — caused false mid-hand disconnects)
- [x] Peer model for play start (either player can click "Play This Hand")
- [x] Hand review phase (partner's hand revealed when auction completes)
- [x] Table rotation for North player (PlayTable accepts userPosition prop, rotates positions)
- [x] Heartbeat timeout for disconnect detection (60s timeout via poll-based heartbeat)

### Remaining (Phase 2)

- [ ] Wire `partnership_id` to hand history saves (schema ready, code path needs room→session bridge)
- [ ] Partner invite flow (generate shareable link, partner list in profile)
- [ ] SAYC feedback per bid in hand review (engine integration)
- [ ] Production deployment + testing with real users
- [ ] Integration tests for room lifecycle
- [ ] E2E tests for partner flow
