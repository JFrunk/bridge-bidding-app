---
description: Pre-commit validation combining architectural, documentation, file health, and test checks
---

Run preflight checks before committing: $ARGUMENTS

---

## Purpose

Single pre-commit validation that replaces manually invoking `/check-scope`, documentation checks, and test scripts separately. Run this before any commit to catch issues early.

---

## Step 1: Identify Changed Files

```bash
git diff --name-only HEAD
git diff --name-only --cached
git status --short
```

Record all changed files for targeted checks below.

---

## Step 2: Architectural Trigger Check

```bash
python3 .claude/scripts/check_architectural_triggers.py --verbose
```

**If high-risk triggers detected (exit code 2):**
- STOP and report triggers to user
- Do NOT proceed to remaining checks
- User must acknowledge before continuing

**If medium-risk triggers (exit code 1):**
- Report warnings but continue checks

**If clean (exit code 0):**
- Continue

---

## Step 3: Documentation Compliance

```bash
python3 .claude/scripts/check_documentation_compliance.py
```

Check that:
- Changed code files have corresponding documentation updates
- No docs in project root (must be in `docs/` subdirectories)
- Feature docs exist for new features, bug-fix docs for fixes

**If docs-only or config-only changes:** Skip this check.

---

## Step 4: File Health

```bash
python3 .claude/scripts/check_filesystem_health.py
```

Validates:
- No files exceed 500 lines (warning at 400)
- Root directory isn't cluttered
- Files are in correct directories

---

## Step 5: Quick Tests (changed domains only)

Run tests ONLY for domains with changed files:

| Domain | File Patterns | Test Command |
|--------|--------------|--------------|
| Backend | `backend/engine/**`, `backend/server.py`, `backend/utils/**` | `cd backend && ./test_quick.sh` |
| Frontend | `frontend/src/**` | `cd frontend && CI=true npx react-scripts test --watchAll=false` |
| Docs/Config only | `docs/`, `*.md`, `.claude/` | No tests needed |

Do NOT run full quality scores (500 hands) — that's for `/smart-commit`. This is a fast check (~30s-2min).

---

## Step 6: Report

Present results in this format:

```
## Preflight Results

| Check | Status | Details |
|-------|--------|---------|
| Architectural Triggers | PASS/WARN/BLOCK | N triggers found |
| Documentation Compliance | PASS/WARN/SKIP | N issues |
| File Health | PASS/WARN | N warnings |
| Backend Tests | PASS/FAIL/SKIP | N passed, N failed |
| Frontend Tests | PASS/FAIL/SKIP | N passed, N failed |

Overall: READY TO COMMIT / ISSUES FOUND
```

---

## Decisions

**If all checks pass:**
- Report "Ready to commit" — user can proceed with `/smart-commit` or manual commit

**If any check fails:**
- Report failures with specific details
- Suggest fixes for each failure
- Do NOT commit

**If only warnings (no failures):**
- Report warnings
- Indicate "Ready to commit with warnings"

---

## Success Criteria

- [ ] Architectural triggers checked
- [ ] Documentation compliance verified (if applicable)
- [ ] File health validated
- [ ] Relevant domain tests passed
- [ ] Clear pass/fail report presented
