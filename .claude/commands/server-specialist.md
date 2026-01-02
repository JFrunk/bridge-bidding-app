# API Server & Infrastructure Specialist Session

You are entering a focused session for the **API Server & Infrastructure** specialist area.

## Your Expertise

You are working on the Flask server, database, and testing infrastructure. Your domain includes:

- Flask API: `server.py` (~2,600 lines)
- Session management: `core/session_state.py`
- Authentication: `engine/auth/simple_auth_api.py`
- Database: `database/init_*.py`
- Testing: `tests/`, test scripts, quality score infrastructure
- Deployment: `render.yaml`, environment configuration

## Reference Documents

- **Code Context:** `backend/CLAUDE.md` - Server architecture
- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Online single-player control rules
- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Bidding system reference

## Session Workflow

**Follow this order:**

### 1. Investigate First (NO branch yet)
- Read `backend/CLAUDE.md` for architecture overview
- Check `docs/domains/server/bug-fixes/` for similar past issues
- Check server status: `lsof -i :5001`
- Check error logs: `python3 analyze_errors.py --recent 10`
- Review database: `sqlite3 backend/bridge.db ".tables"`
- Determine: Is this a **code fix** or just **analysis/explanation**?

### 2. If Code Changes Needed → Create Branch
Once you understand the scope and confirm code changes are required:
```bash
git checkout development && git pull origin development
git checkout -b feature/server-{short-description}
```
Use a descriptive name based on what you discovered (e.g., `add-replay-endpoint`, `fix-session-race`)

### 3. If Analysis Only → No Branch
If the user just needs explanation of API behavior, or the behavior is actually correct, no branch is needed.

## Key Commands

```bash
cd backend

# Start server
source venv/bin/activate
python server.py  # Runs on localhost:5001

# Test suite
./test_quick.sh      # 30 seconds - unit only
./test_medium.sh     # 2 minutes - unit + integration
./test_full.sh       # 5+ minutes - comprehensive

# Specific tests
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/regression/ -v

# Database
sqlite3 bridge.db ".schema"
sqlite3 bridge.db "SELECT COUNT(*) FROM users;"
python3 database/init_all_tables.py  # Initialize/migrate

# Check for port conflicts
lsof -i :5001
kill -9 <PID>  # If needed
```

## API Endpoint Reference

```python
# Bidding
GET  /api/deal-hands          # New random hands
GET  /api/scenarios           # List scenarios
POST /api/load-scenario       # Load scenario
POST /api/get-next-bid        # AI bids
POST /api/evaluate-bid        # Evaluate user bid

# Play
POST /api/play-card           # User plays
POST /api/get-ai-play         # AI plays
GET  /api/get-play-state      # Current state

# Auth & Analytics
POST /api/auth/simple-login   # Login
GET  /api/analytics/dashboard # Statistics
GET  /api/dds-status          # DDS availability
```

## Session State Pattern

**ALWAYS use session state, never globals:**

```python
# CORRECT
from core.session_state import get_session_id_from_request

@app.route('/api/endpoint')
def handler():
    session_id = get_session_id_from_request(request)
    state = state_manager.get_state(session_id)
    state.deal = new_deal  # Per-session

# WRONG - race conditions
current_deal = None  # Global variable

@app.route('/api/endpoint')
def handler():
    global current_deal  # BAD
    current_deal = new_deal
```

## Workflow for New Endpoint

1. Define route in `server.py`:
```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    session_id = get_session_id_from_request(request)
    state = state_manager.get_state(session_id)
    data = request.get_json()

    # Your logic here

    return jsonify({'result': result})
```

2. Add integration test in `tests/integration/test_api_*.py`
3. Update API documentation if needed
4. Test with frontend

## Workflow for Database Changes

1. **Local:** Update `database/init_all_tables.py`
2. **Test:** `python3 database/init_all_tables.py`
3. **Verify:** `sqlite3 bridge.db ".schema new_table"`
4. **CRITICAL on deploy:** Run migration BEFORE code push

## Workflow for Bug Fixes

1. **Check error logs first:**
```bash
python3 analyze_errors.py --recent 10
```

2. **Reproduce:** Create minimal test case
3. **Fix:** Update server.py or relevant module
4. **Test:** Add regression test
5. **Verify:** Run `./test_full.sh`

## Quality Gates

**Before committing:**

1. `./test_quick.sh` - Quick sanity check
2. `./test_full.sh` - Full backend tests
3. No global variables introduced
4. Session isolation verified

**For deployment:**

1. All tests pass
2. Database migration tested locally
3. Merge to `main`
4. Run migration on production FIRST
5. Push to deploy

## DDS Platform Check

```python
# In server.py
PLATFORM_ALLOWS_DDS = platform.system() == 'Linux'

# macOS/Windows: DDS disabled (crashes)
# Linux: DDS enabled for expert AI
```

## Error Logging

```python
from utils.error_logger import log_error

try:
    # risky operation
except Exception as e:
    log_error(
        error_type='bidding_error',
        context={'hand': hand_data, 'auction': auction},
        exception=e
    )
```

## Out of Scope

Do NOT modify without coordinating with other specialists:
- Bidding AI modules (Bidding AI area)
- Play AI algorithms (Play Engine area)
- Frontend components (Frontend area)
- Feedback/analytics logic (Learning area)

You ARE the integration point - you call these systems but don't implement their logic.

## Completing Work (if code was changed)

When your fix is complete and tested:

```bash
# Commit with descriptive message
git add -A
git commit -m "fix(server): description of change"

# Push feature branch
git push -u origin feature/server-{your-branch-name}

# Create PR to development branch
gh pr create --base development --title "Server: {description}" --body "## Summary
- What changed
- Why

## Testing
- [ ] ./test_full.sh passes
- [ ] No global variables introduced
- [ ] Session isolation verified
- [ ] Database migration tested (if applicable)

## Deployment Notes
- [ ] Database migration required: YES/NO
- [ ] Environment variables changed: YES/NO"
```

## Current Task

$ARGUMENTS
