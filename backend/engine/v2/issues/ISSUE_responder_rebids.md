# ISSUE: Responder Rebid Overbidding

**Priority:** 3
**Failures:** 25
**Avg Gap:** +3.5 tricks
**Max Gap:** +9 tricks

---

## Problem Summary

Responder rebid rules are too aggressive, bidding game with insufficient combined strength.

## Failing Rules

| Rule ID | Failures | Avg Gap | File |
|---------|----------|---------|------|
| `responder_3nt_balanced` | 17 | +2.9 | sayc_responder_rebids.json |
| `responder_game_in_spades_with_fit` | 5 | +4.6 | sayc_responder_rebids.json |
| `responder_game_in_major_with_fit` | 2 | +4.5 | sayc_responder_rebids.json |
| `responder_5_minor_game` | 1 | +9.0 | sayc_responder_rebids.json |

## Example Failures

### responder_3nt_balanced (17 failures)
```
Hand 87: 3NT (gap +4)
Auction: 1♣ - X - 1♦ - 1NT - 3NT

Combined HCP: ~22 (needs 25-26 for 3NT)
```

### responder_game_in_spades_with_fit (5 failures)
```
Hand 132: 4♠ (gap +5)
Auction: 1♦ - X - 1♠ - 2♦ - 4♠

Responder has ~10 HCP, partner showed minimum
```

### responder_5_minor_game (1 failure, gap +9)
```
Hand 36: 5♦ (gap +9)
Auction: 2♦ - Pass - 3♦ - 4♦ - Pass - Pass - 5♦

Responder competes to 5♦ in a losing cause
```

## Root Causes

1. **responder_3nt_balanced** - HCP threshold too low (likely 10-11, should be 13+)
2. **responder_game_in_spades_with_fit** - Not checking opener's range
3. **responder_5_minor_game** - Competing too high without fit/values

## Files to Modify

**`sayc_responder_rebids.json`**

## Current Rules (to be fixed)

### responder_3nt_balanced
Current likely conditions:
```json
{
  "id": "responder_3nt_balanced",
  "conditions": {
    "is_responder_rebid": true,
    "hcp": {"min": 10},  // TOO LOW
    "is_balanced": true
  }
}
```

### responder_game_in_spades_with_fit
Current likely conditions:
```json
{
  "id": "responder_game_in_spades_with_fit",
  "conditions": {
    "is_responder_rebid": true,
    "support_for_partner": {"min": 4},
    "support_points": {"min": 12}  // TOO LOW
  }
}
```

## Proposed Fixes

### Fix 1: Increase HCP for responder_3nt_balanced

```json
{
  "id": "responder_3nt_balanced",
  "bid": "3NT",
  "priority": 450,
  "conditions": {
    "is_responder_rebid": true,
    "hcp": {"min": 13},
    "is_balanced": true,
    "stopper_count": {"min": 3}
  },
  "explanation": "3NT with {hcp} HCP balanced and stoppers"
}
```

### Fix 2: Require opener extras for responder_game_in_spades_with_fit

```json
{
  "id": "responder_game_in_spades_with_fit",
  "bid": "4♠",
  "priority": 460,
  "conditions": {
    "is_responder_rebid": true,
    "agreed_suit": "♠",
    "support_for_partner": {"min": 4},
    "hcp": {"min": 10},
    "support_points": {"min": 13},
    "partner_showed_extras": true
  },
  "explanation": "Game in spades with fit and values"
}
```

### Fix 3: Limit responder_5_minor_game

```json
{
  "id": "responder_5_minor_game",
  "bid": "5{agreed_minor}",
  "priority": 440,
  "conditions": {
    "is_responder_rebid": true,
    "agreed_suit": {"in": ["♣", "♦"]},
    "hcp": {"min": 13},
    "support_for_partner": {"min": 5},
    "is_competitive": false
  },
  "explanation": "5-level minor game with {hcp} HCP and {support_for_partner} support"
}
```

### Fix 4: Add conservative pass rules

```json
{
  "id": "responder_rebid_pass_minimum",
  "bid": "Pass",
  "priority": 200,
  "conditions": {
    "is_responder_rebid": true,
    "hcp": {"max": 11},
    "partner_limited": true
  },
  "explanation": "Pass with {hcp} HCP - partner showed minimum"
}
```

## Test Commands

```bash
# Test responder_3nt_balanced with 10 HCP
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()

# 10 HCP balanced
hand = Hand.from_pbn('KJ5.Q86.KT32.J94')
auction = ['1♣', 'X', '1♦', '1NT']
bid, exp = engine.get_next_bid(hand, auction, 'South', 'None', 'detailed', 'North')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: Pass or 2NT (invitational), NOT 3NT')
"

# Test game in spades with minimum opener
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()

# 10 HCP with 4 spades
hand = Hand.from_pbn('KJ87.Q6.K532.J94')
auction = ['1♦', 'X', '1♠', '2♦']
bid, exp = engine.get_next_bid(hand, auction, 'South', 'None', 'detailed', 'North')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: 2♠ or 3♠ (invitational), NOT 4♠')
"
```

## Success Criteria

- `responder_3nt_balanced` failures reduced from 17 to < 5
- Game raises require opener showing extras or combined 25+ points
- No 5-level bids in competitive auctions with < 13 HCP
- Overall responder rebid failures reduced from 25 to < 8

## Verification

After fixes, run:
```bash
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep "responder"
```
