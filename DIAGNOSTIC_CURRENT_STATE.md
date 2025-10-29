# Diagnostic: Current Card Display State

## What I See in the Screenshot

### ✅ Working Correctly:
1. **External Library is Active**: East and West hands show SVG-based cards (from @letele/playing-cards)
2. **Vertical Layout**: Cards are stacked vertically as intended
3. **Overlap is Happening**: Cards are overlapping (not showing full 100px each)
4. **No Console Errors**: No "Card not found" errors in console

### 🔍 Need to Verify:
1. **Overlap Amount**: Cards appear to show ~30-40px each (not the target 20px)
2. **Total Card Count**: Can't tell from screenshot if all 13 cards are visible in the stack
3. **First Card Clipping**: First card should show only 20px (bottom portion), need to verify if top is clipped
4. **Last Card**: Last card should show full 100px height, need to verify

## Current Implementation

### Inline Style Application
```javascript
// App.js lines 59-68
const absoluteIndex = cardsBeforeThisSuit + cardIndex;
const inlineStyle = absoluteIndex === 0 ? {} : { marginTop: '-80px' };

return (
  <CardComponent
    key={`${suit}-${cardIndex}`}
    rank={card.rank}
    suit={card.suit}
    style={inlineStyle}  // ← marginTop: '-80px' for cards 1-12
  />
);
```

### LibraryCard Wrapper
```javascript
// LibraryCard.jsx lines 62-69
<div
  className="library-card"
  style={{
    width: '70px',
    height: '100px',
    position: 'relative',
    ...style  // ← marginTop: '-80px' applied here
  }}
>
  <CardComponent style={combinedStyle} />
</div>
```

### Container CSS
```css
/* App.css lines 476-487 */
.player-east .hand-display,
.player-west .hand-display {
  max-height: 350px;  /* Should clip first card's top 80px */
  overflow: hidden;   /* Hides clipped content */
  display: flex;
  flex-direction: column;
}
```

## Possible Issues

### Issue 1: Insufficient Overlap
**Symptom**: Cards show ~30-40px instead of 20px
**Cause**: marginTop: -80px might not be aggressive enough
**Solution**: Increase overlap to -85px or -90px

### Issue 2: Container Not Clipping First Card
**Symptom**: First card shows more than 20px
**Cause**: Container overflow or padding preventing clip
**Solution**: Adjust container max-height or remove top padding

### Issue 3: Wrapper Div Interference
**Symptom**: Inline styles not applying correctly
**Cause**: LibraryCard wrapper div might have conflicting styles
**Solution**: Apply marginTop directly to the wrapper (already done)

## Diagnostic Steps

### Step 1: Check Browser DevTools
Open browser DevTools (F12) and inspect an East or West card:

1. Right-click on a card in East or West hand
2. Select "Inspect Element"
3. Look for:
   ```html
   <div class="library-card" style="width: 70px; height: 100px; position: relative; margin-top: -80px;">
     <svg>...</svg>
   </div>
   ```

4. Verify:
   - ✅ `margin-top: -80px` is present on all cards except first
   - ✅ First card has no margin-top (or margin-top: 0)
   - ✅ All cards have height: 100px

### Step 2: Measure Visible Card Height
1. In DevTools, hover over a card element
2. Browser will highlight the element and show dimensions
3. Check the visible height (should be ~20px for overlapped cards)

### Step 3: Check Container Clipping
1. Inspect the `.hand-display` container
2. Verify:
   - ✅ `overflow: hidden` is applied
   - ✅ `max-height: 350px` is applied
   - ✅ First card's top is being clipped

## Expected vs Actual

### Expected Rendering
```
Container (max-height: 350px)
┏━━━━━━━━━━┓
┃ (hidden) ┃ ← Card 1: Top 80px hidden, bottom 20px visible
┃ Card 1   ┃ ← Shows only rank/suit (20px)
┃ Card 2   ┃ ← Overlaps Card 1 by 80px (20px visible)
┃ Card 3   ┃ ← Overlaps Card 2 by 80px (20px visible)
┃   ...    ┃
┃ Card 12  ┃ ← Overlaps Card 11 by 80px (20px visible)
┃ Card 13  ┃ ← Last card: FULLY visible (100px)
┃          ┃
┃          ┃
┗━━━━━━━━━━┛

Total visible height:
- 12 cards × 20px = 240px
- Last card = 100px
- Total = 340px (fits in 350px container with 10px padding)
```

### What Screenshot Shows
```
┏━━━━━━━━━━┓
┃ Card 1   ┃ ← Appears to show ~30-40px
┃ Card 2   ┃ ← Appears to show ~30-40px
┃ Card 3   ┃ ← Appears to show ~30-40px
┃   ...    ┃
┗━━━━━━━━━━┛
```

## Adjustment Options

### Option 1: Increase Overlap (More Aggressive)
Change inline style from `-80px` to `-85px` or `-90px`:

```javascript
// Show only 15px or 10px per card
const inlineStyle = absoluteIndex === 0 ? {} : { marginTop: '-85px' };  // 15px visible
// OR
const inlineStyle = absoluteIndex === 0 ? {} : { marginTop: '-90px' };  // 10px visible
```

### Option 2: Adjust Container Clipping
Reduce container max-height to force more clipping:

```css
.player-east .hand-display,
.player-west .hand-display {
  max-height: 300px;  /* More aggressive clipping */
}
```

### Option 3: Remove Top Padding
Ensure first card starts at container top:

```css
.player-east .hand-display,
.player-west .hand-display {
  padding: 0 10px 10px;  /* Already correct: no top padding */
}
```

## Questions for User

1. **Can you count the cards?**
   - How many cards are visible in the East hand?
   - How many cards are visible in the West hand?
   - Should be 13 each (one full deck per hand)

2. **What's the visible height?**
   - Roughly how many pixels of each card (except the last) are visible?
   - Target: 20px (just rank and suit visible)
   - If showing 30-40px: Need to increase overlap

3. **Is the last card fully visible?**
   - The bottom card in each stack should show the full card (100px height)
   - Can you see the entire last card?

4. **Browser DevTools check:**
   - Can you inspect a card and confirm `margin-top: -80px` is applied?
   - Screenshot of DevTools would be helpful

## Next Steps

Based on your answers, we can:
1. **Fine-tune the overlap**: Adjust from -80px to -85px or -90px
2. **Adjust container**: Modify max-height for better clipping
3. **Verify library integration**: Ensure SVG cards are rendering correctly

## Current Status: ✅ LIBRARY IS WORKING

The external library (@letele/playing-cards) **is successfully integrated and displaying cards**. We just need to fine-tune the overlap percentage to match your exact requirements.
