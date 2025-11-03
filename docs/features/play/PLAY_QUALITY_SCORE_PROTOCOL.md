# Play Quality Score Protocol

**Status:** Framework created, full implementation pending PlayEngine integration

---

## Overview

Similar to the bidding quality score, the play quality score system evaluates card play decisions across multiple dimensions. This ensures play logic improvements are measurable and regressions are detected.

---

## Scoring Dimensions

### 1. Legality Score (CRITICAL - Must be 100%)

**Definition:** Percentage of plays that follow game rules

**Checks:**
- ✅ Card played is in player's hand
- ✅ Suit followed when required
- ✅ Card selection is legal (not void when suit exists)
- ✅ Trick rules followed correctly

**Target:** 100% (any illegal play is critical bug)

---

### 2. Success Rate (Target 70%+)

**Definition:** Percentage of contracts successfully made by declarer

**Checks:**
- ✅ Declarer makes contract with makeable hands
- ✅ Defense defeats vulnerable contracts
- ✅ Appropriate risk-taking based on vulnerability

**Baseline expectations by AI level:**
- Simple AI (1-2/10): 50-60% success rate
- Minimax depth 1 (3-4/10): 60-70% success rate
- Minimax depth 2 (5-8/10): 70-80% success rate
- DDS (9-10/10): 85-95% success rate

**Target:** 70%+ for level 8 AI

---

### 3. Efficiency Score (Target 55%+)

**Definition:** Balance between overtricks and undertricks

**Formula:**
```
Efficiency = 50 + (Overtricks - Undertricks) / Total_Contracts * 10
Range: 0-100%, 50% = neutral
```

**What it measures:**
- Positive efficiency: More overtricks than undertricks (aggressive, good)
- Negative efficiency: More undertricks than overtricks (conservative, poor)

**Target:** 55%+ (slightly positive efficiency)

---

### 4. Tactical Quality (Target 90%+)

**Definition:** Percentage of plays that avoid tactical errors

**Tactical errors:**
- ❌ Finessing when should cash (or vice versa)
- ❌ Discarding winners
- ❌ Blocking suits
- ❌ Failing to unblock
- ❌ Poor trump management
- ❌ Defensive signals ignored

**Target:** 90%+ (most plays tactically sound)

---

### 5. Timing Performance (Target 85%+)

**Definition:** Speed of play decisions

**Benchmarks:**
- <1s per hand: Excellent (100%)
- <5s per hand: Good (90%)
- <10s per hand: Acceptable (75%)
- >10s per hand: Poor (50%)

**Target:** <5s average per hand

---

## Composite Play Quality Score

**Formula:**
```
PQS = (Legality × 0.30) +          # Must be perfect (30%)
      (Success Rate × 0.25) +      # Critical (25%)
      (Efficiency × 0.20) +        # Important (20%)
      (Tactical × 0.15) +          # Important (15%)
      (Timing × 0.10)              # Performance (10%)
```

**Grading Scale:**
- 🟢 **A (95-100%):** Excellent play
- 🟡 **B (90-94%):** Good play
- 🟠 **C (85-89%):** Acceptable play
- 🔴 **D (80-84%):** Poor play
- ⛔ **F (<80%):** Failing play

---

## AI Level Baselines

### Expected Performance by Level

| Level | AI Type | Bidding | Play | Combined |
|-------|---------|---------|------|----------|
| 1-2/10 | Simple | 85-88% | 75-80% | 80-84% (D) |
| 3-4/10 | Minimax d1 | 88-90% | 80-85% | 84-87% (C) |
| 5-6/10 | Minimax d2 | 90-92% | 85-88% | 87-90% (B-) |
| 7-8/10 | Minimax d2 | 91-93% | 88-91% | 89-92% (B) |
| 9-10/10 | DDS | 93-95% | 92-96% | 92-95% (A) |

**Note:** Bidding uses same scoring system. Play scoring is new.

---

## Current Baseline (as of 2025-10-28)

### Level 8 (8/10 AI - Minimax depth 2)

**Bidding Quality Score:** 91.3% (Grade B+)
- Test: 100 hands
- Improvement from general baseline (89.7% → 91.3%)
- Shows bidding is stronger than average

**Play Quality Score:** ⏳ Pending
- Awaits PlayEngine integration
- Manual testing shows ~75-80% success rate
- Estimated composite: 88-90%

**Combined Estimated Score:** ~90% (Grade B)

---

## Implementation Status

### ✅ Completed
1. Play quality score framework (`test_play_quality_score.py`)
2. AI levels baseline framework (`test_ai_levels_baseline.py`)
3. Bidding baseline for level 8 (91.3%)
4. Scoring dimensions defined
5. Grading criteria established

### ⏳ Pending
1. Full PlayEngine integration for automated testing
2. Actual play quality measurements
3. Tactical error detection
4. Historical baselines for all levels

### 🎯 Next Steps
1. Integrate with existing PlayEngine
2. Run 500-hand baseline for level 8
3. Establish baselines for levels 1, 3, 5, 9
4. Document baseline in protocol

---

## Usage (When Implemented)

### Testing Specific AI Level

```bash
# Quick test (100 hands)
python3 backend/test_ai_levels_baseline.py --level 8 --hands 100

# Comprehensive test (500 hands)
python3 backend/test_ai_levels_baseline.py --level 8 --hands 500
```

### Testing All Key Levels

```bash
# Tests levels 1, 3, 5, 8, 9 (if DDS available)
python3 backend/test_ai_levels_baseline.py --hands 500
```

### Play Quality Only

```bash
# Test play with Minimax depth 2
python3 backend/test_play_quality_score.py --hands 500 --ai minimax --depth 2

# Test play with Simple AI
python3 backend/test_play_quality_score.py --hands 500 --ai simple

# Test play with DDS (production only)
python3 backend/test_play_quality_score.py --hands 500 --ai dds
```

---

## Standard Workflow (When Implemented)

### Before Play Logic Changes

```bash
# 1. Establish baseline
python3 backend/test_play_quality_score.py --hands 500 --ai minimax --depth 2 --output baseline_before.json
```

### During Development

```bash
# Quick checks (100 hands)
python3 backend/test_play_quality_score.py --hands 100 --ai minimax --depth 2
```

### Before Committing

```bash
# 1. Comprehensive test
python3 backend/test_play_quality_score.py --hands 500 --ai minimax --depth 2 --output baseline_after.json

# 2. Compare
python3 compare_play_scores.py baseline_before.json baseline_after.json

# 3. Only commit if no regression
```

---

## Blocking Criteria

**DO NOT COMMIT if:**
- Legality score < 100% (illegal plays)
- Success rate drops >5% from baseline
- Composite score drops >2% from baseline
- Timing increases >50% from baseline

---

## Testing on Production (DDS)

### Special Considerations for DDS Testing

**DDS (Double Dummy Solver) is only available on Linux production:**
- ✅ Linux: DDS enabled, can test level 9/10
- ❌ macOS: DDS disabled (crashes on M1/M2)
- ❌ Windows: DDS not tested

### Production Testing Protocol

```bash
# On production server only
python3 backend/test_ai_levels_baseline.py --level 9 --hands 500

# Expected results:
# - Bidding: 93-95%
# - Play: 92-96%
# - Combined: 92-95% (Grade A)
```

### When to Test DDS

- Before deploying play logic changes to production
- Monthly baseline checks
- After any DDS library updates
- When users report play quality issues

---

## Integration with Coding Guidelines

### To Be Added

This protocol will be added to `.claude/CODING_GUIDELINES.md` once PlayEngine integration is complete, following the same pattern as the bidding quality protocol:

1. When to run play quality score
2. How to run tests
3. Standard workflow
4. Quality requirements
5. Blocking criteria
6. Historical baselines

---

## Historical Baselines (To Be Established)

### Template for Future Baselines

```
Date: YYYY-MM-DD
Test: 500 hands
AI Level: X/10

Bidding Quality:
- Composite: X.X%
- Appropriateness: X.X%
- Conventions: X.X%

Play Quality:
- Composite: X.X%
- Success Rate: X.X%
- Efficiency: X.X%

Combined Score: X.X% (Grade X)
```

---

## Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Bidding Quality** | ✅ Complete | Baseline: 91.3% for level 8 |
| **Play Quality Framework** | ✅ Complete | Awaits PlayEngine integration |
| **Level 8 Baseline** | 🔄 Partial | Bidding done, play pending |
| **Multi-Level Testing** | ✅ Framework | Script ready, needs execution |
| **DDS Testing** | 📋 Documented | Production-only protocol |
| **Coding Guidelines** | ⏳ Pending | Awaits full implementation |

---

## Files Created

1. ✅ `backend/test_play_quality_score.py` - Play quality scoring
2. ✅ `backend/test_ai_levels_baseline.py` - Multi-level testing
3. ✅ `PLAY_QUALITY_SCORE_PROTOCOL.md` - This document
4. ✅ `ai_baselines/` directory - Results storage
5. ⏳ `compare_play_scores.py` - To be created

---

## Next Actions

### Immediate (For You to Decide)

1. **Option A:** Proceed with appropriateness fix first (bidding improvements)
   - Already have baseline (91.3%)
   - Can measure improvement immediately
   - Play testing can wait

2. **Option B:** Implement PlayEngine integration for play testing
   - Enables full play quality baselines
   - More comprehensive testing
   - Takes longer to implement

3. **Option C:** Do both in parallel
   - Fix bidding appropriateness
   - Integrate play testing
   - Most comprehensive approach

**Recommendation:** Option A - fix bidding first (you have baseline), then add play testing.

---

## Summary

✅ **Bidding Quality:** Baseline established (91.3% for level 8)
✅ **Play Quality Framework:** Created and ready
⏳ **Full Play Testing:** Awaits PlayEngine integration
📋 **Protocol:** Documented and ready to implement
🎯 **Next:** Your decision on priority

The framework is ready - we just need to wire it up to the actual PlayEngine once you decide when to prioritize that work.
