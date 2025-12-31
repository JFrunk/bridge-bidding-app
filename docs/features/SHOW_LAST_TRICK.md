# Show Last Trick Feature

**Date:** 2025-12-31
**Status:** Implemented

## Overview

Allows users to view the most recently completed trick during card play. This is a common bridge table feature that helps players track the play.

## User Experience

1. After the first trick completes, a "↶ Last Trick" button appears below the trick display
2. Clicking the button shows the last completed trick in the same compass layout
3. The winning card is highlighted with a yellow ring
4. Header shows "Trick #X - Won by [Position]"
5. Auto-dismisses after 3 seconds, or click anywhere to dismiss immediately
6. Button text toggles to "Current Trick" while viewing last trick

## Implementation

### Backend Changes

**File:** `backend/server.py`

Added `trick_history` to the `/api/get-play-state` response:

```python
trick_history_json = []
for trick in state.play_state.trick_history:
    trick_cards = [
        {"card": {"rank": card.rank, "suit": card.suit}, "position": player}
        for card, player in trick.cards
    ]
    trick_history_json.append({
        "cards": trick_cards,
        "leader": trick.leader,
        "winner": trick.winner
    })
```

### Frontend Changes

**New Component:** `frontend/src/components/play/LastTrickOverlay.jsx`
- Displays trick in compass layout (N/E/S/W positions)
- Winner highlighted with yellow ring
- Click to dismiss functionality

**State Management:** `frontend/src/App.js`
- `showLastTrick` - boolean to toggle overlay
- `lastTrick` - stores last trick data
- useEffect to extract last trick from play state
- useEffect for 3-second auto-dismiss timer

**UI Integration:** `frontend/src/PlayComponents.js`
- Button added below current trick display
- Conditional rendering: overlay vs current trick

**Styling:** `frontend/src/PlayComponents.css`
- `.last-trick-button` - subtle secondary button styling
- Responsive sizing for mobile

## Files

- `backend/server.py` - API response update
- `frontend/src/App.js` - State management
- `frontend/src/components/play/LastTrickOverlay.jsx` - New component
- `frontend/src/PlayComponents.js` - UI integration
- `frontend/src/PlayComponents.css` - Styling

## Future Enhancements

- **Claim Feature** - Allow user to declare they can win all remaining tricks (in backlog)
