# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Bridge Bidding Training Application** that teaches players the Standard American Yellow Card (SAYC) bidding system. The app uses an AI bidding engine to simulate opponents and partner, providing real-time feedback on user bids.

**Stack:**
- **Backend**: Python Flask server (port 5001) with bidding engine
- **Frontend**: React app (port 3000)
- **Architecture**: Client-server with REST API communication

## Development Commands

### Backend (Python/Flask)
```bash
# From backend/ directory
python3 -m venv venv              # Create virtual environment (first time)
source venv/bin/activate          # Activate virtual environment
pip install -r requirements.txt   # Install dependencies

# Run server
python server.py                  # Starts Flask server on http://localhost:5001

# Run tests
pytest                            # Run all tests
pytest tests/test_opening_bids.py # Run specific test file
pytest -v                         # Verbose output
```

### Frontend (React)
```bash
# From frontend/ directory
npm install                       # Install dependencies
npm start                         # Start dev server on http://localhost:3000
npm test                          # Run tests
npm run build                     # Production build
```

### Running the Full App
1. Start backend: `cd backend && source venv/bin/activate && python server.py`
2. Start frontend: `cd frontend && npm start`
3. Access at http://localhost:3000

## Architecture

### Backend Structure

The backend implements a **modular AI bidding engine** with a state-based decision system:

**Core Flow:**
```
HTTP Request → server.py → BiddingEngine → DecisionEngine → Specialist Module → Bid + Explanation
```

**Key Components:**

1. **server.py** - Flask REST API with endpoints:
   - `/api/deal-hands` - Generates random hands
   - `/api/scenarios` - Lists predefined scenarios
   - `/api/load-scenario` - Loads scenario from scenarios.json
   - `/api/get-next-bid` - AI makes a bid
   - `/api/get-feedback` - Evaluates user's bid

2. **engine/bidding_engine.py** - Main orchestrator:
   - `BiddingEngine` maintains all specialist modules
   - Routes to appropriate module via `select_bidding_module()`
   - Performs universal legality checks on AI bids

3. **engine/ai/decision_engine.py** - State-based routing logic:
   - Determines bidding context (opening, competitive, partnership auction)
   - Selects appropriate specialist module based on features
   - Priority order: Conventions → Standard bidding modules

4. **Specialist Modules** (all extend `ConventionModule` interface):
   - **Opening Bids** (`opening_bids.py`): Initial bids (1NT, 2♣, suit openings)
   - **Responses** (`responses.py`): Responding to partner's opening
   - **Rebids** (`rebids.py`): Opener's second bid
   - **Overcalls** (`overcalls.py`): Bidding after opponent opens
   - **Advancer Bids** (`advancer_bids.py`): Bidding after partner overcalls
   - **Conventions** (`engine/ai/conventions/`):
     - Stayman, Jacoby Transfers, Blackwood, Preempts
     - Takeout Doubles, Negative Doubles (partially implemented)
     - Placeholder files: Michaels Cuebid, Unusual 2NT, Fourth Suit Forcing, Splinter Bids

5. **engine/hand.py** - `Hand` class:
   - Represents 13-card bridge hand
   - Auto-calculates: HCP, distribution points, suit lengths, suit HCP, balanced status
   - Uses `Card` namedtuple (rank, suit)

6. **engine/hand_constructor.py**:
   - `generate_hand_for_convention()` - Creates hands matching convention requirements
   - `generate_hand_with_constraints()` - Creates hands with specific HCP/shape constraints

7. **engine/ai/feature_extractor.py**:
   - Extracts contextual features from auction history
   - Determines partnerships, positions, opener relationships

### Frontend Structure

**Single-page React app** (`frontend/src/App.js`):

**Components:**
- `Card` - Visual card representation
- `HandAnalysis` - Shows HCP, distribution, suit breakdown, vulnerability
- `BiddingTable` - 4-column auction display (North/East/South/West)
- `BiddingBox` - Interactive bidding interface with legality checks
- `App` - Main orchestrator

**State Management:**
- `hand` - User's 13 cards (South position)
- `auction` - Array of `{bid, explanation}` objects
- `nextPlayerIndex` - Whose turn (0=North, 1=East, 2=South, 3=West)
- `isAiBidding` - Controls AI turn automation
- `vulnerability` - Tracks vulnerability rotation (None → NS → EW → Both)

**User Flow:**
1. User sees their hand (South) and bidding table
2. When it's South's turn, BiddingBox enables
3. User makes bid → Frontend sends to `/api/get-feedback`
4. Feedback displays (✅ correct or ⚠️ recommended alternative)
5. AI players automatically bid in sequence via `/api/get-next-bid`

### Scenarios System

**scenarios.json** defines training scenarios with hand generation rules:
- `generate_for_convention` - Uses convention's hand generator
- `constraints` - Specifies HCP range, suit lengths, balanced requirement
- Remaining positions get random hands from remaining deck

## Testing Strategy

**Backend Tests** (`backend/tests/`):
- Each module has dedicated test file (e.g., `test_opening_bids.py`)
- Tests verify bid selection and explanations
- Use `BiddingEngine` with feature dictionaries

**Frontend Tests**:
- React Testing Library setup in `setupTests.js`
- Component tests in `App.test.js`

## Key Bidding Engine Concepts

**Feature Extraction**: Every bid decision requires contextual features:
- Auction history
- Player positions (North/East/South/West)
- Opener relationship (Me/Partner/Opponent/None)
- Vulnerability
- Hand properties

**Module Interface**: All specialists implement:
```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    # Returns (bid, explanation) or None
```

**Decision Priority**: Decision engine checks in order:
1. Opening situation → Preempts → Opening Bids
2. Competitive situation → Overcalls → Takeout Doubles → Advancer
3. Partnership auction → Conventions (Stayman/Jacoby/Blackwood) → Natural responses/rebids

**Legality Enforcement**: `BiddingEngine._is_bid_legal()` prevents illegal bids:
- Higher level OR same level + higher suit ranking
- Special bids (Pass, X, XX) always legal

## Important Implementation Notes

- **Vulnerability rotation**: Cycles None → NS → EW → Both on each new deal
- **Bid format**: Strings like "1♠", "3NT", "Pass", "X", "XX"
- **Suit ranking**: ♣ < ♦ < ♥ < ♠ < NT
- **Current dealer**: Always North (dealer doesn't rotate yet)
- **User position**: Always South
- **AI delay**: 500ms between AI bids for UX

## Adding New Conventions

1. Create convention file in `backend/engine/ai/conventions/`
2. Extend `ConventionModule` base class
3. Implement `evaluate()` method
4. Register in `BiddingEngine.modules` dictionary
5. Add logic to `decision_engine.py` for when to check convention
6. (Optional) Add hand generator method for scenarios
7. Add test file in `backend/tests/`

## Common Pitfalls

- **Frontend bid legality**: BiddingBox has client-side legality check that must match backend logic
- **Feature extraction**: Specialist modules receive full features dict even if they don't use it
- **Module naming**: Decision engine returns module name as string (e.g., 'stayman'), not the class
- **Hand generation**: Scenarios consume cards from deck, so order matters
- **Auction indexing**: Position in auction determined by `index % 4` mapping to player positions
