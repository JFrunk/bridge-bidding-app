# V2 Schema Engine - Implementation Plan

**Generated:** 2026-01-05
**Based on:** 4-agent parallel investigation of 125+ bidding failures
**Goal:** Reduce overbid rate from 80.3% to <50%, improve accuracy from 9.1% to 25%+

---

## Priority Order (by impact)

### Phase 1: V1 Fallback Fixes (78 failures → ~40 expected)

**File:** `sayc_interference.json`

#### Fix 1.1: Expand pass_competitive_no_fit
Remove the `longest_suit_length` restriction that causes fallback:

```json
{
  "id": "pass_competitive_no_fit",
  "bid": "Pass",
  "priority": 180,
  "description": "Pass with weak hand, no fit, after opponent interference",
  "conditions": {
    "is_response": true,
    "is_contested": true,
    "hcp": {"min": 6, "max": 9},
    "support_for_partner": {"max": 2}
  },
  "explanation": "Pass with {hcp} HCP - no fit for partner's suit"
}
```

#### Fix 1.2: Add pass_competitive_long_minor
New rule for hands with long minor but no major fit:

```json
{
  "id": "pass_competitive_long_minor",
  "bid": "Pass",
  "priority": 175,
  "description": "Pass with minimum hand and long minor after interference",
  "conditions": {
    "is_response": true,
    "is_contested": true,
    "hcp": {"min": 6, "max": 9},
    "support_for_partner": {"max": 2},
    "longest_suit": {"in": ["♦", "♣"]},
    "longest_suit_length": {"min": 5}
  },
  "explanation": "Pass with {hcp} HCP - long minor but no major fit"
}
```

#### Fix 1.3: Add pass_weak_after_preempt_doubled
```json
{
  "id": "pass_weak_after_preempt_doubled",
  "bid": "Pass",
  "priority": 185,
  "description": "Pass after partner's preempt is doubled with weak hand",
  "conditions": {
    "partner_preempted": true,
    "rho_doubled": true,
    "hcp": {"max": 9},
    "support_for_partner": {"max": 2}
  },
  "explanation": "Pass with {hcp} HCP - insufficient to act after partner's preempt"
}
```

---

### Phase 2: RKCB/Slam Fixes (13 failures → ~2 expected)

**File:** `sayc_rkcb.json`

#### Fix 2.1: Add HCP guard to queen_ask_positive
```json
{
  "id": "queen_ask_positive",
  "bid": "6{agreed_suit}",
  "priority": 905,
  "conditions": {
    "partner_last_bid": {"in": ["5♣", "5♦"]},
    "fit_known": true,
    "has_trump_queen": true,
    "hcp": {"min": 12},
    "total_keycards_min": {"min": 4}
  },
  "explanation": "Show trump queen with {hcp} HCP - partnership has all keycards"
}
```

#### Fix 2.2: Add HCP guard to slam_after_rkcb_5d_hearts
```json
{
  "id": "slam_after_rkcb_5d_hearts",
  "bid": "6♥",
  "priority": 910,
  "conditions": {
    "partner_last_bid": "5♦",
    "asked_blackwood": true,
    "hcp": {"min": 17},
    "agreed_suit": "♥",
    "total_keycards_min": {"min": 4}
  },
  "explanation": "Bid 6♥ with {hcp} HCP after partner shows keycards"
}
```

#### Fix 2.3: Add no_blackwood_after_transfer_signoff
```json
{
  "id": "no_blackwood_after_transfer_signoff",
  "bid": "Pass",
  "priority": 950,
  "description": "Do not continue after partner's transfer signoff",
  "conditions": {
    "partner_last_bid": {"in": ["4♥", "4♠"]},
    "partner_transferred": true,
    "fit_known": true,
    "hcp": {"max": 16}
  },
  "explanation": "Pass - partner's game bid is a signoff",
  "sets_forcing_level": "NON_FORCING"
}
```

**File:** `sayc_slam_controls.json`

#### Fix 2.4: Add HCP guard to bid_slam_all_keycards
```json
{
  "id": "bid_slam_all_keycards",
  "bid": "6{agreed_suit}",
  "priority": 900,
  "conditions": {
    "have_all_keycards": true,
    "fit_known": true,
    "hcp": {"min": 15},
    "partnership_hcp_min": {"min": 33}
  },
  "explanation": "Bid slam with all keycards and {hcp} HCP"
}
```

---

### Phase 3: Responder Rebid Fixes (25 failures → ~8 expected)

**File:** `sayc_responder_rebids.json`

#### Fix 3.1: Tighten responder_3nt_balanced
```json
{
  "id": "responder_3nt_balanced",
  "bid": "3NT",
  "priority": 450,
  "conditions": {
    "my_bid_count": 1,
    "hcp": {"min": 13, "max": 15},
    "is_balanced": true,
    "partnership_hcp_min": {"min": 25}
  },
  "explanation": "3NT with {hcp} HCP balanced - game values"
}
```

#### Fix 3.2: Add partner_showed_extras to game raises
```json
{
  "id": "responder_game_in_spades_with_fit",
  "bid": "4♠",
  "priority": 500,
  "conditions": {
    "my_bid_count": 1,
    "hcp": {"min": 10},
    "spades_length": {"min": 4},
    "partner_last_bid": {"in": ["3♠", "2♠", "1♠"]},
    "OR": [
      {"partner_showed_extras": true},
      {"hcp": {"min": 13}}
    ]
  },
  "explanation": "Game in spades with fit and values"
}
```

#### Fix 3.3: Add responder_rebid_pass_minimum
```json
{
  "id": "responder_rebid_pass_minimum",
  "bid": "Pass",
  "priority": 200,
  "conditions": {
    "is_responder_rebid": true,
    "hcp": {"max": 11},
    "partner_showed_limit": true
  },
  "explanation": "Pass with {hcp} HCP - partner showed minimum"
}
```

---

### Phase 4: Preempt & Opener Rebid Fixes (9 failures → ~0 expected)

**File:** `sayc_preempts.json`

#### Fix 4.1: Add HCP guard to 5-level minor raises
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
    "is_contested": false
  },
  "explanation": "Raise to 5♣ with {hcp} HCP and {support_for_partner} clubs"
}
```

#### Fix 4.2: Tighten raise_partner_preempt_to_game
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
        "is_contested": false
      }
    ]
  },
  "explanation": "Game raise with {hcp} HCP and support"
}
```

**File:** `sayc_rebids.json`

#### Fix 4.3: Add is_contested guard to opener_invite_after_single_raise_medium
```json
{
  "id": "opener_invite_after_single_raise_medium",
  "bid": "3{agreed_suit}",
  "priority": 540,
  "conditions": {
    "is_rebid": true,
    "partner_raised": true,
    "is_contested": false,
    "hcp": {"min": 15, "max": 17}
  },
  "explanation": "Invite with {hcp} HCP after partner's uncontested raise"
}
```

#### Fix 4.4: Add opener_pass_after_contested_raise
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
  "explanation": "Pass - partner's raise was competitive/preemptive"
}
```

#### Fix 4.5: Guard Smolen rules with 1NT context
```json
{
  "id": "opener_accept_smolen_spades",
  "bid": "4♠",
  "priority": 650,
  "conditions": {
    "is_rebid": true,
    "partner_bid_smolen": true,
    "opener_opened_1nt": true,
    "spades_length": {"min": 3},
    "hcp": {"min": 15}
  },
  "explanation": "Accept Smolen transfer with {hcp} HCP and {spades_length} spades"
}
```

---

## Verification Commands

After implementing each phase, run:

```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
source venv/bin/activate

# Quick test (Phase-specific)
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 50 --seed 42

# Comprehensive test
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 --output efficiency_after_fixes.json
```

## Success Metrics

| Metric | Before | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Target |
|--------|--------|---------|---------|---------|---------|--------|
| Accuracy | 9.1% | 15%+ | 18%+ | 22%+ | 25%+ | 25%+ |
| Overbid Rate | 80.3% | 65% | 55% | 48% | <45% | <50% |
| Mean Gap | +2.80 | +2.2 | +1.9 | +1.6 | <+1.5 | <+1.5 |
| Critical | 109 | 80 | 60 | 45 | <40 | <40 |

---

## Implementation Notes

1. **Feature Dependencies**: Some conditions require new features in `enhanced_extractor.py`:
   - `partner_showed_extras` - already exists
   - `partnership_hcp_min` - already exists
   - `partner_showed_limit` - already exists
   - `partner_preempted` - already exists
   - `rho_doubled` - need to verify
   - `opener_opened_1nt` - may need to add
   - `partner_bid_smolen` - may need to add

2. **Priority Ordering**: Ensure new Pass rules have lower priority than action rules

3. **Testing Order**: Implement Phase 1 first (biggest impact), verify, then continue
