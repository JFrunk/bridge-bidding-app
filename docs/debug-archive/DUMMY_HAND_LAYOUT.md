# Dummy Hand Display - Layout Enhancement

## Request
"Please display my partner's cards above the green card box once the opponent plays the first card."

## Layout Structure

The play area uses CSS Grid with the following layout:

```
+------------------+
|      NORTH       |  ← Partner's hand (dummy) if you're declarer
|    (Dummy)       |     OR Opponent's dummy if you're defender
+------------------+
|        |         |
| WEST   | CENTER  | EAST
|        | (Trick) |
|        |         |
+------------------+
|      SOUTH       |  ← Your hand (always visible)
|      (You)       |
+------------------+
```

**Grid Areas:**
- `.play-area` defines: `grid-template-areas: ". north ." / "west center east" / ". south ."`
- North position: `grid-area: north` (top center)
- CurrentTrick: `grid-area: center` (middle center) - **GREEN BOX**
- South position: `grid-area: south` (bottom center)
- East/West: `grid-area: east/west` (sides)

## Changes Applied

### 1. Position Layout Enhancement

**File:** [PlayComponents.css:142-172](frontend/src/PlayComponents.css#L142-L172)

Added flexbox centering to all positions:

```css
.position-north {
  grid-area: north;
  display: flex;
  flex-direction: column;
  align-items: center;      /* Center horizontally */
  justify-content: center;   /* Center vertically */
}

/* Same for .position-east, .position-south, .position-west */
```

**Result:**
- All position containers now center their content
- North's dummy hand will be centered above the trick area
- Consistent alignment across all positions

### 2. Position Label Enhancement

**File:** [PlayComponents.css:174-183](frontend/src/PlayComponents.css#L174-L183)

```css
.position-label {
  font-weight: bold;
  color: #61dafb;
  text-align: center;
  padding: 5px 10px;
  background-color: #2a2a2a;
  border-radius: 5px;
  margin-bottom: 10px;    /* NEW - Space between label and cards */
  width: 100%;            /* NEW - Full width of container */
}
```

**Result:**
- Label has space below it before cards appear
- Full-width label for better visual separation

### 3. Dummy Hand Visual Enhancement

**File:** [PlayComponents.css:374-385](frontend/src/PlayComponents.css#L374-L385)

```css
.dummy-hand {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 600px;
  width: 100%;                                    /* NEW - Full width of container */
  margin: 0 auto;
  padding: 10px;                                  /* NEW - Internal spacing */
  background-color: rgba(97, 218, 251, 0.1);     /* NEW - Subtle blue background */
  border-radius: 8px;                             /* NEW - Rounded corners */
  border: 2px solid rgba(97, 218, 251, 0.3);     /* NEW - Blue border */
}
```

**Result:**
- Dummy hand has subtle blue background/border to make it stand out
- More prominent visual presence
- Clear indication that these are dummy's cards

## How It Works

### Standard Bridge Rules:
1. **Before opening lead:** Only your hand is visible
2. **After opening lead:** Dummy's hand is revealed face-up
3. **Declarer controls:** Both their own hand and dummy's hand
4. **Defenders see:** Their own hand + dummy's hand (but can't control dummy)

### Implementation:

**Dummy Revealed Trigger** (Backend: server.py:676-677):
```python
if len(current_play_state.current_trick) == 1 and not current_play_state.dummy_revealed:
    current_play_state.dummy_revealed = True
```

**Frontend Display** (PlayComponents.js:213-228 for North):
```javascript
{/* Show North's hand if it's dummy */}
{dummyPosition === 'N' && dummyHand && (
  <div className="dummy-hand">
    {['♠', '♥', '♦', '♣'].map(suit => (
      <div key={suit} className="suit-group">
        {dummyHand.filter(card => card.suit === suit).map((card, index) => (
          <PlayableCard
            key={`${suit}-${index}`}
            card={card}
            onClick={userIsDeclarer ? onDummyCardPlay : () => {}}
            disabled={userIsDeclarer ? !isDummyTurn : true}
          />
        ))}
      </div>
    ))}
  </div>
)}
```

## Visual Appearance

### North Position (Partner's Dummy):

```
┌──────────────────────────────────────┐
│      North (Dummy)                   │  ← Label
├──────────────────────────────────────┤
│  ┌────────────────────────────────┐  │
│  │  ♠ [A] [K] [Q] [J] [10]       │  │  ← Blue-tinted box
│  │  ♥ [9] [7] [5] [3]            │  │     with border
│  │  ♦ [A] [K] [8]                │  │
│  │  ♣ [Q] [J] [10] [6]           │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
                  ↓
         ┌──────────────┐
         │  GREEN BOX   │  ← Current Trick
         │  (Center)    │
         └──────────────┘
                  ↓
┌──────────────────────────────────────┐
│      South (You) ⬅️ Your turn!       │  ← Your hand
├──────────────────────────────────────┤
│  ♠ [K] [10] [5] [3]                 │
│  ♥ [A] [Q] [J] [8] [5]              │
│  ♦ [9] [6] [2]                      │
│  ♣ [K] [7] [4]                      │
└──────────────────────────────────────┘
```

## When Partner's Cards Appear

### Scenario 1: You Are Declarer
- **Your hand (South):** Visible from start, bottom position
- **Partner (North) is dummy:** Revealed after opening lead
- **Display:** North's cards appear ABOVE green box after opponent plays first card
- **Clickable:** Yes - you control dummy's cards on dummy's turn

### Scenario 2: You Are Defender
- **Your hand (South):** Visible from start, bottom position
- **Opponent's partner is dummy:** Could be North, East, or West
- **Display:** Dummy appears in their position after opening lead
- **Clickable:** No - only declarer controls dummy

## Card Organization

All hands (including dummy) display with **4 rows** organized by suit:
- Row 1: ♠ Spades
- Row 2: ♥ Hearts
- Row 3: ♦ Diamonds
- Row 4: ♣ Clubs

Each suit row has:
- Subtle background highlight (rgba(255, 255, 255, 0.05))
- Cards arranged left-to-right
- 5px gap between cards
- Padding and rounded corners

## Testing the Layout

### Step 1: Refresh Browser
Hard refresh (Cmd+Shift+R) to load new CSS.

### Step 2: Start Game
1. Deal hand
2. Complete bidding
3. Wait 3 seconds for play

### Step 3: Verify Layout

**Before Opening Lead:**
- ✅ Your hand visible at bottom (South)
- ✅ North position shows label only (no cards yet)
- ✅ Green trick box in center is empty

**After Opening Lead (Opponent Plays First Card):**
- ✅ North's dummy hand appears ABOVE green box
- ✅ Dummy hand has blue-tinted background with border
- ✅ Dummy cards organized in 4 rows by suit
- ✅ Dummy label shows "North (Dummy)"
- ✅ Green box shows the first card played
- ✅ Your hand still visible at bottom

### Step 4: Check Interactivity

**If you're declarer:**
- Dummy cards are clickable when it's dummy's turn
- Cards show pointer cursor on hover
- Full color (not faded)

**If you're defender:**
- Dummy cards visible but not clickable
- Cards show not-allowed cursor
- Slightly faded

## Grid Dimensions

**Desktop (default):**
```css
grid-template-columns: 200px 1fr 200px;
grid-template-rows: auto 300px auto;
```

- Columns: 200px (West) | flexible (Center) | 200px (East)
- Rows: auto (North) | 300px (Center/Trick) | auto (South)

**Mobile (< 768px):**
```css
grid-template-columns: 150px 1fr 150px;
grid-template-rows: auto 250px auto;
```

- Narrower side columns
- Shorter center row

## Files Modified

### 1. frontend/src/PlayComponents.css

**Lines 142-172:** Added flexbox centering to all position containers
```css
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
```

**Lines 174-183:** Enhanced position label with spacing
```css
margin-bottom: 10px;
width: 100%;
```

**Lines 374-385:** Enhanced dummy-hand with visual prominence
```css
padding: 10px;
background-color: rgba(97, 218, 251, 0.1);
border: 2px solid rgba(97, 218, 251, 0.3);
width: 100%;
max-width: 600px;
```

## Summary

Partner's cards (North dummy) will now:
- ✅ Display **centered above** the green trick box
- ✅ Appear **after opponent plays first card** (opening lead)
- ✅ Show with **prominent blue background/border**
- ✅ Be **organized by suit** in 4 rows
- ✅ Be **clickable if you're declarer**, disabled if you're defender

The layout properly reflects standard bridge dummy display with North (partner) positioned directly above the center trick area.
