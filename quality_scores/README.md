# Quality Score History

This directory contains historical bidding quality scores for tracking improvements and detecting regressions.

## Current Baseline

**File:** `2025-10-28_baseline.json`
**Date:** October 28, 2025
**Composite Score:** 89.7% (Grade C - Acceptable, needs work)

### Breakdown:
- **Legality:** 100.0% ✅ (0 errors)
- **Appropriateness:** 78.7% ❌ (196 errors)
- **Conventions:** 99.7% ✅ (1 error)
- **Reasonableness:** 92.1% ✅
- **Game/Slam:** 24.7% ❌ (113 errors)

### Key Issues:
- 48% of errors: Bidding 3-card suits (94 errors)
- 15.8% of errors: Weak hands at 4-level (31 errors)
- 13.8% of errors: Weak hands at 3-level (27 errors)

---

## History

### 2025-10-28: Initial Baseline
- **Score:** 89.7% (Grade C)
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

### Short Term (Next Fix)
- **Appropriateness:** 78.7% → 90%+ (fix weak bids at high levels)
- **Composite:** 89.7% → 92%+ (Grade B)

### Medium Term (After Convention Fixes)
- **Appropriateness:** 90%+ → 95%+ (fix short suit bidding)
- **Composite:** 92%+ → 95%+ (Grade A)

### Long Term (Production Ready)
- **Legality:** 100% (maintain)
- **Appropriateness:** 95%+
- **Conventions:** 90%+
- **Composite:** 95%+ (Grade A)

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
