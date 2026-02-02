# CLAUDE.md

**Last Updated:** 2026-01-05

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Bridge Bidding Training Application** that teaches players the Standard American Yellow Card (SAYC) bidding system. The app features a complete bidding and card play system with AI opponents, real-time feedback, multi-user support, and comprehensive analytics.

**Stack:**
- **Backend**: Python Flask server (port 5001) with bidding engine and play engine
- **Frontend**: React app (port 3000)
- **Database**: SQLite (bridge.db)
- **Architecture**: Client-server with REST API communication

**Production URLs:**
- **Landing Page:** https://mybridgebuddy.com (GitHub Pages)
- **Application:** https://app.mybridgebuddy.com (Oracle Cloud)

**Hosting Architecture:**
| Domain | Host | Purpose |
|--------|------|---------|
| mybridgebuddy.com | GitHub Pages | Landing page |
| www.mybridgebuddy.com | GitHub Pages | Landing page |
| app.mybridgebuddy.com | Oracle Cloud (161.153.7.196) | Bridge app |

**Deployment:**
- **App:** `ssh oracle-bridge "bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh update"`
- **Landing page:** Push to GitHub Pages repo (auto-deploys)
- **SSH config:** `~/.ssh/config` has alias `oracle-bridge` → 161.153.7.196

---

## Conversation & Task Management Standards

### ⚠️ MANDATORY: Always Use Todo Lists for Multi-Step Tasks

**To prevent task loss when the user adds instructions mid-conversation, ALWAYS use the TodoWrite tool proactively.**

**When to Create a Todo List:**
- Any task with 2+ steps
- When starting work on a user request
- Immediately when receiving multiple instructions

**When User Adds Mid-Task Instructions:**
1. **DO NOT** treat new instructions as replacing current work
2. **ADD** the new instruction to the existing todo list
3. **CONTINUE** with all tasks (original + new)
4. **CONFIRM** by showing the updated todo list

**Example Workflow:**
```
User: "Fix the login bug and update the tests"
Claude: *creates todo list:*
   ☐ Fix login bug
   ☐ Update tests
Claude: *marks "Fix login bug" as in_progress*

User: "Also add error logging"
Claude: *adds to todo list:*
   🔄 Fix login bug (in progress)
   ☐ Update tests
   ☐ Add error logging    ← new item captured
Claude: *completes all three tasks*
```

**Key Rules:**
- ✅ Create todo list at task start (not after)
- ✅ Mark items in_progress BEFORE starting work
- ✅ Mark items complete IMMEDIATELY when done
- ✅ Add new user instructions to the list (don't replace)
- ✅ Show updated list when adding items mid-task
- ❌ NEVER lose track of original tasks when new ones arrive
- ❌ NEVER have more than one item in_progress at a time

---

## Development Commands

### Backend (Python/Flask)
```bash
# From backend/ directory
python3 -m venv venv              # Create virtual environment (first time)
source venv/bin/activate          # Activate virtual environment
pip install -r requirements.txt   # Install dependencies

# Run server
python server.py                  # Starts Flask server on http://localhost:5001

# Run tests
./test_quick.sh      # 30 seconds - unit tests only
./test_medium.sh     # 2 minutes - unit + integration
./test_full.sh       # 5+ minutes - all tests
pytest -v            # Verbose output
```

### Frontend (React)
```bash
# From frontend/ directory
npm install                       # Install dependencies
npm start                         # Start dev server on http://localhost:3000
npm test                          # Run unit tests (Jest)
npm run build                     # Production build

# E2E tests (Playwright)
npm run test:e2e                  # Run all E2E tests (headless)
npm run test:e2e:ui               # Interactive debugging (recommended for development)
npm run test:e2e:headed           # Watch tests run in browser
npm run test:e2e:report           # View last test report (HTML)
npm run test:e2e:codegen          # Record actions → auto-generate test code
```

### Running the Full App
1. Start backend: `cd backend && source venv/bin/activate && python server.py`
2. Start frontend: `cd frontend && npm start`
3. Access at http://localhost:3000

### Running All Tests (Comprehensive)
```bash
# From project root
./test_all.sh                     # Runs backend + frontend + E2E (2-3 minutes)
./test_all.sh --quick             # Runs unit tests only (30 seconds)
./test_all.sh --skip-e2e          # Skips E2E tests (1 minute)
```

### Error Analysis (Automated Bug Detection)

**⚠️ ALWAYS check error logs FIRST when investigating bugs**

```bash
# From backend/ directory
python3 analyze_errors.py         # Summary of all errors
python3 analyze_errors.py --recent 10      # Last 10 errors with details
python3 analyze_errors.py --patterns       # Detect recurring issues
python3 analyze_errors.py --category bidding_logic  # Filter by category
```

**Slash command:** `/analyze-errors` - Quick error analysis workflow

**When to Use:**
- **FIRST STEP** when investigating any bug report
- Daily health check for new errors
- After making changes to bidding/play logic
- When debugging user-reported issues
- To find recurring problems
- Before starting manual debugging

**Why Check Error Logs First:**
- ✅ Instant stack traces (no manual debugging needed)
- ✅ Full context captured (auction state, hand data, user session)
- ✅ Error patterns detected (recurring vs one-off issues)
- ✅ Error hashes for tracking (verify fixes work)
- ✅ Timestamps (know when bug started)

**Debugging Workflow:**
1. **Check error logs** - Run `python3 analyze_errors.py --recent 10`
2. **If logged:** Use stack trace and context to implement fix
3. **If not logged:** Reproduce bug, then check logs again (may appear during reproduction)
4. **After fix:** Monitor error hash to verify bug stays fixed

**See:** [docs/features/ERROR_LOGGING_QUICKSTART.md](docs/features/ERROR_LOGGING_QUICKSTART.md), [docs/features/ERROR_LOGGING_SYSTEM.md](docs/features/ERROR_LOGGING_SYSTEM.md)

### User Feedback (Production)

**⚠️ IMPORTANT: When asked to review user feedback, check the PRODUCTION server — feedback is NOT stored locally.**

User feedback submitted via the in-app feedback button is saved as JSON files on the Oracle Cloud production server.

**Location:** `/opt/bridge-bidding-app/backend/user_feedback/` on the production server (accessible via `ssh oracle-bridge`)

**How to retrieve user feedback:**
```bash
# List recent feedback files (most recent first)
ssh oracle-bridge "ls -t /opt/bridge-bidding-app/backend/user_feedback/feedback_*.json 2>/dev/null | head -15"

# Read a specific feedback file
ssh oracle-bridge "cat /opt/bridge-bidding-app/backend/user_feedback/feedback_freeplay_YYYY-MM-DD_HH-MM-SS.json"

# Read ALL recent feedback content (last 3 days)
ssh oracle-bridge "find /opt/bridge-bidding-app/backend/user_feedback/ -mtime -3 -name '*.json' -exec cat {} \;"

# Read ALL recent feedback content (last 7 days)
ssh oracle-bridge "find /opt/bridge-bidding-app/backend/user_feedback/ -mtime -7 -name '*.json' -exec cat {} \;"
```

**Feedback File Naming Convention:**
- `feedback_freeplay_YYYY-MM-DD_HH-MM-SS.json` — General feedback from freeplay mode
- `feedback_YYYY-MM-DD_HH-MM-SS.json` — Feedback with full game context

**Local (dev only):** `backend/user_feedback/` — only captures feedback from local testing, not real users

**Email Notifications:** Feedback also triggers email notifications if configured (see `backend/engine/notifications/email_service.py`)

---

## Quality Assurance Protocols

### ⚠️ MANDATORY: Baseline Quality Score Testing

**ALWAYS run baseline quality score before committing changes to bidding or play logic.**

#### Bidding Quality Score Protocol

**When to Run:**
- Before modifying any bidding module (`backend/engine/*.py`)
- Before changing convention logic (`backend/engine/ai/conventions/*.py`)
- Before updating bid validation or base convention class

**How to Run:**
```bash
# Quick test (5 minutes, 100 hands) - during development
python3 backend/test_bidding_quality_score.py --hands 100

# Comprehensive test (15 minutes, 500 hands) - before commits
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_after.json

# Compare with baseline
python3 compare_scores.py baseline_before.json baseline_after.json
```

**Quality Requirements (BLOCKING):**
- ✅ **Legality: 100%** (no illegal bids allowed)
- ✅ **Appropriateness: ≥ baseline** (no regression)
- ✅ **Composite: ≥ baseline - 2%** (small regression tolerance)

**Target Scores:**
- **Legality: 100%** (must be perfect)
- **Appropriateness: 95%+** (excellent)
- **Conventions: 90%+** (good)
- **Composite: 95%+** (Grade A - production ready)

**Current Baseline (as of 2025-10-28):**
```
Test: 500 hands, 3,013 bids
Composite: 89.7% (Grade C)

Breakdown:
- Legality:        100.0% ✅
- Appropriateness:  78.7% (improvement area)
- Conventions:      99.7% ✅
- Reasonableness:   92.1% ✅
- Game/Slam:        24.7% (needs work)
```

**See:** `.claude/CODING_GUIDELINES.md` (lines 343-665) for complete bidding protocol

#### Play Quality Score Protocol

**When to Run:**
- Before modifying play engine (`backend/engine/play_engine.py`)
- Before changing play AI logic (`backend/engine/play/ai/*.py`)
- Before updating card selection or trick evaluation

**How to Run:**
```bash
# Quick test (10 minutes, 100 hands)
python3 backend/test_play_quality_integrated.py --hands 100 --level 8

# Comprehensive test (30 minutes, 500 hands)
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_after.json

# Compare with baseline
python3 compare_play_scores.py play_baseline_before.json play_after.json
```

**Quality Requirements (BLOCKING):**
- ✅ **Legality: 100%** (no illegal plays allowed)
- ✅ **Success Rate: ≥ baseline - 5%**
- ✅ **Composite: ≥ baseline - 2%**
- ✅ **Timing: < baseline + 50%**

**Target Scores by AI Level:**
- **Level 8 (Minimax):** 80-85% composite (Grade B)
- **Level 10 (DDS):** 90-95% composite (Grade A)

**⚠️ DDS Limitations:**
- DDS only works on Linux production servers
- Crashes on macOS M1/M2 chips
- Use Level 8 (Minimax) for development testing

**See:** `.claude/CODING_GUIDELINES.md` (lines 667-1027) for complete play protocol

#### V2 Schema Engine Bidding Efficiency Test

**When to Run:**
- Before modifying V2 schema rules (`backend/engine/v2/schemas/*.json`)
- Before changing feature extractor (`backend/engine/v2/features/enhanced_extractor.py`)
- Before updating schema interpreter (`backend/engine/v2/interpreters/schema_interpreter.py`)
- After implementing bidding rule fixes

**How to Run:**
```bash
# From backend/ directory
source venv/bin/activate

# Quick test (50 hands, ~2 minutes) - during development
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 50 --seed 42

# Comprehensive test (200 hands, ~5 minutes) - before commits
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 --output efficiency_results.json
```

**What This Test Does:**
1. Generates random hands locally
2. Runs V2 schema bidding engine locally
3. SSHs to production server for DDS (Double Dummy Solver) analysis (Linux only)
4. Computes efficiency gap: `Tricks_Required - DDS_Max_Tricks`
5. Generates rule falsification reports showing which rules cause overbids
6. Creates visualization charts (`bidding_efficiency.png`)

**Key Metrics:**
- **Accuracy Rate (Gap=0):** Percentage of contracts at exactly makeable level
- **Overbid Rate (Gap>0):** Percentage of contracts bid too high
- **Mean Gap:** Average tricks overbid (target: < +1.5)
- **Critical Failures (Gap≥3):** Severe overbids needing immediate attention

**Quality Requirements:**
- ✅ **Accuracy: ≥ 25%** (target)
- ✅ **Overbid Rate: < 50%** (target)
- ✅ **Mean Gap: < +1.5 tricks** (target)
- ✅ **Critical Failures: < 40** per 200 hands (target)

**Rule Falsification Audit:**
The test output includes a falsification report showing which specific rules are causing overbids:
```
Rules with Critical Overbids (Gap ≥ 2):
------------------------------------------------------------
Rule ID                               Uses  Fails     Rate  Mean Gap
------------------------------------------------------------
v1_fallback                             68     48    70.6%    +2.72
slam_after_rkcb_5d_hearts                2      2   100.0%    +3.50
```

**⚠️ Note:** This test requires SSH access to the production server for DDS analysis. DDS only works on Linux (crashes on macOS M1/M2).

---

## Systematic Issue Analysis

### ⚠️ MANDATORY: Before implementing any fix, complete systematic analysis

#### 4-Step Protocol

**1. Identify & Search (2 minutes)**

After finding root cause, search for similar patterns:
```bash
# Example: If issue involves useEffect + data fetching
grep -r "useEffect" --include="*.js" --include="*.jsx" frontend/src/
grep -r "modal.*useState" --include="*.js*" frontend/src/
```

**Questions:**
- Does this pattern appear in other components?
- Are there similar hooks/lifecycle patterns?
- Do other features use the same approach?

**2. Document Scope (1 minute)**
- **Immediate issue:** [component/feature affected]
- **Pattern found in:** [list all similar occurrences]
- **Actually affected:** [which ones exhibit the bug]
- **Preventatively fix:** [which ones could have bug later]

**3. Solution Design (1 minute)**
- **1 occurrence:** Fix locally
- **2-3 occurrences:** Fix all instances, consider shared utility
- **4+ occurrences:** Create abstraction (hook/service), fix architecturally

**4. Present to User**

Present complete analysis before implementing:
```
## Systematic Analysis Complete

**Reported:** [user's description]
**Root Cause:** [technical cause]
**Scope:** Found in [N] components

**All Affected:**
1. ComponentA - [status]
2. ComponentB - [status]

**Solution:** [approach that fixes all instances]

Proceed with implementation?
```

**See:** `.claude/CODING_GUIDELINES.md` for complete systematic analysis framework and common patterns

---

## Git Workflow

### Branch Strategy

This project uses a **two-branch workflow**:
- **`development`** - Active development branch (default for commits)
- **`main`** - Production branch (deploy via Oracle Cloud)

### Standard Workflow (Development Branch)

**Use this for regular development work:**

```bash
# Ensure you're on development branch
git checkout development

# Make changes, test locally, then commit
git add .
git commit -m "Descriptive commit message"

# Push to GitHub
git push origin development
```

### Deploying to Production

**Production Infrastructure:**
| Component | Host | URL |
|-----------|------|-----|
| Landing page | GitHub Pages | https://mybridgebuddy.com |
| Bridge app | Oracle Cloud (161.153.7.196) | https://app.mybridgebuddy.com |

**Oracle Cloud Server:**
- **IP Address:** 161.153.7.196
- **SSH Host Alias:** oracle-bridge (configured in ~/.ssh/config)

**⚠️ CRITICAL: Database migration must run BEFORE deploying code**

**Step 1: Database Migration (Production)**
```bash
# SSH to Oracle Cloud server (use alias)
ssh oracle-bridge
cd /opt/bridge-bidding-app/backend
source venv/bin/activate
python3 database/init_all_tables.py

# Verify tables exist
sqlite3 bridge.db "SELECT name FROM sqlite_master WHERE type='table';"
```

**Expected tables:** users, bidding_decisions, hand_analyses, game_sessions, session_hands

**Step 2: Code Deployment**
```bash
# Switch to main branch
git checkout main

# Merge development changes
git merge development

# Push to GitHub
git push origin main

# Deploy to Oracle via SSH
ssh oracle-bridge "bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh update"

# Switch back to development for continued work
git checkout development
```

**One-liner for quick deploy (after pushing to main):**
```bash
ssh oracle-bridge "cd /opt/bridge-bidding-app && git pull origin main && bash deploy/oracle/maintenance.sh restart"
```

**Step 3: Verification**
- [ ] Dashboard loads without errors
- [ ] Database tables exist
- [ ] Users can login and play
- [ ] Bidding feedback works
- [ ] Dashboard shows statistics

### Rollback Procedure

If deployment fails:
```bash
# Revert main branch
git checkout main
git reset --hard HEAD~1
git push origin main --force

# Or restore from previous commit
git revert HEAD
git push origin main
```

### Quick Reference

```bash
# Check which branch you're on
git branch

# Switch branches
git checkout development  # For dev work
git checkout main        # For deployment

# View recent commits
git log --oneline -5

# View status
git status
```

### Important Notes

- **Always commit to `development`** unless deploying
- **Only push to `main`** when ready for public deployment
- **App** is on Oracle Cloud (https://app.mybridgebuddy.com)
- **Landing page** is on GitHub Pages (https://mybridgebuddy.com)
- **Deploy app via SSH:** `ssh oracle-bridge "bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh update"`
- SSH config at `~/.ssh/config` has alias `oracle-bridge` → 161.153.7.196
- Keep `development` as your default working branch

**See:** `deploy/oracle/README.md`, `docs/deployment/ORACLE_CLOUD_MIGRATION.md`

---

## Architecture

### Backend Structure

The backend implements a **modular AI bidding engine and play engine** with state-based decision systems.

#### Core Bidding Flow
```
HTTP Request → server.py → BiddingEngine → DecisionEngine → Specialist Module → Bid + Explanation
```

#### Core Play Flow
```
HTTP Request → server.py → PlayEngine → AI (Simple/Minimax/DDS) → Card Selection → Trick Evaluation
```

#### Key Components

**1. server.py** - Flask REST API with endpoints:
- `/api/deal-hands` - Generates random hands
- `/api/scenarios` - Lists predefined scenarios
- `/api/load-scenario` - Loads scenario from scenarios.json
- `/api/get-next-bid` - AI makes a bid
- `/api/evaluate-bid` - Evaluates user's bid (with scoring 0-10)
- `/api/get-feedback` - Legacy feedback endpoint
- `/api/play-card` - Submits card play
- `/api/get-ai-play` - AI plays a card
- `/api/analytics/dashboard` - User analytics and statistics
- `/api/auth/simple-login` - Email/phone authentication

**2. engine/bidding_engine.py** - Main bidding orchestrator:
- `BiddingEngine` maintains all specialist modules
- Routes to appropriate module via `select_bidding_module()`
- Performs universal legality checks on AI bids
- Validates bid appropriateness

**3. engine/play_engine.py** - Card play orchestrator:
- Manages complete hand play execution
- Trick evaluation and winner determination
- Contract tracking and scoring
- AI level selection (1-10)

**4. engine/ai/decision_engine.py** - State-based routing logic:
- Determines bidding context (opening, competitive, partnership auction)
- Selects appropriate specialist module based on features
- Priority order: Conventions → Standard bidding modules

**5. Specialist Bidding Modules** (all extend `ConventionModule`):
- **Opening Bids** (`opening_bids.py`): Initial bids (1NT, 2♣, suit openings)
- **Responses** (`responses.py`): Responding to partner's opening
- **Rebids** (`rebids.py`): Opener's second bid
- **Overcalls** (`overcalls.py`): Bidding after opponent opens
- **Advancer Bids** (`advancer_bids.py`): Bidding after partner overcalls

**6. Conventions** (`engine/ai/conventions/`):
- ✅ **Fully Implemented:** Stayman, Jacoby Transfers, Blackwood, Preempts
- ✅ **Fully Implemented:** Takeout Doubles, Negative Doubles
- ✅ **Fully Implemented:** Michaels Cuebid, Unusual 2NT, Fourth Suit Forcing, Splinter Bids
- **Convention Registry:** Manages all conventions with `base_convention.py`

**7. Play AI Systems** (`engine/play/ai/`):
- **SimplePlayAI** (Levels 1-6): Basic heuristics, fast performance (<1s/hand), 40-60% success
- **MinimaxPlayAI** (Levels 7-8): Lookahead search depth 2-3, 2-3s/hand, 70-80% success
- **DDS** (Levels 9-10): Perfect play analysis, **<1ms/play**, 95%+ success, Linux only (default on production)

**8. engine/hand.py** - `Hand` class:
- Represents 13-card bridge hand
- Auto-calculates: HCP, distribution points, suit lengths, suit HCP, balanced status
- Uses `Card` namedtuple (rank, suit)

**9. engine/hand_constructor.py**:
- `generate_hand_for_convention()` - Creates hands matching convention requirements
- `generate_hand_with_constraints()` - Creates hands with specific HCP/shape constraints

**10. engine/ai/feature_extractor.py**:
- Extracts contextual features from auction history
- Determines partnerships, positions, opener relationships

**11. engine/feedback/bidding_feedback.py**:
- Evaluates user bids for correctness
- Provides scoring (0-10) and ratings (optimal/acceptable/suboptimal/error)
- Generates improvement hints
- Tracks bidding quality statistics

### Frontend Structure

**Single-page React app** (`frontend/src/App.js`):

#### Main Components
- **Card** - Visual card representation
- **LibraryCard** - Professional SVG cards for East/West (vertical layout)
- **HandAnalysis** - Shows HCP, distribution, suit breakdown, vulnerability
- **BiddingTable** - 4-column auction display (North/East/South/West) with dealer indicator "(D)"
- **BiddingBox** - Interactive bidding interface with legality checks
- **PlayTable** - Card play interface with trick display
- **LearningDashboard** - Analytics modal with 7 statistics cards
- **SimpleLogin** - Email/phone authentication
- **App** - Main orchestrator

#### State Management
- **Authentication**: AuthContext provides `userId`, `isAuthenticated`, `login()`, `logout()`
- **Hand**: User's 13 cards (South position)
- **Auction**: Array of `{bid, explanation}` objects
- **Play State**: Current trick, cards played, tricks won
- **Next Player**: Whose turn (0=North, 1=East, 2=South, 3=West)
- **Dealer**: Rotates North → East → South → West (Chicago system)
- **Vulnerability**: Tracks vulnerability rotation (None → NS → EW → Both)

#### User Flow
1. User logs in (email/phone) or continues as guest
2. User sees their hand (South) and bidding table
3. Bidding phase: User bids → Receives feedback → AI players bid
4. Play phase: Declarer and dummy identified → Cards played → Tricks evaluated
5. Scoring: Contract result calculated → Dashboard updated
6. Dashboard: View statistics and learning insights

### Multi-User System

The app supports multiple users with isolated data tracking.

#### Authentication

**SimpleLogin System:**
- Email or phone only (no password)
- Automatic account creation on first login
- Guest mode for quick play
- Persistent login via localStorage

**API:** `/api/auth/simple-login`

**Frontend:** `frontend/src/components/auth/SimpleLogin.jsx`, `frontend/src/contexts/AuthContext.jsx`

#### User Separation

**Each user has:**
- Unique `user_id` in database
- Isolated bidding history (`bidding_decisions` table)
- Separate dashboard analytics
- Personal game sessions (`game_sessions` table)
- Individual progress tracking

**Data Flow:**
```javascript
// User logs in → userId stored in context
const { userId } = useAuth();

// All API calls include user_id
fetch('/api/evaluate-bid', {
  body: JSON.stringify({ user_id: userId, ...})
})

// Backend filters all queries by user_id
SELECT * FROM bidding_decisions WHERE user_id = ?
```

**Database Schema:**
```sql
users: id, email, phone, display_name, created_at
bidding_decisions: id, user_id, user_bid, optimal_bid, score, timestamp
hand_analyses: id, user_id, hand_id, hcp, shape, timestamp
game_sessions: id, user_id, session_type, hands_completed, timestamp
session_hands: id, session_id, score, declarer_made, contract, timestamp
```

**See:** `USER_FLOW_GUIDE.md` for complete multi-user documentation

### Card Play System

Full card play implementation with AI opponent simulation.

#### PlayEngine

**File:** `backend/engine/play_engine.py`

**Responsibilities:**
- Execute complete hand play
- Manage trick evaluation
- Determine trick winners
- Track contract progress
- Calculate final scores

#### AI Levels (1-10)

**Level 1-6: SimplePlayAI**
- Basic heuristics (high card, trump management)
- Fast performance (<1s per hand)
- Success rate: 40-60%

**Level 7-8: MinimaxPlayAI**
- Lookahead search (depth 2-3)
- Position evaluation
- Success rate: 70-80%
- Moderate performance (2-3s per hand)

**Level 9-10: DDS (Double Dummy Solver)**
- Perfect play analysis using solve_board
- Success rate: 95%+ (optimal double-dummy play)
- **Fast performance (<1ms per play)** - suitable for real-time
- **Default on production (Linux)** - uses endplay library
- **⚠️ Linux only** (crashes on macOS M1/M2)

#### Play Flow

```
Deal hands → Bidding → Contract established →
  Play loop:
    1. Determine current player
    2. Get legal plays
    3. AI selects card (or user input)
    4. Add card to trick
    5. Evaluate trick winner
    6. Next trick
  → Calculate final score
```

**Frontend:** `frontend/src/PlayComponents.js` (PlayableCard, CurrentTrick, PlayTable)

**Backend:** `backend/engine/play/ai/` (simple_play_ai.py, minimax_play_ai.py)

**See:** `PLAY_QUALITY_SCORE_PROTOCOL.md` for testing and quality requirements

### Key Features

#### Dashboard Analytics
- **Bidding Quality Tracking:** Optimal rate, avg score, error rate
- **Recent Decisions:** Last 10 bids with feedback
- **Gameplay Statistics:** Contracts made/failed, declarer success rate
- **Learning Insights:** Patterns, growth areas, recommendations
- **Real-time Updates:** Dashboard refreshes on modal reopen (key-based remounting)

**API:** `/api/analytics/dashboard?user_id={user_id}`

**Implementation:** Uses `key={Date.now()}` to force remount and fresh data fetch

#### Bidding Feedback System
- **Real-time Evaluation:** Every user bid evaluated against optimal
- **Correctness Ratings:** Optimal (10), Acceptable (7-9), Suboptimal (4-6), Error (0-3)
- **Scoring:** 0-10 scale with detailed feedback
- **Improvement Hints:** Specific suggestions for better bids
- **Historical Tracking:** All decisions stored per user

**API:** `/api/evaluate-bid`

#### Chicago Rotation
- **4-Hand Sessions:** Complete Chicago-style sessions
- **Dealer Rotation:** North → East → South → West (fully implemented)
- **Vulnerability Rotation:** None → NS → EW → Both
- **Score Tracking:** North-South vs East-West
- **Dealer Indicator:** "(D)" shows in bidding table

#### Card Display
- **Professional SVG Cards:** External library (@letele/playing-cards)
- **Responsive Layouts:** Horizontal (North/South) and vertical (East/West)
- **Proper Overlap:** 80% overlap for vertical hands (East/West)
- **Suit Separation:** Visual grouping by suit
- **LibraryCard Component:** Handles East/West vertical display

**See:** `IMPLEMENTATION_COMPLETE_QUICK_REF.md`, `USER_FLOW_GUIDE.md`

### Scenarios System

**scenarios.json** defines training scenarios with hand generation rules:
- `generate_for_convention` - Uses convention's hand generator
- `constraints` - Specifies HCP range, suit lengths, balanced requirement
- Remaining positions get random hands from remaining deck

---

## Testing Strategy

**Comprehensive Test Suite Documentation:**
- **[Bidding Test Suite](docs/testing/BIDDING_TEST_SUITE.md)** - Complete bidding testing guide
- **[Play Test Suite](docs/testing/PLAY_TEST_SUITE.md)** - Complete card play testing guide

### Fast Feedback Loop

**During Development:**
```bash
cd backend
./test_quick.sh      # 30 seconds - unit tests only
./test_medium.sh     # 2 minutes - unit + integration

# E2E tests during development
cd frontend
npm run test:e2e:ui  # Interactive E2E debugging (recommended)
```

**Before Committing:**
```bash
# Comprehensive - all tests (RECOMMENDED)
./test_all.sh        # Backend + Frontend + E2E (2-3 minutes)

# Quick - unit tests only
./test_all.sh --quick --skip-e2e  # 30 seconds

# Backend only
cd backend && ./test_full.sh      # 5+ minutes - all backend tests
```

**Pre-commit Hook:**
When you run `git commit`, you'll be prompted to choose:
1. Quick tests (30 seconds) - Unit tests only
2. Full tests (2-3 minutes) - All tests including E2E
3. Skip tests (not recommended)

The pre-commit hook automatically runs tests based on your choice.

### Test Organization

```
backend/tests/
├── unit/          # Fast unit tests - run constantly
├── integration/   # Integration tests - run before commit
├── regression/    # Bug fix tests - proves bugs stay fixed
├── features/      # Feature tests - end-to-end validation
├── scenarios/     # Specific bidding situations
└── play/          # Card play engine tests

frontend/
├── src/
│   └── **/*.test.js   # Jest unit tests for React components
└── e2e/
    └── tests/
        ├── verification.spec.js      # Environment verification
        ├── app-smoke-test.spec.js    # Basic app functionality
        └── *.spec.js                 # E2E test files (Playwright)
```

### Quality Score Testing

**Before any bidding logic change:**
```bash
# Establish baseline
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_before.json

# Make changes, then comprehensive test
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_after.json

# Compare
python3 compare_scores.py baseline_before.json baseline_after.json
```

**Before any play logic change:**
```bash
# Establish baseline
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_before.json

# Make changes, then test
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_after.json

# Compare
python3 compare_play_scores.py play_before.json play_after.json
```

### Testing Rules

**ALWAYS:**
- ✅ Add tests for new features
- ✅ Add regression tests for bug fixes
- ✅ Run quick tests during development
- ✅ Run `./test_all.sh` before committing
- ✅ Run quality scores before bidding/play changes
- ✅ Add E2E tests for user-facing features
- ✅ Use data-testid attributes in React components for E2E testing

**NEVER:**
- ❌ Commit without running tests (pre-commit hook enforces this)
- ❌ Skip regression tests for bugs
- ❌ Modify bidding logic without baseline quality score
- ❌ Modify play logic without baseline quality score
- ❌ Use `git commit --no-verify` unless absolutely necessary

**E2E Testing Best Practices:**
- ✅ Use `data-testid` attributes for stable selectors
- ✅ Test user behavior, not implementation details
- ✅ Keep tests independent (no shared state)
- ✅ Use `npm run test:e2e:ui` for debugging failed tests
- ✅ Add E2E test when fixing a regression bug

**See:** `.claude/CODING_GUIDELINES.md` for complete quality assurance protocols

---

## Key Bidding Engine Concepts

**Feature Extraction**: Every bid decision requires contextual features:
- Auction history
- Player positions (North/East/South/West)
- Opener relationship (Me/Partner/Opponent/None)
- Vulnerability
- Hand properties

**Module Interface**: All specialists implement:
```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    # Returns (bid, explanation) or None
```

**Decision Priority**: Decision engine checks in order:
1. Opening situation → Preempts → Opening Bids
2. Competitive situation → Overcalls → Takeout Doubles → Advancer
3. Partnership auction → Conventions (Stayman/Jacoby/Blackwood) → Natural responses/rebids

**Legality Enforcement**: `BiddingEngine._is_bid_legal()` prevents illegal bids:
- Higher level OR same level + higher suit ranking
- Special bids (Pass, X, XX) always legal

**Appropriateness Validation**: Base convention class validates bid appropriateness:
- HCP requirements for level (3-level needs 10+ HCP, 4-level needs 12+ HCP)
- Suit length requirements (3+ for raises, 4+ for new suits)
- Prevents inappropriate bids that are technically legal

---

## Important Implementation Notes

- **Vulnerability rotation**: Cycles None → NS → EW → Both on each new deal
- **Bid format**: Strings like "1♠", "3NT", "Pass", "X", "XX"
- **Suit ranking**: ♣ < ♦ < ♥ < ♠ < NT
- **Dealer rotation**: Implements Chicago rotation (North → East → South → West) across 4-hand sessions
- **Dealer indicator**: Shows "(D)" next to dealer in bidding table
- **User position**: Always South
- **AI delay**: 500ms between AI bids for UX

---

## Seat Position Utilities

**CRITICAL: Use the seats utility module for ALL seat/position calculations.**

The application uses a modulo-4 clock system for seat positions:
- `NORTH = 0`, `EAST = 1`, `SOUTH = 2`, `WEST = 3`
- Partner is always `+2` (opposite)
- LHO (Left Hand Opponent) is always `+1` (clockwise)
- RHO (Right Hand Opponent) is always `+3`

**Backend (Python):**
```python
from utils.seats import partner, lho, rho, relative_position, display_name, bidder_role

# Get partner of a seat
partner('S')  # Returns 'N'

# Get relative position (0=Self, 1=LHO, 2=Partner, 3=RHO)
relative_position('N', hero='S')  # Returns 2 (Partner)

# Get display name for UI
display_name('E', hero='S')  # Returns 'RHO'
bidder_role('N', user='S')   # Returns 'North (Partner)'
```

**Frontend (JavaScript):**
```javascript
import { partner, lho, rho, relativePosition, displayName, bidderRole, nsSuccess } from '../utils/seats';

// Same functions with camelCase naming
partner('S')  // Returns 'N'
relativePosition('N', 'S')  // Returns 2
displayName('E', 'S')  // Returns 'RHO'
bidderRole('N', 'S')   // Returns 'North (Partner)'

// NS success calculation for both declaring and defending
nsSuccess(nsIsDeclarer, actualTricksNs, requiredTricks)
```

**Rules:**
- ✅ ALWAYS import from `utils/seats` for seat calculations
- ✅ Use integer indices (0-3) in storage/logic, strings ('N','E','S','W') in display
- ✅ Use `normalize()` to convert full names ('North') to single letters ('N')
- ❌ NEVER hardcode seat relationships (e.g., `if player == 'South'`)
- ❌ NEVER duplicate seat math inline - use the utility functions

**Files:**
- Backend: `backend/utils/seats.py`
- Frontend: `frontend/src/utils/seats.js`
- Tests: `backend/tests/unit/test_seats.py`, `frontend/src/utils/seats.test.js`

---

## Adding New Conventions

1. Create convention file in `backend/engine/ai/conventions/`
2. Extend `ConventionModule` base class
3. Implement `evaluate()` method
4. Register in `BiddingEngine.modules` dictionary
5. Add logic to `decision_engine.py` for when to check convention
6. (Optional) Add hand generator method for scenarios
7. Add test file in `backend/tests/`
8. **Run baseline quality score** before and after to verify no regressions

---

## Common Pitfalls

- **Frontend bid legality**: BiddingBox has client-side legality check that must match backend logic
- **Feature extraction**: Specialist modules receive full features dict even if they don't use it
- **Module naming**: Decision engine returns module name as string (e.g., 'stayman'), not the class
- **Hand generation**: Scenarios consume cards from deck, so order matters
- **Auction indexing**: Position in auction determined by `index % 4` mapping to player positions
- **DDS crashes on macOS**: Always use Level 8 (Minimax) for development, Level 10 (DDS) only on Linux production
- **DDS debugging requires production**: DDS-related features (decay curves, play analysis) cannot be tested locally on macOS. To debug DDS issues, deploy to production or SSH to Oracle server and run tests there. Never attempt to verify DDS results locally.
- **Quality score regression**: Always compare before/after scores to catch performance degradation

---

## Documentation Standards

**⚠️ CRITICAL: Documentation is NOT optional. All code changes require documentation updates.**

### Documentation-First Principle

**Before making ANY change:**
1. Read `.claude/DOCUMENTATION_PRACTICES.md` (MANDATORY)
2. Use `docs/DOCUMENTATION_CHECKLIST.md` (ALWAYS)
3. Identify which docs will be affected
4. Note current discrepancies

**During implementation:**
- Update technical/feature docs inline with code
- Keep documentation in sync

**Before completing:**
- Use documentation checklist systematically
- Update ALL affected documentation files
- Verify documentation quality
- Include docs in same commit as code

### Required Documentation

**For EVERY feature:**
- Create `docs/features/FEATURE_NAME.md`
- Update `docs/project-overview/FEATURES_SUMMARY.md`

**For EVERY bug fix:**
- Create `docs/bug-fixes/BUG_NAME.md`
- Update relevant feature documentation

**For EVERY milestone:**
- Create `docs/development-phases/PHASE#_COMPLETE.md`

### Documentation Organization

**IMPORTANT**: All project documentation is organized in the `docs/` directory with a structured hierarchy.

#### Directory Structure

```
docs/
├── README.md                 # Main documentation index
├── project-overview/         # Core project docs, setup, strategy
├── development-phases/       # Phase 1, Phase 2, milestone docs
├── features/                 # Feature-specific documentation
├── guides/                   # Testing guides, usage guides
└── bug-fixes/                # Bug reports, fixes, known issues
```

#### Documentation Rules

**When Creating New Documentation:**

1. **NEVER create markdown files in the project root** - Always use `docs/` subdirectories
2. **Choose the appropriate category**:
   - **project-overview/** - Project-wide documentation, deployment, setup, strategy, tooling
   - **development-phases/** - Milestone completions, phase summaries, session notes (use `PHASE#_DESCRIPTION.md` format)
   - **features/** - Feature implementations, architecture, specifications (use `FEATURE_NAME.md` format)
   - **guides/** - Testing procedures, usage guides, how-tos (use `SUBJECT_GUIDE.md` format)
   - **bug-fixes/** - Bug tracking, fixes, known issues (use `BUG_FIX_AREA.md` or `AREA_FIXES_DATE.md` format)

3. **Update docs/README.md** when adding new documents to maintain the index

4. **Use descriptive, consistent filenames**:
   - ALL_CAPS with underscores (e.g., `CONVENTION_SYSTEM.md`)
   - Include dates for time-specific docs (e.g., `BIDDING_FIXES_2025-10-10.md`)
   - Use category prefixes when helpful (e.g., `PHASE2_API_INTEGRATION.md`)

**When Updating Existing Documentation:**

1. Find the existing document in `docs/` using the category system
2. Update in place - don't create duplicates
3. If a doc spans multiple categories, choose the primary category and reference it from others

**Quick Reference:**

- Need to document a new feature? → `docs/features/FEATURE_NAME.md`
- Completed a development phase? → `docs/development-phases/PHASE#_DESCRIPTION.md`
- Writing a testing guide? → `docs/guides/TESTING_SUBJECT.md`
- Tracking a bug fix? → `docs/bug-fixes/BUG_FIX_AREA.md`
- General project info? → `docs/project-overview/TOPIC.md`

### Automated Checks

**Before every commit:**
```bash
# Run documentation compliance checker
python3 .claude/scripts/check_documentation_compliance.py --verbose

# Run validation script
./.claude/scripts/validate_documentation.sh

# All checks must pass
```

**Pre-commit hook:** Automatically checks documentation and warns if missing

### Documentation Quality Standard

**A task is NOT complete until:**
- [ ] Code is implemented
- [ ] Tests pass
- [ ] Documentation is updated
- [ ] Documentation checklist is completed
- [ ] All files committed together
- [ ] Automated checks pass

**Standard:** A new developer should be able to understand, use, and modify any feature based solely on the documentation.

**See:** `.claude/DOCUMENTATION_PRACTICES.md`, `.claude/PROJECT_CONTEXT.md`, [docs/README.md](docs/README.md)

---

## UI/UX Standards

**⚠️ MANDATORY: Reference UI/UX standards for ALL interface changes**

### Design Authority

**Primary Document:** `.claude/UI_UX_DESIGN_STANDARDS.md`

This is the **authoritative source** for all UI/UX decisions.

### When to Consult Standards

**ALWAYS reference UI_UX_DESIGN_STANDARDS.md when:**
- Creating new UI components
- Modifying existing components
- Adding interactive elements (buttons, modals, etc.)
- Changing colors, spacing, or typography
- Implementing animations or transitions
- Adding tooltips, error messages, or feedback
- Making responsive design decisions
- Implementing accessibility features

### Key Requirements

**Design System:**
- **Colors:** Use CSS variables only (NO hardcoded colors)
  - `--color-success`, `--color-danger`, `--color-info`
  - `--bg-primary`, `--bg-secondary`, `--text-primary`
- **Spacing:** Use 8px grid system (`--space-2`, `--space-4`, `--space-6`)
- **Typography:** Use font scale (`--text-sm`, `--text-base`, `--text-lg`)

**Responsive Design (MANDATORY):**
- **Mobile-first approach**
- **Test at breakpoints:** 360px (small phone), 480px (phone), 768px (tablet), 1024px (iPad landscape), 1280px (desktop)
- **Use responsive classes:** `w-9 sm:w-12 md:w-16` (NOT fixed `w-12`)
- **Breakpoint prefixes:** base, sm:, md:, lg:

**Responsive CSS Patterns (CRITICAL):**
- **NEVER use fixed `min-width` over 300px** - Use `min-width: min(350px, 100%)` instead
- **NEVER use fixed `min-height` over 200px** without a responsive fallback
- **ALWAYS add 360px breakpoint** for extra small phones when using grids/flex layouts
- **ALWAYS use `calc(100vw - Xpx)` or `min()` function** for widths that could overflow
- **ALWAYS test on 360px viewport** before committing CSS changes
- **Grid layouts:** Use `minmax(min(300px, 100%), 1fr)` pattern for responsive grids
- **Animations:** Use percentage-based transforms (`translateX(100%)`) not fixed pixels (`translateX(400px)`)

**Accessibility (WCAG 2.1 AA):**
- Keyboard navigation support
- ARIA labels for all interactive elements
- Contrast ratios meet standards
- Touch targets ≥44px on mobile
- Screen reader compatibility

### UI Code Review Checklist

Before committing UI code:
- [ ] Uses CSS variables (not hardcoded colors)
- [ ] Responsive at all breakpoints (test 375px, 768px, 1280px)
- [ ] Keyboard navigation works
- [ ] ARIA labels present
- [ ] Touch targets ≥44px
- [ ] Animations respect prefers-reduced-motion
- [ ] Loading states implemented
- [ ] Error messages are educational (not technical)

**See:** `.claude/UI_UX_DESIGN_STANDARDS.md`, `.claude/RESPONSIVE_DESIGN_RULES.md`, `.claude/HOW_TO_ENSURE_CLAUDE_FOLLOWS_STANDARDS.md`

---

## Architectural Decisions

### When to Perform Architectural Review

**HIGH-RISK triggers (MUST review):**
- Creating new directories or reorganizing structure
- Adding new dependencies (npm, pip, etc.)
- Changing data structures used across multiple modules
- Modifying API contracts
- Introducing new state management patterns
- Creating database schemas or migrations
- Modifying build/deployment configuration
- Refactoring code used by 3+ other modules

**MEDIUM-RISK triggers (strongly recommended):**
- Creating new classes/services with 200+ lines
- Adding environment variables or configuration
- Modifying shared utilities
- Changes affecting test infrastructure

### Review Process

When trigger detected:
1. **PAUSE** implementation
2. Read `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md`
3. Complete 30-minute review checklist
4. Generate 3+ alternatives
5. Score options using decision matrix
6. Create ADR in `docs/architecture/decisions/`
7. Present analysis to user for HIGH-RISK changes
8. Only then implement

**See:** `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md`, `docs/architecture/decisions/README.md`

---

## Additional Resources

- **Quick Start:** `.claude/QUICK_START.md` - Quick debugging and validation checklist
- **Project Context:** `.claude/PROJECT_CONTEXT.md` - Comprehensive project information
- **Coding Guidelines:** `.claude/CODING_GUIDELINES.md` - Systematic analysis and QA protocols
- **Bidding Test Suite:** `docs/testing/BIDDING_TEST_SUITE.md` - Comprehensive bidding testing guide
- **Play Test Suite:** `docs/testing/PLAY_TEST_SUITE.md` - Comprehensive card play testing guide
- **Documentation Index:** `docs/README.md` - Complete documentation navigation
- **Production Readiness:** `READY_FOR_PRODUCTION.md` - Production deployment checklist
- **User Flow:** `USER_FLOW_GUIDE.md` - Complete user journey documentation
