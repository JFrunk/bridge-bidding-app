# SAYC Compliance - Prioritized Fix List

**Based on:** 500-hand benchmark (95.1% overall compliance)
**Date:** 2026-02-24

---

## Priority 1: CRITICAL - 1M Opening HCP Requirements

**Issue:** 1M openings allow insufficient HCP (8-11 instead of 12+)
**Compliance:** 75.6% (10 errors in 41 tests = 24% failure rate)
**Severity:** HIGH - Violates fundamental SAYC opening requirements

### Errors Found
```
- 1♠ opened with 10 HCP (need 12+)
- 1♥ opened with 11 HCP (need 12+)
- 1♠ opened with 8 HCP (need 12+)
- 1♥ opened with only 4 cards (need 5+)
```

### Root Cause Analysis

The opening bid module likely has:
1. HCP threshold set to 11 instead of 12
2. Missing strict validation in `opening_bids.py`

### Files to Fix

**Primary:** `backend/engine/ai/opening_bids.py`

### Recommended Fix

1. **Locate the 1M opening logic:**
```bash
grep -n "def.*1.*major\|def.*opening.*major" backend/engine/ai/opening_bids.py
grep -n "hcp.*11\|hcp.*12" backend/engine/ai/opening_bids.py
```

2. **Update HCP requirement:**
```python
# BEFORE (likely):
if hand.hcp >= 11 and hand.suit_lengths[suit] >= 5:

# AFTER (correct):
if hand.hcp >= 12 and hand.suit_lengths[suit] >= 5:
```

3. **Add strict validation:**
```python
def can_open_1_major(hand: Hand, suit: str) -> bool:
    """Check if hand qualifies for 1M opening."""
    if hand.hcp < 12:
        return False  # SAYC requires 12+ HCP
    if hand.suit_lengths[suit] < 5:
        return False  # SAYC requires 5+ cards
    return True
```

### Testing

```bash
# Before fix - capture baseline
python3 test_sayc_compliance.py --category "1M" --hands 200 --output 1m_before.json

# After fix - verify improvement
python3 test_sayc_compliance.py --category "1M" --hands 200 --output 1m_after.json

# Compare
diff 1m_before.json 1m_after.json

# Expected result: 100% compliance (was 75.6%)
```

### Expected Impact
- **Compliance improvement:** 75.6% → 100% (24% improvement)
- **Affected auctions:** ~15-20% of all hands
- **Risk:** Low - strict SAYC requirement

---

## Priority 2: CRITICAL - Weak Two Suit Length Requirements

**Issue:** Weak two bids allow insufficient suit length (0-5 cards instead of 6+)
**Compliance:** 73.2% (11 errors in 41 tests = 27% failure rate)
**Severity:** HIGH - Violates preemptive bid definition

### Errors Found
```
- 2♠ weak two with only 4 cards (need 6+)
- 2♦ weak two with only 0 cards (need 6+)
- 2♦ weak two with only 3 cards (need 6+)
```

### Root Cause Analysis

The preempts module likely has:
1. Insufficient suit length validation
2. Hand generation function not enforcing 6-card requirement
3. Possible confusion between weak two (6 cards) and overcalls (5 cards)

### Files to Fix

**Primary:** `backend/engine/ai/conventions/preempts.py`
**Secondary:** `backend/engine/hand_constructor.py` (if hand generation is involved)

### Recommended Fix

1. **Locate weak two logic:**
```bash
grep -n "weak.*two\|2.*level.*preempt" backend/engine/ai/conventions/preempts.py
grep -n "def.*weak\|def.*preempt" backend/engine/ai/conventions/preempts.py
```

2. **Update suit length requirement:**
```python
# In preempts.py - weak two evaluation
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    # ... existing code ...

    # For 2-level preempts (2♦/2♥/2♠)
    for suit in ['♠', '♥', '♦']:
        suit_length = hand.suit_lengths[suit]

        # CRITICAL: Must have exactly 6 cards (SAYC requirement)
        if suit_length != 6:  # Not < 6, but == 6 for classic weak two
            continue

        # HCP requirement: 5-11
        if not (5 <= hand.hcp <= 11):
            continue

        # Weak two criteria met
        return (f'2{suit}', f'Weak two: 6-card {suit}, {hand.hcp} HCP')
```

3. **Add strict validation in hand generator (if used):**
```python
# In hand_constructor.py or similar
def generate_weak_two_hand() -> Hand:
    """Generate hand suitable for weak two bid."""
    max_attempts = 1000
    for _ in range(max_attempts):
        hand = generate_random_hand()

        # Strict requirements
        if not (5 <= hand.hcp <= 11):
            continue

        # Must have exactly one 6-card major (or 6-card diamond)
        has_6_card_suit = (
            hand.suit_lengths['♠'] == 6 or
            hand.suit_lengths['♥'] == 6 or
            hand.suit_lengths['♦'] == 6
        )

        if has_6_card_suit:
            return hand

    # Fallback
    return generate_random_hand()
```

### Testing

```bash
# Before fix
python3 test_sayc_compliance.py --category "Weak" --hands 200 --output weak_before.json

# After fix
python3 test_sayc_compliance.py --category "Weak" --hands 200 --output weak_after.json

# Expected result: 100% compliance (was 73.2%)
```

### Expected Impact
- **Compliance improvement:** 73.2% → 100% (27% improvement)
- **Affected auctions:** ~8-10% of all hands
- **Risk:** Low - strict SAYC requirement

---

## Priority 3: MEDIUM - 1NT Opening HCP Range

**Issue:** 1NT opening occasionally violates 15-17 HCP range
**Compliance:** 95.1% (2 errors in 41 tests = 5% failure rate)
**Severity:** MEDIUM - Edge case failures

### Errors Found
```
- 1NT opened with 7 HCP (need 15-17)
- 1NT opened with 18 HCP (need 15-17)
```

### Root Cause Analysis

Edge case failures suggest:
1. Missing bounds check (allows 18 HCP)
2. Possible hand generation issue (7 HCP is very unusual)

### Files to Fix

**Primary:** `backend/engine/ai/opening_bids.py`

### Recommended Fix

1. **Locate 1NT opening logic:**
```bash
grep -n "1NT\|notrump" backend/engine/ai/opening_bids.py -A 5 -B 5
```

2. **Ensure strict bounds:**
```python
def can_open_1nt(hand: Hand) -> bool:
    """Check if hand qualifies for 1NT opening."""
    # Strict HCP bounds (not >= 15 and <= 17, but explicit range check)
    if hand.hcp < 15 or hand.hcp > 17:
        return False

    # Balanced requirement
    if not hand.is_balanced:
        return False

    return True
```

3. **Add assertion in evaluation:**
```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    # ... existing code ...

    if can_open_1nt(hand):
        # Sanity check
        assert 15 <= hand.hcp <= 17, f"1NT logic error: {hand.hcp} HCP"
        assert hand.is_balanced, "1NT logic error: not balanced"

        return ('1NT', f'Balanced, {hand.hcp} HCP')
```

### Testing

```bash
# Specific test for 1NT range
python3 test_sayc_compliance.py --category "1NT" --hands 500 --output 1nt_after.json

# Expected result: 100% compliance (was 95.1%)
```

### Expected Impact
- **Compliance improvement:** 95.1% → 100% (5% improvement)
- **Affected auctions:** ~12-15% of all hands
- **Risk:** Very low - rare edge case

---

## Priority 4: LOW - Blackwood HCP Threshold

**Issue:** Blackwood used with 15 HCP instead of recommended 16+ for slam interest
**Compliance:** 97.6% (1 error in 41 tests = 2% failure rate)
**Severity:** LOW - Marginal edge case

### Errors Found
```
- Blackwood with only 15 HCP (need 16+ for slam)
```

### Root Cause Analysis

This is a borderline case:
- 15 HCP is close to slam range
- Partnership might have 30-31 combined points
- Not strictly illegal, but suboptimal

### Files to Fix

**Primary:** `backend/engine/ai/conventions/blackwood.py`

### Recommended Fix

1. **Update Blackwood requirements:**
```python
def requirements(self, hand: Hand) -> bool:
    """Check if hand is strong enough for Blackwood."""
    # Minimum HCP for slam interest
    if hand.hcp < 16:  # Was 15
        return False

    # Should have trump fit established
    # ... existing fit logic ...

    return True
```

### Testing

```bash
python3 test_sayc_compliance.py --category "Blackwood" --hands 500 --output blackwood_after.json

# Expected result: 100% compliance (was 97.6%)
```

### Expected Impact
- **Compliance improvement:** 97.6% → 100% (2% improvement)
- **Affected auctions:** <1% of all hands
- **Risk:** Very low - conservative improvement

---

## Implementation Plan

### Phase 1: Critical Fixes (Week 1)

1. **Fix 1M Opening HCP** (Priority 1)
   - Update `opening_bids.py`
   - Run category test
   - Verify 100% compliance

2. **Fix Weak Two Length** (Priority 2)
   - Update `preempts.py`
   - Update hand generation if needed
   - Run category test
   - Verify 100% compliance

### Phase 2: Medium Fixes (Week 2)

3. **Fix 1NT Range** (Priority 3)
   - Update `opening_bids.py`
   - Run category test
   - Verify 100% compliance

### Phase 3: Polish (Week 3)

4. **Fix Blackwood Threshold** (Priority 4)
   - Update `blackwood.py`
   - Run category test
   - Verify 100% compliance

### Phase 4: Verification (Week 4)

5. **Run Full Benchmark**
```bash
python3 test_sayc_compliance.py --hands 1000 \
    --output final_compliance.json \
    --pbn final_compliance.pbn
```

**Expected final result:** 99-100% overall compliance

---

## Quality Gates

### Before Each Fix
```bash
# Capture baseline
python3 test_sayc_compliance.py --hands 500 --output baseline_before.json
```

### After Each Fix
```bash
# Verify improvement
python3 test_sayc_compliance.py --hands 500 --output baseline_after.json

# Quality gates (must pass):
# - Legality: 100% (no regressions)
# - Fixed category: 100% compliance
# - Other categories: No regressions (≥ previous score)
```

### Final Verification
```bash
# Comprehensive test
python3 test_bidding_quality_score.py --hands 500 --output quality_after.json

# Compare with previous quality score
python3 compare_scores.py quality_before.json quality_after.json

# Must not regress:
# - Legality: 100%
# - Appropriateness: ≥ baseline
# - Composite: ≥ baseline - 2%
```

---

## Additional Improvements (Future)

### Category Coverage Expansion

Add tests for categories not yet covered:
1. **2NT Opening** (20-21 HCP)
2. **1m Openings** (1♣/1♦)
3. **Gerber** (4♣ over NT)
4. **Grand Slam Force** (5NT)
5. **Opener Rebids** (minimum/medium/maximum)
6. **Responder Rebids**
7. **Game/Slam Accuracy**

### Convention-Specific Tests

Create targeted tests for each convention:
```python
# Example: Stayman deep dive
python3 test_convention_specific.py --convention stayman --hands 1000

# Example: Jacoby transfers deep dive
python3 test_convention_specific.py --convention jacoby --hands 1000
```

### Integration with DDS

Add double-dummy analysis to verify optimal contracts:
```python
# Compare AI auction to double-dummy optimal contract
python3 analyze_bidding_vs_dds.py --hands 500
```

---

## Success Criteria

### Minimum Acceptable
- Overall compliance: ≥ 95% ✅ (currently 95.1%)
- Legality: 100% ✅ (currently 100%)
- All critical categories: ≥ 90%

### Target
- Overall compliance: ≥ 98%
- Legality: 100%
- All categories: ≥ 95%

### Stretch Goal
- Overall compliance: 100%
- All categories: 100%
- Zero SAYC violations across 1000+ hands

---

## Notes

- **Hand generation matters:** Some errors may be in `hand_constructor.py` rather than bidding logic
- **Test thoroughly:** Each fix should be tested in isolation before integration
- **Document changes:** Update CLAUDE.md with any architectural changes
- **Regression prevention:** Add unit tests for each fixed issue
- **External validation:** Use PBN export for human expert review

---

**Prepared by:** Claude Code Bidding AI Specialist
**Date:** 2026-02-24
**Status:** Ready for implementation
