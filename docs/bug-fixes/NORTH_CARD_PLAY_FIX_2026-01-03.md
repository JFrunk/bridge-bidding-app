# Bug Fix: Cannot Play Cards from North After First Trick

**Date:** 2026-01-03
**Status:** Fixed
**Severity:** Critical (recurring user complaint)

## Issue Summary

Users reported being unable to play cards from North's position after the first trick was completed. This occurred when North was the declarer and South (user) was the dummy.

Example feedback:
- "I cannot play my cards from north after the first trick was completed. This has occurred prior."
- "The game shows north is to lead a card but I cannot play any card. They move but are not played."

## Root Cause

The AI play loop's "nextIsUserTurn" logic was incorrect in determining when the user controls the North position.

### Incorrect Logic
```javascript
const nextIsUserTurn = next_to_play === 'S' ||
  (next_to_play === dummy && declarer === 'S');
```

This only worked when South was the declarer. It failed when:
- North is declarer
- South is dummy
- It's North's turn to play

In bridge, when a player is dummy, they control the declarer's cards. So when South is dummy and North is declarer, the user should control BOTH positions.

## Fix Applied

Changed the logic to properly detect when NS is declaring (declarer is N or S), which means the user controls both N and S:

```javascript
const nsIsDeclaring = declarer === 'N' || declarer === 'S';
const nextIsUserTurn = next_to_play === 'S' ||
  (next_to_play === 'N' && nsIsDeclaring);
```

## Files Changed

- `frontend/src/App.js` - Fixed in 7 locations across:
  - `handleCardPlay` (2 occurrences)
  - `handleDeclarerCardPlay` (2 occurrences)
  - `handleDummyCardPlay` (2 occurrences)
  - AI play loop (1 occurrence)

## Testing

- Frontend build passes
- PlayComponents unit tests pass
- Manual verification of the scenario pending

## Prevention

The fix includes comments explaining the logic to prevent future regression:
```javascript
// CRITICAL FIX: User controls BOTH N and S when NS is declaring (declarer is N or S)
// This fixes the bug where user couldn't play from North after first trick
```
