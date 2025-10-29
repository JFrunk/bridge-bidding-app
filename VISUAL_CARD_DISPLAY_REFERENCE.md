# Visual Card Display Reference

## Current Implementation Status: ✅ COMPLETE

The external SVG card library (`@letele/playing-cards`) is now integrated and deployed. The dev server is running at http://localhost:3000.

## Expected Display: Vertical Hands (East/West)

### 80% Overlap Visualization

```
┌──────────┐
│    ♠A    │  ← Card 1: Top 80px clipped by container (only 20px visible)
│          │
│          │
│          │
└──────────┘
┌──────────┐
│    ♠K    │  ← Card 2: Overlaps Card 1 by 80px (marginTop: -80px)
│          │
│          │
│          │
└──────────┘
┌──────────┐
│    ♠Q    │  ← Card 3: Overlaps Card 2 by 80px
│          │
│          │
│          │
└──────────┘
┌──────────┐
│    ♠J    │  ← Card 4: Overlaps Card 3 by 80px
│          │
│          │
│          │
└──────────┘
┌──────────┐
│    ♥A    │  ← Card 5: NO GAP between suits, continues overlap
│          │
│          │
│          │
└──────────┘
┌──────────┐
│    ♥K    │  ← Card 6: Overlaps Card 5 by 80px
│          │
│          │
│          │
└──────────┘
     ...
┌──────────┐
│    ♣2    │  ← Last card: Fully visible (100px height)
│          │
│          │
│          │
│          │
└──────────┘
```

### Actual Rendering (With 80% Overlap)

```
Container: max-height 350px, overflow hidden
┏━━━━━━━━━━┓
┃ [Spades] ┃ ← Only bottom 20px visible
┃ [Spades] ┃ ← Only bottom 20px visible
┃ [Spades] ┃ ← Only bottom 20px visible
┃ [Spades] ┃ ← Only bottom 20px visible
┃ [Hearts] ┃ ← NO gap, continues overlap
┃ [Hearts] ┃ ← Only bottom 20px visible
┃ [Hearts] ┃ ← Only bottom 20px visible
┃[Diamonds]┃ ← NO gap, continues overlap
┃[Diamonds]┃ ← Only bottom 20px visible
┃ [Clubs]  ┃ ← NO gap, continues overlap
┃ [Clubs]  ┃ ← Only bottom 20px visible
┃ [Clubs]  ┃ ← Last card FULLY visible (100px)
┃          ┃
┃          ┃
┃          ┃
┗━━━━━━━━━━┛
```

## Technical Specifications

### Card Dimensions
- **Width**: 70px
- **Height**: 100px
- **Aspect Ratio**: 5:7 (standard playing card)

### Overlap Calculation
- **Card Height**: 100px
- **Visible Portion**: 20px (20%)
- **Hidden Portion**: 80px (80%)
- **Margin**: -80px (pulls card up to overlap)

### Inline Style Application
```javascript
// First card (index 0): No margin
const inlineStyle = absoluteIndex === 0 ? {} : { marginTop: '-80px' };

// Results in:
Card 0:  style={{}}                    // No margin, container clips top
Card 1:  style={{marginTop: '-80px'}}  // Overlaps Card 0
Card 2:  style={{marginTop: '-80px'}}  // Overlaps Card 1
Card 3:  style={{marginTop: '-80px'}}  // Overlaps Card 2
...
Card N:  style={{marginTop: '-80px'}}  // Last card, fully visible
```

### Container Styling
```css
.player-east .hand-display,
.player-west .hand-display {
  max-height: 350px;    /* Clips first card's top */
  overflow: hidden;     /* Hides clipped portions */
  display: flex;
  flex-direction: column;
  align-items: center;
}
```

## Horizontal Hands (North/South) - Already Working

### 35% Overlap (Unchanged)

```
┌───┐┌───┐┌───┐┌───┐  ┌───┐┌───┐┌───┐  ┌───┐┌───┐  ┌───┐┌───┐
│ ♠ ││ ♠ ││ ♠ ││ ♠ │  │ ♥ ││ ♥ ││ ♥ │  │ ♦ ││ ♦ │  │ ♣ ││ ♣ │
│ A ││ K ││ Q ││ J │  │ A ││ K ││ Q │  │ A ││ K │  │ A ││ K │
└───┘└───┘└───┘└───┘  └───┘└───┘└───┘  └───┘└───┘  └───┘└───┘
 ←35%→                  ←35%→              ←35%→        ←35%→
  overlap               overlap            overlap      overlap
```

- First card in each suit: Same 35% overlap (NO extra gap)
- Continues to use BridgeCard component (CSS-based)
- No changes needed - already working correctly

## Card Library Format

### Internal Format (Your App)
```javascript
{rank: 'A', suit: '♠'}
{rank: 'T', suit: '♥'}  // T = 10
{rank: 'K', suit: '♦'}
{rank: '2', suit: '♣'}
```

### Library Format (@letele/playing-cards)
```javascript
deck['Sa']  // Ace of Spades
deck['Ht']  // 10 of Hearts
deck['Dk']  // King of Diamonds
deck['C2']  // 2 of Clubs
```

### Mapping Logic
```javascript
// Suits
'♠' → 'S' (Spades)
'♥' → 'H' (Hearts)
'♦' → 'D' (Diamonds)
'♣' → 'C' (Clubs)

// Ranks
'A' → 'a' (Ace)
'2'-'9' → '2'-'9' (Numbers)
'T' → 't' (Ten)
'J' → 'j' (Jack)
'Q' → 'q' (Queen)
'K' → 'k' (King)
```

## Testing Checklist

When you refresh the browser, verify:

### East/West Hands (Vertical)
- [ ] Cards display as SVG images (not CSS-drawn cards)
- [ ] First card shows only bottom 20px (top 80px clipped)
- [ ] Each subsequent card overlaps previous by 80px
- [ ] Exactly 20px visible per card (except last)
- [ ] Last card in hand is fully visible (100px)
- [ ] **NO gaps between different suits**
- [ ] Cards are centered in vertical column
- [ ] Hover effects work (if cards are clickable)

### North/South Hands (Horizontal)
- [ ] Cards display horizontally (should NOT change)
- [ ] 35% overlap between cards
- [ ] NO extra gap for first card in each suit
- [ ] All suits aligned in single row

### During Play Phase
- [ ] Cards can be played (clicked)
- [ ] Played cards are removed
- [ ] Remaining cards compress toward center
- [ ] Display remains consistent

## Browser DevTools Inspection

Open browser DevTools (F12) and inspect a vertical card:

### Expected HTML Structure
```html
<div class="suit-group">
  <div class="library-card" style="width: 70px; height: 100px; position: relative;">
    <svg style="height: 100%; width: 100%; cursor: pointer; transition: transform 0.2s;">
      <!-- SVG card content -->
    </svg>
  </div>
  <div class="library-card" style="width: 70px; height: 100px; position: relative; margin-top: -80px;">
    <svg style="height: 100%; width: 100%; cursor: pointer; transition: transform 0.2s;">
      <!-- SVG card content -->
    </svg>
  </div>
  <!-- More cards... -->
</div>
```

### Expected Computed Styles
```
Card 1:
  margin-top: 0px (or not set)
  height: 100px
  width: 70px

Card 2:
  margin-top: -80px  ← CRITICAL: Must be -80px
  height: 100px
  width: 70px

Card 3:
  margin-top: -80px  ← CRITICAL: Must be -80px
  height: 100px
  width: 70px
```

## Troubleshooting

### If Cards Still Have Gaps

1. **Check inline styles applied**:
   - Open DevTools → Elements tab
   - Inspect card divs
   - Verify `style="...margin-top: -80px..."` is present

2. **Check for CSS overrides**:
   - Look for any CSS rules with `margin-top: 0 !important`
   - Check for `margin` shorthand that might override inline styles

3. **Check container overflow**:
   - Verify `.hand-display` has `overflow: hidden`
   - Check that container clips the top of first card

4. **Browser cache**:
   - Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+F5 (Windows)
   - Clear browser cache if needed

### If Cards Don't Appear at All

1. **Check console for errors**:
   - Open DevTools → Console tab
   - Look for "Card not found" errors
   - Verify card mapping is correct

2. **Check LibraryCard import**:
   - Verify `import { LibraryCard } from './components/bridge/LibraryCard'`
   - Check that file exists at correct path

3. **Check library installation**:
   - Run: `npm list @letele/playing-cards`
   - Should show installed version

## Success Criteria

✅ **Visual**: Vertical cards display with clean 20px strips, no gaps
✅ **First Card**: Top 80px clipped, only 20px visible
✅ **Last Card**: Fully visible (100px height)
✅ **Suits**: Continuous overlap, no breaks between suits
✅ **Consistency**: All cards except last show exactly 20px
✅ **Performance**: Smooth rendering, no lag
✅ **Interactivity**: Click/hover works correctly

## Implementation Files

- [LibraryCard.jsx](frontend/src/components/bridge/LibraryCard.jsx:1-88) - Wrapper component
- [App.js:28-100](frontend/src/App.js#L28-L100) - PlayerHand rendering
- [App.css:475-487](frontend/src/App.css#L475-L487) - Container styles
- [EXTERNAL_LIBRARY_IMPLEMENTATION_COMPLETE.md](EXTERNAL_LIBRARY_IMPLEMENTATION_COMPLETE.md) - Full documentation

## Ready to Test!

The implementation is complete and the dev server is running. Simply refresh your browser at http://localhost:3000 to see the new SVG card display with proper 80% overlap.
