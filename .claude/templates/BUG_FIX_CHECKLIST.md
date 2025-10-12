# Bug Fix Checklist

**Bug Description**: _____________________
**Related Issue**: #_____________________
**Date Started**: _____________________
**Severity**: [ ] Critical [ ] High [ ] Medium [ ] Low

## Investigation

- [ ] Reproduce the bug reliably
- [ ] Identify root cause
- [ ] Document symptoms and behavior
- [ ] Check if other areas are affected
- [ ] Search for similar issues in codebase
- [ ] 🏗️ **CHECK IF FIX REQUIRES ARCHITECTURAL REVIEW**
  - [ ] Does fix involve modifying data structures used across modules?
  - [ ] Does fix require API changes?
  - [ ] Does fix introduce new state management?
  - [ ] Does fix require refactoring 3+ modules?
  - **IF YES**: Complete [ARCHITECTURAL_DECISION_FRAMEWORK.md](../.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md) review
  - **IF HIGH-RISK**: Create ADR and get user approval before proceeding

## Test First

- [ ] Write failing test that demonstrates the bug
- [ ] Verify test fails as expected
- [ ] Place test in `backend/tests/regression/test_[bug_name].py`

## Fix Implementation

- [ ] Create fix branch: `git checkout -b fix/bug-description`
- [ ] Implement minimal fix (smallest change to fix bug)
- [ ] Verify failing test now passes
- [ ] Add inline comments explaining the fix
- [ ] Update docstrings if behavior changed

## Testing

- [ ] Original failing test now passes
- [ ] Run quick tests: `./backend/test_quick.sh`
- [ ] Run full test suite: `./backend/test_full.sh`
- [ ] All tests pass (no regressions)
- [ ] Test edge cases related to the bug
- [ ] Manual testing of the fix

## Documentation (for significant bugs only)

Choose ONE:

### Option A: Simple Fix (most bugs)
- [ ] Write clear commit message with:
  - What the bug was
  - Why it occurred
  - How it was fixed
- [ ] No separate documentation needed (commit message is sufficient)

### Option B: Complex Fix (requires documentation)
- [ ] Create `docs/bug-fixes/FIX_[BUG_NAME].md` with:
  - Problem description
  - Root cause
  - Solution implemented
  - Testing approach
  - Files modified
- [ ] Update related feature documentation if behavior changed
- [ ] Update architecture docs if design affected

## Compliance

- [ ] Run compliance checker: `python3 .claude/scripts/check_documentation_compliance.py --verbose`
- [ ] Address any issues found

## Pre-Commit

- [ ] Stage all files: `git add .`
- [ ] Review changes: `git diff --cached`
- [ ] Verify regression test is included

## Commit

- [ ] Write clear commit message:
  ```
  fix: Brief description of what was broken

  Explain what was wrong and why the fix works.
  Include any context needed to understand the bug.

  Closes #123 (if applicable)
  ```
- [ ] Commit: `git commit` (pre-commit hook will run)
- [ ] Address any pre-commit hook issues

## Verification

- [ ] Bug is fixed in local environment
- [ ] Regression test proves fix works
- [ ] No new bugs introduced
- [ ] Related areas still work correctly

## Completion

- [ ] Mark task complete in TodoWrite
- [ ] Close related issue (if applicable)
- [ ] Note if any follow-up work needed

## Root Cause Analysis (for critical bugs)

**What went wrong?**


**Why did it go wrong?**


**How can we prevent similar bugs?**


## Notes

(Add any relevant notes, workarounds attempted, or context here)
