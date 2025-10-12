# Shared Infrastructure Architecture: Modular Bidding & Play

**Date:** 2025-10-12
**Status:** 📋 Revised Planning Document
**Supersedes:** MODULAR_ARCHITECTURE_PLAN.md (concept retained, implementation revised)

---

## Executive Summary

**Key Insight:** Bidding and play should share common infrastructure (hand generation, display components, user management) while remaining **operationally independent** for development and testing.

**Architecture Principle:**
```
┌─────────────────────────────────────────────────────────────┐
│              SHARED INFRASTRUCTURE LAYER                     │
│  (Hand generation, display, scoring, user management)        │
└─────────────────────────────────────────────────────────────┘
                    ↓           ↓           ↓
        ┌───────────────┬──────────────┬─────────────┐
        │  Bidding      │   Play       │  Integrated │
        │  Module       │   Module     │  Module     │
        └───────────────┴──────────────┴─────────────┘
```

**Not duplicating:** Hand generation, card display, user state
**Duplicating:** Operational flow, API routes, UI apps

---

## Current Shared Components Analysis

### Backend Shared (Already Exist)

```python
engine/
├── hand.py                    ✅ SHARED - Card and Hand classes
├── hand_constructor.py        ✅ SHARED - Hand generation logic
├── bidding_engine.py          🔵 BIDDING ONLY
├── play_engine.py             🟢 PLAY ONLY
└── scoring.py                 ✅ SHARED - Bridge scoring rules
```

**Shared Components:**
1. **`Hand` class** - Represents 13-card bridge hand
   - Properties: HCP, distribution, suit lengths, balanced
   - Used by both bidding and play

2. **`Card` namedtuple** - Individual card representation
   - Used by both bidding and play

3. **`hand_constructor.py`** - Hand generation utilities
   - `generate_hand_with_constraints()` - Used by scenarios
   - `generate_hand_for_convention()` - Used by bidding scenarios
   - Should be used by play scenarios too

4. **Scoring logic** - Calculate final scores
   - Used by both bidding evaluation and play results

### Frontend Shared (Currently in App.js)

```javascript
// Components that should be shared
1. Card component (lines 9-30)          ✅ SHARED
2. HandAnalysis (lines 31-34)           ✅ SHARED
3. PlayerHand display (lines 36-55)     ✅ SHARED
4. VulnerabilityDisplay                 ✅ SHARED

// Components that are module-specific
5. BiddingTable (lines 56-67)           🔵 BIDDING ONLY
6. BiddingBox (lines 68-103)            🔵 BIDDING ONLY
7. PlayTable (PlayComponents.js)        🟢 PLAY ONLY
```

---

## Revised Architecture: Shared Infrastructure

### Backend Structure

```
backend/
├── engine/                             (SHARED CORE)
│   ├── hand.py                         ✅ Shared by all
│   ├── hand_constructor.py             ✅ Shared by all
│   ├── scoring.py                      ✅ Shared by all
│   ├── bidding_engine.py               🔵 Bidding module uses
│   └── play_engine.py                  🟢 Play module uses
│
├── core/                               (NEW - Shared utilities)
│   ├── session_manager.py              ✅ Manage user sessions
│   ├── scenario_loader.py              ✅ Load bidding/play scenarios
│   ├── deal_generator.py               ✅ Generate deals (uses hand_constructor)
│   └── user_manager.py                 ✅ User accounts, progress (future)
│
├── modules/                            (NEW - Independent modules)
│   ├── bidding/
│   │   ├── bidding_service.py          🔵 Bidding session logic
│   │   ├── bidding_routes.py           🔵 API: /api/bidding/*
│   │   └── bidding_scenarios.json      🔵 Bidding practice scenarios
│   │
│   └── play/
│       ├── play_service.py             🟢 Play session logic
│       ├── play_routes.py              🟢 API: /api/play/*
│       └── play_scenarios.json         🟢 Play practice scenarios
│
├── api/                                (NEW - Route registration)
│   ├── __init__.py                     Register all blueprints
│   └── integrated_routes.py            Full game flow routes
│
└── server.py                           (REFACTORED - lightweight)
    - Register blueprints
    - Shared config
    - CORS, error handling
```

### Frontend Structure

```
frontend/src/
├── shared/                             (NEW - Shared components)
│   ├── components/
│   │   ├── Card.js                     ✅ Card display
│   │   ├── HandDisplay.js              ✅ Show 13 cards by suit
│   │   ├── HandAnalysis.js             ✅ HCP/distribution
│   │   ├── VulnerabilityDisplay.js     ✅ Show vulnerability
│   │   └── ScoreDisplay.js             ✅ Show final score
│   │
│   ├── services/
│   │   ├── apiClient.js                ✅ Common API utilities
│   │   └── sessionService.js           ✅ Session management
│   │
│   └── utils/
│       ├── cardUtils.js                ✅ Card sorting, formatting
│       ├── scoringUtils.js             ✅ Score calculation
│       └── suitOrder.js                ✅ getSuitOrder() function
│
├── modules/                            (NEW - Independent modules)
│   ├── bidding/
│   │   ├── BiddingApp.js               🔵 Bidding practice UI
│   │   ├── components/
│   │   │   ├── BiddingTable.js         🔵 Auction display
│   │   │   ├── BiddingBox.js           🔵 Bid selector
│   │   │   └── FeedbackPanel.js        🔵 Bid evaluation
│   │   └── services/
│   │       └── biddingService.js       🔵 API calls for bidding
│   │
│   └── play/
│       ├── PlayApp.js                  🟢 Play practice UI
│       ├── components/
│       │   ├── PlayTable.js            🟢 Play area (from PlayComponents)
│       │   ├── CurrentTrick.js         🟢 Trick display
│       │   ├── PlayableCard.js         🟢 Clickable card
│       │   └── ScenarioSelector.js     🟢 Choose play scenario
│       └── services/
│           └── playService.js          🟢 API calls for play
│
├── integrated/                         (NEW - Full game)
│   ├── IntegratedApp.js                Full game flow
│   └── GameFlowManager.js              Orchestrate bidding → play
│
├── App.js                              (REFACTORED - Mode selector)
└── index.js                            Entry point
```

---

## Key Design Principles

### 1. Share Infrastructure, Not Business Logic

**✅ DO SHARE:**
- Hand and Card data structures
- Hand generation utilities
- Display components (cards, hands, analysis)
- Scoring calculations
- User management (future)
- Session management

**❌ DON'T SHARE:**
- Bidding engine ← Only bidding module uses
- Play engine ← Only play module uses
- Bidding UI components ← Specific to bidding
- Play UI components ← Specific to play
- Operational flow ← Each module has own flow

### 2. Modules Import from Shared, Not Each Other

```python
# ✅ GOOD: Module imports from shared
from engine.hand import Hand, Card
from core.deal_generator import generate_deal
from modules.play.play_service import PlayService

# ❌ BAD: Modules importing from each other
from modules.bidding.bidding_service import BiddingService  # in play module
from modules.play.play_service import PlayService  # in bidding module
```

### 3. Session Isolation

Each module manages its own sessions independently:

```python
# Bidding sessions
bidding_sessions = {
    "bidding_session_123": BiddingState(...),
    "bidding_session_456": BiddingState(...)
}

# Play sessions
play_sessions = {
    "play_session_789": PlayState(...),
    "play_session_abc": PlayState(...)
}

# Integrated game sessions
game_sessions = {
    "game_session_xyz": {
        "bidding_session": "bidding_session_123",
        "play_session": "play_session_789",
        "phase": "playing"
    }
}
```

---

## Implementation Plan (Revised)

### Phase 1: Extract Shared Components (2-3 days)

#### Step 1.1: Backend - Create Core Layer

**File:** `backend/core/deal_generator.py`

```python
"""
Shared deal generation - used by both bidding and play modules
"""

from engine.hand_constructor import generate_hand_with_constraints
from engine.hand import Hand, Card
from typing import Dict, List, Tuple
import random

class DealGenerator:
    """Generate deals for bidding or play scenarios"""

    @staticmethod
    def generate_random_deal() -> Dict[str, Hand]:
        """
        Generate completely random 4 hands
        Used by: Bidding practice, random play scenarios
        """
        deck = Card.full_deck()
        random.shuffle(deck)

        return {
            'N': Hand(deck[0:13]),
            'E': Hand(deck[13:26]),
            'S': Hand(deck[26:39]),
            'W': Hand(deck[39:52])
        }

    @staticmethod
    def generate_constrained_deal(constraints: Dict) -> Dict[str, Hand]:
        """
        Generate deal with specific constraints

        Example constraints:
        {
            'S': {'hcp_range': (12, 14), 'is_balanced': True},
            'N': {'hcp_range': (15, 17), 'is_balanced': True},
            'E': None,  # random
            'W': None   # random
        }

        Used by: Bidding scenarios, teaching scenarios
        """
        deck = list(Card.full_deck())
        hands = {}

        for position in ['N', 'E', 'S', 'W']:
            if constraints.get(position):
                hand, deck = generate_hand_with_constraints(
                    constraints[position], deck
                )
                hands[position] = hand
            else:
                # Random from remaining deck
                random.shuffle(deck)
                hands[position] = Hand(deck[:13])
                deck = deck[13:]

        return hands

    @staticmethod
    def generate_for_contract(contract_str: str, declarer: str) -> Dict[str, Hand]:
        """
        Generate plausible hands for a specific contract

        Example: "3NT" by South
        - S+N should have ~25 HCP combined
        - Both likely balanced

        Used by: Play scenarios
        """
        level = int(contract_str[0])
        strain = contract_str[1:]

        # Determine HCP needed for contract
        hcp_needed = 20 + (level - 1) * 3  # Rough estimate

        # Split HCP between declarer and dummy
        declarer_hcp = random.randint(12, 15)
        dummy_hcp = hcp_needed - declarer_hcp

        # Build constraints
        dummy_pos = {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}[declarer]

        constraints = {
            declarer: {'hcp_range': (declarer_hcp - 1, declarer_hcp + 1)},
            dummy_pos: {'hcp_range': (dummy_hcp - 1, dummy_hcp + 1)}
        }

        if strain == 'NT':
            constraints[declarer]['is_balanced'] = True
            constraints[dummy_pos]['is_balanced'] = True

        return DealGenerator.generate_constrained_deal(constraints)
```

**File:** `backend/core/scenario_loader.py`

```python
"""
Unified scenario loading for bidding and play scenarios
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

class ScenarioLoader:
    """Load scenarios from JSON files"""

    def __init__(self, scenarios_dir: str = "scenarios"):
        self.scenarios_dir = Path(scenarios_dir)

    def load_bidding_scenarios(self) -> List[Dict]:
        """Load bidding practice scenarios"""
        file_path = self.scenarios_dir / "bidding_scenarios.json"
        with open(file_path) as f:
            data = json.load(f)
        return data.get('scenarios', [])

    def load_play_scenarios(self) -> List[Dict]:
        """Load play practice scenarios"""
        file_path = self.scenarios_dir / "play_scenarios.json"
        with open(file_path) as f:
            data = json.load(f)
        return data.get('scenarios', [])

    def get_scenario_by_id(self, scenario_type: str, scenario_id: str) -> Optional[Dict]:
        """Get specific scenario by ID"""
        if scenario_type == 'bidding':
            scenarios = self.load_bidding_scenarios()
        elif scenario_type == 'play':
            scenarios = self.load_play_scenarios()
        else:
            return None

        for scenario in scenarios:
            if scenario['id'] == scenario_id:
                return scenario
        return None
```

**File:** `backend/core/session_manager.py`

```python
"""
Shared session management
Tracks active bidding/play sessions and user state
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class SessionManager:
    """
    Manage active sessions across all modules
    Future: Connect to user accounts, save progress
    """

    def __init__(self):
        self.sessions = {}  # session_id → session_data
        self.user_sessions = {}  # user_id → [session_ids]

    def create_session(self, session_type: str, user_id: Optional[str] = None) -> str:
        """
        Create a new session

        Args:
            session_type: 'bidding', 'play', or 'game'
            user_id: Optional user identifier (for future use)

        Returns:
            session_id
        """
        session_id = f"{session_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        self.sessions[session_id] = {
            'type': session_type,
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'data': None  # Module-specific data stored here
        }

        if user_id:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        session = self.sessions.get(session_id)
        if session:
            session['last_accessed'] = datetime.now()
        return session

    def update_session(self, session_id: str, data: Any):
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id]['data'] = data
            self.sessions[session_id]['last_accessed'] = datetime.now()

    def delete_session(self, session_id: str):
        """Delete session"""
        if session_id in self.sessions:
            user_id = self.sessions[session_id]['user_id']
            del self.sessions[session_id]

            if user_id and user_id in self.user_sessions:
                self.user_sessions[user_id].remove(session_id)

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        expired = [
            sid for sid, sess in self.sessions.items()
            if sess['last_accessed'] < cutoff
        ]
        for sid in expired:
            self.delete_session(sid)
```

#### Step 1.2: Frontend - Extract Shared Components

**File:** `frontend/src/shared/components/Card.js`

```javascript
/**
 * Card component - used by both bidding and play modules
 */

import React from 'react';
import './Card.css';

export function Card({ rank, suit, onClick, disabled = false, className = '' }) {
  const suitColor = suit === '♥' || suit === '♦' ? 'suit-red' : 'suit-black';
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[rank] || rank;

  const handleClick = () => {
    if (!disabled && onClick) {
      onClick({ rank, suit });
    }
  };

  return (
    <div
      className={`card ${className} ${disabled ? 'disabled' : ''}`}
      onClick={handleClick}
      style={{ cursor: onClick && !disabled ? 'pointer' : 'default' }}
    >
      <div className={`card-corner top-left ${suitColor}`}>
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol-small">{suit}</span>
      </div>
      <div className={`card-center ${suitColor}`}>
        <span className="suit-symbol-large">{suit}</span>
      </div>
      <div className={`card-corner bottom-right ${suitColor}`}>
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol-small">{suit}</span>
      </div>
    </div>
  );
}
```

**File:** `frontend/src/shared/components/HandDisplay.js`

```javascript
/**
 * HandDisplay - shows 13 cards organized by suit
 * Used by both bidding and play modules
 */

import React from 'react';
import { Card } from './Card';
import { getSuitOrder } from '../utils/suitOrder';
import './HandDisplay.css';

export function HandDisplay({
  hand,
  trump = null,
  onCardClick = null,
  disabledCards = [],
  showAnalysis = false,
  analysis = null
}) {
  if (!hand || hand.length === 0) {
    return <div className="hand-display empty">No cards</div>;
  }

  const suitOrder = getSuitOrder(trump);

  const isCardDisabled = (card) => {
    return disabledCards.some(dc => dc.rank === card.rank && dc.suit === card.suit);
  };

  return (
    <div className="hand-display">
      {suitOrder.map(suit => {
        const cardsInSuit = hand.filter(card => card.suit === suit);
        return (
          <div key={suit} className="suit-group">
            <span className="suit-label">{suit}</span>
            <div className="suit-cards">
              {cardsInSuit.map((card, index) => (
                <Card
                  key={`${suit}-${index}`}
                  rank={card.rank}
                  suit={card.suit}
                  onClick={onCardClick}
                  disabled={isCardDisabled(card)}
                />
              ))}
            </div>
          </div>
        );
      })}

      {showAnalysis && analysis && (
        <HandAnalysis analysis={analysis} />
      )}
    </div>
  );
}

function HandAnalysis({ analysis }) {
  return (
    <div className="hand-analysis">
      <p>
        <strong>HCP:</strong> {analysis.hcp} +
        <strong> Dist:</strong> {analysis.dist_points} =
        <strong> Total:</strong> {analysis.total_points}
      </p>
      <div className="suit-breakdown">
        {Object.entries(analysis.suit_hcp).map(([suit, hcp]) => (
          <div key={suit}>
            {suit} {hcp} pts ({analysis.suit_lengths[suit]})
          </div>
        ))}
      </div>
    </div>
  );
}
```

**File:** `frontend/src/shared/utils/suitOrder.js`

```javascript
/**
 * Suit ordering utilities
 * Used by both bidding and play to organize hands
 */

export function getSuitOrder(trump = null) {
  // Default order: Spades, Hearts, Diamonds, Clubs (high to low)
  const defaultOrder = ['♠', '♥', '♦', '♣'];

  if (!trump || trump === 'NT') {
    return defaultOrder;
  }

  // If there's a trump suit, show it first
  return [trump, ...defaultOrder.filter(s => s !== trump)];
}

export function sortCardsBySuit(cards, trump = null) {
  const suitOrder = getSuitOrder(trump);
  const rankOrder = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];

  return cards.sort((a, b) => {
    const suitCompare = suitOrder.indexOf(a.suit) - suitOrder.indexOf(b.suit);
    if (suitCompare !== 0) return suitCompare;

    return rankOrder.indexOf(a.rank) - rankOrder.indexOf(b.rank);
  });
}
```

---

### Phase 2: Create Play Module (3-4 days)

Now that shared components exist, create play module that **uses** them:

**File:** `backend/modules/play/play_service.py`

```python
"""
Play Service - Independent play session management
Uses shared components but manages play-specific logic
"""

from engine.play_engine import PlayEngine, PlayState, Contract
from engine.hand import Hand, Card
from core.deal_generator import DealGenerator
from core.scenario_loader import ScenarioLoader
from typing import Dict, Optional

class PlayService:
    """Manage play sessions independently"""

    def __init__(self, session_manager):
        self.play_engine = PlayEngine()
        self.session_manager = session_manager
        self.scenario_loader = ScenarioLoader()
        self.deal_generator = DealGenerator()

    def create_from_scenario(self, session_id: str, scenario_id: str) -> PlayState:
        """
        Load a play scenario
        Uses: ScenarioLoader (shared), DealGenerator (shared)
        """
        scenario = self.scenario_loader.get_scenario_by_id('play', scenario_id)

        # Parse hands (could also use DealGenerator if needed)
        hands = self._parse_scenario_hands(scenario['hands'])
        contract = Contract(**scenario['contract'])

        opening_leader = self._get_opening_leader(contract.declarer)
        play_state = self.play_engine.create_play_session(
            contract, hands, opening_leader
        )

        # Store in session manager
        self.session_manager.update_session(session_id, play_state)

        return play_state

    def create_random(self, session_id: str, contract: Contract) -> PlayState:
        """
        Create random play session with given contract
        Uses: DealGenerator (shared)
        """
        hands = self.deal_generator.generate_for_contract(
            str(contract), contract.declarer
        )

        opening_leader = self._get_opening_leader(contract.declarer)
        play_state = self.play_engine.create_play_session(
            contract, hands, opening_leader
        )

        self.session_manager.update_session(session_id, play_state)
        return play_state

    def get_state(self, session_id: str) -> Optional[PlayState]:
        """Get play state from session"""
        session = self.session_manager.get_session(session_id)
        return session['data'] if session else None

    def play_card(self, session_id: str, position: str, card: Card) -> PlayState:
        """Play a card - updates session state"""
        play_state = self.get_state(session_id)
        play_state = self.play_engine.play_card(play_state, position, card)
        self.session_manager.update_session(session_id, play_state)
        return play_state

    def _get_opening_leader(self, declarer: str) -> str:
        order = ['N', 'E', 'S', 'W']
        idx = order.index(declarer)
        return order[(idx + 1) % 4]

    def _parse_scenario_hands(self, hands_dict: dict) -> Dict[str, Hand]:
        # Implementation
        pass
```

**File:** `frontend/src/modules/play/PlayApp.js`

```javascript
/**
 * Play-Only Application
 * Uses shared components: Card, HandDisplay, getSuitOrder
 */

import React, { useState, useEffect } from 'react';
import { HandDisplay } from '../../shared/components/HandDisplay';
import { ScenarioSelector } from './components/ScenarioSelector';
import { PlayTable } from './components/PlayTable';
import { playService } from './services/playService';

function PlayApp() {
  const [phase, setPhase] = useState('select'); // 'select', 'playing', 'complete'
  const [sessionId, setSessionId] = useState(null);
  const [playState, setPlayState] = useState(null);
  const [scenarios, setScenarios] = useState([]);

  useEffect(() => {
    playService.getScenarios().then(setScenarios);
  }, []);

  const handleScenarioSelect = async (scenarioId) => {
    const response = await playService.loadScenario(scenarioId);
    setSessionId(response.session_id);

    const state = await playService.getState(response.session_id);
    setPlayState(state);
    setPhase('playing');
  };

  if (phase === 'select') {
    return (
      <div className="play-app">
        <h1>Card Play Practice</h1>
        <ScenarioSelector
          scenarios={scenarios}
          onSelect={handleScenarioSelect}
        />
      </div>
    );
  }

  if (phase === 'playing') {
    return (
      <div className="play-app">
        <PlayTable
          playState={playState}
          sessionId={sessionId}
          onComplete={() => setPhase('complete')}
        />
      </div>
    );
  }

  // Complete phase...
}

export default PlayApp;
```

---

### Phase 3: Keep Bidding Module (Minimal Changes) (1-2 days)

The existing bidding system continues to work, just needs to:
1. Use shared `HandDisplay` component instead of inline version
2. Use shared `Card` component
3. Register routes under `/api/bidding/*` namespace

**Changes to existing code:**

```javascript
// OLD: App.js has inline Card component
function Card({ rank, suit }) { ... }

// NEW: Import from shared
import { Card } from './shared/components/Card';
import { HandDisplay } from './shared/components/HandDisplay';
```

**Minimal refactoring needed** - bidding module already works!

---

## Benefits of Shared Infrastructure Approach

### Development Efficiency
✅ **No duplication** - Hand generation, display written once
✅ **Consistent UX** - Cards look the same in bidding and play
✅ **Easier maintenance** - Fix a bug once, affects both modules
✅ **Faster feature addition** - New display features benefit both

### Testing Benefits
✅ **Test shared components once** - Both modules inherit quality
✅ **Independent module testing** - Test bidding without play, vice versa
✅ **Shared test utilities** - Generate test hands consistently

### Future Extensibility
✅ **User management layer** - Add once, both modules use it
✅ **Progress tracking** - Track bidding and play progress separately
✅ **Analytics** - Unified analytics across both modules
✅ **Multiplayer** - Shared session infrastructure enables multiplayer

---

## Migration Strategy

### Week 1: Extract Shared (Backend)
- [x] Create `core/` directory
- [ ] Move hand generation to `core/deal_generator.py`
- [ ] Create `core/scenario_loader.py`
- [ ] Create `core/session_manager.py`
- [ ] Test shared components

### Week 2: Extract Shared (Frontend)
- [ ] Create `shared/` directory
- [ ] Move `Card` component to `shared/components/`
- [ ] Create `HandDisplay` component in `shared/components/`
- [ ] Move `getSuitOrder` to `shared/utils/`
- [ ] Update existing App.js to use shared components

### Week 3: Create Play Module
- [ ] Create `modules/play/` directory (backend)
- [ ] Implement `play_service.py` using shared components
- [ ] Implement `play_routes.py`
- [ ] Create play scenarios JSON
- [ ] Test play API independently

### Week 4: Create Play UI
- [ ] Create `modules/play/` directory (frontend)
- [ ] Implement `PlayApp.js` using shared components
- [ ] Create play-specific components (PlayTable, etc.)
- [ ] Test play-only mode end-to-end

### Week 5: Integration & Polish
- [ ] Create mode selector in App.js
- [ ] Test all three modes
- [ ] Update documentation
- [ ] Performance optimization

---

## Comparison: Original vs Shared Infrastructure

### Original Plan (MODULAR_ARCHITECTURE_PLAN.md)
```
❌ Separate HandDisplay for bidding and play
❌ Duplicate Card components
❌ Separate hand generation logic
❌ More code to maintain
```

### Revised Plan (This Document)
```
✅ Single HandDisplay used by both
✅ Single Card component
✅ Shared hand generation (DealGenerator)
✅ Less code, more maintainable
✅ Consistent user experience
✅ Future-proof for user management
```

---

## File Structure Comparison

**Before (Current):**
```
backend/server.py (everything mixed together)
frontend/src/App.js (bidding + play mixed)
```

**After (Shared Infrastructure):**
```
backend/
├── core/ (SHARED)
│   ├── deal_generator.py
│   ├── scenario_loader.py
│   └── session_manager.py
├── engine/ (SHARED)
│   ├── hand.py
│   ├── hand_constructor.py
│   └── scoring.py
├── modules/
│   ├── bidding/ (uses shared)
│   └── play/ (uses shared)

frontend/src/
├── shared/ (SHARED)
│   ├── components/
│   └── utils/
├── modules/
│   ├── bidding/ (uses shared)
│   └── play/ (uses shared)
```

---

## Next Steps

1. **Review this revised architecture** - Does it address the shared infrastructure requirement?

2. **Decide on migration approach:**
   - Quick: Extract shared components + create play module (2 weeks)
   - Full: Complete modular architecture (3 weeks)

3. **Start with Phase 1:** Extract shared components
   - This provides immediate value
   - Low risk (doesn't break existing code)
   - Foundation for everything else

4. **Questions to resolve:**
   - Should user management be added now or later?
   - How to handle session persistence (in-memory vs database)?
   - Should we support saving/loading hands?

---

**Summary:** This architecture maintains your working bidding system, extracts truly shared components (hand generation, display, etc.), and creates an independent play module that **reuses** rather than duplicates infrastructure.

**Key Principle:** Share the foundation, separate the operations.
