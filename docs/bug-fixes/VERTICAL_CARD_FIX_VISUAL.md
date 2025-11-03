# Vertical Card Display - CORRECT Implementation

## Requirements (User Specified)

1. **80% overlap** on ALL cards (except the last/bottom card)
2. **Last card shows FULLY** (100% visible)
3. **NO exceptions** - same overlap regardless of suit or rank
4. **Consistent** - first card of each suit gets same overlap as other cards

## Math

- Card height: **100px**
- 80% overlap = show only **20px** of each card
- Margin-top needed: **-80px**

## Visual Representation

```
┌──────────┐
│ K♠       │ ← Card 1 (100px visible - first card, no overlap above)
│          │
│    ♠     │
│          │
│       ♠K │
└──────────┘
     ↓ -80px (80% overlap)
┌──────────┐
│ 10♠      │ ← Card 2 (20px visible - rank + suit)
├══════════┤ ← Overlap line
│ 4♠       │ ← Card 3 (20px visible)
├══════════┤
│ 2♠       │ ← Card 4 (20px visible) [END OF SPADES]
├══════════┤
│ Q♥       │ ← Card 5 (20px visible) [START OF HEARTS - NO GAP!]
├══════════┤
│ 9♥       │ ← Card 6 (20px visible)
├══════════┤
│ 7♥       │ ← Card 7 (20px visible)
├══════════┤
│ 6♥       │ ← Card 8 (20px visible)
├══════════┤
    ...
├══════════┤
│ 4♦       │ ← Card 13 (LAST CARD - 100px visible, FULL)
│          │
│    ♦     │
│          │
│       ♦4 │
└──────────┘
```

## CSS Implementation

### Key Changes:

1. **margin-top: -80px** on all cards (except first)
2. **NO special cases** for suit boundaries
3. **Remove max-height/overflow** to let last card show fully

### CSS Rules:

```css
/* All vertical cards get 80% overlap */
.player-east .suit-group > div,
.player-west .suit-group > div {
  margin-top: -80px; /* 80% overlap - show 20px */
}

/* First card only - no overlap */
.player-east .hand-display .suit-group:first-child > div:first-child,
.player-west .hand-display .suit-group:first-child > div:first-child {
  margin-top: 0; /* First card fully visible */
}

/* NO special rules for suit boundaries - continuous overlap */
```

## Expected Result

### Visual Height Calculation:
- **First card**: 100px (full)
- **Cards 2-12**: 20px each visible = 12 × 20px = 240px
- **Last card**: 100px (full)
- **Total**: 100 + 240 + 100 = **440px**

### User Experience:
✅ Consistent 20px visible per card (rank + suit clearly readable)
✅ No gaps between suits
✅ Last card fully visible
✅ Compact vertical display
✅ Easy to count cards at a glance

## Before vs After

### BEFORE (Current - Broken):
- Irregular overlap
- Gaps between suits
- Cards look like thin strips due to overflow clipping
- Inconsistent spacing

### AFTER (Fixed):
- Perfect 80% overlap (20px visible) on all cards except last
- Smooth continuous flow across all suits
- Last card shows fully for visual anchor
- Professional bridge interface appearance
