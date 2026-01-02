# Play Engine Specialist Session

You are entering a focused session for the **Play Engine & AI** specialist area.

## Your Expertise

You are working on the card play system and AI opponents. Your domain includes:

- Play orchestration: `play_engine.py`, `bridge_rules_engine.py`
- AI implementations: `play/ai/simple_ai.py`, `minimax_ai.py`, `dds_ai.py`
- Position evaluation: `play/ai/evaluation.py`
- Contract scoring: `contract_utils.py`

## Reference Documents

- **Code Context:** `backend/engine/play/CLAUDE.md` - Play engine architecture
- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Online single-player rules + offline reference
- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Bidding system reference

## Session Workflow

**Follow this order:**

### 1. Investigate First (NO branch yet)
- Read `backend/engine/play/CLAUDE.md` for architecture overview
- Analyze the issue - read relevant files, trace the problem
- Determine: Is this a **code fix** or just **analysis/explanation**?
- Note: **DDS only works on Linux** - use 'advanced' difficulty for local testing

### 2. If Code Changes Needed → Create Branch
Once you understand the scope and confirm code changes are required:
```bash
git checkout development && git pull origin development
git checkout -b feature/play-{short-description}
```
Use a descriptive name based on what you discovered (e.g., `fix-trump-management`, `improve-minimax-eval`)

### 3. If Analysis Only → No Branch
If the user just needs explanation of why the AI made a play, or the behavior is actually correct, no branch is needed.

## Key Commands

```bash
# Quick play tests (all play unit tests - 56 tests)
cd backend && source venv/bin/activate && PYTHONPATH=. pytest tests/play/ -v

# Run specific test suites:
PYTHONPATH=. pytest tests/play/test_simple_ai.py -v              # SimplePlayAI unit tests (18 tests)
PYTHONPATH=. pytest tests/play/test_play_evaluation_api.py -v    # API endpoint tests (16 tests)
PYTHONPATH=. pytest tests/play/test_convention_play_scenarios.py -v  # Convention hands (22 tests)

# Quality score by AI level
python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 3  # Quick
python3 test_play_quality_integrated.py --hands 500 --ai minimax --depth 3  # Full

# Performance profiling
python3 -m cProfile -s cumtime test_play_quality_integrated.py --hands 20 --ai minimax --depth 3

# E2E card play tests
cd frontend && npm run test:e2e -- --grep "Card Play"
```

## Baseline Testing Protocol

**CRITICAL: Always run baseline BEFORE and AFTER code changes**

### Step 1: Capture Baseline (BEFORE changes)
```bash
cd backend
python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 3 \
    --output /tmp/play_baseline_before.json
```

### Step 2: Make Your Changes
Implement the fix or improvement.

### Step 3: Run Post-Change Test
```bash
python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 3 \
    --output /tmp/play_baseline_after.json
```

### Step 4: Compare Results
```bash
# If compare_play_scores.py exists:
python3 compare_play_scores.py /tmp/play_baseline_before.json /tmp/play_baseline_after.json

# Or manually compare key metrics:
# - Legality must stay 100%
# - Composite score must not decrease by more than 2%
# - Timing must not increase by more than 50%
```

### Step 5: Update Stored Baseline (if improved)
If your change **improves** quality scores:
```bash
cp /tmp/play_baseline_after.json quality_scores/play_baseline_minimax_depth3.json
```
Document the improvement in your PR description.

## AI Difficulty Reference

| Difficulty | AI | Speed | Use Case |
|------------|-----|-------|----------|
| beginner | SimplePlayAI | <1s | Quick games |
| intermediate | MinimaxPlayAI(depth=2) | 2-3s | Moderate challenge |
| advanced | MinimaxPlayAI(depth=3) | 2-3s | Development testing |
| expert | DDSPlayAI | 15-30s | Linux production only |

## Workflow for Bug Fixes

1. **Investigate:** Read the hand/trick data, trace AI decision
2. **Diagnose:** Identify root cause - which AI level, which logic path
3. **Decide:** Is this a bug or expected behavior for that AI level?
4. **If bug → Create branch** (see above)
5. **Fix:** Modify AI logic
6. **Test:** Add regression test + run quality score
7. **Verify:** Ensure no regression, acceptable performance

## Quality Gates

**You MUST run quality score before committing play changes:**

- Legality: 100% (blocking)
- Success Rate: ≥ baseline - 5% (blocking)
- Composite: ≥ baseline - 2% (blocking)
- Timing: < baseline + 50% (blocking)

## DDS Warning

**DO NOT test DDS on macOS** - it will crash with segmentation fault.

Development workflow:
```bash
# Local (macOS/Windows) - use 'advanced' (Minimax depth 3)
python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 3

# Production (Linux) - 'expert' (DDS) available
```

## Out of Scope

Do NOT modify without coordinating with other specialists:
- Bidding modules (Bidding AI area)
- Frontend play components (Frontend area)
- API endpoint structure (API Server area)

## Completing Work (if code was changed)

When your fix is complete and tested:

```bash
# Commit with descriptive message
git add -A
git commit -m "fix(play): description of change"

# Push feature branch
git push -u origin feature/play-{your-branch-name}

# Create PR to development branch
gh pr create --base development --title "Play: {description}" --body "## Summary
- What changed
- Why

## Testing
- [ ] Quality score: no regression (advanced difficulty)
- [ ] Unit tests pass
- [ ] Performance acceptable
- [ ] Regression test added (if bug fix)"
```

## Current Task

$ARGUMENTS
