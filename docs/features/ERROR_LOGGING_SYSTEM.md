# Automated Error Logging System

**Status:** ✅ Implemented (2025-11-02)
**Version:** 1.0
**Focus:** Bidding & Play Engine Error Tracking

## Overview

Automated error logging system that captures, categorizes, and analyzes errors in core game functionality (bidding and card play). Enables proactive bug detection and resolution without manual investigation.

## Architecture

### Components

1. **Backend Error Logger** (`backend/utils/error_logger.py`)
   - Structured JSON logging
   - Automatic error categorization
   - Context capture (auction state, hand data, user info)
   - Pattern detection (recurring errors, high-frequency issues)
   - Error aggregation and summary statistics

2. **Server Integration** (`backend/server.py`)
   - Error logging in critical endpoints:
     - `/api/get-next-bid` - AI bidding errors
     - `/api/evaluate-bid` - Bid evaluation errors
     - `/api/play-card` - User card play errors
     - `/api/get-ai-play` - AI card play errors

3. **Analysis Tool** (`backend/analyze_errors.py`)
   - Command-line error analysis
   - Pattern detection
   - Category filtering
   - Recent error viewing

## Error Categories

Errors are automatically categorized:

- **`bidding_logic`** - Bidding engine errors (conventions, responses, rebids)
- **`play_engine`** - Card play errors (trick evaluation, AI decisions)
- **`database`** - Database connection/query errors
- **`api`** - API endpoint errors
- **`performance`** - Timeout and performance issues

## Error Logging

### What Gets Logged

Each error captures:

```json
{
  "timestamp": "2025-11-02T16:30:15.123",
  "error_type": "ValueError",
  "error_message": "Invalid bid format",
  "category": "bidding_logic",
  "user_id": 42,
  "endpoint": "/api/get-next-bid",
  "traceback": "...",
  "error_hash": "a1b2c3d4e5f6",
  "context": {
    "current_player": "North",
    "auction_length": 5,
    "vulnerability": "NS",
    "has_hand": true
  },
  "request_data": {
    "auction_history": ["1♠", "Pass", "2♥"],
    "current_player": "North"
  }
}
```

### Error Hash

Each error gets a unique hash based on:
- Error type
- Error message
- Stack trace location

This enables **pattern detection** - identifying the same error occurring multiple times.

## Usage

### Viewing Error Summary

```bash
cd backend
python3 analyze_errors.py
```

Output:
```
================================================================================
ERROR SUMMARY
================================================================================

Total Errors: 127

--- Errors by Category ---
  bidding_logic       :   45
  play_engine         :   32
  api                 :   28
  performance         :   22

--- Errors by Endpoint ---
  /api/get-next-bid                       :   45
  /api/play-card                          :   32
  /api/evaluate-bid                       :   28
```

### Viewing Recent Errors

```bash
python3 analyze_errors.py --recent 10
```

Shows last 10 errors with full context and stack traces.

### Detecting Patterns

```bash
python3 analyze_errors.py --patterns
```

Output:
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
  /api/play-card                          : 8 errors
```

### Filtering by Category

```bash
python3 analyze_errors.py --category bidding_logic
```

Shows all bidding-related errors with details.

## Log Files

Error logs are stored in `backend/logs/`:

- **`errors.jsonl`** - All errors (JSON Lines format - one error per line)
- **`error_summary.json`** - Aggregated statistics and pattern data

## Integration Example

### In Backend Code

Error logging is automatic. When an exception occurs in a monitored endpoint, it's automatically logged with full context:

```python
@app.route('/api/get-next-bid', methods=['POST'])
def get_next_bid():
    try:
        # ... bidding logic ...
        bid, explanation = engine.get_next_bid(...)
        return jsonify({'bid': bid, 'explanation': explanation})

    except Exception as e:
        # Automatically logs with context
        log_error(
            error=e,
            endpoint='/api/get-next-bid',
            user_id=data.get('user_id'),
            context={
                'current_player': data.get('current_player'),
                'auction_length': len(data.get('auction_history', [])),
                'vulnerability': state.vulnerability
            },
            request_data=data
        )
        return jsonify({'error': str(e)}), 500
```

### Console Output

When an error is logged, you'll see:
```
🚨 ERROR LOGGED: [bidding_logic] ValueError: Invalid bid format
   Hash: a1b2c3d4e5f6 | Endpoint: /api/get-next-bid | User: 42
```

## Pattern Detection

The system automatically detects:

1. **High Frequency Errors** - Same error occurring >10 times
2. **Critical Endpoints** - Endpoints with >5 errors
3. **Recent Spikes** - Sudden increase in error rate (future enhancement)
4. **Affected Users** - Users encountering multiple errors (future enhancement)

## Benefits

### Proactive Bug Detection

Instead of waiting for user reports:
- ✅ Errors are logged immediately with full context
- ✅ Patterns are detected automatically
- ✅ Recurring issues are highlighted
- ✅ Root causes are easier to identify

### Faster Debugging

Error logs include:
- Full stack traces
- Request data (auction history, hand state)
- Game context (vulnerability, dealer, contract)
- User information
- Timestamp and error hash

### Continuous Monitoring

Run analysis periodically:
```bash
# Check for new errors
python3 analyze_errors.py

# If errors found, investigate patterns
python3 analyze_errors.py --patterns

# View specific error details
python3 analyze_errors.py --recent 5
```

## Example Workflow

**1. Error occurs during gameplay**
```
User bids 3NT → Backend error → Automatically logged
```

**2. Analyze errors periodically**
```bash
python3 analyze_errors.py
# Shows: 15 new bidding_logic errors
```

**3. Detect patterns**
```bash
python3 analyze_errors.py --patterns
# Shows: Error hash a1b2c3 occurred 12 times
```

**4. View error details**
```bash
python3 analyze_errors.py --recent 1
# Shows: Full stack trace, context, request data
```

**5. Fix root cause**
```
Identify bug in convention module → Fix code → Deploy
```

**6. Verify fix**
```bash
python3 analyze_errors.py --patterns
# Should show: Error hash a1b2c3 stopped occurring
```

## Future Enhancements

Potential improvements:

1. **Email/Slack Alerts** - Automatic notifications for critical errors
2. **Error Dashboard** - Web UI for error visualization
3. **Trend Analysis** - Error rate over time graphs
4. **User Impact Analysis** - Which users are affected by which errors
5. **Automatic Bug Report Generation** - Convert patterns into GitHub issues
6. **Performance Metrics** - Endpoint response time tracking
7. **Error Recovery Suggestions** - AI-generated fix suggestions

## API Reference

### `log_error(error, context, user_id, endpoint, request_data)`

Logs an error with full context.

**Parameters:**
- `error` (Exception) - The exception that occurred
- `context` (dict) - Additional context (auction state, hand data, etc.)
- `user_id` (int, optional) - User who encountered error
- `endpoint` (str, optional) - API endpoint where error occurred
- `request_data` (dict, optional) - Request payload

**Example:**
```python
from utils.error_logger import log_error

try:
    # ... code ...
except Exception as e:
    log_error(
        error=e,
        endpoint='/api/evaluate-bid',
        user_id=user_id,
        context={'auction_length': len(auction), 'player': 'South'},
        request_data=data
    )
```

### `get_error_summary()`

Returns aggregated error statistics.

**Returns:** Dictionary with total errors, counts by category, counts by endpoint, error hashes, etc.

### `get_recent_errors(limit=50)`

Returns most recent errors.

**Parameters:**
- `limit` (int) - Number of recent errors to return

**Returns:** List of error dictionaries

### `detect_error_patterns()`

Detects recurring error patterns.

**Returns:** Dictionary with:
- `high_frequency_errors` - Errors occurring >10 times
- `critical_endpoints` - Endpoints with >5 errors
- `recent_spikes` - Errors with sudden increase
- `affected_users` - Users encountering multiple errors

## Related Documentation

- **Testing Guide:** `docs/guides/TESTING_GUIDE.md` - Quality assurance protocols
- **Quality Scores:** `CLAUDE.md` - Bidding/play quality score requirements
- **Bug Tracking:** `docs/bug-fixes/` - Bug fix documentation

## Maintenance

### Cleaning Old Logs

Error logs grow over time. Periodically clean old entries:

```bash
# Archive logs older than 30 days
cd backend/logs
mv errors.jsonl errors_archive_$(date +%Y%m%d).jsonl
touch errors.jsonl

# Reset summary
rm error_summary.json
```

### Monitoring Best Practices

1. **Daily:** Check for new high-frequency errors
   ```bash
   python3 analyze_errors.py --patterns
   ```

2. **After deployments:** Verify no new error spikes
   ```bash
   python3 analyze_errors.py --recent 20
   ```

3. **Weekly:** Review error trends and fix recurring issues
   ```bash
   python3 analyze_errors.py
   ```

## Troubleshooting

**Q: No errors showing but I know errors occurred**

A: Check that backend restarted after adding error logging:
```bash
lsof -ti:5001 | xargs kill
cd backend && source venv/bin/activate && python3 server.py
```

**Q: Error logs taking too much disk space**

A: Archive old logs periodically (see Maintenance section above)

**Q: Want to log custom errors**

A: Use `log_error()` directly in your code:
```python
from utils.error_logger import log_error

try:
    # Your code
except Exception as e:
    log_error(error=e, context={'custom_field': 'value'})
```

## Version History

- **1.0** (2025-11-02) - Initial implementation
  - Structured JSON logging
  - Error categorization
  - Pattern detection
  - Analysis CLI tool
  - Integration with bidding/play endpoints
