# Implementation Plan: Show Last Trick Feature

## Overview

Add a "Show Last Trick" button during card play that allows users to review the most recently completed trick. This is a common bridge table feature that helps players track the play.

## Current State Analysis

### Backend (Already Supports This)
- `trick_history` is already maintained in `PlayState` (server.py:249, 277)
- Each completed trick is stored as a `Trick` object with: `cards`, `leader`, `winner`
- `/api/get-play-state` already returns `trick_history` in response
- No backend changes needed

### Frontend (Needs Implementation)
- `trick_history` is returned by API but **not currently used**
- `CurrentTrickDisplay` component exists and can be reused for showing last trick
- Play controls are in App.js action-area section

## Design Decision: Button Placement

After analyzing the UI layout, I recommend **Option A: Inline with Current Trick Display**

### Why This Location?
1. **Contextually relevant** - Next to where tricks are displayed
2. **Non-intrusive** - Small button that doesn't interfere with card play
3. **Discoverable** - Visible when looking at the trick area
4. **Follows bridge table conventions** - Real tables have trick cards nearby

### Alternative Considered (Not Recommended)
- Bottom control area: Too far from trick display, less intuitive
- Modal button: Overkill for quick review

## UI Design

### Button Appearance
- Small secondary button: "Last Trick" or icon (↶ or 🔄)
- Only visible when `trick_history.length > 0` (at least one trick completed)
- Positioned below the current trick display, centered
- Subtle styling to not distract from gameplay

### Display Behavior (Toggle, Not Modal)
- **Click once**: Show last trick in place of current trick (overlay/replace)
- **Click again** or **after 3 seconds**: Return to current trick
- OR: Hover/hold to show, release to return (simpler for quick glance)

**Recommended: Simple toggle with auto-dismiss after 3 seconds**

This is less intrusive than a modal and feels natural for a "quick peek" use case.

## Implementation Steps

### Step 1: Update App.js State Management
Add state for showing last trick:
```javascript
const [showLastTrick, setShowLastTrick] = useState(false);
const [lastTrick, setLastTrick] = useState(null);
```

### Step 2: Extract Last Trick from API Response
In the play state fetch, extract and store last trick:
```javascript
// When fetching play state
if (data.trick_history && data.trick_history.length > 0) {
  setLastTrick(data.trick_history[data.trick_history.length - 1]);
}
```

### Step 3: Create ShowLastTrickButton Component
New component: `frontend/src/components/play/ShowLastTrickButton.jsx`

```jsx
export function ShowLastTrickButton({ onClick, disabled }) {
  return (
    <button
      className="show-last-trick-btn"
      onClick={onClick}
      disabled={disabled}
    >
      ↶ Last Trick
    </button>
  );
}
```

### Step 4: Modify CurrentTrickDisplay or Create LastTrickOverlay
Option A: Add overlay mode to CurrentTrickDisplay
Option B: Create separate LastTrickDisplay (reuses same card layout)

Recommend Option B for cleaner separation:
```jsx
export function LastTrickOverlay({ trick, winner, onClose }) {
  // Reuse TrickCard component from CurrentTrickDisplay
  // Add header: "Trick #X - Won by {position}"
  // Auto-close after 3 seconds OR click to dismiss
}
```

### Step 5: Integrate into PlayTable
Add button below current-trick-container:
```jsx
<div className="current-trick-container">
  {showLastTrick && lastTrick ? (
    <LastTrickOverlay
      trick={lastTrick}
      winner={lastTrick.winner}
      onClose={() => setShowLastTrick(false)}
    />
  ) : (
    <CurrentTrick ... />
  )}
</div>

{/* Button below trick display */}
{lastTrick && (
  <ShowLastTrickButton
    onClick={() => setShowLastTrick(!showLastTrick)}
    disabled={showLastTrick}
  />
)}
```

### Step 6: Add CSS Styling
```css
.show-last-trick-btn {
  margin-top: 8px;
  padding: 4px 12px;
  font-size: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.show-last-trick-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.last-trick-overlay {
  position: relative;
}

.last-trick-header {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
```

### Step 7: Auto-Dismiss Timer
```javascript
useEffect(() => {
  if (showLastTrick) {
    const timer = setTimeout(() => setShowLastTrick(false), 3000);
    return () => clearTimeout(timer);
  }
}, [showLastTrick]);
```

## Files to Modify

1. **frontend/src/App.js**
   - Add `showLastTrick` and `lastTrick` state
   - Extract last trick from play state API response
   - Pass props to PlayTable

2. **frontend/src/PlayComponents.js**
   - Add ShowLastTrickButton to PlayTable
   - Add conditional rendering for last trick overlay

3. **frontend/src/components/play/LastTrickOverlay.jsx** (NEW)
   - Create new component for displaying last trick

4. **frontend/src/PlayComponents.css**
   - Add styles for button and overlay

## Testing Plan

1. Play through a hand, complete at least one trick
2. Verify "Last Trick" button appears after first trick completes
3. Click button - last trick should display with winner highlighted
4. Verify auto-dismiss after 3 seconds
5. Click button again - should toggle back immediately
6. Complete more tricks - button should always show most recent
7. Verify button not visible before any tricks completed

## Future Enhancement: Claim Feature

As noted by user, "Claim" functionality should be added later:
- User declares they can win all remaining tricks
- Requires confirmation from opponents (in practice, AI would auto-accept or evaluate)
- Speeds up obvious endgames
- Add to enhancement backlog, not this implementation

---

## Summary

This is a straightforward feature that:
1. Uses existing backend data (no API changes)
2. Reuses existing trick display components
3. Adds minimal UI (one small button)
4. Non-intrusive (toggle, auto-dismiss)
5. Can be implemented in ~2-3 hours
