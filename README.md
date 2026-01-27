# Bridge Bidding Training Application

A comprehensive web-based application for learning and practicing bridge bidding conventions with AI-powered assistance and gameplay review.

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd bridge_bidding_app

# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Running Locally

```bash
# Terminal 1: Start backend
cd backend
python server.py

# Terminal 2: Start frontend
cd frontend
npm start
```

Visit `http://localhost:3000` to use the application.

## Project Status

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current status, features, and known issues.

## Documentation

### Essential Resources

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute (includes mandatory documentation requirements)
- **[docs/README.md](docs/README.md)** - Complete documentation index
- **[docs/project-overview/DOCUMENTATION_INDEX.md](docs/project-overview/DOCUMENTATION_INDEX.md)** - Comprehensive documentation map
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current project status

### For Contributors

**CRITICAL**: Documentation updates are mandatory for all code changes.

Before making any code changes, read:
1. **[.claude/DOCUMENTATION_PRACTICES.md](.claude/DOCUMENTATION_PRACTICES.md)** - Documentation guidelines
2. **[docs/DOCUMENTATION_CHECKLIST.md](docs/DOCUMENTATION_CHECKLIST.md)** - Checklist for every change
3. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Full contributing guide

### Working with Claude Code

When using Claude to debug or develop:

- **[.claude/QUICK_START.md](.claude/QUICK_START.md)** - Quick reference for systematic debugging
- **[.claude/CODING_GUIDELINES.md](.claude/CODING_GUIDELINES.md)** - Complete systematic analysis framework
- **[docs/project-status/SYSTEMATIC_ANALYSIS_SUMMARY.md](docs/project-status/SYSTEMATIC_ANALYSIS_SUMMARY.md)** - Overview and usage guide

**Key Practice**: When debugging, always check if an issue exists broadly across the codebase, not just in the reported location.

### For Developers

- **Getting Started**: [docs/project-overview/CLAUDE.md](docs/project-overview/CLAUDE.md)
- **Features**: [docs/project-overview/FEATURES_SUMMARY.md](docs/project-overview/FEATURES_SUMMARY.md)
- **Testing**: [docs/guides/TESTING_GUIDE.md](docs/guides/TESTING_GUIDE.md)
- **Architecture**: [docs/architecture/](docs/architecture/)

### For Testers

- **Testing Guide**: [docs/guides/GAMEPLAY_TESTING_GUIDE.md](docs/guides/GAMEPLAY_TESTING_GUIDE.md)
- **Quick Test Checklist**: [docs/guides/QUICK_TEST_CHECKLIST.md](docs/guides/QUICK_TEST_CHECKLIST.md)

## Features

### Current Features
- Interactive bridge bidding practice
- Standard American Yellow Card (SAYC) conventions
- **AI-powered bidding with BiddingEngineV2 (95.6% quality score)**
- Detailed bid explanations
- Multiple bidding scenarios
- Gameplay review with AI analysis
- Card play engine
- Responsive design for mobile/tablet

### Bidding Engine (Production)
**BiddingEngineV2** (Python State Machine) - Deployed 2026-01-27
- **Quality Score**: 95.6% (Grade A - Production Ready)
- **Performance**: 4,000+ hands/second, 0.03ms per bid
- **Features**: Full SAYC conventions, Blackwood, Stayman, Transfers
- See `backend/QUALITY_SCORECARD.md` for detailed metrics

See [docs/project-overview/FEATURES_SUMMARY.md](docs/project-overview/FEATURES_SUMMARY.md) for complete feature list.

## Development

### Branch Workflow

- **main/master**: Production-ready code
- **development**: Integration branch (current working branch)
- **feature/name**: Feature branches
- **fix/name**: Bug fix branches

### Running Tests

```bash
# Backend tests
cd backend
pytest                          # All tests
pytest tests/test_file.py      # Specific file
pytest -v                       # Verbose output

# Frontend tests
cd frontend
npm test
```

### Code Standards

- Python: Follow PEP 8, use type hints, write docstrings
- JavaScript/React: Use functional components, follow ESLint config
- Documentation: Update docs with every code change (mandatory)

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed standards.

## Architecture

### Backend (Python/Flask)
```
backend/
├── server.py              # Flask server (session-based state)
├── core/
│   └── session_state.py   # Session state manager (thread-safe)
├── engine/                # Bidding logic
│   ├── opening_bids.py
│   ├── rebids.py
│   ├── responses.py
│   ├── overcalls.py
│   └── advancer_bids.py
├── tests/                 # Test suite
│   ├── test_simple.py     # Session state verification
│   └── test_session_state.py  # Full integration tests
└── simulation_enhanced.py # Bidding simulation tool
```

**Key Architecture:**
- ✅ **Session-based state** - No global variables, thread-safe
- ✅ **Multi-user support** - Each session isolated via `SessionStateManager`
- ✅ **Scalable** - Ready for horizontal scaling with Redis

### Frontend (React)
```
frontend/
├── src/
│   ├── components/        # React components
│   ├── services/
│   │   └── api.js        # API service with session management
│   ├── utils/
│   │   └── sessionHelper.js  # Session ID utilities
│   ├── App.js            # Main application
│   └── ...
└── package.json
```

**Key Architecture:**
- ✅ **Session headers** - All API calls include `X-Session-ID`
- ✅ **Centralized API** - Consistent session management
- ✅ **LocalStorage persistence** - Session IDs persist across reloads

### Documentation
```
docs/
├── architecture/          # System design documentation
├── bug-fixes/            # Bug fix documentation
├── development-phases/   # Milestone documentation
├── features/             # Feature documentation
├── guides/               # User and testing guides
└── project-overview/     # High-level summaries
```

See [docs/project-overview/CLAUDE.md](docs/project-overview/CLAUDE.md) for detailed architecture.

### Session State Architecture (Critical - Oct 2025)

**⚠️ IMPORTANT:** This application uses session-based state management. **Never use global variables** for user-specific state.

**How It Works:**
```python
# Backend: Every endpoint must use session state
from core.session_state import get_session_id_from_request

@app.route('/api/endpoint')
def my_endpoint():
    state = get_state()  # Get isolated session state
    state.deal = {...}    # Use state, not globals!
    return jsonify({'success': True})
```

```javascript
// Frontend: All API calls must include session headers
import { getSessionHeaders } from './utils/sessionHelper';

fetch(`${API_URL}/api/endpoint`, {
  headers: {
    'Content-Type': 'application/json',
    ...getSessionHeaders()  // Always include this!
  }
});
```

**Why This Matters:**
- 🚫 **DO NOT** use global variables like `current_deal`, `current_state`
- ✅ **DO** use `state = get_state()` and `state.deal`, `state.play_state`
- ✅ **DO** include `X-Session-ID` header in all frontend API calls
- 📖 **READ:** [backend/GLOBAL_STATE_FIX_COMPLETED.md](backend/GLOBAL_STATE_FIX_COMPLETED.md) before making changes

**See Also:**
- [backend/GLOBAL_STATE_FIX_COMPLETED.md](backend/GLOBAL_STATE_FIX_COMPLETED.md) - Complete fix overview
- [backend/core/session_state.py](backend/core/session_state.py) - Session manager implementation
- [backend/GLOBAL_STATE_FIX_GUIDE.md](backend/GLOBAL_STATE_FIX_GUIDE.md) - Development guide
- [frontend/src/utils/sessionHelper.js](frontend/src/utils/sessionHelper.js) - Frontend session utilities

## Contributing

We welcome contributions! Please follow these steps:

1. **Read the documentation requirements** in [CONTRIBUTING.md](CONTRIBUTING.md)
2. **Create a feature branch** from `development`
3. **Make your changes** with tests and documentation
4. **Run tests** to ensure everything passes
5. **Update documentation** using [docs/DOCUMENTATION_CHECKLIST.md](docs/DOCUMENTATION_CHECKLIST.md)
6. **Submit a pull request** with complete documentation

**Important**: Documentation is not optional. All PRs must include appropriate documentation updates.

## Pre-Commit Hook

The project includes a pre-commit hook that reminds you to update documentation. It will:
- Check for code changes without documentation
- Verify documentation quality
- Catch common issues

To bypass (use sparingly): `git commit --no-verify`

## Testing

### Manual Testing
1. Start the application locally
2. Follow [docs/guides/GAMEPLAY_TESTING_GUIDE.md](docs/guides/GAMEPLAY_TESTING_GUIDE.md)
3. Use [docs/guides/QUICK_TEST_CHECKLIST.md](docs/guides/QUICK_TEST_CHECKLIST.md)

### Automated Testing
```bash
# Backend
cd backend
pytest -v

# Simulation (100-hand analysis)
python simulation_enhanced.py
```

### Test Coverage
See [docs/guides/TEST_VALIDATION_REPORT.md](docs/guides/TEST_VALIDATION_REPORT.md) for current test coverage.

## Deployment

See [docs/project-overview/DEPLOYMENT.md](docs/project-overview/DEPLOYMENT.md) for deployment instructions.

The application is deployed on Oracle Cloud Always Free tier. See [deploy/oracle/README.md](deploy/oracle/README.md) for deployment instructions.

## Known Issues

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current known issues and [docs/bug-fixes/RESIDUAL_ISSUES.md](docs/bug-fixes/RESIDUAL_ISSUES.md) for technical debt.

## Support and Resources

### Documentation
- Full documentation index: [docs/README.md](docs/README.md)
- Project overview: [docs/project-overview/DOCUMENTATION_INDEX.md](docs/project-overview/DOCUMENTATION_INDEX.md)

### Bridge Resources
- **[Complete Bridge Rules](docs/COMPLETE_BRIDGE_RULES.md)** - Comprehensive reference covering all aspects (bidding, play, scoring, transitions)
- **[Bridge Rules Summary](docs/BRIDGE_RULES_SUMMARY.md)** - Quick reference for common rules
- **[Play Implementation Audit](docs/BRIDGE_PLAY_AUDIT_SUMMARY.md)** - Status of play implementation vs official rules
- **[Play Fixes Completed](docs/BRIDGE_PLAY_FIXES_COMPLETED.md)** - ✅ Priority 1 fixes complete (Jan 2025)
- [SAYC Rules](https://www.acbl.org/learn_page/how-to-play-bridge/standard-american-yellow-card/)
- [Bridge Laws](http://www.worldbridge.org/laws-and-regulations/)

## License

[Add your license here]

## Authors and Acknowledgments

[Add authors and acknowledgments here]

---

## For Claude Code

**🚀 UPDATED 2025-10-12: Architectural review system + efficiency improvements!**

If you're Claude Code working on this project:

### 🎯 START HERE Every Session
1. **[.claude/QUICK_REFERENCE.md](.claude/QUICK_REFERENCE.md)** ⭐ **MUST READ at start of every session**
2. **[.claude/PROJECT_CONTEXT.md](.claude/PROJECT_CONTEXT.md)** - Full project context (auto-loads)

### 🏗️ NEW: Architectural Review (2025-10-12)

**BEFORE implementing changes with architectural impact:**

```bash
# Check for triggers (new dirs, APIs, data structures, etc.)
python3 .claude/scripts/check_architectural_triggers.py --verbose
```

**If HIGH-RISK detected:**
1. PAUSE implementation
2. Read [.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md](.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md)
3. Complete 30-minute architectural review
4. Create ADR in `docs/architecture/decisions/`
5. Present to user for approval
6. Only then implement

**Why:** Past mistakes (tight coupling, global state) cost velocity. This prevents them.

📖 **Full system**: [docs/project-overview/ARCHITECTURAL_DECISION_SYSTEM.md](docs/project-overview/ARCHITECTURAL_DECISION_SYSTEM.md)
📖 **ADR index**: [docs/architecture/decisions/README.md](docs/architecture/decisions/README.md)

### 📋 Development Workflow

**Templates for every task:**
- Feature: [.claude/templates/FEATURE_CHECKLIST.md](.claude/templates/FEATURE_CHECKLIST.md) (includes architectural checks)
- Bug Fix: [.claude/templates/BUG_FIX_CHECKLIST.md](.claude/templates/BUG_FIX_CHECKLIST.md) (includes architectural checks)
- Testing: [backend/tests/README.md](backend/tests/README.md)

**Quick Commands:**
```bash
# Testing (fast feedback loops)
./backend/test_quick.sh   # 30 sec - run during development
./backend/test_medium.sh  # 2 min - run before commit
./backend/test_full.sh    # 5+ min - run before push

# Architectural compliance
python3 .claude/scripts/check_architectural_triggers.py --verbose
python3 .claude/scripts/architectural_compliance_report.py --verbose

# Documentation compliance
python3 .claude/scripts/check_documentation_compliance.py --verbose
```

### 🎯 Key Improvements

**Architectural Decision System (NEW):**
- ✅ Automated trigger detection
- ✅ 30-minute review framework
- ✅ ADR documentation system
- ✅ Anti-pattern prevention

**Efficiency Improvements:**
- ✅ Test reorganization (30 sec feedback)
- ✅ Development templates
- ✅ CI/CD automation
- ✅ Consolidated documentation

### 📚 Essential Reading
1. [ARCHITECTURAL_DECISION_FRAMEWORK.md](.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md) - Review process
2. [EFFICIENCY_IMPROVEMENTS_COMPLETE.md](docs/project-overview/EFFICIENCY_IMPROVEMENTS_COMPLETE.md) - Workflow improvements
3. [ARCHITECTURAL_DECISION_SYSTEM.md](docs/project-overview/ARCHITECTURAL_DECISION_SYSTEM.md) - Complete system overview

**Documentation and architectural review are mandatory for all significant changes. No exceptions.**
