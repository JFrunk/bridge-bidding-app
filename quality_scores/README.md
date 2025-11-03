# Quality Score History

This directory contains historical bidding quality scores for tracking improvements and detecting regressions.

## Current Baseline (2025-10-30)

### Bidding Quality Score

**File:** `baseline_20251030_145945.json`
**Date:** October 30, 2025
**Composite Score:** 94.8% (Grade B - Good, minor issues)

**Breakdown:**
- **Legality:** 100.0% ✅ (0 errors)
- **Appropriateness:** 100.0% ✅ (0 errors) - **MAJOR IMPROVEMENT**
- **Conventions:** 98.8% ✅ (3 errors)
- **Reasonableness:** 100.0% ✅
- **Game/Slam:** 0.0% ❌ (168 errors) - **Not yet implemented**

**Test Details:** 500 hands, 2,480 bids, 577 non-pass bids

### Play Quality Score

**File:** `play_baseline_20251030_151213.json`
**Date:** October 30, 2025
**AI Type:** MINIMAX (depth 2)
**Composite Score:** 80.3% (Grade D - Poor)

**Breakdown:**
- **Legality:** 100.0% ✅ (0 errors)
- **Success Rate:** 60.4% ⚠️ (206/341 contracts made)
- **Efficiency:** 50.9% ⚠️ (297 overtricks, 265 undertricks)
- **Tactical:** 100.0% ✅ (0 errors)
- **Timing:** 100.0% ✅

**Test Details:** 500 hands, 341 contracts played, 149 passed out

---

## History

### 2025-10-30: Updated Comprehensive Baseline
- **Bidding Score:** 94.8% (Grade B) - Up from 89.7%
- **Play Score:** 80.3% (Grade D)
- **Test:** 500 hands each
- **Notes:** Major improvement in bidding appropriateness (78.7% → 100%). Convention errors down to 3. Game/Slam scoring not yet implemented. Play engine shows 60.4% contract success rate with Minimax AI (depth 2).

### 2025-10-28: Initial Baseline
- **Bidding Score:** 89.7% (Grade C)
- **Test:** 500 hands, 3,013 bids
- **Notes:** First comprehensive baseline established. Identified systemic appropriateness issue with weak hands bidding at high levels after auto-adjustments.

---

## Usage

### Running New Tests

```bash
# Quick test (100 hands)
python3 backend/test_bidding_quality_score.py --hands 100

# Comprehensive test (500 hands)
python3 backend/test_bidding_quality_score.py --hands 500 --output quality_scores/YYYY-MM-DD_description.json
```

### Comparing Scores

```bash
# Compare against baseline
python3 compare_scores.py quality_scores/2025-10-28_baseline.json quality_scores/YYYY-MM-DD_description.json
```

### Adding New Entries

When adding a new quality score:

1. Run the test: `python3 backend/test_bidding_quality_score.py --hands 500 --output quality_scores/YYYY-MM-DD_description.json`
2. Compare to baseline: `python3 compare_scores.py baseline_quality_score_500.json quality_scores/YYYY-MM-DD_description.json`
3. Update this README with the new entry
4. If score improves significantly, update the baseline reference in root: `cp quality_scores/YYYY-MM-DD_description.json baseline_quality_score_500.json`

---

## Target Goals

### Bidding System

**Short Term (Next Fix):**
- **Conventions:** 98.8% → 99.5%+ (fix Stayman 4-card major requirement)
- **Game/Slam:** 0.0% → Implement scoring system
- **Composite:** 94.8% → 96%+ (Grade A-)

**Medium Term:**
- **Game/Slam:** Implement → 80%+ (basic game/slam detection)
- **Composite:** 96% → 97%+ (Grade A)

**Long Term (Production Ready):**
- **Legality:** 100% (maintain)
- **Appropriateness:** 100% (maintain)
- **Conventions:** 99%+
- **Game/Slam:** 90%+
- **Composite:** 98%+ (Grade A+)

### Play System

**Short Term:**
- **Success Rate:** 60.4% → 70%+ (improve Minimax depth 2 → 3)
- **Efficiency:** 50.9% → 60%+ (better overtrick/undertrick balance)
- **Composite:** 80.3% → 85%+ (Grade B-)

**Medium Term:**
- **Success Rate:** 70% → 80%+ (optimize Minimax heuristics)
- **Composite:** 85% → 90%+ (Grade A-)

**Long Term (Production Ready):**
- **Success Rate:** 85%+ (Minimax depth 3, DDS integration)
- **Efficiency:** 75%+
- **Composite:** 92%+ (Grade A)

---

## Naming Convention

Format: `YYYY-MM-DD_description.json`

Examples:
- `2025-10-28_baseline.json` - Initial baseline
- `2025-10-29_after_appropriateness_fix.json` - After implementing appropriateness validation
- `2025-10-30_after_short_suit_fix.json` - After fixing short suit bidding
- `2025-11-01_before_major_refactor.json` - Pre-refactor baseline

---

## Notes

- Always use 500 hands for comprehensive testing before commits
- Use 100 hands for quick iteration during development
- Keep at least 3 months of history
- Tag significant improvements in git: `git tag quality-score-95 -m "Achieved Grade A quality score"`
