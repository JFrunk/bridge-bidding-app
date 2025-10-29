# East/West Positioning Guide

## Quick Reference for Adjusting East/West Layout

To adjust the positioning of hand analysis boxes and card displays for East and West, edit the CSS variables at **lines 430-448** in `src/App.css`.

### Location in Code
File: `frontend/src/App.css`
Lines: 430-448

### Variables Explained

#### East Position Variables
```css
.player-east {
  /* East hand analysis positioning */
  --east-analysis-margin-left: -100px;  /* Negative = move LEFT (inward) */
  --east-analysis-margin-right: 10px;   /* Space from cards */

  /* East card display positioning */
  --east-cards-margin-left: 0px;        /* Adjust to move cards left/right */
  --east-cards-margin-right: 0px;
}
```

#### West Position Variables
```css
.player-west {
  /* West hand analysis positioning */
  --west-analysis-margin-left: 10px;    /* Space from cards */
  --west-analysis-margin-right: -100px; /* Negative = move RIGHT (inward) */

  /* West card display positioning */
  --west-cards-margin-left: 0px;        /* Adjust to move cards left/right */
  --west-cards-margin-right: 0px;
}
```

## How to Adjust

### Moving Hand Analysis Boxes

**East Hand Analysis:**
- Increase `--east-analysis-margin-left` (more negative) → moves LEFT/inward
- Decrease `--east-analysis-margin-left` (less negative) → moves RIGHT/outward
- Example: `-150px` moves it further left, `-50px` moves it less left

**West Hand Analysis:**
- Increase `--west-analysis-margin-right` (more negative) → moves RIGHT/inward
- Decrease `--west-analysis-margin-right` (less negative) → moves LEFT/outward
- Example: `-150px` moves it further right, `-50px` moves it less right

### Moving Card Displays

**East Cards:**
- Positive `--east-cards-margin-left` → moves cards RIGHT
- Negative `--east-cards-margin-left` → moves cards LEFT
- Example: `20px` moves cards right, `-20px` moves cards left

**West Cards:**
- Positive `--west-cards-margin-left` → moves cards RIGHT
- Negative `--west-cards-margin-left` → moves cards LEFT
- Example: `20px` moves cards right, `-20px` moves cards left

## Current Settings (as of last update)

- **East hand analysis**: `-100px` left (well inside frame)
- **West hand analysis**: `-100px` right (well inside frame)
- **East cards**: `0px` (centered)
- **West cards**: `0px` (centered)

## Tips

1. **Start with small adjustments** (10-20px) and test
2. **Negative values** pull elements inward toward the frame
3. **Positive values** push elements outward away from center
4. **Test on different screen sizes** after making changes
5. Save and refresh browser to see changes

## Example Adjustments

### Make hand analysis more visible (move outward)
```css
--east-analysis-margin-left: -50px;   /* Less negative = more outward */
--west-analysis-margin-right: -50px;  /* Less negative = more outward */
```

### Make hand analysis fit tighter (move inward)
```css
--east-analysis-margin-left: -150px;  /* More negative = more inward */
--west-analysis-margin-right: -150px; /* More negative = more inward */
```

### Shift cards to the right
```css
--east-cards-margin-left: 30px;  /* Moves East cards right */
--west-cards-margin-left: 30px;  /* Moves West cards right */
```
