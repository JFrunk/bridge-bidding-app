# Scoring Perspective Fix - October 2025

## Problem Summary

The contract scoring display was showing scores with the wrong sign (positive/negative reversed) from the user's perspective. This issue has occurred multiple times and kept reverting.

## Root Cause

**Two Display Locations, One Missing the Fix:**

1. ✅ **ScoreModal.jsx** - Was correctly converting scores to user perspective
2. ❌ **ContractHeader.jsx** - Was showing raw backend scores without conversion

## The Scoring Perspective System

### Backend (Python)
- Returns scores from **DECLARER'S perspective**
- Positive score = declarer made their contract
- Negative score = declarer went down (defenders win)

### Frontend (React)
- User always plays **South** (part of the **North-South team**)
- Must convert backend scores to **user's NS perspective**

## The Conversion Logic

```javascript
// Step 1: Determine if declarer is on user's team
const declarerIsNS = contract.declarer === 'N' || contract.declarer === 'S';

// Step 2: Convert to user's perspective
// If EW is declarer, flip the sign (their wins are our losses)
const userScore = declarerIsNS ? score : -score;
```

## Correct Behavior Examples

| Scenario | Declarer | Backend Score | User Sees | Why |
|----------|----------|--------------|-----------|-----|
| NS makes 3NT | N or S | +400 | +400 | We made our contract ✅ |
| NS down 2 | N or S | -100 | -100 | We failed our contract ❌ |
| EW makes 4♠ | E or W | +420 | -420 | Opponents made (we lost) ❌ |
| EW down 1 | E or W | -50 | +50 | We set opponents ✅ |

## Files Modified

### 1. `/frontend/src/components/play/ContractHeader.jsx`

**Added perspective conversion logic:**
```javascript
// Lines 25-30
const declarerIsNS = declarer === 'N' || declarer === 'S';
const userScore = scoreData ? (declarerIsNS ? scoreData.score : -scoreData.score) : null;
```

**Updated display to use `userScore`:**
```javascript
// Lines 67-86
{scoreData && totalTricksPlayed === 13 && (
  <div className={cn(
    "flex items-center gap-3 px-4 py-2 rounded-md border-2 w-fit",
    userScore >= 0 ? "bg-green-900/30 border-success" : "bg-red-900/30 border-danger"
  )}>
    <span className="text-lg font-medium text-gray-300">Your Score:</span>
    <span className={cn(
      "text-2xl font-bold",
      userScore >= 0 ? "text-success" : "text-danger"
    )}>
      {userScore >= 0 ? '+' : ''}{userScore}
    </span>
    {/* ... */}
  </div>
)}
```

**Added comprehensive documentation (lines 4-19)** explaining the CRITICAL SCORING PERSPECTIVE LOGIC.

### 2. `/frontend/src/components/play/ScoreModal.jsx`

**Simplified and aligned comments (lines 34-43)** to match ContractHeader.jsx documentation.

## Prevention Strategy

### Documentation Added
1. **Detailed JSDoc comments** in both ContractHeader.jsx and ScoreModal.jsx
2. **Explicit warnings** that logic MUST match between components
3. **This documentation file** explaining the full system

### Test Coverage
Created `/test_score_display_fix.py` with 8 test cases covering all scenarios:
- NS declares and makes/goes down
- EW declares and makes/goes down

### Code Review Checklist
When reviewing scoring changes, verify:
- [ ] Both ContractHeader.jsx and ScoreModal.jsx use the same conversion logic
- [ ] Score comes from `userScore` not raw `scoreData.score`
- [ ] Comments explain WHY the conversion happens
- [ ] Test passes: `python3 test_score_display_fix.py`

## Git History

This issue has been fixed multiple times:
```bash
2b0948a feat: Major gameplay enhancements (Oct 16, 2025)
eac1336 FEATURE: Add scoring display (Oct 13, 2025)
663c596 docs: Session state implementation
8ba2ff8 feat: Add session scoring system
```

The recurring issue was that ContractHeader was added later and never received the perspective conversion logic that ScoreModal had.

## Testing Instructions

### Manual Testing
1. Start the development server
2. Play a hand where EW declares
3. Let EW make their contract
4. **Expected:** Score shows as NEGATIVE (red) - you lost
5. Play a hand where EW declares
6. Set the contract (EW goes down)
7. **Expected:** Score shows as POSITIVE (green) - you set them

### Automated Testing
```bash
python3 test_score_display_fix.py
```
Should show: "✅ All tests passed! Scoring perspective is correct."

## Related Files

- `/backend/engine/play_engine.py` - Lines 376-545 (calculate_score function)
- `/backend/engine/session_manager.py` - Lines 52-88 (add_hand_score method)
- `/frontend/src/App.js` - Lines 1250-1260 (fetches scoreData)

## Future Recommendations

1. **Centralize the conversion logic** into a utility function:
   ```javascript
   // utils/scoringUtils.js
   export function convertToUserPerspective(scoreData) {
     const declarerIsNS = scoreData.contract.declarer === 'N' ||
                          scoreData.contract.declarer === 'S';
     return {
       ...scoreData,
       userScore: declarerIsNS ? scoreData.score : -scoreData.score
     };
   }
   ```

2. **Add TypeScript** to catch these issues at compile time

3. **Create integration tests** that verify both components show the same score

## Summary

The fix ensures that **both** ScoreModal and ContractHeader display scores from the user's perspective (NS team) by converting backend scores (declarer's perspective) consistently. Comprehensive documentation prevents future regressions.
