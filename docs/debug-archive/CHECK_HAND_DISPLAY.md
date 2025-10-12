# Check Hand Display Logic

## Current Game State

From backend:
- **Declarer:** W (West)
- **Dummy:** E (East)
- **You:** S (South)

## What SHOULD Display

According to bridge rules:
- ✅ **South (you):** Always visible
- ✅ **East (dummy):** Visible (face-up after opening lead)
- ❌ **North:** NOT visible (defender, cards hidden)
- ❌ **West:** NOT visible (declarer, cards hidden)

## Display Logic in Code

The code shows hands based on these conditions:

**North:** `dummyPosition === 'N' && dummyHand`
- Shows only if North is dummy

**East:** `dummyPosition === 'E' && dummyHand`
- Shows only if East is dummy

**South:** Always shows (your hand)

**West:** `dummyPosition === 'W' && dummyHand`
- Shows only if West is dummy

## In Your Game

With Declarer=W and Dummy=E:
- `dummyPosition === 'N'` → **FALSE** (N is not dummy)
- `dummyPosition === 'E'` → **TRUE** (E is dummy)
- `dummyPosition === 'W'` → **FALSE** (W is not dummy)

**Expected Result:**
- North: NO CARDS
- East: DUMMY CARDS ✅
- South: YOUR CARDS ✅
- West: NO CARDS

## DEBUG Logging Added

I've added a console log that will show:

```javascript
👁️ Hand Display Logic: {
  dummyPosition: "E",
  declarerPosition: "W",
  userIsDeclarer: false,
  userIsDummy: false,
  North should show: false,
  East should show: true,
  South should show: true,
  West should show: false
}
```

## How to Check

1. **Refresh browser** (Cmd+Shift+R)
2. **Open console** (F12 or Cmd+Option+I)
3. **Look for** the `👁️ Hand Display Logic:` log
4. **Check the values:**
   - Which positions show `true`?
   - Do they match what you see on screen?

## What to Report

**In Console:**
Look at `👁️ Hand Display Logic:` and verify:
- `dummyPosition:` should be "E"
- `North should show:` should be false
- `East should show:` should be true
- `West should show:` should be false

**On Screen:**
Expected display:
- North: NO cards (defender)
- East: YES cards (dummy - face up)
- South: YES cards (you)
- West: NO cards (AI declarer)

## Possible Issues

### Issue 1: Both East and West Showing
If both East AND West are showing cards:
- Check `dummyPosition` value in console
- Should be one position only ('E' or 'W', not both)
- If it's showing both, there's a logic bug

### Issue 2: Wrong Position Showing
If the wrong position shows:
- `dummyPosition` might have wrong value
- Backend might be sending wrong dummy position

### Issue 3: All Positions Showing
If all 4 positions show cards:
- Might be in "Show Hands" debug mode
- Check if there's a toggle that was activated

## Visual Checklist

Expected layout with Declarer=W, Dummy=E:

```
         [North]
      (NO CARDS - hidden)

[West]    [CENTER]    [East]
(NO CARDS) TRICK      DUMMY
(hidden)   BOX        CARDS
                      VISIBLE

         [South]
        YOUR CARDS
         VISIBLE
```

## If Cards Are Showing Wrong

**Scenario 1: East NOT showing cards (but East IS dummy)**
- Check if `dummyPosition === 'E'` is false (should be true)
- Check console log for `East should show:` value
- Check if `dummyHand` prop is null/undefined

**Scenario 2: West showing cards (but West is declarer)**
- Check if `dummyPosition === 'W'` is somehow true (should be false)
- Check console log for `West should show:` value
- Backend might be sending wrong dummy position

**Scenario 3: Both East and West showing**
- Check if PlayTable is rendered multiple times
- Look for multiple `👁️ Hand Display Logic:` logs
- Might be duplicate rendering bug

## Next Steps

1. **Refresh and check console**
2. **Find the `👁️ Hand Display Logic:` log**
3. **Compare console values** to what displays on screen
4. **Report any mismatch:**
   - If console says `East should show: false` but East cards ARE showing
   - If console says `West should show: true` but West cards are NOT showing

This will tell us if it's a logic bug (conditions wrong) or a rendering bug (cards showing despite conditions).
