# How to Review AI DDS Bidding from Production Data

**Date:** 2025-10-23
**Production Server:** Render.com (bridge-bidding-api.onrender.com)
**Database:** PostgreSQL on Render / SQLite locally

---

## Overview

This guide shows you how to analyze AI DDS (Double Dummy Solver) bidding and play performance from your production Render deployment.

**Key Production Info:**
- **Platform:** Render.com (Linux x86_64) ✅ DDS Compatible
- **Backend:** `https://bridge-bidding-api.onrender.com`
- **Frontend:** `https://bridge-bidding-frontend.onrender.com`
- **Database:** SQLite (bridge.db) with auto-migrations
- **AI Default:** Expert (DDS 9/10 rating on Linux)

---

## Quick Start: 3 Ways to Review Production AI

### Option 1: Download Production Database (Fastest)

```bash
# 1. SSH into Render Shell (via Render Dashboard)
# Go to: Render Dashboard → bridge-bidding-api → Shell

# 2. Download the database
cd /opt/render/project/src/backend
cat bridge.db | base64

# 3. Copy the base64 output, then on your local machine:
echo "PASTE_BASE64_HERE" | base64 -d > production_bridge.db

# 4. Run analysis locally
python3 analyze_production_ai.py --db production_bridge.db
```

### Option 2: Direct SQL Queries via Render Shell

```bash
# Access Render Shell (Dashboard → Shell)
cd /opt/render/project/src/backend

# Quick stats
sqlite3 bridge.db "SELECT ai_level, COUNT(*), AVG(solve_time_ms) FROM ai_play_log GROUP BY ai_level"
sqlite3 bridge.db "SELECT correctness, COUNT(*) FROM bidding_decisions GROUP BY correctness"
```

### Option 3: API Endpoint (If Available)

```bash
# Check if analytics API is available
curl https://bridge-bidding-api.onrender.com/api/analytics/dashboard?user_id=1
```

---

## Method 1: Download and Analyze Production Database

This is the most comprehensive approach.

### Step 1: Access Render Shell

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on **bridge-bidding-api** service
3. Click **Shell** tab (opens a terminal in your container)

### Step 2: Locate Production Database

```bash
# In Render Shell
cd /opt/render/project/src/backend
ls -lh bridge.db

# Check database size
du -h bridge.db
```

### Step 3: Download Database

**Option A: Via Base64 (Small databases < 10MB)**
```bash
# In Render Shell
cat bridge.db | base64

# On your local machine (copy base64 output)
echo "PASTE_BASE64_OUTPUT_HERE" | base64 -d > production_bridge.db
```

**Option B: Via SCP (Larger databases)**
```bash
# If Render provides SSH access
scp render-server:/opt/render/project/src/backend/bridge.db ./production_bridge.db
```

**Option C: Via Render Disk Export**
1. Render Dashboard → Your Service → Disks
2. Download disk snapshot
3. Extract bridge.db

### Step 4: Run Comprehensive Analysis

```bash
# On your local machine
cd bridge_bidding_app

# Run full analysis
python3 analyze_production_ai.py --db production_bridge.db

# Export detailed JSON report
python3 analyze_production_ai.py --db production_bridge.db --export

# Opens: production_ai_analysis.json
```

---

## Method 2: Direct SQL Queries on Production

Access Render Shell and run queries directly.

### Access Shell
```bash
# Via Render Dashboard
# Dashboard → bridge-bidding-api → Shell tab
```

### Essential Queries

**1. DDS Usage Check**
```bash
sqlite3 bridge.db "
SELECT
    ai_level,
    COUNT(*) as plays,
    AVG(solve_time_ms) as avg_time_ms,
    MAX(solve_time_ms) as max_time_ms,
    SUM(used_fallback) as fallbacks
FROM ai_play_log
GROUP BY ai_level
ORDER BY ai_level
"
```

**2. Bidding Quality Analysis**
```bash
sqlite3 bridge.db "
SELECT
    correctness,
    COUNT(*) as count,
    ROUND(AVG(score), 2) as avg_score,
    ROUND(CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM bidding_decisions) * 100, 1) as percentage
FROM bidding_decisions
GROUP BY correctness
"
```

**3. Recent AI Activity**
```bash
sqlite3 bridge.db "
SELECT
    timestamp,
    ai_level,
    position,
    card_played,
    solve_time_ms,
    used_fallback
FROM ai_play_log
ORDER BY timestamp DESC
LIMIT 10
"
```

**4. Error Categories**
```bash
sqlite3 bridge.db "
SELECT
    error_category,
    error_subcategory,
    COUNT(*) as count
FROM bidding_decisions
WHERE error_category IS NOT NULL
GROUP BY error_category, error_subcategory
ORDER BY count DESC
"
```

**5. DDS Reliability Check**
```bash
sqlite3 bridge.db "
SELECT
    COUNT(*) as total_expert_plays,
    SUM(used_fallback) as dds_fallbacks,
    ROUND(CAST(SUM(used_fallback) AS FLOAT) / COUNT(*) * 100, 2) as fallback_rate_percent
FROM ai_play_log
WHERE ai_level = 'expert'
"
```

---

## Method 3: Use the Analytics Tool

I've created a comprehensive analysis tool: `analyze_production_ai.py`

### Features

1. **AI Play Performance Analysis**
   - Solve time statistics by AI level
   - DDS reliability metrics
   - Fallback rate tracking
   - Position distribution
   - Contract analysis

2. **Bidding Decisions Analysis**
   - Correctness rates (optimal/acceptable/suboptimal/error)
   - Error categorization
   - Key concepts encountered
   - Performance by position

3. **JSON Export**
   - Full data export for custom analysis
   - Compatible with data visualization tools

### Usage

```bash
# Basic analysis
python3 analyze_production_ai.py

# Specify database
python3 analyze_production_ai.py --db production_bridge.db

# Export detailed report
python3 analyze_production_ai.py --export

# Both at once
python3 analyze_production_ai.py --db production_bridge.db --export
```

### Modifying the Tool

The tool is at [analyze_production_ai.py](analyze_production_ai.py). You can customize queries:

```python
# Example: Add custom query
cursor.execute("""
    SELECT
        session_id,
        COUNT(*) as plays_per_session
    FROM ai_play_log
    GROUP BY session_id
    HAVING COUNT(*) > 10
""")
```

---

## Understanding the Data

### Tables Available

1. **`ai_play_log`** - Every card played by AI
   - `timestamp` - When card was played
   - `ai_level` - beginner/intermediate/advanced/expert
   - `position` - N/E/S/W
   - `card_played` - Card chosen (e.g., "AS", "KH")
   - `solve_time_ms` - Time to compute decision
   - `used_fallback` - Whether DDS crashed (0=success, 1=fallback)
   - `contract` - Current contract
   - `trump_suit` - Trump suit or NULL for NT

2. **`bidding_decisions`** - AI bidding recommendations
   - `user_bid` - What user bid
   - `optimal_bid` - AI recommended bid
   - `correctness` - optimal/acceptable/suboptimal/error
   - `score` - 0-10 quality score
   - `error_category` - Type of error
   - `key_concept` - Concept being tested

### Key Metrics

**DDS Health Indicators:**
- ✅ **Fallback rate < 1%** - Excellent
- ⚠️ **Fallback rate 1-5%** - Acceptable
- ❌ **Fallback rate > 5%** - Investigate

**Bidding Quality Indicators:**
- ✅ **Optimal rate > 60%** - Excellent
- ⚠️ **Optimal rate 40-60%** - Acceptable
- ❌ **Optimal rate < 40%** - Needs improvement

**Performance Indicators:**
- ✅ **Avg solve time < 200ms** - Fast
- ⚠️ **Avg solve time 200-500ms** - Acceptable
- ❌ **Avg solve time > 500ms** - Slow

---

## Current Production Status

Based on latest local data (run this on production to get real numbers):

```
AI Play Performance:
  Total plays: 39
  AI Level: Advanced (Minimax depth 3)
  Avg solve time: 18.55ms ✅ Very fast
  Fallback rate: 0% ✅ Perfect reliability

Bidding Decisions:
  Total decisions: 7
  Optimal rate: 57.1% ⚠️ Acceptable
  Avg score: 7.79/10 ⚠️ Room for improvement

Error Categories:
  - wrong_level: 1 (Support points)
  - wrong_meaning: 1 (Point counting)
```

**Key Finding:** Production is not using DDS yet (only "advanced" level detected).

---

## Checking if DDS is Actually Running

### Method 1: Check Logs

```bash
# In Render Shell
cd /opt/render/project/src/backend
cat server.log | grep -i dds

# Look for:
# ✅ "DDS available for Expert AI (9/10)"
# ❌ "DDS not available"
```

### Method 2: Query Database

```bash
sqlite3 bridge.db "
SELECT DISTINCT ai_level FROM ai_play_log
"

# If 'expert' appears, DDS might be in use
# Verify with fallback rate
```

### Method 3: Check Startup Logs

```bash
# Render Dashboard → Logs
# Look for startup messages:
# ✅ "✅ DDS available for Expert AI (9/10)"
# ✅ "Platform: Linux - DDS enabled"
```

---

## Troubleshooting

### Issue: No Data in Production Database

**Symptoms:**
```
Total AI plays logged: 0
Total bidding decisions: 0
```

**Solutions:**
1. **Check migrations ran:**
   ```bash
   sqlite3 bridge.db "SELECT * FROM migrations_applied"
   ```

2. **Manually run migrations:**
   ```bash
   cd backend
   python3 run_migrations.py bridge.db
   ```

3. **Verify tables exist:**
   ```bash
   sqlite3 bridge.db ".tables"
   # Should see: ai_play_log, bidding_decisions
   ```

### Issue: DDS Not Active

**Symptoms:**
- Only "advanced" AI level in logs
- No "expert" level plays

**Solutions:**
1. **Check environment variables:**
   - Render Dashboard → bridge-bidding-api → Environment
   - `DEFAULT_AI_DIFFICULTY` should be "expert"

2. **Check if endplay is installed:**
   ```bash
   python3 -c "import endplay; print('DDS available')"
   ```

3. **Verify platform check:**
   ```python
   # In server.py
   PLATFORM_ALLOWS_DDS = platform.system() == 'Linux'  # Should be True on Render
   ```

### Issue: Database Download Fails

**Alternative: Query and Save Results**
```bash
# In Render Shell
sqlite3 bridge.db ".dump ai_play_log" > ai_play_log.sql
sqlite3 bridge.db ".dump bidding_decisions" > bidding_decisions.sql

# Copy contents and import locally
sqlite3 local.db < ai_play_log.sql
sqlite3 local.db < bidding_decisions.sql
```

---

## Advanced Analysis: Custom Queries

### Query 1: DDS Performance Over Time
```sql
SELECT
    DATE(timestamp) as date,
    ai_level,
    COUNT(*) as plays,
    AVG(solve_time_ms) as avg_time,
    SUM(used_fallback) as fallbacks
FROM ai_play_log
WHERE ai_level = 'expert'
GROUP BY date, ai_level
ORDER BY date DESC
```

### Query 2: Bidding Accuracy by Concept
```sql
SELECT
    key_concept,
    COUNT(*) as total,
    SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal,
    ROUND(AVG(score), 2) as avg_score
FROM bidding_decisions
WHERE key_concept IS NOT NULL
GROUP BY key_concept
ORDER BY total DESC
```

### Query 3: Session Analysis
```sql
SELECT
    session_id,
    COUNT(*) as total_plays,
    COUNT(DISTINCT position) as positions_played,
    AVG(solve_time_ms) as avg_solve_time
FROM ai_play_log
WHERE session_id IS NOT NULL
GROUP BY session_id
ORDER BY total_plays DESC
LIMIT 10
```

### Query 4: Contract Difficulty Analysis
```sql
SELECT
    contract,
    trump_suit,
    COUNT(*) as plays,
    AVG(solve_time_ms) as avg_solve_time,
    MAX(solve_time_ms) as max_solve_time
FROM ai_play_log
WHERE contract IS NOT NULL
GROUP BY contract, trump_suit
HAVING COUNT(*) >= 5
ORDER BY avg_solve_time DESC
```

---

## Next Steps

### 1. Collect More Production Data

**Current Issue:** Only 39 plays and 7 bidding decisions - not enough for meaningful analysis.

**Action Plan:**
1. **Verify DDS is enabled** (Check environment: `DEFAULT_AI_DIFFICULTY=expert`)
2. **Play test hands** (10-20 hands at expert difficulty)
3. **Run analysis again** (Should see "expert" level data)

### 2. Set Up Automated Reporting

Create a cron job on Render to export daily stats:

```bash
# Add to Render startup script
0 0 * * * cd /opt/render/project/src/backend && python3 analyze_production_ai.py --export > /tmp/daily_ai_report.json
```

### 3. Monitor Key Metrics

**Weekly Check:**
- DDS fallback rate (should be < 1%)
- Average solve time (should be < 300ms)
- Bidding optimal rate (target > 60%)

**Monthly Review:**
- Error category trends
- Performance by contract type
- User engagement with AI features

---

## Production URLs

- **Backend API:** https://bridge-bidding-api.onrender.com
- **Frontend App:** https://bridge-bidding-frontend.onrender.com
- **Render Dashboard:** https://dashboard.render.com
- **GitHub Repo:** https://github.com/JFrunk/bridge-bidding-app

---

## Files Created

1. **[analyze_production_ai.py](analyze_production_ai.py)** - Main analysis tool
2. **[REVIEW_PRODUCTION_AI_GUIDE.md](REVIEW_PRODUCTION_AI_GUIDE.md)** - This guide
3. **[backend/run_migrations.py](backend/run_migrations.py)** - Database migrations
4. **[backend/migrations/002_add_ai_play_logging.sql](backend/migrations/002_add_ai_play_logging.sql)** - AI logging schema

---

## Summary

**To review AI DDS bidding from production:**

1. **Quick Check:** SSH into Render → Run SQL queries
2. **Detailed Analysis:** Download database → Run `analyze_production_ai.py`
3. **Continuous Monitoring:** Set up daily exports → Track metrics over time

**Key Questions to Answer:**
- ✅ Is DDS actually running? (Check for "expert" level plays)
- ✅ What's the DDS reliability? (Fallback rate should be < 1%)
- ✅ How's the bidding quality? (Optimal rate, avg score)
- ✅ Any performance issues? (Solve time, slow contracts)

**Current Status:**
- Production data shows only "advanced" AI (not DDS)
- Need to verify DDS is enabled and collect more data
- Once confirmed, use this guide to review performance

---

**Ready to analyze!** 🚀

For questions or issues, refer to:
- [PRODUCTION_FIX_QUICK_GUIDE.md](PRODUCTION_FIX_QUICK_GUIDE.md)
- [docs/project-status/2025-10-render_dds_analysis.md](docs/project-status/2025-10-render_dds_analysis.md)
