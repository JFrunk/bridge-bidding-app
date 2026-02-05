---
description: Review code for quality and best practices
---

---
description: Review code for quality and best practices
---

Review code for quality and best practices: $ARGUMENTS

Target: $ARGUMENTS (file path, directory, or "recent changes")

---

## Code Review Checklist

### 1. Code Quality

**Read the code and check:**
- [ ] Functions are focused and do one thing
- [ ] Variable names are clear and descriptive
- [ ] No magic numbers (use constants)
- [ ] Error handling is present
- [ ] No code duplication (DRY principle)
- [ ] Comments explain "why", not "what"
- [ ] No commented-out code left behind

---

### 2. Testing

**Verify tests exist:**
- [ ] Unit tests for new functions/classes
- [ ] Integration tests for API endpoints
- [ ] Regression tests for bug fixes
- [ ] Edge cases covered
- [ ] Test names are descriptive
- [ ] Tests are independent (no order dependency)

**Run tests:**
```bash
pytest [test_file] -v
```

---

### 3. Documentation

**Check documentation completeness:**
- [ ] Docstrings for all functions/classes
- [ ] Feature documentation in docs/features/
- [ ] CLAUDE.md updated (if architecture changed)
- [ ] API endpoints documented
- [ ] README updated (if setup changed)
- [ ] Inline comments for complex logic

---

### 4. Quality Baselines (if applicable)

**If bidding logic changed:**
- [ ] Bidding quality baseline run (500 hands)
- [ ] No regression in composite score (±2% tolerance)
- [ ] Legality remains 100%

**If play logic changed:**
- [ ] Play quality baseline run (500 hands, level 8)
- [ ] No regression in composite score (±2% tolerance)
- [ ] Legality remains 100%

---

### 5. UI/UX Standards (if frontend changed)

**Design System Compliance:**
- [ ] Uses CSS variables (no hardcoded colors)
- [ ] Uses spacing system (--space-2, --space-4, etc.)
- [ ] Responsive at breakpoints (375px, 768px, 1280px)
- [ ] Keyboard navigation works
- [ ] ARIA labels present
- [ ] Touch targets ≥44px on mobile
- [ ] Loading states implemented
- [ ] Error messages are user-friendly

Reference: `.claude/UI_UX_DESIGN_STANDARDS.md`

---

### 6. Security & Performance

**Security:**
- [ ] No sensitive data in logs
- [ ] Input validation present
- [ ] No SQL injection vulnerabilities
- [ ] User data filtered by user_id
- [ ] No exposed API keys or credentials

**Performance:**
- [ ] No N+1 queries
- [ ] Database queries use indexes
- [ ] No unnecessary re-renders (React)
- [ ] Large lists use pagination/virtualization
- [ ] API responses cached appropriately

---

### 7. Git & Deployment

**Version Control:**
- [ ] Commit messages are descriptive
- [ ] One logical change per commit
- [ ] No merge conflicts
- [ ] Branch is up to date with development

**Deployment Readiness:**
- [ ] All tests pass
- [ ] No console.log or debug statements
- [ ] No TODO/FIXME markers (or documented)
- [ ] Database migrations documented (if applicable)

---

## Output Format

**Provide review summary:**

```
## Code Review Summary

### ✅ Strengths
- [List positive aspects]

### ⚠️  Issues Found
1. **[Severity]** [File:Line] - [Issue description]
   - Recommendation: [How to fix]

2. **[Severity]** [File:Line] - [Issue description]
   - Recommendation: [How to fix]

### 📋 Checklist Status
- Code Quality: X/7 ✅
- Testing: X/7 ✅
- Documentation: X/6 ✅
- Quality Baselines: X/3 ✅ (or N/A)
- UI/UX: X/8 ✅ (or N/A)
- Security: X/5 ✅
- Git: X/4 ✅

### 🎯 Recommendations
1. [Priority 1 recommendation]
2. [Priority 2 recommendation]
3. [Priority 3 recommendation]

### Approval Status
- [ ] ✅ APPROVED - Ready to merge
- [ ] ⚠️  APPROVED WITH COMMENTS - Merge after addressing comments
- [ ] ❌ CHANGES REQUESTED - Fix issues before merging
```

Reference: .claude/CODING_GUIDELINES.md, CLAUDE.md Documentation Standards
