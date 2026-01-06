# ISSUE: V1 Fallback Overbidding

**Priority:** 1 (Highest)
**Failures:** 78 (40% of all overbids)
**Avg Gap:** +4.2 tricks
**Max Gap:** +10 tricks

---

## Problem Summary

When V2 schema has no matching rule, the engine falls back to V1 which is too aggressive, especially in competitive auctions after takeout doubles.

## Root Cause

Missing V2 schema rules for:
1. Weak hand passes after partner opens and RHO doubles
2. Weak hand passes after partner preempts
3. Competitive auction passes with insufficient values

## Failing Patterns

### Pattern 1: Game raise after takeout double (most common)
```
Auction: 1♠ - X - 4♠
South hand: ♠K65 ♥9872 ♦T52 ♣643 (4 HCP, 3 spades)
Expected: Pass
Actual: 4♠ (V1 fallback)
Gap: +10
```

### Pattern 2: Preempt response overbid
```
Auction: 2♠ - Pass - 4♥
South hand: ♠T ♥KQJ7542 ♦9754 ♣K (weak, long hearts)
Expected: Pass or 3♥
Actual: 4♥ (V1 fallback)
Gap: +9
```

### Pattern 3: Competitive continuation
```
Auction: 1♥ - X - 4♥
North hand: ♠AK4 ♥KQ842 ♦T43 ♣QT (opener rebids game)
Problem: V1 rebids game without fit confirmation
```

## Files to Modify

1. **`sayc_interference.json`** - Add pass rules for weak hands
2. **`sayc_responses.json`** - Add pass after partner opens + RHO doubles

## Proposed Fixes

### Fix 1: Add pass rule for weak hand after partner opens + RHO doubles

Add to `sayc_interference.json`:
```json
{
  "id": "pass_weak_after_partner_opened_doubled",
  "bid": "Pass",
  "priority": 50,
  "description": "Pass with weak hand after partner opens and RHO doubles",
  "conditions": {
    "is_response": true,
    "is_contested": true,
    "opener_relationship": "Partner",
    "rho_last_bid": "X",
    "hcp": {"max": 5}
  },
  "forcing": "none",
  "explanation": "Pass with {hcp} HCP - too weak to act over double",
  "sets_forcing_level": "NON_FORCING"
}
```

### Fix 2: Add pass rule for minimum hand after partner opens + RHO doubles

Add to `sayc_interference.json`:
```json
{
  "id": "pass_minimum_no_fit_after_double",
  "bid": "Pass",
  "priority": 45,
  "description": "Pass with minimum and no fit after RHO doubles",
  "conditions": {
    "is_response": true,
    "is_contested": true,
    "opener_relationship": "Partner",
    "rho_last_bid": "X",
    "hcp": {"min": 6, "max": 9},
    "support_for_partner": {"max": 2}
  },
  "forcing": "none",
  "explanation": "Pass with {hcp} HCP and only {support_for_partner} trumps",
  "sets_forcing_level": "NON_FORCING"
}
```

### Fix 3: Expand preemptive jump raise conditions

Current `jump_raise_after_interference` only matches certain conditions. Add:
```json
{
  "id": "pass_weak_preemptive_situation",
  "bid": "Pass",
  "priority": 40,
  "description": "Pass with weak hand in preemptive situation",
  "conditions": {
    "is_response": true,
    "is_contested": true,
    "hcp": {"max": 5},
    "support_for_partner": {"max": 3}
  },
  "forcing": "none",
  "explanation": "Pass - insufficient values for action",
  "sets_forcing_level": "NON_FORCING"
}
```

## Test Commands

```bash
# Test weak hand after 1♠ - X
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()
hand = Hand.from_pbn('K65.9872.T52.643')  # 4 HCP
bid, exp = engine.get_next_bid(hand, ['1♠', 'X'], 'South', 'None', 'detailed', 'North')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: Pass')
"

# Test minimum hand no fit after 1♥ - X
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()
hand = Hand.from_pbn('QJ87.65.KT32.J94')  # 7 HCP, 2 hearts
bid, exp = engine.get_next_bid(hand, ['1♥', 'X'], 'South', 'None', 'detailed', 'North')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: Pass or 1♠')
"
```

## Success Criteria

- V1 fallback count reduced from 78 to < 20
- All weak hands (< 6 HCP) pass in competitive auctions
- Minimum hands without fit pass after doubles

## Verification

After fixes, run:
```bash
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep "v1_fallback"
```

Expected: Significantly fewer v1_fallback entries
