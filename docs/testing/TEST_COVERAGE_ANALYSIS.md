# Test Coverage Analysis

**Date:** 2026-02-05
**Scope:** Full codebase (backend + frontend)

---

## Executive Summary

| Area | Test Files | Test Functions | Coverage Assessment |
|------|-----------|----------------|---------------------|
| Backend | 132 | ~1,572 | Strong on bidding/play logic; weak on infrastructure |
| Frontend Unit | 6 | 92 | Minimal — only utilities and 2 shared components |
| Frontend E2E | 12 | 69 | Good — covers critical user flows |
| **Total** | **150** | **~1,733** | |

The test suite is heavily weighted toward bidding engine logic (conventions, opening bids, responses, rebids) and play AI. There are significant gaps in API endpoint testing, infrastructure modules, frontend component unit tests, and the entire learning/analytics subsystem.

---

## Backend Coverage Map

### Well-Tested Modules (Low Risk)

| Module | Approx Tests | Notes |
|--------|-------------|-------|
| `engine/ai/sanity_checker.py` | 158 | Thorough |
| `engine/play/ai/dds_ai.py` | 152 | Thorough (Linux-only) |
| `engine/ai/auction_context.py` | 113 | Well covered |
| `engine/ai/feature_extractor.py` | 100+ | Core feature extraction |
| `engine/ai/validation_pipeline.py` | 59 | Good |
| `engine/ai/conventions/*.py` | 200+ | Stayman, Jacoby, Blackwood, etc. |
| `engine/opening_bids.py` | 50+ | Core bidding |
| `engine/responses.py` | 50+ | Core bidding |
| `engine/rebids.py` | 50+ | Core bidding |
| `engine/hand.py` | Used everywhere | Implicitly covered |
| `engine/feedback/play_feedback.py` | 38 | Good |
| `engine/play/ai/minimax_ai.py` | 39 | Scattered across files |
| `utils/seats.py` | 52 (frontend) + backend | Well tested |

### Under-Tested Modules (Medium Risk)

| Module | Tests | Gap |
|--------|-------|-----|
| `engine/bidding_engine.py` (578 lines) | ~44 regression | No dedicated unit tests for routing/module selection |
| `engine/play_engine.py` (545 lines) | ~19 scattered | No dedicated unit tests for trick evaluation edge cases |
| `engine/responder_rebids.py` (1,214 lines) | Sparse | Largest bidding module, disproportionately few tests |
| `engine/advancer_bids.py` (566 lines) | Sparse | Limited coverage |
| `engine/balancing.py` (369 lines) | Sparse | Limited coverage |
| `engine/feedback/bidding_feedback.py` (782 lines) | Indirect | Tested via API, not unit-tested directly |
| `engine/ai/bidding_state.py` (780 lines) | ~8 files reference it | Empty dedicated test files |
| `engine/bridge_rules_engine.py` (470 lines) | Empty test file | Scoring logic untested |
| `db.py` (569 lines) | ~10 indirect | No direct database layer tests |

### Untested Modules (High Risk)

| Module | Lines | Risk | Why It Matters |
|--------|-------|------|---------------|
| **`server.py`** (API endpoints) | 5,213 | **CRITICAL** | No systematic endpoint tests; only regression tests hit specific routes |
| **`engine/learning/analytics_api.py`** | 4,174 | **CRITICAL** | Dashboard depends on it; zero tests |
| **`engine/learning/learning_path_api.py`** | 1,795 | HIGH | Skill tree progression untested |
| **`engine/learning/mistake_analyzer.py`** | 688 | HIGH | Error pattern detection untested |
| **`engine/learning/error_categorizer.py`** | 363 | HIGH | Mistake classification untested |
| **`engine/learning/skill_tree.py`** | 764 | HIGH | Progression system untested |
| **`engine/learning/play_skill_tree.py`** | 859 | HIGH | Play progression untested |
| **`engine/learning/skill_hand_generators.py`** | 2,054 | HIGH | Practice hand generation untested |
| **`engine/learning/play_skill_hand_generators.py`** | 980 | HIGH | Play practice hands untested |
| **`engine/learning/user_manager.py`** | 565 | HIGH | User progress tracking untested |
| **`engine/learning/celebration_manager.py`** | 563 | MEDIUM | Achievement system untested |
| **`engine/auth/simple_auth_api.py`** | 256 | **CRITICAL** | Auth system has zero dedicated tests |
| **`engine/analysis/analysis_engine.py`** | 1,196 | MEDIUM | Post-game analysis untested |
| **`engine/analysis/decay_curve.py`** | 648 | MEDIUM | Performance curves untested |
| **`engine/imports/acbl_import_api.py`** | 1,123 | MEDIUM | ACBL import untested |
| **`engine/imports/acbl_audit_service.py`** | 651 | MEDIUM | ACBL validation untested |
| **`engine/notifications/email_service.py`** | 610 | MEDIUM | Email system untested |
| **`engine/v2/interpreters/schema_interpreter.py`** | 1,098 | MEDIUM | V2 schema interpretation untested |
| **`engine/v2/inference/conflict_resolver.py`** | 223 | MEDIUM | Rule conflict resolution untested |
| **`engine/feedback/heuristic_backfill_adapter.py`** | 647 | MEDIUM | Feedback fallback untested |
| **`core/session_state.py`** | 324 | MEDIUM | Per-session state isolation untested |
| **`database/init_all_tables.py`** | 201 | LOW | Schema creation untested |

**Total untested code: ~18,000+ lines across 22 modules.**

The entire `engine/learning/` subsystem (10 modules, ~14,900 lines) has zero test coverage.

---

## Frontend Coverage Map

### Unit Tests (6 files, 92 test cases)

| Test File | Cases | What It Tests |
|-----------|-------|---------------|
| `seats.test.js` | 52 | Seat position utility functions |
| `cardUtils.test.js` | 16 | Card sorting, parsing, formatting |
| `Card.test.js` | 9 | Shared Card component rendering |
| `HandAnalysis.test.js` | 7 | Hand analysis display component |
| `PlayComponents.test.js` | 5 | Hand visibility logic during play |
| `App.test.js` | 3 | Basic smoke test |

### E2E Tests (12 files, 69 test cases)

| Test File | Cases | Coverage |
|-----------|-------|----------|
| `7-card-play-basic.spec.js` | 12 | Play phase, tricks, legality |
| `8-differential-feedback.spec.js` | 8 | Feedback panel, ratings |
| `1-authentication.spec.js` | 7 | Login flows |
| `3-bidding-feedback.spec.js` | 7 | Bidding box, feedback |
| `2-complete-game-flow.spec.js` | 5 | Full game cycle |
| `4-dashboard-analytics.spec.js` | 5 | Dashboard stats |
| `5-multi-user-isolation.spec.js` | 5 | User data isolation |
| `9-play-feedback-review.spec.js` | 5 | Play review modal |
| `app-smoke-test.spec.js` | 5 | Basic app load |
| `card-highlight-bug-regression.spec.js` | 4 | Card highlight regression |
| `6-bid-display-timing.spec.js` | 3 | AI bid timing |
| `verification.spec.js` | 3 | Environment check |

### Untested Frontend Modules (78 source files without unit tests)

**Critical gaps (core interactive components):**
- `BiddingBox.jsx` — Core bidding interface with client-side legality checks
- `BiddingTable.jsx` — Auction display
- `PlayableCard.jsx` — Card play interaction
- `CurrentTrickDisplay.jsx` — Trick visualization
- `ContractGoalTracker.js` — Contract progress tracking

**State management and services (zero unit tests):**
- `AuthContext.jsx` — Authentication state provider
- `UserContext.js` — User state provider
- `api.js` — Backend API client (error handling, retries)
- `analyticsService.js` — Analytics calculations
- `learningService.js` — Learning system integration
- `SessionService.js` — Session management

**Complex business components:**
- `LearningDashboard.js` — Analytics modal with 7 statistics cards
- `BiddingGapAnalysis.js` — Bidding analysis
- `DifferentialAnalysisPanel.jsx` — Differential feedback
- `BiddingWorkspace.jsx` — Bidding phase orchestration
- `PlayWorkspace.jsx` — Play phase orchestration
- `PlayIntegration.js` — Play integration layer

**Auth/navigation:**
- `SimpleLogin.jsx` — Login UI
- `TopNavigation.jsx` — Navigation bar
- `WelcomeWizard.jsx` — Onboarding flow

---

## Recommended Improvements (Prioritized)

### Priority 1: Critical Infrastructure Tests

These modules handle authentication, data persistence, and API contracts. Failures here affect every user.

#### 1A. API Endpoint Tests for `server.py`

**Why:** The 5,213-line server has no systematic endpoint tests. Regressions in request/response contracts go undetected until production.

**What to test:**
- Each `/api/*` endpoint: valid requests, error responses, edge cases
- Request validation (missing fields, wrong types)
- Authentication enforcement (endpoints that require `user_id`)
- Error responses return correct HTTP status codes
- Game state transitions (deal → bid → play → score)

**Approach:** Create `backend/tests/integration/test_api_endpoints.py` using Flask's test client.

#### 1B. Authentication Tests for `simple_auth_api.py`

**Why:** Zero dedicated tests for the auth system that gates user data isolation.

**What to test:**
- Login with email creates new user on first login
- Login with phone creates new user on first login
- Repeat login returns same user
- Guest mode works
- Invalid input handling
- User ID consistency across sessions

#### 1C. Analytics API Tests for `analytics_api.py`

**Why:** The 4,174-line analytics module powers the dashboard with zero test coverage.

**What to test:**
- Dashboard data aggregation accuracy
- User data isolation (user A cannot see user B's stats)
- Empty state handling (new user with no data)
- Score calculations and percentages
- Date range filtering

### Priority 2: Learning Subsystem Tests

The entire `engine/learning/` directory (10 modules, ~14,900 lines) is untested. This is the largest block of untested code.

#### 2A. `learning_path_api.py` and `skill_tree.py`

**What to test:**
- Skill progression calculations
- Prerequisite dependency validation
- Convention mastery level transitions
- Practice recommendation logic

#### 2B. `mistake_analyzer.py` and `error_categorizer.py`

**What to test:**
- Mistake detection accuracy against known bid/play errors
- Error categorization correctness
- Pattern recognition for repeated mistakes

#### 2C. `skill_hand_generators.py` and `play_skill_hand_generators.py`

**What to test:**
- Generated hands meet specified constraints
- Difficulty scaling produces appropriate hands
- Edge cases (very narrow constraints)

### Priority 3: Frontend Unit Tests for Core Components

The frontend has only 6 unit test files covering utilities, while 78 source files (including all interactive components) lack unit tests. E2E tests cover some of this, but are slow and fragile.

#### 3A. `BiddingBox.jsx` Unit Tests

**Why:** Core bidding interface with client-side legality checking that must match backend logic.

**What to test:**
- Legal bid filtering (only valid bids shown)
- Bid level progression
- Pass/Double/Redouble availability
- Bid submission callback with correct data

#### 3B. `api.js` Service Tests

**Why:** All backend communication flows through this module with no test coverage.

**What to test:**
- API call formatting
- Error handling and retry logic
- Response parsing
- Network failure behavior

#### 3C. `AuthContext.jsx` Tests

**Why:** Authentication state affects every component in the app.

**What to test:**
- Login/logout state transitions
- Persistent login (localStorage)
- Guest mode handling
- User ID propagation to child components

#### 3D. `PlayableCard.jsx` and Play Component Tests

**Why:** Card play interaction is the most complex UI in the app.

**What to test:**
- Card selectability based on turn and legality
- Follow-suit enforcement
- Card submission
- Dummy hand interaction restrictions

### Priority 4: Bidding Engine Gaps

#### 4A. `responder_rebids.py` (1,214 lines)

**Why:** The largest bidding module has disproportionately few tests relative to its complexity.

**What to test:**
- All decision branches (invitational vs game-forcing sequences)
- Partnership inference from prior bids
- Edge cases around borderline hands

#### 4B. `bidding_engine.py` — Module Selection Tests

**Why:** The routing logic that selects which specialist module to use has no dedicated tests.

**What to test:**
- Correct module selection for each auction context
- Priority ordering (conventions checked before natural bidding)
- Fallback behavior when no module matches

#### 4C. `bridge_rules_engine.py` — Scoring Tests

**Why:** Scoring logic (470 lines) has an empty test file.

**What to test:**
- Contract scoring (making, going down)
- Vulnerability impact on scores
- Doubled/redoubled scoring
- Slam bonuses
- Overtrick/undertrick calculations

### Priority 5: Database and Session Layer

#### 5A. `db.py` Direct Tests

**What to test:**
- Connection management
- SQLite placeholder handling
- Query execution edge cases (empty results, large datasets)

#### 5B. `core/session_state.py` Tests

**What to test:**
- Per-session isolation (concurrent sessions don't interfere)
- Default state initialization
- State cleanup

### Priority 6: Empty Test File Cleanup

There are approximately 60 test files that exist as empty shells (have file structure but zero or near-zero test functions). These include:

- **22 regression test files** — Created for specific bugs but never populated
- **30 unit test files** — Placeholder files for modules that need coverage
- **10 ACBL/SAYC compliance files** — Framework exists but no tests written
- **5 SAYC baseline files** — All empty

**Recommendation:** Either populate these with real tests or remove them to avoid false sense of coverage. A script could flag test files with zero `def test_` functions in CI.

---

## Structural Observations

### Strengths

1. **Convention testing is thorough** — Stayman, Jacoby, Blackwood, Takeout Doubles, etc. all have dedicated tests
2. **Regression tests exist for many bugs** — Good practice of creating test files for bug fixes
3. **E2E tests cover critical user flows** — Authentication, bidding, play, dashboard, multi-user isolation
4. **Quality score testing** — Baseline quality tests for bidding and play exist (though they're benchmarks, not unit tests)
5. **Seat utility tests** — 52 frontend tests + backend tests for this critical module

### Weaknesses

1. **No API contract tests** — The 5,213-line server.py has no systematic endpoint tests
2. **Learning subsystem entirely untested** — 14,900 lines of zero coverage
3. **Frontend unit tests are minimal** — 92 tests for 84 source files; only utilities have coverage
4. **Empty test files inflate perceived coverage** — ~60 files with zero test functions
5. **No database layer tests** — Schema creation, queries, and data integrity are untested
6. **Test organization is inconsistent** — Tests in root, tests/, and within engine/ directories

---

## Quick Wins

These are high-impact, low-effort improvements:

1. **Add Flask test client tests for top 5 API endpoints** — `/api/deal-hands`, `/api/get-next-bid`, `/api/evaluate-bid`, `/api/play-card`, `/api/analytics/dashboard`
2. **Add auth tests** — Login creates user, repeat login returns same user, guest mode works
3. **Add `bridge_rules_engine.py` scoring tests** — Known inputs/outputs, easy to write
4. **Add `BiddingBox.jsx` unit tests** — Test bid legality filtering with mock data
5. **CI check for empty test files** — Flag test files with zero test functions
