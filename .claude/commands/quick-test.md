Run quick tests during development: $ARGUMENTS

Optional: Specify test category (unit/integration/regression/all)

---

## Quick Test Workflow

**Purpose:** Fast feedback loop during active development (30 seconds - 2 minutes)

---

## Option 1: Unit Tests Only (30 seconds)

**When:** Making small changes, want instant feedback

```bash
cd backend
./test_quick.sh
```

**Coverage:** Fast unit tests only, no integration or quality scores

---

## Option 2: Unit + Integration (2 minutes)

**When:** Finished feature, ready to commit

```bash
cd backend
./test_medium.sh
```

**Coverage:** Unit tests + integration tests, no quality scores

---

## Option 3: Specific Test File

**When:** Debugging specific module

```bash
# Single test file
pytest tests/unit/test_opening_bids.py -v

# Specific test function
pytest tests/unit/test_opening_bids.py::test_strong_2_clubs -v

# With output
pytest tests/unit/test_opening_bids.py -v -s
```

---

## Option 4: Bidding Quality Quick Check (5 minutes)

**When:** Changed bidding logic, want quick quality feedback

```bash
python3 backend/test_bidding_quality_score.py --hands 100
```

**Note:** 100 hands gives rough indication, not comprehensive

---

## Option 5: Play Quality Quick Check (10 minutes)

**When:** Changed play logic, want quick quality feedback

```bash
python3 backend/test_play_quality_integrated.py --hands 100 --level 8
```

**Note:** 100 hands gives rough indication, not comprehensive

---

## Test Output Interpretation

**All tests passed ✅:**
- Safe to continue development
- Ready for next iteration

**Some tests failed ❌:**
- Review failure messages
- Fix issues before continuing
- Run again to verify fix

**Quality score dropped ⚠️:**
- Review what changed
- Consider reverting if significant drop
- Run comprehensive baseline (500 hands) before commit

---

## Before Committing: Full Suite

**ALWAYS run full test suite before committing:**

```bash
cd backend
./test_full.sh  # 5+ minutes - runs everything
```

**Plus quality baselines if bidding/play logic changed:**
```bash
python3 backend/test_bidding_quality_score.py --hands 500
python3 backend/test_play_quality_integrated.py --hands 500 --level 8
```

---

## Success Criteria

✅ Quick tests for fast iteration (30s - 2min)
✅ Full tests before commit (5+ min)
✅ Quality baselines before committing bidding/play changes

Reference: CLAUDE.md Testing Strategy
