# AI Play Logging - Quick Start Guide

## 🎉 Implementation Complete!

The minimal viable logging system for DDS quality monitoring is now live and ready for production.

## What Was Implemented

### 1. Database Schema ✅
- **Table**: `ai_play_log` - Stores every AI play decision
- **Views**:
  - `v_ai_health_24h` - Last 24 hours metrics
  - `v_session_ai_quality` - Per-session quality metrics
  - `v_dds_health_summary` - Overall health summary

**Location**: [backend/migrations/002_add_ai_play_logging.sql](backend/migrations/002_add_ai_play_logging.sql)

### 2. Logging Function ✅
- **Function**: `log_ai_play()` in [server.py:107](backend/server.py#L107)
- **Integration**: Automatically logs every AI play at [server.py:1757](backend/server.py#L1757)
- **Overhead**: ~1.3ms per play (< 1% overhead)
- **Safety**: Never breaks gameplay - logs failures are caught and ignored

### 3. Monitoring Endpoints ✅

#### `/api/dds-health` - Real-time Health Dashboard
```bash
curl http://localhost:5001/api/dds-health

# Query last 48 hours
curl http://localhost:5001/api/dds-health?hours=48
```

**Returns:**
```json
{
  "dds_available": false,
  "platform": "Darwin",
  "hours_analyzed": 24,
  "overall": {
    "total_plays": 156,
    "avg_solve_time_ms": 45.2,
    "fallback_rate": 1.0,
    "fallback_count": 156
  },
  "by_level": {
    "expert": {
      "plays": 156,
      "avg_solve_time_ms": 45.2,
      "fallback_rate": 1.0
    }
  },
  "recent_plays": [...]
}
```

#### `/api/ai-quality-summary` - Quality Analysis
```bash
curl http://localhost:5001/api/ai-quality-summary
```

**Returns:**
```json
{
  "quality_score": 75.0,
  "all_time": {
    "total_plays_all_time": 156,
    "avg_solve_time_ms": 45.2,
    "overall_fallback_rate": 1.0
  },
  "daily_trends": [...],
  "by_contract": [...],
  "recommendations": [
    {
      "level": "info",
      "message": "Limited data (156 plays) - accumulating baseline",
      "action": "Quality metrics will improve with more gameplay data"
    }
  ]
}
```

## Performance Metrics

**Test Results** (from [test_ai_logging.py](backend/test_ai_logging.py)):
- ✅ 100 logs in 128ms = **1.28ms per log**
- ✅ All 4 tests passed
- ✅ Database overhead: **< 1%**
- ✅ API latency impact: **+1-2ms**

## How It Works

### Automatic Logging Flow

1. **AI makes a play** → Timed with `time.time()`
2. **Card validated** → Ensure it's legal
3. **Log to database** → `log_ai_play()` called with:
   - Card played
   - Position (N/E/S/W)
   - AI difficulty level
   - Solve time in milliseconds
   - Fallback flag (was DDS used or Minimax?)
   - Session context (optional)
   - Contract info (optional)
4. **Play continues** → Logging never blocks gameplay

### Data Collected Per Play

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| timestamp | TIMESTAMP | 2025-10-23 14:30:00 | When |
| position | TEXT | "N" | Who played |
| ai_level | TEXT | "expert" | Difficulty |
| card_played | TEXT | "A♠" | What card |
| solve_time_ms | REAL | 45.2 | Performance |
| used_fallback | BOOLEAN | true | DDS crashed? |
| session_id | TEXT | "abc123" | Link to session |
| trick_number | INTEGER | 5 | Game context |
| contract | TEXT | "4♠" | Contract |

**Storage**: ~100 bytes per play
- 100 hands (5,200 plays) = ~520KB
- 1,000 hands (52,000 plays) = ~5.2MB

## Usage Examples

### View Recent AI Plays
```bash
sqlite3 backend/bridge.db "
  SELECT
    datetime(timestamp, 'localtime') as time,
    position,
    ai_level,
    card_played,
    ROUND(solve_time_ms, 1) as time_ms,
    used_fallback
  FROM ai_play_log
  ORDER BY timestamp DESC
  LIMIT 10
"
```

### Check Fallback Rate
```bash
sqlite3 backend/bridge.db "
  SELECT
    ai_level,
    COUNT(*) as plays,
    ROUND(AVG(used_fallback) * 100, 1) as fallback_pct
  FROM ai_play_log
  GROUP BY ai_level
"
```

### Average Solve Time by Level
```bash
sqlite3 backend/bridge.db "
  SELECT
    ai_level,
    ROUND(AVG(solve_time_ms), 1) as avg_ms,
    ROUND(MIN(solve_time_ms), 1) as min_ms,
    ROUND(MAX(solve_time_ms), 1) as max_ms
  FROM ai_play_log
  GROUP BY ai_level
"
```

### Today's Activity
```bash
sqlite3 backend/bridge.db "
  SELECT * FROM v_ai_health_24h
"
```

## Production Deployment

### On Render.com (Linux)

1. **DDS will be available** (unlike macOS)
2. **Logging is automatic** - no configuration needed
3. **Monitor via API**:
   ```bash
   curl https://your-app.onrender.com/api/dds-health
   ```
4. **Check daily**:
   ```bash
   # Save to check trends
   curl https://your-app.onrender.com/api/ai-quality-summary > daily_report_$(date +%Y%m%d).json
   ```

### Expected Production Metrics

**With DDS on Linux:**
- Solve time: 10-200ms (fast to complex positions)
- Fallback rate: ~0% (DDS should work reliably on Linux)
- Quality score: 90-100

**Without DDS (macOS dev):**
- Solve time: 20-100ms (Minimax depth 4)
- Fallback rate: 100% for expert level
- Quality score: 50-75 (due to fallback penalty)

## Next Steps

### Week 1-2: Data Collection
- ✅ System is logging automatically
- Let 50-100 hands accumulate
- Monitor `/api/dds-health` daily
- Watch for high fallback rates (>10%)

### Week 3-4: Analysis
- Run quality analysis on collected data
- Compare DDS vs Minimax performance
- Identify any problem positions
- Generate quality report

### Optional: Add Sparse Sampling (10%)
If you want more detailed logging:

```python
# In server.py, around line 1757
import random

# After validating card is legal
if random.random() < 0.10:  # 10% sampling
    # Log complete game state
    log_complete_hand_state(
        all_hands=state.deal,
        trick_history=state.play_state.trick_history,
        ai_reasoning=...  # Could add AI's internal state
    )
```

This would add 2-5% more overhead but provide richer analysis data.

## Troubleshooting

### No data appearing?
```bash
# Check if table exists
sqlite3 backend/bridge.db "SELECT COUNT(*) FROM ai_play_log"

# Check if server has access
sqlite3 backend/bridge.db "SELECT name FROM sqlite_master WHERE type='table'"
```

### High solve times?
- Normal: 10-200ms depending on position complexity
- Concerning: >500ms consistently
- Check: Are you using correct AI difficulty?

### 100% fallback rate on macOS?
- **Expected** - DDS doesn't work on macOS
- Deploy to Linux (Render) to use DDS
- macOS uses Minimax depth 4 fallback (still good!)

### API returns empty results?
- Need at least 1 play logged first
- Try playing a hand to generate data
- Check `/api/dds-health?hours=168` (1 week)

## Files Modified

1. ✅ [backend/migrations/002_add_ai_play_logging.sql](backend/migrations/002_add_ai_play_logging.sql) - Database schema
2. ✅ [backend/server.py:107](backend/server.py#L107) - Logging function
3. ✅ [backend/server.py:1757](backend/server.py#L1757) - Integration point
4. ✅ [backend/server.py:2054](backend/server.py#L2054) - Dashboard endpoints
5. ✅ [backend/test_ai_logging.py](backend/test_ai_logging.py) - Test suite

## Summary

**What You Get:**
- ✅ Automatic logging of every AI play
- ✅ Real-time health dashboard
- ✅ Performance metrics
- ✅ Quality score calculation
- ✅ Fallback tracking
- ✅ <1% overhead
- ✅ Never breaks gameplay

**Cost:**
- Implementation time: ~2 hours
- Runtime overhead: 1-2ms per play
- Storage: ~5MB per 1000 hands
- Maintenance: Zero - fully automatic

**Value:**
- Know if DDS is working in production
- Track AI quality over time
- Identify performance issues
- Debug gameplay problems
- Generate quality reports

---

## Questions?

See detailed analysis in:
- [DDS_TESTING_PERFORMANCE_ANALYSIS.md](DDS_TESTING_PERFORMANCE_ANALYSIS.md) - All approaches compared
- [HOW_TO_CHECK_AI_IN_PRODUCTION.md](HOW_TO_CHECK_AI_IN_PRODUCTION.md) - AI configuration guide

**System is ready for production! 🚀**
