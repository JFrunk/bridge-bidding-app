# UI Refactor Implementation Plan

## Current Status
The PlayComponents.js file has become corrupted with duplicate sections and incomplete edits. Need to carefully implement the requested changes.

## Changes Required

### 1. Remove "East's Turn" Banner
- Delete `<TurnIndicator>` component (lines 321-325)
- Turn indication will be via active player highlighting

### 2. Consolidated Contract Header
Replace separate header components with one horizontal layout:

```jsx
<div className="contract-header-consolidated">
  {/* Unified Tricks Bar - tri-color */}
  <div className="unified-tricks-bar">
    <div className="tricks-won-section" style={{width: `${won%}%`}}>
      {wonCount}
    </div>
    <div className="tricks-remaining-section" style={{width: `${remaining%}%`}}>
      {remainingCount}
    </div>
    <div className="tricks-lost-section" style={{width: `${lost%}%`}}>
      {lostCount}
    </div>
  </div>

  <div className="contract-display-large">
    4NT by South
  </div>

  <div className="tricks-summary">
    Won: X | Lost: Y | Remaining: Z
  </div>

  <div className="bidding-summary-compact">
    Bidding: N E S W...
  </div>
</div>
```

### 3. Restore Compass Layout
```
        North
    West  🎴  East
        South
```

### 4. 2-Suit Stacking for East/West
Helper function to stack suits 2x2:
- Top row: Trump suit (or ♠ for NT) + opposite color suit
- Bottom row: Remaining 2 suits

### 5. Remove Card Shadows
All `.playable-card` CSS:
- Remove `box-shadow`
- Remove 3D depth effects
- Keep overlap for horizontal spacing

### 6. Increase Position Label Font
`.position-label { font-size: 2rem; }` (2x current)

### 7. Active Player Highlighting
```css
.position.active-player {
  border: 3px solid #4CAF50;
  box-shadow: 0 0 15px rgba(76, 175, 80, 0.6);
}
```

## Files to Edit
1. `frontend/src/PlayComponents.js` - Structure changes
2. `frontend/src/PlayComponents.css` - Styling

## Implementation Order
1. Clean up duplicate sections in PlayComponents.js
2. Add helper function `renderStackedSuits()`
3. Replace header with consolidated version
4. Fix grid layout back to compass
5. Update CSS for all visual changes
6. Test build

## Next Action
Due to file corruption, recommend:
1. Read full PlayComponents.js file
2. Identify all duplicate sections
3. Create clean version with proper structure
4. Then add new features systematically
