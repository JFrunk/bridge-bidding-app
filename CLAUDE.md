# CLAUDE.md

**Last Updated:** 2026-03-02

This file provides guidance to Claude Code when working with this repository. Detailed reference guides are in `.claude/` and loaded on-demand.

## Project Overview

**Bridge Bidding Training Application** — teaches SAYC bidding system with AI opponents, real-time feedback, and analytics.

**Stack:** Python Flask (port 5001) + React (port 3000) + PostgreSQL
**Production:** https://app.mybridgebuddy.com (Hetzner Cloud 178.156.132.108)
**Landing:** https://mybridgebuddy.com (GitHub Pages)
**Deploy:** `ssh hetzner-bridge "bash /opt/bridge-bidding-app/update.sh"`
**Branches:** `development` (active work) / `main` (production)

---

## Conversation & Task Management Standards

**MANDATORY: Always use TodoWrite for multi-step tasks.**

- Create todo list at task start, not after
- Mark items in_progress BEFORE starting work
- Mark items complete IMMEDIATELY when done
- When user adds mid-task instructions: ADD to existing list, don't replace
- NEVER lose track of original tasks when new ones arrive
- NEVER have more than one item in_progress at a time

---

## Code Reuse — Never Recreate

**Before writing ANY new function, utility, or logic, verify it doesn't already exist.**

**Search protocol:**
1. Search for function/variable names related to what you're building
2. Check utility directories: `frontend/src/utils/`, `backend/utils/`, `frontend/src/hooks/`, `frontend/src/contexts/`, `backend/engine/`
3. Read related files completely before deciding to create something new

**Rules:**
- ALWAYS search before writing — no exceptions
- Import and reuse existing utilities (seats.js, etc.)
- Extend existing functions rather than creating parallel ones
- NEVER duplicate state management, calculations, or display logic

**Bad examples:** Creating `getBiddingHistory()` when `auction` state exists. Writing inline seat math when `utils/seats.js` has `partner()`, `lho()`, `rho()`. Duplicating HCP calculation when `Hand` class computes it.

---

## Development Commands

### Quick Reference
```bash
# Backend
cd backend && source venv/bin/activate && python server.py    # Start server (port 5001)
./test_quick.sh      # 30s — unit tests
./test_medium.sh     # 2min — unit + integration
./test_full.sh       # 5min — all backend tests

# Frontend
cd frontend && npm start     # Dev server (port 3000)
npm test                     # Jest unit tests
npm run build                # Production build
npm run test:e2e:ui          # Interactive E2E debugging (recommended)

# Full app tests
./test_all.sh                # Backend + Frontend + E2E (2-3min)
./test_all.sh --quick        # Unit tests only (30s)
```

### Error Analysis — Check Logs FIRST
```bash
python3 analyze_errors.py --recent 10    # Last 10 errors with details
python3 analyze_errors.py --patterns     # Detect recurring issues
```
Slash command: `/analyze-errors`

**Debugging workflow:** Check error logs first -> If logged, use stack trace -> If not logged, reproduce then check again -> After fix, monitor error hash.

### User Feedback
Feedback is on the **production server**, not local. See `.claude/DEPLOY_GUIDE.md` for retrieval commands.

---

## Quality Assurance

**MANDATORY: Run baseline quality scores before committing changes to bidding or play logic.**

### Triggers — When to Run

| Test | When to Run |
|------|------------|
| Bidding Quality | Before modifying `backend/engine/*.py` or `backend/engine/ai/conventions/*.py` |
| Play Quality | Before modifying `backend/engine/play_engine.py` or `backend/engine/play/ai/*.py` |
| V2 Schema Efficiency | Before modifying `backend/engine/v2/schemas/*.json` or V2 interpreter/extractor |
| SAYC Compliance | Before modifying bidding modules, after SAYC-related fixes |

### Quick Commands
```bash
# Bidding quality (quick / comprehensive)
python3 backend/test_bidding_quality_score.py --hands 100
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_after.json

# Play quality
python3 backend/test_play_quality_integrated.py --hands 100 --level 8

# SAYC compliance
python3 backend/test_sayc_compliance.py --hands 100 --output sayc_quick.json

# Compare baselines
python3 compare_scores.py baseline_before.json baseline_after.json
```

**DDS only works on Linux production servers — crashes on macOS M1/M2. Use Level 8 (Minimax) for development.**

**See:** `.claude/QUALITY_TESTING_GUIDE.md` for detailed protocols, thresholds, and baselines

---

## Systematic Issue Analysis

**MANDATORY: Before implementing any fix, complete this protocol.**

1. **Identify & Search** — After finding root cause, search for similar patterns across the codebase
2. **Document Scope** — Immediate issue, pattern occurrences, actually affected, preventatively fix
3. **Solution Design** — 1 occurrence: fix locally. 2-3: fix all. 4+: create abstraction
4. **Present to User** — Complete analysis before implementing

**See:** `.claude/CODING_GUIDELINES.md` for complete framework and common patterns

---

## Git Workflow

- **`development`** — Active development (default for commits)
- **`main`** — Production (deploy via Hetzner Cloud)
- Always commit to `development` unless deploying
- Database migrations must be applied to BOTH local (`bridge_app`) AND production (`bridge_bidding`)

**See:** `.claude/DEPLOY_GUIDE.md` for deploy procedures, PR creation, database migrations, rollback

---

## Architecture

### Core Flows
```
Bidding: HTTP Request -> server.py -> BiddingEngine -> DecisionEngine -> Specialist Module -> Bid + Explanation
Play:    HTTP Request -> server.py -> PlayEngine -> AI (Simple/Minimax/DDS) -> Card Selection -> Trick Evaluation
```

### Backend Key Components

| Component | File | Purpose |
|-----------|------|---------|
| REST API | `server.py` | Flask endpoints (`/api/deal-hands`, `/api/evaluate-bid`, `/api/play-card`, etc.) |
| Bidding Engine | `engine/bidding_engine.py` | Orchestrator, legality checks, module routing |
| Play Engine | `engine/play_engine.py` | Card play, trick evaluation, contract tracking |
| Decision Engine | `engine/ai/decision_engine.py` | State-based routing to specialist modules |
| Opening Bids | `engine/opening_bids.py` | 1NT, 2C, suit openings |
| Responses | `engine/responses.py` | Responding to partner's opening |
| Rebids | `engine/rebids.py` | Opener's second bid |
| Overcalls | `engine/overcalls.py` | Bidding after opponent opens |
| Conventions | `engine/ai/conventions/` | Stayman, Jacoby, Blackwood, Takeout Doubles, etc. |
| Play AI | `engine/play/ai/` | SimplePlayAI (1-6), MinimaxPlayAI (7-8), DDS (9-10) |
| Hand | `engine/hand.py` | 13-card hand with HCP, distribution, suit analysis |
| Feature Extractor | `engine/ai/feature_extractor.py` | Auction context features |
| Feedback | `engine/feedback/bidding_feedback.py` | Bid evaluation, scoring (0-10), hints |

### Module Interface
```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    # Returns (bid, explanation) or None
```

### Decision Priority
1. Opening situation -> Preempts -> Opening Bids
2. Competitive situation -> Overcalls -> Takeout Doubles -> Advancer
3. Partnership auction -> Conventions -> Natural responses/rebids

**See:** `.claude/ARCHITECTURE_DETAIL.md` for frontend structure, multi-user system, play system, features

---

## Key Bidding Engine Concepts

**Legality Enforcement:** `BiddingEngine._is_bid_legal()` — higher level OR same level + higher suit. Special bids (Pass, X, XX) always legal.

**Appropriateness Validation:** Base convention class checks HCP requirements for level, suit length requirements. Prevents inappropriate but technically legal bids.

---

## Implementation Notes

- **Vulnerability rotation:** None -> NS -> EW -> Both per deal
- **Bid format:** Strings: "1♠", "3NT", "Pass", "X", "XX"
- **Suit ranking:** ♣ < ♦ < ♥ < ♠ < NT
- **Dealer rotation:** Chicago (N -> E -> S -> W), indicator "(D)" in bidding table
- **User position:** Always South
- **AI delay:** 500ms between bids for UX

---

## Seat Position Utilities

**CRITICAL: Use the seats utility module for ALL seat/position calculations.**

Modulo-4 clock: `NORTH=0, EAST=1, SOUTH=2, WEST=3`. Partner=+2, LHO=+1, RHO=+3.

**Backend:** `from utils.seats import partner, lho, rho, relative_position, display_name, bidder_role`
**Frontend:** `import { partner, lho, rho, relativePosition, displayName, bidderRole, nsSuccess } from '../utils/seats'`

**Rules:**
- ALWAYS import from `utils/seats` for seat calculations
- Use integer indices (0-3) in storage/logic, strings ('N','E','S','W') in display
- NEVER hardcode seat relationships or duplicate seat math inline

---

## Common Pitfalls

- **Frontend bid legality:** BiddingBox client-side check must match backend logic
- **Feature extraction:** Specialist modules receive full features dict even if unused
- **Module naming:** Decision engine returns module name as string, not the class
- **Hand generation:** Scenarios consume cards from deck — order matters
- **Auction indexing:** Position = `index % 4` mapping to player positions
- **DDS crashes on macOS:** Use Level 8 (Minimax) for dev, Level 10 (DDS) only on Linux production
- **DDS debugging requires production:** Deploy or SSH to test DDS features — never verify locally
- **Quality score regression:** Always compare before/after scores

---

## Testing Strategy

### Fast Feedback Loop
```bash
./test_quick.sh          # 30s during development
./test_all.sh            # 2-3min before committing
npm run test:e2e:ui      # Interactive E2E debugging
```

### Key Rules
- Add tests for new features, regression tests for bug fixes
- Run quality scores before bidding/play changes
- Use `data-testid` attributes for E2E selectors
- NEVER commit without running tests

**See:** `.claude/QUALITY_TESTING_GUIDE.md` for test organization, quality protocols, and E2E practices

---

## Documentation Standards

**Documentation is NOT optional. All code changes require documentation updates.**

- Update docs inline during implementation, include in same commit
- Features: `docs/features/FEATURE_NAME.md`
- Bug fixes: `docs/bug-fixes/BUG_NAME.md`
- Never create markdown files in the project root — use `docs/` subdirectories

**See:** `.claude/DOCUMENTATION_PRACTICES.md` for complete workflow and checklists

---

## UI/UX Standards

**Read `.claude/UI_STANDARDS.md` before ANY UI work.**

**Binding rules:**
1. **No Tailwind for layout** — Use CSS with `clamp()`, `vmin`, `max-width` media queries
2. **South Hand + Bidding Box are sacrosanct** — Never obscured, `flex-shrink: 0`
3. **Design tokens in index.css only** — All CSS variables in `:root`, no redefinition in components
4. **Desktop-first** responsive with `max-width` queries
5. **Breakpoints:** 1024px, 768px, 600px, 480px, 360px + height 700px

---

## Architectural Decisions

**HIGH-RISK triggers (MUST review before implementing):**
- New directories, new dependencies, cross-module data structure changes
- API contract modifications, new state management patterns
- Database schemas/migrations, build/deployment config changes
- Refactoring code used by 3+ modules

When triggered: PAUSE -> Read `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md` -> Generate alternatives -> Present to user

---

## LLM-First Development

- **Max file size:** 500 lines (warning at 400)
- **Max useState per component:** 15 (group related state in hooks)
- **Search before writing:** Check `utils/`, `hooks/`, `services/` first
- **Consider extraction:** If adding >50 lines, should it be a new file?

---

## Adding New Conventions

1. Create file in `backend/engine/ai/conventions/`
2. Extend `ConventionModule`, implement `evaluate()`
3. Register in `BiddingEngine.modules`
4. Add routing logic to `decision_engine.py`
5. Add tests in `backend/tests/`
6. Run baseline quality score before and after

---

## Additional Resources

- `docs/project-overview/LOCAL_SETUP.md` — Local development setup, PostgreSQL, environment config
- `.claude/DEPLOY_GUIDE.md` — Git workflow, deploy, database, rollback, user feedback
- `.claude/QUALITY_TESTING_GUIDE.md` — QA protocols, baselines, test organization
- `.claude/ARCHITECTURE_DETAIL.md` — Frontend, multi-user, play system, features
- `.claude/CODING_GUIDELINES.md` — Systematic analysis, complete QA protocols
- `.claude/DOCUMENTATION_PRACTICES.md` — Documentation workflow and checklists
- `.claude/UI_STANDARDS.md` — Design tokens, zone architecture, component patterns
- `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md` — ADR process and decision matrix
- `.claude/PROJECT_CONTEXT.md` — Comprehensive project information
- `docs/README.md` — Complete documentation index
