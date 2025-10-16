# Modular Architecture Plan: Decoupled Bidding & Card Play

**Date:** 2025-10-12
**Status:** 📋 Planning Document
**Goal:** Enable independent development and testing of bidding and card play modules

---

## Executive Summary

**Problem:** Current architecture tightly couples bidding and card play, making it inefficient to test and develop gameplay features independently.

**Solution:** Create three independent operational modes:
1. **Bidding-Only Mode** - Deal → Bid → Result (no play)
2. **Play-Only Mode** - Load contract + hands → Play → Score (no bidding)
3. **Integrated Mode** - Deal → Bid → Play → Score (full game)

**Benefits:**
- ✅ Test card play without going through bidding every time
- ✅ Develop bidding improvements without breaking play
- ✅ Parallel development on both systems
- ✅ Easier debugging and unit testing
- ✅ Clear separation of concerns
- ✅ Future: Allow loading saved hands/contracts for practice

---

## Current Architecture (Tightly Coupled)

```
┌─────────────────────────────────────────────────────────┐
│                     Current Flow                         │
└─────────────────────────────────────────────────────────┘

Frontend (App.js):
  gamePhase: 'dealing' → 'bidding' → 'playing' → 'complete'
         ↓                   ↓            ↓           ↓
    Deal Hands         Bidding       Card Play    Show Score
                       Engine
         └──────────── TIGHTLY COUPLED ────────────┘

Backend (server.py):
  Global State:
    - current_deal (hands)
    - current_vulnerability
    - current_play_state

  API Endpoints:
    /api/deal-hands → sets current_deal
    /api/get-next-bid → uses current_deal
    /api/start-play → uses current_deal + auction
    /api/play-card → uses current_play_state
```

**Issues:**
- Can't test play without bidding first
- Changing bidding affects play testing
- State management complex and coupled
- Hard to create specific play scenarios

---

## Proposed Modular Architecture

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Three Independent Modes                        │
└──────────────────────────────────────────────────────────────────┘

MODE 1: BIDDING ONLY
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: BiddingApp.js                                         │
│    ↓                                                              │
│  Backend: /api/bidding/*                                         │
│    ├─ /api/bidding/deal                                          │
│    ├─ /api/bidding/get-next-bid                                 │
│    ├─ /api/bidding/get-feedback                                 │
│    └─ /api/bidding/result (final contract + explanation)        │
└─────────────────────────────────────────────────────────────────┘

MODE 2: PLAY ONLY
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: PlayApp.js                                            │
│    ↓                                                              │
│  Backend: /api/play/*                                            │
│    ├─ /api/play/load-scenario (contract + 4 hands)              │
│    ├─ /api/play/start                                            │
│    ├─ /api/play/card                                             │
│    ├─ /api/play/ai-play                                          │
│    ├─ /api/play/state                                            │
│    └─ /api/play/result (final score)                            │
└─────────────────────────────────────────────────────────────────┘

MODE 3: INTEGRATED (Full Game)
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: IntegratedApp.js                                      │
│    ↓                                                              │
│  Backend: /api/game/*                                            │
│    ├─ Uses /api/bidding/* for bidding phase                     │
│    ├─ Uses /api/play/* for play phase                           │
│    └─ /api/game/session (manages full game session)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### Backend Module Structure

```
backend/
├── engine/
│   ├── bidding_engine.py           (existing - no changes)
│   ├── play_engine.py              (existing - no changes)
│   └── game_session.py             (NEW - orchestrates both)
│
├── services/                        (NEW directory)
│   ├── bidding_service.py          (NEW - bidding business logic)
│   ├── play_service.py             (NEW - play business logic)
│   └── game_service.py             (NEW - integrated game logic)
│
├── api/                             (NEW directory - route separation)
│   ├── bidding_routes.py           (NEW - /api/bidding/*)
│   ├── play_routes.py              (NEW - /api/play/*)
│   └── game_routes.py              (NEW - /api/game/*)
│
├── scenarios/                       (NEW directory)
│   ├── bidding_scenarios.json      (existing scenarios.json moved)
│   ├── play_scenarios.json         (NEW - pre-built play scenarios)
│   └── scenario_loader.py          (NEW - load any scenario type)
│
└── server.py                        (REFACTORED - route registration only)
```

### Frontend Module Structure

```
frontend/src/
├── apps/                            (NEW directory)
│   ├── BiddingApp.js               (NEW - bidding-only interface)
│   ├── PlayApp.js                  (NEW - play-only interface)
│   └── IntegratedApp.js            (NEW - full game flow)
│
├── components/
│   ├── bidding/                     (NEW - move bidding UI here)
│   │   ├── BiddingTable.js
│   │   ├── BiddingBox.js
│   │   ├── HandAnalysis.js
│   │   └── Card.js
│   │
│   ├── play/                        (NEW - move play UI here)
│   │   ├── PlayTable.js            (from PlayComponents.js)
│   │   ├── CurrentTrick.js
│   │   ├── PlayableCard.js
│   │   └── ScoreDisplay.js
│   │
│   └── shared/                      (NEW - common components)
│       ├── Card.js                  (shared between bidding/play)
│       └── VulnerabilityDisplay.js
│
├── services/                        (NEW directory)
│   ├── biddingService.js           (NEW - API calls for bidding)
│   ├── playService.js              (NEW - API calls for play)
│   └── gameService.js              (NEW - API calls for integrated)
│
├── App.js                           (REFACTORED - mode selector)
└── index.js                         (entry point)
```

---

## Implementation Plan

### Phase 1: Backend Refactoring (Estimated: 2-3 hours)

#### Step 1.1: Create Service Layer
**File:** `backend/services/play_service.py`

```python
"""
PlayService - Business logic for play-only mode
Manages play sessions independently of bidding
"""

from typing import Dict, List, Optional
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.hand import Hand, Card

class PlayService:
    def __init__(self):
        self.sessions = {}  # session_id → PlayState
        self.play_engine = PlayEngine()

    def create_session(self, session_id: str, contract: Contract,
                      hands: Dict[str, Hand], vulnerability: str) -> PlayState:
        """
        Create a new play session from scratch
        No bidding required - just provide contract and hands
        """
        opening_leader = self._get_opening_leader(contract.declarer)
        play_state = self.play_engine.create_play_session(
            contract, hands, opening_leader
        )
        self.sessions[session_id] = play_state
        return play_state

    def load_scenario(self, session_id: str, scenario: dict) -> PlayState:
        """
        Load a pre-defined play scenario
        Format: {
            "name": "3NT with club lead",
            "contract": {"level": 3, "strain": "NT", "declarer": "S"},
            "hands": {"N": [...], "E": [...], "S": [...], "W": [...]},
            "vulnerability": "None"
        }
        """
        contract = Contract(**scenario['contract'])
        hands = self._parse_hands(scenario['hands'])
        return self.create_session(session_id, contract, hands,
                                   scenario['vulnerability'])

    def get_session(self, session_id: str) -> Optional[PlayState]:
        """Get existing session"""
        return self.sessions.get(session_id)

    def play_card(self, session_id: str, position: str, card: Card) -> PlayState:
        """Play a card in the session"""
        play_state = self.sessions[session_id]
        return self.play_engine.play_card(play_state, position, card)

    def _get_opening_leader(self, declarer: str) -> str:
        """Opening leader is left of declarer"""
        order = ['N', 'E', 'S', 'W']
        idx = order.index(declarer)
        return order[(idx + 1) % 4]

    def _parse_hands(self, hands_dict: dict) -> Dict[str, Hand]:
        """Parse hand data from scenario"""
        # Implementation
        pass
```

#### Step 1.2: Create Play API Routes
**File:** `backend/api/play_routes.py`

```python
"""
Play-only API routes
No bidding required - directly create play scenarios
"""

from flask import Blueprint, request, jsonify
from services.play_service import PlayService
from engine.play_engine import Contract
from engine.hand import Hand, Card

play_bp = Blueprint('play', __name__, url_prefix='/api/play')
play_service = PlayService()

@play_bp.route('/scenarios', methods=['GET'])
def get_play_scenarios():
    """
    Return available pre-built play scenarios
    Users can select these to practice specific situations
    """
    from scenarios.scenario_loader import load_play_scenarios
    scenarios = load_play_scenarios()
    return jsonify({
        "scenarios": [
            {
                "id": s['id'],
                "name": s['name'],
                "description": s['description'],
                "contract": str(Contract(**s['contract'])),
                "difficulty": s.get('difficulty', 'intermediate')
            }
            for s in scenarios
        ]
    })

@play_bp.route('/load-scenario', methods=['POST'])
def load_scenario():
    """
    Load a specific play scenario
    Returns: session_id, play_state
    """
    data = request.get_json()
    scenario_id = data.get('scenario_id')

    from scenarios.scenario_loader import load_play_scenario_by_id
    scenario = load_play_scenario_by_id(scenario_id)

    session_id = f"play_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    play_state = play_service.load_scenario(session_id, scenario)

    return jsonify({
        "session_id": session_id,
        "contract": {
            "level": play_state.contract.level,
            "strain": play_state.contract.strain,
            "declarer": play_state.contract.declarer
        },
        "opening_leader": play_state.next_to_play,
        "dummy": play_state.dummy,
        "user_position": "S",  # Always South for now
        "scenario_name": scenario['name']
    })

@play_bp.route('/custom', methods=['POST'])
def create_custom():
    """
    Create custom play session with user-provided contract and hands
    Useful for testing specific situations
    """
    data = request.get_json()
    session_id = f"play_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    contract = Contract(**data['contract'])
    hands = parse_hands(data['hands'])
    vulnerability = data.get('vulnerability', 'None')

    play_state = play_service.create_session(
        session_id, contract, hands, vulnerability
    )

    return jsonify({"session_id": session_id, "status": "created"})

@play_bp.route('/<session_id>/state', methods=['GET'])
def get_state(session_id):
    """Get current play state"""
    play_state = play_service.get_session(session_id)
    if not play_state:
        return jsonify({"error": "Session not found"}), 404

    # Return full state (same as current /api/get-play-state)
    return jsonify(serialize_play_state(play_state))

@play_bp.route('/<session_id>/play-card', methods=['POST'])
def play_card(session_id):
    """Play a card"""
    data = request.get_json()
    position = data['position']
    card = Card(rank=data['card']['rank'], suit=data['card']['suit'])

    play_state = play_service.play_card(session_id, position, card)
    return jsonify(serialize_play_state(play_state))

@play_bp.route('/<session_id>/ai-play', methods=['POST'])
def ai_play(session_id):
    """AI plays next card"""
    # Use current AI difficulty
    from server import ai_instances, current_ai_difficulty

    play_state = play_service.get_session(session_id)
    ai = ai_instances[current_ai_difficulty]

    card = ai.choose_card(play_state)
    position = play_state.next_to_play

    play_state = play_service.play_card(session_id, position, card)
    return jsonify({
        "played": {"card": {"rank": card.rank, "suit": card.suit},
                  "position": position},
        "state": serialize_play_state(play_state)
    })

@play_bp.route('/<session_id>/result', methods=['GET'])
def get_result(session_id):
    """Get final result after all tricks played"""
    play_state = play_service.get_session(session_id)
    if not play_state.is_complete:
        return jsonify({"error": "Play not complete"}), 400

    # Calculate score (use existing logic)
    return jsonify({
        "contract": str(play_state.contract),
        "tricks_taken": play_state.tricks_taken_ns
                       if play_state.contract.declarer in ['N', 'S']
                       else play_state.tricks_taken_ew,
        "score": calculate_score(play_state)
    })
```

#### Step 1.3: Create Play Scenarios File
**File:** `backend/scenarios/play_scenarios.json`

```json
{
  "scenarios": [
    {
      "id": "3nt_basic",
      "name": "3NT - Basic Finesse",
      "description": "You're declarer in 3NT. Take the diamond finesse to make your contract.",
      "difficulty": "beginner",
      "contract": {
        "level": 3,
        "strain": "NT",
        "declarer": "S"
      },
      "hands": {
        "N": ["AK3", "Q54", "AKJ", "9876"],
        "E": ["J987", "J98", "Q876", "43"],
        "S": ["Q64", "AK3", "543", "AKQJ"],
        "W": ["T52", "T762", "T92", "T52"]
      },
      "vulnerability": "None",
      "teaching_points": [
        "Take the diamond finesse to make 9 tricks",
        "Cash club tricks first for entries"
      ]
    },
    {
      "id": "4h_trump_control",
      "name": "4♥ - Trump Control",
      "description": "Draw trumps methodically to avoid defenders ruffing your winners.",
      "difficulty": "intermediate",
      "contract": {
        "level": 4,
        "strain": "♥",
        "declarer": "S"
      },
      "hands": {
        "N": ["K84", "QJ5", "AK3", "9876"],
        "E": ["QJ97", "83", "QJ84", "AJ3"],
        "S": ["A63", "AKT9764", "65", "2"],
        "W": ["T52", "2", "T972", "KQT54"]
      },
      "vulnerability": "NS",
      "teaching_points": [
        "Draw trumps in 3 rounds",
        "Cash diamond winners before losing the lead"
      ]
    },
    {
      "id": "3nt_hold_up",
      "name": "3NT - Hold-Up Play",
      "description": "Use the hold-up play to break defenders' communication.",
      "difficulty": "intermediate",
      "contract": {
        "level": 3,
        "strain": "NT",
        "declarer": "S"
      },
      "hands": {
        "N": ["K73", "AQ4", "KJ6", "8765"],
        "E": ["J982", "J87", "T95", "KQ3"],
        "S": ["AQ6", "K53", "AQ42", "A42"],
        "W": ["T54", "T962", "873", "JT9"]
      },
      "vulnerability": "None",
      "teaching_points": [
        "Hold up your spade ace until the third round",
        "Run diamonds to make 9 tricks"
      ]
    }
  ]
}
```

---

### Phase 2: Frontend Refactoring (Estimated: 3-4 hours)

#### Step 2.1: Create Play-Only App
**File:** `frontend/src/apps/PlayApp.js`

```javascript
/**
 * PlayApp - Standalone card play interface
 * No bidding required - load scenarios or custom deals directly
 */

import React, { useState, useEffect } from 'react';
import { PlayTable, ScoreDisplay } from '../components/play/PlayTable';
import { playService } from '../services/playService';

function PlayApp() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [playState, setPlayState] = useState(null);
  const [gamePhase, setGamePhase] = useState('scenario-select'); // or 'playing', 'complete'

  // Load available scenarios on mount
  useEffect(() => {
    playService.getScenarios().then(setScenarios);
  }, []);

  const handleScenarioSelect = async (scenarioId) => {
    const response = await playService.loadScenario(scenarioId);
    setSessionId(response.session_id);
    setSelectedScenario(response);

    // Fetch initial state
    const state = await playService.getState(response.session_id);
    setPlayState(state);
    setGamePhase('playing');
  };

  const handleCardPlay = async (card) => {
    const state = await playService.playCard(sessionId, 'S', card);
    setPlayState(state);

    // Check if complete
    if (state.is_complete) {
      setGamePhase('complete');
    }
  };

  const handleAIPlay = async () => {
    const response = await playService.aiPlay(sessionId);
    setPlayState(response.state);

    if (response.state.is_complete) {
      setGamePhase('complete');
    }
  };

  if (gamePhase === 'scenario-select') {
    return (
      <div className="play-app">
        <h1>Card Play Practice</h1>
        <div className="scenario-list">
          {scenarios.map(scenario => (
            <div key={scenario.id} className="scenario-card">
              <h3>{scenario.name}</h3>
              <p>{scenario.description}</p>
              <p>Contract: {scenario.contract}</p>
              <p>Difficulty: {scenario.difficulty}</p>
              <button onClick={() => handleScenarioSelect(scenario.id)}>
                Play This Scenario
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (gamePhase === 'playing') {
    return (
      <div className="play-app">
        <h2>{selectedScenario.scenario_name}</h2>
        <PlayTable
          playState={playState}
          onCardPlay={handleCardPlay}
          onAIPlay={handleAIPlay}
        />
      </div>
    );
  }

  if (gamePhase === 'complete') {
    return (
      <div className="play-app">
        <h2>Hand Complete</h2>
        <ScoreDisplay playState={playState} />
        <button onClick={() => setGamePhase('scenario-select')}>
          Try Another Scenario
        </button>
      </div>
    );
  }
}

export default PlayApp;
```

#### Step 2.2: Create Play Service
**File:** `frontend/src/services/playService.js`

```javascript
/**
 * Play Service - API calls for play-only mode
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export const playService = {
  // Get available scenarios
  getScenarios: async () => {
    const response = await fetch(`${API_URL}/api/play/scenarios`);
    const data = await response.json();
    return data.scenarios;
  },

  // Load a specific scenario
  loadScenario: async (scenarioId) => {
    const response = await fetch(`${API_URL}/api/play/load-scenario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: scenarioId })
    });
    return response.json();
  },

  // Create custom play session
  createCustom: async (contract, hands, vulnerability) => {
    const response = await fetch(`${API_URL}/api/play/custom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contract, hands, vulnerability })
    });
    return response.json();
  },

  // Get current state
  getState: async (sessionId) => {
    const response = await fetch(`${API_URL}/api/play/${sessionId}/state`);
    return response.json();
  },

  // Play a card
  playCard: async (sessionId, position, card) => {
    const response = await fetch(`${API_URL}/api/play/${sessionId}/play-card`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ position, card })
    });
    return response.json();
  },

  // AI plays
  aiPlay: async (sessionId) => {
    const response = await fetch(`${API_URL}/api/play/${sessionId}/ai-play`, {
      method: 'POST'
    });
    return response.json();
  },

  // Get final result
  getResult: async (sessionId) => {
    const response = await fetch(`${API_URL}/api/play/${sessionId}/result`);
    return response.json();
  }
};
```

#### Step 2.3: Create Mode Selector
**File:** `frontend/src/App.js` (refactored)

```javascript
import React, { useState } from 'react';
import BiddingApp from './apps/BiddingApp';
import PlayApp from './apps/PlayApp';
import IntegratedApp from './apps/IntegratedApp';
import './App.css';

function App() {
  const [mode, setMode] = useState('mode-select');

  if (mode === 'mode-select') {
    return (
      <div className="app-container">
        <h1>Bridge Training Application</h1>
        <div className="mode-selector">
          <div className="mode-card" onClick={() => setMode('bidding')}>
            <h2>🃏 Bidding Practice</h2>
            <p>Practice bidding conventions and sequences</p>
            <ul>
              <li>Learn SAYC bidding system</li>
              <li>Practice opening bids, responses, rebids</li>
              <li>Get AI feedback on your bids</li>
            </ul>
          </div>

          <div className="mode-card" onClick={() => setMode('play')}>
            <h2>🎯 Card Play Practice</h2>
            <p>Practice declarer play and defense</p>
            <ul>
              <li>Pre-built scenarios (finesses, hold-ups, etc.)</li>
              <li>Focus on card play technique</li>
              <li>No bidding required</li>
            </ul>
          </div>

          <div className="mode-card" onClick={() => setMode('integrated')}>
            <h2>🎮 Full Game</h2>
            <p>Complete bridge experience</p>
            <ul>
              <li>Deal → Bid → Play → Score</li>
              <li>Full game simulation</li>
              <li>Train end-to-end</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (mode === 'bidding') {
    return (
      <div>
        <button onClick={() => setMode('mode-select')}>← Back to Menu</button>
        <BiddingApp />
      </div>
    );
  }

  if (mode === 'play') {
    return (
      <div>
        <button onClick={() => setMode('mode-select')}>← Back to Menu</button>
        <PlayApp />
      </div>
    );
  }

  if (mode === 'integrated') {
    return (
      <div>
        <button onClick={() => setMode('mode-select')}>← Back to Menu</button>
        <IntegratedApp />
      </div>
    );
  }
}

export default App;
```

---

### Phase 3: Testing Setup (Estimated: 1-2 hours)

#### Test Structure

```
backend/tests/
├── unit/
│   ├── test_play_service.py        (NEW - test play service)
│   ├── test_bidding_service.py     (NEW - test bidding service)
│   └── test_scenario_loader.py     (NEW - test scenario loading)
│
├── integration/
│   ├── test_play_routes.py         (NEW - test play API)
│   ├── test_bidding_routes.py      (NEW - test bidding API)
│   └── test_game_routes.py         (NEW - test integrated API)
│
└── scenarios/
    └── test_play_scenarios.py       (NEW - validate scenarios)
```

#### Example Test
**File:** `backend/tests/unit/test_play_service.py`

```python
import pytest
from services.play_service import PlayService
from engine.play_engine import Contract
from engine.hand import Hand, Card

def test_create_session():
    service = PlayService()
    contract = Contract(level=3, strain='NT', declarer='S')
    hands = {
        'N': Hand([Card('A', '♠'), ...]),
        'E': Hand([Card('K', '♠'), ...]),
        'S': Hand([Card('Q', '♠'), ...]),
        'W': Hand([Card('J', '♠'), ...])
    }

    play_state = service.create_session('test1', contract, hands, 'None')

    assert play_state.contract == contract
    assert play_state.next_to_play == 'W'  # Left of declarer
    assert play_state.dummy == 'N'
    assert not play_state.dummy_revealed

def test_load_scenario():
    service = PlayService()
    scenario = {
        "name": "Test",
        "contract": {"level": 4, "strain": "♥", "declarer": "S"},
        "hands": {...},
        "vulnerability": "NS"
    }

    play_state = service.load_scenario('test2', scenario)

    assert play_state.contract.level == 4
    assert play_state.contract.strain == '♥'
```

---

## Migration Strategy

### Option A: Big Bang (Not Recommended)
Refactor everything at once → High risk of breakage

### Option B: Gradual Migration (Recommended)

**Week 1: Backend Setup**
- Create service layer (play_service.py, bidding_service.py)
- Create new API routes (/api/play/*, /api/bidding/*)
- Keep existing routes working (backward compatibility)
- Create play scenarios file
- Write tests for new services

**Week 2: Frontend Setup**
- Create PlayApp.js (play-only interface)
- Create playService.js (API client)
- Test play-only mode thoroughly
- Keep existing App.js untouched

**Week 3: Extract Bidding**
- Create BiddingApp.js (bidding-only interface)
- Create biddingService.js
- Test bidding-only mode

**Week 4: Integration**
- Create mode selector in App.js
- Create IntegratedApp.js (combines both)
- Full testing of all three modes
- Deprecate old routes

**Week 5: Cleanup**
- Remove deprecated code
- Update documentation
- Performance optimization

---

## Benefits of This Architecture

### Development
✅ **Parallel Work** - Work on bidding and play independently
✅ **Faster Testing** - Test play without bidding overhead
✅ **Clear Boundaries** - Each module has clear responsibility
✅ **Easier Debugging** - Isolate issues to specific modules

### User Experience
✅ **Targeted Practice** - Practice just bidding or just play
✅ **Scenario Library** - Pre-built situations for learning
✅ **Custom Scenarios** - Load specific hands for analysis
✅ **Progressive Learning** - Master each aspect separately

### Maintainability
✅ **Decoupled** - Changes to bidding don't affect play
✅ **Testable** - Unit test each module independently
✅ **Extensible** - Easy to add new modes (e.g., defense-only)
✅ **Reusable** - Services can be used by multiple interfaces

---

## Future Enhancements

### Scenario Features
- **Save/Load Hands** - Save interesting hands for later
- **Scenario Editor** - Create custom scenarios in UI
- **Difficulty Progression** - Scenarios from beginner to expert
- **Teaching Mode** - Hints and explanations during play

### Analysis Features
- **Double Dummy Analysis** - Show optimal play
- **Play Review** - Analyze your play after completion
- **Alternative Lines** - Show what would have happened
- **Statistics** - Track your success rate by scenario type

### Multiplayer (Future)
- **Remote Play** - Play against human opponents
- **Simultaneous Pairs** - Multiple tables, same deals
- **Teaching Mode** - Instructor watches and guides

---

## Implementation Checklist

### Backend
- [ ] Create `services/` directory
- [ ] Implement `play_service.py`
- [ ] Implement `bidding_service.py`
- [ ] Create `api/` directory
- [ ] Implement `play_routes.py`
- [ ] Implement `bidding_routes.py`
- [ ] Create `scenarios/play_scenarios.json`
- [ ] Implement `scenario_loader.py`
- [ ] Write unit tests for services
- [ ] Write integration tests for routes
- [ ] Update server.py to register new blueprints

### Frontend
- [ ] Create `apps/` directory
- [ ] Implement `PlayApp.js`
- [ ] Implement `BiddingApp.js`
- [ ] Implement `IntegratedApp.js`
- [ ] Create `services/` directory
- [ ] Implement `playService.js`
- [ ] Implement `biddingService.js`
- [ ] Refactor `App.js` as mode selector
- [ ] Organize components into subdirectories
- [ ] Create scenario selection UI
- [ ] Test each mode independently

### Testing
- [ ] Test play-only mode end-to-end
- [ ] Test bidding-only mode end-to-end
- [ ] Test integrated mode end-to-end
- [ ] Test scenario loading
- [ ] Test custom deal creation
- [ ] Performance testing

### Documentation
- [ ] Update CLAUDE.md with new architecture
- [ ] Document play scenarios format
- [ ] Create API documentation for new routes
- [ ] Update testing guide
- [ ] Create user guide for each mode

---

## Estimated Timeline

**Total Effort:** 2-3 weeks (assuming part-time work)

**Phase 1 (Backend):** 2-3 days
**Phase 2 (Frontend):** 3-4 days
**Phase 3 (Testing):** 2-3 days
**Phase 4 (Integration):** 2-3 days
**Phase 5 (Documentation):** 1-2 days

**Quick Start Option:** Implement play-only mode first (Phase 1 + subset of Phase 2) = 1 week

---

## Questions to Consider

1. **User Position**: Should play-only mode always put user as South, or allow choosing position?
2. **AI Difficulty**: Should scenarios have recommended AI difficulty, or always use user's selected difficulty?
3. **Scenario Format**: PBN format vs custom JSON?
4. **Hints**: Should play scenarios provide hints/teaching points during play?
5. **Replay**: Should users be able to replay the same scenario multiple times?

---

**Next Step:** Review this plan and decide:
- Implement full plan (2-3 weeks)
- Quick start with play-only mode (1 week)
- Modify/adjust the approach

**Recommendation:** Start with play-only mode (backend services + PlayApp.js) to prove the concept, then expand to full modular architecture.
