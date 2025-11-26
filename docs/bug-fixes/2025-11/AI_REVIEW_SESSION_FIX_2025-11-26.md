# AI Review Session Loss Fix - November 26, 2025

## Issue

**Error:** "Could not save review request" when clicking "Request AI Review" on production

**Environment:** Production (Render)

## Root Cause

On Render (production), server instances are ephemeral. When the server restarts:
1. In-memory session state (`state.deal`) is lost
2. Backend's `/api/request-review` endpoint tries to access `state.deal.get(position)`
3. Returns `None` for all positions (North, East, West)
4. Endpoint returns 400 error: "Hand for {position} not available"
5. Frontend displays: "Could not save review request"

The previous fix (October 2025) addressed database migration issues but not session state loss.

## Solution

Two coordinated changes to handle session state loss gracefully:

### 1. Frontend Change (App.js)

Send `allHands` data when requesting a review (if user has clicked "Show All Hands" during the session):

```javascript
body: JSON.stringify({
  auction_history: auction,
  user_concern: userConcern,
  game_phase: gamePhase,
  user_hand: hand,
  user_hand_points: handPoints,
  all_hands: allHands  // NEW: Fallback for production session loss
})
```

### 2. Backend Change (server.py)

Use frontend-provided hands as fallback when backend state is missing:

```python
frontend_all_hands = data.get('all_hands')  # Fallback from frontend

# In the loop building all_hands:
if hand:
    # Use backend state (normal case)
    all_hands[position] = {...}
elif frontend_all_hands and frontend_all_hands.get(position):
    # Fallback: use frontend-provided hands
    fe_hand = frontend_all_hands[position]
    all_hands[position] = {
        'cards': fe_hand.get('hand', []),
        'points': fe_hand.get('points', {})
    }
else:
    # No hand available from either source
    return jsonify({'error': f'Hand for {position} not available. Try clicking "Show All Hands" first.'}), 400
```

## User Experience

| Scenario | Before Fix | After Fix |
|----------|------------|-----------|
| Normal (backend has state) | Works | Works |
| After server restart + user clicked "Show All Hands" | Error | Works |
| After server restart + user never showed hands | Error | Helpful error message |

## Files Changed

- `frontend/src/App.js` - Send allHands in review request
- `backend/server.py` - Use frontend hands as fallback in `/api/request-review`

## Testing

1. Start app locally
2. Deal a hand
3. Click "Show All Hands"
4. Restart backend server (simulates Render restart)
5. Click "Request AI Review"
6. Verify review modal opens successfully

## Related

- Previous fix: `docs/bug-fixes/2025-10/PRODUCTION_ISSUES_FIX_2025-10-23.md`
- AI Review feature: `docs/features/AI_REVIEW_FEATURE.md`
