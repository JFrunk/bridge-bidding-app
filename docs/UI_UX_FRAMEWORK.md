# UI/UX Framework for Bridge Bidding Application

## Executive Summary

This document establishes a **consistent, LLM-friendly UI/UX framework** for the Bridge Bidding Application, incorporating expert recommendations from UI/UX analysis and aligning with the reality that an LLM coding assistant (Claude Code) is the primary developer.

**Framework Choice**: **Shadcn/ui + Tailwind CSS**
- **Why**: Atomic utility-first design optimized for LLM code generation
- **Backend**: FastAPI + Pydantic (already in use)
- **State Management**: Zustand or Jotai (recommendation for migration)

---

## I. Current State Analysis

### Architecture Overview
- **Frontend**: React 19.1.1 (functional, but "rough UI experience")
- **Styling**: Mix of vanilla CSS files with CSS variables
- **Component Structure**: Mix of inline components and shared components
- **State**: React hooks (useState, useEffect)
- **API Layer**: FastAPI backend at localhost:5001

### Identified Issues
1. **Inconsistent Component Patterns**: Card components duplicated in App.js and shared/components
2. **Mixed Styling Approaches**: CSS modules, inline styles, and CSS variables all coexist
3. **No Design System Enforcement**: Components created ad-hoc without unified standards
4. **Complex State Management**: Deep prop drilling and scattered state logic
5. **No Component Library**: Each UI element built from scratch

### Strengths to Preserve
1. **Well-defined CSS variables** in PlayComponents.css (color palette, spacing, typography)
2. **Shared component architecture** started in frontend/src/shared/
3. **Comprehensive testing** setup with @testing-library
4. **Clear separation** between bidding and play phases

---

## II. The "Rule of Three" Design System

### Product Manager Governance Rules
*These simple rules ensure consistency without requiring deep UI/UX expertise*

#### 1. Typography - Three Sizes
```css
--text-base: 1rem;     /* 16px - Body text, standard UI */
--text-xl: 1.25rem;    /* 20px - Section headings, emphasis */
--text-3xl: 2rem;      /* 32px - Page titles, major headings */
```

**Rule**: LLM MUST ONLY use these three sizes. No exceptions.

#### 2. Color Palette - Three Core Colors + Suit Colors
```css
/* Core Feedback Colors */
--color-success: #4caf50;   /* Green - Legal, correct, positive */
--color-danger: #f44336;    /* Red - Illegal, error, negative */
--color-info: #61dafb;      /* Blue - Highlights, information */

/* Bridge-Specific (Never Change) */
--suit-red: #d32f2f;        /* Hearts & Diamonds */
--suit-black: #000000;      /* Spades & Clubs */
```

**Rule**: ALL feedback uses these three colors. Suits ALWAYS use standard bridge colors.

#### 3. Spacing - Three Levels
```css
--space-4: 1rem;      /* 16px - Standard spacing between elements */
--space-6: 1.5rem;    /* 24px - Section spacing */
--space-12: 3rem;     /* 48px - Major layout spacing */
```

**Rule**: Component gaps, padding, margins use ONLY these three values.

#### 4. Border Radius - Three Levels
```css
--radius-sm: 4px;     /* Buttons, small cards */
--radius-md: 8px;     /* Standard cards, panels */
--radius-lg: 12px;    /* Large containers, modals */
```

#### 5. The "One Layout" Rule
**Mandate**: The application has ONE top-level layout structure that NEVER changes:
```
┌─────────────────────────────────────┐
│         Header / Title              │
├─────────────────────────────────────┤
│                                     │
│         Main Content Area           │
│     (Bidding or Play Phase)         │
│                                     │
├─────────────────────────────────────┤
│         Action Controls             │
└─────────────────────────────────────┘
```

**Rule**: LLM cannot deviate from this structure. All pages/views follow this pattern.

---

## III. Component Library Standards

### A. Shadcn/ui + Tailwind CSS Migration Plan

#### Phase 1: Setup (Week 1)
1. **Install Dependencies**
   ```bash
   cd frontend
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   npm install class-variance-authority clsx tailwind-merge
   ```

2. **Configure Tailwind** (tailwind.config.js)
   ```javascript
   module.exports = {
     content: ["./src/**/*.{js,jsx,ts,tsx}"],
     theme: {
       extend: {
         colors: {
           success: '#4caf50',
           danger: '#f44336',
           info: '#61dafb',
           'suit-red': '#d32f2f',
           'suit-black': '#000000',
         },
         spacing: {
           '4': '1rem',
           '6': '1.5rem',
           '12': '3rem',
         },
       },
     },
   }
   ```

3. **Initialize Shadcn/ui**
   ```bash
   npx shadcn-ui@latest init
   ```

#### Phase 2: Create Base Components (Week 2)
Replace existing components with Shadcn/ui equivalents:

| Current Component | Shadcn/ui Replacement | Priority |
|-------------------|----------------------|----------|
| Card (bidding) | shadcn/ui Card | HIGH |
| BiddingBox buttons | shadcn/ui Button | HIGH |
| Modal (review) | shadcn/ui Dialog | MEDIUM |
| Scenario selector | shadcn/ui Select | MEDIUM |
| Error messages | shadcn/ui Alert | LOW |

#### Phase 3: Bridge-Specific Components (Week 3-4)
Build custom components using Shadcn/ui + Tailwind:

1. **BridgeCard Component**
   - Location: `frontend/src/components/ui/bridge-card.jsx`
   - Uses Shadcn Card as base
   - Applies bridge-specific styling (suit colors, rank display)
   - Replaces both App.js Card and shared/components/Card

2. **BiddingBox Component**
   - Location: `frontend/src/components/ui/bidding-box.jsx`
   - Uses Shadcn Button components
   - Enforces SAYC bidding rules via disabled states
   - Clear visual hierarchy (levels → suits → calls)

3. **PlayTable Component**
   - Location: `frontend/src/components/ui/play-table.jsx`
   - Compass layout using Tailwind Grid
   - Integrates TurnIndicator and ContractGoalTracker

### B. Component Reuse Mandate

**Rule**: LLM MUST check for existing components before creating new ones.

**Approved Component Locations**:
```
frontend/src/
├── components/
│   ├── ui/              # Shadcn/ui base components
│   │   ├── button.jsx
│   │   ├── card.jsx
│   │   ├── dialog.jsx
│   │   └── select.jsx
│   ├── bridge/          # Bridge-specific components
│   │   ├── bridge-card.jsx
│   │   ├── bidding-box.jsx
│   │   ├── play-table.jsx
│   │   └── hand-analysis.jsx
│   └── play/            # Play-phase components
│       ├── turn-indicator.jsx
│       └── contract-goal-tracker.jsx
└── shared/              # Legacy (migrate to components/bridge)
```

---

## IV. State Management Strategy

### Current Issues
- Deep prop drilling (e.g., `playState`, `isPlayingCard` passed through multiple levels)
- Multiple useState calls scattered across App.js (38+ state variables)
- Race conditions in AI bidding loop

### Recommended Migration: Zustand

**Why Zustand over Redux**:
- Minimal boilerplate (LLM-friendly)
- No provider wrapping needed
- Simple async action handling
- Smaller bundle size

**Implementation Plan**:

#### 1. Install Zustand
```bash
cd frontend && npm install zustand
```

#### 2. Create Domain Stores

**BiddingStore** (`frontend/src/stores/biddingStore.js`)
```javascript
import create from 'zustand';

export const useBiddingStore = create((set) => ({
  hand: [],
  handPoints: null,
  auction: [],
  nextPlayerIndex: 0,
  isAiBidding: false,
  vulnerability: 'None',

  setHand: (hand) => set({ hand }),
  addBid: (bid) => set((state) => ({
    auction: [...state.auction, bid],
    nextPlayerIndex: (state.nextPlayerIndex + 1) % 4
  })),
  resetAuction: () => set({
    auction: [],
    nextPlayerIndex: 0,
    isAiBidding: false,
  }),
}));
```

**PlayStore** (`frontend/src/stores/playStore.js`)
```javascript
import create from 'zustand';

export const usePlayStore = create((set) => ({
  gamePhase: 'bidding', // 'bidding' | 'playing'
  playState: null,
  dummyHand: null,
  declarerHand: null,
  isPlayingCard: false,
  scoreData: null,

  startPlay: (playState) => set({
    gamePhase: 'playing',
    playState
  }),
  updatePlayState: (playState) => set({ playState }),
  setDummyHand: (hand) => set({ dummyHand: hand }),
}));
```

#### 3. Migration Priority
1. **Phase 1**: Bidding state (lower risk, clearer boundaries)
2. **Phase 2**: Play state (higher complexity, test thoroughly)
3. **Phase 3**: UI state (modals, errors, messages)

---

## V. Future Feature Integration

### A. Bid Interpreter ("Reverse Lookup")
**Requirement**: User clicks a bid → system explains what it means

**Architectural Preparation**:
1. **Backend**: Separate `BidExplainer` class in bidding_engine.py
   ```python
   class BidExplainer:
       def explain_bid(self, bid: str, context: AuctionContext) -> BidExplanation:
           """Returns structured explanation for a bid"""
   ```

2. **Frontend**: Add click handler to BiddingTable
   ```jsx
   const handleBidClick = async (bid) => {
       const explanation = await fetch('/api/explain-bid', {
           method: 'POST',
           body: JSON.stringify({ bid, auction_history })
       });
       showExplanationModal(explanation);
   };
   ```

3. **UI Component**: Shadcn Dialog for explanation display

### B. Custom Convention Input Form
**Requirement**: User can modify point values for conventions

**Architectural Preparation**:
1. **Backend**: Pydantic models for validation
   ```python
   class ConventionSettings(BaseModel):
       min_opening_hcp: int = Field(ge=10, le=20)  # 10-20 range
       weak_two_max: int = Field(ge=8, le=12)
       strong_notrump_min: int = Field(ge=15, le=17)
   ```

2. **Frontend**: Shadcn Form components
   ```jsx
   <Form>
       <FormField name="min_opening_hcp" label="Minimum Opening HCP">
           <Input type="number" min={10} max={20} />
       </FormField>
   </Form>
   ```

3. **State**: Store in Zustand `conventionStore`

### C. Manager / Simulation for Uncertainty
**Requirement**: Track and display confidence in AI decisions

**Architectural Preparation**:
1. **Backend**: Keep game logic modular (already done in engine/)
2. **API Response**: Include confidence scores
   ```json
   {
       "bid": "3NT",
       "confidence": 0.85,
       "alternatives": [
           {"bid": "4♠", "confidence": 0.12}
       ]
   }
   ```

3. **Frontend**: Visual indicator (progress bar or color-coded border)

---

## VI. LLM Prompting Guidelines

### A. Component Creation Prompt Template
```
Create a [component name] component using Shadcn/ui and Tailwind CSS.

REQUIREMENTS:
1. Use ONLY the three font sizes: text-base, text-xl, text-3xl
2. Use ONLY the three colors: success, danger, info
3. Use ONLY the three spacing values: space-4, space-6, space-12
4. File location: frontend/src/components/[domain]/[component-name].jsx
5. Import Shadcn components from @/components/ui/

DESIGN:
- [Specific design requirements]

BEHAVIOR:
- [Specific behavior requirements]

TESTS:
- Create test file at frontend/src/components/[domain]/__tests__/[component-name].test.jsx
```

### B. Refactoring Prompt Template
```
Refactor [file name] to use Shadcn/ui + Tailwind CSS.

CURRENT STATE:
- [Description of current implementation]

TARGET STATE:
- Replace custom CSS with Tailwind utility classes
- Replace inline components with Shadcn/ui components
- Extract reusable logic to custom hooks if needed

CONSTRAINTS:
- Maintain existing functionality
- Follow Rule of Three for typography, colors, spacing
- Add tests to verify no regression

STEPS:
1. Read current file
2. Identify CSS to convert to Tailwind
3. Identify components to replace with Shadcn
4. Implement changes
5. Run tests
```

### C. Code Review Checklist for LLM
Before marking a task complete, LLM must verify:

- [ ] Uses Shadcn/ui components (not custom divs)
- [ ] Uses Tailwind utility classes (not inline styles)
- [ ] Follows Rule of Three (typography, colors, spacing)
- [ ] Component location matches approved structure
- [ ] Has corresponding test file
- [ ] No prop drilling (state via Zustand if complex)
- [ ] Accessible (ARIA labels, keyboard navigation)

---

## VII. Implementation Roadmap

### Sprint 1: Foundation (2 weeks)
- [x] Document UI/UX Framework (this document)
- [ ] Install Tailwind CSS + Shadcn/ui
- [ ] Configure design tokens in tailwind.config.js
- [ ] Create first Shadcn component (Button)
- [ ] Migrate BiddingBox to use Shadcn Button

### Sprint 2: Core Components (2 weeks)
- [ ] Create BridgeCard component (Shadcn + Tailwind)
- [ ] Migrate Card usage in App.js
- [ ] Install Zustand
- [ ] Create BiddingStore
- [ ] Refactor bidding state to use Zustand

### Sprint 3: Play Phase (2 weeks)
- [ ] Create PlayTable component (Shadcn + Tailwind)
- [ ] Migrate PlayComponents.js to Shadcn
- [ ] Create PlayStore
- [ ] Refactor play state to use Zustand
- [ ] Test play phase thoroughly

### Sprint 4: Polish & Future Prep (2 weeks)
- [ ] Migrate all modals to Shadcn Dialog
- [ ] Create ConventionForm component (for future feature)
- [ ] Add BidExplainer UI (for future feature)
- [ ] Documentation update
- [ ] Full regression testing

---

## VIII. Quality Gates

### Before ANY component is merged:
1. **Visual Consistency**: Matches Rule of Three
2. **Accessibility**: WCAG 2.1 AA compliant
3. **Tests**: >80% coverage, all tests pass
4. **Performance**: No layout shift, <100ms interaction delay
5. **LLM Audit**: Passes Code Review Checklist (Section VI.C)

### Continuous Monitoring:
- Bundle size (target: <500KB gzipped)
- Lighthouse score (target: >90 all categories)
- Build time (target: <60s)

---

## IX. References & Resources

### Documentation Links
- [Shadcn/ui Docs](https://ui.shadcn.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Zustand Docs](https://docs.pmnd.rs/zustand/)
- [React 19 Docs](https://react.dev/)

### Design System Examples
- [Vercel Design System](https://vercel.com/design)
- [Radix UI Primitives](https://www.radix-ui.com/)

### Internal References
- `.claude/UI_UX_DESIGN_STANDARDS.md` - CSS variables reference
- `PlayComponents.css` - Current design tokens
- `UI_REFACTOR_PLAN.md` - Tactical refactoring notes

---

## X. Approval & Sign-Off

**Product Manager**: Simon Roy
**Framework Approved**: [Date]
**Implementation Start**: [Date]
**Target Completion**: [Date + 8 weeks]

---

## Appendix A: CSS Variable Migration Map

| Current Variable | Tailwind Equivalent | Notes |
|-----------------|-------------------|-------|
| `--color-success` | `bg-success` | Custom color in config |
| `--color-danger` | `bg-danger` | Custom color in config |
| `--color-info` | `bg-info` | Custom color in config |
| `--space-4` | `gap-4`, `p-4`, `m-4` | 1rem |
| `--space-6` | `gap-6`, `p-6`, `m-6` | 1.5rem |
| `--space-12` | `gap-12`, `p-12`, `m-12` | 3rem |
| `--text-base` | `text-base` | Default |
| `--text-xl` | `text-xl` | Default |
| `--text-3xl` | `text-3xl` | Default |
| `--radius-md` | `rounded-md` | Default |
| `--shadow-md` | `shadow-md` | Default |

## Appendix B: Component Audit

| Component | Current Status | Target State | Priority |
|-----------|---------------|-------------|----------|
| Card (bidding) | Inline in App.js | Shadcn Card | HIGH |
| BiddingBox | Custom CSS | Shadcn Button | HIGH |
| BiddingTable | Custom table | Shadcn Table | MEDIUM |
| PlayTable | Custom grid | Tailwind Grid + Shadcn | HIGH |
| Modal (review) | Custom | Shadcn Dialog | MEDIUM |
| HandAnalysis | Inline | Shared component | LOW |
| ScoreDisplay | Custom modal | Shadcn Dialog | LOW |

---

**Last Updated**: 2025-10-13
**Document Version**: 1.0
**Status**: Draft - Pending Approval
