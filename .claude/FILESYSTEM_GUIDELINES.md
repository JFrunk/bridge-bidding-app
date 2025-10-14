# File System Organization Guidelines

**Version:** 1.0
**Last Updated:** 2025-10-13
**Purpose:** Maintain clean, navigable file system structure across all Claude Code sessions

---

## 🎯 Philosophy

**Root directory is precious real estate** - only essential reference documents belong there.

**Key Principle:** If a future developer (or Claude session) needs to find something, they should know exactly where to look based on consistent patterns.

---

## 📁 Directory Structure & Rules

### Root Directory (Target: 8-12 files maximum)

**Only keep files that developers need IMMEDIATELY upon project entry:**

✅ **Always Keep:**
- `README.md` - Project entry point
- `PROJECT_STATUS.md` - Current state (living document)
- `CONTRIBUTING.md` - How to contribute
- `START_APP.md` - Quick start guide

✅ **Essential References (if actively used):**
- `ARCHITECTURE_SUMMARY.md` - Current architecture overview
- `SHARED_INFRASTRUCTURE_ARCHITECTURE.md` - Shared patterns
- `VIEW_CONVENTIONS.md` - Active UI/UX conventions
- `VALIDATION_STRATEGY.md` - Testing strategy

❌ **Never at Root:**
- Completion reports (`*_COMPLETE.md`)
- Implementation status documents (`*_IMPLEMENTATION.md`)
- Temporary analysis files
- Dated validation reports
- Archived documentation

---

### `.claude/` Directory (Claude-Specific Context)

**Purpose:** Context, processes, and tools for Claude Code sessions

```
.claude/
├── QUICK_REFERENCE.md              # ⭐ START HERE every session
├── PROJECT_CONTEXT.md              # Full project context (auto-loads)
├── FILESYSTEM_GUIDELINES.md        # This file
├── ARCHITECTURAL_DECISION_FRAMEWORK.md  # Review process
├── HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md
├── UI_UX_DESIGN_STANDARDS.md
├── DOCUMENTATION_PRACTICES.md
├── scripts/                        # Automation scripts
│   ├── check_filesystem_health.py
│   ├── check_architectural_triggers.py
│   └── check_documentation_compliance.py
├── templates/                      # Development templates
│   ├── FEATURE_CHECKLIST.md
│   └── BUG_FIX_CHECKLIST.md
└── metrics/                        # Baseline metrics
    └── baseline_metrics_*.txt
```

**What Belongs Here:**
- ✅ Process documents (how to do things)
- ✅ Quick references (checklists)
- ✅ Standards (architectural patterns, coding standards)
- ✅ Scripts (automation tools)
- ✅ Templates (reusable checklists)
- ✅ Metrics (baseline measurements)

**What Doesn't:**
- ❌ Feature-specific documentation (→ `docs/features/`)
- ❌ Bug fix reports (→ `docs/bug-fixes/`)
- ❌ Architecture decisions (→ `docs/architecture/decisions/`)

---

### `docs/` Directory (Organized Documentation)

**Purpose:** All project documentation organized by category

```
docs/
├── README.md                       # Documentation index
├── architecture/                   # System design
│   ├── decisions/                 # ADRs (Architecture Decision Records)
│   │   ├── README.md
│   │   └── YYYY-MM-DD_title.md
│   └── diagrams/
├── features/                       # Feature documentation
│   └── feature_name.md
├── bug-fixes/                      # Bug documentation & fixes
│   └── issue_name.md
├── guides/                         # How-to guides
│   ├── TESTING_GUIDE.md
│   └── DEPLOYMENT_GUIDE.md
├── project-overview/               # High-level summaries
│   ├── FEATURES_SUMMARY.md
│   └── CLAUDE.md
├── project-status/                 # Milestone completions
│   ├── 2025-10-12_shadcn_migration_complete.md
│   └── archive/                   # Older milestones
│       └── 2025-10-XX_older_milestone.md
└── debug-archive/                  # Historical debugging info
```

**Filing Rules:**

| Document Type | Location | Example |
|--------------|----------|---------|
| Completed milestone | `docs/project-status/` | `2025-10-13_honors_scoring_complete.md` |
| Architecture decision | `docs/architecture/decisions/` | `2025-10-13_state_machine_pattern.md` |
| Feature documentation | `docs/features/` | `convention_help_system.md` |
| Bug fix documentation | `docs/bug-fixes/` | `trick_leader_bug_fix.md` |
| Implementation guide | `docs/guides/` | `adding_new_convention.md` |
| High-level overview | `docs/project-overview/` | `ARCHITECTURE_OVERVIEW.md` |

---

### Backend Structure

```
backend/
├── server.py                       # Main Flask server
├── engine/                         # Core bidding logic
│   ├── ai/                        # AI decision engine
│   ├── learning/                  # Learning system
│   └── play/                      # Card play engine
├── core/                           # Session/scenario management
├── database/                       # Database schemas
│   ├── schema_*.sql
│   └── init_*.py
├── tests/                          # Test suite
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   ├── scenarios/
│   └── features/
├── scripts/                        # Utility scripts
│   ├── analyze_hands.py
│   ├── simulation_enhanced.py
│   └── debug_hand.py
├── data/                           # Data files (mostly gitignored)
│   ├── convention_descriptions.json
│   └── .gitignore
├── requirements.txt
└── pytest.ini
```

**Rules:**
- ❌ No loose Python scripts at root (use `scripts/`)
- ❌ No data files at root (use `data/`)
- ✅ Keep module structure clean (`engine/`, `core/`, `tests/`)

---

### Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── bridge/                # Domain components
│   │   ├── play/                  # Play-specific
│   │   └── ui/                    # Shadcn UI components
│   ├── shared/                    # Reusable code
│   │   ├── components/
│   │   ├── services/
│   │   └── utils/
│   ├── App.js
│   └── index.js
├── public/
├── package.json
└── README.md
```

**Rules:**
- ✅ Use `.jsx` for React components (consistency)
- ✅ Colocate tests with components (`__tests__/`)
- ✅ Keep domain boundaries clear (bridge, play, shared)

---

## 🚫 Common Anti-Patterns to Avoid

### 1. Creating `*_COMPLETE.md` at Root

❌ **Wrong:**
```
/PROJECT_ROOT/
├── HONORS_SCORING_COMPLETE.md
├── TURN_INDICATOR_IMPLEMENTATION_COMPLETE.md
└── CONTRACT_GOAL_TRACKER_COMPLETE.md
```

✅ **Correct:**
```
/PROJECT_ROOT/docs/project-status/
├── 2025-10-13_honors_scoring_complete.md
├── 2025-10-12_turn_indicator_complete.md
└── 2025-10-11_contract_goal_tracker_complete.md
```

**Why:** Completion documents are historical records, not daily references. Date them and file them.

---

### 2. Creating Temporary Analysis Files

❌ **Wrong:**
```
/PROJECT_ROOT/
├── architecture_analysis.md
├── temp_notes.md
└── debugging_session.md
```

✅ **Correct:**
- Add findings to existing architecture docs
- Or file in `docs/architecture/`
- Or keep in `.claude/` if it's process-related
- Delete if truly temporary

---

### 3. Leaving Temp Files in Repo

❌ **Wrong:**
```
/PROJECT_ROOT/
├── debug.log
├── test.patch
├── output.tmp
└── .DS_Store
```

✅ **Correct:**
- Add to `.gitignore`
- Delete regularly
- Use `scripts/cleanup_temp_files.sh` if needed

---

### 4. Creating Orphaned Directories

❌ **Wrong:**
```
/PROJECT_ROOT/
├── random_scripts/
├── old_code/
├── Documents/
└── misc/
```

✅ **Correct:**
- `random_scripts/` → `backend/scripts/` or delete
- `old_code/` → Delete (use git history)
- `Documents/` → Consolidate into `docs/`
- `misc/` → Organize or delete

---

## ✅ Decision Tree for New Documents

### Step 1: What Type of Document?

```
Is this a one-time report/completion?
  ├─ YES → docs/project-status/YYYY-MM-DD_title.md
  └─ NO → Continue to Step 2

Is this for Claude context/process?
  ├─ YES → .claude/TITLE.md
  └─ NO → Continue to Step 3

Is this an essential daily reference?
  ├─ YES → Root (but check if you can UPDATE existing doc instead!)
  └─ NO → Continue to Step 4

Is this architecture-related?
  ├─ Decision? → docs/architecture/decisions/
  ├─ Overview? → docs/architecture/
  └─ Continue to Step 5

Is this feature or bug documentation?
  ├─ Feature? → docs/features/
  ├─ Bug? → docs/bug-fixes/
  └─ Continue to Step 6

Is this a how-to guide?
  ├─ YES → docs/guides/
  └─ NO → docs/project-overview/ (if high-level summary)
```

### Step 2: Naming Convention

**Living Documents** (constantly updated):
- `ARCHITECTURE_SUMMARY.md`
- `PROJECT_STATUS.md`
- `VIEW_CONVENTIONS.md`

**Dated Reports** (point-in-time):
- `docs/project-status/2025-10-13_performance_audit.md`
- `docs/architecture/decisions/2025-10-13_state_machine_pattern.md`

**Status Files** (milestone markers):
- `docs/project-status/2025-10-12_shadcn_migration_complete.md`

---

## 🔄 Regular Maintenance

### Before Every Commit

```bash
# 1. Count root docs (should be <15)
ls -1 *.md 2>/dev/null | wc -l

# 2. Check for temp files (should be empty)
git status | grep -E "\.log|\.patch|DS_Store"

# 3. Check for Python cache (should be empty)
git status | grep __pycache__

# 4. Run health check (when available)
python3 .claude/scripts/check_filesystem_health.py
```

### Weekly (or Before Major Commits)

```bash
# Full health check
python3 .claude/scripts/check_filesystem_health.py --verbose

# Review root directory
ls -la | head -20
# Ask: Should any of these be moved?
```

### Monthly (or After Major Milestones)

```bash
# Archive old status documents
python3 .claude/scripts/archive_old_status_docs.py

# Review and consolidate documentation
# - Any duplicate content?
# - Any outdated references?
# - Any docs that can be merged?
```

---

## 🎯 Target Metrics

### Current Health Targets

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Root MD files | 8-12 | <15 |
| Root total items | <25 | <30 |
| Python cache files | 0 | 0 |
| `.DS_Store` files | 0 | 0 |
| Temp files (`.log`, `.patch`) | 0 | 0 |
| Orphaned directories | 0 | 0 |
| Large uncommitted data files | 0 | 0 |

### Run Health Check

```bash
python3 .claude/scripts/check_filesystem_health.py
```

Expected output:
```
✅ Root directory: 10 MD files (target: <15)
✅ No temporary files found
✅ No Python cache files tracked
✅ No orphaned directories
✅ Filesystem health check passed!
```

---

## 📚 Quick Reference Commands

```bash
# Check root MD count
ls -1 *.md 2>/dev/null | wc -l

# Find temp files
find . -name "*.log" -o -name "*.patch" -o -name ".DS_Store"

# Find Python cache
find . -name "*.pyc" -o -name "__pycache__"

# Check git status for issues
git status | grep -E "__pycache__|\.pyc|\.DS_Store|\.log|\.patch"

# Full health check
python3 .claude/scripts/check_filesystem_health.py --verbose
```

---

## 🔗 Related Documentation

- [`.claude/QUICK_REFERENCE.md`](.claude/QUICK_REFERENCE.md) - Session startup checklist
- [`.claude/DOCUMENTATION_PRACTICES.md`](.claude/DOCUMENTATION_PRACTICES.md) - Doc guidelines
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) - Contribution guide
- [`docs/README.md`](../docs/README.md) - Documentation index

---

## 📝 Version History

- **1.0** (2025-10-13): Initial creation after filesystem review
