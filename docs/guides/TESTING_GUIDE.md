# Phase 1 Card Play - Testing Guide

## ✅ Pre-Test Status

**Backend:** ✅ Running on http://localhost:5001
- Flask server is live
- All play endpoints responding with HTTP 200
- Recent endpoint calls visible in logs

**Frontend:** ✅ Running on http://localhost:3000
- React app is live with hot-reload
- Changes automatically picked up

## 🧪 Testing Checklist

### Test 1: Basic Play Flow
**Objective:** Verify complete bidding-to-play transition

1. **Open the app:** Go to http://localhost:3000
2. **Deal a hand:** Click "Deal New Hand" button
3. **Complete bidding:** Make bids until you reach a contract
   - Example: 1NT - Pass - 3NT - Pass - Pass - Pass
4. **Expected Results:**
   - ✅ After 3rd pass, message appears: "Contract: 3NT by [Player]. Opening leader: [Player]"
   - ✅ Screen transitions from bidding to play phase
   - ✅ Bidding box disappears or is disabled

### Test 2: Opening Lead & Dummy
**Objective:** Verify opening lead and dummy reveal

5. **Watch opening lead:**
   - ✅ AI automatically makes opening lead (1 second delay)
   - ✅ Message shows: "[Player] played [Card]"
   - ✅ Card appears in center play area
6. **Dummy revealed:**
   - ✅ Dummy hand (partner of declarer) is shown
   - ✅ Dummy position labeled "(Dummy)"

### Test 3: AI Play Loop
**Objective:** Verify AI players continue automatically

7. **Watch AI play:**
   - ✅ AI players automatically play cards in sequence
   - ✅ ~1 second delay between plays (for visibility)
   - ✅ Current trick shows up to 4 cards
   - ✅ When trick complete, cards clear and tricks count updates
   - ✅ Next trick begins with winner of previous trick

### Test 4: User Card Play
**Objective:** Verify user can play cards

8. **Wait for your turn (South):**
   - ✅ Message appears: "Your turn to play!"
   - ✅ Arrow indicator shows: "South (You) ⬅️ Your turn!"
9. **Play a card:**
   - ✅ Cards in your hand are clickable (hover effect)
   - ✅ Click a card
   - ✅ Card is removed from your hand
   - ✅ Card appears in play area
   - ✅ AI continues playing

### Test 5: Trick Tracking
**Objective:** Verify tricks are counted correctly

10. **Monitor tricks display:**
    - ✅ "Tricks Won" shows: NS: X, EW: Y
    - ✅ Counts update after each trick completes
    - ✅ Trick winner gets the trick
    - ✅ Total tricks = NS + EW increases each trick

### Test 6: Complete Hand (13 Tricks)
**Objective:** Verify all 13 tricks can be played

11. **Play all 13 tricks:**
    - ✅ All cards are played
    - ✅ No errors occur
    - ✅ Hand empties as cards are played

### Test 7: Score Display
**Objective:** Verify final score calculation

12. **After 13 tricks:**
    - ✅ Score modal appears automatically
    - ✅ Shows contract (e.g., "3NT by N")
    - ✅ Shows tricks taken (e.g., "9")
    - ✅ Shows result:
      - Green "Made 3NT" if contract made
      - Red "Down 1" if contract failed
    - ✅ Shows score (positive or negative)
13. **Close modal:**
    - ✅ Click "Close" button
    - ✅ Modal closes
    - ✅ Can deal new hand

### Test 8: Edge Cases

#### Test 8a: Illegal Card Play
**Objective:** Verify follow-suit rules enforced

14. **Try to play wrong suit (if possible):**
    - ✅ Should show error message
    - ✅ Card should not be played
    - ✅ Can try again with legal card

#### Test 8b: Multiple Contracts
**Objective:** Verify different contract types work

15. **Test different contracts:**
    - ✅ No Trump contracts (1NT, 3NT, 6NT)
    - ✅ Suit contracts (4♠, 5♣, 2♥)
    - ✅ Low-level contracts (1♣, 2♦)
    - ✅ Slam contracts (6♠, 7NT)

#### Test 8c: Vulnerability
**Objective:** Verify vulnerability affects scoring

16. **Test with different vulnerabilities:**
    - Note: Vulnerability rotates automatically (None → NS → EW → Both)
    - ✅ Score is higher when vulnerable
    - ✅ Score is lower when not vulnerable

### Test 9: Deal New Hand After Play
**Objective:** Verify can restart after completing play

17. **Click "Deal New Hand":**
    - ✅ New hand dealt
    - ✅ Back to bidding phase
    - ✅ Auction is empty
    - ✅ No play state visible

### Test 10: Console Logs (Developer Check)
**Objective:** Verify no errors in console

18. **Open browser console (F12):**
    - ✅ No red errors
    - ✅ Should see logs like:
      - "Play started: {contract: '3NT', ...}"
      - "AI played: {card: {...}, ...}"
      - "Card played: {card: {...}, ...}"

---

## 🐛 Known Issues to Watch For

### Minor Issues (Expected)
1. **Multiple background processes:** Many Flask servers running (doesn't affect functionality)
2. **Card removal timing:** Slight delay when user plays card
3. **First play transition:** May take 1-2 seconds to start play phase

### Critical Issues (Report Immediately)
- ❌ Play phase doesn't start after 3 passes
- ❌ Cards don't appear in play area
- ❌ Trick winner calculated incorrectly
- ❌ Score not displayed after 13 tricks
- ❌ Cannot play cards on your turn
- ❌ App crashes or freezes

---

## 📊 Test Results Template

Copy this template and fill in your results:

```
PHASE 1 CARD PLAY - TEST RESULTS
Date: __________
Tester: __________

Test 1 - Basic Play Flow: ☐ Pass ☐ Fail
Test 2 - Opening Lead & Dummy: ☐ Pass ☐ Fail
Test 3 - AI Play Loop: ☐ Pass ☐ Fail
Test 4 - User Card Play: ☐ Pass ☐ Fail
Test 5 - Trick Tracking: ☐ Pass ☐ Fail
Test 6 - Complete Hand: ☐ Pass ☐ Fail
Test 7 - Score Display: ☐ Pass ☐ Fail
Test 8a - Illegal Card Play: ☐ Pass ☐ Fail ☐ N/A
Test 8b - Multiple Contracts: ☐ Pass ☐ Fail
Test 8c - Vulnerability: ☐ Pass ☐ Fail
Test 9 - Deal New Hand: ☐ Pass ☐ Fail
Test 10 - Console Logs: ☐ Pass ☐ Fail

Overall: ☐ APPROVED ☐ NEEDS FIXES

Issues Found:
1. ___________________________________
2. ___________________________________
3. ___________________________________

Comments:
_______________________________________
_______________________________________
```

---

## 🔧 Debugging Tips

### If play phase doesn't start:
1. Check browser console for errors
2. Check Flask logs for errors on `/api/start-play`
3. Verify auction has 3 consecutive passes
4. Try refreshing the page and dealing new hand

### If cards don't play:
1. Check if it's your turn (South)
2. Check browser console for errors
3. Check Flask logs for errors on `/api/play-card`
4. Try clicking different cards

### If AI doesn't play:
1. Check browser console for errors
2. Check Flask logs for `/api/get-ai-play` errors
3. Wait a few seconds (may be network delay)
4. Check if play state is updating

### If score doesn't show:
1. Verify all 13 tricks were played
2. Check browser console for errors
3. Check Flask logs for `/api/complete-play` errors
4. Check tricks count adds up to 13

---

## ✅ When Testing is Complete

Once all tests pass:
1. Report results using the template above
2. Note any issues or suggestions
3. Ready to commit and deploy to Render!

**Good luck with testing!** 🎉
