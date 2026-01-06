# ISSUE: Preempt Raise Overbidding

**Priority:** 4
**Failures:** 4
**Avg Gap:** +5.4 tricks
**Max Gap:** +9 tricks

---

## Problem Summary

Raises of partner's preempt are too aggressive, especially at the 5-level for minors.

## Failing Rules

| Rule ID | Failures | Avg Gap | File |
|---------|----------|---------|------|
| `raise_partner_club_preempt_to_5` | 2 | +7.5 | sayc_preempts.json |
| `raise_partner_preempt_to_game` | 1 | +4.0 | sayc_preempts.json |
| `raise_partner_spade_preempt_to_game` | 1 | +3.0 | sayc_preempts.json |

## Example Failures

### raise_partner_club_preempt_to_5 (gap +9)
```
Hand 25: 5♣ (gap +9)
Auction: 1♣ - X - 3♣ - Pass - 5♣

East raises partner's preemptive 3♣ to 5♣
Combined: Can only make 2 tricks
```

### raise_partner_preempt_to_game (gap +4)
```
Hand 152: 4♥ (gap +4)
Auction: 2♥ - X - 4♥

North raises partner's weak 2♥ to game after RHO doubles
Problem: Partner's preempt is weak (6-10 HCP), combined insufficient
```

## Root Causes

1. **5-level minor raises** - No HCP requirement
2. **Game raises after double** - Not accounting for weak preempt range
3. **Law of Total Tricks** - Not properly applied

## Files to Modify

**`sayc_preempts.json`**

## Proposed Fixes

### Fix 1: Require HCP for 5-level minor raise

```json
{
  "id": "raise_partner_club_preempt_to_5",
  "bid": "5♣",
  "priority": 350,
  "conditions": {
    "partner_preempted": true,
    "partner_suit": "♣",
    "hcp": {"min": 10},
    "support_for_partner": {"min": 4},
    "is_competitive": false
  },
  "explanation": "Raise to 5♣ with {hcp} HCP and {support_for_partner} clubs"
}
```

### Fix 2: Conservative game raise of preempt

```json
{
  "id": "raise_partner_preempt_to_game",
  "bid": "4{partner_suit}",
  "priority": 340,
  "conditions": {
    "partner_preempted": true,
    "partner_suit": {"in": ["♥", "♠"]},
    "OR": [
      {
        "hcp": {"min": 14},
        "support_for_partner": {"min": 3}
      },
      {
        "hcp": {"min": 10},
        "support_for_partner": {"min": 4},
        "is_competitive": false
      }
    ]
  },
  "explanation": "Game raise with {hcp} HCP and support"
}
```

### Fix 3: Add Law of Total Tricks consideration

```json
{
  "id": "raise_preempt_competitive_lott",
  "bid": "4{partner_suit}",
  "priority": 330,
  "description": "Competitive raise based on Law of Total Tricks",
  "conditions": {
    "partner_preempted": true,
    "partner_suit": {"in": ["♥", "♠"]},
    "is_contested": true,
    "support_for_partner": {"min": 4},
    "total_trumps": {"min": 10}
  },
  "explanation": "Competitive raise with {support_for_partner} trumps (LOTT)"
}
```

### Fix 4: Pass with weak hand after preempt

```json
{
  "id": "pass_after_partner_preempt_weak",
  "bid": "Pass",
  "priority": 100,
  "conditions": {
    "partner_preempted": true,
    "hcp": {"max": 9},
    "support_for_partner": {"max": 2}
  },
  "explanation": "Pass with {hcp} HCP - insufficient for action"
}
```

## Test Commands

```bash
# Test 5♣ raise
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()

# Hand after 1♣ - X - 3♣
hand = Hand.from_pbn('J7.652.K98.QJ765')  # 8 HCP, 5 clubs
auction = ['1♣', 'X', '3♣', 'Pass']
bid, exp = engine.get_next_bid(hand, auction, 'East', 'None', 'detailed', 'North')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: Pass (not 5♣)')
"

# Test game raise of weak 2
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()

# Hand after 2♥ - X
hand = Hand.from_pbn('K87.Q65.J32.J984')  # 7 HCP, 3 hearts
auction = ['2♥', 'X']
bid, exp = engine.get_next_bid(hand, auction, 'North', 'None', 'detailed', 'South')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: 3♥ (preemptive) or Pass, NOT 4♥')
"
```

## Success Criteria

- 5-level raises require 10+ HCP
- Game raises of preempts require 14+ HCP or 10+ with 4-card support
- Preempt raise failures reduced from 4 to 0

## Verification

After fixes, run:
```bash
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep "preempt"
```
