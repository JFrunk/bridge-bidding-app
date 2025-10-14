# Changelog

All notable changes to the Bridge Bidding Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - refactor/shadcn-tailwind-migration branch

### Added
- **UI/UX Framework Migration**: Migrated to Shadcn/ui + Tailwind CSS with "Rule of Three" design system
- **Card Overlap**: Cards now overlap showing 35% visible (like real hand-holding)
  - Bidding phase: South's hand and "Show All Hands" display
  - Play phase: All player hands
  - Responsive: -45px desktop, -33px mobile, -25px extra small
- **Scoring Display**:
  - Shows in ContractHeader when hand completes (13 tricks)
  - Color-coded: green (positive), red (negative)
  - Displays result text (e.g., "Made 1", "Down 2")
- **Deal New Hand Button**: Primary action in score modal to start new hand immediately
- **Show All Hands Button**: Available in gameplay after hand completion for review
- **Learning Dashboard**: Progress tracking with analytics and mistake patterns
  - Access via "📊 My Progress" button
  - Tracks bidding mistakes by category
  - Provides practice recommendations
  - Celebrates milestones
- **Contract Header Redesign**:
  - 13-block progress bar with visual goal marker
  - Trick counts below Won/Remaining/Lost labels
  - Goal indicator (↓ 9) above progress bar
  - Bidding table with borders (N/E/S/W columns)

### Fixed
- **AI Play Bug**: AI no longer plays user-controlled cards after trick wins
  - Added check after trick clear to stop AI if next player is user-controlled
  - Prevents AI from playing South or dummy (when South is declarer)
- **Dummy Visibility**: North's dummy hand now appears after first card is played
  - Backend already had correct logic
  - Cards display ABOVE "North" label (standard bridge convention)
- **Trick Display Position**: Centered between all four players in compass layout
- **Standard Bridge Layout**: West on left, East on right, North top, South bottom

### Changed
- **Component Architecture**: Migrated to modern component structure
  - `components/bridge/`: BridgeCard, BiddingBox, ReviewModal, ConventionHelpModal
  - `components/play/`: ContractHeader, CurrentTrickDisplay, PlayableCard, ScoreModal, TurnIndicator
  - `components/learning/`: LearningDashboard, CelebrationNotification
  - `components/ui/`: Shadcn UI primitives (button, dialog, card, etc.)
- **Design System**: Implemented "Rule of Three"
  - Typography: 3 sizes (16px, 20px, 32px)
  - Colors: 3 core + suit colors
  - Spacing: 3 levels (1rem, 1.5rem, 3rem)
  - Senior-friendly: High contrast (WCAG AA), large touch targets (40px+)

### Technical Improvements
- **CSS Organization**: Separated concerns
  - `App.css`: Global styles and bidding phase
  - `PlayComponents.css`: Play phase specific styles
  - Component-specific CSS: TurnIndicator.css, LearningDashboard.css, etc.
- **State Management**: Proper React patterns
  - Clear separation of bidding vs play state
  - AI loop management with proper cleanup
  - Modal state management

## [Previous Version] - main branch

### Features
- Bridge bidding system with SAYC conventions
- AI opponents with bidding logic
- Card play engine with trick-taking logic
- AI Review system with Claude integration
- Convention help system
- Scenario loading and replay functionality
- Hand analysis with HCP and distribution points

---

## Migration Guide

### For Developers

**New Dependencies:**
```bash
# Frontend
npm install @radix-ui/react-dialog
npm install class-variance-authority
npm install clsx tailwind-merge

# Tailwind already installed (v3.4.0)
```

**Component Imports Changed:**
```javascript
// Old
import { PlayableCard } from './PlayComponents';

// New
import { PlayableCard } from './components/play/PlayableCard';
```

**CSS Classes:**
- Card overlap now uses `.suit-group > div` for BridgeCard components
- Play phase uses `.playable-card` class for PlayableCard components
- Both support -45px (35% visible) overlap

### For Users

**What Changed:**
- Cards now overlap to save horizontal space
- Clearer visual hierarchy with larger fonts
- Better color contrast for readability
- New progress bar shows trick progress visually
- Score displays automatically after hand completion

**New Features:**
- Click "📊 My Progress" to see your learning analytics
- Click "Show All Hands" after hand completion to review
- Click "Deal New Hand" in score modal to start new hand quickly

---

## Deployment Checklist

- [ ] All tests passing (`pytest backend/tests/`)
- [ ] Frontend builds without errors (`npm run build`)
- [ ] No console errors in browser
- [ ] All features tested manually:
  - [ ] Card overlap in bidding
  - [ ] Card overlap in play
  - [ ] AI doesn't play user cards
  - [ ] Dummy appears after first card
  - [ ] Scoring displays correctly
  - [ ] Deal New Hand works
  - [ ] Show All Hands works
  - [ ] Learning Dashboard loads
- [ ] Performance acceptable (< 3s initial load)
- [ ] Mobile responsive (test on 320px, 768px, 1024px)
- [ ] Accessibility: keyboard navigation works
- [ ] Backend API endpoints responding
- [ ] Database migrations applied (if any)

---

## Known Issues

### Minor
- ESLint warnings for unused variables (non-breaking)
- React useEffect dependency warnings (non-breaking)
- Deprecation warning for simple_play_ai import path

### Future Enhancements
- Add unit tests for new components
- Add Storybook for component documentation
- Implement end-to-end tests with Playwright
- Add error boundary components
- Implement loading states for async operations
- Add animation for card play
- Implement undo/redo for bidding
- Add sound effects (optional)
- Dark mode support
