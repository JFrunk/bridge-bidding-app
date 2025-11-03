# Error Logging System - Quick Start

**Implemented:** 2025-11-02
**Status:** ✅ Active in backend (server running)

## What It Does

Automatically logs all errors in bidding and card play functionality with full context, enabling:
- 🔍 **Proactive bug detection** - Find issues before users report them
- 📊 **Pattern identification** - Detect recurring problems automatically
- 🚀 **Faster debugging** - Full stack traces + game state context
- 📈 **Quality monitoring** - Track error trends over time

## Quick Commands

### Check for Errors

```bash
cd backend
python3 analyze_errors.py
```

Shows summary of all errors (total count, by category, by endpoint).

### View Recent Errors

```bash
python3 analyze_errors.py --recent 10
```

Shows last 10 errors with full details (stack trace, context, request data).

### Detect Patterns

```bash
python3 analyze_errors.py --patterns
```

Identifies:
- High-frequency errors (same error >10 times)
- Critical endpoints (endpoints with >5 errors)
- Error hashes for tracking

### Filter by Category

```bash
python3 analyze_errors.py --category bidding_logic
python3 analyze_errors.py --category play_engine
```

## Monitored Endpoints

Errors are automatically logged for:

1. **`/api/get-next-bid`** - AI bidding decisions
2. **`/api/evaluate-bid`** - User bid evaluation
3. **`/api/play-card`** - User card plays
4. **`/api/get-ai-play`** - AI card plays

## What Gets Logged

Each error includes:
- ✅ Error type and message
- ✅ Full stack trace
- ✅ User ID
- ✅ Endpoint
- ✅ Game context (auction state, contract, vulnerability, etc.)
- ✅ Request data
- ✅ Timestamp
- ✅ Unique error hash for pattern tracking

## Log Files

Located in `backend/logs/`:
- **`errors.jsonl`** - All errors (JSON Lines format)
- **`error_summary.json`** - Aggregated statistics

## Error Categories

Errors are automatically categorized as:
- **`bidding_logic`** - Bidding engine errors
- **`play_engine`** - Card play errors
- **`database`** - Database errors
- **`api`** - API/request errors
- **`performance`** - Timeouts/performance issues

## Example Output

```bash
$ python3 analyze_errors.py

================================================================================
ERROR SUMMARY
================================================================================

Total Errors: 0

================================================================================

✅ No errors logged yet - system is running clean!
```

When errors occur:

```bash
$ python3 analyze_errors.py

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

================================================================================

⚠️  Issues detected! Run with --patterns for details
```

## Workflow

1. **Play the game normally**
2. **Periodically check for errors:**
   ```bash
   python3 analyze_errors.py
   ```
3. **If errors found, investigate patterns:**
   ```bash
   python3 analyze_errors.py --patterns
   ```
4. **View error details:**
   ```bash
   python3 analyze_errors.py --recent 5
   ```
5. **Fix root cause** using stack trace and context
6. **Verify fix** by checking if error hash stops occurring

## Console Alerts

When errors are logged, you'll see in backend console:

```
🚨 ERROR LOGGED: [bidding_logic] ValueError: Invalid bid format
   Hash: a1b2c3d4e5f6 | Endpoint: /api/get-next-bid | User: 42
```

## Benefits

**Before:** Wait for user to report bug → Ask for reproduction steps → Try to recreate → Debug

**After:** Error logged automatically with full context → Check analysis → Fix immediately

**Time saved:** Hours per bug

## Full Documentation

See [docs/features/ERROR_LOGGING_SYSTEM.md](docs/features/ERROR_LOGGING_SYSTEM.md) for:
- Architecture details
- API reference
- Pattern detection algorithms
- Maintenance procedures
- Future enhancements

## Status

- ✅ Backend error logger implemented
- ✅ Server integration complete (4 critical endpoints)
- ✅ Analysis CLI tool ready
- ✅ Pattern detection active
- ✅ Backend server running with error logging enabled
- ⏸️ Frontend error boundary (not needed for core bidding/play focus)
- ⏸️ Email/Slack alerts (future enhancement)
- ⏸️ Error dashboard UI (future enhancement)

## Next Steps

1. Play a few hands to verify system is working
2. Run `python3 analyze_errors.py` to confirm no critical errors
3. If errors appear, use `--patterns` and `--recent` to investigate
4. Fix any recurring issues identified

---

**Questions?** See full documentation at [docs/features/ERROR_LOGGING_SYSTEM.md](docs/features/ERROR_LOGGING_SYSTEM.md)
