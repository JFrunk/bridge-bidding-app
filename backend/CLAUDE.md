# API Server & Infrastructure

**Specialist Area:** Flask REST API, authentication, session management, database, testing infrastructure

## Scope

This area covers the server layer and infrastructure. You are responsible for:

- **Flask API:** All REST endpoints in `server.py`
- **Session management:** Per-session state isolation
- **Authentication:** Simple login (email/phone)
- **Database:** SQLite schema, initialization, queries
- **Testing infrastructure:** Test scripts, fixtures, quality scoring
- **Deployment:** Render configuration, environment variables

## Key Files

```
backend/
├── server.py                  # Flask REST API (~2,600 lines)
├── core/
│   ├── session_state.py       # Per-session state manager
│   ├── deal_generator.py      # Random hand generation
│   ├── scenario_loader.py     # Training scenarios
│   └── session_manager.py     # Game session tracking
├── database/
│   ├── init_all_tables.py     # Schema initialization
│   ├── init_auth_tables.py    # User tables
│   └── init_convention_data.py
├── engine/auth/
│   └── simple_auth_api.py     # Authentication logic
├── utils/
│   └── error_logger.py        # Error logging system
├── scenarios/
│   └── bidding_scenarios.json
├── tests/                     # All test infrastructure
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── features/
├── test_quick.sh              # 30-second unit tests
├── test_medium.sh             # 2-minute integration
├── test_full.sh               # 5+ minute comprehensive
├── test_bidding_quality_score.py
├── test_play_quality_integrated.py
├── requirements.txt
└── pytest.ini

# Root
├── test_all.sh                # Full suite including E2E
└── render.yaml                # Deployment config
```

## Architecture

### Server Startup
```python
app = Flask(__name__)
CORS(app)
engine = BiddingEngine()           # Bidding AI
play_engine = PlayEngine()         # Play orchestration
state_manager = SessionStateManager()  # Per-session state
session_manager = SessionManager('bridge.db')

# AI instances for difficulty levels
ai_instances = {
    'beginner': SimplePlayAI(),
    'intermediate': MinimaxPlayAI(max_depth=2),
    'advanced': MinimaxPlayAI(max_depth=3),
    'expert': DDSPlayAI() if DDS_AVAILABLE else MinimaxPlayAI(max_depth=4)
}
```

### Session State Management
```python
# OLD (race conditions)
current_deal = None  # Global variable - BAD

# NEW (per-session isolation)
state = state_manager.get_state(session_id)
state.deal = deal_data
```

### Request Flow
```
HTTP Request
  → Flask route handler
  → get_session_id_from_request()
  → state_manager.get_state(session_id)
  → Call appropriate engine (Bidding/Play)
  → Store results in session state
  → Return JSON response
```

## API Endpoints

### Bidding
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/deal-hands` | GET | Generate new random hands |
| `/api/scenarios` | GET | List training scenarios |
| `/api/load-scenario` | POST | Load specific scenario |
| `/api/get-next-bid` | POST | AI makes a bid |
| `/api/evaluate-bid` | POST | Evaluate user's bid |

### Play
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/play-card` | POST | User plays a card |
| `/api/get-ai-play` | POST | AI plays a card |
| `/api/get-play-state` | GET | Current play state |

### Auth & Analytics
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/simple-login` | POST | Email/phone login |
| `/api/analytics/dashboard` | GET | User statistics |
| `/api/dds-status` | GET | DDS availability |

## Database Schema

```sql
-- Users
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT,
    phone TEXT,
    display_name TEXT,
    created_at TIMESTAMP
);

-- Bidding history
CREATE TABLE bidding_decisions (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    user_bid TEXT,
    optimal_bid TEXT,
    score INTEGER,
    timestamp TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Game sessions
CREATE TABLE game_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    session_type TEXT,
    hands_completed INTEGER,
    timestamp TIMESTAMP
);
```

## Testing Infrastructure

### Test Hierarchy
```bash
./test_quick.sh      # 30s - Unit tests only
./test_medium.sh     # 2min - Unit + Integration
./test_full.sh       # 5min+ - All backend tests
./test_all.sh        # Full - Backend + Frontend + E2E
```

### Quality Score Tests
```bash
# Bidding quality
python3 test_bidding_quality_score.py --hands 500 --output baseline.json

# Play quality
python3 test_play_quality_integrated.py --hands 500 --level 8 --output play.json

# Compare
python3 compare_scores.py before.json after.json
```

## Common Tasks

### Add New Endpoint
1. Define route in `server.py`
2. Get session state: `state = get_state()`
3. Call appropriate engine
4. Return JSON response
5. Add integration test

### Fix Session State Bug
1. Check `core/session_state.py`
2. Verify session ID extraction
3. Ensure no global variable usage
4. Test multi-user scenario

### Database Migration
1. Update `database/init_all_tables.py`
2. Test locally: `python3 database/init_all_tables.py`
3. **CRITICAL:** Run on production BEFORE deploying code

### Add New Test Category
1. Create directory in `tests/`
2. Add `__init__.py`
3. Create test files following `test_*.py` pattern
4. Update `pytest.ini` if needed

## Deployment

### Render Configuration (`render.yaml`)
```yaml
services:
  - type: web
    name: bridge-bidding-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn server:app
```

### Deployment Steps
1. **Database first:** Run migrations on production
2. Merge to `main` branch
3. Push triggers auto-deploy
4. Verify: Dashboard loads, login works

### Environment Variables
```
FLASK_ENV=production
DATABASE_PATH=/var/data/bridge.db
```

## Testing

```bash
# All backend tests
cd backend
./test_full.sh

# Specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/regression/ -v

# With coverage
pytest --cov=. --cov-report=html

# Single test file
pytest tests/integration/test_api_endpoints.py -v
```

## Dependencies

- **Flask 3.0+** - Web framework
- **Flask-CORS** - Cross-origin requests
- **gunicorn** - Production server
- **pytest 7.4+** - Testing
- **endplay 0.5+** - DDS (Linux only)

## Gotchas

- DDS only works on Linux - check `PLATFORM_ALLOWS_DDS`
- Session state replaces ALL global variables
- Database migrations must run BEFORE code deployment
- CORS is enabled for all origins (development convenience)
- AI instances are created at startup (not per-request)
- Error logging captures stack traces for debugging

## Error Analysis

**Always check error logs first when debugging:**
```bash
python3 analyze_errors.py              # Summary of all errors
python3 analyze_errors.py --recent 10  # Last 10 with details
python3 analyze_errors.py --patterns   # Recurring issues
```
Errors include full context: auction state, hand data, stack traces.

## Reference Documents

- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Online single-player control rules
- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Bidding system reference
