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

## Testing

### Baseline Test Results
```
Total tests: 218
Matched expected: 28 (12.8%)
No rule found: 130 (59.6%)
Errors: 0
```

Category highlights:
- **Balancing:** 36.4% match
- **Reopening Double:** 36.4% match
- **Doubles:** 23.5% match

### Unit Tests

Run the hand constructor tests:
```bash
cd backend
python3 -c "from engine.hand_constructor import generate_hand_with_constraints; ..."
```

## Future Work

1. **Expand rule coverage** - Reduce "No Rule Found" rate from 59.6%
2. **Add fourth_suit_available feature** - Enable fourth suit forcing detection
3. **Add partner_first_suit tracking** - For preference bids
4. **Add my_suit tracking** - For rebidding own suit

## Related Files

- Schema Interpreter: `backend/engine/v2/interpreters/schema_interpreter.py`
- Feature Extractor: `backend/engine/v2/features/enhanced_extractor.py`
- Hand Constructor: `backend/engine/hand_constructor.py`
- Rebids Schema: `backend/engine/v2/schemas/sayc_rebids.json`
