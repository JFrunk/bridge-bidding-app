---
description: Run appropriate quality gates based on changed files, then commit
---

Run quality gates and commit: $ARGUMENTS

Commit message or context: $ARGUMENTS

---

## Step 1: Analyze Changed Files

```bash
git diff --name-only HEAD
git diff --name-only --cached
git status --short
```

Categorize every changed file into one or more of these domains:

| Domain | File Patterns | Quality Gate |
|--------|--------------|--------------|
| Bidding Engine | `backend/engine/*.py`, `backend/engine/ai/conventions/*.py` | Bidding quality (100 hands) |
| Play Engine | `backend/engine/play_engine.py`, `backend/engine/play/ai/*.py` | Play quality (100 hands, Level 8) |
| SAYC/V2 | `backend/engine/v2/` | SAYC compliance (100 hands) |
| Frontend | `frontend/src/**` | `npm test` + `npm run build` |
| Backend Tests | `backend/tests/` | `cd backend && ./test_quick.sh` |
| Server/API | `backend/server.py`, `backend/utils/` | `cd backend && ./test_quick.sh` |
| Docs Only | `docs/`, `*.md` | No quality gate needed |
| Config | `.claude/`, config files | No quality gate needed |

---

## Step 2: Diff Review (catch issues before they become follow-up commits)

Review the full diff of all changed files:

```bash
git diff HEAD
git diff --cached
```

Scan specifically for these common causes of follow-up fix commits:

- **Leftover debug code:** `console.log`, `print()`, `debugger`, commented-out code blocks
- **Incomplete state handling:** New state added without cleanup, missing reset on unmount
- **Missing imports/exports:** New functions referenced but not imported, new components not exported
- **Inconsistent naming:** Variable/function names that don't match existing conventions in the file
- **Hardcoded values:** Magic numbers, hardcoded strings that should use constants or config
- **Edge cases:** Empty arrays, null/undefined, zero-length strings, boundary conditions
- **CSS issues:** Missing responsive breakpoints for new UI elements, z-index conflicts
- **API contract mismatches:** Frontend expecting different shape than backend returns

**If issues found:**
- List each issue with file and line
- Fix them NOW before proceeding to quality gates
- Re-run `git diff` after fixes to confirm

**If clean:** Continue to Step 3.

---

## Step 3: Run Quality Gates

Run ONLY the gates triggered by changed files. Skip gates for unchanged domains.

**Bidding Engine:**
```bash
cd backend && source venv/bin/activate
python3 test_bidding_quality_score.py --hands 100
```
Fail if: legality < 100% or composite drops > 2% from baseline.

**Play Engine:**
```bash
cd backend && source venv/bin/activate
python3 test_play_quality_integrated.py --hands 100 --level 8
```
Fail if: legality < 100% or composite drops > 5% from baseline.

**SAYC Compliance:**
```bash
cd backend && source venv/bin/activate
python3 test_sayc_compliance.py --hands 100
```

**Frontend:**
```bash
cd frontend && npm test -- --watchAll=false 2>&1
cd frontend && npm run build 2>&1
```
Fail if: tests fail or build fails.

**Backend Tests:**
```bash
cd backend && ./test_quick.sh
```
Fail if: any test fails.

---

## Step 4: Report Results

```
## Smart Commit Results

| Check | Status | Details |
|-------|--------|---------|
| Diff Review | PASS/FIXED | N issues found and fixed |
| Bidding Quality | PASS/FAIL/SKIP | Composite: X% |
| Play Quality | PASS/FAIL/SKIP | Composite: X% |
| SAYC Compliance | PASS/FAIL/SKIP | Score: X% |
| Frontend Tests | PASS/FAIL/SKIP | N tests passed |
| Frontend Build | PASS/FAIL/SKIP | Build size: X |
| Backend Tests | PASS/FAIL/SKIP | N tests passed |
```

---

## Step 5: Commit or Stop

**If ALL gates pass:**
- Stage relevant files (not untracked files unless explicitly part of the change)
- Generate commit message from `$ARGUMENTS` and changed file analysis
- Use conventional commit format: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- If diff review fixed issues, include them in the same commit (they're pre-commit cleanup, not separate work)
- Commit

**If ANY gate fails:**
- Report which gate(s) failed with details
- Do NOT commit
- Suggest fixes for failures

---

## Success Criteria

- [ ] All changed files categorized
- [ ] Diff reviewed for common follow-up-fix patterns
- [ ] Issues found in diff review fixed before quality gates
- [ ] Only relevant quality gates executed (not all)
- [ ] No gate failures before committing
- [ ] Commit message reflects the nature of changes
- [ ] No unrelated files staged
