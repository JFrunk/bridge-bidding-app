# V2 Schema Engine - Bidding Issues Triage

**Generated:** 2026-01-05
**Source:** 200 hands analyzed with production DDS
**Overall Stats:** 80.3% overbid rate, 9.1% accuracy, mean gap +2.80

---

## Priority 1: V1 Fallback (78 failures, 72.9% failure rate)

**Location:** Falls back to V1 engine when no V2 schema rule matches
**Impact:** 78 overbids, avg gap +4.2, max gap +10
**Root Cause:** V2 schema coverage gaps causing fallback to aggressive V1 engine

### Key Patterns to Fix

1. **Game raises after takeout double** (most common)
   - Example: `1♠ - X - 4♠` with weak responding hand
   - South has 3-4 HCP, should pass, but V1 bids 4♠
   - **Fix:** Add V2 rule for `pass_after_partner_opened_and_rho_doubled`

2. **Competitive rebids**
   - Example: `1♥ - X - 4♥`
   - **Fix:** Ensure V2 interference schema handles all weak hand passes

3. **Preempt responses**
   - Example: `2♠ - Pass - 4♥` with weak hand
   - **Fix:** Add V2 rules for weak preempt responses

### Investigation Commands
```bash
# Find all V1 fallback cases
grep -n "v1_fallback" efficiency_report.json | head -20

# Test specific auction
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.hand import Hand
engine = BiddingEngineV2Schema()
hand = Hand.from_pbn('K65.9872.T52.643')  # 4 HCP
bid, exp = engine.get_next_bid(hand, ['1♠', 'X'], 'South', 'None', 'detailed', 'North')
print(f'{bid}: {exp}')
"
```

---

## Priority 2: RKCB/Slam Bidding (13 failures, 100% failure rate on some rules)

**Location:** `sayc_rkcb.json`
**Impact:** 13 overbids, avg gap +4.5, max gap +10
**Root Cause:** Slam rules triggering without sufficient combined strength

### Rules to Fix

| Rule ID | Failures | Avg Gap | Issue |
|---------|----------|---------|-------|
| `queen_ask_positive` | 6 | +4.8 | Bidding slam without enough keycards |
| `slam_after_rkcb_5d_hearts` | 4 | +5.8 | 6♥ after 5♦ response always overbids |
| `signoff_6_after_rkcb` | 3 | +3.3 | Signing off at 6-level too easily |

### Example Failure
```
Hand 68: 6♥ by East (gap +10)
Auction: 1NT - 2♦ - 2♥ - 4♥ - 4NT - 5♦ - 6♥
North: ♠T84 ♥6 ♦AQ6 ♣AT8652
South: ♠K52 ♥A984 ♦98742 ♣3
```
**Problem:** Responder jumps to 4♥ then bids Blackwood, but combined HCP is only ~20

### Fixes Needed
1. `slam_after_rkcb_5d_hearts`: Add `hcp: {min: 15}` condition
2. `queen_ask_positive`: Require more keycards before bidding 6
3. Add sanity check: Don't bid slam with < 30 combined points

---

## Priority 3: Responder Rebids (25 failures)

**Location:** `sayc_responder_rebids.json`
**Impact:** 25 overbids, avg gap +3.5

### Rules to Fix

| Rule ID | Failures | Avg Gap | Issue |
|---------|----------|---------|-------|
| `responder_3nt_balanced` | 17 | +2.9 | 3NT bid with insufficient points |
| `responder_game_in_spades_with_fit` | 5 | +4.6 | Game raise without game values |
| `responder_game_in_major_with_fit` | 2 | +4.5 | Game raise without game values |
| `responder_5_minor_game` | 1 | +9.0 | 5-level minor too aggressive |

### Example Failure
```
Hand 87: 3NT (gap +4)
Auction: 1♣ - X - 1♦ - 1NT - 3NT
```
**Problem:** Responder bids 3NT with ~10 HCP when combined is only ~22

### Fixes Needed
1. `responder_3nt_balanced`: Increase `hcp: {min: 13}` (currently too low)
2. `responder_game_in_spades_with_fit`: Require `support_points: {min: 13}` AND `hcp: {min: 10}`
3. `responder_5_minor_game`: Add `combined_points: {min: 29}` check

---

## Priority 4: Slam Controls (7 failures)

**Location:** `sayc_slam_controls.json`
**Impact:** 7 overbids, avg gap +3.5

### Rules to Fix

| Rule ID | Failures | Avg Gap | Issue |
|---------|----------|---------|-------|
| `bid_slam_all_keycards` | 4 | +3.0 | Bidding slam with all keycards but no tricks |
| `slam_brake_denied_control` | 3 | +4.3 | Control-bid logic failing |

### Fixes Needed
1. `bid_slam_all_keycards`: Add trick source validation (not just keycards)
2. Review control-bidding sequence logic

---

## Priority 5: Preempts (4 failures)

**Location:** `sayc_preempts.json`
**Impact:** 4 overbids, avg gap +5.4

### Rules to Fix

| Rule ID | Failures | Avg Gap | Issue |
|---------|----------|---------|-------|
| `raise_partner_club_preempt_to_5` | 2 | +7.5 | 5♣ with insufficient fit/values |
| `raise_partner_preempt_to_game` | 1 | +4.0 | Game raise too aggressive |

### Fixes Needed
1. Require stronger hand for 5-level preempt raises
2. Add `support_points: {min: 15}` for game raises of preempts

---

## Priority 6: Opener Rebids (5 failures)

**Location:** `sayc_rebids.json`
**Impact:** 5 overbids, avg gap +4.6

### Rules to Fix
- `opener_accept_smolen_spades`: Gap +6
- `opener_respond_negative_double_hearts`: Gap +6
- `opener_invite_after_single_raise_medium`: Gap +6

### Fixes Needed
Review HCP requirements for these rebid situations

---

## Parallel Investigation Assignment

### Agent 1: V1 Fallback Coverage
- **Goal:** Reduce V1 fallback from 78 to <20 cases
- **Files:** `sayc_interference.json`, `sayc_responses.json`
- **Task:** Add missing pass rules for weak hands in competitive auctions

### Agent 2: RKCB/Slam Logic
- **Goal:** Fix 100% failure rate on slam rules
- **Files:** `sayc_rkcb.json`, `sayc_slam_controls.json`
- **Task:** Add HCP guards and combined-strength checks

### Agent 3: Responder Rebids
- **Goal:** Fix responder_3nt_balanced (17 failures)
- **Files:** `sayc_responder_rebids.json`
- **Task:** Tighten HCP requirements for game bids

### Agent 4: Preempt Responses
- **Goal:** Fix preempt raise overbids
- **Files:** `sayc_preempts.json`
- **Task:** Add support point requirements for raises

---

## Testing Commands

```bash
# Run full efficiency analysis
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42

# Quick test specific rule
USE_V2_SCHEMA_ENGINE=true python3 -c "
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
engine = BiddingEngineV2Schema()
# Test hand here
"

# Compare before/after
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 --output before.json
# Make changes
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 --output after.json
```

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Accuracy Rate | 9.1% | 25%+ |
| Overbid Rate | 80.3% | <50% |
| Mean Gap | +2.80 | <+1.5 |
| Critical Failures (Gap≥3) | 109 | <40 |
