# Documentation Index

**Last Updated:** 2025-10-23

This document provides a quick reference to all major documentation in the project.

---

## 🎨 UI/UX Standards (NEW - 2025-10-12)

### Authoritative Standards
- **[.claude/UI_UX_DESIGN_STANDARDS.md](../../.claude/UI_UX_DESIGN_STANDARDS.md)** ⭐ MUST READ BEFORE ANY UI WORK
  - Complete UI/UX reference based on competitive analysis
  - Color palette, spacing, typography systems
  - Component patterns with copy-paste examples
  - Accessibility and responsive design standards
  - Educational UI patterns for learners
  - 13,000+ words of comprehensive guidance

### Implementation & Planning
- **[docs/features/INTERFACE_IMPROVEMENTS_PLAN.md](../features/INTERFACE_IMPROVEMENTS_PLAN.md)** - 4-phase UI roadmap
  - Phase 1: Core educational features (turn indicators, hints, contract tracking)
  - Phase 2: Post-hand analysis (mistake identification, replay)
  - Phase 3: Practice modes (Just Declare, daily challenges)
  - Phase 4: Advanced features (AI explanations, teaching tools)
  - Based on competitive analysis of BBO, Funbridge, SharkBridge, Jack

### Usage Guides
- **[.claude/HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md](../../.claude/HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md)** - How the auto-loading system works
- **[.claude/UI_QUICK_START.md](../../.claude/UI_QUICK_START.md)** - Quick reference card for rapid lookup
- **[UI_UX_STANDARDS_IMPLEMENTATION_COMPLETE.md](../../UI_UX_STANDARDS_IMPLEMENTATION_COMPLETE.md)** - Implementation summary

### Current UI Components
- **[frontend/src/PlayComponents.js](../../frontend/src/PlayComponents.js)** - Existing play UI components
- **[frontend/src/PlayComponents.css](../../frontend/src/PlayComponents.css)** - Current styles

**Key Takeaway:** All UI work must reference UI_UX_DESIGN_STANDARDS.md to ensure consistency with established patterns and competitive best practices.

---

## 📋 Quick Status Documents

### Current Status
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Overall project status with metrics
- **[CARD_PLAY_INTEGRATION_STATUS.md](CARD_PLAY_INTEGRATION_STATUS.md)** - Card play integration progress (2025-10-12)

### Phase Completion Reports
- **[PHASE1_COMPLETE.md](PHASE1_COMPLETE.md)** - Phase 1 critical fixes completion
- **[OPTION1_COMPLETE.md](OPTION1_COMPLETE.md)** - Complete Option 1 validation

### Master Tracking
- **[docs/features/CONVENTION_FIXES_PUNCHLIST.md](docs/features/CONVENTION_FIXES_PUNCHLIST.md)** - 33-issue master tracker

---

## 🔧 Active Debugging (2025-10-12)

### Hand Display Investigation
1. **[DEBUG_HAND_DISPLAY.md](DEBUG_HAND_DISPLAY.md)** ⭐ START HERE
   - Complete debugging guide
   - Console output interpretation
   - Step-by-step verification

2. **[HAND_DISPLAY_CORRECTION.md](HAND_DISPLAY_CORRECTION.md)**
   - Explains previous analysis error
   - Correct declarer/dummy positions
   - Why expectations changed

3. **[CHECK_HAND_DISPLAY.md](CHECK_HAND_DISPLAY.md)**
   - Quick reference for expected behavior
   - Display logic conditions
   - Visual checklist

---

## 🎮 Card Play Documentation

### User Guides
- **[GAMEPLAY_STARTUP_GUIDE.md](../guides/GAMEPLAY_STARTUP_GUIDE.md)** ⭐ **START HERE** - Complete startup & testing guide
- **[START_APP.md](../../START_APP.md)** - Quick reference (3-step start)
- **[GAMEPLAY_LOCAL_TESTING_GUIDE.md](../guides/GAMEPLAY_LOCAL_TESTING_GUIDE.md)** - How to test gameplay locally
- **[HOW_TO_CHECK_AI_LOOP.md](../guides/HOW_TO_CHECK_AI_LOOP.md)** - Understanding AI loop indicator

### Technical Documentation
- **[PLAY_STATE_ARCHITECTURE.md](PLAY_STATE_ARCHITECTURE.md)** - State management design
- **[PLAY_SEQUENCE_REVIEW.md](PLAY_SEQUENCE_REVIEW.md)** - Complete code review (400+ lines)
- **[AI_PLAY_LOGGING.md](../features/AI_PLAY_LOGGING.md)** - AI performance monitoring system (2025-10-23)

### Bug Fix Documentation
- **[FIX_CARD_DISPLAY_ISSUE.md](FIX_CARD_DISPLAY_ISSUE.md)** - Initial card display fix
- **[FIX_AI_CARDS_NOT_SHOWING.md](FIX_AI_CARDS_NOT_SHOWING.md)** - AI card display fix
- **[SESSION_PERSISTENCE_FIX_2025-10-23.md](../bug-fixes/SESSION_PERSISTENCE_FIX_2025-10-23.md)** - Session hand saving improvements (2025-10-23)

---

## 📚 Architecture & Development

### Core Architecture
- **[CLAUDE.md](CLAUDE.md)** ⭐ ESSENTIAL - Project overview and development guide
  - Stack overview
  - Architecture diagrams
  - Development commands
  - Common pitfalls

### Code Documentation
- **[backend/README.md](backend/README.md)** - Backend architecture (if exists)
- **[frontend/README.md](frontend/README.md)** - Frontend structure (if exists)

### Recent Improvements (October 2025)
- **[BIDDING_ENGINE_IMPROVEMENTS_2025-10-23.md](../bug-fixes/BIDDING_ENGINE_IMPROVEMENTS_2025-10-23.md)** - Bidding accuracy enhancements
  - Advancer bids, rebids, responses improvements
  - Blackwood, Jacoby Transfers, Michaels Cuebid refinements
  - +204 lines across 8 files

---

## 🧪 Testing Documentation

### Test Reports
- **[backend/TEST_VALIDATION_REPORT.md](backend/TEST_VALIDATION_REPORT.md)** - Detailed test results
- **[backend/test_manual_scenarios.py](backend/test_manual_scenarios.py)** - Manual test scenarios

### Test Commands
```bash
# All tests
cd backend && source venv/bin/activate && python3 -m pytest -v

# Bidding tests only
pytest tests/test_*.py -v

# Play tests only
pytest tests/play/ -v

# Specific module
pytest tests/test_opening_bids.py -v
```

---

## 📂 Document Organization

### Root Level (Current Status & Quick Refs)
```
bridge_bidding_app/
├── PROJECT_STATUS.md                    ⭐ Main status
├── CARD_PLAY_INTEGRATION_STATUS.md      ⭐ Card play progress
├── DOCUMENTATION_INDEX.md               ⭐ This file
├── CLAUDE.md                            ⭐ Development guide
├── PHASE1_COMPLETE.md
├── OPTION1_COMPLETE.md
├── DEBUG_HAND_DISPLAY.md                🔧 Active debugging
├── HAND_DISPLAY_CORRECTION.md           🔧 Active debugging
├── CHECK_HAND_DISPLAY.md                🔧 Active debugging
├── GAMEPLAY_LOCAL_TESTING_GUIDE.md
├── HOW_TO_CHECK_AI_LOOP.md
├── PLAY_STATE_ARCHITECTURE.md
├── PLAY_SEQUENCE_REVIEW.md
├── FIX_CARD_DISPLAY_ISSUE.md
└── FIX_AI_CARDS_NOT_SHOWING.md
```

### docs/ Directory (Organized Docs)
```
docs/
├── features/
│   └── CONVENTION_FIXES_PUNCHLIST.md    ⭐ Master tracker
├── project-overview/
│   └── (various overview docs)
└── development-phases/
    ├── PHASE1_MVP_STATUS.md
    └── (phase-specific docs)
```

### backend/ Directory
```
backend/
├── TEST_VALIDATION_REPORT.md
└── tests/
    └── (test files)
```

---

## 🔍 Finding What You Need

### "What's the current status?"
→ [PROJECT_STATUS.md](PROJECT_STATUS.md)

### "What works and what doesn't?"
→ [PROJECT_STATUS.md](PROJECT_STATUS.md) - Section: "What Works Right Now"

### "How do I test the gameplay?"
→ [GAMEPLAY_LOCAL_TESTING_GUIDE.md](GAMEPLAY_LOCAL_TESTING_GUIDE.md)

### "What's being worked on now?"
→ [CARD_PLAY_INTEGRATION_STATUS.md](CARD_PLAY_INTEGRATION_STATUS.md) - Section: "Active Work"

### "Why aren't the right hands showing?"
→ [DEBUG_HAND_DISPLAY.md](DEBUG_HAND_DISPLAY.md) ⭐

### "How do I develop/add features?"
→ [CLAUDE.md](CLAUDE.md) - Sections: "Architecture" & "Adding New Conventions"

### "What are all the issues/bugs?"
→ [PROJECT_STATUS.md](PROJECT_STATUS.md) - Section: "Known Issues"
→ [docs/features/CONVENTION_FIXES_PUNCHLIST.md](docs/features/CONVENTION_FIXES_PUNCHLIST.md)

### "How do I run tests?"
→ [CLAUDE.md](CLAUDE.md) - Section: "Development Commands"

### "What's the test coverage?"
→ [backend/TEST_VALIDATION_REPORT.md](backend/TEST_VALIDATION_REPORT.md)

### "What conventions are implemented?"
→ [PROJECT_STATUS.md](PROJECT_STATUS.md) - Section: "What Works Right Now"

---

## 📊 Document Types

### Status Documents (Present Tense)
Current state of the project
- PROJECT_STATUS.md
- CARD_PLAY_INTEGRATION_STATUS.md

### Completion Reports (Past Tense)
What was accomplished
- PHASE1_COMPLETE.md
- OPTION1_COMPLETE.md

### Guides (Instructional)
How to do something
- CLAUDE.md
- GAMEPLAY_LOCAL_TESTING_GUIDE.md
- DEBUG_HAND_DISPLAY.md

### Technical Docs (Reference)
How things work
- PLAY_STATE_ARCHITECTURE.md
- PLAY_SEQUENCE_REVIEW.md

### Fix Documentation (Historical)
What was fixed and how
- FIX_CARD_DISPLAY_ISSUE.md
- FIX_AI_CARDS_NOT_SHOWING.md

---

## 🔄 Update Frequency

### Updated Daily (During Active Development)
- PROJECT_STATUS.md
- CARD_PLAY_INTEGRATION_STATUS.md
- Active debugging docs (DEBUG_HAND_DISPLAY.md, etc.)

### Updated Per Phase
- Phase completion reports
- Master tracker (CONVENTION_FIXES_PUNCHLIST.md)
- TEST_VALIDATION_REPORT.md

### Updated As Needed
- CLAUDE.md (when architecture changes)
- Technical architecture docs
- User guides

### Static (Historical Record)
- Phase completion reports (PHASE1_COMPLETE.md)
- Fix documentation (FIX_*.md)

---

## 🎯 For New Developers

**Start with these 3 documents:**
1. **[CLAUDE.md](CLAUDE.md)** - Understand the architecture
2. **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Know what's working
3. **[CARD_PLAY_INTEGRATION_STATUS.md](CARD_PLAY_INTEGRATION_STATUS.md)** - Current work

**Then explore:**
- Master tracker for all issues
- Test reports for coverage
- Technical docs for deep dives

---

## 🎯 For Users/Testers

**Start here:**
1. **[GAMEPLAY_LOCAL_TESTING_GUIDE.md](GAMEPLAY_LOCAL_TESTING_GUIDE.md)** - How to test

**If something seems wrong:**
1. **[DEBUG_HAND_DISPLAY.md](DEBUG_HAND_DISPLAY.md)** - Hand display issues
2. **[HOW_TO_CHECK_AI_LOOP.md](HOW_TO_CHECK_AI_LOOP.md)** - AI not playing

**To report issues:**
- Check [PROJECT_STATUS.md](PROJECT_STATUS.md) - "Known Issues" section first
- Provide console output from browser (F12)
- Describe what you expected vs what happened

---

## 📝 Documentation Standards & Guidelines

### CRITICAL: Documentation Maintenance Requirements

**Documentation is mandatory for all code changes.** This is not optional.

#### Essential Documentation Resources
1. **[.claude/DOCUMENTATION_PRACTICES.md](../../.claude/DOCUMENTATION_PRACTICES.md)** ⭐ MUST READ
   - Comprehensive guidelines for maintaining documentation
   - Required workflow for every code change
   - Documentation templates and examples
   - Claude Code specific instructions

2. **[docs/DOCUMENTATION_CHECKLIST.md](../DOCUMENTATION_CHECKLIST.md)** ⭐ USE ALWAYS
   - Systematic checklist for every feature/bug fix
   - Quality checks and review questions
   - Special case guidance

3. **[CONTRIBUTING.md](../../CONTRIBUTING.md)** ⭐ CONTRIBUTING GUIDE
   - Development workflow
   - Documentation requirements
   - Code standards and testing
   - PR process with documentation

4. **[.github/pull_request_template.md](../../.github/pull_request_template.md)**
   - PR template with documentation checklist
   - Ensures documentation is reviewed

### Documentation Update Workflow

For EVERY code change:
1. **Before**: Identify affected documentation
2. **During**: Update docs inline with code
3. **After**: Systematic review using checklist
4. **Commit**: Include docs in same commit as code

### File Naming Conventions
- `PROJECT_STATUS.md` - Overall status
- `PHASE1_COMPLETE.md` - Phase completion
- `FIX_*.md` - Bug fix documentation (required for all bug fixes)
- `DEBUG_*.md` - Active debugging
- `*_GUIDE.md` - User guides
- `CONVENTION_NAME.md` - Feature documentation

### Documentation Directory Structure
```
docs/
├── architecture/          # System design, patterns, technical architecture
├── bug-fixes/            # Bug fix documentation (create for every bug)
├── development-phases/   # Milestone and phase completion docs
├── features/             # Feature implementation guides (update when features change)
├── guides/               # How-to guides, simulation, testing
└── project-overview/     # High-level summaries, feature lists, this index
```

### Section Formatting
```markdown
# Feature/Document Name

**Status:** [In Progress / Complete / Deprecated]
**Last Updated:** YYYY-MM-DD

## Overview
Brief description

## [Additional Sections]
Detailed content
```

### Status Indicators
- ✅ Complete/Working
- 🔧 In Progress/Active Development
- ⏳ Pending/Not Started
- ⚠️ Issue/Warning
- ❌ Broken/Failed
- ⭐ Important/Start Here
- 🗂️ Archived/Deprecated

### Pre-Commit Hook

The project includes a pre-commit hook (`.git/hooks/pre-commit`) that:
- Reminds about documentation updates when committing code
- Checks for common documentation issues
- Can be bypassed with `--no-verify` (use sparingly!)

### Documentation Quality Standards

Documentation is complete when:
- A new developer can understand the system from docs alone
- Code and docs never contradict each other
- Features are discoverable through documentation
- All code examples are accurate and tested
- Historical context is preserved

---

## 🔗 Quick Links

### External Resources
- [SAYC Rules](https://www.acbl.org/learn_page/how-to-play-bridge/standard-american-yellow-card/) - Official SAYC conventions
- [Bridge Laws](http://www.worldbridge.org/laws-and-regulations/) - International bridge laws

### Related Files
- [requirements.txt](backend/requirements.txt) - Python dependencies
- [package.json](frontend/package.json) - Node dependencies
- [scenarios.json](backend/scenarios.json) - Training scenarios

---

**Maintained by:** Claude Code (with human oversight)
**Last Review:** 2025-10-23
**Next Review:** As needed

---

## 📦 Recent Deployments (October 2025)

### October 23, 2025 - AI Logging & Bidding Improvements

**Commit:** a0c1629

**Features Added:**
- **AI Play Logging** - Performance monitoring for DDS quality assurance
  - See: [AI_PLAY_LOGGING.md](../features/AI_PLAY_LOGGING.md)

**Bug Fixes:**
- **Bidding Engine Improvements** - Enhanced accuracy across conventions
  - See: [BIDDING_ENGINE_IMPROVEMENTS_2025-10-23.md](../bug-fixes/BIDDING_ENGINE_IMPROVEMENTS_2025-10-23.md)

- **Session Persistence Fix** - Reliable hand saving to database
  - See: [SESSION_PERSISTENCE_FIX_2025-10-23.md](../bug-fixes/SESSION_PERSISTENCE_FIX_2025-10-23.md)

**UI/UX Improvements:**
- **Learning Dashboard Empty State** - Better onboarding for new players
  - See: [learning_enhancements.md](../features/learning_enhancements.md)

**Files Changed:** 12 files, +665 insertions, -39 deletions
