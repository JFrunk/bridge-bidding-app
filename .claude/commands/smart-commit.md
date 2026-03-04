---
description: Run appropriate quality gates based on changed files, then commit
---

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

## Step 2: Run Quality Gates

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

## Step 3: Report Results

```
## Quality Gate Results

| Gate | Status | Details |
|------|--------|---------|
| Bidding Quality | PASS/FAIL/SKIPPED | Composite: X% |
| Play Quality | PASS/FAIL/SKIPPED | Composite: X% |
| SAYC Compliance | PASS/FAIL/SKIPPED | Score: X% |
| Frontend Tests | PASS/FAIL/SKIPPED | N tests passed |
| Frontend Build | PASS/FAIL/SKIPPED | Build size: X |
| Backend Tests | PASS/FAIL/SKIPPED | N tests passed |
```

---

## Step 4: Commit or Stop

**If ALL gates pass:**
- Stage relevant files (not untracked files unless explicitly part of the change)
- Generate commit message from `$ARGUMENTS` and changed file analysis
- Use conventional commit format: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Commit

**If ANY gate fails:**
- Report which gate(s) failed with details
- Do NOT commit
- Suggest fixes for failures

---

## Success Criteria

- [ ] All changed files categorized
- [ ] Only relevant quality gates executed (not all)
- [ ] No gate failures before committing
- [ ] Commit message reflects the nature of changes
- [ ] No unrelated files staged
