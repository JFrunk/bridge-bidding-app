# UI/UX Refactoring Plan: Shadcn/ui + Tailwind CSS Migration

## Overview

This document provides a **step-by-step tactical plan** for migrating the Bridge Bidding Application from custom CSS to Shadcn/ui + Tailwind CSS, following the strategic framework defined in [UI_UX_FRAMEWORK.md](./UI_UX_FRAMEWORK.md).

**Estimated Timeline**: 8 weeks
**Risk Level**: Medium (UI changes only, no logic changes)
**Rollback Strategy**: Git branches for each sprint

---

## Phase 0: Preparation (Week 0)

### 0.1 Create Feature Branch
```bash
git checkout -b refactor/shadcn-tailwind-migration
git push -u origin refactor/shadcn-tailwind-migration
```

### 0.2 Baseline Metrics
Capture current state before any changes:

```bash
cd frontend
npm run build
# Record build size, warnings
npm test -- --coverage
# Record test coverage
```

**Save to**: `.claude/baseline_metrics_refactoring.txt`

### 0.3 Backup Critical Files
```bash
cp src/App.js src/App.js.backup
cp src/App.css src/App.css.backup
cp src/PlayComponents.js src/PlayComponents.js.backup
cp src/PlayComponents.css src/PlayComponents.css.backup
```

---

## Phase 1: Foundation Setup (Week 1)

### 1.1 Install Tailwind CSS

**Step 1**: Install dependencies
```bash
cd frontend
npm install -D tailwindcss@latest postcss@latest autoprefixer@latest
npx tailwindcss init -p
```

**Step 2**: Configure Tailwind (`tailwind.config.js`)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Bridge-specific colors
        'success': '#4caf50',
        'danger': '#f44336',
        'info': '#61dafb',
        'suit-red': '#d32f2f',
        'suit-black': '#000000',

        // Partnership colors
        'partnership-ns': '#4caf50',
        'partnership-ew': '#ff9800',

        // Backgrounds
        'bg-primary': '#1a1a1a',
        'bg-secondary': '#2a2a2a',
        'bg-tertiary': '#3a3a3a',

        // Special states
        'highlight-current': '#61dafb',
        'highlight-winner': '#ffd700',
      },
      spacing: {
        // Add custom spacing to match existing design
        '15': '3.75rem',
      },
      borderRadius: {
        'card': '6px',
      },
    },
  },
  plugins: [],
}
```

**Step 3**: Add Tailwind directives to CSS (`src/index.css`)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Keep existing body styles temporarily */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  background-color: #3d6b52;
  color: white;
  padding: 20px;
}
```

**Step 4**: Verify build
```bash
npm start
# Should compile without errors
```

### 1.2 Install Shadcn/ui

**Step 1**: Install CLI and dependencies
```bash
npm install class-variance-authority clsx tailwind-merge
npm install lucide-react  # Icon library used by Shadcn
npx shadcn-ui@latest init
```

**Interactive prompts** (select these options):
- Style: Default
- Base color: Slate
- CSS variables: Yes
- Config location: `tailwind.config.js`
- Component location: `src/components/ui`
- Utils location: `src/lib/utils.js`
- React Server Components: No
- Write config: Yes

**Step 2**: Install first components
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
```

**Step 3**: Verify components exist
```bash
ls src/components/ui/
# Should show: button.jsx, card.jsx, dialog.jsx
```

### 1.3 Create Utility Helper

**File**: `src/lib/utils.js` (already created by Shadcn init)

Verify it contains:
```javascript
import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}
```

### 1.4 Test Integration

**Create test component** (`src/components/TestShadcn.js`):
```jsx
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export function TestShadcn() {
  return (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Shadcn Test</CardTitle>
      </CardHeader>
      <CardContent>
        <Button variant="default">Test Button</Button>
      </CardContent>
    </Card>
  );
}
```

**Add to App.js temporarily**:
```jsx
import { TestShadcn } from './components/TestShadcn';

// In return statement, add temporarily:
<TestShadcn />
```

**Run and verify**: Card and button should render with Shadcn styling.

**Remove test component** after verification.

---

## Phase 2: Migrate Core Components (Week 2-3)

### 2.1 Migrate Card Component

**Current State**: Card defined inline in App.js (lines 9-30)

**Target**: Shared BridgeCard component using Shadcn Card

**File**: `src/components/bridge/BridgeCard.jsx`

```jsx
import { Card as ShadcnCard } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function BridgeCard({ rank, suit, onClick, disabled = false, className }) {
  const suitColor = suit === '♥' || suit === '♦' ? 'text-suit-red' : 'text-suit-black';

  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[rank] || rank;

  return (
    <ShadcnCard
      className={cn(
        "relative w-[70px] h-[100px] bg-white border border-gray-400 rounded-card shadow-md",
        "transition-transform duration-200 hover:-translate-y-4 hover:z-50",
        disabled && "opacity-60 cursor-not-allowed",
        !disabled && onClick && "cursor-pointer",
        className
      )}
      onClick={!disabled ? onClick : undefined}
    >
      {/* Top-left corner */}
      <div className={cn("absolute top-1 left-1.5 flex flex-col items-center", suitColor)}>
        <span className="text-lg font-bold leading-none">{displayRank}</span>
        <span className="text-base leading-none">{suit}</span>
      </div>

      {/* Center suit symbol */}
      <div className={cn("absolute inset-0 flex items-center justify-center", suitColor)}>
        <span className="text-4xl leading-none">{suit}</span>
      </div>

      {/* Bottom-right corner (rotated) */}
      <div className={cn("absolute bottom-1 right-1.5 flex flex-col items-center rotate-180", suitColor)}>
        <span className="text-lg font-bold leading-none">{displayRank}</span>
        <span className="text-base leading-none">{suit}</span>
      </div>
    </ShadcnCard>
  );
}
```

**Migration Steps**:
1. Create `src/components/bridge/` directory
2. Create BridgeCard.jsx with above code
3. Replace Card usage in App.js:
   ```jsx
   // OLD
   import { Card } from './App.js' // inline component

   // NEW
   import { BridgeCard } from '@/components/bridge/BridgeCard'

   // Replace all <Card rank={} suit={} /> with <BridgeCard rank={} suit={} />
   ```
4. Delete inline Card component from App.js (lines 9-30)
5. Test: Verify cards render correctly in bidding phase

### 2.2 Migrate BiddingBox Component

**Current State**: Custom CSS in App.css (lines 132-174)

**Target**: Shadcn Button components with Tailwind

**File**: `src/components/bridge/BiddingBox.jsx`

```jsx
import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function BiddingBox({ onBid, disabled, auction }) {
  const [level, setLevel] = useState(null);
  const suits = ['♣', '♦', '♥', '♠', 'NT'];
  const calls = ['Pass', 'X', 'XX'];

  const lastRealBid = [...auction].reverse().find(b => !['Pass', 'X', 'XX'].includes(b.bid));
  const suitOrder = { '♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5 };

  const isBidLegal = (level, suit) => {
    if (!lastRealBid) return true;
    const lastLevel = parseInt(lastRealBid.bid[0], 10);
    const lastSuit = lastRealBid.bid.slice(1);
    if (level > lastLevel) return true;
    if (level === lastLevel && suitOrder[suit] > suitOrder[lastSuit]) return true;
    return false;
  };

  const handleBid = (suit) => {
    if (level) {
      onBid(suit === 'NT' ? `${level}NT` : `${level}${suit}`);
      setLevel(null);
    }
  };

  const handleCall = (call) => {
    onBid(call);
    setLevel(null);
  };

  return (
    <div className="flex flex-col gap-2.5 p-4 bg-bg-secondary rounded-lg">
      <h3 className="m-0 mb-2.5 text-white text-base">Bidding</h3>

      {/* Level buttons */}
      <div className="flex flex-row gap-2 justify-center">
        {[1, 2, 3, 4, 5, 6, 7].map(l => (
          <Button
            key={l}
            onClick={() => setLevel(l)}
            variant={level === l ? "default" : "outline"}
            disabled={disabled}
            className="w-12 h-10"
          >
            {l}
          </Button>
        ))}
      </div>

      {/* Suit buttons */}
      <div className="flex flex-row gap-2 justify-center">
        {suits.map(s => (
          <Button
            key={s}
            onClick={() => handleBid(s)}
            disabled={!level || disabled || !isBidLegal(level, s)}
            variant="outline"
            className="w-12 h-10"
          >
            {s === 'NT' ? 'NT' : (
              <span className={s === '♥' || s === '♦' ? 'text-suit-red' : 'text-suit-black'}>
                {s}
              </span>
            )}
          </Button>
        ))}
      </div>

      {/* Call buttons */}
      <div className="flex flex-row gap-2 justify-center">
        {calls.map(c => (
          <Button
            key={c}
            onClick={() => handleCall(c)}
            disabled={disabled}
            variant="outline"
            className="w-16 h-10"
          >
            {c}
          </Button>
        ))}
      </div>
    </div>
  );
}
```

**Migration Steps**:
1. Create BiddingBox.jsx with above code
2. Replace usage in App.js:
   ```jsx
   // OLD
   <BiddingBox onBid={handleUserBid} disabled={...} auction={auction} />

   // NEW (same, just change import)
   import { BiddingBox } from '@/components/bridge/BiddingBox'
   ```
3. Delete BiddingBox function from App.js (lines 69-105)
4. Remove BiddingBox CSS from App.css (lines 132-174)
5. Test: Verify bidding works correctly

### 2.3 Migrate Modal Components

**Target Files**:
- Review Modal (App.js lines 1118-1163)
- Convention Help Modal (App.js lines 1165-1200)

**New Component**: `src/components/bridge/ReviewModal.jsx`

```jsx
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export function ReviewModal({
  isOpen,
  onClose,
  onSubmit,
  userConcern,
  setUserConcern,
  reviewPrompt,
  reviewFilename,
  gamePhase,
  onCopyPrompt
}) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Request AI Review</DialogTitle>
          <DialogDescription>
            {gamePhase === 'playing'
              ? 'Hand data including auction and card play will be saved to: '
              : 'Hand data will be saved to: '}
            <code className="bg-secondary px-1.5 py-0.5 rounded text-info">
              backend/review_requests/{reviewFilename || 'hand_[timestamp].json'}
            </code>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label htmlFor="user-concern" className="block text-sm font-semibold mb-2">
              What concerns you about this hand? (Optional)
            </label>
            <Textarea
              id="user-concern"
              value={userConcern}
              onChange={(e) => setUserConcern(e.target.value)}
              placeholder={
                gamePhase === 'playing'
                  ? "e.g., 'Should declarer have led a different suit?'"
                  : "e.g., 'Why did North bid 3NT here?'"
              }
              rows={3}
            />
          </div>

          <div className="flex gap-2">
            <Button onClick={onSubmit} className="flex-1">
              Save & Generate Prompt
            </Button>
            <Button onClick={onClose} variant="outline" className="flex-1">
              Cancel
            </Button>
          </div>

          {reviewPrompt && (
            <div className="border-t pt-4">
              <h3 className="text-lg font-semibold mb-2">Copy this prompt to Claude Code:</h3>
              <div className="bg-secondary border rounded p-4 max-h-48 overflow-y-auto mb-4">
                <pre className="text-sm whitespace-pre-wrap">{reviewPrompt}</pre>
              </div>
              <div className="flex gap-2">
                <Button onClick={onCopyPrompt} className="flex-1">
                  📋 Copy to Clipboard
                </Button>
                <Button onClick={onClose} variant="outline" className="flex-1">
                  Close
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

**Install additional Shadcn components**:
```bash
npx shadcn-ui@latest add textarea
```

**Migration Steps**:
1. Create ReviewModal.jsx
2. Create similar ConventionHelpModal.jsx
3. Replace modal JSX in App.js with component usage
4. Remove modal CSS from App.css (lines 370-595)

---

## Phase 3: Migrate Play Components (Week 4-5)

### 3.1 Audit PlayComponents.js

**Current Structure**:
- BiddingSummary (lines ~20-60)
- ContractDisplay (lines ~60-100)
- TricksDisplay (lines ~100-140)
- PlayTable (lines ~140-400)
- ScoreDisplay (lines ~400-450)

**Target**: Break into smaller components using Shadcn + Tailwind

### 3.2 Create PlayTable Component

**File**: `src/components/play/PlayTable.jsx`

This is complex - will need to be broken down further. Key sections:
1. **Contract Header** (consolidated as per UI_REFACTOR_PLAN.md)
2. **Compass Play Area** (grid layout)
3. **User Hand Display**
4. **Dummy Hand Display**

**Priority**: Start with Contract Header

**File**: `src/components/play/ContractHeader.jsx`

```jsx
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function ContractHeader({ playState, auction }) {
  if (!playState?.contract) return null;

  const { contract, declarer } = playState.contract;
  const tricksWon = playState.tricks_won || {};
  const totalTricks = Object.values(tricksWon).reduce((a, b) => a + b, 0);
  const tricksNeeded = parseInt(contract[0]) + 6;
  const tricksLost = 13 - totalTricks - (13 - totalTricks - tricksNeeded);
  const tricksRemaining = 13 - totalTricks;

  const wonPercent = (tricksWon / 13) * 100;
  const lostPercent = (tricksLost / 13) * 100;
  const remainingPercent = (tricksRemaining / 13) * 100;

  return (
    <div className="flex items-stretch gap-4 p-4 bg-success rounded-lg mb-6 min-h-[100px]">
      {/* Unified Tricks Bar */}
      <div className="flex-[2] flex items-stretch rounded-md overflow-hidden bg-bg-tertiary min-h-[80px]">
        <div
          className="flex items-center justify-center bg-gradient-to-r from-success to-green-400 transition-all duration-300"
          style={{ width: `${wonPercent}%` }}
        >
          <span className="text-2xl font-bold text-white drop-shadow-md">
            {tricksWon}
          </span>
        </div>
        <div
          className="flex items-center justify-center bg-bg-tertiary transition-all duration-300"
          style={{ width: `${remainingPercent}%` }}
        >
          <span className="text-2xl font-bold text-white drop-shadow-md">
            {tricksRemaining}
          </span>
        </div>
        <div
          className="flex items-center justify-center bg-gradient-to-r from-red-400 to-danger transition-all duration-300"
          style={{ width: `${lostPercent}%` }}
        >
          <span className="text-2xl font-bold text-white drop-shadow-md">
            {tricksLost}
          </span>
        </div>
      </div>

      {/* Contract Display */}
      <Card className="flex-1 bg-bg-secondary rounded-md">
        <CardContent className="flex flex-col items-center justify-center h-full gap-2 p-4">
          <span className="text-3xl font-bold text-white leading-none">
            {contract}
          </span>
          <span className="text-lg text-gray-400">
            by {declarer}
          </span>
        </CardContent>
      </Card>

      {/* Tricks Summary */}
      <Card className="flex-1 bg-bg-secondary rounded-md">
        <CardContent className="flex flex-col justify-around h-full p-4">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400 min-w-[80px]">Won:</span>
            <span className="text-xl font-bold text-white">{tricksWon}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400 min-w-[80px]">Lost:</span>
            <span className="text-xl font-bold text-white">{tricksLost}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400 min-w-[80px]">Remaining:</span>
            <span className="text-xl font-bold text-white">{tricksRemaining}</span>
          </div>
        </CardContent>
      </Card>

      {/* Compact Bidding Summary */}
      <Card className="flex-1 bg-bg-secondary rounded-md overflow-hidden">
        <div className="p-3 text-lg font-bold text-white bg-bg-tertiary text-center border-b-2 border-bg-primary">
          Bidding
        </div>
        <div className="flex-1 overflow-y-auto p-2 text-sm max-h-[60px]">
          {auction.map((bid, i) => (
            <div key={i} className="flex items-center gap-3 p-0.5">
              <span className="font-bold text-info min-w-[20px]">
                {['N', 'E', 'S', 'W'][i % 4]}
              </span>
              <span className="text-white">{bid.bid}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
```

**Migration Steps**:
1. Create ContractHeader.jsx
2. Import and use in PlayTable
3. Remove old header components from PlayComponents.js
4. Update PlayComponents.css to remove old styles
5. Test rendering during play phase

### 3.3 Migrate Remaining Play Components

**Week 5 Tasks**:
- [ ] Create PlayArea.jsx (compass layout grid)
- [ ] Create TrickDisplay.jsx (center area)
- [ ] Create UserHand.jsx (South position)
- [ ] Create DummyHand.jsx (revealed hand)
- [ ] Create ScoreModal.jsx (end-of-hand scoring)

---

## Phase 4: State Management Migration (Week 6)

### 4.1 Install Zustand

```bash
cd frontend
npm install zustand
```

### 4.2 Create Bidding Store

**File**: `src/stores/biddingStore.js`

```javascript
import { create } from 'zustand';

export const useBiddingStore = create((set, get) => ({
  // State
  hand: [],
  handPoints: null,
  auction: [],
  players: ['North', 'East', 'South', 'West'],
  dealer: 'North',
  nextPlayerIndex: 0,
  isAiBidding: false,
  vulnerability: 'None',
  allHands: null,
  showHandsThisDeal: false,
  alwaysShowHands: false,
  selectedScenario: '',
  scenarioList: [],
  initialDeal: null,

  // Actions
  setHand: (hand, points) => set({ hand, handPoints: points }),

  addBid: (bidObject) => set((state) => ({
    auction: [...state.auction, bidObject],
    nextPlayerIndex: (state.nextPlayerIndex + 1) % 4,
  })),

  setAiBidding: (isAiBidding) => set({ isAiBidding }),

  resetAuction: (dealData, skipInitialAiBidding = false) => set({
    initialDeal: dealData,
    hand: dealData.hand,
    handPoints: dealData.points,
    vulnerability: dealData.vulnerability,
    auction: [],
    nextPlayerIndex: get().players.indexOf(get().dealer),
    isAiBidding: !skipInitialAiBidding,
  }),

  setAllHands: (hands) => set({ allHands: hands }),

  toggleShowHandsThisDeal: () => set((state) => ({
    showHandsThisDeal: !state.showHandsThisDeal
  })),

  toggleAlwaysShowHands: () => set((state) => ({
    alwaysShowHands: !state.alwaysShowHands,
    showHandsThisDeal: !state.alwaysShowHands ? true : state.showHandsThisDeal,
  })),

  setScenarios: (scenarios) => set({
    scenarioList: scenarios,
    selectedScenario: scenarios[0] || '',
  }),

  setSelectedScenario: (scenario) => set({ selectedScenario: scenario }),
}));
```

### 4.3 Migrate App.js to Use Bidding Store

**Step 1**: Import store at top of App.js
```jsx
import { useBiddingStore } from './stores/biddingStore';
```

**Step 2**: Replace useState calls with store
```jsx
// OLD
const [hand, setHand] = useState([]);
const [handPoints, setHandPoints] = useState(null);
const [auction, setAuction] = useState([]);

// NEW
const {
  hand,
  handPoints,
  auction,
  addBid,
  setHand,
  resetAuction,
  // ... other selectors
} = useBiddingStore();
```

**Step 3**: Update functions to use store actions
```jsx
// OLD
setAuction([...auction, newBid]);
setNextPlayerIndex((nextPlayerIndex + 1) % 4);

// NEW
addBid(newBid);
```

**Step 4**: Test bidding flow thoroughly

### 4.4 Create Play Store

**File**: `src/stores/playStore.js`

```javascript
import { create } from 'zustand';

export const usePlayStore = create((set) => ({
  // State
  gamePhase: 'bidding',
  playState: null,
  dummyHand: null,
  declarerHand: null,
  isPlayingCard: false,
  scoreData: null,

  // Actions
  startPlay: (playState) => set({
    gamePhase: 'playing',
    playState,
    isPlayingCard: true,
  }),

  updatePlayState: (playState) => set({ playState }),

  setDummyHand: (hand) => set({ dummyHand: hand }),

  setDeclarerHand: (hand) => set({ declarerHand: hand }),

  setIsPlayingCard: (isPlaying) => set({ isPlayingCard: isPlaying }),

  setScoreData: (data) => set({ scoreData: data }),

  resetPlay: () => set({
    gamePhase: 'bidding',
    playState: null,
    dummyHand: null,
    declarerHand: null,
    isPlayingCard: false,
    scoreData: null,
  }),
}));
```

### 4.5 Migrate Play State

Similar process to bidding store migration.

---

## Phase 5: Cleanup & Polish (Week 7)

### 5.1 Remove Old CSS Files

**Audit**: Check which CSS can be deleted
```bash
# Check for unused CSS classes
grep -r "className=" src/ | grep -v node_modules > used_classes.txt
# Compare with CSS files
```

**Files to review**:
- [ ] App.css - Can remove most styles, keep only body/container
- [ ] PlayComponents.css - Remove after PlayTable migration
- [ ] shared/components/*.css - Migrate to Tailwind

### 5.2 Update Import Paths

**Configure path alias** in `jsconfig.json`:
```json
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "@/*": ["*"]
    }
  }
}
```

**Update all imports**:
```jsx
// OLD
import { Card } from '../../../components/ui/card'

// NEW
import { Card } from '@/components/ui/card'
```

### 5.3 Accessibility Audit

**Run automated checks**:
```bash
npm install -D @axe-core/react
```

**Add to index.js** (development only):
```jsx
if (process.env.NODE_ENV !== 'production') {
  import('@axe-core/react').then(axe => {
    axe.default(React, ReactDOM, 1000);
  });
}
```

**Manual checks**:
- [ ] All buttons have accessible labels
- [ ] Color contrast meets WCAG AA
- [ ] Keyboard navigation works
- [ ] Screen reader announces state changes

### 5.4 Performance Optimization

**Lazy load play components**:
```jsx
import { lazy, Suspense } from 'react';

const PlayTable = lazy(() => import('@/components/play/PlayTable'));

// In render:
<Suspense fallback={<div>Loading play table...</div>}>
  <PlayTable />
</Suspense>
```

**Measure bundle size**:
```bash
npm run build
npx source-map-explorer 'build/static/js/*.js'
```

**Target**: Total JS < 500KB gzipped

---

## Phase 6: Testing & Documentation (Week 8)

### 6.1 Update Tests

**For each migrated component**:
1. Update imports to new paths
2. Add tests for Tailwind classes (if needed)
3. Test accessibility
4. Test responsive behavior

**Example test** (`BridgeCard.test.jsx`):
```jsx
import { render, screen } from '@testing-library/react';
import { BridgeCard } from '../BridgeCard';

describe('BridgeCard', () => {
  it('renders rank and suit', () => {
    render(<BridgeCard rank="A" suit="♠" />);
    expect(screen.getAllByText('A')).toHaveLength(2);
    expect(screen.getAllByText('♠')).toHaveLength(3);
  });

  it('applies red color to hearts and diamonds', () => {
    const { container } = render(<BridgeCard rank="A" suit="♥" />);
    expect(container.querySelector('.text-suit-red')).toBeInTheDocument();
  });

  it('is clickable when not disabled', () => {
    const handleClick = jest.fn();
    render(<BridgeCard rank="A" suit="♠" onClick={handleClick} />);
    screen.getByRole('button').click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### 6.2 Update Documentation

**Update files**:
- [ ] README.md - Add Tailwind/Shadcn setup instructions
- [ ] UI_UX_FRAMEWORK.md - Mark completed phases
- [ ] REFACTORING_PLAN.md (this file) - Add completion notes

**Create new docs**:
- [ ] `docs/COMPONENT_LIBRARY.md` - Visual catalog of all components
- [ ] `docs/TAILWIND_PATTERNS.md` - Common patterns for LLM reference

### 6.3 Final QA Checklist

- [ ] All pages render without errors
- [ ] Bidding flow works end-to-end
- [ ] Play phase works end-to-end
- [ ] Modals open and close correctly
- [ ] Mobile responsive (test on 320px, 768px, 1024px)
- [ ] Accessibility: keyboard navigation works
- [ ] Accessibility: screen reader announces correctly
- [ ] Performance: Lighthouse score >90 all categories
- [ ] Build size: <500KB gzipped
- [ ] All tests pass
- [ ] No console errors or warnings

---

## Phase 7: Deployment (Week 8+)

### 7.1 Merge to Main

**Steps**:
1. Ensure all tests pass
2. Create PR from refactor branch
3. Review changes
4. Squash commits if needed
5. Merge to main

```bash
git checkout refactor/shadcn-tailwind-migration
git rebase main  # Resolve conflicts if any
git push origin refactor/shadcn-tailwind-migration

# Create PR on GitHub
# After approval:
git checkout main
git merge --squash refactor/shadcn-tailwind-migration
git commit -m "Refactor: Migrate to Shadcn/ui + Tailwind CSS"
git push origin main
```

### 7.2 Monitor Production

**Watch for**:
- Build errors
- Runtime errors in browser console
- Performance regressions
- User-reported issues

### 7.3 Rollback Plan (if needed)

**If critical issues arise**:
```bash
git revert HEAD  # Revert the merge commit
git push origin main
```

**Or**: Deploy previous version from backup

---

## Rollback Strategy

### Level 1: Component Rollback
If a single component has issues, revert just that file:
```bash
git checkout HEAD~1 -- src/components/bridge/BridgeCard.jsx
```

### Level 2: Phase Rollback
If an entire phase fails, cherry-pick good commits:
```bash
git log --oneline
git cherry-pick <good-commit-hash>
```

### Level 3: Full Rollback
Revert entire refactoring:
```bash
git revert <merge-commit-hash>
```

---

## Success Metrics

### Before Migration
- Build time: [X seconds]
- Bundle size: [X KB]
- Lighthouse score: [X]
- Test coverage: [X%]
- Component count: [X]

### After Migration (Targets)
- Build time: <60 seconds
- Bundle size: <500KB gzipped
- Lighthouse score: >90 all categories
- Test coverage: >80%
- Component count: Reduced by 30% (reuse)
- CSS files: Reduced from 8 to 2

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Build breaks | Low | High | Test after each phase, maintain backup branch |
| UI regression | Medium | Medium | Visual regression tests, manual QA |
| Performance issues | Low | Medium | Monitor bundle size, lazy load |
| Accessibility regression | Medium | High | Automated axe tests, manual testing |
| State management bugs | High | High | Migrate incrementally, test thoroughly |

---

## Lessons Learned (Post-Migration)

*To be filled in after completion*

### What Went Well
-

### What Could Be Improved
-

### Recommendations for Future
-

---

**Document Status**: Ready for Implementation
**Last Updated**: 2025-10-13
**Author**: Claude Code
**Reviewer**: Simon Roy
