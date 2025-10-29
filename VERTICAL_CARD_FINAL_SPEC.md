# Vertical Card Display - FINAL SPECIFICATION

## Requirements (User Confirmed)

1. **ALL cards show 20px visible** (80% overlap) - INCLUDING FIRST CARD
2. **EXCEPT last card** - shows FULLY (100px)
3. **NO exceptions** - same overlap for all suits

## Math

- Card height: **100px**
- 80% overlap = show only **20px** of each card
- Margin-top needed: **-80px**

## Visual Representation

```
Container top (clip here ↓)
══════════════════════════
│ K♠       │ ← Card 1 (20px visible - top is CLIPPED)
├══════════┤
│ 10♠      │ ← Card 2 (20px visible)
├══════════┤
│ 4♠       │ ← Card 3 (20px visible)
├══════════┤
│ 2♠       │ ← Card 4 (20px visible) [END SPADES]
├══════════┤
│ Q♥       │ ← Card 5 (20px visible) [START HEARTS - NO GAP!]
├══════════┤
│ 9♥       │ ← Card 6 (20px visible)
├══════════┤
│ 7♥       │ ← Card 7 (20px visible)
├══════════┤
│ 6♥       │ ← Card 8 (20px visible)
├══════════┤
    ...
├══════════┤
│ 4♦       │ ← Card 13 (LAST - 100px visible, FULL)
│          │
│    ♦     │
│          │
│       ♦4 │
└══════════┘
Container bottom
```

## CSS Implementation

### Strategy:
1. Apply **-80px margin-top to ALL cards** (no exceptions)
2. Use **overflow: hidden** on container
3. Add **padding-top: 0** to ensure first card is clipped
4. Calculate **exact container height** to show last card fully

### Height Calculation:
- **Cards 1-12**: 20px each = 12 × 20px = 240px
- **Last card (13)**: 100px (full)
- **Total container height**: 240px + 100px = **340px**

### CSS:

```css
.player-east .hand-display,
.player-west .hand-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  max-width: 100px;
  padding: 10px;
  padding-top: 0;  /* No top padding - clip first card */
  padding-bottom: 10px;
  background-color: rgba(97, 218, 251, 0.1);
  border-radius: 8px;
  border: 2px solid rgba(97, 218, 251, 0.3);
  overflow: hidden; /* Clip first card's top */
  max-height: 360px; /* 240px (12 cards × 20px) + 100px (last card) + 20px padding */
}

/* ALL cards get 80% overlap - NO EXCEPTIONS */
.player-east .suit-group > div,
.player-west .suit-group > div {
  margin-top: -80px; /* 80% overlap everywhere */
}

/* REMOVE this rule - first card should also be overlapped */
/* .player-east .hand-display .suit-group:first-child > div:first-child,
.player-west .hand-display .suit-group:first-child > div:first-child {
  margin-top: 0;
} */
```

## Expected Result

### Visual:
✅ **Card 1**: 20px visible (top 80px clipped by container)
✅ **Cards 2-12**: 20px visible each (80% overlapped)
✅ **Card 13**: 100px visible (fully displayed)
✅ **No gaps** between suits
✅ **Total height**: ~360px (very compact!)

### User sees:
```
[K♠      ] ← 20px
[10♠     ] ← 20px
[4♠      ] ← 20px
[2♠      ] ← 20px
[Q♥      ] ← 20px
[9♥      ] ← 20px
...
[4♦      ] ← 100px (FULL)
[   ♦    ]
[     ♦4 ]
```

Perfect consistency - every card except the last shows exactly 20px!
