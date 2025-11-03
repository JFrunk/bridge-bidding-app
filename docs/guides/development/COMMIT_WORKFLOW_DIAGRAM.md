# Git Commit Workflow - With Automated Testing

**Visual guide to what happens when you run `git commit`**

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Developer: git commit -m "Fix bidding logic"              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  PRE-COMMIT HOOK TRIGGERED                                  │
│  (.git/hooks/pre-commit)                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Documentation Check                                │
│  • Detect code changes                                      │
│  • Check for documentation updates                          │
│  • Warn if docs missing (optional proceed)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Test Selection Prompt                              │
│                                                             │
│  Code changes detected. Choose test level:                  │
│    1. Quick  - Unit tests only (30 seconds)                 │
│    2. Full   - All tests including E2E (2-3 minutes)        │
│    3. Skip   - Skip tests (not recommended)                 │
│                                                             │
│  Developer enters: [1, 2, or 3]                             │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    Option 1        Option 2        Option 3
         │               │               │
         ▼               ▼               ▼
┌────────────┐  ┌────────────────┐  ┌────────────┐
│QUICK TESTS │  │  FULL TESTS    │  │  SKIP      │
│            │  │                │  │  (Warning) │
│• Backend   │  │• Backend unit  │  └──────┬─────┘
│  unit (30s)│  │• Backend integ │         │
│            │  │• Backend regr  │         │
└─────┬──────┘  │• Frontend unit │         │
      │         │• E2E tests     │         │
      │         │  (2-3 min)     │         │
      │         └────────┬───────┘         │
      │                  │                 │
      └──────────────────┼─────────────────┘
                         │
                         ▼
           ┌─────────────┴─────────────┐
           │                           │
        PASSED                      FAILED
           │                           │
           ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│ ✓ Tests PASSED!      │    │ ✗ Tests FAILED!      │
│                      │    │                      │
│ Commit proceeds...   │    │ Commit BLOCKED       │
│                      │    │                      │
│ → Files committed    │    │ Debug tips shown:    │
│ → Ready to push      │    │ • Backend tests cmd  │
│                      │    │ • Frontend tests cmd │
└──────────┬───────────┘    │ • E2E tests cmd      │
           │                │                      │
           │                │ Fix tests first!     │
           │                └──────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  FILES COMMITTED TO LOCAL REPO                               │
│  • Changes saved locally                                     │
│  • Not yet pushed to GitHub                                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  Developer: git push origin development                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  GITHUB ACTIONS TRIGGERED                                    │
│  (.github/workflows/test.yml)                                │
└────────────────────────┬─────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌──────────────┐  ┌───────────────┐
│ Backend     │  │ Frontend     │  │ E2E Tests     │
│ Tests       │  │ Tests        │  │ (Playwright)  │
│             │  │              │  │               │
│ • Unit      │  │ • Jest tests │  │ Waits for     │
│ • Integr    │  │ • Coverage   │  │ Backend +     │
│ • Regress   │  │              │  │ Frontend      │
│ • Coverage  │  └──────┬───────┘  │               │
│             │         │          │ • Starts both │
│ (3-4 min)   │         │          │   servers     │
└──────┬──────┘         │          │ • Runs tests  │
       │                │          │ • Screenshots │
       └────────────────┼──────────┤   on failure  │
                        │          │               │
                        │          │ (3-4 min)     │
                        │          └───────┬───────┘
                        │                  │
                        └──────────┬───────┘
                                   │
                                   ▼
                     ┌─────────────┴─────────────┐
                     │                           │
                  PASSED                      FAILED
                     │                           │
                     ▼                           ▼
          ┌──────────────────┐      ┌──────────────────────┐
          │ ✓ All CI Passed  │      │ ✗ CI Failed          │
          │                  │      │                      │
          │ • Green check    │      │ • Red X on PR        │
          │ • PR can merge   │      │ • View artifacts:    │
          │ • Safe to deploy │      │   - Test reports     │
          │                  │      │   - Screenshots      │
          └────────┬─────────┘      │   - Videos           │
                   │                │                      │
                   │                │ Fix and push again   │
                   │                └──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Merge to main        │
        │ → Auto-deploy        │
        │ → Production update  │
        └──────────────────────┘
```

---

## Detailed Step-by-Step

### Local Development

#### 1. Make Changes
```bash
# Edit files
vim backend/engine/ai/opening_bids.py
vim frontend/src/App.js
```

#### 2. Stage Changes
```bash
git add .
```

#### 3. Commit (Pre-commit Hook Runs)
```bash
git commit -m "Fix: Improve 1NT opening bid logic"
```

**Output:**
```
=== Documentation Check ===
⚠️  Warning: Code changes detected without documentation updates
Continue with commit? (y/N) y

=== Running Tests ===

Code changes detected. Choose test level:
  1. Quick  - Unit tests only (30 seconds)
  2. Full   - All tests including E2E (2-3 minutes)
  3. Skip   - Skip tests (not recommended)

Select option (1/2/3): 2
```

#### 4a. Tests Pass ✅
```
Running full test suite...

[1/3] Running Backend Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Backend tests PASSED

[2/3] Running Frontend Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Frontend tests PASSED

[3/3] Running E2E Tests (Playwright)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ E2E tests PASSED

========================================
  ALL TESTS PASSED! ✓
  Safe to commit.
========================================

✓ Pre-commit checks complete!

[development abc1234] Fix: Improve 1NT opening bid logic
 2 files changed, 15 insertions(+), 8 deletions(-)
```

**Result:** Commit succeeds, files saved to local repo

#### 4b. Tests Fail ✗
```
Running full test suite...

[1/3] Running Backend Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Backend tests PASSED

[2/3] Running Frontend Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Frontend tests PASSED

[3/3] Running E2E Tests (Playwright)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✗ E2E tests FAILED

========================================
  TESTS FAILED! ✗
  Do not commit until tests pass.
========================================

✗ Tests failed! Fix tests before committing.

Debug tips:
  • Backend tests: cd backend && ./test_quick.sh
  • Frontend tests: cd frontend && npm test
  • E2E tests: cd frontend && npm run test:e2e:ui

To commit anyway (not recommended): git commit --no-verify
```

**Result:** Commit BLOCKED, must fix tests

---

### Bypassing Pre-commit Hook (Emergency Only)

```bash
# Skip pre-commit hook (NOT RECOMMENDED)
git commit --no-verify -m "WIP: Experimental change"

# Warning: Tests won't run locally
# GitHub Actions will still run and may fail
```

---

### CI/CD Pipeline (GitHub Actions)

#### Trigger: Push to GitHub
```bash
git push origin development
```

#### GitHub Actions Executes
```
Workflow: Tests
Triggered by: push to development

Jobs:
  ✓ backend-tests (3m 42s)
    • Unit tests: 85 passed
    • Integration tests: 23 passed
    • Regression tests: 13 passed
    • Coverage: 92%

  ✓ frontend-tests (2m 18s)
    • Unit tests: 5 passed
    • Coverage: 65%

  ✓ e2e-tests (3m 55s)
    Depends on: backend-tests, frontend-tests
    • Server startup: OK
    • E2E tests: 8 passed
    • Screenshots: None (all passed)

Total time: 7m 12s
Status: ✓ All checks passed
```

#### Artifacts Available
- Test reports (30 days)
- Coverage reports (codecov.io)
- Screenshots (if failed)
- Videos (if failed)

---

## Quick Reference

### Run Tests Manually (Before Commit)

```bash
# Quick validation during development
./test_all.sh --quick               # 30 seconds

# Full validation before commit
./test_all.sh                       # 2-3 minutes

# Backend only
cd backend && ./test_quick.sh       # 30 seconds

# E2E only (interactive)
cd frontend && npm run test:e2e:ui  # Visual debugging
```

### Commit With Pre-selected Test Level

The pre-commit hook always prompts, but you can prepare by running tests first:

```bash
# Run full tests first
./test_all.sh

# If passed, commit
git commit -m "Message"
# Then choose option 3 (skip) since you already validated
```

### Emergency Override

```bash
# Only use in true emergency (build is broken, critical hotfix)
git commit --no-verify -m "Hotfix: Critical production bug"
git push

# GitHub Actions will still run - fix tests ASAP
```

---

## Time Estimates

| Action | Time | When |
|--------|------|------|
| Quick tests (option 1) | 30s | During active development |
| Full tests (option 2) | 2-3m | Before pushing |
| Skip tests (option 3) | 0s | Not recommended |
| Manual ./test_all.sh | 2-3m | Pre-validate before commit |
| GitHub Actions | 7-8m | Every push (automatic) |

---

## Best Practices

### During Active Development
1. Make small changes
2. Run `./test_all.sh --quick` frequently
3. Use option 1 (quick) when committing
4. Commit often with small changes

### Before Pushing/PR
1. Run `./test_all.sh` manually
2. If passed, commit with option 2 (full)
3. Push to GitHub
4. Verify GitHub Actions passes

### When Tests Fail
1. **Don't bypass with --no-verify**
2. Use debug commands:
   - `cd backend && ./test_quick.sh`
   - `cd frontend && npm run test:e2e:ui`
3. Fix the issue
4. Re-run tests
5. Commit when green

### Emergency Situations
1. If absolutely must commit: `--no-verify`
2. Create issue to fix tests immediately
3. Don't push to main until tests pass
4. Fix before next commit

---

## What You See vs What Happens

### You Type:
```bash
git commit -m "Fix bidding logic"
```

### Behind The Scenes:
```
1. Git stages commit
2. Runs .git/hooks/pre-commit
3. Documentation check runs
4. Prompts for test level
5. Executes ./test_all.sh with flags
6. Backend tests run (pytest)
7. Frontend tests run (jest)
8. E2E tests run (playwright)
9. Results evaluated
10a. Pass → Commit saved
10b. Fail → Commit rejected
```

### Time: 2-3 minutes (option 2) or 30 seconds (option 1)

---

## Comparison: Before vs After

### Before E2E Testing

```bash
# Developer workflow
git add .
git commit -m "Fix"
git push

# Manual testing (maybe)
# Hope nothing broke
# Find bugs in production
```

**Time:** 30 seconds (plus 30 minutes fixing production bugs later)

### After E2E Testing

```bash
# Developer workflow
git add .
git commit -m "Fix"
# → Pre-commit hook runs tests (2-3 min)
# → All tests pass ✓
git push
# → GitHub Actions validates (7 min)
# → All CI passes ✓
# → Safe to deploy

# No production bugs from this change
```

**Time:** 3 minutes (saves hours of debugging production issues)

---

## Summary

Your new commit workflow has **three layers of protection**:

1. **Pre-commit Hook** - Catches issues before commit
2. **Manual Testing** - Optional validation with `./test_all.sh`
3. **GitHub Actions** - Final validation before merge

**Result:** Regressions caught automatically, production stays stable, confidence in every deploy.

**The workflow is now integrated - just commit as usual and the tests run automatically!** ✅
