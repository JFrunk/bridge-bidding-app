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
- Only one TodoWrite item should be in_progress at a time in the main conversation
- This does NOT restrict launching parallel Agent subagents for independent subtasks
- When delegating to parallel agents, mark the parent task as in_progress and track subtasks through agent results

---

## Proactive Commit Discipline

**CC is responsible for suggesting commits — the user should not have to remember.**

- After completing any logical unit of work (bug fix, feature, refactor), proactively ask the user: "This looks like a good commit point. Want me to run `/smart-commit`?"
- A "logical unit" means: the task from the todo list is marked complete, tests pass, or the user's request has been fulfilled
- If the Stop hook reports uncommitted changes accumulating, act on it — don't ignore the signal
- When the user says yes, invoke `/smart-commit` which handles diff review, quality gates, and committing
- Never let more than one logical unit of work accumulate uncommitted
- For docs-only or config-only changes, a lightweight commit is fine (no quality gates needed)

---

## Skill-First Workflow

**When a task maps to an existing slash command, invoke the skill instead of doing the work manually.**

Before starting any task, check if a matching skill exists. If it does, use the Skill tool to invoke it. Do not replicate what a skill already automates.

| Task | Invoke |
|------|--------|
| Debugging a bug | `/debug-systematic` |
| Fixing a bug with tests | `/fix-with-tests` |
| Checking for similar patterns | `/check-scope` |
| Committing changes | `/smart-commit` |
| Capturing quality baselines | `/quality-baseline` |
| Comparing quality scores | `/compare-quality` |
| Adding a new convention | `/add-convention` |
| Reviewing user feedback | `/fetch-feedback` |
| Checking production server | `/production-health` |
| Choosing which specialist to use | `/suggest-specialist` |
| Planning a feature | `/plan-feature` |
| Starting TDD feature | `/start-tdd-feature` |
| Reviewing code quality | `/review-code` |
| Running tests | `/test` or `/quick-test` |
| Triaging multiple issues | `/triage-issues` |
| Analyzing error logs | `/analyze-errors` |
| Analyzing a specific hand | `/analyze-hand` |
| Pre-commit validation | `/preflight` |
| Deploying to production | `/deploy-production` |
| Partner practice dev/debug | `/partner` |

---

## Code Reuse — Never Recreate

**Before writing ANY new function, utility, or logic, verify it doesn't already exist.**

**Search protocol:**
1. **Check `.claude/UTILITY_REGISTRY.md` first** — it lists every shared utility and their banned inline patterns
2. Search for function/variable names related to what you're building
3. Check utility directories: `frontend/src/utils/`, `backend/utils/`, `frontend/src/hooks/`, `frontend/src/contexts/`, `backend/engine/`
4. Read related files completely before deciding to create something new

**Rules:**
- ALWAYS search before writing — no exceptions
- Import and reuse registered utilities — see `.claude/UTILITY_REGISTRY.md`
- Extend existing utilities rather than creating parallel implementations
- NEVER duplicate state management, calculations, or display logic
- When a new utility is created, register it in `.claude/UTILITY_REGISTRY.md`

**Bad examples:** Creating `getBiddingHistory()` when `auction` state exists. Writing inline seat math when `utils/seats.js` has `partner()`, `lho()`, `rho()`. Duplicating HCP calculation when `Hand` class computes it. Defining `{'S':'♠','H':'♥',...}` when `SUIT_MAP` is exported from `suitColors.js`.

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

**Use `/smart-commit` to automatically detect which quality gates to run based on changed files.**

| Slash Command | When to Use |
|---------------|-------------|
| `/quality-baseline` | Capture baseline scores before starting work |
| `/compare-quality` | Compare before/after scores to detect regressions |
| `/smart-commit` | Auto-detect changed domains, run relevant gates, then commit |

**DDS only works on Linux production servers — crashes on macOS M1/M2. Use Level 8 (Minimax) for development.**

**See:** `.claude/QUALITY_TESTING_GUIDE.md` for detailed protocols, thresholds, and baselines

---

## Systematic Issue Analysis

**MANDATORY: Before implementing any fix, complete systematic analysis.**

| Slash Command | When to Use |
|---------------|-------------|
| `/debug-systematic` | Full 4-step debugging protocol (identify, search, scope, present) |
| `/check-scope` | Search for similar patterns after finding root cause |
| `/fix-with-tests` | TDD workflow: regression test first, then implement fix |

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

## Shared Utilities Registry

**CRITICAL: Before writing ANY logic that touches seats, suits, cards, errors, or sessions — check `.claude/UTILITY_REGISTRY.md` and import from the canonical utility.**

**MANDATORY: Read `.claude/UTILITY_REGISTRY.md` before implementing any feature.** It contains:
- The complete list of shared utilities, what they export, and their import paths
- Banned inline patterns with the correct replacement for each
- Known tech debt (what NOT to extend)
- Instructions for registering new utilities

**Quick reference — which utility to use:**

| Domain | Backend | Frontend |
|--------|---------|----------|
| Seat positions, turns, partnerships | `utils.seats` | `utils/seats` |
| Suit symbols, colors, bid formatting | — | `utils/suitColors` |
| Card sorting, grouping, contracts | — | `shared/utils/cardUtils` |
| Error logging & exception handling | `utils.error_logger` | — |
| Session IDs & API headers | — | `utils/sessionHelper` |

**Rules (apply to ALL registered utilities):**
- ALWAYS import from the canonical utility — never duplicate its logic inline
- If a utility is missing a function you need, **extend the utility** — don't create a parallel implementation
- When adding a new shared utility, register it in `.claude/UTILITY_REGISTRY.md`
- Self-check before committing: search changed files for banned patterns listed in the registry

**See:** `.claude/UTILITY_REGISTRY.md` for complete import paths, banned patterns, and tech debt

---

## Common Pitfalls

- **Inline utility duplication:** The most common violation. ALWAYS check the Shared Utilities Registry above before writing inline seat math, suit maps, card sorting, error handling, or session management
- **Frontend bid legality:** BiddingBox client-side check must match backend logic
- **Feature extraction:** Specialist modules receive full features dict even if unused
- **Module naming:** Decision engine returns module name as string, not the class
- **Hand generation:** Scenarios consume cards from deck — order matters
- **Auction indexing:** Use `active_seat_bidding(dealer, bid_count)` — never `(idx + count) % 4`
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

Use `/add-convention` to scaffold the full 6-step integration process (create file, register, route, test, baseline).

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
- `.claude/UTILITY_REGISTRY.md` — **Shared utility registry, banned patterns, and tech debt tracking**
- `.claude/PROJECT_CONTEXT.md` — Comprehensive project information
- `docs/README.md` — Complete documentation index
