# Vertical Card Fix - Visual Diagram

## CURRENT PROBLEM (From Screenshot)

Cards appear as thin horizontal lines:
```
┌──────────────┐
│ K♠2          │ ← Thin line (~20px tall, 100px wide)
├──────────────┤
│ 10♠          │ ← Thin line
├──────────────┤
│ 4♠           │ ← Thin line
├──────────────┤
│ 2♠           │ ← Thin line
└──────────────┘
```

**Why?** The `display: contents` on `.suit-group` is removing the flex container structure, causing cards to collapse into thin strips.

## THE FIX

### Remove `display: contents` and restore proper flex structure:

```css
/* Container */
.player-east .hand-display,
.player-west .hand-display {
  display: flex;
  flex-direction: column;
  align-items: center;        /* ← Center cards */
  max-width: 100px;
  max-height: 350px;
  padding: 0 10px 10px;
  overflow: hidden;
}

/* Suit groups are flex containers */
.player-east .suit-group,
.player-west .suit-group {
  display: flex;               /* ← NOT contents! */
  flex-direction: column;      /* ← Stack vertically */
  align-items: center;         /* ← Center each card */
}

/* Cards get overlap */
.player-east .suit-group > div,
.player-west .suit-group > div {
  margin-top: -80px;
}

/* First card gets no overlap */
.player-east .hand-display > .suit-group:first-child > div:first-child,
.player-west .hand-display > .suit-group:first-child > div:first-child {
  margin-top: 0;
}
```

## VISUAL RESULT

```
Container (100px wide, 350px tall, overflow hidden)
┌─────────────────────────┐
│  ┌──────────┐           │ ← First card: margin-top: 0
│  │ K♠       │           │   (full 100px height visible)
│  │          │           │
│  │    ♠     │           │
│  │          │           │
│  │       ♠K │           │
│  └──────────┘           │
│  ┌──────────┐           │ ← Card 2: margin-top: -80px
│  │ 10♠      │           │   (only 20px visible)
│  ├══════════┤           │
│  │ 4♠       │           │ ← Card 3: margin-top: -80px
│  ├══════════┤           │
│  │ 2♠       │           │ ← Card 4 (end of spades)
│  ├══════════┤           │
│  │ Q♥       │           │ ← Card 5 (hearts start - no gap!)
│  ├══════════┤           │
│  │ 9♥       │           │
│  ├══════════┤           │
│     ...                 │
│  ├══════════┤           │
│  │ 6♦       │           │ ← Last card (shows fully)
│  │    ♦     │           │
│  │       ♦6 │           │
│  └──────────┘           │
└─────────────────────────┘
```

## KEY DIFFERENCES

### BEFORE (Broken with `display: contents`):
```
hand-display
  ├─ card 1 (K♠)   ← No container structure
  ├─ card 2 (10♠)  ← Cards collapse
  ├─ card 3 (4♠)   ← Into thin lines
  └─ card 4 (2♠)
```

### AFTER (Fixed with proper flex):
```
hand-display (flex column)
  ├─ suit-group (flex column)
  │   ├─ card 1 (K♠)     margin-top: 0
  │   ├─ card 2 (10♠)    margin-top: -80px
  │   ├─ card 3 (4♠)     margin-top: -80px
  │   └─ card 4 (2♠)     margin-top: -80px
  │
  ├─ suit-group (flex column)
  │   ├─ card 5 (Q♥)     margin-top: -80px
  │   └─ ...
```

## MEASUREMENTS

- **Card dimensions**: 70px wide × 100px tall
- **Container**: 100px wide (70px card + 15px padding each side)
- **Each card visible**: 20px (except first: 100px, last: 100px)
- **Total height**: ~350px
  - First card: 100px
  - Cards 2-12: 11 × 20px = 220px
  - Last card: 100px
  - Padding: 10px
  - Total: 100 + 220 + 100 + 10 = 430px
  - Container clips at 350px to show last card partially

## IMPLEMENTATION

The fix requires:
1. ✅ Remove `display: contents`
2. ✅ Add `flex-direction: column` to suit-groups
3. ✅ Add `align-items: center` to center cards
4. ✅ Add special rule for first card (margin-top: 0)

This will make cards render as proper vertical playing cards with 80% overlap!
