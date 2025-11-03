# Card Display Requirements - All States

## Current Display States

### 1. **Bidding Phase - Normal View**
- **South (User)**: Horizontal cards, no overlap, all cards visible
- **North**: Horizontal cards, hidden (shows back of cards or nothing)
- **East**: Hidden
- **West**: Hidden

### 2. **Bidding Phase - "Show Hands" Mode**
- **South (User)**: Horizontal cards, ~35% overlap, all cards visible
- **North**: Horizontal cards, ~35% overlap, all cards visible
- **East**: **Vertical cards, 80% overlap (20px visible per card), last card shows fully**
- **West**: **Vertical cards, 80% overlap (20px visible per card), last card shows fully**

### 3. **Play Phase - Declarer View**
- **Declarer (South or North)**: Horizontal cards, clickable, legal plays highlighted
- **Dummy**: Horizontal cards, all visible, displayed prominently
- **Opponents (East/West)**: Vertical cards with back showing, or minimal display

### 4. **Play Phase - Defender View**
- **User's Hand**: Horizontal cards, clickable
- **Dummy**: Horizontal cards, all visible
- **Declarer**: Hidden or card backs
- **Partner**: Hidden or card backs

## Card Component Types

### BridgeCard (Horizontal)
- **Dimensions**: 70px wide × 100px tall (when standing upright)
- **Used for**: North, South positions
- **Overlap**: ~35% overlap (cards show ~45px each)
- **Layout**: Horizontal row, grouped by suit

### VerticalCard
- **Dimensions**: 70px wide × 100px tall
- **Used for**: East, West positions
- **Overlap**: **80% overlap (20px visible per card)**
- **Special**: First card shows 20px, last card shows fully (100px)
- **Layout**: Vertical column, grouped by suit

## Current Issues (from screenshot)

Looking at your screenshot, I see:

1. ✅ **Cards are rendering** - Both East and West show vertical cards
2. ⚠️ **Yellow background on suit groups** - Debug CSS still active
3. ⚠️ **Blue borders on cards** - Debug CSS still active
4. ⚠️ **Red border on container** - Debug CSS still active
5. ❓ **Overlap amount** - Need to verify it's 80% (20px visible)

## Questions for Clarification

Before refactoring, I need to understand your requirements:

### Display Requirements:

1. **Overlap Percentage**:
   - Current: 80% overlap (20px visible per card)
   - Is this correct for vertical hands (East/West)?
   - What about horizontal hands (North/South)? Still 35% overlap?

2. **First Card Behavior**:
   - **Current requirement**: First card shows 20px (clipped at top)
   - **Alternative**: First card shows fully (100px)?
   - Which do you prefer?

3. **Last Card Behavior**:
   - **Confirmed**: Last card shows fully (100px) ✅
   - This is working as intended?

4. **Suit Separation**:
   - **Confirmed**: NO gaps between suits ✅
   - Continuous overlap across all suits?

5. **During Play Phase**:
   - Should vertical cards (East/West) remain vertical during play?
   - Or should they rotate/change orientation?

### Card Display States:

6. **"Show Hands" Feature**:
   - When enabled, should it show:
     - All 4 hands visible?
     - Opponents' hands (E/W) in vertical orientation?
     - Is this working correctly now?

7. **Dummy Hand**:
   - During play, should dummy always be horizontal?
   - Should it be in a special prominent position?

8. **Card Backs**:
   - When should we show card backs vs. hiding cards entirely?
   - Currently, we don't show card backs - is this correct?

## Proposed Refactoring Goals

### Simplification:
1. **Single Card Component**: One unified card component that adapts to orientation
2. **Consistent Overlap Logic**: Same overlap calculation regardless of position
3. **Clean CSS**: Remove all hardcoded overlaps, use CSS variables
4. **State-Driven Display**: Clear separation between display states

### Code Structure:
```
components/
  bridge/
    Card.jsx              ← Unified card component
    CardHand.jsx          ← Hand container (horizontal or vertical)
    CardDisplay.jsx       ← Top-level display coordinator
```

### CSS Architecture:
```css
:root {
  --card-width: 70px;
  --card-height: 100px;
  --horizontal-overlap: 65%;  /* Show 35% */
  --vertical-overlap: 80%;    /* Show 20% */
}
```

## Next Steps

**Please answer the clarifying questions above, then I will:**

1. Create a new git branch: `feature/card-display-refactor`
2. Document the complete requirements
3. Implement the simplified card display system
4. Test all display states
5. Create a PR for review

**What are your answers to the questions above?**
