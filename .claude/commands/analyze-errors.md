Analyze error logs for bidding and play issues: $ARGUMENTS

Optional arguments: --recent N, --patterns, --category NAME

---

## Error Analysis Workflow

**Purpose:** Quickly identify and diagnose bidding/play errors using automated logging system

---

## Option 1: Error Summary (Default)

**When:** Quick health check, see if any errors occurred

```bash
cd backend
python3 analyze_errors.py
```

**Shows:**
- Total error count
- Errors by category (bidding_logic, play_engine, api, etc.)
- Errors by endpoint
- Alert if patterns detected

**Example Output:**
```
================================================================================
ERROR SUMMARY
================================================================================

Total Errors: 23

--- Errors by Category ---
  bidding_logic       :   15
  play_engine         :    8

--- Errors by Endpoint ---
  /api/get-next-bid                       :   15
  /api/play-card                          :    8

⚠️  Issues detected! Run with --patterns for details
```

---

## Option 2: Recent Errors

**When:** Want to see latest error details with full context

```bash
# Last 10 errors (default)
python3 analyze_errors.py --recent 10

# Last 5 errors
python3 analyze_errors.py --recent 5

# Last 20 errors
python3 analyze_errors.py --recent 20
```

**Shows:**
- Timestamp
- Error type and message
- Category
- Endpoint
- User ID
- Error hash (for tracking)
- Full context (auction state, hand data, etc.)

**Use case:** Debugging a bug that just occurred

---

## Option 3: Pattern Detection

**When:** Want to identify recurring issues

```bash
python3 analyze_errors.py --patterns
```

**Detects:**
- High frequency errors (same error >10 times)
- Critical endpoints (endpoints with >5 errors)
- First/last occurrence timestamps

**Example Output:**
```
================================================================================
ERROR PATTERNS DETECTED
================================================================================

--- High Frequency Errors (>10 occurrences) ---

  Hash: a1b2c3d4e5f6
    Count: 23
    First seen: 2025-11-02T15:00:00.000
    Last seen: 2025-11-02T16:30:15.123

--- Critical Endpoints (>5 errors) ---
  /api/get-next-bid                       : 15 errors
```

**Use case:** Finding systematic problems vs one-off bugs

---

## Option 4: Filter by Category

**When:** Investigating specific subsystem (bidding vs play)

```bash
# Bidding errors only
python3 analyze_errors.py --category bidding_logic

# Play errors only
python3 analyze_errors.py --category play_engine

# Database errors
python3 analyze_errors.py --category database

# API errors
python3 analyze_errors.py --category api

# Performance errors
python3 analyze_errors.py --category performance
```

**Shows:** All errors in that category with details

**Use case:** Focused investigation of one subsystem

---

## Error Categories

**bidding_logic:**
- Convention errors
- Response/rebid errors
- Opening bid errors
- Competitive bidding errors

**play_engine:**
- Card play errors
- Trick evaluation errors
- AI decision errors
- Contract tracking errors

**database:**
- SQLite connection errors
- Query errors
- Data integrity errors

**api:**
- Request validation errors
- Endpoint errors
- Session state errors

**performance:**
- Timeout errors
- Slow response errors

---

## Common Workflows

### 1. Daily Health Check

```bash
# Quick check for new errors
python3 analyze_errors.py

# If errors found, check patterns
python3 analyze_errors.py --patterns

# View recent details
python3 analyze_errors.py --recent 5
```

---

### 2. After Changing Bidding Logic

```bash
# Play a few hands, then check for bidding errors
python3 analyze_errors.py --category bidding_logic

# If errors found, see recent ones
python3 analyze_errors.py --recent 5
```

---

### 3. After Changing Play Logic

```bash
# Play through a hand, then check for play errors
python3 analyze_errors.py --category play_engine

# Check patterns
python3 analyze_errors.py --patterns
```

---

### 4. Investigating User-Reported Bug

```bash
# See if error was logged
python3 analyze_errors.py --recent 20

# Check for patterns
python3 analyze_errors.py --patterns

# Filter by relevant category
python3 analyze_errors.py --category bidding_logic
```

---

## Understanding Error Output

### Error Hash
Unique identifier for error pattern (e.g., `a1b2c3d4e5f6`)
- Same error → Same hash
- Tracks recurring issues
- Use to verify fixes

### Context Fields

**Bidding errors:**
```
context:
  - current_player: "North"
  - auction_length: 5
  - vulnerability: "NS"
  - has_hand: true
```

**Play errors:**
```
context:
  - position: "South"
  - card: {"rank": "A", "suit": "♠"}
  - trick_length: 2
  - contract: "3NT by South"
  - next_to_play: "West"
```

---

## No Errors? Great!

If you see:
```
✅ No errors logged yet - system is running clean!
```

This means:
- No exceptions occurred in bidding/play
- System is healthy
- Error logging is working (just nothing to log)

---

## Log Files

Located in `backend/logs/`:
- `errors.jsonl` - All errors (JSON Lines - one per line)
- `error_summary.json` - Aggregated statistics

**Manual inspection:**
```bash
# View raw error log
cat backend/logs/errors.jsonl | tail -5 | jq

# View summary
cat backend/logs/error_summary.json | jq
```

---

## Fixing Errors Workflow

1. **Identify error:**
   ```bash
   python3 analyze_errors.py --patterns
   ```

2. **View details:**
   ```bash
   python3 analyze_errors.py --recent 5
   ```

3. **Fix code** using stack trace + context

4. **Verify fix:**
   - Play hands to trigger same scenario
   - Run analysis again
   - Error hash should stop appearing

5. **Monitor:**
   - Check daily for new errors
   - Ensure fix holds

---

## When to Use Each Command

| Situation | Command |
|-----------|---------|
| Daily health check | `python3 analyze_errors.py` |
| Just hit a bug | `python3 analyze_errors.py --recent 5` |
| Finding patterns | `python3 analyze_errors.py --patterns` |
| Bidding investigation | `python3 analyze_errors.py --category bidding_logic` |
| Play investigation | `python3 analyze_errors.py --category play_engine` |
| Detailed debugging | `python3 analyze_errors.py --recent 20` |

---

## Integration with Testing

**Before running tests:**
```bash
# Clear old errors (optional)
rm backend/logs/errors.jsonl backend/logs/error_summary.json
```

**After running tests:**
```bash
# Check if tests triggered any errors
python3 analyze_errors.py
```

**This reveals:**
- Errors that don't fail tests (caught exceptions)
- Edge cases in error handling
- Unreported issues

---

## Success Criteria

✅ No high-frequency errors (same error >10 times)
✅ No critical endpoints (endpoint with >5 errors)
✅ Recent errors list is empty or declining
✅ Error patterns identified and fixed quickly

---

## Console Alerts

Backend console shows errors as they happen:
```
🚨 ERROR LOGGED: [bidding_logic] ValueError: Invalid bid format
   Hash: a1b2c3d4e5f6 | Endpoint: /api/get-next-bid | User: 42
```

Use hash to track in analysis tool.

---

## Full Documentation

See: [docs/features/ERROR_LOGGING_SYSTEM.md](../docs/features/ERROR_LOGGING_SYSTEM.md)

Quick start: [ERROR_LOGGING_QUICKSTART.md](../ERROR_LOGGING_QUICKSTART.md)

---

## Related Commands

- `/quick-test` - Run fast tests
- `/debug-systematic` - Systematic debugging protocol
- `/analyze-hand` - Analyze specific hand quality
