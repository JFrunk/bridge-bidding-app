# ISSUE: Opener Rebid Overbidding

**Priority:** 5
**Failures:** 5
**Avg Gap:** +4.6 tricks
**Max Gap:** +6 tricks

---

## Problem Summary

Several opener rebid rules are overbidding, especially after conventions like Smolen and negative doubles.

## Failing Rules

| Rule ID | Failures | Avg Gap | File |
|---------|----------|---------|------|
| `opener_accept_smolen_spades` | 1 | +6.0 | sayc_rebids.json |
| `opener_respond_negative_double_hearts` | 1 | +6.0 | sayc_rebids.json |
| `opener_invite_after_single_raise_medium` | 1 | +6.0 | sayc_rebids.json |
| `opener_stayman_show_spades` | 1 | +2.0 | sayc_rebids.json |
| `opener_reject_smolen_spades` | 1 | +3.0 | sayc_rebids.json |

## Example Failures

### opener_accept_smolen_spades (gap +6)
```
Hand 12: 4♠ (gap +6)
Auction: 2♦ - Pass - 3♥ - Pass - 4♠

Opener accepts Smolen transfer to 4♠ but combined strength insufficient
```

### opener_respond_negative_double_hearts (gap +6)
```
Hand 77: 2♥ (gap +6)
Auction: 1♥ - 2♦ - X - Pass - 2♥

Opener rebids 2♥ after partner's negative double
Problem: Partner's negative double may only show 6+ HCP
```

### opener_invite_after_single_raise_medium (gap +6)
```
Hand 129: 3♠ (gap +6)
Auction: 1♠ - X - 2♠ - Pass - 3♠

Opener invites with 3♠ after partner's single raise
Problem: In contested auction, raises are weaker
```

## Root Causes

1. **Smolen rules** - Not checking combined strength
2. **Negative double responses** - Overbidding when partner is minimum
3. **Invites after contested raise** - Not accounting for preemptive nature

## Files to Modify

**`sayc_rebids.json`**

## Proposed Fixes

### Fix 1: Guard Smolen acceptance

```json
{
  "id": "opener_accept_smolen_spades",
  "bid": "4♠",
  "priority": 650,
  "conditions": {
    "is_rebid": true,
    "partner_bid_smolen": true,
    "spades_length": {"min": 3},
    "hcp": {"min": 16}
  },
  "explanation": "Accept Smolen transfer with {hcp} HCP and {spades_length} spades"
}
```

### Fix 2: Conservative negative double response

```json
{
  "id": "opener_respond_negative_double_hearts",
  "bid": "2♥",
  "priority": 650,
  "conditions": {
    "is_rebid": true,
    "partner_last_bid": "X",
    "hearts_length": {"min": 4},
    "hcp": {"min": 12, "max": 16}
  },
  "explanation": "Show hearts after negative double with minimum opener"
}
```

### Fix 3: Cautious invite after contested raise

```json
{
  "id": "opener_invite_after_single_raise_medium",
  "bid": "3{first_suit}",
  "priority": 540,
  "conditions": {
    "is_rebid": true,
    "partner_raised": true,
    "is_contested": false,
    "hcp": {"min": 16, "max": 18}
  },
  "explanation": "Invite with {hcp} HCP after partner's raise"
}
```

### Fix 4: Add pass option after contested raise

```json
{
  "id": "opener_pass_after_contested_raise",
  "bid": "Pass",
  "priority": 200,
  "conditions": {
    "is_rebid": true,
    "partner_raised": true,
    "is_contested": true,
    "hcp": {"max": 16}
  },
  "explanation": "Pass - partner's raise was preemptive"
}
```

## Test Commands

```bash
# Test Smolen acceptance
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()

# 1NT opener after 2D - 3H (Smolen)
hand = Hand.from_pbn('J87.AK5.KQ32.A94')  # 17 HCP, 3 spades
auction = ['2♦', 'Pass', '3♥', 'Pass']
bid, exp = engine.get_next_bid(hand, auction, 'North', 'None', 'detailed', 'North')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: 4♠ if fit, 3NT otherwise')
"

# Test invite after contested raise
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()

# After 1♠ - X - 2♠
hand = Hand.from_pbn('AKJ87.Q5.KJ32.94')  # 15 HCP
auction = ['1♠', 'X', '2♠', 'Pass']
bid, exp = engine.get_next_bid(hand, auction, 'South', 'None', 'detailed', 'South')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: Pass (partner s raise was competitive/preemptive)')
"
```

## Success Criteria

- Smolen acceptance requires 16+ HCP
- Negative double responses stay at lowest level with minimum
- No invites after contested/preemptive raises
- Opener rebid failures reduced from 5 to 0

## Verification

After fixes, run:
```bash
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep "opener"
```
