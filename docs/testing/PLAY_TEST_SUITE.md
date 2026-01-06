# Play Test Suite

**Purpose:** Comprehensive testing infrastructure for the card play engine.

**Goal:** Ensure AI card play is accurate, efficient, and produces human-understandable decisions.

---

## Quick Reference

### Daily Development
```bash
cd backend
./test_quick.sh                    # 30 sec - unit tests only
pytest tests/play/ -v              # Play-specific unit tests
```

### Before Committing Play Changes
```bash
# 1. Establish baseline (Level 8 Minimax for macOS)
python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 2 --output play_before.json

# 2. Make your changes...

# 3. Test after changes
python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 2 --output play_after.json

# 4. Compare (MUST pass)
python3 ../compare_play_scores.py play_before.json play_after.json
```

### Comprehensive Testing (Before Merge/Deploy)
```bash
# 500 hands - production-grade validation
python3 test_play_quality_integrated.py --hands 500 --ai minimax --depth 2 --output production_play.json

# On production server (Linux) - DDS testing
python3 test_play_quality_integrated.py --hands 500 --ai dds --output dds_baseline.json
```

---

## AI Levels Overview

| Level | AI Type | Performance | Success Rate | Use Case |
|-------|---------|-------------|--------------|----------|
| 1-6 | SimplePlayAI | <1s/hand | 40-60% | Quick testing |
| 7-8 | MinimaxPlayAI | 2-3s/hand | 70-80% | Development (macOS) |
| 9-10 | DDS | <1ms/play | 95%+ | Production (Linux only) |

**Platform Notes:**
- **macOS:** Use Level 8 (Minimax) - DDS crashes on M1/M2
- **Linux:** Use Level 10 (DDS) - Optimal play analysis
- **Production:** DDS is the default

---

## Test Categories

### 1. Unit Tests (`backend/tests/play/`)

**Purpose:** Fast tests for individual play components.

**Runtime:** ~1 minute

**Key Files:**
| File | What It Tests |
|------|--------------|
| `test_evaluation.py` | Position evaluator for Minimax |
| `test_minimax_ai.py` | MinimaxPlayAI search and selection |
| `test_simple_ai.py` | SimplePlayAI rule-based logic |
| `test_dds_analysis.py` | DDS board solving |
| `test_discard_quality.py` | Discard decision logic |
| `test_tactical_signal_overlay.py` | Tactical signaling |
| `test_play_evaluation_api.py` | Play evaluation endpoints |
| `test_convention_play_scenarios.py` | Play after conventions |

**Run:**
```bash
pytest tests/play/ -v
```

---

### 2. Integration Tests

**Purpose:** Test complete play flows and engine interactions.

**Key Files:**
| File | What It Tests |
|------|--------------|
| `tests/integration/test_standalone_play.py` | Play without bidding |
| `tests/integration/play_test_helpers.py` | Test utilities |
| `tests/features/test_play_endpoints.py` | API endpoints |
| `tests/features/test_gameplay_review.py` | Play review features |

**Run:**
```bash
pytest tests/integration/test_standalone_play.py -v
pytest tests/features/test_play_endpoints.py -v
```

---

### 3. Regression Tests

**Purpose:** Prevent fixed bugs from reoccurring.

**Key Files:**
| File | Bug Prevented |
|------|--------------|
| `test_opening_lead_not_played_*.py` | Opening lead selection |
| `test_player_rotation_bug_*.py` | Player rotation during play |
| `test_single_player_dummy_control.py` | Dummy control issues |
| `test_play_bug.py` | Various play engine bugs |
| `test_trick_leader_bug.py` | Trick leader tracking |
| `test_discard_fix.py` | Discard logic |
| `test_master_trump_bug.py` | Trump handling |
| `test_trick11_bug.py` | Late trick evaluation |

**Run:**
```bash
pytest tests/regression/test_*play*.py tests/regression/test_*trick*.py -v
```

---

### 4. DDS Tests

**Purpose:** Validate Double Dummy Solver integration.

**Key Files:**
| File | What It Tests |
|------|--------------|
| `test_dds_e2e.py` | End-to-end DDS gameplay |
| `test_dds_simple.py` | Basic DDS availability |
| `test_dds_quick.py` | Quick DDS verification |
| `test_dds_integration.py` | DDS with PlayEngine |
| `test_dds_fallback.py` | Graceful fallback |
| `run_dds_baseline.py` | DDS baseline runner |

**Run (Linux only):**
```bash
python3 test_dds_e2e.py
python3 test_dds_simple.py
```

---

## Quality Score System

### Main Quality Scorer

**File:** `backend/test_play_quality_integrated.py`

**What It Measures:**

| Metric | Weight | Target | Description |
|--------|--------|--------|-------------|
| Legality | 30% | 100% | No illegal plays (MUST be 100%) |
| Success Rate | 25% | ≥70% | Contracts made percentage |
| Efficiency | 20% | ≥55% | Overtricks vs undertricks |
| Tactical | 15% | ≥90% | Few tactical errors |
| Timing | 10% | ≥85% | Performance speed |

**Grading Scale:**
- **A (95+%):** Excellent
- **B (90-94%):** Good
- **C (85-89%):** Acceptable
- **D (80-84%):** Poor
- **F (<80%):** Failing

**Usage:**
```bash
# Quick test with SimpleAI (2 minutes)
python3 test_play_quality_integrated.py --hands 100 --ai simple

# Standard test with Minimax (10 minutes)
python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 2

# Comprehensive test (30 minutes)
python3 test_play_quality_integrated.py --hands 500 --ai minimax --depth 2 --output play_baseline.json

# Production test with DDS (Linux only)
python3 test_play_quality_integrated.py --hands 500 --ai dds --output dds_baseline.json
```

**Sample Output:**
```
================================================================================
INTEGRATED PLAY QUALITY SCORE REPORT
================================================================================

AI Type:           MINIMAX (depth 2)
Hands Tested:      500
Contracts Played:  487
Passed Out:        13
Contracts Made:    358 (73.5%)
Contracts Failed:  129
Overtricks:        247
Undertricks:       412
Cards Played:      25,324

--------------------------------------------------------------------------------
INDIVIDUAL SCORES:
--------------------------------------------------------------------------------
  1. Legality:      100.0% ✅ (0 errors)
  2. Success Rate:   73.5% ✅
  3. Efficiency:     48.2% ⚠️
  4. Tactical:      100.0% ✅ (0 errors)
  5. Timing:         90.0% ✅

--------------------------------------------------------------------------------
COMPOSITE SCORE: 82.8%
GRADE:           C (Acceptable)
--------------------------------------------------------------------------------

TIMING METRICS:
  Avg Time/Hand: 2.341s
  Min Time:      0.892s
  Max Time:      8.127s
================================================================================
```

---

### Comparison Tool

**File:** `compare_play_scores.py`

**Purpose:** Detect regressions between baseline and new scores.

**Regression Thresholds:**
- Legality: Must stay at 100%
- Composite: Max -2% drop allowed
- Success Rate: Max -5% drop allowed
- Timing: Max +50% increase allowed

**Usage:**
```bash
python3 compare_play_scores.py play_before.json play_after.json
```

**Sample Output:**
```
================================================================================
PLAY QUALITY SCORE COMPARISON
================================================================================

Baseline AI: MINIMAX (depth 2)
New AI:      MINIMAX (depth 2)

Metric               Baseline        New      Delta     Status
--------------------------------------------------------------------------------
Legality              100.0%     100.0%     +0.0%        ✅ OK
Success rate           73.5%      75.2%     +1.7%        ✅ OK
Efficiency             48.2%      51.8%     +3.6%        ✅ OK
Tactical              100.0%     100.0%     +0.0%        ✅ OK
Timing                 90.0%      90.0%     +0.0%        ✅ OK
Composite              82.8%      84.1%     +1.3%        ✅ OK
--------------------------------------------------------------------------------

Performance           Baseline        New      Delta
--------------------------------------------------------------------------------
Contracts Made %        73.5%      75.2%     +1.7%
Overtricks               247        263       +16
Undertricks              412        387       -25
Avg Time/Hand (s)      2.341      2.287     -0.054
--------------------------------------------------------------------------------

✅ Quality score acceptable - no significant regression
```

---

## Play AI Components

### SimplePlayAI (Levels 1-6)

**File:** `backend/engine/play/ai/simple_ai.py`

**Strategy:** Rule-based heuristics

**Rules Tested:**
- 2nd hand low
- 3rd hand high
- Cover an honor with an honor
- Lead through strength
- Return partner's lead
- Trump management

**Best For:** Quick testing, low-resource environments

---

### MinimaxPlayAI (Levels 7-8)

**File:** `backend/engine/play/ai/minimax_ai.py`

**Strategy:** Alpha-beta pruning search

**Parameters:**
| Depth | Search | Performance | Accuracy |
|-------|--------|-------------|----------|
| 1 | 4 moves | <1s | 60-65% |
| 2 | 16 moves | 2-3s | 70-80% |
| 3 | 64 moves | 5-10s | 80-85% |

**Position Evaluation:**
- Tricks won component
- Sure winners estimation
- Card counting
- Trump management

**Best For:** Development on macOS, balanced speed/accuracy

---

### DDS AI (Levels 9-10)

**File:** `backend/engine/play/ai/dds_ai.py`

**Strategy:** Double Dummy Solver (perfect analysis)

**Requirements:**
- Linux OS (crashes on macOS M1/M2)
- `endplay` library installed

**Performance:**
- <1ms per play decision
- 95%+ optimal play
- Perfect defense calculation

**Best For:** Production deployment, validation baseline

---

## Test Shell Scripts

| Script | Runtime | What It Runs |
|--------|---------|--------------|
| `test_quick.sh` | 30 sec | Unit tests (includes play) |
| `test_medium.sh` | 2 min | Unit + integration |
| `test_full.sh` | 5+ min | All tests with coverage |

---

## Recommended Workflows

### New Feature Development
1. Write unit tests first (TDD)
2. Run `pytest tests/play/ -v` frequently
3. Run play quality score before finishing
4. Test with both SimpleAI and Minimax

### Bug Fixing
1. Check error logs: `python3 analyze_errors.py --category play_logic`
2. Create minimal reproduction test in `tests/regression/`
3. Run quality baseline before fix
4. Fix the bug
5. Verify with quality baseline after
6. Add regression test

### Before Merge
1. Run full test suite: `./test_full.sh`
2. Run play quality score:
   ```bash
   python3 test_play_quality_integrated.py --hands 500 --ai minimax
   ```
3. Compare with baseline: `python3 compare_play_scores.py`
4. Verify no regressions

### AI Changes
1. Test with SimpleAI first (fast feedback)
2. Test with Minimax depth 2 (development standard)
3. On production: Test with DDS (gold standard)
4. Compare all three for consistency

---

## Quality Requirements

### BLOCKING (Must Pass)

| Requirement | Threshold |
|-------------|-----------|
| Legality | 100% (no illegal plays) |
| Composite | ≥ baseline - 2% |
| Success Rate | ≥ baseline - 5% |
| Timing | ≤ baseline + 50% |
| Unit tests | All pass |
| Regression tests | All pass |

### TARGET (Quality Goals)

| Metric | Minimax Target | DDS Target |
|--------|----------------|------------|
| Legality | 100% | 100% |
| Success Rate | 75%+ | 95%+ |
| Efficiency | 55%+ | 80%+ |
| Tactical | 95%+ | 99%+ |
| Composite | 85%+ | 95%+ |

---

## Platform-Specific Testing

### macOS Development

```bash
# Use Minimax (DDS crashes on M1/M2)
python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 2

# Skip DDS tests
pytest tests/play/ -v -k "not dds"
```

### Linux/Production

```bash
# Use DDS for gold standard
python3 test_play_quality_integrated.py --hands 500 --ai dds

# Run DDS-specific tests
python3 test_dds_e2e.py
python3 run_dds_baseline.py
```

### CI/CD (GitHub Actions)

DDS baseline workflow: `.github/workflows/dds_baseline.yml`

```yaml
# Triggers: manual dispatch
# Environment: Linux (DDS support)
# Inputs: hands (default 500), ai_level (default dds)
```

---

## File Locations

```
bridge_bidding_app/
├── backend/
│   ├── test_play_quality_integrated.py  # Main quality scorer
│   ├── test_play_quality_score.py       # Legacy quality scorer
│   ├── test_dds_*.py                    # DDS test scripts
│   ├── test_ai_levels_baseline.py       # AI level comparison
│   ├── run_dds_baseline.py              # DDS baseline runner
│   ├── test_ai_play_validation.py       # AI control validation
│   ├── tests/
│   │   └── play/                        # Play unit tests
│   │       ├── test_evaluation.py
│   │       ├── test_minimax_ai.py
│   │       ├── test_simple_ai.py
│   │       ├── test_dds_analysis.py
│   │       └── ...
│   └── engine/play/
│       ├── play_engine.py               # Main play orchestrator
│       └── ai/
│           ├── simple_ai.py             # Level 1-6
│           ├── minimax_ai.py            # Level 7-8
│           ├── dds_ai.py                # Level 9-10
│           └── evaluation.py            # Position evaluator
├── compare_play_scores.py               # Baseline comparison tool
└── docs/testing/
    └── PLAY_TEST_SUITE.md               # This document
```

---

## Current Baseline

### Minimax (Level 8, Depth 2) - Development Standard

```
Test: 500 hands

Composite: ~83% (Grade C)

Breakdown:
- Legality:      100.0% ✅
- Success Rate:   73.5%
- Efficiency:     48.2% (improvement area)
- Tactical:      100.0% ✅
- Timing:         90.0% ✅
```

### DDS (Level 10) - Production Standard

```
Test: 500 hands (Linux only)

Composite: ~95% (Grade A)

Breakdown:
- Legality:      100.0% ✅
- Success Rate:   95%+  ✅
- Efficiency:     80%+  ✅
- Tactical:       99%+  ✅
- Timing:        100%   ✅ (<1ms/play)
```

**Priority Improvement Areas:**
1. Efficiency (48% → 55% Minimax target)
2. Success Rate (73% → 75% Minimax target)
3. Defensive play optimization
4. Trump management
