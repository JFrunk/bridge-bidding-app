# ISSUE: RKCB/Slam Overbidding

**Priority:** 2
**Failures:** 13
**Avg Gap:** +4.5 tricks
**Max Gap:** +10 tricks

---

## Problem Summary

Slam bidding rules trigger without sufficient combined strength, leading to 6-level contracts that can only make 2-4 tricks.

## Failing Rules

| Rule ID | Failures | Avg Gap | File |
|---------|----------|---------|------|
| `queen_ask_positive` | 6 | +4.8 | sayc_rkcb.json |
| `slam_after_rkcb_5d_hearts` | 4 | +5.8 | sayc_rkcb.json |
| `signoff_6_after_rkcb` | 3 | +3.3 | sayc_rkcb.json |
| `bid_slam_all_keycards` | 4 | +3.0 | sayc_slam_controls.json |
| `slam_brake_denied_control` | 3 | +4.3 | sayc_slam_controls.json |

## Worst Example

```
Hand 68: 6♥ by East (gap +10)
Auction: 1NT - 2♦ - 2♥ - 4♥ - 4NT - 5♦ - 6♥
Rule: slam_after_rkcb_5d_hearts

East: ♠J96 ♥KQJ53 ♦KJ ♣KQ6 (17 HCP)
West: ♠AQ732 ♥T72 ♦A3 ♣J82 (12 HCP)
Combined: 29 HCP

North: ♠T84 ♥6 ♦AQ6 ♣AT8652 (12 HCP)
South: ♠K52 ♥A984 ♦98742 ♣3 (5 HCP)

DDS: Can only make 2 tricks in hearts (opponents have all the defensive tricks)
```

**Problem:** After Jacoby transfer, responder jumps to 4♥ showing game values but NOT slam interest. Opener shouldn't bid Blackwood.

## Root Causes

1. **No HCP guard on Blackwood initiation** - Anyone can bid 4NT
2. **No combined strength check** - Slam bid with 29 HCP when 33+ needed
3. **Blackwood after Jacoby transfer** - 4♥ is a signoff, not slam try

## Files to Modify

1. **`sayc_rkcb.json`** - Add HCP requirements to slam rules
2. **`sayc_slam_controls.json`** - Add combined strength checks

## Proposed Fixes

### Fix 1: Add HCP requirement to slam after RKCB

In `sayc_rkcb.json`, modify `slam_after_rkcb_5d_hearts`:
```json
{
  "id": "slam_after_rkcb_5d_hearts",
  "bid": "6♥",
  "priority": 910,
  "conditions": {
    "partner_last_bid": "5♦",
    "asked_blackwood": true,
    "hcp": {"min": 17},
    "agreed_suit": "♥"
  },
  "explanation": "Bid 6♥ with {hcp} HCP after partner shows 1 or 4 keycards"
}
```

### Fix 2: Add HCP requirement to queen ask positive

In `sayc_rkcb.json`, modify `queen_ask_positive`:
```json
{
  "id": "queen_ask_positive",
  "bid": "6{agreed_suit}",
  "priority": 905,
  "conditions": {
    "partner_asked_queen": true,
    "has_trump_queen": true,
    "hcp": {"min": 12}
  },
  "explanation": "Show trump queen with {hcp} HCP"
}
```

### Fix 3: Prevent Blackwood after Jacoby transfer signoff

Add to `sayc_rkcb.json`:
```json
{
  "id": "no_blackwood_after_transfer_signoff",
  "bid": "Pass",
  "priority": 950,
  "description": "Do not bid Blackwood after partner's transfer signoff",
  "conditions": {
    "partner_last_bid": {"in": ["4♥", "4♠"]},
    "partner_transferred": true,
    "fit_known": true
  },
  "explanation": "Pass - partner's game bid is a signoff",
  "sets_forcing_level": "NON_FORCING"
}
```

### Fix 4: Add combined strength check for slam

Add to `sayc_slam_controls.json`:
```json
{
  "id": "slam_sanity_check",
  "description": "Only bid slam with 33+ combined points",
  "conditions": {
    "combined_points": {"min": 33}
  }
}
```

## Test Commands

```bash
# Test slam after RKCB with weak hand
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()

# East's hand from failing example (17 HCP)
hand = Hand.from_pbn('J96.KQJ53.KJ.KQ6')
auction = ['Pass', '1NT', 'Pass', '2♦', 'Pass', '2♥', 'Pass', '4♥', 'Pass', '4NT', 'Pass', '5♦']
bid, exp = engine.get_next_bid(hand, auction, 'East', 'None', 'detailed', 'North')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: Pass or 5♥ (not 6♥)')
"

# Test Blackwood with insufficient values
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()

# Opener after partner's transfer to game
hand = Hand.from_pbn('AQ732.T72.A3.J82')  # 12 HCP
auction = ['1NT', 'Pass', '2♦', 'Pass', '2♥', 'Pass', '4♥']
bid, exp = engine.get_next_bid(hand, auction, 'West', 'None', 'detailed', 'North')
print(f'Bid: {bid}')
print(f'Rule: {engine._last_rule_id}')
print(f'Expected: Pass (4♥ is signoff)')
"
```

## Success Criteria

- All slam rules require minimum 15+ HCP
- No Blackwood after partner's signoff in game
- RKCB failures reduced from 13 to < 3
- No slam bid with < 30 combined points

## Verification

After fixes, run:
```bash
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep -E "(rkcb|slam)"
```
