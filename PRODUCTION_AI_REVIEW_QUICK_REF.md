# Production AI Review - Quick Reference Card

**Date:** 2025-10-23

---

## TL;DR - 3 Steps to Review Production AI

```bash
# 1. Access Render Shell
#    Go to: https://dashboard.render.com
#    Click: bridge-bidding-api → Shell

# 2. Download database (in Render Shell)
cd /opt/render/project/src/backend
cat bridge.db | base64
# Copy the output

# 3. On your local machine
echo "PASTE_BASE64_HERE" | base64 -d > production.db
python3 analyze_production_ai.py --db production.db --export
```

---

## Quick SQL Queries (Run in Render Shell)

```bash
# Is DDS running?
sqlite3 bridge.db "SELECT DISTINCT ai_level FROM ai_play_log"
# Look for 'expert' = DDS active

# DDS reliability
sqlite3 bridge.db "
SELECT
    COUNT(*) as plays,
    SUM(used_fallback) as crashes,
    ROUND(AVG(solve_time_ms), 1) as avg_ms
FROM ai_play_log
WHERE ai_level = 'expert'"

# Bidding quality
sqlite3 bridge.db "
SELECT
    correctness,
    COUNT(*)
FROM bidding_decisions
GROUP BY correctness"

# Recent activity
sqlite3 bridge.db "
SELECT
    timestamp,
    ai_level,
    solve_time_ms
FROM ai_play_log
ORDER BY timestamp DESC
LIMIT 5"
```

---

## Analysis Tool Usage

```bash
# Default (local database)
python3 analyze_production_ai.py

# Specify database
python3 analyze_production_ai.py --db production.db

# Export JSON report
python3 analyze_production_ai.py --db production.db --export
```

---

## Key Metrics to Check

### ✅ DDS Health
- **Fallback rate:** < 1% is excellent
- **Avg solve time:** < 300ms is good
- **AI level:** Should see "expert" in production

### ✅ Bidding Quality
- **Optimal rate:** > 60% is excellent
- **Avg score:** > 7.5/10 is good
- **Error rate:** < 20% is acceptable

### ✅ Data Volume
- **Need:** 50+ plays for meaningful analysis
- **Current:** 39 plays (need more data)

---

## Common Issues

### Issue: No expert level data
**Fix:** Check `DEFAULT_AI_DIFFICULTY=expert` in Render env vars

### Issue: High fallback rate
**Cause:** DDS crashing (shouldn't happen on Linux)
**Fix:** Check Render logs for errors

### Issue: No data at all
**Fix:** Run migrations: `python3 run_migrations.py bridge.db`

---

## Files

- **Analysis Tool:** [analyze_production_ai.py](analyze_production_ai.py)
- **Full Guide:** [REVIEW_PRODUCTION_AI_GUIDE.md](REVIEW_PRODUCTION_AI_GUIDE.md)
- **DDS Info:** [docs/project-status/2025-10-render_dds_analysis.md](docs/project-status/2025-10-render_dds_analysis.md)

---

## Production URLs

- **Backend:** https://bridge-bidding-api.onrender.com
- **Frontend:** https://bridge-bidding-frontend.onrender.com
- **Dashboard:** https://dashboard.render.com

---

## Next Steps

1. ✅ Verify DDS is enabled (check env vars)
2. 🎮 Play 20+ test hands at expert difficulty
3. 📊 Download database and run analysis
4. 📈 Review metrics and trends

**Goal:** Confirm DDS is working optimally in production (9/10 AI rating)
