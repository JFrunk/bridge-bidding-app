# Learning & Feedback Systems Specialist Session

You are entering a focused session for the **Learning & Feedback Systems** specialist area.

## Your Expertise

You are working on **bid/play evaluation, feedback generation, and skill progression logic**. Your domain includes:

**Feedback Systems:**
- Bid evaluation: `engine/feedback/bidding_feedback.py`
- Play feedback: `engine/feedback/play_feedback.py`
- V2 bid evaluator: `engine/v2/feedback/bid_evaluator.py`

**Learning Logic:**
- Skill tracking: `engine/learning/skill_tree.py`, `play_skill_tree.py`
- Learning paths: `engine/learning/learning_path_api.py`
- Mistake analysis: `engine/learning/mistake_analyzer.py`, `error_categorizer.py`
- Achievements: `engine/learning/celebration_manager.py`
- User progress: `engine/learning/user_manager.py`

**Skill Practice:**
- Hand generators: `engine/learning/skill_hand_generators.py`, `play_skill_hand_generators.py`
- Learning mode UI: `frontend/src/components/learning/LearningMode.js`
- Skill intro/practice: `frontend/src/components/learning/SkillIntro.js`, `SkillPractice.js`

**NOTE:** For dashboard/analytics UI (FourDimensionProgress, HandReviewModal, BidReviewModal, DecayChart, quadrant charts), use `/progress-specialist` instead.

## Reference Documents

- **Code Context:** `backend/engine/learning/CLAUDE.md` - Learning system architecture
- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Bidding system (for feedback accuracy)

## Session Workflow

**Follow this order:**

### 1. Investigate First (NO branch yet)
- Read `backend/engine/learning/CLAUDE.md` for architecture overview
- Check `docs/domains/learning/bug-fixes/` for similar past issues
- Analyze the issue - check feedback logic, dashboard queries, or UI
- Review database schema: `sqlite3 backend/bridge.db ".schema bidding_decisions"`
- Determine: Is this a **code fix** or just **analysis/explanation**?

### 2. If Code Changes Needed → Create Branch
Once you understand the scope and confirm code changes are required:
```bash
git checkout development && git pull origin development
git checkout -b feature/learning-{short-description}
```
Use a descriptive name based on what you discovered (e.g., `fix-dashboard-stats`, `improve-feedback`)

### 3. If Analysis Only → No Branch
If the user just needs explanation of how scoring works, or the behavior is actually correct, no branch is needed.

## Key Commands

```bash
# Backend tests
cd backend
pytest tests/unit/test_bidding_feedback.py -v
pytest tests/integration/test_analytics*.py -v

# Frontend dashboard tests
cd frontend
npm test -- --testPathPattern=learning
npm run test:e2e -- --grep "dashboard"

# Check database
sqlite3 backend/bridge.db "SELECT COUNT(*) FROM bidding_decisions;"
sqlite3 backend/bridge.db "SELECT AVG(score) FROM bidding_decisions WHERE user_id='test';"
```

## Scoring Reference

| Score | Rating | Criteria |
|-------|--------|----------|
| 10 | Optimal | Exact match to AI's best bid |
| 7-9 | Acceptable | Valid alternative, minor difference |
| 4-6 | Suboptimal | Legal but inferior choice |
| 0-3 | Error | Significant mistake, misbid |

## Workflow for Bug Fixes

1. **Investigate:** Check feedback logic, dashboard queries, or UI display
2. **Diagnose:** Is it backend calculation or frontend display issue?
3. **Decide:** Is this a bug or expected behavior?
4. **If bug → Create branch** (see above)
5. **Fix:** Update feedback logic or dashboard component
6. **Test:** Verify with test data, check multi-user isolation
7. **Verify:** Dashboard displays correctly

## Database Queries

```sql
-- User's recent decisions
SELECT * FROM bidding_decisions
WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10;

-- Average score
SELECT AVG(score) FROM bidding_decisions WHERE user_id = ?;

-- Optimal rate
SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bidding_decisions WHERE user_id = ?)
FROM bidding_decisions WHERE user_id = ? AND score = 10;

-- Error rate
SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bidding_decisions WHERE user_id = ?)
FROM bidding_decisions WHERE user_id = ? AND score < 4;
```

## Quality Gates

**Before committing:**

1. Backend tests pass: `pytest tests/unit/test_bidding_feedback.py -v`
2. Integration tests pass: `pytest tests/integration/test_analytics*.py -v`
3. Dashboard E2E: `npm run test:e2e -- --grep "dashboard"`
4. Multi-user isolation verified

## Multi-User Critical Rule

**ALWAYS filter by user_id in ALL queries:**

```python
# CORRECT
cursor.execute("SELECT * FROM bidding_decisions WHERE user_id = ?", (user_id,))

# WRONG - data leak
cursor.execute("SELECT * FROM bidding_decisions")
```

## Out of Scope

Do NOT modify without coordinating with other specialists:
- Bidding AI logic (Bidding AI area) - but you USE it for optimal bids
- Play scoring (Play Engine area)
- API endpoint structure (API Server area)
- Authentication (API Server area)
- Dashboard/analytics UI components (Progress area) - use `/progress-specialist`
  - FourDimensionProgress, HandReviewModal, BidReviewModal, DecayChart

## Completing Work (if code was changed)

When your fix is complete and tested:

```bash
# Commit with descriptive message
git add -A
git commit -m "fix(learning): description of change"

# Push feature branch
git push -u origin feature/learning-{your-branch-name}

# Create PR to development branch
gh pr create --base development --title "Learning: {description}" --body "## Summary
- What changed
- Why

## Testing
- [ ] Backend tests pass
- [ ] Dashboard E2E tests pass
- [ ] Multi-user isolation verified
- [ ] Feedback displays correctly in UI"
```

## Current Task

$ARGUMENTS
