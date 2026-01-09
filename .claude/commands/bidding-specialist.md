---
description: Bidding AI Specialist Session
---

---
description: Bidding AI Specialist Session
---

# Bidding AI Specialist Session

You are entering a focused session for the **Bidding AI Engine** specialist area.

## Your Expertise

You are working on the SAYC (Standard American Yellow Card) bidding AI system. Your domain includes:

- Bidding modules: `opening_bids.py`, `responses.py`, `rebids.py`, `responder_rebids.py`, `overcalls.py`, `advancer_bids.py`
- All 12 conventions in `engine/ai/conventions/`
- Decision routing in `decision_engine.py`
- Bid validation in `validation_pipeline.py` and `sanity_checker.py`
- Feature extraction in `feature_extractor.py`

## Reference Documents

- **Code Context:** `backend/engine/CLAUDE.md` - Bidding engine architecture
- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Official SAYC bidding system
- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Card play mechanics

## Session Workflow

**Follow this order:**

### 1. Investigate First (NO branch yet)
- Read `backend/engine/CLAUDE.md` for architecture overview
- Analyze the issue - read relevant files, trace the problem
- Determine: Is this a **code fix** or just **analysis/explanation**?

### 2. If Code Changes Needed → Create Branch
Once you understand the scope and confirm code changes are required:
```bash
git checkout development && git pull origin development
git checkout -b feature/bidding-{short-description}
```
Use a descriptive name based on what you discovered (e.g., `fix-1nt-response`, `improve-preempt-logic`)

### 3. If Analysis Only → No Branch
If the user just needs explanation of why something happened, or the behavior is actually correct, no branch is needed.

## Key Commands

```bash
# Quick bidding tests
cd backend && pytest tests/unit/test_opening_bids.py tests/unit/test_responses.py -v

# Convention tests
pytest tests/unit/test_stayman.py tests/unit/test_jacoby_transfers.py -v

# Quality score (REQUIRED before committing code changes)
python3 test_bidding_quality_score.py --hands 100  # Quick check
python3 test_bidding_quality_score.py --hands 500  # Full baseline
```

## Baseline Testing Protocol

**CRITICAL: Always run baseline BEFORE and AFTER code changes**

### Step 1: Capture Baseline (BEFORE changes)
```bash
cd backend
python3 test_bidding_quality_score.py --hands 100 \
    --output /tmp/bidding_baseline_before.json
```

### Step 2: Make Your Changes
Implement the fix or improvement.

### Step 3: Run Post-Change Test
```bash
python3 test_bidding_quality_score.py --hands 100 \
    --output /tmp/bidding_baseline_after.json
```

### Step 4: Compare Results
```bash
# If compare_scores.py exists:
python3 compare_scores.py /tmp/bidding_baseline_before.json /tmp/bidding_baseline_after.json

# Or manually compare key metrics:
# - Legality must stay 100%
# - Appropriateness must not decrease
# - Composite score must not decrease by more than 2%
```

### Step 5: Update Stored Baseline (if improved)
If your change **improves** quality scores:
```bash
cp /tmp/bidding_baseline_after.json quality_scores/bidding_baseline.json
```
Document the improvement in your PR description.

## Workflow for Bug Fixes

1. **Investigate:** Read the hand data, trace decision_engine routing
2. **Diagnose:** Identify root cause - which module, which logic path
3. **Decide:** Is this a bug or expected behavior?
4. **If bug → Create branch** (see above)
5. **Fix:** Modify module logic
6. **Test:** Add regression test + run quality score
7. **Verify:** Ensure no regression in composite score

## Workflow for New Conventions

1. Create branch: `feature/bidding-add-{convention-name}`
2. Create `backend/engine/ai/conventions/convention_name.py`
3. Extend `ConventionModule`, implement `evaluate()`
4. Add `@ModuleRegistry.register('name')` decorator
5. Import in `bidding_engine.py`
6. Add routing in `decision_engine.py`
7. Create tests in `tests/unit/test_convention_name.py`
8. Run full quality score

## Quality Gates

**You MUST run quality score before committing any bidding changes:**

- Legality: 100% (blocking)
- Appropriateness: No regression (blocking)
- Composite: ≥ baseline - 2% (blocking)

## Out of Scope

Do NOT modify without coordinating with other specialists:
- `server.py` endpoints (API Server area)
- `play_engine.py` or play AI (Play Engine area)
- Frontend components (Frontend area)
- Dashboard/analytics (Learning area)

## Completing Work (if code was changed)

When your fix is complete and tested:

```bash
# Commit with descriptive message
git add -A
git commit -m "fix(bidding): description of change"

# Push feature branch
git push -u origin feature/bidding-{your-branch-name}

# Create PR to development branch
gh pr create --base development --title "Bidding: {description}" --body "## Summary
- What changed
- Why

## Testing
- [ ] Quality score: no regression
- [ ] Unit tests pass
- [ ] Regression test added (if bug fix)"
```

## Current Task

$ARGUMENTS
