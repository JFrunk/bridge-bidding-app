# Frontend UI/UX

**Specialist Area:** React application, user interface, visual presentation

## Scope

This area covers the user-facing React application. You are responsible for:

- **Main app:** `App.js` orchestration, state management
- **Bidding UI:** BiddingBox, BiddingTable, bid display
- **Play UI:** PlayTable, trick display, card interactions
- **Cards:** BridgeCard, VerticalCard, LibraryCard (SVG)
- **Session:** Chicago rotation, vulnerability display
- **Styling:** Tailwind CSS, responsive design

## Key Files

```
frontend/src/
├── App.js                     # Main orchestrator (~800 lines)
├── App.css                    # Global styles
├── PlayComponents.js          # Play phase components
├── components/
│   ├── bridge/
│   │   ├── BiddingBox.jsx     # Interactive bidding interface
│   │   ├── BiddingTable.jsx   # Auction display (N/E/S/W columns)
│   │   ├── BridgeCard.jsx     # Standard card display
│   │   ├── VerticalCard.jsx   # Rotated cards (East/West)
│   │   ├── LibraryCard.jsx    # SVG cards (@letele/playing-cards)
│   │   ├── ReviewModal.jsx    # Bid review popup
│   │   └── ConventionHelpModal.jsx
│   ├── play/
│   │   ├── PlayableCard.jsx   # Interactive card in play
│   │   ├── VerticalPlayableCard.jsx
│   │   ├── PlayTable.jsx      # Main play interface
│   │   ├── CurrentTrickDisplay.jsx
│   │   ├── ContractHeader.jsx
│   │   ├── ScoreModal.jsx
│   │   └── ScoreBreakdown.jsx
│   ├── session/
│   │   └── SessionScorePanel.jsx
│   ├── auth/
│   │   └── SimpleLogin.jsx
│   └── ui/                    # Shadcn components
├── contexts/
│   └── AuthContext.jsx        # Authentication state
├── services/
│   └── api.js                 # Backend communication
└── utils/
    └── sessionHelper.js       # Session utilities
```

## Architecture

### Component Hierarchy
```
App.js
├── AuthProvider (context)
├── SimpleLogin (if not authenticated)
└── Main App
    ├── Header (dealer, vulnerability)
    ├── PlayerHand (North)
    ├── PlayerHand (East - vertical)
    ├── PlayerHand (West - vertical)
    ├── PlayerHand (South - user)
    ├── BiddingTable + BiddingBox (bidding phase)
    ├── PlayTable (play phase)
    ├── SessionScorePanel
    └── LearningDashboard (modal)
```

### State Management
```javascript
// Key state in App.js
const [hand, setHand] = useState([]);           // User's 13 cards
const [auction, setAuction] = useState([]);      // Bid history
const [phase, setPhase] = useState('bidding');   // 'bidding' | 'play'
const [dealer, setDealer] = useState('North');   // Current dealer
const [vulnerability, setVulnerability] = useState('None');
```

### API Communication
All backend calls go through `services/api.js`:
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Example call with session headers
fetch(`${API_URL}/api/deal-hands`, {
  headers: getSessionHeaders()
})
```

## Design Standards

**Reference:** `.claude/UI_STANDARDS.md` (single source of truth)

### Key Rules
- **No Tailwind for layout.** Use CSS with `clamp()`, `vmin`, and `max-width` media queries.
- **South Hand + Bidding Box are sacrosanct.** They must never be obscured or pushed off-screen.
- **All CSS variables defined in `index.css` only.** Do not redefine `:root` in component CSS.

### Colors (CSS Variables Only)
```css
/* Clubhouse theme — NEVER hardcode colors */
--table-green, --cream, --gold, --charcoal
--color-success, --color-danger, --color-info
--text-primary, --text-secondary
```

### Responsive Breakpoints (max-width, desktop-first)
```
1024px - Small desktop (coach panel stacks)
768px  - Tablet (reduced padding, stacked layouts)
600px  - Compact tablet (bid actions stack)
480px  - Mobile (minimal padding, bottom-sheet modals)
360px  - Small phone (tightest squeeze)
```

### Card Display
- **North/South:** Horizontal layout, vmin-based overlap via `--card-overlap-horizontal`
- **East/West:** Vertical (rotated 90°), overlap controlled by inline styles
- **Card sizing:** `clamp()` + `vmin` — never set fixed pixel card sizes

## Quality Requirements

### Before Committing
```bash
# Unit tests
npm test

# E2E tests (REQUIRED for UI changes)
npm run test:e2e

# Interactive debugging
npm run test:e2e:ui
```

### UI Checklist
- [ ] Uses CSS variables (no hardcoded colors)
- [ ] Responsive at 375px, 768px, 1280px
- [ ] Keyboard navigation works
- [ ] ARIA labels on interactive elements
- [ ] Touch targets ≥ 44px on mobile
- [ ] Loading states implemented
- [ ] Error messages are user-friendly

## Common Tasks

### Fix Card Display Issue
1. Identify component: `BridgeCard`, `VerticalCard`, or `LibraryCard`
2. Check CSS for positioning/overlap
3. Test at all breakpoints
4. Run E2E tests

### Fix Bidding Box Bug
1. Check `BiddingBox.jsx` for legality logic
2. Verify state updates in `App.js`
3. Test keyboard navigation
4. Add E2E test for scenario

### Add New Modal/Dialog
1. Use Shadcn `Dialog` component from `components/ui/`
2. Follow existing modal patterns (ReviewModal, ScoreModal)
3. Ensure keyboard dismissible (Escape key)
4. Test at mobile breakpoint

## Testing

```bash
# Jest unit tests
npm test
npm test -- --coverage

# Playwright E2E
npm run test:e2e              # Headless
npm run test:e2e:ui           # Interactive (RECOMMENDED)
npm run test:e2e:headed       # Visible browser
npm run test:e2e:codegen      # Record tests
npm run test:e2e:report       # View last report
```

### E2E Test Location
```
frontend/e2e/tests/
├── verification.spec.js      # Environment checks
├── app-smoke-test.spec.js    # Basic functionality
└── *.spec.js                 # Feature tests
```

## Dependencies

- **React 18.3** - UI framework
- **Tailwind CSS 3.4** - Styling
- **@letele/playing-cards** - Card graphics
- **Playwright 1.56+** - E2E testing
- **Shadcn/ui** - Component library

## Gotchas

- BiddingBox has client-side legality check - must match backend logic
- East/West cards use `transform: rotate(90deg)` - affects click targets
- Dashboard uses `key={Date.now()}` for forced remount on reopen
- Session headers required for all API calls (multi-user isolation)
- Card overlap values differ: horizontal (standard) vs vertical (65%)

## Reference Documents

- **Design Standards:** `.claude/UI_STANDARDS.md` - UI layout, tokens, zone architecture (single source of truth)
- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Online single-player control rules
