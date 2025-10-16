# Score Breakdown Feature - Visual Mockup

## Before Expansion (Default State)

```
┌─────────────────────────────────────────────────┐
│              Hand Complete!                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Contract:        4♠X by N                     │
│                                                 │
│  Tricks Taken:    10                           │
│                                                 │
│  Result:          Made ✓                       │
│                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  Score:                         +590    ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  📊 How was this calculated?      ▼    │   │  ← Click to expand
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Session Standings: NS 590 vs EW 0            │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ New Hand to Bid  │  │  📊 My Progress  │   │
│  └──────────────────┘  └──────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │              Close                      │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## After Expansion (Showing Breakdown)

```
┌─────────────────────────────────────────────────┐
│              Hand Complete!                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Contract:        4♠X by N                     │
│                                                 │
│  Tricks Taken:    10                           │
│                                                 │
│  Result:          Made ✓                       │
│                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  Score:                         +590    ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  📊 How was this calculated?      ▲    │   │  ← Click to collapse
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  Score Breakdown                        │   │
│  │                                          │   │
│  │  Contract Tricks            +240        │   │
│  │    4♠ doubled: 4 × 30 × 2              │   │
│  │                                          │   │
│  │  Double Bonus               +50         │   │
│  │    For making doubled contract          │   │
│  │                                          │   │
│  │  Game Bonus                 +300        │   │
│  │    Made game (trick score ≥ 100),      │   │
│  │    not vulnerable                       │   │
│  │                                          │   │
│  │  Overtricks (0)             +0          │   │
│  │                                          │   │
│  │  ─────────────────────────────────      │   │
│  │  Total Score                +590        │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Session Standings: NS 590 vs EW 0            │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ New Hand to Bid  │  │  📊 My Progress  │   │
│  └──────────────────┘  └──────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │              Close                      │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Example: Defeated Contract (Down 2, Doubled, Vulnerable)

```
┌─────────────────────────────────────────────────┐
│              Hand Complete!                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Contract:        3NTX by S                    │
│                                                 │
│  Tricks Taken:    7                            │
│                                                 │
│  Result:          Down 2 ✗                     │
│                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  Score:                         -500    ┃  │ (red text)
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  📊 How was this calculated?      ▲    │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  Score Breakdown                        │   │
│  │                                          │   │
│  │  Contract Failed (Down 2)   -500        │   │
│  │    2 undertricks doubled, vulnerable    │   │
│  │                                          │   │
│  │    • First undertrick: 200              │   │
│  │    • Next 1 undertrick: 1 × 300         │   │
│  │                                          │   │
│  │  ─────────────────────────────────      │   │
│  │  Total Penalty              -500        │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Session Standings: NS 590 vs EW 500          │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ New Hand to Bid  │  │  📊 My Progress  │   │
│  └──────────────────┘  └──────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │              Close                      │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Example: Grand Slam with Honors

```
┌─────────────────────────────────────────────────┐
│              Hand Complete!                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Contract:        7♥ by S                      │
│                                                 │
│  Tricks Taken:    13                           │
│                                                 │
│  Result:          Made +1 ✓                    │
│                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  Score:                        +2240    ┃  │ (green text)
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  📊 How was this calculated?      ▲    │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  Score Breakdown                        │   │
│  │                                          │   │
│  │  Contract Tricks            +210        │   │
│  │    7♥: 7 tricks × 30                   │   │
│  │                                          │   │
│  │  Game Bonus                 +500        │   │
│  │    Made game (trick score ≥ 100),      │   │
│  │    vulnerable                           │   │
│  │                                          │   │
│  │  Grand Slam Bonus          +1500        │   │
│  │    7-level contract, vulnerable         │   │
│  │                                          │   │
│  │  Overtricks (1)             +30         │   │
│  │    1 extra trick × 30                   │   │
│  │                                          │   │
│  │  Honors Bonus               +150        │   │
│  │    All 5 trump honors                   │   │
│  │    (A-K-Q-J-10 of ♥) in one hand       │   │
│  │                                          │   │
│  │  ─────────────────────────────────      │   │
│  │  Total Score               +2390        │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Session Standings: NS 2390 vs EW 500         │
│                                                 │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ New Hand to Bid  │  │  📊 My Progress  │   │
│  └──────────────────┘  └──────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │              Close                      │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Color Scheme

- **Positive scores**: Green text (#22c55e)
- **Negative scores**: Red text (#ef4444)
- **Background**: Light gray (#f9fafb)
- **Border**: Gray (#e5e7eb)
- **Button**: Blue text (#2563eb) with hover effect
- **Total line**: Bold with top border separator

## Typography

- **Score total**: 3xl (30px), bold
- **Breakdown items**: Base (16px), medium weight
- **Explanations**: Small (14px), gray
- **Total in breakdown**: 2xl (24px), bold

## Interaction

1. **Click button** → Smooth expand animation (0.3s)
2. **Breakdown appears** → Fade in effect
3. **Chevron flips** → Down ▼ becomes Up ▲
4. **Click again** → Smooth collapse animation
5. **Breakdown hides** → Fade out effect
6. **Chevron flips back** → Up ▲ becomes Down ▼

## Mobile Responsive

On smaller screens:
- Font sizes scale down slightly
- Padding reduces
- Button spans full width
- Two-column layout becomes single column
- Still fully readable and usable
