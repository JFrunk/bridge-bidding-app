# Claude Code Quick Reference

**Always read this at the start of each session!**

## 🎯 Session Checklist

At the start of EVERY session:
- [ ] Read `.claude/PROJECT_CONTEXT.md` (especially architectural review & efficiency improvements)
- [ ] Check git status: `git status`
- [ ] Check current branch (should be `development`)
- [ ] Review any open TODOs

## 🏗️ Architectural Review (NEW - 2025-10-12)

**BEFORE implementing changes that involve:**
- New directories, dependencies, API changes
- Data structure modifications across modules
- New state management patterns
- Classes > 200 lines
- Refactoring 3+ modules

**DO THIS:**
1. ✅ PAUSE implementation
2. ✅ Run: `python3 .claude/scripts/check_architectural_triggers.py --verbose`
3. ✅ If HIGH-RISK: Read `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md`
4. ✅ Complete 30-minute architectural review
5. ✅ Create ADR in `docs/architecture/decisions/`
6. ✅ Present to user for approval
7. ✅ Only then implement

**Why:** Past mistakes (tight coupling, global state) cost velocity
**Framework:** `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md`
**ADRs:** `docs/architecture/decisions/README.md`

## 📋 Task Workflow

### Starting a Feature
1. ✅ Copy `.claude/templates/FEATURE_CHECKLIST.md`
2. ✅ Read requirements thoroughly
3. ✅ Identify affected docs
4. ✅ Use `TodoWrite` to track progress
5. ✅ Run `./backend/test_quick.sh` frequently

### Starting a Bug Fix
1. ✅ Copy `.claude/templates/BUG_FIX_CHECKLIST.md`
2. ✅ Reproduce bug
3. ✅ Write failing test in `tests/regression/`
4. ✅ Fix bug
5. ✅ Verify test passes

## 🧪 Testing Commands (CRITICAL)

```bash
# During development (RUN THIS CONSTANTLY)
./backend/test_quick.sh  # 30 seconds

# Before committing (RUN THIS EVERY TIME)
./backend/test_medium.sh  # 2 minutes

# Before pushing (RUN THIS BEFORE PUSH)
./backend/test_full.sh  # 5+ minutes

# Specific test category
pytest backend/tests/unit/ -v           # Unit tests only
pytest backend/tests/regression/ -v    # Regression tests only
pytest backend/tests/integration/ -v   # Integration tests only
```

## 📁 Test File Placement

**WHERE TO PUT NEW TESTS:**
- Feature test → `backend/tests/features/test_[feature_name].py`
- Bug fix test → `backend/tests/regression/test_[bug_name].py`
- Unit test → `backend/tests/unit/test_[module].py`
- Integration test → `backend/tests/integration/test_[integration].py`

## 📝 Documentation Rules

**For SIMPLE changes:**
- ✅ Write clear commit message (sufficient documentation)
- ❌ No separate doc file needed

**For COMPLEX changes:**
- ✅ Update consolidated docs in `docs/features/`
- ✅ Run compliance checker: `python3 .claude/scripts/check_documentation_compliance.py --verbose`

## 🧹 File System Hygiene (Check Before Commits)

**Quick Decision: Where Does This Document Belong?**

| Question | Answer | Location |
|----------|--------|----------|
| Claude context/process? | YES | `.claude/` |
| Essential daily reference? | YES | Root (only 7 kept) |
| Completed milestone? | YES | `docs/project-status/YYYY-MM-DD_title.md` |
| Architecture decision? | YES | `docs/architecture/decisions/` |
| Feature/bug doc? | YES | `docs/features/` or `docs/bug-fixes/` |
| Guide/how-to? | YES | `docs/guides/` |

**Red Flags 🚩**
- Creating `*_COMPLETE.md` at root → Move to `docs/project-status/`
- \>7 MD files at root → Consolidate or archive
- Temp files (`.log`, `.patch`) → Delete
- New orphaned directory → Organize into existing structure

**Root Directory MD Files (KEEP ONLY 7):**
- `README.md` - Main entry point
- `CONTRIBUTING.md` - Contributing guidelines
- `PROJECT_STATUS.md` - Current status
- `CHANGELOG.md` - Version history
- `ARCHITECTURE_SUMMARY.md` - Architecture overview
- `SHARED_INFRASTRUCTURE_ARCHITECTURE.md` - Infrastructure patterns
- `VIEW_CONVENTIONS.md` - View conventions

**Before Commit - File System Check:**
```bash
# 1. Count root docs (should be exactly 7)
ls -1 *.md 2>/dev/null | wc -l

# 2. Check for temp files (should be empty)
git status | grep -E "\.log|\.patch|DS_Store"

# 3. Check for Python cache (should be empty)
git status | grep __pycache__

# 4. Run health check (recommended)
python3 .claude/scripts/check_filesystem_health.py
```

**📖 Full guide:** `.claude/FILESYSTEM_GUIDELINES.md`

## ✅ Before Every Commit

**MANDATORY CHECKLIST:**
- [ ] **File system check**: Root MD count = 7, no temp files, no cache
- [ ] Tests pass: `./backend/test_medium.sh`
- [ ] Documentation updated (if needed)
- [ ] Run: `python3 .claude/scripts/check_documentation_compliance.py --verbose`
- [ ] Review staged changes: `git diff --cached`
- [ ] Stage all files: `git add .`
- [ ] Commit: `git commit -m "type: description"`
- [ ] Pre-commit hook passes (fix any issues it finds)

## 🚫 Common Mistakes to AVOID

❌ Committing without running tests
❌ Using `git commit --no-verify` (bypasses pre-commit hook)
❌ Marking task complete without running checks
❌ Forgetting to add regression test for bug fixes
❌ Running full test suite during development (too slow - use quick tests!)
❌ Creating new documentation when you should update existing
❌ Putting tests in wrong directory
❌ Creating `*_COMPLETE.md` files at root (use `docs/project-status/`)
❌ Letting root directory accumulate >7 MD files
❌ Creating new docs at root instead of in docs/ subdirectories

## ✅ Good Habits

✅ Run `./backend/test_quick.sh` after every code change
✅ Use templates for features and bugs
✅ Write tests FIRST for bug fixes
✅ Use TodoWrite to track progress
✅ Mark todos complete immediately after finishing
✅ Commit frequently with clear messages
✅ Update consolidated docs instead of creating new ones

## 🔍 When You're Stuck

**Can't find where code is?**
- Check `backend/engine/` for bidding logic
- Check `backend/tests/` for tests (organized by type)

**Don't know which test to run?**
- Default to `./backend/test_quick.sh` (fastest)

**Don't know if documentation is needed?**
- Simple change? Commit message is enough
- Complex change? Update consolidated docs

**Tests failing?**
- Read error messages carefully
- Run specific test: `pytest path/to/test_file.py -v`
- Check if you broke existing functionality

## 📚 Key Documents

**Must Read:**
- `.claude/PROJECT_CONTEXT.md` - Full project context
- `docs/COMPLETE_BRIDGE_RULES.md` - **Complete bridge rules reference (bidding, play, scoring, all phases)**
- `.claude/DOCUMENTATION_PRACTICES.md` - Documentation guidelines
- `.claude/FILESYSTEM_GUIDELINES.md` - **File organization rules (NEW)**
- `backend/tests/README.md` - Complete testing guide

**Templates:**
- `.claude/templates/FEATURE_CHECKLIST.md` - Feature workflow
- `.claude/templates/BUG_FIX_CHECKLIST.md` - Bug fix workflow

**Summaries:**
- `docs/project-overview/FEATURES_SUMMARY.md` - What's implemented
- `docs/project-status/` - Completed milestones and status reports

## 💡 Pro Tips

1. **Fast Feedback is Key**: Run `./backend/test_quick.sh` constantly (30 sec)
2. **Use Templates**: They prevent forgetting steps
3. **Test First for Bugs**: Write failing test before fixing
4. **Organize Tests Properly**: Right directory = easy to find later
5. **Commit Often**: Small commits are easier to review and revert
6. **Let CI/CD Validate**: Push to `development` and CI checks everything

## 🎯 Success Criteria

**You're doing it right when:**
- ✅ Tests run in 30 seconds during development
- ✅ You never forget which docs to update (template tells you)
- ✅ All bug fixes have regression tests
- ✅ Tests are easy to find (organized by type)
- ✅ CI/CD passes automatically
- ✅ You're shipping features faster

---

**Remember**: These improvements save 6.4 hours per 2-week sprint. Use them!
