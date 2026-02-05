# Bidding Test Suite

**Purpose:** Comprehensive testing infrastructure for the SAYC bidding engine.

**Goal:** Ensure bidding logic produces quality, human-understandable bids that follow SAYC conventions.

---

## Quick Reference

### Daily Development
```bash
cd backend
./test_quick.sh                    # 30 sec - unit tests only
```

### Before Committing Bidding Changes
```bash
# 1. Establish baseline
python3 test_bidding_quality_score.py --hands 100 --output baseline_before.json

# 2. Make your changes...

# 3. Test after changes
python3 test_bidding_quality_score.py --hands 100 --output baseline_after.json

# 4. Compare (MUST pass)
python3 ../compare_scores.py baseline_before.json baseline_after.json
```

### Comprehensive Testing (Before Merge/Deploy)
```bash
# 500 hands - production-grade validation
python3 test_bidding_quality_score.py --hands 500 --output production_baseline.json

# V2 Schema Engine efficiency analysis
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42
```

---

## Test Categories

### 1. Unit Tests (`backend/tests/unit/`)

**Purpose:** Fast tests for individual bidding components.

**Runtime:** ~30 seconds

**Key Files:**
| File | What It Tests |
|------|--------------|
| `test_stayman.py` | Stayman convention |
| `test_jacoby_transfers.py` | Jacoby Transfer bids |
| `test_negative_doubles.py` | Negative double handling |
| `test_responses.py` | Response bidding logic |
| `test_phase3_conventions.py` | Advanced conventions |
| `test_bridge_rules_engine.py` | Core bidding rules |
| `test_module_registry.py` | Module registration |
| `test_sanity_checker.py` | Bid sanity validation |

**Run:**
```bash
pytest tests/unit/ -v
```

---

### 2. Integration Tests (`backend/tests/integration/`)

**Purpose:** Test bidding module interactions and complete auction flows.

**Runtime:** ~2 minutes

**Key Files:**
| File | What It Tests |
|------|--------------|
| `test_bidding_fixes.py` | Historical bidding bug fixes |
| `test_competitive_auctions.py` | Competitive bidding scenarios |
| `test_slam_bidding.py` | Slam detection and bidding |
| `test_blackwood_grand_slam.py` | Blackwood/Grand Slam sequences |
| `test_architecture_integration.py` | Module architecture |
| `test_core_integration.py` | Core engine integration |

**Run:**
```bash
pytest tests/integration/ -v
```

---

### 3. Regression Tests (`backend/tests/regression/`)

**Purpose:** Prevent fixed bugs from reoccurring.

**Key Files:**
| File | Bug Prevented |
|------|--------------|
| `test_2club_forcing_fix.py` | 2♣ forcing bid handling |
| `test_double_declarer_fix.py` | Double/redouble declarer issues |
| `test_first_hand_bug.py` | First hand initialization |
| `test_illegal_bid_bug.py` | Illegal bid generation |
| `test_jacoby_fix.py` | Jacoby transfer completion |
| `test_negative_double_rebid.py` | Rebids after negative doubles |
| `test_takeout_double_fix.py` | Takeout double responses |
| `test_west_response_fix.py` | West position responses |

**Run:**
```bash
pytest tests/regression/ -v
```

---

### 4. V3 Logic Stack Tests (`backend/tests/v3/`)

**Purpose:** Comprehensive tests for V3 bidding logic that uses ACTUAL HCP (not midpoint estimates) and implements the Borrowed King principle for balancing.

**Runtime:** ~30 seconds (quick), ~2 minutes (full)

**Key Files:**
| File | What It Tests |
|------|--------------|
| `v3_logic_test_suite.json` | Test case definitions for all V3 levels |
| `test_v3_logic.sh` | Shell script runner for automated testing |
| `test_v3_bidding.py` | Python pytest tests for bidding engine |

**Test Levels Covered:**
| Level | Category | Tests |
|-------|----------|-------|
| Level 1 | Basic Bidding Actions | Pass, Opening bids, Raises, Responses |
| Level 2 | Opener's Rebid | Minimum rebid, Raise responder |
| Level 4 | Competitive Bidding | Overcalls, Takeout doubles, Balancing |
| Conventions | Essential SAYC | Stayman, Jacoby, Blackwood, Negative Double |

**Run:**
```bash
# Quick smoke test
bash tests/v3/test_v3_logic.sh --quick

# Full test suite
bash tests/v3/test_v3_logic.sh

# Level-specific tests
bash tests/v3/test_v3_logic.sh --level 1

# Python tests
pytest tests/v3/test_v3_bidding.py -v
```

**V3 Principles:**
1. **ACTUAL HCP:** Uses actual hand HCP, not midpoint estimates from partner's range
2. **Borrowed King:** +3 Virtual HCP Offset for balancing seat decisions
3. **Foundational Tier:** Basic bidding elements treated as convention-like modules

---

### 5. Scenario Tests (`backend/tests/scenarios/`)

**Purpose:** Test specific bidding situations and conventions.

**Key Files:**
| File | What It Tests |
|------|--------------|
| `test_convention_scenarios.py` | Convention-specific hands |
| `test_all_1nt_conventions.py` | 1NT opening and responses |
| `test_stayman_7hcp.py` | Minimum Stayman requirements |
| `test_manual_scenarios.py` | Hand-crafted test cases |

**Run:**
```bash
pytest tests/scenarios/ -v
```

---

### 6. SAYC Baseline Tests (`backend/tests/sayc_baseline/`)

**Purpose:** Validate V2 schema engine against SAYC standard.

**Key Files:**
| File | What It Tests |
|------|--------------|
| `test_baseline_v2.py` | V2 schema compliance |
| `test_baseline_compliance.py` | V1 baseline comparison |
| `compare_v1_v2.py` | V1 vs V2 differences |
| `ratchet_tracker.py` | Progress tracking |

**Run:**
```bash
pytest tests/sayc_baseline/ -v
```

---

## Quality Score System

### Main Quality Scorer

**File:** `backend/test_bidding_quality_score.py`

**What It Measures:**

| Metric | Weight | Target | Description |
|--------|--------|--------|-------------|
| Legality | 30% | 100% | No illegal bids (MUST be 100%) |
| Appropriateness | 25% | ≥95% | Bids match hand strength |
| Conventions | 15% | ≥90% | Correct convention usage |
| Consistency | 10% | ≥85% | Same hand → same bid |
| Reasonableness | 15% | ≥90% | Subjective bid quality |
| Game/Slam | 5% | ≥80% | Reaches correct level |

**Grading Scale:**
- **A (95+%):** Production Ready
- **B (90-94%):** Good, minor issues
- **C (85-89%):** Acceptable, needs work
- **D (80-84%):** Poor, major issues
- **F (<80%):** Failing, do not deploy

**Usage:**
```bash
# Quick test (5 minutes)
python3 test_bidding_quality_score.py --hands 100

# Comprehensive test (15 minutes)
python3 test_bidding_quality_score.py --hands 500 --output baseline.json
```

**Sample Output:**
```
================================================================================
BIDDING QUALITY SCORE REPORT
================================================================================

Hands Tested:      500
Total Bids:        3,013
Non-Pass Bids:     1,847

--------------------------------------------------------------------------------
INDIVIDUAL SCORES:
--------------------------------------------------------------------------------
  1. Legality:        100.0% ✅ (0 errors)
  2. Appropriateness:  78.7% ⚠️  (392 errors)
  3. Conventions:      99.7% ✅ (3 errors)
  4. Consistency:     100.0% ✅ (not implemented)
  5. Reasonableness:   92.1% ✅
  6. Game/Slam:        24.7% ❌ (needs work)

--------------------------------------------------------------------------------
COMPOSITE SCORE: 89.7%
GRADE:           C (Acceptable, needs work)
--------------------------------------------------------------------------------
```

---

### Comparison Tool

**File:** `compare_scores.py`

**Purpose:** Detect regressions between baseline and new scores.

**Regression Thresholds:**
- Legality: Must stay at 100%
- Composite: Max -2% drop allowed
- Appropriateness: Max -5% drop allowed

**Usage:**
```bash
python3 compare_scores.py baseline_before.json baseline_after.json
```

**Sample Output:**
```
================================================================================
QUALITY SCORE COMPARISON
================================================================================

Metric               Baseline        New      Delta     Status
--------------------------------------------------------------------------------
Legality              100.0%     100.0%     +0.0%        ✅ OK
Appropriateness        78.7%      82.3%     +3.6%        ✅ OK
Conventions            99.7%      99.8%     +0.1%        ✅ OK
Reasonableness         92.1%      93.4%     +1.3%        ✅ OK
Game_slam              24.7%      28.9%     +4.2%        ✅ OK
Composite              89.7%      91.2%     +1.5%        ✅ OK
--------------------------------------------------------------------------------

✅ Quality score acceptable - no significant regression
```

---

### V2 Schema Efficiency Analysis

**File:** `backend/analyze_bidding_efficiency.py`

**Purpose:** Analyze bidding accuracy against Double Dummy Solver (DDS).

**What It Measures:**
- **Efficiency Gap:** `Tricks_Required - DDS_Max_Tricks`
- **Accuracy Rate:** Contracts at exactly makeable level
- **Overbid Rate:** Contracts bid too high
- **Critical Failures:** Severe overbids (Gap ≥ 3)

**Targets:**
| Metric | Target |
|--------|--------|
| Accuracy Rate | ≥25% |
| Overbid Rate | <50% |
| Mean Gap | <+1.5 tricks |
| Critical Failures | <40 per 200 hands |

**Usage:**
```bash
# Requires V2 schema engine enabled
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42

# With output file and visualization
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --output results.json --chart efficiency.png
```

**Rule Falsification Report:**
The tool identifies which schema rules cause overbids:
```
Rules with Critical Overbids (Gap ≥ 2):
------------------------------------------------------------
Rule ID                               Uses  Fails     Rate  Mean Gap
------------------------------------------------------------
v1_fallback                             68     48    70.6%    +2.72
slam_after_rkcb_5d_hearts                2      2   100.0%    +3.50
```

---

## Test Shell Scripts

| Script | Runtime | What It Runs |
|--------|---------|--------------|
| `test_quick.sh` | 30 sec | Unit tests only |
| `test_medium.sh` | 2 min | Unit + integration |
| `test_full.sh` | 5+ min | All tests with coverage |
| `test_full.sh --with-efficiency` | 10+ min | All + V2 efficiency |

---

## Error Analysis

**File:** `backend/analyze_errors.py`

**Purpose:** Analyze production error logs for bidding issues.

**Usage:**
```bash
# Summary of all errors
python3 analyze_errors.py

# Recent errors with context
python3 analyze_errors.py --recent 20

# Detect recurring patterns
python3 analyze_errors.py --patterns

# Filter by category
python3 analyze_errors.py --category bidding_logic
```

---

## Recommended Workflows

### New Feature Development
1. Write unit tests first (TDD)
2. Run `./test_quick.sh` frequently
3. Run quality score before finishing
4. Add regression tests if fixing bugs

### Bug Fixing
1. Check error logs first: `python3 analyze_errors.py --recent 10`
2. Create minimal reproduction test
3. Run quality baseline before fix
4. Fix the bug
5. Verify with quality baseline after
6. Add regression test

### Before Merge
1. Run full test suite: `./test_full.sh`
2. Run quality score: `python3 test_bidding_quality_score.py --hands 500`
3. Compare with baseline: `python3 compare_scores.py`
4. Verify no regressions

### Convention Changes
1. Run 500-hand quality score baseline
2. Make convention changes
3. Run 500-hand quality score again
4. Use efficiency analysis for deep validation
5. Review rule falsification report

---

## Quality Requirements

### BLOCKING (Must Pass)

| Requirement | Threshold |
|-------------|-----------|
| Legality | 100% (no illegal bids) |
| Composite | ≥ baseline - 2% |
| Appropriateness | ≥ baseline - 5% |
| Unit tests | All pass |
| Regression tests | All pass |

### TARGET (Quality Goals)

| Metric | Current | Target |
|--------|---------|--------|
| Legality | 100% | 100% |
| Appropriateness | 78.7% | 95%+ |
| Conventions | 99.7% | 99%+ |
| Reasonableness | 92.1% | 95%+ |
| Game Finding | 24.7% | 80%+ |
| Composite | 89.7% | 95%+ |

---

## File Locations

```
bridge_bidding_app/
├── backend/
│   ├── test_bidding_quality_score.py    # Main quality scorer
│   ├── analyze_bidding_efficiency.py    # V2 efficiency analysis
│   ├── analyze_errors.py                # Error log analysis
│   ├── test_quick.sh                    # Quick test runner
│   ├── test_medium.sh                   # Medium test runner
│   ├── test_full.sh                     # Full test runner
│   └── tests/
│       ├── unit/                        # Unit tests
│       ├── integration/                 # Integration tests
│       ├── regression/                  # Regression tests
│       ├── scenarios/                   # Scenario tests
│       └── sayc_baseline/               # V2 baseline tests
├── compare_scores.py                    # Baseline comparison tool
└── docs/testing/
    └── BIDDING_TEST_SUITE.md            # This document
```

---

## Current Baseline (as of 2025-10-28)

```
Test: 500 hands, 3,013 bids

Composite: 89.7% (Grade C)

Breakdown:
- Legality:        100.0% ✅
- Appropriateness:  78.7% (improvement area)
- Conventions:      99.7% ✅
- Reasonableness:   92.1% ✅
- Game/Slam:        24.7% (needs work)
```

**Priority Improvement Areas:**
1. Game finding (25% → 80% target)
2. Appropriateness (79% → 95% target)
3. Slam detection
