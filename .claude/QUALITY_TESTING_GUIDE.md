# Quality Assurance & Testing Guide

**Referenced from:** `CLAUDE.md` — Quality Assurance and Testing sections

For the trigger rules (when to run these), see `CLAUDE.md`. This file contains the detailed protocols.

---

## Bidding Quality Score Protocol

### How to Run
```bash
# Quick test (5 minutes, 100 hands) - during development
python3 backend/test_bidding_quality_score.py --hands 100

# Comprehensive test (15 minutes, 500 hands) - before commits
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_after.json

# Compare with baseline
python3 compare_scores.py baseline_before.json baseline_after.json
```

### Quality Requirements (BLOCKING)
- **Legality: 100%** (no illegal bids allowed)
- **Appropriateness: >= baseline** (no regression)
- **Composite: >= baseline - 2%** (small regression tolerance)

### Target Scores
- **Legality: 100%** (must be perfect)
- **Appropriateness: 95%+** (excellent)
- **Conventions: 90%+** (good)
- **Composite: 95%+** (Grade A - production ready)

### Current Baseline (as of 2025-10-28)
```
Test: 500 hands, 3,013 bids
Composite: 89.7% (Grade C)

Breakdown:
- Legality:        100.0%
- Appropriateness:  78.7% (improvement area)
- Conventions:      99.7%
- Reasonableness:   92.1%
- Game/Slam:        24.7% (needs work)
```

---

## Play Quality Score Protocol

### How to Run
```bash
# Quick test (10 minutes, 100 hands)
python3 backend/test_play_quality_integrated.py --hands 100 --level 8

# Comprehensive test (30 minutes, 500 hands)
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_after.json

# Compare with baseline
python3 compare_play_scores.py play_baseline_before.json play_after.json
```

### Quality Requirements (BLOCKING)
- **Legality: 100%** (no illegal plays allowed)
- **Success Rate: >= baseline - 5%**
- **Composite: >= baseline - 2%**
- **Timing: < baseline + 50%**

### Target Scores by AI Level
- **Level 8 (Minimax):** 80-85% composite (Grade B)
- **Level 10 (DDS):** 90-95% composite (Grade A)

### DDS Limitations
- DDS only works on Linux production servers
- Crashes on macOS M1/M2 chips
- Use Level 8 (Minimax) for development testing

**See:** `.claude/CODING_GUIDELINES.md` (lines 667-1027) for complete play protocol

---

## V2 Schema Engine Bidding Efficiency Test

### How to Run
```bash
# From backend/ directory
source venv/bin/activate

# Quick test (50 hands, ~2 minutes) - during development
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 50 --seed 42

# Comprehensive test (200 hands, ~5 minutes) - before commits
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 --output efficiency_results.json
```

### What This Test Does
1. Generates random hands locally
2. Runs V2 schema bidding engine locally
3. SSHs to production server for DDS analysis (Linux only)
4. Computes efficiency gap: `Tricks_Required - DDS_Max_Tricks`
5. Generates rule falsification reports
6. Creates visualization charts (`bidding_efficiency.png`)

### Key Metrics
- **Accuracy Rate (Gap=0):** Contracts at exactly makeable level
- **Overbid Rate (Gap>0):** Contracts bid too high
- **Mean Gap:** Average tricks overbid (target: < +1.5)
- **Critical Failures (Gap>=3):** Severe overbids

### Quality Requirements
- **Accuracy: >= 25%**
- **Overbid Rate: < 50%**
- **Mean Gap: < +1.5 tricks**
- **Critical Failures: < 40** per 200 hands

### Rule Falsification Audit
The test output includes a falsification report showing which specific rules cause overbids:
```
Rules with Critical Overbids (Gap >= 2):
------------------------------------------------------------
Rule ID                               Uses  Fails     Rate  Mean Gap
------------------------------------------------------------
v1_fallback                             68     48    70.6%    +2.72
slam_after_rkcb_5d_hearts                2      2   100.0%    +3.50
```

**Note:** Requires SSH access to production for DDS analysis.

---

## SAYC Compliance Benchmark

### How to Run
```bash
# From backend/ directory
source venv/bin/activate

# Quick test (100 hands, ~3 minutes) - during development
python3 test_sayc_compliance.py --hands 100 --output sayc_quick.json

# Comprehensive test (500 hands, ~10 minutes) - before commits
python3 test_sayc_compliance.py --hands 500 --output sayc_full.json --pbn sayc_full.pbn
```

### Categories Tested
1. **1NT Opening** — 15-17 HCP, balanced
2. **1M Opening** — 12+ HCP, 5+ cards in major
3. **Weak Two** — 6-10 HCP, exactly 6 cards
4. **2C Strong** — 22+ HCP or game-forcing hand
5. **Stayman** — 2C response to 1NT with 4-card major
6. **Jacoby Transfer** — 2D/2H response to 1NT with 5-card major
7. **Blackwood** — 4NT asking for aces, 16+ HCP
8. **Takeout Double** — 12+ HCP direct, 8+ balancing
9. **Negative Double** — Support for unbid major after overcall
10. **Preempts** — 3-level (7 cards), 4-level (8 cards)
11. **Strong Jump Shift** — 17+ HCP, 5+ card suit
12. **Splinter Bids** — 13+ HCP, 4+ trump support, singleton/void

### Quality Requirements (BLOCKING)
- **Overall Compliance: >= 95%** (minimum acceptable)
- **Critical Categories (1NT, 1M, Weak Two): 100%**
- **Advanced Categories: >= 90%**
- **Target: 99%+ overall compliance**

### Current Baseline (as of 2026-02-24)
```
Test: 500 hands, ~3,000 bids
Overall Compliance: 99.4%
- 1NT Opening:        100.0%
- 1M Opening:         100.0%
- Weak Two:           100.0%
- 2C Strong:          100.0%
- Stayman:            100.0%
- Jacoby Transfer:    100.0%
- Blackwood:          100.0%
- Takeout Double:      92.7% (minor edge cases)
- Negative Double:    100.0%
- Preempts:           100.0%
- Strong Jump Shift:  100.0%
- Splinter Bids:      100.0%
```

### Output Files
- **{output}.json** — Detailed compliance report with per-category scores
- **{output}.pbn** — PBN 2.1 format for external analysis

### Implementation Notes
- Test only checks **opening bids** (first non-pass bid), not overcalls/rebids
- Critical distinction: `hand.hcp` (opening requirements) vs `hand.total_points` (includes distribution)
- Errors categorized with context (hand data, auction, expected vs actual)

**See:** `backend/SAYC_COMPLIANCE_SUMMARY.md`, `backend/SAYC_COMPLIANCE_FIXES.md`

---

## Test Organization

```
backend/tests/
+-- unit/          # Fast unit tests - run constantly
+-- integration/   # Integration tests - run before commit
+-- regression/    # Bug fix tests - proves bugs stay fixed
+-- features/      # Feature tests - end-to-end validation
+-- scenarios/     # Specific bidding situations
+-- play/          # Card play engine tests

frontend/
+-- src/
|   +-- **/*.test.js   # Jest unit tests for React components
+-- e2e/
    +-- tests/
        +-- verification.spec.js      # Environment verification
        +-- app-smoke-test.spec.js    # Basic app functionality
        +-- *.spec.js                 # E2E test files (Playwright)
```

---

## Testing Rules

**ALWAYS:**
- Add tests for new features
- Add regression tests for bug fixes
- Run quick tests during development
- Run `./test_all.sh` before committing
- Run quality scores before bidding/play changes
- Add E2E tests for user-facing features
- Use `data-testid` attributes in React components for E2E testing

**NEVER:**
- Commit without running tests (pre-commit hook enforces this)
- Skip regression tests for bugs
- Modify bidding logic without baseline quality score
- Modify play logic without baseline quality score
- Use `git commit --no-verify` unless absolutely necessary

**E2E Best Practices:**
- Use `data-testid` attributes for stable selectors
- Test user behavior, not implementation details
- Keep tests independent (no shared state)
- Use `npm run test:e2e:ui` for debugging failed tests
- Add E2E test when fixing a regression bug
