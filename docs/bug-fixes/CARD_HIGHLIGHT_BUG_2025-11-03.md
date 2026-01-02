# Card Highlight Bug Fix - 2025-11-03

**Last Updated:** 2025-11-03

**Status:** ✅ Fixed
**Severity:** High (Production Bug)
**Affects:** Card play phase - dummy/declarer hands
**Fixed In:** Commit fixing React key collision

## Summary

Cards in North position (dummy/declarer hand) were appearing highlighted and raised without user interaction. The bug was caused by React key collisions causing component state to be reused across different hands.

## Symptoms

**User Report:**
- Queen of Diamonds appeared highlighted/raised when it was North's turn
- Card remained visually highlighted even though it was illegal to play
- Next hand: 9 of Diamonds appeared highlighted/raised
- Pattern: Always the **second card in the last suit group (diamonds)**

**Visual Behavior:**
- Card appeared raised above others (transform: translateY)
- Green glow/border visible
- Appeared as if card was in `:active` CSS state
- Clicking the card did nothing (correctly disabled)
- Clicking legal cards worked correctly

## Root Cause Analysis

### Investigation Steps

1. **Initial Hypothesis:** Touch event bug causing stuck `:active` state
   - Ruled out: Touch events were properly handled

2. **Second Hypothesis:** CSS hover/focus state stuck
   - Ruled out: No focus management issues found

3. **Third Hypothesis:** Follow-suit validation missing
   - Partially correct: Validation was missing, but didn't explain specific card highlight

4. **Actual Cause:** React key collision

### The Bug

**Problem:** React keys used `suit-index` format:
```javascript
key={`${suit}-${index}`}  // e.g., "♦-0", "♦-1", "♦-2"
```

**Impact:**
- Same key (`♦-1`) used for second diamond card across ALL hands
- React's virtual DOM reconciliation reused component for matching keys
- Component state (including `:active` pseudo-class) persisted across hands
- Whichever card was at `♦-1` inherited the previous hand's visual state

**Why Second Diamond Specifically:**
- Diamonds are the last suit in NT suit order (♠, ♥, ♣, ♦)
- Index `1` is the second card in each suit group
- This specific key was somehow getting a stuck `:active` state
- State persisted across hand transitions due to key reuse

## The Fix

### 1. React Key Generation (Primary Fix)

**File:** `frontend/src/PlayComponents.js`

**Changed from:**
```javascript
key={`${suit}-${index}`}
```

**Changed to:**
```javascript
const cardKey = `${position}-${card.rank}-${card.suit}`;
// Examples: "north-Q-♦", "north-9-♦", "south-A-♠"
```

**Impact:**
- Keys now unique across ALL hands (not just within one hand)
- React creates new component instances for new cards
- No state reuse between different hands
- Applied to all 4 positions (North, East, South, West)

### 2. Touch Event Handling (Defense-in-Depth)

**Files:**
- `frontend/src/components/play/PlayableCard.jsx`
- `frontend/src/components/play/VerticalPlayableCard.jsx`

**Changed from:**
```javascript
onTouchEnd={!disabled ? (e) => {
  e.preventDefault();
  onClick?.();
} : undefined}
```

**Changed to:**
```javascript
onTouchEnd={(e) => {
  // CRITICAL: Always handle touch events to prevent stuck :active state
  e.preventDefault();
  if (!disabled && onClick) {
    onClick();
  }
}}
```

**Impact:**
- Touch events now properly complete even on disabled cards
- Prevents `:active` pseudo-class from getting stuck
- Secondary safeguard against visual state bugs

### 3. CSS Safeguard (Defense-in-Depth)

**File:** `frontend/src/PlayComponents.css`

**Added:**
```css
/* CRITICAL: Prevent :active state on disabled cards */
.playable-card:not(.clickable):active {
  transform: none !important;
  box-shadow: none !important;
  animation: none !important;
}
```

**Impact:**
- Explicitly prevents visual `:active` state on disabled cards
- Failsafe if touch events or React keys have issues

### 4. Follow-Suit Validation (Feature Addition)

**File:** `frontend/src/PlayComponents.js`

**Added:**
```javascript
function isCardLegalToPlay(card, hand, currentTrick) {
  // Implements bridge follow-suit rules
  // - Must follow led suit if able
  // - Can discard any card if void in led suit
}
```

**Impact:**
- Only legal cards are now enabled (green glow)
- Illegal cards are disabled and not clickable
- Proper bridge rules enforcement in frontend

## Testing

### Verification Steps

1. **Scenario 1:** Q♦ highlight (original bug report)
   - ✅ Q♦ no longer highlighted when hearts led
   - ✅ Only 8♥ (legal card) has green glow
   - ✅ Q♦ is disabled and not clickable

2. **Scenario 2:** 9♦ highlight (second occurrence)
   - ✅ 9♦ no longer highlighted when clubs led
   - ✅ North has no clubs, so all cards should be legal (discard)
   - ✅ All cards correctly enabled when void in led suit

3. **Multiple Hands:** Play 10+ hands
   - ✅ No cards appear pre-highlighted
   - ✅ Follow-suit validation works consistently
   - ✅ Touch events complete properly

## Prevention

### Code Review Checklist

When rendering lists of React components:

- [ ] Keys are **globally unique** (not just unique within parent)
- [ ] Keys include **identifiable data** (rank+suit, not just index)
- [ ] Keys **don't reuse** across different data sets
- [ ] Touch events are **always handled** (even on disabled elements)
- [ ] CSS pseudo-classes can't get **stuck** on disabled elements

### Best Practices

**DO:**
```javascript
// ✅ Unique key using card identity
key={`${position}-${card.rank}-${card.suit}`}

// ✅ Always handle touch events
onTouchEnd={(e) => {
  e.preventDefault();
  if (!disabled) onClick();
}}
```

**DON'T:**
```javascript
// ❌ Index-based keys can collide
key={index}

// ❌ Partial identity keys can collide
key={`${suit}-${index}`}

// ❌ Conditional event handlers leave pseudo-classes stuck
onTouchEnd={!disabled ? handler : undefined}
```

## Related Issues

- Follow-suit validation was missing (now implemented)
- Touch event handling on disabled cards was incomplete (now fixed)
- CSS `:active` state management (now safeguarded)

## References

- User report: Screenshot showing Q♦ raised when hearts led
- Second report: Screenshot showing 9♦ raised when clubs led
- React documentation: [Lists and Keys](https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key)
- CSS pseudo-classes: [:active](https://developer.mozilla.org/en-US/docs/Web/CSS/:active)
