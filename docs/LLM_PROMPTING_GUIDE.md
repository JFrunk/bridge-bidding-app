# LLM Prompting Guide for UI/UX Development

## Purpose
This document provides **ready-to-use prompt templates** for Claude Code when developing UI components for the Bridge Bidding Application using Shadcn/ui + Tailwind CSS.

---

## Quick Reference: The Rules

### Rule of Three
- **Typography**: `text-base`, `text-xl`, `text-3xl` only
- **Colors**: `success`, `danger`, `info` + bridge suit colors
- **Spacing**: `gap-4`, `gap-6`, `gap-12` (also `p-*`, `m-*`)
- **Border Radius**: `rounded-sm`, `rounded-md`, `rounded-lg`

### Component Location
```
src/
├── components/
│   ├── ui/           # Shadcn base (button, card, dialog)
│   ├── bridge/       # Bridge-specific (bridge-card, bidding-box)
│   └── play/         # Play phase (play-table, turn-indicator)
```

---

## Prompt Templates

### Template 1: Create New Component

```
Create a {COMPONENT_NAME} component for the Bridge Bidding Application.

**Component Type**: {Bridge-specific / Play-phase / UI element}
**File Location**: src/components/{bridge|play|ui}/{component-name}.jsx

**REQUIREMENTS**:
1. Use Shadcn/ui as base: {button|card|dialog|select|etc}
2. Apply Tailwind CSS utility classes
3. Follow "Rule of Three":
   - Typography: ONLY text-base, text-xl, text-3xl
   - Colors: ONLY success, danger, info (+ suit-red, suit-black for cards)
   - Spacing: ONLY gap-4, gap-6, gap-12, p-4, p-6, p-12, m-4, m-6, m-12
   - Border Radius: ONLY rounded-sm, rounded-md, rounded-lg
4. Export as named export: export function {ComponentName}
5. Use cn() utility for conditional classes
6. Add TypeScript-style JSDoc comments for props

**FUNCTIONALITY**:
{Describe what the component should do}

**VISUAL DESIGN**:
{Describe layout, colors, interactions}

**PROPS**:
{List expected props with types}

**EXAMPLE USAGE**:
```jsx
<{ComponentName}
  prop1="value"
  prop2={value}
/>
```

**ACCESSIBILITY**:
- Add aria-label where needed
- Ensure keyboard navigation
- Color contrast must meet WCAG AA

**TESTS**:
Create test file at: src/components/{domain}/__tests__/{component-name}.test.jsx
Test: rendering, interactions, accessibility

Do you understand the requirements? Please create the component.
```

**Example Usage**:
```
Create a BridgeCard component for the Bridge Bidding Application.

**Component Type**: Bridge-specific
**File Location**: src/components/bridge/bridge-card.jsx

**REQUIREMENTS**:
1. Use Shadcn/ui Card as base
2. Apply Tailwind CSS utility classes
3. Follow "Rule of Three" (see above)
4. Export as named export: export function BridgeCard
5. Use cn() utility for conditional classes
6. Add JSDoc comments

**FUNCTIONALITY**:
Display a playing card with rank and suit, with standard bridge card styling.
- Shows rank in corners (top-left, bottom-right rotated)
- Shows large suit symbol in center
- Red color for Hearts and Diamonds, black for Spades and Clubs
- Hover effect: lifts up slightly
- Clickable with onClick handler (optional)
- Can be disabled (grayed out, no interaction)

**VISUAL DESIGN**:
- White background with subtle shadow
- 70px wide x 100px tall
- Rounded corners (rounded-card = 6px)
- Rank displayed as: A, K, Q, J, 10, 9, 8, 7, 6, 5, 4, 3, 2
- Hover: translate up by 16px, increase z-index

**PROPS**:
- rank: string (e.g., 'A', 'K', 'Q', 'J', 'T' for 10, '9', etc.)
- suit: string (e.g., '♠', '♥', '♦', '♣')
- onClick?: function (optional click handler)
- disabled?: boolean (default false)
- className?: string (additional classes)

**EXAMPLE USAGE**:
```jsx
<BridgeCard rank="A" suit="♠" onClick={() => playCard('A', '♠')} />
<BridgeCard rank="K" suit="♥" disabled />
```

**ACCESSIBILITY**:
- Add role="button" if clickable
- Add aria-label="Ace of Spades" (rank of suit)
- Ensure disabled state is announced

**TESTS**:
Create test file at: src/components/bridge/__tests__/bridge-card.test.jsx
Test:
1. Renders rank and suit correctly
2. Applies red color to hearts/diamonds
3. Applies black color to spades/clubs
4. Calls onClick when clicked (if not disabled)
5. Does not call onClick when disabled
6. Has correct aria-label

Do you understand the requirements? Please create the component.
```

---

### Template 2: Migrate Existing Component

```
Migrate the {COMPONENT_NAME} component from custom CSS to Shadcn/ui + Tailwind CSS.

**Current Implementation**:
- File: {current file path}
- Lines: {line numbers if known}

**Target Location**: src/components/{domain}/{component-name}.jsx

**MIGRATION STEPS**:
1. Read the current component implementation
2. Identify Shadcn/ui base component to use: {button|card|dialog|etc}
3. Convert inline styles and CSS classes to Tailwind utilities
4. Apply "Rule of Three" constraints
5. Extract to new file at target location
6. Update imports in parent components
7. Delete old implementation
8. Update or create tests

**CONSTRAINTS**:
- Maintain exact same functionality (no behavior changes)
- Maintain exact same visual appearance (or improve if specified)
- Follow Rule of Three for typography, colors, spacing
- Use Shadcn/ui components as base

**VERIFICATION**:
After migration:
1. Visual comparison: old vs new should look identical
2. Run tests: all existing tests should pass
3. Manual testing: interactions should work the same
4. Check bundle size: should be same or smaller

Please proceed with migration.
```

**Example Usage**:
```
Migrate the BiddingBox component from custom CSS to Shadcn/ui + Tailwind CSS.

**Current Implementation**:
- File: src/App.js
- Lines: 69-105 (component definition)
- CSS: src/App.css, lines 132-174

**Target Location**: src/components/bridge/bidding-box.jsx

**MIGRATION STEPS**:
1. Read App.js lines 69-105 and App.css lines 132-174
2. Identify Shadcn/ui base: Button component
3. Convert CSS to Tailwind:
   - .bidding-box-container → flex flex-col gap-2.5 p-4 bg-bg-secondary rounded-lg
   - .bidding-box-levels → flex flex-row gap-2 justify-center
   - button styling → use Shadcn Button variants
4. Apply Rule of Three
5. Create src/components/bridge/bidding-box.jsx
6. Update import in App.js
7. Delete inline component from App.js
8. Delete CSS from App.css

**CONSTRAINTS**:
- Maintain exact same bidding functionality
- Maintain legal bid validation logic
- Use Shadcn Button with variants: default, outline
- Follow spacing rule: gap-2 or gap-4 only

**VERIFICATION**:
1. Visual: buttons should look similar (Shadcn styled)
2. Tests: bidding logic tests should pass
3. Manual: click levels, suits, calls - should bid correctly
4. Check: CSS file is smaller after deletion

Please proceed with migration.
```

---

### Template 3: Refactor with State Management

```
Refactor {COMPONENT_NAME} to use Zustand for state management.

**Current State**:
- Component: {file path}
- State variables: {list of useState calls to migrate}

**Target Store**: {biddingStore|playStore|uiStore}
**Store Location**: src/stores/{store-name}.js

**MIGRATION STEPS**:
1. Read current component to identify state and actions
2. Read target store (or create if new)
3. Move state and actions to store:
   - State: {variable} → store property
   - Actions: {function} → store action
4. Update component to use store:
   - Import: import { use{Store}Store } from '@/stores/{store-name}'
   - Replace useState: const { {vars}, {actions} } = use{Store}Store()
   - Replace state updates: setVar(val) → action(val)
5. Remove old useState calls
6. Update tests to mock store

**CONSTRAINTS**:
- Do NOT change component logic or behavior
- Do NOT change visual appearance
- Maintain all existing functionality
- Store actions should be pure (no side effects unless necessary)

**VERIFICATION**:
1. All tests pass (update mocks as needed)
2. Manual testing: component works identically
3. No prop drilling: state accessed directly from store
4. DevTools: Zustand store is visible and updates correctly

Please proceed with refactoring.
```

**Example Usage**:
```
Refactor App.js bidding state to use Zustand for state management.

**Current State**:
- Component: src/App.js
- State variables to migrate:
  - hand, setHand
  - handPoints, setHandPoints
  - auction, setAuction
  - nextPlayerIndex, setNextPlayerIndex
  - isAiBidding, setIsAiBidding
  - vulnerability, setVulnerability
  - allHands, setAllHands
  - showHandsThisDeal, setShowHandsThisDeal
  - alwaysShowHands, setAlwaysShowHands
  - selectedScenario, setSelectedScenario
  - scenarioList, setScenarioList
  - initialDeal, setInitialDeal

**Target Store**: biddingStore
**Store Location**: src/stores/biddingStore.js

**MIGRATION STEPS**:
1. Read App.js to identify all bidding-related state and logic
2. Create src/stores/biddingStore.js with Zustand
3. Move state properties to store
4. Create actions:
   - setHand(hand, points)
   - addBid(bidObject)
   - resetAuction(dealData)
   - toggleShowHandsThisDeal()
   - toggleAlwaysShowHands()
   - setScenarios(scenarios)
   - setSelectedScenario(scenario)
5. Update App.js:
   - Remove all useState for bidding state
   - Import and use biddingStore
   - Replace setters with store actions
6. Update tests to mock useBiddingStore

**CONSTRAINTS**:
- Bidding flow must work identically
- AI bidding loop must function the same
- Scenario loading must work the same
- No visual changes

**VERIFICATION**:
1. npm test passes
2. Manual: Deal new hand → works
3. Manual: Load scenario → works
4. Manual: Bid sequence → works
5. Manual: Show hands toggle → works
6. DevTools: useBiddingStore visible

Please proceed with refactoring.
```

---

### Template 4: Fix Bug / Issue

```
Fix the following issue in {COMPONENT_NAME}.

**Issue Description**:
{Detailed description of the bug}

**Current Behavior**:
{What currently happens}

**Expected Behavior**:
{What should happen}

**Steps to Reproduce**:
1. {Step 1}
2. {Step 2}
3. {Step 3}

**Affected Files**:
- {file 1}
- {file 2}

**Debugging Steps**:
1. Read affected files
2. Identify root cause
3. Propose fix
4. Implement fix
5. Add test to prevent regression
6. Verify fix manually

**CONSTRAINTS**:
- Fix must not break existing functionality
- Follow existing code style (Shadcn + Tailwind)
- Add comments explaining the fix
- Add or update tests

Please diagnose and fix the issue.
```

---

### Template 5: Add Feature to Existing Component

```
Add {FEATURE_NAME} to the {COMPONENT_NAME} component.

**Component Location**: {file path}

**Current Functionality**:
{Brief description of what component currently does}

**New Feature**:
{Detailed description of feature to add}

**REQUIREMENTS**:
1. Maintain existing functionality (no breaking changes)
2. Follow Rule of Three for any new UI elements
3. Use Shadcn/ui components if adding UI
4. Add props with TypeScript-style JSDoc
5. Update tests to cover new feature
6. Add accessibility features

**DESIGN**:
{Visual design of new feature}

**BEHAVIOR**:
{How the feature should behave}

**INTEGRATION**:
{How it integrates with existing code}

**TESTS**:
Add tests for:
- New prop handling
- New interaction
- Edge cases

Please implement the feature.
```

**Example Usage**:
```
Add hover explanation tooltip to the BridgeCard component.

**Component Location**: src/components/bridge/bridge-card.jsx

**Current Functionality**:
BridgeCard displays a playing card with rank and suit. It can be clicked and disabled.

**New Feature**:
Add a tooltip that shows on hover, explaining the card (e.g., "Ace of Spades").

**REQUIREMENTS**:
1. Maintain existing click and hover-to-lift functionality
2. Use Shadcn Tooltip component
3. Tooltip should appear above card on hover
4. Tooltip delay: 500ms
5. Add optional prop: showTooltip (default true)
6. Update tests

**DESIGN**:
- Tooltip background: dark gray (bg-gray-900)
- Tooltip text: white, text-sm
- Arrow pointing to card
- Appears 8px above card top

**BEHAVIOR**:
- Hover over card → wait 500ms → tooltip appears
- Move mouse away → tooltip disappears immediately
- If disabled, tooltip shows "Card is disabled"
- Tooltip text format: "{Rank} of {Suit Name}"
  - e.g., "Ace of Spades", "10 of Hearts"

**INTEGRATION**:
- Wrap existing Card JSX with Shadcn TooltipProvider, Tooltip, TooltipTrigger, TooltipContent
- No changes to existing card rendering
- Add suitNameMap for full suit names

**TESTS**:
Add tests for:
1. Tooltip shows correct text for each rank/suit combo
2. Tooltip respects showTooltip prop
3. Tooltip shows "disabled" message when card is disabled
4. Tooltip has correct aria attributes

Please implement the feature.
```

---

## Common Patterns

### Pattern 1: Shadcn Button Variants

```jsx
// Primary action (green)
<Button variant="default" className="bg-success hover:bg-green-600">
  Deal New Hand
</Button>

// Secondary action (outlined)
<Button variant="outline">
  Cancel
</Button>

// Danger action (red)
<Button variant="destructive">
  Delete
</Button>

// Disabled
<Button disabled>
  Loading...
</Button>
```

### Pattern 2: Responsive Spacing

```jsx
// Mobile: gap-4, Desktop: gap-6
<div className="flex gap-4 md:gap-6">
  {/* content */}
</div>

// Mobile: p-4, Desktop: p-6
<div className="p-4 md:p-6">
  {/* content */}
</div>
```

### Pattern 3: Conditional Classes with cn()

```jsx
import { cn } from '@/lib/utils';

<div className={cn(
  "base-classes always-applied",
  isActive && "active-classes",
  isDisabled && "disabled-classes",
  className // Allow override via prop
)}>
  {/* content */}
</div>
```

### Pattern 4: Suit Color Helper

```jsx
// In any component dealing with suits
const getSuitColor = (suit) => {
  return (suit === '♥' || suit === '♦') ? 'text-suit-red' : 'text-suit-black';
};

// Usage
<span className={getSuitColor(suit)}>{suit}</span>
```

### Pattern 5: Zustand Store Pattern

```javascript
import { create } from 'zustand';

export const useMyStore = create((set, get) => ({
  // State
  value: initialValue,

  // Simple action
  setValue: (newValue) => set({ value: newValue }),

  // Action with state dependency
  increment: () => set((state) => ({ value: state.value + 1 })),

  // Action using get()
  complexAction: () => {
    const currentValue = get().value;
    // ... do something with currentValue
    set({ value: newValue });
  },
}));
```

---

## Pre-Implementation Checklist

Before starting any component work, verify:

- [ ] Read [UI_UX_FRAMEWORK.md](./UI_UX_FRAMEWORK.md) for strategic context
- [ ] Check component doesn't already exist in `src/components/`
- [ ] Identify correct Shadcn base component
- [ ] Confirm target file location follows structure
- [ ] Have clear requirements (functionality + design)
- [ ] Know which store to use (if state management needed)

---

## Post-Implementation Checklist

After completing component work, verify:

- [ ] Component uses Shadcn/ui as base (not custom divs)
- [ ] All classes are Tailwind utilities (no inline styles)
- [ ] Follows Rule of Three (typography, colors, spacing)
- [ ] File location matches approved structure
- [ ] Has JSDoc comments for props
- [ ] Has test file with >80% coverage
- [ ] Tests pass: `npm test`
- [ ] Builds without errors: `npm run build`
- [ ] Accessible: keyboard navigation works
- [ ] Accessible: has ARIA labels
- [ ] Responsive: works on mobile (320px) and desktop (1024px)
- [ ] No console errors or warnings

---

## Troubleshooting

### Issue: Tailwind classes not applying
**Solution**: Check `tailwind.config.js` content array includes the file path

### Issue: Shadcn component import error
**Solution**: Ensure `jsconfig.json` has correct path alias for `@`

### Issue: cn() function not working
**Solution**: Import from `@/lib/utils`, verify utils.js exists

### Issue: Zustand store not updating component
**Solution**: Ensure using store hook correctly: `const { value } = useStore()`

### Issue: Build fails with "module not found"
**Solution**: Check import paths, ensure using `@/` alias consistently

---

## Quick Reference: File Locations

```
Frontend Structure:
src/
├── components/
│   ├── ui/              # Shadcn components (button.jsx, card.jsx, etc.)
│   ├── bridge/          # Bridge-specific (bridge-card.jsx, bidding-box.jsx)
│   └── play/            # Play phase (play-table.jsx, contract-header.jsx)
├── stores/
│   ├── biddingStore.js  # Bidding state
│   ├── playStore.js     # Play phase state
│   └── uiStore.js       # UI state (modals, errors)
├── lib/
│   └── utils.js         # Utility functions (cn, etc.)
├── App.js               # Main app component
└── index.css            # Global styles + Tailwind imports
```

---

## Examples from Codebase

### Example 1: BridgeCard (Target Implementation)
**File**: `src/components/bridge/bridge-card.jsx`
**Uses**: Shadcn Card, Tailwind utilities, cn(), Rule of Three

### Example 2: BiddingBox (Target Implementation)
**File**: `src/components/bridge/bidding-box.jsx`
**Uses**: Shadcn Button, Tailwind flex/gap, legal bid logic

### Example 3: ReviewModal (Target Implementation)
**File**: `src/components/bridge/review-modal.jsx`
**Uses**: Shadcn Dialog, Textarea, Button

---

**Last Updated**: 2025-10-13
**Version**: 1.0
**Status**: Ready for Use
