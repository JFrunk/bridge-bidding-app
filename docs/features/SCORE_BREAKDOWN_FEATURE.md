# Score Breakdown Feature - Implementation Plan

## Overview
Add a "How was this calculated?" expandable section to the ScoreModal that shows the detailed scoring breakdown after a hand is complete.

## Current State
✅ **Backend already provides all necessary data:**
- `/api/complete-play` returns a `breakdown` object with:
  - `trick_score` - Base points for making tricks
  - `game_bonus` - Bonus for making game (or part-score)
  - `slam_bonus` - Bonus for small/grand slam
  - `overtrick_score` - Points for extra tricks
  - `double_bonus` - Bonus for doubled/redoubled contracts (50 or 100)
  - `honors_bonus` - Bonus for holding honors (optional)
  - `penalty` - For defeated contracts

✅ **Frontend already receives this data** in the ScoreModal component

## What Needs to Be Built

### 1. Enhanced ScoreModal Component
**File:** `frontend/src/components/play/ScoreModal.jsx`

**Changes needed:**
- Add a collapsible "Show calculation" button/accordion
- Display the breakdown in a clear, itemized format
- Use simple language (not bridge jargon)
- Add tooltips or brief explanations for each component

### 2. Component Structure

```jsx
<ScoreModal>
  {/* Existing content: Contract, Tricks, Result, Score */}

  {/* NEW: Expandable breakdown section */}
  <Collapsible>
    <CollapsibleTrigger>
      <Button variant="ghost">
        📊 How was this calculated?
      </Button>
    </CollapsibleTrigger>

    <CollapsibleContent>
      <ScoreBreakdown
        breakdown={scoreData.breakdown}
        contract={scoreData.contract}
        made={scoreData.made}
        overtricks={scoreData.overtricks}
        undertricks={scoreData.undertricks}
      />
    </CollapsibleContent>
  </Collapsible>
</ScoreModal>
```

### 3. New ScoreBreakdown Component
**File:** `frontend/src/components/play/ScoreBreakdown.jsx`

**Displays:**
- **For Made Contracts:**
  ```
  Contract Tricks:        +240  (4♠ doubled: 4 × 30 × 2)
  Double Bonus:           +50   (For accepting the double)
  Game Bonus:             +300  (Making game, not vulnerable)
  Overtricks:             +0    (No overtricks)
  Honors:                 +0    (No honors held)
  ─────────────────────────────
  Total Score:            +590
  ```

- **For Defeated Contracts:**
  ```
  Contract Failed:        -100
  ─────────────────────────────
  Breakdown:
  • Down 1, doubled, not vulnerable = 100 penalty per trick
  ─────────────────────────────
  Total Penalty:          -100
  ```

### 4. User-Friendly Explanations

Add tooltips or help text:
- **Contract Tricks**: "Points earned for making your contracted number of tricks"
- **Double Bonus**: "Extra points for making a contract that was doubled"
- **Game Bonus**: "Bonus for making game (trick score ≥ 100 points)"
- **Slam Bonus**: "Bonus for bidding and making 6 or 7-level contracts"
- **Overtricks**: "Extra points for tricks beyond your contract"
- **Honors**: "Bonus for holding high cards in trump (A, K, Q, J, 10)"

## Implementation Steps

### Step 1: Install/Use Collapsible Component
The project uses shadcn/ui components. Need to add Collapsible:

```bash
cd frontend
npx shadcn@latest add collapsible
```

### Step 2: Create ScoreBreakdown Component
Create new file with proper formatting and tooltips.

### Step 3: Update ScoreModal
Integrate the new breakdown section into the existing modal.

### Step 4: Add CSS Styling
Create accompanying CSS file for clean presentation.

### Step 5: Test with Different Scenarios
- Making contracts (undoubled, doubled, redoubled)
- Down contracts (various undertricks)
- Slams
- Honors bonuses
- Part-scores vs games

## Estimated Effort

- **Backend work**: ✅ Already complete (0 hours)
- **Frontend component**: 2-3 hours
  - ScoreBreakdown component: 1 hour
  - ScoreModal integration: 30 minutes
  - CSS styling: 30 minutes
  - Testing: 30 minutes
  - Tooltips/help text: 30 minutes
- **Total**: ~3 hours

## Design Mockup (Text Version)

```
┌─────────────────────────────────────────────────┐
│           Hand Complete!                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  Contract:    4♠X by N                         │
│  Tricks:      10                                │
│  Result:      Made ✓                           │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │  Score: +590                              │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  [ 📊 How was this calculated? ▼ ]            │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ Score Breakdown:                          │ │
│  │                                            │ │
│  │ Contract Tricks     +240 ⓘ               │ │
│  │   4♠ doubled: 4 × 30 × 2                 │ │
│  │                                            │ │
│  │ Double Bonus        +50  ⓘ               │ │
│  │   For making doubled contract             │ │
│  │                                            │ │
│  │ Game Bonus          +300 ⓘ               │ │
│  │   Made game (not vulnerable)              │ │
│  │                                            │ │
│  │ ─────────────────────────────              │ │
│  │ Total               +590                   │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  Session Standings: NS 590 vs EW 0            │
│                                                 │
│  [ New Hand to Bid ]  [ 📊 My Progress ]      │
│  [ Close ]                                      │
└─────────────────────────────────────────────────┘
```

## Benefits

1. **Educational** - Users learn how bridge scoring works
2. **Transparent** - No "magic numbers", everything is explained
3. **Senior-friendly** - Large text, clear labels, optional (collapsed by default)
4. **Debugging** - Helps verify scoring is correct
5. **Engagement** - Increases understanding and interest in the game

## Alternative: Simple Tooltip Approach

If you want something even simpler (15 minutes):
- Just add a tooltip to the Score number that shows the breakdown
- Less code, less UI complexity
- But less visible and educational

## Next Steps

Would you like me to:
1. **Implement the full feature** (~3 hours) with expandable breakdown?
2. **Create just the tooltip version** (~15 minutes) for quick wins?
3. **Create a mockup first** to review the design?
