# Glossary Integration Protocol

## Overview

The Bridge Glossary system provides contextual definitions for bridge terminology throughout the application. This document describes how to integrate glossary features into new or existing components.

## Components

### 1. TermHighlight
Auto-detects and highlights bridge terms in text, making them interactive.

```jsx
import { TermHighlight } from '../glossary';

// Basic usage - wrap any text content
<TermHighlight text="Count your HCP and check for a balanced hand." />

// With glossary drawer integration (opens drawer to specific term)
<TermHighlight
  text="Use Stayman to find a 4-4 major fit."
  onOpenGlossary={(termId) => handleOpenGlossary(termId)}
/>
```

### 2. GlossaryDrawer
Slide-in panel for browsing/searching all glossary terms.

```jsx
import { GlossaryDrawer } from '../glossary';

// Basic usage
<GlossaryDrawer
  isOpen={showGlossary}
  onClose={() => setShowGlossary(false)}
/>

// Open to a specific term (user clicked from TermHighlight)
<GlossaryDrawer
  isOpen={showGlossary}
  onClose={handleCloseGlossary}
  initialTermId={selectedTermId}  // Auto-scrolls to this term
/>
```

### 3. TermTooltip
Individual term tooltip for specific terms (used by TermHighlight internally).

```jsx
import { TermTooltip } from '../glossary';

<TermTooltip term="hcp">HCP</TermTooltip>
```

## Integration Checklist

When adding educational content to the application, follow this checklist:

### Required Integration Points

Any component displaying these types of content MUST use `TermHighlight`:

- [ ] **Skill/lesson explanations** - Educational text describing bridge concepts
- [ ] **Feedback messages** - Explanations of correct/incorrect answers
- [ ] **Convention help** - How conventions work, when to use them
- [ ] **Hints and tips** - Practice tips, helpful hints
- [ ] **Error explanations** - Why a bid or play was suboptimal

### Files Currently Integrated

| Component | File | Content Types |
|-----------|------|---------------|
| SkillIntro | `components/learning/SkillIntro.js` | Skill descriptions, practice tips |
| SkillPractice | `components/learning/SkillPractice.js` | Feedback text, explanations |
| ConventionHelpModal | `components/bridge/ConventionHelpModal.jsx` | Convention background, how-to |
| RecentDecisionsCard | `components/learning/RecentDecisionsCard.js` | Key concepts, hints |

### Files That May Need Integration

| Component | File | Status |
|-----------|------|--------|
| LearningDashboard | `components/learning/LearningDashboard.js` | Consider for growth recommendations |
| ModeSelector | `components/ModeSelector.jsx` | Consider for mode descriptions |
| AIDifficultySelector | `components/AIDifficultySelector.jsx` | Consider for level descriptions |

## Adding New Terms to the Glossary

### 1. Add to glossary data file

Edit `frontend/src/data/bridgeGlossary.js`:

```javascript
{
  id: 'your_term_id',           // Unique identifier (snake_case)
  term: 'Your Term',            // Display name
  category: 'playTerms',        // Category ID (see CATEGORIES)
  difficulty: 'intermediate',   // beginner, intermediate, advanced
  definition: 'Clear, concise definition for new players.',
  example: 'Example showing term in context.',
  relatedTerms: ['related_term_1', 'related_term_2'],  // Term IDs
}
```

### 2. Add detection pattern (if needed)

Edit `frontend/src/components/glossary/TermTooltip.js`:

```javascript
// In the detectableTerms array, add:

// For multi-word terms (add near the top)
{ pattern: /\byour multi-word term\b/gi, termId: 'your_term_id' },

// For single-word terms (add alphabetically)
{ pattern: /\byourterm\b/gi, termId: 'your_term_id' },
```

**Pattern Guidelines:**
- Use `\b` for word boundaries
- Use `gi` flags (global, case-insensitive)
- Handle plurals: `\bterms?\b` matches "term" and "terms"
- Handle variants: `\bhold[- ]?up\b` matches "holdup", "hold-up", "hold up"
- Multi-word patterns should be listed BEFORE single-word patterns

### 3. Test the integration

1. Restart the development server
2. Navigate to a page with the term
3. Verify the term is highlighted
4. Click the term and verify tooltip appears
5. Click "See more in glossary" and verify drawer opens to the term

## Categories

Available categories in `CATEGORIES`:
- `basicCardTerms` - Cards, deck, suits, ranks
- `handEvaluation` - HCP, distribution, shape
- `biddingTerms` - Auction, bids, responses
- `suitContractTerms` - Contracts, game, slam
- `conventions` - Stayman, Jacoby, Blackwood, etc.
- `playTerms` - Finesse, lead, trick, ruff
- `strategyTerms` - Counting, inference, signals
- `scoringTerms` - Points, bonus, penalties

## Difficulty Levels

- `beginner` - Essential terms every new player needs
- `intermediate` - Terms for developing players
- `advanced` - Terms for experienced players

## Code Review Checklist

When reviewing code changes:

1. **New educational text added?**
   - Is it wrapped with `<TermHighlight text={...} />`?

2. **New bridge terms introduced?**
   - Are they added to `bridgeGlossary.js`?
   - Are detection patterns added to `TermTooltip.js`?

3. **Feedback or explanation messages?**
   - Use `<TermHighlight text={message} />` instead of `{message}`

## Best Practices

1. **Keep definitions beginner-friendly** - Assume the reader is new to bridge
2. **Include examples** - Show the term in a real bridge context
3. **Link related terms** - Help users discover connected concepts
4. **Test on mobile** - Tooltips use tap instead of hover on touch devices
5. **Don't over-highlight** - Common English words like "game" are highlighted; be judicious

## Troubleshooting

### Term not being highlighted
1. Check if term exists in `bridgeGlossary.js`
2. Check if pattern exists in `detectableTerms` array
3. Verify pattern regex is correct (test with `console.log(text.match(pattern))`)
4. Check pattern order (specific patterns should come before general ones)

### Tooltip not appearing
1. Verify `getTermById(termId)` returns the term data
2. Check browser console for errors
3. Verify CSS is loaded (`TermTooltip.css`)

### Glossary drawer not opening to term
1. Verify `initialTermId` is passed correctly
2. Check that term ID matches exactly (case-sensitive)
3. Verify `termRefs.current[termId]` is being set
