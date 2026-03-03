# Architecture Detail Reference

**Referenced from:** `CLAUDE.md` — Architecture section

This file contains detailed subsystem documentation. For the high-level architecture overview, see `CLAUDE.md`.

---

## Frontend Structure

**Single-page React app** (`frontend/src/App.js`):

### Main Components
- **Card** — Visual card representation
- **LibraryCard** — Professional SVG cards for East/West (vertical layout)
- **HandAnalysis** — Shows HCP, distribution, suit breakdown, vulnerability
- **BiddingTable** — 4-column auction display (North/East/South/West) with dealer indicator "(D)"
- **BiddingBox** — Interactive bidding interface with legality checks
- **PlayTable** — Card play interface with trick display
- **LearningDashboard** — Analytics modal with 7 statistics cards
- **SimpleLogin** — Email/phone authentication
- **App** — Main orchestrator

### State Management
- **Authentication**: AuthContext provides `userId`, `isAuthenticated`, `login()`, `logout()`
- **Hand**: User's 13 cards (South position)
- **Auction**: Array of `{bid, explanation}` objects
- **Play State**: Current trick, cards played, tricks won
- **Next Player**: Whose turn (0=North, 1=East, 2=South, 3=West)
- **Dealer**: Rotates North -> East -> South -> West (Chicago system)
- **Vulnerability**: Tracks vulnerability rotation (None -> NS -> EW -> Both)

### User Flow
1. User logs in (email/phone) or continues as guest
2. User sees their hand (South) and bidding table
3. Bidding phase: User bids -> Receives feedback -> AI players bid
4. Play phase: Declarer and dummy identified -> Cards played -> Tricks evaluated
5. Scoring: Contract result calculated -> Dashboard updated
6. Dashboard: View statistics and learning insights

---

## Multi-User System

### Authentication

**SimpleLogin System:**
- Email or phone only (no password)
- Automatic account creation on first login
- Guest mode for quick play
- Persistent login via localStorage

**API:** `/api/auth/simple-login`
**Frontend:** `frontend/src/components/auth/SimpleLogin.jsx`, `frontend/src/contexts/AuthContext.jsx`

### User Separation

**Each user has:**
- Unique `user_id` in database
- Isolated bidding history (`bidding_decisions` table)
- Separate dashboard analytics
- Personal game sessions (`game_sessions` table)
- Individual progress tracking

**Data Flow:**
```javascript
// User logs in -> userId stored in context
const { userId } = useAuth();

// All API calls include user_id
fetch('/api/evaluate-bid', {
  body: JSON.stringify({ user_id: userId, ...})
})

// Backend filters all queries by user_id
SELECT * FROM bidding_decisions WHERE user_id = ?
```

**Database Schema:**
```sql
users: id, email, phone, display_name, created_at
bidding_decisions: id, user_id, user_bid, optimal_bid, score, timestamp
hand_analyses: id, user_id, hand_id, hcp, shape, timestamp
game_sessions: id, user_id, session_type, hands_completed, timestamp
session_hands: id, session_id, score, declarer_made, contract, timestamp
```

---

## Card Play System

### PlayEngine

**File:** `backend/engine/play_engine.py`

**Responsibilities:**
- Execute complete hand play
- Manage trick evaluation
- Determine trick winners
- Track contract progress
- Calculate final scores

### AI Levels (1-10)

**Level 1-6: SimplePlayAI**
- Basic heuristics (high card, trump management)
- Fast performance (<1s per hand)
- Success rate: 40-60%

**Level 7-8: MinimaxPlayAI**
- Lookahead search (depth 2-3)
- Position evaluation
- Success rate: 70-80%
- Moderate performance (2-3s per hand)

**Level 9-10: DDS (Double Dummy Solver)**
- Perfect play analysis using solve_board
- Success rate: 95%+ (optimal double-dummy play)
- **Fast performance (<1ms per play)** — suitable for real-time
- **Default on production (Linux)** — uses endplay library
- **Linux only** (crashes on macOS M1/M2)

### Play Flow

```
Deal hands -> Bidding -> Contract established ->
  Play loop:
    1. Determine current player
    2. Get legal plays
    3. AI selects card (or user input)
    4. Add card to trick
    5. Evaluate trick winner
    6. Next trick
  -> Calculate final score
```

**Frontend:** `frontend/src/PlayComponents.js` (PlayableCard, CurrentTrick, PlayTable)
**Backend:** `backend/engine/play/ai/` (simple_play_ai.py, minimax_play_ai.py)

---

## Key Features

### Dashboard Analytics
- **Bidding Quality Tracking:** Optimal rate, avg score, error rate
- **Recent Decisions:** Last 10 bids with feedback
- **Gameplay Statistics:** Contracts made/failed, declarer success rate
- **Learning Insights:** Patterns, growth areas, recommendations
- **Real-time Updates:** Dashboard refreshes on modal reopen (key-based remounting)

**API:** `/api/analytics/dashboard?user_id={user_id}`
**Implementation:** Uses `key={Date.now()}` to force remount and fresh data fetch

### Bidding Feedback System
- **Real-time Evaluation:** Every user bid evaluated against optimal
- **Correctness Ratings:** Optimal (10), Acceptable (7-9), Suboptimal (4-6), Error (0-3)
- **Scoring:** 0-10 scale with detailed feedback
- **Improvement Hints:** Specific suggestions for better bids
- **Historical Tracking:** All decisions stored per user

**API:** `/api/evaluate-bid`

### Chicago Rotation
- **4-Hand Sessions:** Complete Chicago-style sessions
- **Dealer Rotation:** North -> East -> South -> West (fully implemented)
- **Vulnerability Rotation:** None -> NS -> EW -> Both
- **Score Tracking:** North-South vs East-West
- **Dealer Indicator:** "(D)" shows in bidding table

### Card Display
- **Professional SVG Cards:** External library (@letele/playing-cards)
- **Responsive Layouts:** Horizontal (North/South) and vertical (East/West)
- **Proper Overlap:** 80% overlap for vertical hands (East/West)
- **Suit Separation:** Visual grouping by suit
- **LibraryCard Component:** Handles East/West vertical display

### Scenarios System

**scenarios.json** defines training scenarios with hand generation rules:
- `generate_for_convention` — Uses convention's hand generator
- `constraints` — Specifies HCP range, suit lengths, balanced requirement
- Remaining positions get random hands from remaining deck
