# Interface Design Best Practices - Implementation Plan

## Executive Summary

Based on competitive analysis of BBO, Funbridge, SharkBridge, and Jack, this document outlines a phased implementation plan to transform the gameplay interface from a basic card display into an effective teaching tool for bridge learners.

**Date:** 2025-10-12
**Current Status:** Gameplay UI is functional but lacks educational features
**Target Users:** Bridge learners (beginner to intermediate)

---

## Current State Analysis

### What Works Well
- ✅ Basic card play functionality implemented
- ✅ Bidding summary display
- ✅ Contract display with declarer information
- ✅ Tricks won counter (NS/EW)
- ✅ Current trick visualization with winner highlighting
- ✅ Playable cards with hover effects
- ✅ Responsive design for mobile
- ✅ Score modal after hand completion
- ✅ Dummy hand display (after fixes in PLAY_STATE_ARCHITECTURE.md)

### Critical Gaps for Learners
- ❌ No "whose turn" visual indicator beyond small emoji
- ❌ No guidance on legal plays or why plays are illegal
- ❌ No hint system for suggesting good plays
- ❌ No explanation of AI decisions
- ❌ No contract goal tracking (e.g., "Need 8 tricks")
- ❌ No trick history or replay
- ❌ No post-hand analysis or learning feedback
- ❌ Limited bidding history visibility
- ❌ No vulnerability or opening lead display
- ❌ No trick count progress indicator

---

## Competitive Feature Analysis

### Feature Comparison Matrix

| Feature | BBO | Funbridge | SharkBridge | Jack | **Current** | **Priority** |
|---------|-----|-----------|-------------|------|-------------|--------------|
| Post-hand analysis | ✓ | ✓✓✓ | ✓✓ | ✓✓ | ❌ | HIGH |
| Hint system | ✓ | ✓✓ | ✓ | ✓ | ❌ | HIGH |
| Replay hands | ✓✓ | ✓✓✓ | ✓✓ | ✓✓ | ❌ | HIGH |
| Legal play indicators | ✓ | ✓ | ✓✓ | ✓ | ❌ | HIGH |
| AI explanation | ❌ | ✓✓✓ | ✓ | ✓ | ❌ | MEDIUM |
| Progressive learning | ✓ | ✓✓✓ | ✓✓ | ❌ | ❌ | MEDIUM |
| Multiple practice modes | ✓✓✓ | ✓✓ | ✓✓ | ✓ | ❌ | MEDIUM |
| Trick history | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ❌ | MEDIUM |
| Contract goal tracking | ✓ | ✓✓ | ✓ | ✓ | ❌ | HIGH |
| Teaching tools | ✓✓ | ✓ | ✓✓✓ | ✓ | ❌ | LOW |

**Legend:** ✓ = Basic, ✓✓ = Good, ✓✓✓ = Excellent, ❌ = Missing

---

## Implementation Plan: 4 Phases

## Phase 1: Core Educational Features (2-3 weeks)
**Goal:** Make the interface learner-friendly with immediate feedback

### 1.1 Enhanced Turn Indicators & Legal Plays
**Priority:** CRITICAL
**Files:** `PlayComponents.js`, `PlayComponents.css`, `App.js`

#### Features:
- **Large "Your Turn" banner** when it's user's turn
  - Position: Above user's hand
  - Style: Animated, high visibility (pulsing border)

- **Legal play highlighting**
  - Highlight playable cards with green glow
  - Dim illegal cards with red tint + "Cannot play" tooltip

- **Active player indicator**
  - Large, animated arrow pointing to current player
  - Color-coded by partnership (NS = green, EW = orange)

#### Technical Implementation:
```javascript
// New component: TurnIndicator
<TurnIndicator
  currentPlayer={playState.next_to_play}
  isUserTurn={playState.next_to_play === 'S'}
  message={getTurnMessage(playState)}
/>

// Enhanced PlayableCard with legal play detection
<PlayableCard
  card={card}
  onClick={onCardPlay}
  disabled={!isUserTurn}
  isLegal={isCardLegal(card, userHand, currentTrick, trumpSuit)}
  legalityReason={getIllegalReason(card)}
/>
```

#### Backend Support Needed:
- New endpoint: `POST /api/check-legal-play`
  - Input: `{ position, card, current_trick }`
  - Output: `{ legal: bool, reason: string }`

---

### 1.2 Contract Goal Tracker
**Priority:** CRITICAL
**Files:** `PlayComponents.js`, `PlayComponents.css`

#### Features:
- **Contract goal display** with progress bar
  - "Declarer needs 8 tricks to make 2♠"
  - Visual progress: 3/8 tricks (color-coded: green = on track, red = danger)

- **Overtrick/undertrick potential**
  - "Currently making with 1 overtrick"
  - "Down 1 - need to win all remaining tricks"

- **Tricks remaining counter**
  - "9 tricks remaining"

#### UI Mockup:
```
┌─────────────────────────────────────────┐
│ Contract Goal: 8 Tricks                 │
│ ████████░░░░░░░░ 3/8 ✓ On Track        │
│ Tricks Remaining: 10                    │
└─────────────────────────────────────────┘
```

#### Technical Implementation:
```javascript
// New component: ContractGoalTracker
<ContractGoalTracker
  contract={playState.contract}
  tricksWon={calculateDeclarerTricks(playState)}
  tricksNeeded={playState.contract.level + 6}
  tricksRemaining={13 - totalTricksPlayed}
/>
```

---

### 1.3 Hint System (Basic)
**Priority:** HIGH
**Files:** `PlayComponents.js`, `App.js`, backend `server.py`

#### Features:
- **"Show Hint" button** (bottom right)
  - Shows suggested card with brief reasoning
  - Example: "Play Q♠ - Finesse opportunity"
  - Limited to 3 hints per hand for learning

- **Hint reasoning levels:**
  - **Basic:** "Play a trump to draw opponent's trumps"
  - **Intermediate:** "Play Q♠ for finesse through East's likely K♠"
  - **Advanced:** "Cash ♥A first to avoid blocked suit"

#### UI Mockup:
```
┌──────────────────────────────────────┐
│ 💡 Hint (2 remaining)                │
│                                       │
│ Suggested Play: Q♠                   │
│ Reason: Finesse through East who     │
│ likely holds K♠ based on bidding     │
│                                       │
│ [Use This Hint] [Dismiss]            │
└──────────────────────────────────────┘
```

#### Technical Implementation:
```javascript
// Frontend
const [hintsRemaining, setHintsRemaining] = useState(3);
const [currentHint, setCurrentHint] = useState(null);

const requestHint = async () => {
  const response = await fetch(`${API_URL}/api/get-hint`, {
    method: 'POST',
    body: JSON.stringify({
      position: 'S',
      skill_level: 'intermediate'
    })
  });
  const hint = await response.json();
  setCurrentHint(hint);
  setHintsRemaining(hintsRemaining - 1);
};

// Backend endpoint needed:
// POST /api/get-hint
// Returns: { suggested_card: {rank, suit}, reasoning: string, confidence: float }
```

---

### 1.4 Enhanced Bidding Display
**Priority:** MEDIUM
**Files:** `PlayComponents.js`, `PlayComponents.css`

#### Features:
- **Expandable bidding history**
  - Collapsed: Shows only final contract
  - Expanded: Full auction table with alerts

- **Bid explanations on hover**
  - Tooltip: "2♣ = Stayman, asking for 4-card major"

- **Vulnerability display**
  - "Both Vulnerable" or "N/S Vulnerable" badge

- **Opening lead indicator**
  - "Opening Lead: 7♠ by West"

#### UI Mockup:
```
┌────────────────────────────────────────┐
│ Bidding [▼ Show Full Auction]          │
│ Contract: 2♠ by South                  │
│ Vulnerability: Both Vul                │
│ Opening Lead: 7♠ by West               │
└────────────────────────────────────────┘

[When expanded:]
┌────────────────────────────────────────┐
│ Bidding [▲ Hide Auction]               │
│ ┌─────┬──────┬──────┬──────┐          │
│ │  N  │  E   │  S   │  W   │          │
│ ├─────┼──────┼──────┼──────┤          │
│ │ 1NT │ Pass │ 2♣*  │ Pass │          │
│ │ 2♦  │ Pass │ 2♠   │ Pass │          │
│ │ Pass│ Pass │      │      │          │
│ └─────┴──────┴──────┴──────┘          │
│ * = Alert: 2♣ = Stayman               │
└────────────────────────────────────────┘
```

---

### 1.5 Improved Error Messages
**Priority:** MEDIUM
**Files:** `PlayComponents.js`, `App.js`

#### Features:
- **Clear illegal play messages**
  - ❌ "Cannot play 5♣ - must follow suit (♠)"
  - ❌ "Cannot play trump - must follow suit first"

- **Educational error modal**
  - Shows rule being violated
  - Link to rule explanation
  - Suggests legal alternatives

#### UI Mockup:
```
┌───────────────────────────────────────┐
│ ⚠️  Illegal Play                      │
│                                       │
│ You cannot play 5♣                    │
│                                       │
│ Reason: You must follow suit (♠)     │
│         since ♠ was led               │
│                                       │
│ Legal plays: A♠, K♠, Q♠, 7♠          │
│                                       │
│ [Learn More] [OK]                     │
└───────────────────────────────────────┘
```

---

## Phase 2: Post-Hand Analysis (2-3 weeks)
**Goal:** Provide learning feedback after each hand

### 2.1 Mistake Identification (Funbridge-style)
**Priority:** HIGH
**Files:** New `AnalysisComponents.js`, backend `analysis_engine.py`

#### Features:
- **Automatic mistake detection**
  - Compare user plays to double-dummy optimal
  - Flag suboptimal plays (cost 1+ tricks)

- **Mistake categories:**
  - Critical (cost 2+ tricks)
  - Suboptimal (cost 1 trick)
  - Acceptable alternative

- **Explanation for each mistake**
  - "Trick 3: Playing Q♠ was suboptimal"
  - "Better: Play low ♠ to preserve entry to dummy"
  - "Result: Lost 1 extra trick"

#### UI Mockup:
```
┌──────────────────────────────────────────┐
│ Hand Analysis                            │
│                                          │
│ Result: 2♠ Made exactly (8 tricks)       │
│ Your Performance: Fair (2 mistakes)      │
│                                          │
│ ❌ Trick 3 - Critical Mistake            │
│    You played: Q♠                        │
│    Better play: 7♠                       │
│    Impact: Cost 1 trick                  │
│    Reason: Blocked your spade suit       │
│    [Replay This Trick]                   │
│                                          │
│ ⚠️  Trick 7 - Suboptimal                 │
│    You played: K♥                        │
│    Better play: A♥                       │
│    Impact: Minor timing issue            │
│    [Replay This Trick]                   │
│                                          │
│ [Replay Entire Hand] [Share Results]     │
└──────────────────────────────────────────┘
```

#### Technical Implementation:
```javascript
// Frontend: Show analysis after hand completes
const [analysisData, setAnalysisData] = useState(null);

useEffect(() => {
  if (scoreData) {
    fetchAnalysis();
  }
}, [scoreData]);

const fetchAnalysis = async () => {
  const response = await fetch(`${API_URL}/api/analyze-hand`, {
    method: 'POST'
  });
  const analysis = await response.json();
  setAnalysisData(analysis);
};

// Backend endpoint needed:
// POST /api/analyze-hand
// Uses double-dummy solver to compare plays
// Returns: {
//   mistakes: [{ trick_number, your_play, optimal_play, cost, reason }],
//   performance_grade: "excellent|good|fair|poor",
//   optimal_tricks: 9,
//   actual_tricks: 8
// }
```

---

### 2.2 Replay Functionality
**Priority:** HIGH
**Files:** New `ReplayComponents.js`, `App.js`

#### Features:
- **Full hand replay** with controls
  - Play forward/backward through tricks
  - Jump to specific trick
  - Pause at key moments

- **"What if?" alternate plays**
  - Go back to Trick 3, try different card
  - See different outcome

- **Replay with annotations**
  - Show AI reasoning for each play
  - Highlight best plays in green, mistakes in red

#### UI Mockup:
```
┌─────────────────────────────────────────┐
│ Replay Hand                             │
│                                         │
│ [◀◀] [◀] [▶] [▶▶] [Jump to Trick ▼]   │
│                                         │
│ Trick 3 of 13                           │
│ ┌─────────────────────────────────┐    │
│ │  Current play: South played Q♠  │    │
│ │  ❌ Suboptimal - blocked suit   │    │
│ │                                 │    │
│ │  [Try Different Card]           │    │
│ └─────────────────────────────────┘    │
│                                         │
│ [Show All 4 Hands] [Exit Replay]        │
└─────────────────────────────────────────┘
```

---

### 2.3 Trick History Panel
**Priority:** MEDIUM
**Files:** `PlayComponents.js`, `PlayComponents.css`

#### Features:
- **Scrollable trick history** (side panel or drawer)
  - Shows all completed tricks
  - Click to review a specific trick

- **Trick summary:**
  - Trick 1: W led 7♠, won by South with A♠
  - Trick 2: S led K♥, won by North with A♥

- **Visual trick cards**
  - Show all 4 cards from each trick
  - Highlight winner

#### UI Mockup:
```
┌─────────────────────────────┐
│ Trick History        [▼]    │
├─────────────────────────────┤
│ Trick 1: Won by South       │
│ W:7♠ N:3♠ E:2♠ S:A♠ ←      │
│                             │
│ Trick 2: Won by North       │
│ S:K♥ W:Q♥ N:A♥ ← E:5♥      │
│                             │
│ Trick 3: Current            │
│ N:4♠ E:9♠ S:Q♠ W:?         │
└─────────────────────────────┘
```

---

### 2.4 Comparative Results
**Priority:** MEDIUM
**Files:** Backend `database.py`, `AnalysisComponents.js`

#### Features:
- **Compare to other players**
  - "67% of players made this contract"
  - "Your result: +110 (Better than 42% of players)"

- **Show distribution of results**
  - Histogram: How many made 8, 9, 10, 11 tricks

- **Best result possible**
  - "Double-dummy: 10 tricks makeable"

#### UI Mockup:
```
┌──────────────────────────────────────┐
│ Your Result vs Others                │
│                                      │
│ Your Result: Made 2♠ (+110)          │
│ Average Result: Made 2♠ + 1 (+140)   │
│                                      │
│ Trick Distribution:                  │
│ 11 tricks: ███ 5%                   │
│ 10 tricks: ████████ 15%             │
│  9 tricks: ████████████████ 35%     │
│  8 tricks: ████████████ 25% ← You   │
│  7 tricks: ██████ 12%               │
│  6 tricks: ███ 8%                   │
│                                      │
│ Double-Dummy Optimal: 9 tricks       │
└──────────────────────────────────────┘
```

---

## Phase 3: Practice Modes (2-3 weeks)
**Goal:** Offer specialized learning experiences

### 3.1 "Just Declare" Mode
**Priority:** MEDIUM
**Files:** New `PracticeModes.js`, backend `practice_modes.py`

#### Features:
- **Practice declarer play only**
  - Skip bidding entirely
  - Pre-assigned contracts
  - Focus on trick-taking techniques

- **Themed challenges:**
  - "Finesse Practice" - 10 hands with finesse opportunities
  - "Trump Management" - Drawing trumps effectively
  - "Suit Establishment" - Setting up long suits

- **Difficulty levels:**
  - Beginner: Straightforward contracts
  - Intermediate: Requires planning
  - Advanced: Complex squeeze/endplay scenarios

---

### 3.2 Daily Challenges
**Priority:** LOW
**Files:** Backend `daily_challenges.py`, frontend `ChallengeComponents.js`

#### Features:
- **Daily pre-curated hand**
  - Same hand for all users (competitive)
  - Specific learning focus (e.g., "4-3 trump fits")

- **Leaderboard:**
  - Rank by tricks taken or time

- **"7 Tricks Challenge"** (BBO-style)
  - Goal: Take exactly 7 tricks
  - Simple, achievable daily practice

---

### 3.3 MiniBridge Mode
**Priority:** LOW
**Files:** New `MiniBridge.js`, backend updates

#### Features:
- **Simplified bidding for beginners**
  - Just declare hand values
  - Auto-contract selection

- **Focus on card play fundamentals**
  - Following suit
  - Trump usage
  - High card play

---

## Phase 4: Advanced Features (3-4 weeks)
**Goal:** Professional-grade teaching tools

### 4.1 AI Explanation System
**Priority:** MEDIUM
**Files:** Backend `ai_explainer.py`, frontend components

#### Features:
- **"Why did AI do that?" button**
  - After each AI play
  - Shows reasoning: "North played A♥ to win trick and gain lead for finesse"

- **Bidding explanations:**
  - Click any bid to see AI's reasoning
  - "North opened 1NT showing 15-17 HCP balanced"

---

### 4.2 Teaching Tables
**Priority:** LOW
**Files:** New teacher interface

#### Features:
- **Load prepared hands**
  - Import .PBN, .LIN files
  - Create custom hands

- **Pause and discuss**
  - Stop at any point
  - Annotate with drawings

- **Student progress tracking**

---

### 4.3 Voice Commands (Accessibility)
**Priority:** LOW
**Files:** Voice recognition integration

#### Features:
- **"Play ace of spades"**
- **"Show hints"**
- **"Explain last bid"**

---

## Technical Architecture Changes

### Frontend File Structure
```
frontend/src/
├── components/
│   ├── play/
│   │   ├── PlayComponents.js (existing - enhance)
│   │   ├── PlayComponents.css (existing - enhance)
│   │   ├── TurnIndicator.js (new)
│   │   ├── ContractGoalTracker.js (new)
│   │   ├── HintSystem.js (new)
│   │   ├── TrickHistory.js (new)
│   │   └── LegalPlayIndicator.js (new)
│   ├── analysis/
│   │   ├── AnalysisModal.js (new)
│   │   ├── MistakeCard.js (new)
│   │   ├── ComparativeResults.js (new)
│   │   └── AnalysisComponents.css (new)
│   ├── replay/
│   │   ├── ReplayControls.js (new)
│   │   ├── ReplayViewer.js (new)
│   │   └── AlternatePlayExplorer.js (new)
│   └── practice/
│       ├── JustDeclareMode.js (new)
│       ├── DailyChallenge.js (new)
│       └── MiniBridge.js (new)
```

### Backend File Structure
```
backend/
├── engine/
│   ├── analysis_engine.py (new)
│   ├── hint_system.py (new)
│   ├── double_dummy_solver.py (new)
│   └── ai_explainer.py (new)
├── practice_modes.py (new)
├── daily_challenges.py (new)
└── database.py (enhance for result storage)
```

---

## Backend API Endpoints Required

### Phase 1 Endpoints
```
POST /api/check-legal-play
  → { legal: bool, reason: string, legal_cards: [] }

POST /api/get-hint
  → { suggested_card, reasoning, confidence }

GET /api/get-contract-goal
  → { tricks_needed, tricks_won, status: "on_track|danger" }
```

### Phase 2 Endpoints
```
POST /api/analyze-hand
  → { mistakes: [], performance_grade, optimal_line }

POST /api/replay-trick
  → { trick_data, annotations }

POST /api/save-result
  → Store for comparative analysis

GET /api/get-comparative-results?hand_id=X
  → { distribution, percentile, average }
```

### Phase 3 Endpoints
```
POST /api/start-just-declare
  → { hand, contract, difficulty }

GET /api/get-daily-challenge
  → { hand, goal, leaderboard }

POST /api/submit-challenge-result
  → { rank, score }
```

---

## Performance Considerations

### Double-Dummy Solving
- **Library:** python-dds or Bridge Solver
- **When to calculate:**
  - Post-hand only (not during play)
  - Cache results per hand
  - Background processing

### State Management
- **Current issue:** Multiple sources of truth (see PLAY_STATE_ARCHITECTURE.md)
- **Solution:** Single playState source
  - Derive all data from playState
  - Use React useMemo for computed values

### API Call Optimization
- **Batch requests** where possible
- **Debounce** hint requests
- **Cache** bid explanations
- **WebSocket** for real-time updates (future)

---

## UI/UX Design Principles

### 1. Progressive Disclosure
- Don't overwhelm beginners with all features
- Start simple, reveal advanced features gradually
- Collapsible panels for optional information

### 2. Immediate Feedback
- Visual confirmation of every action
- Error messages that teach, not just scold
- Success animations for correct plays

### 3. Consistency
- Same color scheme throughout (green = good, red = bad, blue = info)
- Consistent card sizing and spacing
- Standard iconography

### 4. Accessibility
- High contrast mode
- Screen reader support
- Keyboard navigation
- Touch-friendly targets (44x44px minimum)

### 5. Mobile-First
- All features work on small screens
- Touch gestures intuitive
- Landscape/portrait optimization

---

## Testing Strategy

### Unit Tests (Jest + React Testing Library)
- Each new component has tests
- Legal play detection logic
- Hint system accuracy
- Analysis mistake detection

### Integration Tests
- Full hand play with hints
- Replay functionality end-to-end
- Practice mode transitions

### User Testing
- 5 beginners, 5 intermediate players
- Task: Play 3 hands with new interface
- Collect feedback on:
  - Clarity of hints
  - Usefulness of analysis
  - UI intuitiveness

---

## Success Metrics

### Quantitative
- **Hint usage:** % of users who use hints
- **Completion rate:** % of hands played to end
- **Return rate:** % of users who play 2+ sessions
- **Analysis engagement:** % who review post-hand analysis

### Qualitative
- **User feedback:** Surveys after each hand
- **Mistake reduction:** Do users improve over time?
- **Feature requests:** What do users ask for?

---

## Implementation Priority Summary

### Must Have (Phase 1) - 2-3 weeks
1. ✅ Turn indicators & legal play highlighting
2. ✅ Contract goal tracker with progress
3. ✅ Basic hint system
4. ✅ Enhanced bidding display
5. ✅ Better error messages

### Should Have (Phase 2) - 2-3 weeks
6. ✅ Post-hand mistake analysis
7. ✅ Replay functionality
8. ✅ Trick history panel
9. ✅ Comparative results

### Nice to Have (Phase 3) - 2-3 weeks
10. ✅ Just Declare mode
11. ✅ Daily challenges
12. ✅ MiniBridge mode

### Future (Phase 4) - 3-4 weeks
13. ✅ AI explanation system
14. ✅ Teaching tables
15. ✅ Voice commands

---

## Risk Assessment

### Technical Risks
- **Double-dummy solver performance:** May be slow for complex hands
  - *Mitigation:* Background processing, caching

- **State management complexity:** Adding features increases state
  - *Mitigation:* Refactor to single source of truth first

### UX Risks
- **Feature overload:** Too many buttons/panels
  - *Mitigation:* Progressive disclosure, user settings

- **Mobile performance:** Heavy features on small screens
  - *Mitigation:* Simplified mobile view, lazy loading

### Business Risks
- **Scope creep:** 4 phases could expand
  - *Mitigation:* Strict MVP for each phase, defer nice-to-haves

---

## Dependencies

### Python Libraries
- `python-dds` or `libdds` - Double-dummy solver
- `flask-caching` - Result caching
- `sqlalchemy` - Database for results storage

### JavaScript Libraries
- `react-spring` - Smooth animations
- `react-tooltip` - Hover explanations
- `recharts` - Comparative results charts

### External Services (Optional)
- **Bridge Base Online API:** Import hands
- **Anthropic Claude API:** AI explanations (already using for review)

---

## Next Steps

1. **Review and approve this plan** with stakeholders
2. **Set up project tracking** (GitHub issues for each feature)
3. **Start Phase 1, Task 1.1:** Turn indicators & legal plays
4. **Create design mockups** for key components (Figma or wireframes)
5. **Backend prep:** Research double-dummy solver libraries

---

## Appendix A: Competitor Feature Deep Dive

### Funbridge's "Argine" AI Analysis
- Identifies bidding inconsistencies
- Compares play to conventions chosen
- Provides personalized statistics
- **Lesson:** Make feedback specific to user's skill level

### BBO's Teaching Tables
- Support 1-500 students simultaneously
- Video/voice integration
- Prepared hand libraries
- **Lesson:** Build for scale from the start

### SharkBridge's Teacher Console
- Generate hands with specific criteria
- Export/import multiple formats
- Student progress dashboard
- **Lesson:** Teachers are power users, give them tools

### Jack's Bidding Strength
- Multiple convention systems built-in
- Explains AI bidding in real-time
- **Lesson:** Transparency in AI decisions builds trust

---

## Appendix B: Color Scheme

### Palette
- **Success/Legal:** #4caf50 (green)
- **Warning/Danger:** #f44336 (red)
- **Info/Highlight:** #61dafb (cyan)
- **Neutral/Disabled:** #aaa (gray)
- **Background Dark:** #1a1a1a
- **Background Mid:** #2a2a2a
- **Text Primary:** #ffffff
- **Text Secondary:** #aaa

### Suit Colors (Standard)
- **Spades/Clubs:** #000000 (black)
- **Hearts/Diamonds:** #d32f2f (red)

---

## Appendix C: Mobile Breakpoints

```css
/* Large Desktop: > 1200px - Full features */
/* Desktop: 900px - 1200px - Standard layout */

@media (max-width: 900px) {
  /* Tablet: Smaller grids, vertical panels */
}

@media (max-width: 768px) {
  /* Mobile: Stacked layout, simplified UI */
}

@media (max-width: 480px) {
  /* Small Mobile: Minimal UI, essential only */
}
```

---

**Document Status:** ✅ READY FOR REVIEW
**Next Review Date:** After Phase 1 completion
**Owner:** Development Team
**Stakeholders:** Product, Design, Engineering
