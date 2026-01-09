---
description: Fix bug using test-driven approach
---

---
description: Fix bug using test-driven approach
---

Fix bug using test-driven approach: $ARGUMENTS

Bug description: $ARGUMENTS

⚠️  **TDD Workflow: Tests prove the bug exists, then implementation fixes it**

---

## Phase 1: Understand the Bug

1. Reproduce the bug (if possible)
2. Read error logs and stack traces
3. Identify affected code location
4. **Think hard** about root cause
5. Use systematic analysis (search for similar patterns)

---

## Phase 2: Write Regression Test FIRST

⚠️  **Critical: Write test that FAILS due to the bug**

6. Create regression test file:
   - `backend/tests/regression/test_[bug_name]_[date].py`
   - Follow naming: `test_[issue]_mmddyyyy.py`
7. Write test that reproduces the bug:
   - Test should FAIL with current code
   - Test should PASS after fix
   - Test proves bug stays fixed forever
8. **Run test to confirm it fails:**
   - `pytest tests/regression/test_[bug]_*.py -v`
   - Verify failure message matches expected bug behavior
9. Commit failing test:
   - `git add tests/regression/ && git commit -m "test: Add regression test for [bug]"`

---

## Phase 3: Implement Fix

10. Implement minimal fix to make test pass
11. **Run regression test repeatedly:**
    - `pytest tests/regression/test_[bug]_*.py -v`
    - Iterate until test passes
12. **Run related tests** to ensure no new issues:
    - Unit tests: `pytest tests/unit/ -v`
    - Integration tests: `pytest tests/integration/ -v`
13. **Run quality baselines** (if bidding/play logic):
    - Before: Capture baseline
    - After: Compare to verify no regression
    - `python3 compare_scores.py baseline_before.json baseline_after.json`

---

## Phase 4: Systematic Verification

14. Search codebase for similar bugs (use systematic protocol)
15. If found in multiple places, fix all instances
16. Add regression tests for each instance
17. Run full test suite: `cd backend && ./test_full.sh`

---

## Phase 5: Document & Commit

18. Create bug fix documentation:
    - `docs/bug-fixes/BUG_[NAME].md`
    - Include: symptoms, root cause, fix approach, testing
19. Update relevant feature documentation
20. Commit fix with comprehensive message:
```bash
git commit -m "fix: [Brief description]

Root Cause: [Technical explanation]
Affected: [Components/files]
Fix: [Approach taken]

Regression test: tests/regression/test_[bug]_[date].py
Quality baseline: No regression (X.X% maintained)

Fixes: #[issue_number] (if applicable)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Success Criteria

- [ ] Regression test written and committed BEFORE fix
- [ ] Test fails before fix (proves bug exists)
- [ ] Test passes after fix (proves bug is fixed)
- [ ] Similar bugs found and fixed (systematic analysis)
- [ ] Quality baselines show no regression
- [ ] Full test suite passes
- [ ] Documentation updated
- [ ] Bug fix committed with regression test

Reference: .claude/CODING_GUIDELINES.md Testing Rules, CLAUDE.md Testing Strategy
