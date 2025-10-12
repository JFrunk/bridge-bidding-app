# UI/UX Design Standards for Bridge Bidding App

**Purpose:** This document serves as the definitive reference for all UI/UX decisions in the Bridge Bidding App. All future development must adhere to these standards to ensure consistency and learner-focused design.

**Last Updated:** 2025-10-12
**Status:** 🔒 AUTHORITATIVE - Reference this document before making any UI/UX changes
**Location:** `.claude/UI_UX_DESIGN_STANDARDS.md` (Auto-loaded in Claude Code context)

---

## 🎯 Core Design Philosophy

### Primary User: Bridge Learners (Beginner to Intermediate)

Our application is designed for **people learning bridge**, not experts. Every design decision must answer: **"Does this help someone learn bridge better?"**

### Design Principles (In Priority Order)

1. **Teach, Don't Just Play**
   - Every interaction is a learning opportunity
   - Provide context, not just functionality
   - Explain "why" not just "what"

2. **Progressive Disclosure**
   - Start simple, reveal complexity gradually
   - Don't overwhelm beginners with advanced features
   - Use collapsible sections for optional information

3. **Immediate Feedback**
   - Confirm every user action visually
   - Error messages must educate, not frustrate
   - Show consequences of decisions in real-time

4. **Consistency Over Novelty**
   - Same patterns throughout the app
   - Predictable behavior builds confidence
   - Follow established bridge conventions (when they exist)

5. **Accessibility First**
   - Works for colorblind users
   - Screen reader compatible
   - Keyboard navigable
   - Touch-friendly (44x44px minimum targets)

6. **Mobile-First Responsive**
   - Majority of learners use phones/tablets
   - Design for smallest screen, enhance for larger
   - Landscape and portrait optimization

---

## 📚 Lessons from Competitive Analysis

### What We Learned from the Best Bridge Apps

#### From Funbridge (Rating: ⭐⭐⭐⭐⭐)
**Best Practice: "Argine" AI Post-Hand Analysis**

✅ **ALWAYS IMPLEMENT:**
- Identify mistakes immediately after hand completes
- Provide replay functionality with "what if?" scenarios
- Compare user's result to optimal (double-dummy)
- Explain mistakes in plain language, not technical jargon
- Show improvement over time (performance tracking)

❌ **AVOID:**
- Vague feedback like "You could have done better"
- Analysis without actionable advice
- Comparing only to other players (need optimal comparison too)

**Code Example:**
```javascript
// Good: Specific, actionable feedback
<MistakeCard
  trick={3}
  yourPlay="Q♠"
  betterPlay="7♠"
  impact="Cost 1 trick"
  reasoning="Playing Q♠ blocked your spade suit. Playing low preserves entries to dummy."
  replayUrl="/replay/hand123/trick3"
/>

// Bad: Generic, unhelpful
<div>You made a mistake on trick 3. Try again.</div>
```

---

#### From BBO - Bridge Base Online (Rating: ⭐⭐⭐⭐)
**Best Practice: Multiple Practice Modes**

✅ **ALWAYS IMPLEMENT:**
- Offer "Just Declare" mode (skip bidding, practice play)
- Provide "MiniBridge" for absolute beginners
- Create daily challenges (same hand for all users)
- Support teaching tables (prepared hands, pause/discuss)
- Allow undo/replay during practice

❌ **AVOID:**
- One-size-fits-all gameplay
- Forcing beginners through full auctions
- No way to practice specific skills in isolation

**Implementation Strategy:**
```javascript
// Game mode selection
const PRACTICE_MODES = {
  FULL_GAME: 'Complete bidding and play',
  JUST_DECLARE: 'Practice declarer play only',
  MINI_BRIDGE: 'Simplified for beginners',
  DAILY_CHALLENGE: 'Compete with others on same hand',
  TEACHING_TABLE: 'Custom hands with instructor mode'
};

// Allow mode switching
<ModeSelector
  currentMode={gameMode}
  onSelect={setGameMode}
  description={PRACTICE_MODES[gameMode]}
/>
```

---

#### From SharkBridge (Rating: ⭐⭐⭐⭐⭐ for Teaching)
**Best Practice: Teacher-Focused Tools**

✅ **ALWAYS IMPLEMENT:**
- Hand generation with specific criteria (e.g., "4-4 major fit, 25 HCP")
- Import/export hands (.PBN, .LIN formats)
- Pause at any point for discussion
- Save teaching notes on each hand
- Multi-table management (for group lessons)

❌ **AVOID:**
- Teacher having to manually create hands card-by-card
- No way to share hands with students
- Can't annotate or save lesson plans

---

#### From Jack Bridge (Rating: ⭐⭐⭐⭐ for Bidding)
**Best Practice: Transparent AI with Multiple Systems**

✅ **ALWAYS IMPLEMENT:**
- Support multiple bidding systems (SAYC, 2/1, Acol, etc.)
- Explain AI bids in real-time
- Show what bid means in different systems
- Convention card integration

❌ **AVOID:**
- Single rigid bidding system
- AI plays with no explanation
- Assuming user knows what bids mean

---

## 🎨 Visual Design Standards

### Color Palette

**Standard Colors (Must Use These Exactly):**

```css
/* Feedback Colors */
--color-success: #4caf50;        /* Legal plays, correct actions, making contract */
--color-danger: #f44336;         /* Illegal plays, errors, going down */
--color-warning: #ff9800;        /* Warnings, suboptimal plays */
--color-info: #61dafb;           /* Highlights, informational */

/* Backgrounds */
--bg-primary: #1a1a1a;           /* Main dark background */
--bg-secondary: #2a2a2a;         /* Card backgrounds, panels */
--bg-tertiary: #3a3a3a;          /* Hover states */

/* Text */
--text-primary: #ffffff;          /* Main text */
--text-secondary: #aaaaaa;        /* Secondary text, labels */
--text-disabled: #666666;         /* Disabled text */

/* Card Suits (Bridge Standard) */
--suit-red: #d32f2f;             /* Hearts & Diamonds */
--suit-black: #000000;            /* Spades & Clubs */

/* Partnerships (Consistent Throughout) */
--partnership-ns: #4caf50;        /* North-South = Green */
--partnership-ew: #ff9800;        /* East-West = Orange */

/* Special States */
--highlight-current-player: #61dafb; /* Whose turn indicator */
--highlight-winner: #ffd700;         /* Winning card/trick (gold) */
--highlight-vulnerable: #d32f2f;     /* Vulnerability indicator */
```

**Accessibility Requirement:**
- All color combinations must meet WCAG 2.1 AA standards (4.5:1 contrast ratio)
- Provide colorblind mode option (use patterns + colors)

---

### Typography

**Font Stack:**
```css
--font-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
--font-monospace: 'SF Mono', Monaco, 'Courier New', monospace; /* For card ranks */

/* Font Sizes (Mobile-First) */
--text-xs: 0.75rem;    /* 12px - Fine print */
--text-sm: 0.875rem;   /* 14px - Secondary text */
--text-base: 1rem;     /* 16px - Body text */
--text-lg: 1.125rem;   /* 18px - Subheadings */
--text-xl: 1.25rem;    /* 20px - Headings */
--text-2xl: 1.5rem;    /* 24px - Major headings */
--text-3xl: 2rem;      /* 32px - Hero text */

/* Card Suit Symbols */
--suit-symbol-small: 1rem;
--suit-symbol-medium: 1.5rem;
--suit-symbol-large: 2.5rem;
```

**Font Weight:**
- Normal text: 400
- Emphasis: 600
- Strong emphasis: 700

---

### Spacing System (8px Grid)

```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-5: 1.25rem;  /* 20px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-10: 2.5rem;  /* 40px */
--space-12: 3rem;    /* 48px */
--space-16: 4rem;    /* 64px */
```

**Usage:**
- Padding within components: `--space-4` (16px)
- Margin between components: `--space-6` (24px)
- Section spacing: `--space-8` (32px)
- Card spacing: `--space-2` to `--space-3` (8-12px)

---

### Border Radius

```css
--radius-sm: 4px;    /* Small elements (badges) */
--radius-md: 8px;    /* Buttons, cards */
--radius-lg: 12px;   /* Panels, modals */
--radius-xl: 16px;   /* Large containers */
--radius-full: 9999px; /* Circular (avatars, pills) */
```

---

### Shadows (Depth)

```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.1);
--shadow-md: 0 4px 6px rgba(0,0,0,0.2);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.3);
--shadow-xl: 0 20px 25px rgba(0,0,0,0.4);

/* Glows for emphasis */
--glow-success: 0 0 20px rgba(76, 175, 80, 0.5);
--glow-danger: 0 0 20px rgba(244, 67, 54, 0.5);
--glow-info: 0 0 20px rgba(97, 218, 251, 0.5);
```

---

## 🃏 Card Component Standards

### Card Dimensions

**Desktop (Base):**
```css
.playable-card {
  min-width: 70px;
  min-height: 100px;
  aspect-ratio: 0.7; /* Standard playing card ratio */
}
```

**Tablet (≤900px):**
```css
.playable-card {
  min-width: 50px;
  min-height: 80px;
}
```

**Mobile (≤768px):**
```css
.playable-card {
  min-width: 45px;
  min-height: 70px;
}

**Small Mobile (≤480px):**
```css
.playable-card {
  min-width: 38px;
  min-height: 60px;
}
```

### Card States (Required for ALL Card Components)

```css
/* Default State */
.playable-card {
  background: white;
  border: 2px solid #333;
  cursor: pointer;
  transition: all 0.2s ease;
}

/* Hover (Clickable Only) */
.playable-card.clickable:hover {
  transform: translateY(-10px); /* Lift effect */
  box-shadow: var(--shadow-lg);
  border-color: var(--color-info);
  z-index: 100; /* Above other cards */
}

/* Legal Play (User's Turn) */
.playable-card.legal {
  border-color: var(--color-success);
  box-shadow: var(--glow-success);
}

/* Illegal Play (Cannot Be Played) */
.playable-card.illegal {
  opacity: 0.5;
  filter: grayscale(50%);
  cursor: not-allowed;
}

/* Illegal Play Hover (Show Why) */
.playable-card.illegal:hover::after {
  content: attr(data-illegal-reason);
  position: absolute;
  bottom: -30px;
  background: var(--color-danger);
  color: white;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  white-space: nowrap;
}

/* Selected Card */
.playable-card.selected {
  border: 3px solid var(--color-info);
  transform: translateY(-5px);
}

/* Disabled (Not User's Turn) */
.playable-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Winner Highlight (After Trick) */
.playable-card.winner {
  border: 3px solid var(--highlight-winner);
  box-shadow: var(--shadow-xl), 0 0 20px rgba(255, 215, 0, 0.9);
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}
```

### Card Overlap for Hand Display

**Horizontal Overlap (Standard View):**
```css
.suit-group .playable-card {
  margin-left: -45px; /* Show ~25px of each card (desktop) */
}

.suit-group .playable-card:first-child {
  margin-left: 0; /* First card fully visible */
}

/* Tablet */
@media (max-width: 900px) {
  .suit-group .playable-card {
    margin-left: -33px;
  }
}

/* Mobile */
@media (max-width: 768px) {
  .suit-group .playable-card {
    margin-left: -28px;
  }
}

/* Small Mobile */
@media (max-width: 480px) {
  .suit-group .playable-card {
    margin-left: -22px;
  }
}
```

**Why These Values:**
- Maintain ~30-35% visibility of each card
- Enough to read rank and suit
- Conserve screen space
- Consistent ratio across breakpoints

---

## 🎮 Interaction Patterns

### Turn Indicators

**REQUIRED: Always show whose turn it is**

```javascript
// Large, unmistakable indicator
<TurnIndicator
  currentPlayer="N"
  isUserTurn={false}
  position="north"
/>

// Renders as:
┌────────────────────────────────┐
│   ⬇️ NORTH'S TURN ⬇️           │
│   (Waiting for North...)       │
└────────────────────────────────┘

// When it's user's turn:
┌────────────────────────────────┐
│   ⏰ YOUR TURN! ⏰              │
│   (Select a card to play)      │
└────────────────────────────────┘
```

**Visual Requirements:**
- Minimum 40px height
- Animated (pulsing border or breathing effect)
- High contrast color (--highlight-current-player)
- Position: Adjacent to active player's hand

---

### Button Hierarchy

**Primary Actions** (Main user goal):
```css
.button-primary {
  background: var(--color-info);
  color: var(--bg-primary);
  font-weight: 600;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  transition: all 0.2s ease;
}

.button-primary:hover {
  background: #4fa8c5;
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```

**Secondary Actions** (Alternative choices):
```css
.button-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 2px solid var(--text-secondary);
  padding: 10px 22px;
}

.button-secondary:hover {
  border-color: var(--color-info);
  color: var(--color-info);
}
```

**Destructive Actions** (Dangerous, irreversible):
```css
.button-destructive {
  background: var(--color-danger);
  color: white;
}

.button-destructive:hover {
  background: #d32f2f;
}
```

**Disabled State** (Cannot interact):
```css
.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--bg-tertiary);
  color: var(--text-disabled);
}
```

---

### Modal / Dialog Patterns

**Standard Modal Structure:**

```javascript
<Modal onClose={handleClose}>
  <ModalHeader>
    <h2>Modal Title</h2>
    <CloseButton onClick={handleClose} />
  </ModalHeader>

  <ModalBody>
    {/* Content */}
  </ModalBody>

  <ModalFooter>
    <ButtonSecondary onClick={handleClose}>Cancel</ButtonSecondary>
    <ButtonPrimary onClick={handleConfirm}>Confirm</ButtonPrimary>
  </ModalFooter>
</Modal>
```

**Modal Styling:**
```css
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  padding: var(--space-6);
  border-bottom: 1px solid var(--bg-tertiary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: var(--space-6);
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--bg-tertiary);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-4);
}
```

---

### Tooltips (Contextual Help)

**When to Use:**
- Explaining bidding conventions
- Card legality reasons
- Feature descriptions
- Terminology definitions

**Implementation:**
```javascript
<Tooltip content="2♣ = Stayman, asking for 4-card major">
  <BidButton bid="2♣" />
</Tooltip>

// Hover shows tooltip
```

**Styling:**
```css
.tooltip {
  position: absolute;
  background: var(--bg-primary);
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-info);
  max-width: 250px;
  z-index: 9999;
  pointer-events: none; /* Don't block clicks */
}

.tooltip-arrow {
  /* Triangle pointing to element */
  width: 0; height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 8px solid var(--bg-primary);
}
```

---

### Loading States

**NEVER show blank screens**. Always indicate activity.

```javascript
// Inline loading (within component)
<LoadingSpinner size="small" text="Loading hand..." />

// Full page loading
<LoadingScreen message="Starting new hand..." />

// Skeleton loading (preferred for better UX)
<CardSkeleton count={13} /> // Shows 13 card outlines while loading
```

**Styling:**
```css
.loading-spinner {
  border: 3px solid var(--bg-tertiary);
  border-top-color: var(--color-info);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.skeleton-card {
  background: linear-gradient(
    90deg,
    var(--bg-secondary) 25%,
    var(--bg-tertiary) 50%,
    var(--bg-secondary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  to { background-position: -200% 0; }
}
```

---

## 📱 Responsive Design Rules

### Breakpoints (Required)

```css
/* Mobile First Approach */

/* Extra Small Mobile: 0 - 480px */
/* Base styles apply here */

/* Mobile: 481px - 768px */
@media (min-width: 481px) {
  /* Slightly larger touch targets, more info visible */
}

/* Tablet: 769px - 900px */
@media (min-width: 769px) {
  /* Two-column layouts, side-by-side panels */
}

/* Desktop: 901px - 1200px */
@media (min-width: 901px) {
  /* Full feature set, multi-column */
}

/* Large Desktop: 1201px+ */
@media (min-width: 1201px) {
  /* Max content width, extra whitespace */
}
```

### Touch Targets (Mobile)

**Minimum Size: 44x44px** (Apple HIG / Material Design standard)

```css
/* All interactive elements on mobile */
@media (max-width: 768px) {
  button,
  .playable-card,
  .bid-button,
  .checkbox,
  .radio,
  a {
    min-width: 44px;
    min-height: 44px;
    /* Or padding that achieves this */
  }
}
```

### Layout Patterns

**Desktop Layout (Bidding Phase):**
```
┌─────────────────────────────────────────┐
│ Header: Game Info, Settings             │
├─────────────────────────────────────────┤
│ ┌─────────────┐  ┌──────────────────┐  │
│ │             │  │                  │  │
│ │  Bidding    │  │   Your Hand      │  │
│ │  Table      │  │                  │  │
│ │             │  │                  │  │
│ └─────────────┘  └──────────────────┘  │
│ ┌───────────────────────────────────┐  │
│ │      Bidding Box                  │  │
│ └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Mobile Layout (Bidding Phase):**
```
┌───────────────────┐
│ Header (compact)  │
├───────────────────┤
│                   │
│  Bidding Table    │
│   (scrollable)    │
│                   │
├───────────────────┤
│                   │
│   Your Hand       │
│  (horizontal      │
│   scroll)         │
│                   │
├───────────────────┤
│  Bidding Box      │
│  (grid/tabs)      │
└───────────────────┘
```

**Desktop Layout (Play Phase):**
```
┌─────────────────────────────────────────┐
│  Bidding │ Contract │ Tricks Won        │
├─────────────────────────────────────────┤
│              North (Dummy)              │
│         [Card] [Card] [Card]...         │
├──────┬──────────────────────────┬───────┤
│      │                          │       │
│ West │    Current Trick         │ East  │
│      │   (center green box)     │       │
│      │                          │       │
├──────┴──────────────────────────┴───────┤
│           South (You)                   │
│      [Card] [Card] [Card]...            │
├─────────────────────────────────────────┤
│ Controls: Hint | Undo | Review          │
└─────────────────────────────────────────┘
```

**Mobile Layout (Play Phase):**
```
┌─────────────────────┐
│ Contract | Tricks   │ (collapsed header)
├─────────────────────┤
│    North (Dummy)    │
│   [C][C][C][C]...   │ (smaller cards)
├─────────────────────┤
│  W │ Trick  │ E     │
│ [C]│ [Cards]│[C]    │
├─────────────────────┤
│   South (You)       │
│  [C][C][C][C]...    │ (horizontal scroll)
├─────────────────────┤
│ [Hint] [Undo]       │
└─────────────────────┘
```

---

## 🎓 Educational UI Patterns

### Hint System Design

**Visibility: Always Present, Never Intrusive**

```javascript
// Position: Bottom right corner (desktop), bottom bar (mobile)
<HintButton
  available={hintsRemaining > 0}
  count={hintsRemaining}
  onClick={showHint}
/>

// When clicked:
<HintPanel>
  <HintHeader>
    💡 Hint ({hintsRemaining} remaining)
  </HintHeader>
  <HintBody>
    <SuggestedCard card={{rank: 'Q', suit: '♠'}} />
    <HintReasoning>
      Play Q♠ to attempt a finesse through East, who likely
      holds K♠ based on the bidding.
    </HintReasoning>
  </HintBody>
  <HintActions>
    <Button onClick={useHint}>Use This Hint</Button>
    <Button secondary onClick={dismissHint}>Dismiss</Button>
  </HintActions>
</HintPanel>
```

**Hint Levels (Adapt to User Skill):**

```javascript
const HINT_LEVELS = {
  BEGINNER: {
    detail: 'high',
    examples: ['Play A♠ to win the trick', 'Follow suit with any ♥']
  },
  INTERMEDIATE: {
    detail: 'medium',
    examples: ['Play Q♠ for finesse', 'Cash ♥A before drawing trumps']
  },
  ADVANCED: {
    detail: 'low',
    examples: ['Finesse', 'Elimination play']
  }
};
```

---

### Error Messages (Teaching Opportunities)

**BAD (Don't Do This):**
```javascript
<ErrorMessage>Invalid bid</ErrorMessage>
<ErrorMessage>Cannot play that card</ErrorMessage>
<ErrorMessage>Error</ErrorMessage>
```

**GOOD (Do This):**
```javascript
<EducationalError>
  <ErrorIcon type="illegal_bid" />
  <ErrorTitle>Cannot Bid 3♣</ErrorTitle>
  <ErrorReason>
    Your previous pass means you cannot enter the auction again
    unless your partner bids.
  </ErrorReason>
  <ErrorRule>
    Rule: Once you pass, you cannot bid unless partner reopens.
  </ErrorRule>
  <ErrorActions>
    <LearnMoreButton href="/rules/passing" />
    <OkButton />
  </ErrorActions>
</EducationalError>
```

**Error Styling:**
```css
.educational-error {
  background: var(--bg-secondary);
  border-left: 4px solid var(--color-danger);
  padding: var(--space-6);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
}

.error-title {
  color: var(--color-danger);
  font-weight: 600;
  font-size: var(--text-lg);
  margin-bottom: var(--space-2);
}

.error-reason {
  color: var(--text-primary);
  margin-bottom: var(--space-4);
}

.error-rule {
  background: var(--bg-tertiary);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  font-style: italic;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}
```

---

### Progress Indicators (Contract Goals)

**Required: Always show progress toward goal**

```javascript
<ContractGoalTracker>
  <GoalStatement>
    Declarer needs 8 tricks to make 2♠
  </GoalStatement>
  <ProgressBar
    current={3}
    target={8}
    total={13}
    status="on_track" // or "danger" or "safe"
  />
  <ProgressDetails>
    <TricksWon>3 tricks won</TricksWon>
    <TricksRemaining>10 tricks remaining</TricksRemaining>
    <StatusMessage>On track to make contract</StatusMessage>
  </ProgressDetails>
</ContractGoalTracker>
```

**Visual Design:**
```css
.progress-bar-container {
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  height: 24px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-bar-fill.on-track {
  background: linear-gradient(90deg, var(--color-success), #66bb6a);
}

.progress-bar-fill.danger {
  background: linear-gradient(90deg, var(--color-danger), #ef5350);
}

.progress-bar-fill.safe {
  background: linear-gradient(90deg, var(--color-info), #4fc3f7);
}

.progress-bar-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: 600;
  font-size: var(--text-sm);
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
```

---

### Post-Hand Analysis UI

**Show Immediately After Hand (Don't Hide Behind Menu)**

```javascript
<PostHandAnalysis>
  <AnalysisHeader>
    <HandResult result="made" />
    <PerformanceGrade grade="good" /> {/* excellent | good | fair | poor */}
  </AnalysisHeader>

  <MistakesList>
    {mistakes.map(mistake => (
      <MistakeCard
        key={mistake.trick}
        severity={mistake.severity} // critical | suboptimal | minor
        trick={mistake.trick}
        yourPlay={mistake.your_play}
        optimalPlay={mistake.optimal_play}
        impact={mistake.impact}
        reasoning={mistake.reasoning}
        onReplay={() => replayTrick(mistake.trick)}
      />
    ))}
  </MistakesList>

  <ComparativeResults>
    <ResultDistribution data={comparativeData} />
    <YourPercentile percentile={67} />
  </ComparativeResults>

  <AnalysisActions>
    <ReplayButton onClick={replayHand}>Replay Entire Hand</ReplayButton>
    <ShareButton onClick={shareResults}>Share Results</ShareButton>
    <NewHandButton onClick={startNewHand}>Play Another Hand</NewHandButton>
  </AnalysisActions>
</PostHandAnalysis>
```

---

## ♿ Accessibility Requirements

### WCAG 2.1 AA Compliance (Minimum)

**Color Contrast:**
- Text on background: Minimum 4.5:1 ratio
- Large text (18pt+): Minimum 3:1 ratio
- Interactive elements: 3:1 ratio for boundaries

**Keyboard Navigation:**
```javascript
// All interactive elements must be keyboard accessible
<PlayableCard
  tabIndex={isUserTurn ? 0 : -1}
  onKeyPress={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleCardPlay(card);
    }
  }}
  aria-label={`${card.rank} of ${suitName(card.suit)}`}
  aria-disabled={!isLegal}
/>
```

**Screen Reader Support:**
```javascript
// Use semantic HTML and ARIA labels
<button
  onClick={handleBid}
  aria-label="Bid 1 No Trump, 15-17 high card points, balanced hand"
  aria-describedby="bid-1nt-explanation"
>
  1NT
</button>

<div id="bid-1nt-explanation" className="sr-only">
  1 No Trump shows 15 to 17 high card points with a balanced hand
</div>
```

**Focus Indicators:**
```css
/* NEVER remove focus outlines without replacement */
button:focus,
.playable-card:focus {
  outline: 3px solid var(--color-info);
  outline-offset: 2px;
}

/* Or custom focus style */
button:focus-visible {
  box-shadow: 0 0 0 3px var(--color-info);
}
```

### Colorblind Mode

**Provide pattern alternatives to color-only indicators:**

```css
/* In addition to color, use patterns/icons */
.legal-card {
  border-color: var(--color-success);
  background-image: url('/icons/checkmark-pattern.svg'); /* Pattern overlay */
}

.illegal-card {
  border-color: var(--color-danger);
  background-image: url('/icons/x-pattern.svg');
}

/* Suit symbols with pattern backgrounds (colorblind mode) */
body.colorblind-mode .suit-hearts,
body.colorblind-mode .suit-diamonds {
  /* Add diagonal lines to red suits */
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.1) 2px,
    rgba(0,0,0,0.1) 4px
  );
}
```

---

## 📊 Data Visualization Standards

### Charts (for Comparative Results)

**Use Recharts library with custom theme:**

```javascript
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

<ResponsiveContainer width="100%" height={300}>
  <BarChart data={trickDistribution}>
    <XAxis
      dataKey="tricks"
      stroke={CSS_VARS['--text-secondary']}
    />
    <YAxis
      stroke={CSS_VARS['--text-secondary']}
    />
    <Tooltip
      contentStyle={{
        background: CSS_VARS['--bg-secondary'],
        border: `1px solid ${CSS_VARS['--bg-tertiary']}`
      }}
    />
    <Bar
      dataKey="count"
      fill={CSS_VARS['--color-info']}
      activeBar={{ fill: CSS_VARS['--color-success'] }}
    />
  </BarChart>
</ResponsiveContainer>
```

### Tables (for Bidding History, Trick History)

```css
.data-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.data-table thead {
  background: var(--bg-tertiary);
  color: var(--color-info);
  font-weight: 600;
}

.data-table th,
.data-table td {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  border-bottom: 1px solid var(--bg-tertiary);
}

.data-table tbody tr:hover {
  background: rgba(97, 218, 251, 0.1);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}
```

---

## 🎬 Animation Standards

### When to Animate

✅ **DO animate:**
- Card plays (smooth transition from hand to trick)
- Turn indicators (pulsing/breathing)
- Trick winner reveal (highlight animation)
- Modal entrances/exits
- Loading states
- Success/error feedback

❌ **DON'T animate:**
- Text content changes
- Background colors
- Layout shifts (causes CLS - Cumulative Layout Shift)

### Animation Durations

```css
--duration-instant: 100ms;   /* Hover effects */
--duration-fast: 200ms;      /* Button clicks, small movements */
--duration-normal: 300ms;    /* Standard transitions */
--duration-slow: 500ms;      /* Modal entrances, card plays */
--duration-slower: 1000ms;   /* Winner reveals, celebrations */
```

### Easing Functions

```css
--ease-out: cubic-bezier(0.25, 0.46, 0.45, 0.94); /* Smooth deceleration */
--ease-in: cubic-bezier(0.55, 0.055, 0.675, 0.19); /* Smooth acceleration */
--ease-in-out: cubic-bezier(0.645, 0.045, 0.355, 1); /* Smooth both ends */
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55); /* Overshoot */
```

### Standard Animations

**Card Play Animation:**
```css
@keyframes card-play {
  from {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  to {
    transform: translateY(-100px) scale(0.8);
    opacity: 0.5;
  }
}

.card-playing {
  animation: card-play var(--duration-slow) var(--ease-in) forwards;
}
```

**Pulsing Turn Indicator:**
```css
@keyframes pulse-border {
  0%, 100% {
    border-color: var(--highlight-current-player);
    box-shadow: 0 0 0 0 rgba(97, 218, 251, 0.7);
  }
  50% {
    border-color: #4fa8c5;
    box-shadow: 0 0 0 10px rgba(97, 218, 251, 0);
  }
}

.your-turn {
  animation: pulse-border 2s ease-in-out infinite;
}
```

**Success Checkmark:**
```css
@keyframes checkmark {
  0% {
    stroke-dashoffset: 100;
  }
  100% {
    stroke-dashoffset: 0;
  }
}

.checkmark-icon path {
  stroke-dasharray: 100;
  animation: checkmark 0.5s ease-in-out forwards;
}
```

### Reduced Motion

**Respect user preferences:**
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 🔔 Notification Standards

### Notification Types

**Success (Contract Made, Good Play):**
```javascript
<Toast type="success" duration={3000}>
  ✓ Contract made! Well played!
</Toast>
```

**Error (Illegal Play, Failed Action):**
```javascript
<Toast type="error" duration={5000}>
  ✗ Cannot play that card - must follow suit
</Toast>
```

**Info (Turn Change, Hint):**
```javascript
<Toast type="info" duration={2000}>
  ℹ️ It's now North's turn
</Toast>
```

**Warning (Suboptimal Play):**
```javascript
<Toast type="warning" duration={4000}>
  ⚠️ That play may cost a trick
</Toast>
```

### Toast Positioning

```css
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.toast {
  min-width: 300px;
  max-width: 500px;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  animation: toast-enter 0.3s var(--ease-out);
}

@keyframes toast-enter {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast.success { background: var(--color-success); color: white; }
.toast.error { background: var(--color-danger); color: white; }
.toast.info { background: var(--color-info); color: var(--bg-primary); }
.toast.warning { background: var(--color-warning); color: var(--bg-primary); }
```

---

## 📝 Form Standards

### Input Fields

```css
.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--bg-secondary);
  border: 2px solid var(--bg-tertiary);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-base);
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-info);
  box-shadow: 0 0 0 3px rgba(97, 218, 251, 0.2);
}

.form-input::placeholder {
  color: var(--text-disabled);
}

.form-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--bg-primary);
}

.form-input.error {
  border-color: var(--color-danger);
}

.form-input.success {
  border-color: var(--color-success);
}
```

### Labels

```css
.form-label {
  display: block;
  margin-bottom: var(--space-2);
  color: var(--text-primary);
  font-weight: 600;
  font-size: var(--text-sm);
}

.form-label.required::after {
  content: " *";
  color: var(--color-danger);
}
```

### Helper Text

```css
.form-helper-text {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.form-helper-text.error {
  color: var(--color-danger);
}
```

---

## 🎯 Component Examples (Copy-Paste Ready)

### Turn Indicator Component

```javascript
// TurnIndicator.jsx
import React from 'react';
import './TurnIndicator.css';

export function TurnIndicator({ currentPlayer, isUserTurn, message }) {
  const playerNames = { N: 'North', E: 'East', S: 'South', W: 'West' };
  const displayMessage = message || (isUserTurn
    ? 'YOUR TURN!'
    : `${playerNames[currentPlayer]}'s Turn`);

  return (
    <div className={`turn-indicator ${isUserTurn ? 'user-turn' : ''}`}>
      <div className="turn-indicator-content">
        {isUserTurn && <span className="turn-icon">⏰</span>}
        <span className="turn-message">{displayMessage}</span>
        {isUserTurn && <span className="turn-icon">⏰</span>}
      </div>
    </div>
  );
}
```

```css
/* TurnIndicator.css */
.turn-indicator {
  background: var(--bg-secondary);
  border: 2px solid var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  text-align: center;
  margin: var(--space-4) 0;
  transition: all 0.3s ease;
}

.turn-indicator.user-turn {
  background: rgba(97, 218, 251, 0.1);
  border-color: var(--highlight-current-player);
  animation: pulse-border 2s ease-in-out infinite;
}

.turn-indicator-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
}

.turn-message {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

.turn-indicator.user-turn .turn-message {
  color: var(--highlight-current-player);
}

.turn-icon {
  font-size: var(--text-2xl);
}

@keyframes pulse-border {
  0%, 100% {
    border-color: var(--highlight-current-player);
    box-shadow: 0 0 0 0 rgba(97, 218, 251, 0.7);
  }
  50% {
    border-color: #4fa8c5;
    box-shadow: 0 0 0 10px rgba(97, 218, 251, 0);
  }
}
```

---

### Legal Play Indicator Component

```javascript
// LegalPlayIndicator.jsx
import React from 'react';
import { PlayableCard } from './PlayableCard';

export function LegalPlayIndicator({ card, onClick, isLegal, legalityReason, isUserTurn }) {
  return (
    <div className="legal-play-wrapper">
      <PlayableCard
        card={card}
        onClick={onClick}
        disabled={!isUserTurn || !isLegal}
        className={`
          ${isLegal ? 'legal-card' : 'illegal-card'}
          ${isUserTurn && isLegal ? 'clickable' : ''}
        `}
        data-illegal-reason={!isLegal ? legalityReason : ''}
      />
      {!isLegal && (
        <div className="illegality-tooltip">
          {legalityReason}
        </div>
      )}
    </div>
  );
}
```

```css
/* LegalPlayIndicator additions to PlayComponents.css */
.legal-card {
  border: 2px solid var(--color-success) !important;
  box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
}

.illegal-card {
  opacity: 0.4;
  filter: grayscale(70%);
  cursor: not-allowed;
  position: relative;
}

.illegal-card:hover .illegality-tooltip {
  display: block;
}

.illegality-tooltip {
  display: none;
  position: absolute;
  bottom: -35px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-danger);
  color: white;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  white-space: nowrap;
  z-index: 1000;
  box-shadow: var(--shadow-md);
}

.illegality-tooltip::before {
  content: '';
  position: absolute;
  top: -5px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-bottom: 5px solid var(--color-danger);
}
```

---

### Contract Goal Tracker Component

```javascript
// ContractGoalTracker.jsx
import React from 'react';
import './ContractGoalTracker.css';

export function ContractGoalTracker({ contract, tricksWon, tricksNeeded, tricksRemaining }) {
  const progress = (tricksWon / tricksNeeded) * 100;
  const tricksShort = tricksNeeded - tricksWon;

  let status = 'on-track';
  let statusMessage = 'On track to make contract';

  if (tricksShort > tricksRemaining) {
    status = 'danger';
    statusMessage = `Down ${tricksShort - tricksRemaining} - cannot make contract`;
  } else if (tricksWon >= tricksNeeded) {
    status = 'safe';
    statusMessage = `Contract made with ${tricksRemaining} tricks remaining`;
  } else if (tricksShort === tricksRemaining) {
    status = 'danger';
    statusMessage = 'Must win all remaining tricks!';
  }

  return (
    <div className="contract-goal-tracker">
      <div className="goal-header">
        <h4>Contract Goal</h4>
        <span className="goal-statement">
          Need {tricksNeeded} tricks to make {contract.level}{contract.strain}
        </span>
      </div>

      <div className="progress-section">
        <div className="progress-bar-container">
          <div
            className={`progress-bar-fill ${status}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
          >
            <span className="progress-bar-label">
              {tricksWon} / {tricksNeeded}
            </span>
          </div>
        </div>
      </div>

      <div className="goal-details">
        <div className="detail-item">
          <span className="detail-label">Tricks Won:</span>
          <span className="detail-value">{tricksWon}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Tricks Remaining:</span>
          <span className="detail-value">{tricksRemaining}</span>
        </div>
        <div className={`status-message ${status}`}>
          {statusMessage}
        </div>
      </div>
    </div>
  );
}
```

```css
/* ContractGoalTracker.css */
.contract-goal-tracker {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  margin: var(--space-4) 0;
}

.goal-header {
  margin-bottom: var(--space-4);
}

.goal-header h4 {
  margin: 0 0 var(--space-2) 0;
  color: var(--color-info);
  font-size: var(--text-lg);
}

.goal-statement {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.progress-section {
  margin: var(--space-4) 0;
}

.progress-bar-container {
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  height: 32px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
}

.progress-bar-fill {
  height: 100%;
  transition: width 0.5s ease;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-bar-fill.on-track {
  background: linear-gradient(90deg, var(--color-success), #66bb6a);
}

.progress-bar-fill.danger {
  background: linear-gradient(90deg, var(--color-danger), #ef5350);
}

.progress-bar-fill.safe {
  background: linear-gradient(90deg, var(--color-info), #4fc3f7);
}

.progress-bar-label {
  color: white;
  font-weight: 700;
  font-size: var(--text-base);
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}

.goal-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--bg-tertiary);
}

.detail-label {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.detail-value {
  color: var(--text-primary);
  font-weight: 600;
  font-size: var(--text-base);
}

.status-message {
  margin-top: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  text-align: center;
  font-weight: 600;
  font-size: var(--text-sm);
}

.status-message.on-track {
  background: rgba(76, 175, 80, 0.2);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.status-message.danger {
  background: rgba(244, 67, 54, 0.2);
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}

.status-message.safe {
  background: rgba(97, 218, 251, 0.2);
  color: var(--color-info);
  border: 1px solid var(--color-info);
}

@media (max-width: 768px) {
  .contract-goal-tracker {
    padding: var(--space-4);
  }

  .progress-bar-container {
    height: 24px;
  }

  .progress-bar-label {
    font-size: var(--text-sm);
  }
}
```

---

## 🔍 Code Review Checklist

### Before Merging Any UI Code, Verify:

- [ ] **Follows color palette** - No random colors introduced
- [ ] **Responsive** - Tested at 480px, 768px, 900px, 1200px
- [ ] **Accessible** - Keyboard navigable, screen reader labels, sufficient contrast
- [ ] **Consistent spacing** - Uses spacing scale (--space-N)
- [ ] **Consistent typography** - Uses defined font sizes
- [ ] **Loading states** - Never shows blank screens
- [ ] **Error handling** - Educational error messages, not technical
- [ ] **Animations respect prefers-reduced-motion**
- [ ] **Touch targets ≥44px** on mobile
- [ ] **Tooltips for unclear elements**
- [ ] **Focus indicators present**
- [ ] **Component follows design patterns** in this document

---

## 📖 Component Library Reference

### Existing Components (Use These)
Located in: `frontend/src/`

- `PlayComponents.js` - Card play UI components
  - `PlayableCard` - Interactive card display
  - `CurrentTrick` - Center play area
  - `PlayTable` - Main play layout
  - `BiddingSummary` - Auction history
  - `ContractDisplay` - Contract information
  - `ScoreDisplay` - Final score modal

### Components to Create (Phase 1)
Reference: `INTERFACE_IMPROVEMENTS_PLAN.md`

- `TurnIndicator` - Whose turn visualization
- `ContractGoalTracker` - Progress toward making contract
- `LegalPlayIndicator` - Highlight legal/illegal plays
- `HintSystem` - Hint display and management
- `EducationalError` - Improved error messages

### Components to Create (Phase 2)
- `AnalysisModal` - Post-hand analysis display
- `MistakeCard` - Individual mistake explanation
- `ReplayControls` - Replay navigation
- `TrickHistoryPanel` - Past tricks viewer
- `ComparativeResults` - Result distribution charts

---

## 🚀 Quick Start for New Features

### Process for Adding UI:

1. **Check this document first** - Is there a pattern for this?
2. **Reference INTERFACE_IMPROVEMENTS_PLAN.md** - Is this feature planned?
3. **Use existing components** - Don't recreate if it exists
4. **Copy component examples** from this doc
5. **Use CSS variables** - Never hardcode colors/spacing
6. **Test responsively** - Check all breakpoints
7. **Add accessibility** - ARIA labels, keyboard nav
8. **Document changes** - Update this file if adding new patterns

### Example Workflow:

```bash
# 1. Create component file
touch frontend/src/components/play/TurnIndicator.js
touch frontend/src/components/play/TurnIndicator.css

# 2. Copy example from this document
# (See "Component Examples" section above)

# 3. Import CSS variables
# In TurnIndicator.css, reference variables like:
# color: var(--color-info);
# padding: var(--space-4);

# 4. Test at all breakpoints
# Use browser dev tools responsive mode

# 5. Verify accessibility
# Tab through with keyboard
# Test with screen reader
# Check contrast with accessibility tools
```

---

## 🎓 Learning Resources

### Bridge UI/UX Inspiration
- **BBO (Bridge Base Online)**: https://www.bridgebase.com/
- **Funbridge**: https://funbridge.com/
- **SharkBridge**: https://www.thesharkbridgecompany.com/

### General UI/UX
- **Material Design**: https://m3.material.io/
- **Apple HIG**: https://developer.apple.com/design/human-interface-guidelines/
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/

### Accessibility Tools
- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **axe DevTools**: https://www.deque.com/axe/devtools/
- **NVDA Screen Reader**: https://www.nvaccess.org/

---

## 📞 Questions?

When making UI/UX decisions not covered here:

1. **Check competitive apps** - What do BBO/Funbridge do?
2. **Ask: "Does this help learners?"** - Primary user test
3. **Consistency > Innovation** - Match existing patterns
4. **Document new patterns** - Update this file

---

## 🔄 Document Updates

**Update this document when:**
- Adding new UI components
- Establishing new design patterns
- Learning from user feedback
- Discovering better practices

**Version History:**
- v1.0 (2025-10-12): Initial creation based on competitive analysis

---

**END OF DOCUMENT**

This is the authoritative source for UI/UX decisions in the Bridge Bidding App.
When in doubt, reference this document. When this document doesn't cover something, update it.
