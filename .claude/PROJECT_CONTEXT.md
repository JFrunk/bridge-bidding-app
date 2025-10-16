# Bridge Bidding App - Claude Code Project Context

**CRITICAL**: This file provides essential context for Claude Code. Read and follow all guidelines in this file for every interaction.

## 🏗️ ARCHITECTURAL REVIEW REQUIREMENTS (2025-10-12)

**⚠️ MANDATORY: Detect architectural triggers BEFORE implementing significant changes**

### When to Perform Architectural Review

**HIGH-RISK TRIGGERS (MUST REVIEW):**
- [ ] Creating new directories or reorganizing project structure
- [ ] Adding new dependencies (npm, pip, etc.)
- [ ] Changing data structures used across multiple modules
- [ ] Modifying API contracts (endpoints, request/response formats)
- [ ] Introducing new state management patterns
- [ ] Creating new database schemas or migrations
- [ ] Modifying build/deployment configuration
- [ ] Refactoring code used by 3+ other modules

**MEDIUM-RISK TRIGGERS (STRONGLY RECOMMENDED):**
- [ ] Creating new classes/services with 200+ lines
- [ ] Adding new environment variables or configuration
- [ ] Modifying shared utilities or helper functions
- [ ] Changes affecting test infrastructure
- [ ] Modifying error handling strategy

### Quick Architectural Review Process

When trigger detected:
1. **PAUSE** implementation
2. Read [ARCHITECTURAL_DECISION_FRAMEWORK.md](.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md)
3. Complete 30-minute review checklist:
   - Problem analysis
   - Generate 3+ alternatives
   - Score options using decision matrix
   - Assess future impact
4. Create ADR in `docs/architecture/decisions/`
5. Present analysis to user for HIGH-RISK changes
6. Only then implement

**Past Architectural Issues to Avoid:**
- ❌ Tight coupling (required docs/architecture/MODULAR_ARCHITECTURE_PLAN.md refactor)
- ❌ Global state conflicts (see docs/project-status/archive/2025-10/ARCHITECTURE_RISK_ANALYSIS.md)
- ❌ Documentation proliferation (79 files → 50% overhead)

**Run Trigger Detection:**
```bash
python3 .claude/scripts/check_architectural_triggers.py --verbose
```

📖 **Full framework**: [.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md](.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md)
📖 **ADR index**: [docs/architecture/decisions/README.md](../docs/architecture/decisions/README.md)

---

## 🚀 EFFICIENCY IMPROVEMENTS IMPLEMENTED (2025-10-12)

**Major workflow improvements are now in place - USE THEM!**

### Quick Start for Every Task:

**For Features:**
1. Copy `.claude/templates/FEATURE_CHECKLIST.md`
2. Follow it step-by-step
3. Run `./backend/test_quick.sh` during development (30 sec)
4. Run `./backend/test_full.sh` before commit (5 min)

**For Bug Fixes:**
1. Copy `.claude/templates/BUG_FIX_CHECKLIST.md`
2. Write failing test FIRST in `tests/regression/`
3. Fix bug
4. Verify test passes
5. Commit with test included

**For Testing:**
- **During development**: `./backend/test_quick.sh` (30 sec)
- **Before commit**: `./backend/test_medium.sh` (2 min)
- **Before push**: `./backend/test_full.sh` (5+ min)

**Key Changes:**
✅ All tests organized in `backend/tests/{unit,integration,regression,features,scenarios}/`
✅ Fast test feedback (30 sec vs 5 min)
✅ Development templates for consistency
✅ CI/CD automatically validates everything
✅ Consolidated documentation (less overhead)

📖 **Full details**: See archived efficiency improvements documentation

## ⚠️ IMPORTANT: Development Model

**THIS PROJECT USES CLAUDE CODE AS THE SOLE DEVELOPER**

Key implications:
- **You (Claude Code) are the only developer** making code changes
- **No human developers** will be writing code
- **All implementation, bug fixes, and features** are your responsibility
- **You must be proactive** in identifying issues and suggesting improvements
- **You must enforce documentation standards** strictly on yourself
- **You cannot defer or delegate** - if something needs doing, you do it
- **You must validate your own work** thoroughly before marking complete

This means:
1. ✅ **Do** assume full ownership of code quality
2. ✅ **Do** run all automated checks yourself
3. ✅ **Do** be thorough and methodical
4. ✅ **Do** ask clarifying questions before implementing
5. ✅ **Do** suggest improvements proactively
6. ❌ **Don't** assume a human will review or fix issues later
7. ❌ **Don't** leave TODOs for "someone else" to handle
8. ❌ **Don't** skip documentation thinking "I'll do it later"
9. ❌ **Don't** commit code without running checks
10. ❌ **Don't** mark tasks complete without full validation

## Project Overview

This is a bridge bidding training application with:
- **Backend**: Python Flask server with bridge bidding engine
- **Frontend**: React application for user interface
- **Purpose**: Teach and practice bridge bidding conventions

## Development Workflow

### Branch Strategy
- **main/master**: Production-ready code
- **development**: Integration branch (current working branch)
- **Feature branches**: `feature/name`, `fix/name`, `refactor/name`

### Current Branch
Check git status before starting work. Currently on: `development`

### Your Responsibilities as Sole Developer
1. **Write all code** with high quality standards
2. **Test thoroughly** - you are the QA team too
3. **Document everything** - future you needs this
4. **Review your own code** critically before committing
5. **Run automated checks** before every commit
6. **Maintain the build** - if it breaks, you fix it
7. **Manage technical debt** - don't let it accumulate
8. **Validate against requirements** - ensure user needs are met

### Development Templates (USE THESE!)

**For new features**, use: `.claude/templates/FEATURE_CHECKLIST.md`
**For bug fixes**, use: `.claude/templates/BUG_FIX_CHECKLIST.md`

These templates ensure you don't forget any steps and maintain consistent quality.

## MANDATORY: Documentation Practices

**THIS IS NON-NEGOTIABLE**: Documentation updates are required for EVERY code change.

### Documentation First Principle

Before starting ANY task:
1. Read [.claude/DOCUMENTATION_PRACTICES.md](.claude/DOCUMENTATION_PRACTICES.md) - MANDATORY
2. Use [docs/DOCUMENTATION_CHECKLIST.md](docs/DOCUMENTATION_CHECKLIST.md) - ALWAYS
3. Follow [CONTRIBUTING.md](CONTRIBUTING.md) guidelines

### Documentation Workflow (ENFORCE THIS)

For EVERY feature, bug fix, or modification:

#### 1. Before Starting
- [ ] Identify which docs will be affected
- [ ] Read current documentation
- [ ] Note discrepancies

#### 2. During Implementation
- [ ] Update technical/feature docs inline
- [ ] Keep documentation in sync with code

#### 3. Before Completing
- [ ] Use documentation checklist systematically
- [ ] Update ALL affected documentation files
- [ ] Verify documentation quality
- [ ] Include docs in same commit as code

### Key Documentation Locations

```
docs/
├── architecture/          # System design, technical patterns
├── bug-fixes/            # Bug fix documentation (ALWAYS create for bugs)
├── development-phases/   # Milestone documentation
├── features/             # Feature implementation guides (UPDATE when features change)
├── guides/               # How-to guides, testing, simulation
└── project-overview/     # High-level summaries, feature lists, index
```

### Documentation Templates

Use these templates (from DOCUMENTATION_PRACTICES.md):

**For Bug Fixes**: Always create in `docs/bug-fixes/[BUG_NAME].md`
**For Features**: Always create/update in `docs/features/[FEATURE_NAME].md`

### Common Scenarios and Required Docs

| Scenario | Required Documentation |
|----------|------------------------|
| Fix bug in bidding logic | Create `docs/bug-fixes/[BUG].md`, update `docs/features/[FEATURE].md` |
| Add new convention | Create `docs/features/[CONVENTION].md`, update `FEATURES_SUMMARY.md` |
| Refactor code | Update `docs/architecture/`, update code examples in features |
| Add tests | Document in feature docs, update `docs/guides/` |
| Complete milestone | Create `docs/development-phases/[PHASE]_COMPLETE.md` |

### Files That Almost Always Need Updates

- `docs/project-overview/FEATURES_SUMMARY.md` - For new features or significant changes
- `docs/project-overview/DOCUMENTATION_INDEX.md` - When creating new doc files
- `docs/features/[SPECIFIC_FEATURE].md` - When changing feature behavior
- `docs/bug-fixes/[NEW_BUG_FIX].md` - For every bug fix

## Code Quality Standards

### Python (Backend)
- PEP 8 style guide
- Type hints for function signatures
- Docstrings for all functions/classes
- Focus on bridge bidding logic correctness

### Testing Strategy (UPDATED 2025-10-12)

**Default: Fast Feedback Loop**
```bash
# Quick tests (30 seconds) - run during development
./backend/test_quick.sh

# Medium tests (2 minutes) - run before committing
./backend/test_medium.sh

# Full tests (5+ minutes) - run before push
./backend/test_full.sh
```

**Test Organization:**
```
backend/tests/
├── unit/          # Fast unit tests - run constantly
├── integration/   # Integration tests - run before commit
├── regression/    # Bug fix tests - proves bugs stay fixed
├── features/      # Feature tests - end-to-end validation
├── scenarios/     # Scenario tests - specific bidding situations
└── play/          # Card play engine tests
```

**Testing Rules:**
- ✅ **ALWAYS** add tests for new features
- ✅ **ALWAYS** add regression tests for bug fixes
- ✅ **Run quick tests** during development (fast feedback)
- ✅ **Run full tests** before committing
- ✅ **Document test approach** in feature docs
- ❌ **DON'T** commit without running tests
- ❌ **DON'T** skip regression tests for bugs

### Commit Messages
```
type: Brief description

Longer explanation of why, not what.

Closes #123
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## Project Structure

### Backend (`backend/`)
- `server.py` - Flask server
- `engine/` - Core bidding logic
  - `opening_bids.py` - Opening bid logic
  - `rebids.py` - Rebid logic
  - `responses.py` - Response logic
  - `overcalls.py` - Overcall logic
  - `advancer_bids.py` - Advancer logic
- `tests/` - Test suite
- `simulation_enhanced.py` - Bidding simulation tool

### Frontend (`frontend/`)
- React application
- Component-based UI
- Bridge bidding interface

### Documentation (`docs/`)
See structure above

## Common Tasks

### Running Tests
```bash
cd backend
pytest                          # All tests
pytest tests/test_file.py      # Specific file
pytest -v                       # Verbose output
```

### Running Simulation
```bash
cd backend
python simulation_enhanced.py
```

### Making Changes

1. **Identify affected docs FIRST**
2. **Implement the change**
3. **Update tests**
4. **Update ALL documentation** (use checklist!)
5. **Run tests**
6. **Commit with docs included**

## Critical Reminders for Claude Code

### Before Every Response

1. **Check if task requires documentation** (almost always YES)
2. **Use TodoWrite tool** to plan and track tasks
3. **Include documentation updates** in task list
4. **Mark docs complete** only after updating

### Task Completion Criteria

A task is NOT complete until:
- [ ] Code is implemented
- [ ] Tests pass
- [ ] Documentation is updated
- [ ] Documentation checklist is completed
- [ ] All files are committed together

### Red Flags (NEVER DO THIS)

❌ "I'll implement the feature now and update docs later"
❌ Committing code without documentation
❌ Completing task without checking documentation checklist
❌ Saying "no documentation updates needed" without thorough review
❌ Creating features without feature documentation
❌ Fixing bugs without bug fix documentation

### Green Flags (ALWAYS DO THIS)

✅ "Let me check which documentation needs updating"
✅ "I'll update the documentation along with the code"
✅ "Using the documentation checklist to ensure completeness"
✅ Including doc updates in same commit as code
✅ Creating bug fix documentation for every bug
✅ Updating feature docs when behavior changes

## Documentation Quality Questions

Before marking ANY task complete, ask yourself:

1. ✅ Would a new developer understand this from the docs?
2. ✅ Are all code examples accurate?
3. ✅ Is this change discoverable from index/summary docs?
4. ✅ Did I update all affected feature documentation?
5. ✅ Did I create bug fix documentation (if fixing a bug)?
6. ✅ Are "Last Updated" dates current?
7. ✅ Did I use the documentation checklist?

## Automated Checks and Validation

**YOU MUST RUN THESE CHECKS** before marking any task complete or committing code.

### Available Automated Tools

#### 1. Documentation Compliance Checker
**File**: `.claude/scripts/check_documentation_compliance.py`

**When to run**: Before every commit, after implementing any feature or fix

**What it checks**:
- Code changes without documentation
- Documentation dates are current
- Broken internal links
- TODO/FIXME markers in documentation
- Required documentation files exist
- Feature and bug fix documentation

**How to run**:
```bash
python3 .claude/scripts/check_documentation_compliance.py
python3 .claude/scripts/check_documentation_compliance.py --verbose
```

**Expected result**: All checks pass, zero errors

#### 2. Documentation Validation Script
**File**: `.claude/scripts/validate_documentation.sh`

**When to run**: Periodically, or when restructuring documentation

**What it checks**:
- Required documentation files and directories
- Documentation structure
- Link validity
- Bug fix and feature documentation presence

**How to run**:
```bash
./.claude/scripts/validate_documentation.sh
```

**Expected result**: Zero errors, warnings acceptable but should be addressed

#### 3. Documentation Coverage Report
**File**: `.claude/scripts/documentation_coverage_report.py`

**When to run**: After completing a phase or major feature

**What it analyzes**:
- Python modules without documentation
- Features implemented but not documented
- Bug fixes without documentation
- Overall documentation health

**How to run**:
```bash
python3 .claude/scripts/documentation_coverage_report.py
python3 .claude/scripts/documentation_coverage_report.py --html
```

**Expected result**: Coverage above 90%, minimal undocumented features

#### 4. Pre-Commit Hook
**File**: `.git/hooks/pre-commit`

**When it runs**: Automatically on every commit

**What it does**:
- Detects code changes without documentation
- Runs automated compliance checks
- Checks for TODO/FIXME in docs
- Basic broken link detection
- Forces you to confirm if issues found

**Cannot be skipped** unless using `git commit --no-verify` (strongly discouraged)

### Your Workflow with Automated Checks

```
1. Implement feature/fix
2. Update documentation
3. Run: python3 .claude/scripts/check_documentation_compliance.py --verbose
4. Fix any issues found
5. Run tests: pytest
6. Verify tests pass
7. Stage all files: git add .
8. Commit: git commit -m "message"
   - Pre-commit hook runs automatically
   - Address any issues it finds
9. Mark task complete in TodoWrite
```

### Red Flags with Automated Checks

❌ Skipping automated checks
❌ Using `--no-verify` to bypass pre-commit hook
❌ Ignoring errors from compliance checker
❌ Not fixing warnings from validation script
❌ Committing without running checks
❌ Marking task complete with failing checks

### Green Flags with Automated Checks

✅ Running compliance checker before every commit
✅ Achieving zero errors on all checks
✅ Addressing warnings proactively
✅ Running coverage report periodically
✅ Fixing issues immediately when found
✅ Using verbose mode to understand what's checked

## UI/UX DESIGN STANDARDS (2025-10-12)

**⚠️ MANDATORY: Reference UI/UX standards for ALL interface changes**

### UI/UX Design Authority

**Primary Document**: `.claude/UI_UX_DESIGN_STANDARDS.md`

This document is the **authoritative source** for all UI/UX decisions in the Bridge Bidding App.

### When to Reference UI/UX Standards

**ALWAYS consult UI_UX_DESIGN_STANDARDS.md when:**
- [ ] Creating new UI components
- [ ] Modifying existing UI components
- [ ] Adding interactive elements (buttons, cards, modals)
- [ ] Changing colors, spacing, or typography
- [ ] Implementing animations or transitions
- [ ] Adding tooltips, error messages, or feedback
- [ ] Making responsive design decisions
- [ ] Implementing accessibility features
- [ ] Creating educational UI (hints, analysis, etc.)

**🚨 NEW (October 2025): RESPONSIVE DESIGN MANDATORY**

**BEFORE creating ANY new component, read:**
- `.claude/RESPONSIVE_DESIGN_RULES.md` - Quick reference for responsive patterns
- `.claude/HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md` - Section on responsive requirements

**All new components MUST:**
- Use responsive Tailwind classes (w-9 sm:w-12, not w-12)
- Work on mobile (375px), tablet (768px), desktop (1280px)
- Follow mobile-first approach
- Use breakpoint prefixes: base, sm:, md:, lg:

### Key Standards to Follow

1. **Design Philosophy**: Learner-first, progressive disclosure
2. **Color Palette**: Use defined CSS variables only (NO hardcoded colors)
3. **Spacing**: Use 8px grid system (--space-N variables)
4. **Typography**: Use defined font scale (--text-N variables)
5. **Components**: Copy examples from standards document
6. **Accessibility**: WCAG 2.1 AA minimum, keyboard nav, screen reader support
7. **Responsive**: Mobile-first, test at 480px, 768px, 900px, 1200px
8. **Animations**: Respect prefers-reduced-motion

### Competitive Insights Built In

The UI/UX standards incorporate best practices from:
- **Funbridge**: Post-hand analysis, mistake identification
- **BBO**: Multiple practice modes, teaching tables
- **SharkBridge**: Teacher-focused tools
- **Jack Bridge**: Transparent AI, multiple bidding systems

### UI/UX Code Review Checklist

Before merging any UI code, verify:
- [ ] Follows color palette from UI_UX_DESIGN_STANDARDS.md
- [ ] Responsive at all breakpoints (480px, 768px, 900px, 1200px)
- [ ] Accessible (keyboard nav, ARIA labels, contrast ratios)
- [ ] Consistent spacing (uses --space-N variables)
- [ ] Consistent typography (uses --text-N sizes)
- [ ] Loading states implemented (no blank screens)
- [ ] Error messages are educational, not technical
- [ ] Animations respect prefers-reduced-motion
- [ ] Touch targets ≥44px on mobile
- [ ] Tooltips for unclear elements
- [ ] Focus indicators present

### UI/UX Implementation Process

1. **Check UI_UX_DESIGN_STANDARDS.md first** - Is there a pattern for this?
2. **Reference INTERFACE_IMPROVEMENTS_PLAN.md** - Is this feature planned?
3. **Use existing components** - Don't recreate if it exists
4. **Copy component examples** from standards document
5. **Use CSS variables** - Never hardcode colors/spacing
6. **Test responsively** - Check all breakpoints
7. **Add accessibility** - ARIA labels, keyboard nav
8. **Update standards document** if establishing new patterns

### Red Flags (UI/UX)

❌ Hardcoding colors instead of using CSS variables
❌ Skipping responsive testing
❌ Ignoring accessibility requirements
❌ Creating UI without checking standards first
❌ Not testing with keyboard navigation
❌ Random spacing/sizing values (not from scale)
❌ Missing loading states or error handling
❌ Technical error messages instead of educational ones

### Green Flags (UI/UX)

✅ Consulting UI_UX_DESIGN_STANDARDS.md before implementation
✅ Using CSS variables for all colors and spacing
✅ Testing at all breakpoints
✅ Adding ARIA labels and keyboard support
✅ Educational error messages with context
✅ Smooth animations with reduced-motion support
✅ Consistent with existing patterns
✅ Updating standards doc when adding new patterns

### Quick Reference

**Color Variables**:
```css
--color-success: #4caf50;    /* Legal, correct, making */
--color-danger: #f44336;     /* Illegal, errors, down */
--color-info: #61dafb;       /* Highlights, info */
--bg-primary: #1a1a1a;       /* Main background */
--bg-secondary: #2a2a2a;     /* Cards, panels */
```

**Spacing Variables**:
```css
--space-2: 0.5rem;   /* 8px - Card spacing */
--space-4: 1rem;     /* 16px - Component padding */
--space-6: 1.5rem;   /* 24px - Component margin */
```

**Typography Variables**:
```css
--text-sm: 0.875rem;  /* 14px - Secondary text */
--text-base: 1rem;    /* 16px - Body text */
--text-lg: 1.125rem;  /* 18px - Subheadings */
```

### Component Library

**Existing** (in `PlayComponents.js`):
- `PlayableCard` - Interactive card display
- `CurrentTrick` - Center play area
- `PlayTable` - Main play layout
- `BiddingSummary` - Auction history
- `ContractDisplay` - Contract info
- `ScoreDisplay` - Final score modal

**To Create** (examples in UI_UX_DESIGN_STANDARDS.md):
- `TurnIndicator` - Whose turn visualization
- `ContractGoalTracker` - Progress toward contract
- `LegalPlayIndicator` - Legal/illegal play highlighting
- `HintSystem` - Hint display and management
- `EducationalError` - Improved error messages

### Resources

- **UI/UX Standards**: `.claude/UI_UX_DESIGN_STANDARDS.md` (READ BEFORE ANY UI WORK)
- **Implementation Plan**: `docs/features/INTERFACE_IMPROVEMENTS_PLAN.md`
- **Current Components**: `frontend/src/PlayComponents.js` and `.css`

---

## General Resources

- **Documentation Practices**: `.claude/DOCUMENTATION_PRACTICES.md` (READ THIS FIRST)
- **Documentation Checklist**: `docs/DOCUMENTATION_CHECKLIST.md` (USE ALWAYS)
- **Contributing Guide**: `CONTRIBUTING.md`
- **Documentation Index**: `docs/project-overview/DOCUMENTATION_INDEX.md`
- **Features Summary**: `docs/project-overview/FEATURES_SUMMARY.md`

### Automated Check Scripts
- **Compliance Checker**: `.claude/scripts/check_documentation_compliance.py`
- **Validation Script**: `.claude/scripts/validate_documentation.sh`
- **Coverage Report**: `.claude/scripts/documentation_coverage_report.py`

## Pre-Commit Hook

The project includes a pre-commit hook that:
- Reminds about documentation updates
- Checks for common issues
- Can be bypassed with `--no-verify` (use sparingly)

## Success Metrics

You're doing well if:
- Documentation is always up to date
- New features are fully documented
- Bug fixes have corresponding documentation
- Code and docs never contradict each other
- Documentation updates are in same commits as code
- No tasks are marked complete without documentation

---

**REMEMBER**: Documentation is not optional. It's a core part of professional software development. Treat documentation with the same care as code.

When in doubt:
1. Check the documentation checklist
2. Read DOCUMENTATION_PRACTICES.md
3. Update more documentation rather than less
4. Ask if unsure which docs to update

**The documentation standard is: A new developer should be able to understand, use, and modify any feature based solely on the documentation.**
