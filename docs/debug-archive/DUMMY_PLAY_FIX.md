# Dummy Play Issue - Fix for "No cards played"

## Problem Identified

User reported: **"No cards played"** after West's opening lead in hand_2025-10-11_14-28-29.json

**Game State:**
- Contract: 2♦ by South
- Dummy: North
- Opening Leader: West
- West has led ♠2
- **Next to play: North (dummy)**
- Dummy should be controlled by South (declarer)

## Root Cause

**Data Structure Mismatch** between backend and frontend:

### Backend (server.py:753-756)
```python
dummy_hand = {
    "cards": [{"rank": c.rank, "suit": c.suit} for c in ...],
    "position": dummy_pos
}
```
Returns: `{ cards: [...], position: "N" }`

### Frontend (App.js:672)
```javascript
if (state.dummy_hand && !dummyHand) {
  setDummyHand(state.dummy_hand);  // ❌ Sets entire object, not just cards
}
```
Expected: `[{rank: "A", suit: "♠"}, ...]` (array of cards)
Actually got: `{cards: [...], position: "N"}` (object with cards property)

### Impact

When PlayComponents.js tried to map over `dummyHand`:
```javascript
{dummyHand.map((card, index) => ...)}  // ❌ Can't map over object!
```

This caused the dummy cards to not render, making it impossible for the declarer to play from dummy.

## Solution

Updated [App.js:674](frontend/src/App.js#L674) to extract the cards array:

```javascript
// Update dummy hand if revealed
if (state.dummy_hand && !dummyHand) {
  // Backend returns dummy_hand as { cards: [...], position: "N" }
  // Extract just the cards array
  const dummyCards = state.dummy_hand.cards || state.dummy_hand;
  setDummyHand(dummyCards);
}
```

This safely handles both formats:
- If `state.dummy_hand.cards` exists, use it (current backend format)
- Otherwise, use `state.dummy_hand` directly (fallback for array format)

## Bridge Rules Context

In bridge, the **declarer controls both their own hand AND dummy's hand**:
- South is declarer
- North is dummy
- After West leads, North's cards are revealed
- **South (the user) clicks on North's cards** to play from dummy

The frontend already had the correct logic for this (line 219 in PlayComponents.js):
```javascript
onClick={userIsDeclarer ? onDummyCardPlay : () => {}}
disabled={userIsDeclarer ? !isDummyTurn : true}
```

The issue was simply that the dummy cards weren't being displayed because of the data structure mismatch.

## Testing

To test this fix:
1. Start a game where South is declarer
2. Wait for West's opening lead
3. Dummy (North) should reveal their cards
4. As South (declarer), you should be able to click North's cards to play from dummy

## Files Modified

1. **`frontend/src/App.js`** (line 674)
   - Fixed dummy hand extraction from backend response

## Related Code

- Backend endpoint: `/api/get-play-state` ([server.py:726](backend/server.py#L726))
- Frontend play logic: `handleDummyCardPlay` ([App.js:467](frontend/src/App.js#L467))
- UI component: `PlayTable` ([PlayComponents.js:159](frontend/src/PlayComponents.js#L159))

---

**Date:** 2025-10-11
**Issue Source:** User gameplay review request - hand_2025-10-11_14-28-29.json
**Status:** ✅ Fixed
