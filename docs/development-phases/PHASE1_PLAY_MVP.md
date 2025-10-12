# Phase 1 Card Play MVP - Implementation Progress

## 🎯 Goal
Add card play functionality after bidding completes, allowing users to practice both bidding AND playing skills.

## ✅ Completed (So Far)

### 1. Core PlayEngine (`backend/engine/play_engine.py`)
**Stable foundation that won't change when AI improves**

**Classes:**
- `Contract` - Represents final contract (level, strain, declarer, doubled)
- `Trick` - One complete trick (4 cards)
- `PlayState` - Complete game state during play
- `PlayEngine` - Core logic (legal plays, trick winner, scoring)

**Key Methods:**
- `determine_contract()` - Extract contract from auction
- `is_legal_play()` - Enforce follow-suit rules
- `determine_trick_winner()` - Find trick winner (trump priority)
- `calculate_score()` - SAYC scoring (made/down, doubled, vulnerable)

### 2. Simple Play AI (`backend/engine/simple_play_ai.py`)
**Pluggable AI - can be upgraded without changing PlayEngine**

**Strategy:**
- **Opening leads:** 4th highest from longest, top of sequence
- **Following suit:** Third hand high, second hand low
- **Discarding:** Lowest from longest weak suit
- **Trumping:** Trump when profitable

**Class:**
- `SimplePlayAI` - Rule-based card selection
  - `choose_card()` - Main entry point (pluggable for Phase 2/3)
  - `_choose_lead()` - Opening lead logic
  - `_follow_suit()` - Following suit strategy
  - `_discard_or_trump()` - Void in led suit logic

## 🚧 Next Steps (Remaining)

### 3. Flask API Endpoints
**Add to `backend/server.py`:**

```python
# After bidding completes
@app.route('/api/start-play', methods=['POST'])
def start_play():
    """
    Called when bidding completes (3 consecutive passes)

    Input: { auction, all_hands, vulnerability }
    Output: { contract, opening_leader, dummy_position }
    """

@app.route('/api/play-card', methods=['POST'])
def play_card():
    """
    User plays a card

    Input: { card, position }
    Output: { legal, trick_complete, trick_winner, next_player }
    """

@app.route('/api/get-ai-play', methods=['POST'])
def get_ai_play():
    """
    AI plays a card

    Input: { position }
    Output: { card, explanation }
    """

@app.route('/api/get-play-state', methods=['GET'])
def get_play_state():
    """
    Get current play state

    Output: { current_trick, tricks_won, contract, dummy_hand, next_player }
    """

@app.route('/api/complete-play', methods=['GET'])
def complete_play():
    """
    Get final results after 13 tricks

    Output: { score, made, overtricks/undertricks, breakdown }
    """
```

### 4. Frontend UI Components
**Add to `frontend/src/App.js`:**

**New State:**
```javascript
const [gamePhase, setGamePhase] = useState('bidding'); // 'bidding' | 'playing' | 'review'
const [contract, setContract] = useState(null);
const [playState, setPlayState] = useState(null);
const [currentTrick, setCurrentTrick] = useState([]);
const [tricksWon, setTricksWon] = useState({N: 0, E: 0, S: 0, W: 0});
const [dummyHand, setDummyHand] = useState(null);
```

**New Components:**
```javascript
function ContractDisplay({ contract }) {
  // Show: "4♠ by South" with doubled indicator
}

function PlayTable({ currentTrick, contract, onCardClick }) {
  // Show 4 positions with cards played in center
  // Dummy hand visible after opening lead
}

function TrickHistory({ tricks }) {
  // Show previous tricks won
}

function ScoreDisplay({ score, contract }) {
  // Show final score after play
}
```

### 5. Game Flow Integration
```javascript
// In App.js
const handleBiddingComplete = async () => {
  // Detect 3 consecutive passes
  const lastThree = auction.slice(-3);
  if (lastThree.every(b => b.bid === 'Pass')) {
    // Start play phase
    const response = await fetch(`${API_URL}/api/start-play`, {
      method: 'POST',
      body: JSON.stringify({ auction, allHands, vulnerability })
    });

    const { contract, opening_leader } = await response.json();
    setGamePhase('playing');
    setContract(contract);
    setNextPlayerIndex(opening_leader);
  }
};

const handleCardPlay = async (card) => {
  // User clicks a card
  const response = await fetch(`${API_URL}/api/play-card`, {
    method: 'POST',
    body: JSON.stringify({ card, position: 'South' })
  });

  const { legal, trick_complete } = await response.json();

  if (trick_complete) {
    // Show trick winner, update scores
    // Wait 2 seconds, then clear trick
  }

  // AI plays next
  await handleAIPlay();
};
```

## 📦 Files Structure

```
backend/
  engine/
    play_engine.py          ✅ DONE - Core logic (stable)
    simple_play_ai.py       ✅ DONE - Rule-based AI (pluggable)
  server.py                 🚧 TODO - Add play endpoints

frontend/
  src/
    App.js                  🚧 TODO - Add play UI
    App.css                 🚧 TODO - Style play table
```

## 🎨 UI Mockup

```
┌─────────────────────────────────────┐
│   Contract: 4♠ by South   Vul: NS  │
│   Tricks Won: NS: 8  EW: 2          │
└─────────────────────────────────────┘

         ┌──────────────┐
         │    North     │
         │   (Dummy)    │
         │  ♠ A K Q 3   │
         │  ♥ 5 4       │
         │  ♦ K J 3     │
         │  ♣ 8 7 6     │
         └──────────────┘
              [♥3]

    [♦K] West         East [♠5]

         ┌──────────────┐
         │    South     │
         │    (You)     │
         │  [♠J T 9 8]  │  ← Click to play
         │  [♥A K Q]    │
         │  [♦A Q]      │
         │  [♣A K Q]    │
         └──────────────┘
```

## 🔌 Extensibility (Phase 2/3)

**Current architecture supports:**

1. **Better AI** - Just replace `SimplePlayAI` with:
   - `MinimaxAI` (Phase 2)
   - `DDSolverAI` (Phase 3)

2. **Hand Analysis** - Add after play:
   ```python
   from endplay.dds import solve_board
   optimal_tricks = solve_board(deal, contract)
   ```

3. **Hints** - During play:
   ```python
   hint = dds.get_best_card(position, state)
   ```

4. **Replay** - Store `trick_history` and allow replay

## 📊 Estimated Remaining Work

| Task | Hours | Status |
|------|-------|--------|
| Flask API endpoints | 4 | TODO |
| Frontend play UI | 6 | TODO |
| CSS styling | 2 | TODO |
| Integration testing | 2 | TODO |
| Bug fixes | 2 | TODO |
| **Total** | **16** | - |

## 🚀 Ready to Continue?

**Next immediate steps:**
1. Add Flask endpoints to `server.py`
2. Add play state management to frontend
3. Build PlayTable UI component
4. Test with a simple hand

Let me know when you're ready to continue!
