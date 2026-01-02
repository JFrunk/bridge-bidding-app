# Claude Code Handoff Context

**Created:** 2025-11-25
**Purpose:** Comprehensive context for continuing development with an upgraded Claude Code instance

---

## Executive Summary

This is a **Bridge Bidding Training Application** that teaches Standard American Yellow Card (SAYC) bidding. The project is in active development with a working production deployment on Render.

**Current Status:** Feature-complete for core bidding and card play, with ongoing polish and bug fixes.

---

## Recent Work Completed (October-November 2025)

### Major Accomplishments

1. **Filesystem Cleanup (Nov 2, 2025)** - Reduced root directory from 180 MD files to 8 (95.6% reduction)
   - All docs now organized in `docs/` subdirectories
   - Scripts moved to `scripts/analysis/` and `scripts/testing/`
   - Quality baselines in `quality_scores/`
   - See: [docs/project-status/2025-11/FILESYSTEM_CLEANUP_COMPLETE_2025-11-02.md](../docs/project-status/2025-11/FILESYSTEM_CLEANUP_COMPLETE_2025-11-02.md)

2. **Convention System Complete (Oct 2025)** - 31/33 convention issues fixed (94%)
   - All 13 critical issues resolved
   - Jacoby Transfers, Stayman, Blackwood fully functional
   - Michaels Cuebid, Unusual 2NT, Splinter Bids, Fourth Suit Forcing implemented
   - See: [docs/features/CONVENTION_FIXES_PUNCHLIST.md](../docs/features/CONVENTION_FIXES_PUNCHLIST.md)

3. **Error Logging System (Nov 2025)** - Automated error capture and analysis
   - Run: `python3 backend/analyze_errors.py --recent 10`
   - See: [docs/features/ERROR_LOGGING_SYSTEM.md](../docs/features/ERROR_LOGGING_SYSTEM.md)

4. **DDS Integration** - Double Dummy Solver for AI play (Level 9-10)
   - Works on Linux production only (crashes on macOS M1/M2)
   - Use Level 8 (Minimax) for development testing
   - See: [docs/guides/VERIFY_DDS_IN_PRODUCTION.md](../docs/guides/VERIFY_DDS_IN_PRODUCTION.md)

### Recent Bug Fixes (November 2025)

1. **AI Bidding Stuck Fix** - Fixed race condition in AI bidding loop
   - See: [docs/bug-fixes/2025-11/AI_BIDDING_STUCK_FIX_2025-11-01.md](../docs/bug-fixes/2025-11/AI_BIDDING_STUCK_FIX_2025-11-01.md)

2. **Michaels Cuebid Fix** - Corrected cuebid detection and response logic
   - See: [docs/bug-fixes/2025-11/MICHAELS_CUEBID_FIX_2025-11-02.md](../docs/bug-fixes/2025-11/MICHAELS_CUEBID_FIX_2025-11-02.md)

3. **Performance Bug Fix** - Resolved slow response times
   - See: [docs/bug-fixes/2025-11/PERFORMANCE_BUG_FIX_2025-11-01.md](../docs/bug-fixes/2025-11/PERFORMANCE_BUG_FIX_2025-11-01.md)

4. **Play Control Error Messaging** - Improved 403 response handling
   - See: [docs/bug-fixes/PLAY_CONTROL_ERROR_MESSAGING_2025-11-03.md](../docs/bug-fixes/PLAY_CONTROL_ERROR_MESSAGING_2025-11-03.md)

---

## Known Issues & Work in Progress

### Critical (Priority: HIGH)

1. **First Hand After Server Startup Bug** - Intermittent, AI players may receive wrong hands
   - Status: Not reliably reproducible
   - Root cause: Race condition in `/api/get-next-bid` endpoint
   - Proposed fix: Add request queuing, session-based state management
   - See: [docs/bug-fixes/RESIDUAL_ISSUES.md](../docs/bug-fixes/RESIDUAL_ISSUES.md)

### Moderate (Priority: MEDIUM)

1. **Remaining Convention Issues (2 items)**
   - Issue #15: Gambling 3NT and 4-level openings (rare, low priority)
   - Issue #23: Michaels Cuebid edge cases (deferred to Phase 3)

2. **Inverted Minors** - Optional convention, not implemented
   - Low priority, can be added if requested

### Minor (Priority: LOW)

1. **Card Play Phase Enhancements**
   - No play history UI
   - No undo/redo
   - No claim feature
   - No play analysis feedback
   - No animations or sound effects

---

## Current Quality Scores

### Bidding Quality (as of Oct 2025)

```
Test: 500 hands, 3,013 bids
Composite: 89.7% (Grade C)

Breakdown:
- Legality:        100.0% (PERFECT)
- Appropriateness:  78.7% (improvement area)
- Conventions:      99.7% (EXCELLENT)
- Reasonableness:   92.1% (GOOD)
- Game/Slam:        24.7% (needs work)
```

### Play Quality (Level 8 Minimax)

```
Composite: 70-80% (Grade B)
- Legality: 100%
- Contract Success: 70-80%
```

---

## Key Development Patterns

### Branch Strategy

- **development** - Active development (current working branch)
- **main** - Production (triggers Render deployment)
- Always commit to `development` unless deploying

### Testing Commands

```bash
# Quick (30 sec) - during development
./backend/test_quick.sh

# Medium (2 min) - before commit
./backend/test_medium.sh

# Full (5+ min) - before push
./backend/test_full.sh

# E2E tests
cd frontend && npm run test:e2e
```

### Quality Score Testing

```bash
# Bidding quality (run before modifying bidding logic)
python3 backend/test_bidding_quality_score.py --hands 500

# Play quality (run before modifying play logic)
python3 backend/test_play_quality_integrated.py --hands 500 --level 8
```

### Error Analysis

```bash
# Check recent errors (ALWAYS do this first when debugging)
python3 backend/analyze_errors.py --recent 10
python3 backend/analyze_errors.py --patterns
```

---

## Architecture Overview

### Backend (Python Flask)

```
backend/
├── server.py                    # Flask REST API
├── engine/
│   ├── bidding_engine.py       # Bidding orchestrator
│   ├── play_engine.py          # Card play orchestrator
│   ├── opening_bids.py         # Opening bid logic
│   ├── responses.py            # Response logic
│   ├── rebids.py               # Rebid logic
│   ├── overcalls.py            # Overcall logic
│   ├── advancer_bids.py        # Advancer logic
│   ├── hand.py                 # Hand class
│   └── ai/
│       ├── decision_engine.py  # State-based routing
│       ├── feature_extractor.py # Auction context extraction
│       ├── sanity_checker.py   # Bid validation
│       ├── validation_pipeline.py # Multi-stage validation
│       └── conventions/        # All convention modules
└── tests/                      # Organized test suite
```

### Frontend (React)

```
frontend/src/
├── App.js                      # Main orchestrator
├── PlayComponents.js           # Card play UI
├── components/
│   ├── auth/SimpleLogin.jsx    # Authentication
│   └── play/ContractHeader.jsx # Contract display
└── contexts/AuthContext.jsx    # Auth state management
```

### Key APIs

| Endpoint | Purpose |
|----------|---------|
| `/api/deal-hands` | Generate random hands |
| `/api/get-next-bid` | AI makes a bid |
| `/api/evaluate-bid` | Evaluate user's bid (0-10 score) |
| `/api/play-card` | Submit card play |
| `/api/get-ai-play` | AI plays a card |
| `/api/analytics/dashboard` | User analytics |

---

## Documentation Structure

```
docs/
├── README.md                   # Documentation index
├── project-overview/           # Core project docs
├── features/                   # Feature documentation
│   ├── bidding/               # Bidding system docs
│   └── play/                  # Play engine docs
├── bug-fixes/                  # Bug fix documentation
│   ├── 2025-10/               # October fixes
│   └── 2025-11/               # November fixes
├── guides/                     # User and dev guides
│   ├── testing/               # Testing guides
│   └── deployment/            # Deployment guides
├── architecture/               # Architecture docs
│   └── decisions/             # ADRs
└── project-status/             # Status reports
```

---

## Immediate Next Steps (Suggested)

### High Priority

1. **Monitor and investigate** the First Hand After Server Startup bug
2. **Improve bid appropriateness score** (currently 78.7%)
3. **Enhance Game/Slam bidding** (currently 24.7%)

### Medium Priority

1. Add remaining convention edge cases
2. Improve card play AI (minimax depth optimization)
3. Add play analysis feedback

### Low Priority

1. Card play UI enhancements (animations, history)
2. Advanced conventions (Gambling 3NT, etc.)
3. Sound effects and polish

---

## Important Reminders

### Before Making Changes

1. **Read CLAUDE.md** - Main project instructions
2. **Check error logs first** when debugging
3. **Run quality scores** before modifying bidding/play logic
4. **Use TodoWrite** to track tasks

### Before Committing

1. Run tests: `./test_all.sh`
2. Update documentation
3. Keep docs in same commit as code
4. Follow filesystem guidelines (no new root MD files)

### Production Deployment

1. Migrate database first: `python3 backend/database/init_all_tables.py`
2. Merge to main: `git checkout main && git merge development`
3. Push: `git push origin main` (auto-deploys to Render)
4. Verify: Dashboard loads, bidding works, DDS available

---

## Files to Read First

1. **[CLAUDE.md](../CLAUDE.md)** - Comprehensive project instructions
2. **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** - Development context and practices
3. **[docs/README.md](../docs/README.md)** - Documentation navigation
4. **[docs/bug-fixes/RESIDUAL_ISSUES.md](../docs/bug-fixes/RESIDUAL_ISSUES.md)** - Known issues

---

## Contact & Resources

- **Production URL**: Deployed on Render (auto-deploys from main)
- **Repository**: Local development on `development` branch
- **Issue Tracking**: Bug fixes documented in `docs/bug-fixes/`

---

---

## User Working Style Profile

### Communication Preferences

| Aspect | Preference |
|--------|------------|
| Detail level | Concise summaries with tables; deep dives on request |
| Decision making | Present options, let user choose |
| Proactivity | Appreciate initiative but want to approve major changes |
| Questions | Direct, practical - wants actionable answers |

### Development Approach

1. **Quality-focused** - Runs tests, checks baselines, cares about regressions
2. **Documentation matters** - Has invested heavily in organized docs
3. **Iterative** - Prefers working in sessions, checking progress, adjusting
4. **Pragmatic** - Willing to defer low-priority items, focus on what matters

### What User Expects from Claude Code

- **Don't over-engineer** - Solve the problem at hand, not hypothetical future ones
- **Be honest about issues** - Tell when something is broken or risky
- **Maintain the codebase** - Respect existing patterns and organization
- **Track work** - Use todos, document completions

### Notable Preferences

- Uses **bridge terminology correctly** - expect Claude to understand SAYC
- Cares about **production stability** - cautious about deployments
- Values **clean filesystem** - just did major cleanup, don't re-clutter
- Hands-on but **delegates implementation** - user steers, Claude builds

---

*This document provides continuity context for Claude Code upgrades. Update this file when major work is completed or new work-in-progress items emerge.*
