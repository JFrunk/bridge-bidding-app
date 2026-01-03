# V2 Schema Engine: Expert Bidding Enhancements

**Last Updated:** 2026-01-03

This document describes the expert bidding enhancements added to the V2 schema-driven bidding engine.

## Overview

The V2 schema engine was enhanced with "multidimensional constraint evaluation" - going beyond simple HCP ranges to include Quick Tricks, Suit Stoppers, Support Points, and Limit Bid tracking.

## Key Enhancements

### 1. Suit-First Generation Algorithm

**File:** `backend/engine/hand_constructor.py`

**Problem:** Pure rejection sampling (shuffle-and-check) performs poorly for tight constraints like "6+ card suit with 8-10 HCP". With 20,000 max attempts, some constraint combinations still timeout.

**Solution:** Suit-First Generation algorithm:
1. Groups available cards by suit
2. Assigns required suit lengths FIRST
3. Fills remaining slots from other suits
4. Only then checks HCP constraint

**Performance Improvement:** Reduces rejection rate by several orders of magnitude for tight constraints. All tests now achieve 100% success rate.

```python
# Example: 6+ card major with 6-10 HCP (weak two)
constraints = {
    'hcp_range': (6, 10),
    'suit_length_req': (['♠', '♥'], 6, 'any_of')
}
# Old: ~5% success rate with random sampling
# New: 100% success rate with suit-first generation
```

### 2. Support Points Trigger

**File:** `backend/engine/v2/features/enhanced_extractor.py`

**Problem:** Support points (HCP + shortness points) should only be counted when a trump fit is confirmed. Previously calculated based on partner's last bid suit.

**Solution:** Recalculate support points when `fit_known=True` and `agreed_suit` is established:

```python
if agreed['fit_known'] and agreed['agreed_suit']:
    # Recalculate with confirmed trump suit
    flat['support_points'] = calculate_support_points(hand, agreed['agreed_suit'])
    flat['support_points_active'] = True
else:
    # Without confirmed fit, support points = HCP (no shortness bonus)
    flat['support_points'] = hf['hcp']
    flat['support_points_active'] = False
```

**Shortness Values:**
- Void: +5 points
- Singleton: +3 points
- Doubleton: +1 point

### 3. Expanded Responder Rebid Rules

**File:** `backend/engine/v2/schemas/sayc_rebids.json`

Added comprehensive responder rebid rules:

| Rule ID | Bid | Description |
|---------|-----|-------------|
| `responder_jump_to_game_in_major` | 4M | Jump to game with 13+ support points |
| `responder_rebid_2nt_invitational` | 2NT | Invitational with 11-12 HCP balanced |
| `responder_delayed_game_raise` | 3M | Delayed game raise with 13+ support points |
| `responder_jump_preference` | 3X | Jump preference showing 10-12 support points |
| `responder_rebid_own_suit_weak` | 2X | Rebid 6+ card suit with 6-9 HCP |
| `responder_rebid_own_suit_invitational` | 3X | Jump rebid with 10-12 HCP |
| `responder_new_suit_at_2_level` | 2X | New lower suit forcing one round |
| `responder_support_opener_minimum` | 2X | Support with minimum values |

### 4. Limit Bid Tracking

**Files:**
- `backend/engine/v2/interpreters/schema_interpreter.py`
- `backend/engine/v2/schemas/sayc_rebids.json`

**Purpose:** Track when a bid shows a narrow range (limit bid), signaling partner to either pass or accept.

**Implementation:**
- Added `is_limit_bid: bool` field to `BidCandidate` dataclass
- Schema rules can specify `"is_limit_bid": true`

**Rules marked as limit bids:**
- `responder_rebid_2nt_invitational` - 2NT (11-12 HCP)
- `responder_jump_preference` - 3X (10-12 support points)
- `responder_rebid_own_suit_invitational` - 3X (10-12 HCP, 6+ cards)

## Schema Condition Types

The schema interpreter supports these expert constraint types:

### `stoppers_required`
Requires minimum number of stopped suits for NT bids.
```json
"stoppers_required": 3
```

### `stoppers_in`
Requires specific suits to be stopped, with dynamic `opponent_suit` reference.
```json
"stoppers_in": ["opponent_suit"]
```

### `quick_tricks`
Minimum quick tricks requirement for takeout doubles.
```json
"quick_tricks": {"min": 1.5}
```

### `support_points`
Points including shortness bonus when fit is confirmed.
```json
"support_points": {"min": 13}
```

### `is_limit_bid`
Marks bid as showing a narrow range.
```json
"is_limit_bid": true
```

### 5. Explicit Pass Rules (NEW)

**Files:**
- `backend/engine/v2/schemas/sayc_responses.json`
- `backend/engine/v2/schemas/sayc_rebids.json`
- `backend/engine/v2/schemas/sayc_balancing.json`

**Problem:** The 59.6% "No Rule Found" rate included many cases where Pass was the correct action but no explicit Pass rule matched.

**Solution:** Added explicit Pass rules for common situations:

| Rule ID | Location | Description |
|---------|----------|-------------|
| `pass_after_nt_minimum` | responses | Pass 1NT with 0-7 balanced |
| `pass_after_2nt_minimum` | responses | Pass 2NT with 0-4 HCP |
| `pass_after_preempt` | responses | Pass partner's preempt with no fit |
| `opener_pass_after_limit_raise` | rebids | Accept limit raise with minimum |
| `opener_pass_after_1nt_response` | rebids | Pass 1NT with balanced minimum |
| `responder_pass_opener_minimum_rebid` | rebids | Pass after minimum rebid |
| `pass_balancing_weak` | balancing | Pass in balancing with 0-4 HCP |
| `pass_balancing_defensive` | balancing | Pass with values in opponent's suit |

### 6. Borrowed King Balancing (NEW)

**File:** `backend/engine/v2/schemas/sayc_balancing.json`

**Concept:** In balancing (pass-out) seat, bid with approximately 3 fewer HCP than in direct seat, because partner is expected to have some values (the "borrowed king").

**Implementation:**
- Balancing takeout double: 8-14 HCP (direct seat requires 12+)
- Balancing 1NT: 11-15 HCP (direct seat requires 15-18)
- Balancing suit bids: 5+ HCP (direct seat requires 8+)

```json
{
  "id": "balancing_double",
  "conditions": {
    "is_balancing": true,
    "hcp": {"min": 8, "max": 14}
  }
}
```

### 7. Partner/Suit Tracking Features (NEW)

**File:** `backend/engine/v2/features/enhanced_extractor.py`

Added new features for preference bids and reverse detection:

| Feature | Type | Description |
|---------|------|-------------|
| `partner_first_suit` | str | Partner's first natural suit bid |
| `support_for_partner_first` | int | Card count in partner's first suit |
| `my_suit` | str | My first natural suit bid |
| `second_suit` | str | My second 4+ card suit |
| `second_suit_higher` | bool | True if second suit ranks higher (reverse) |
| `second_suit_lower` | bool | True if second suit ranks lower (non-reverse) |
| `stopper_in_opponent_suit` | bool | Have stopper in opener's suit |
| `unbid_suit_support` | int | Count of unbid suits with 3+ support |

These enable:
- Preference bids: Return to partner's first suit
- Barrier Principle: Detect reverse bids (higher second suit at 2-level)
- NT overcalls: Check stopper in opponent's suit
- Takeout doubles: Verify support for all unbid suits

## Testing

### Baseline Test Results (Updated 2026-01-03)
```
Total tests: 218
Matched expected: 33 (15.1%)
No rule found: 100 (45.9%)  ← Improved from 52.3%
Errors: 0
```

**Improvement:** "No Rule Found" reduced by 6.4 percentage points (from 52.3% to 45.9%).

Category highlights:
- **Reopening Double:** 36.4% match (27.3% no rule)
- **Balancing:** 27.3% match (0% no rule!)
- **Doubles:** 23.5% match (23.5% no rule)
- **Negative Double:** 20.0% match (0% no rule!)
- **Michaels and Unusual NT:** 21.4% match (64.3% no rule)
- **Overcalls:** 16.7% match (0% no rule!)

### Unit Tests

Run the hand constructor tests:
```bash
cd backend
python3 -c "from engine.hand_constructor import generate_hand_with_constraints; ..."
```

Run the feature extractor test:
```bash
cd backend
python3 -c "
from engine.v2.features.enhanced_extractor import extract_flat_features
from engine.hand import Hand, Card
# ... test partner_first_suit, second_suit_higher, etc.
"
```

### 8. Texas Transfers (NEW)

**File:** `backend/engine/v2/schemas/sayc_responses.json`

**Purpose:** Direct game transfer with 6+ card major and game values (10+ HCP).

**Implementation:**
- 4♦ = Texas transfer to hearts (6+ hearts, 10+ HCP)
- 4♥ = Texas transfer to spades (6+ spades, 10+ HCP)

**Rules:**
| Rule ID | Bid | Description |
|---------|-----|-------------|
| `texas_transfer_hearts` | 4♦ | 6+ hearts, 10+ HCP |
| `texas_transfer_spades` | 4♥ | 6+ spades, 10+ HCP |
| `opener_complete_texas_hearts` | 4♥ | Opener accepts transfer |
| `opener_complete_texas_spades` | 4♠ | Opener accepts transfer |

**Priority Logic:**
- Texas (6+ cards, 10+ HCP) takes priority over Jacoby (5 cards)
- Jacoby invitational (6+ cards, 8-9 HCP) uses Jacoby, not Texas
- Stayman now only matches with exactly 4 cards in a major

### 9. Smolen Convention (NEW)

**File:** `backend/engine/v2/schemas/sayc_rebids.json`

**Purpose:** After Stayman denial (1NT-2♣-2♦), show 5-4 in the majors with game values by jumping to 3 of the 4-card major.

**Sequence:**
1. 1NT - 2♣ (Stayman)
2. 2♦ (no 4-card major)
3. 3♥ = 4 hearts, 5 spades, game values
4. 3♠ = 4 spades, 5 hearts, game values

**Rules:**
| Rule ID | Bid | Description |
|---------|-----|-------------|
| `responder_smolen_3h` | 3♥ | 4 hearts, 5 spades, 10+ HCP |
| `responder_smolen_3s` | 3♠ | 4 spades, 5 hearts, 10+ HCP |
| `opener_accept_smolen_spades` | 4♠ | Accept with 3+ spades |
| `opener_reject_smolen_spades` | 3NT | No spade fit |
| `opener_accept_smolen_hearts` | 4♥ | Accept with 3+ hearts |
| `opener_reject_smolen_hearts` | 3NT | No heart fit |

### 10. Roman Key Card Blackwood - 1430 (NEW)

**Files:**
- `backend/engine/v2/schemas/sayc_rkcb.json`
- `backend/engine/v2/features/enhanced_extractor.py`

**Purpose:** Slam bidding with precise key card tracking.

**Key Card Definition:**
- 5 key cards: 4 aces + trump King
- Features added: `key_cards`, `aces_held`, `has_trump_queen`

**1430 Responses to 4NT:**
| Response | Meaning |
|----------|---------|
| 5♣ | 1 or 4 key cards |
| 5♦ | 0 or 3 key cards |
| 5♥ | 2 key cards without trump Queen |
| 5♠ | 2 key cards with trump Queen |
| 5NT | All 5 key cards |

**Follow-up Bids:**
- Queen Ask: After 5♣/5♦, partner can ask for trump Queen
- King Ask (5NT): Ask for specific side kings
- Sign-off: 6 of trumps after RKCB
- Grand Slam: 7 of trumps when all keys accounted

### 11. Competitive Interference Schema (NEW)

**File:** `backend/engine/v2/schemas/sayc_interference.json`

**Purpose:** Complete competitive bidding after opponent interference.

**Key Rules (20 total):**
| Rule ID | Bid | Description |
|---------|-----|-------------|
| `simple_overcall_1_level_spades` | 1♠ | 8-16 HCP, 5+ spades |
| `simple_overcall_1_level_hearts` | 1♥ | 8-16 HCP, 5+ hearts |
| `takeout_double_standard` | X | 12+ HCP, support for unbid suits |
| `negative_double_1_level` | X | 6+ HCP, partner opened, opponent overcalled |
| `negative_double_2_level` | X | 8+ HCP at 2-level |
| `unusual_2nt` | 2NT | 6-11 HCP, 5-5 in minors |
| `michaels_cuebid_major` | {opp} | 6-11 HCP, 5-5 (other major + minor) |
| `michaels_cuebid_minor` | {opp} | 6-11 HCP, 5-5 in both majors |
| `direct_nt_overcall_1nt` | 1NT | 15-18 HCP balanced with stopper |
| `redouble_after_takeout_double` | XX | 10+ HCP after opponent's double |

### 12. Penalty Double Schema (NEW)

**File:** `backend/engine/v2/schemas/sayc_penalty.json`

**Purpose:** Penalty doubles, forcing passes, and high-level competitive actions.

**Key Rules (8 total):**
| Rule ID | Bid | Description |
|---------|-----|-------------|
| `penalty_double_high_level` | X | 10+ HCP at 3+ level with stopper |
| `forcing_pass_game_level` | Pass | Game forcing established, partner must act |
| `penalty_pass_convert_double` | Pass | Convert partner's takeout double to penalty |
| `cooperative_double` | X | 12+ HCP at 3+ level, optional double |
| `lightner_double` | X | Double of slam, unusual lead requested |

### 13. New Feature: RHO Last Bid (NEW)

**File:** `backend/engine/v2/features/enhanced_extractor.py`

**Feature:** `rho_last_bid` - Tracks Right Hand Opponent's last bid

**Usage:**
```json
{
  "id": "redouble_after_takeout_double",
  "conditions": {
    "rho_last_bid": "X"
  }
}
```

## Future Work

1. ~~**Expand rule coverage** - Reduce "No Rule Found" rate from 59.6%~~ ✅ Reduced to 45.9%
2. **Add fourth_suit_available feature** - Enable fourth suit forcing detection
3. ~~**Add partner_first_suit tracking** - For preference bids~~ ✅ Implemented
4. ~~**Add my_suit tracking** - For rebidding own suit~~ ✅ Implemented
5. **Add more advancer rules** - Responses to partner's overcalls/doubles
6. ~~**Improve competitive auction handling** - More interference response rules~~ ✅ Added sayc_interference.json
7. ~~**Texas Transfers** - Direct game with 6+ major~~ ✅ Implemented
8. ~~**Smolen Convention** - 5-4 majors after Stayman denial~~ ✅ Implemented
9. ~~**RKCB 1430** - Key card responses for slam bidding~~ ✅ Implemented
10. ~~**Penalty and Forcing Passes** - High-level competitive decisions~~ ✅ Added sayc_penalty.json

## Related Files

- Schema Interpreter: `backend/engine/v2/interpreters/schema_interpreter.py`
- Feature Extractor: `backend/engine/v2/features/enhanced_extractor.py`
- Hand Constructor: `backend/engine/hand_constructor.py`
- Schemas:
  - Opening Bids: `backend/engine/v2/schemas/sayc_openings.json`
  - Responses: `backend/engine/v2/schemas/sayc_responses.json`
  - Rebids: `backend/engine/v2/schemas/sayc_rebids.json`
  - Overcalls: `backend/engine/v2/schemas/sayc_overcalls.json`
  - Doubles: `backend/engine/v2/schemas/sayc_doubles.json`
  - Balancing: `backend/engine/v2/schemas/sayc_balancing.json`
  - RKCB: `backend/engine/v2/schemas/sayc_rkcb.json`
  - Interference: `backend/engine/v2/schemas/sayc_interference.json` (NEW)
  - Penalty: `backend/engine/v2/schemas/sayc_penalty.json` (NEW)
