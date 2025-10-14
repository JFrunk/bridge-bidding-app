# Filesystem Cleanup Roadmap

**Status:** Planning Phase
**Created:** 2025-10-13
**Target Completion:** After `refactor/shadcn-tailwind-migration` merges

---

## 🎯 Overview

This document outlines the complete filesystem cleanup plan to reduce root directory clutter from 27 MD files to 8-12 essential files, while preserving all architectural review processes and historical records.

**Key Principle:** Keep PROCESS documents active, archive DATED REPORTS.

---

## ✅ Phase 1: Immediate Changes (COMPLETED)

**Status:** ✅ Complete (2025-10-13)
**Branch:** `refactor/shadcn-tailwind-migration`

### Completed Actions:
1. ✅ Created comprehensive `.gitignore` file
2. ✅ Removed temporary files (`.DS_Store`, `.log`, `.patch`)
3. ✅ Created `.claude/FILESYSTEM_GUIDELINES.md`
4. ✅ Updated `.claude/QUICK_REFERENCE.md` with file system hygiene
5. ✅ Created `.claude/scripts/check_filesystem_health.py`

### Results:
- Temp files removed: 8+ files
- `.gitignore` rules added: ~80 patterns
- New guidance documents: 2 files
- New automation scripts: 1 script

---

## 📋 Phase 2: Documentation Consolidation

**Status:** 🔄 Planned (Not Started)
**Timing:** After current refactor branch merges to main
**Estimated Time:** 2-3 hours

### 2.1: Distinguish Active vs Archive Documents

#### KEEP ACTIVE at Root (Process & Essential References)

These are **living documents** that Claude needs regularly:

```
Root/
├── README.md                              ✅ Keep - Entry point
├── PROJECT_STATUS.md                      ✅ Keep - Living document
├── CONTRIBUTING.md                        ✅ Keep - Essential
├── START_APP.md                          ✅ Keep - Quick start
├── ARCHITECTURE_SUMMARY.md               ✅ Keep - Current architecture
├── SHARED_INFRASTRUCTURE_ARCHITECTURE.md ✅ Keep - Active patterns
├── VIEW_CONVENTIONS.md                   ✅ Keep - Active conventions
├── MODULAR_ARCHITECTURE_PLAN.md          ⚠️  Review - Still relevant?
└── VALIDATION_STRATEGY.md                ✅ Keep - Testing strategy
```

**Total:** 8-9 files (Target achieved!)

#### ARCHIVE to `docs/project-status/archive/2025-10-12/`

These are **dated reports** from Oct 12 architectural review:

```
Archive (One-time reports from 2025-10-12):
├── ARCHITECTURAL_DECISION_VALIDATION.md      → archive/2025-10-12/
├── ARCHITECTURE_REVIEW_COMPLETE.md           → archive/2025-10-12/
├── ARCHITECTURE_RISK_ANALYSIS.md             → archive/2025-10-12/
├── EXECUTIVE_VALIDATION_REPORT.md            → archive/2025-10-12/
├── FINAL_IMPLEMENTATION_PLAN.md              → archive/2025-10-12/
└── DOCUMENTATION_REORGANIZATION_REPORT.md    → archive/2025-10-12/
```

#### MOVE to `docs/project-status/`

These are **completed milestones** (dated status files):

```
Completed Milestones:
├── BUILD_VERIFICATION_COMPLETE.md            → docs/project-status/2025-10-12_build_verification.md
├── CONTRACT_GOAL_TRACKER_COMPLETE.md         → docs/project-status/2025-10-12_contract_goal_tracker.md
├── HONORS_SCORING_IMPLEMENTATION.md          → docs/project-status/2025-10-13_honors_scoring.md
├── RESPONDER_REBIDS_COMPLETE.md              → docs/project-status/2025-10-12_responder_rebids.md
├── TURN_INDICATOR_IMPLEMENTATION_COMPLETE.md → docs/project-status/2025-10-12_turn_indicator.md
├── UI_UX_STANDARDS_IMPLEMENTATION_COMPLETE.md → docs/project-status/2025-10-12_ui_ux_standards.md
└── IMPLEMENTATION_STATUS.md                  → docs/project-status/2025-10-13_implementation_status.md
```

#### MOVE to `docs/features/` or Consolidate

Feature-specific documentation:

```
├── COMMON_MISTAKE_SYSTEM_DESIGN.md           → docs/features/learning_system.md
├── LEARNING_ENHANCEMENTS_PLAN.md             → docs/features/learning_system.md (merge)
├── EXPLICIT_STATE_MACHINE_IMPLEMENTATION.md  → docs/architecture/state_machine.md
└── UI_REFACTOR_PLAN.md                       → docs/architecture/ui_refactor.md (or delete if complete)
```

#### MOVE to `docs/guides/`

```
└── UI_UX_README.md                           → docs/guides/UI_UX_GUIDE.md
```

### 2.2: Preserve Architectural Review PROCESS

**CRITICAL:** These documents must remain accessible for Claude:

**In `.claude/` (Already there - no action needed):**
- ✅ `ARCHITECTURAL_DECISION_FRAMEWORK.md` - The review PROCESS
- ✅ `HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md` - Guidelines
- ✅ `PROJECT_CONTEXT.md` - Current state
- ✅ `QUICK_REFERENCE.md` - Session checklist
- ✅ `scripts/check_architectural_triggers.py` - Automation

**At Root (Keep these):**
- ✅ `ARCHITECTURE_SUMMARY.md` - Current overview
- ✅ `SHARED_INFRASTRUCTURE_ARCHITECTURE.md` - Patterns

**What Gets Archived:**
- ❌ Oct 12 validation reports (historical record only)
- ❌ Completed implementation reports
- ❌ Risk analysis from specific date

### 2.3: Create Directory Structure

```bash
# Create archive structure
mkdir -p docs/project-status/archive/2025-10-12
mkdir -p docs/project-status/archive/2025-10-13
mkdir -p docs/features
mkdir -p docs/architecture

# Verify structure
ls -la docs/
```

### 2.4: Move Files (Detailed Commands)

```bash
# Archive Oct 12 reports
mv ARCHITECTURAL_DECISION_VALIDATION.md docs/project-status/archive/2025-10-12/
mv ARCHITECTURE_REVIEW_COMPLETE.md docs/project-status/archive/2025-10-12/
mv ARCHITECTURE_RISK_ANALYSIS.md docs/project-status/archive/2025-10-12/
mv EXECUTIVE_VALIDATION_REPORT.md docs/project-status/archive/2025-10-12/
mv FINAL_IMPLEMENTATION_PLAN.md docs/project-status/archive/2025-10-12/
mv DOCUMENTATION_REORGANIZATION_REPORT.md docs/project-status/archive/2025-10-12/

# Move completed milestones
mv BUILD_VERIFICATION_COMPLETE.md docs/project-status/2025-10-12_build_verification.md
mv CONTRACT_GOAL_TRACKER_COMPLETE.md docs/project-status/2025-10-12_contract_goal_tracker.md
mv HONORS_SCORING_IMPLEMENTATION.md docs/project-status/2025-10-13_honors_scoring.md
mv RESPONDER_REBIDS_COMPLETE.md docs/project-status/2025-10-12_responder_rebids.md
mv TURN_INDICATOR_IMPLEMENTATION_COMPLETE.md docs/project-status/2025-10-12_turn_indicator.md
mv UI_UX_STANDARDS_IMPLEMENTATION_COMPLETE.md docs/project-status/2025-10-12_ui_ux_standards.md
mv IMPLEMENTATION_STATUS.md docs/project-status/2025-10-13_implementation_status.md

# Move feature docs
mv COMMON_MISTAKE_SYSTEM_DESIGN.md docs/features/common_mistake_system.md
mv LEARNING_ENHANCEMENTS_PLAN.md docs/features/learning_enhancements.md
mv EXPLICIT_STATE_MACHINE_IMPLEMENTATION.md docs/architecture/state_machine.md
mv UI_REFACTOR_PLAN.md docs/architecture/ui_refactor_plan.md

# Move guides
mv UI_UX_README.md docs/guides/UI_UX_GUIDE.md

# Remove orphaned directories
rm -rf Documents/
rm -rf src/
```

### 2.5: Update Cross-References

After moving files, update references in:
- `.claude/PROJECT_CONTEXT.md`
- `.claude/QUICK_REFERENCE.md`
- `docs/README.md`
- `README.md`

---

## 📋 Phase 3: Backend Reorganization

**Status:** 🔄 Planned (Not Started)
**Timing:** After Phase 2 complete
**Estimated Time:** 1-2 hours

### 3.1: Create Backend Subdirectories

```bash
mkdir -p backend/scripts
mkdir -p backend/data
```

### 3.2: Move Analysis Scripts

```bash
# Move to backend/scripts/
mv backend/analyze_hands.py backend/scripts/
mv backend/analyze_simulation_compliance.py backend/scripts/
mv backend/analyze_with_claude_code.py backend/scripts/
mv backend/debug_hand.py backend/scripts/
mv backend/llm_analyzer.py backend/scripts/
mv backend/simulation.py backend/scripts/
mv backend/simulation_enhanced.py backend/scripts/
```

### 3.3: Move Data Files

```bash
# Move to backend/data/
mv backend/bridge.db backend/data/
mv backend/convention_descriptions.json backend/data/

# Large files - should be in .gitignore
# Keep in backend/data/ but ensure they're ignored
mv backend/simulation_results.json backend/data/
mv backend/claude_code_analysis_data.json backend/data/
mv backend/claude_code_analysis_input.txt backend/data/
```

### 3.4: Update Imports

Files that import from root-level scripts need updating:
- Update any imports in tests
- Update any server.py references
- Update documentation references

---

## 📋 Phase 4: Frontend Consistency

**Status:** 🔄 Planned (Low Priority)
**Timing:** Optional - can be done anytime
**Estimated Time:** 30 minutes

### 4.1: Standardize File Extensions

```bash
# Rename .js → .jsx for React components
# (Only if desired for consistency)
cd frontend/src/components/
# Identify and rename files with JSX content
```

### 4.2: CSS Consolidation

```bash
# After Tailwind migration complete:
# - Remove old CSS files
# - Keep only index.css + Tailwind output
```

---

## ✅ Verification Checklist

After each phase, verify:

### Phase 2 Verification:
- [ ] Root has 8-12 MD files
- [ ] All archived docs are in `docs/project-status/archive/`
- [ ] All milestone docs are in `docs/project-status/` with dates
- [ ] `.claude/` still has all process documents
- [ ] Cross-references updated
- [ ] Run: `python3 .claude/scripts/check_filesystem_health.py`

### Phase 3 Verification:
- [ ] No Python scripts at `backend/` root (except server.py)
- [ ] All data files in `backend/data/`
- [ ] All imports still work
- [ ] Tests still pass: `pytest backend/tests/`

### Phase 4 Verification:
- [ ] Consistent file extensions
- [ ] Build still works: `cd frontend && npm run build`

---

## 🎯 Success Metrics

### Before Cleanup:
```
Root MD files:        27
Root total items:     44
Python cache files:   1,281
.gitignore rules:     0
Temp files:           8+
```

### After Cleanup (Target):
```
Root MD files:        8-12
Root total items:     ~25
Python cache files:   0 (ignored)
.gitignore rules:     ~80
Temp files:           0
```

---

## 🔒 Safety Notes

### Before Starting Phase 2 or 3:

1. **Ensure no active branches conflict**
   ```bash
   git status
   git branch -a
   ```

2. **Create backup branch**
   ```bash
   git checkout -b backup/before-cleanup
   git checkout main
   git checkout -b chore/filesystem-cleanup
   ```

3. **Test after each move**
   ```bash
   # After moving files:
   pytest backend/tests/
   cd frontend && npm run build
   ```

4. **Use git mv for tracking**
   ```bash
   # Instead of: mv file.md docs/
   # Use: git mv file.md docs/
   ```

---

## 📚 Related Documentation

- [`.claude/FILESYSTEM_GUIDELINES.md`](FILESYSTEM_GUIDELINES.md) - Ongoing maintenance rules
- [`.claude/QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - Updated session checklist
- [`.gitignore`](../../.gitignore) - New ignore rules

---

## 📝 Implementation Log

### 2025-10-13: Phase 1 Complete
- ✅ Created `.gitignore` with 80+ rules
- ✅ Removed 8+ temporary files
- ✅ Created filesystem guidelines and health check script
- ✅ Updated quick reference with file system hygiene

### Next: Phase 2
**Wait for:** `refactor/shadcn-tailwind-migration` to merge
**Then:** Execute Phase 2 documentation consolidation
