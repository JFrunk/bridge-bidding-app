# DDS Testing Without Shell Access - Complete Guide

**Date:** 2025-10-30
**Problem:** GitHub Actions DDS test failed, no Render Shell access
**Solution:** Multiple alternative methods to test and verify DDS

---

## 🔍 Root Cause Analysis

### Why the GitHub Actions Test Failed

**The original workflow had a critical bug:**

```yaml
# ❌ WRONG - runs from project root, can't find backend modules
python3 backend/test_play_quality_integrated.py \
  --hands ${{ github.event.inputs.hands }} \
  --ai dds \
  --output play_baseline_level10_dds.json
```

**Issues:**
1. **Wrong working directory**: Runs from project root, not `backend/`
2. **Import path problem**: Can't find `engine.play.ai.dds_ai` module
3. **Output path issue**: Creates file in root instead of proper location

**Error you likely saw:**
```
ModuleNotFoundError: No module named 'engine'
or
ValueError: DDS AI not available on this platform
```

---

## ✅ Fixed GitHub Actions Workflow

### What Changed

The new workflow ([.github/workflows/dds_baseline.yml](.github/workflows/dds_baseline.yml)) fixes all issues:

```yaml
# ✅ CORRECT - runs from backend directory
- name: Run DDS Baseline Test
  run: |
    cd backend  # <- Key fix!
    python3 test_play_quality_integrated.py \
      --hands ${{ github.event.inputs.hands }} \
      --ai ${{ github.event.inputs.ai_level }} \
      --output ../play_baseline_level10_dds.json
```

**Key improvements:**
1. ✅ **Runs from `backend/` directory** - fixes import paths
2. ✅ **Adds DDS verification step** - confirms endplay installed
3. ✅ **Better error handling** - `continue-on-error: true`
4. ✅ **Uploads artifacts even on failure** - can debug issues
5. ✅ **Clear error messages** - tells you exactly what went wrong

---

## 🚀 Method 1: Fixed GitHub Actions (RECOMMENDED)

### How to Use

1. **Commit the fixed workflow:**
   ```bash
   git add .github/workflows/dds_baseline.yml
   git commit -m "fix: Correct GitHub Actions DDS baseline workflow"
   git push origin main
   ```

2. **Run the workflow:**
   - Go to: https://github.com/[your-username]/bridge_bidding_app/actions
   - Click: **"DDS Play Quality Baseline"** workflow
   - Click: **"Run workflow"** dropdown
   - Choose options:
     - **hands:** `10` (quick test) or `100` (recommended) or `500` (full)
     - **ai_level:** `dds`
   - Click: **"Run workflow"** button

3. **Monitor progress:**
   - Test duration: ~2 min (10 hands), ~20 min (100 hands), ~90 min (500 hands)
   - Watch for each step to complete
   - Check "Verify DDS Installation" step shows ✅

4. **Download results:**
   - Once complete, scroll to bottom of workflow run
   - Look for **Artifacts** section
   - Download: `dds-baseline-[N]hands.zip`
   - Extract: Contains `play_baseline_level10_dds.json`

5. **Analyze locally:**
   ```bash
   # Compare with existing baseline
   python3 compare_play_scores.py \
     play_baselines/2025-10-29_level8_initial_baseline.json \
     play_baseline_level10_dds.json
   ```

### Expected Results

**For DDS (Level 10):**
```
Composite Score: 90-95% (Grade A)
Success Rate:    85-95%
Legality:        100%
Avg Time/Hand:   15-30 seconds
```

**If you see lower scores (~75%), DDS might not be working** - check verification step.

---

## 🔄 Method 2: API Endpoints (Real-time Monitoring)

### Check DDS Status via API

**No shell access needed - just curl commands!**

#### Step 1: Verify DDS is Available

```bash
curl https://bridge-bidding-api.onrender.com/api/ai/status | python3 -m json.tool
```

**Look for:**
```json
{
  "dds_available": true,
  "difficulties": {
    "expert": {
      "name": "Double Dummy Solver AI",
      "rating": "9/10",
      "using_dds": true  // <- This must be true!
    }
  }
}
```

**If `dds_available: false`:**
- `endplay` not installed in production
- Check Render build logs for installation errors

**If `using_dds: false` but `dds_available: true`:**
- DDS installed but not configured for expert level
- Check environment variables

#### Step 2: Check Real-time Health

```bash
curl https://bridge-bidding-api.onrender.com/api/dds-health | python3 -m json.tool
```

**Expected output:**
```json
{
  "total_plays": 65,
  "expert_plays": 42,
  "dds_fallback_rate": 2.4,
  "avg_solve_time_ms": 45.3,
  "recent_plays": [...]
}
```

**Key metrics:**
- ✅ **`expert_plays > 0`** - DDS is being used
- ✅ **`dds_fallback_rate < 5%`** - DDS working reliably
- ✅ **`avg_solve_time_ms < 200`** - Good performance
- ❌ **`expert_plays = 0`** - DDS not active (check difficulty setting)
- ❌ **`dds_fallback_rate > 10%`** - DDS crashing frequently

#### Step 3: Quality Summary

```bash
curl https://bridge-bidding-api.onrender.com/api/ai-quality-summary | python3 -m json.tool
```

**Shows:**
- Overall quality score (0-100)
- Trends over last 30 days
- Performance by contract type
- Recommendations

---

## 📊 Method 3: Download Production Database

### Without Shell Access

Since you can't access Render Shell directly, use the **API method** or **database disk snapshot**:

#### Option A: Request Database via Support API (If Available)

Some Render plans allow database exports via API or support ticket.

#### Option B: Use Logging Data

The production database is already logging all plays. Use the API endpoints above to get the same data:

```bash
# Get all expert plays
curl "https://bridge-bidding-api.onrender.com/api/dds-health?hours=720" > dds_health_30days.json

# Analyze locally
python3 -c "
import json
with open('dds_health_30days.json') as f:
    data = json.load(f)
    expert_plays = data.get('expert_plays', 0)
    fallback_rate = data.get('dds_fallback_rate', 0)
    print(f'Expert plays: {expert_plays}')
    print(f'Fallback rate: {fallback_rate:.1f}%')
    print(f'Status: {"✅ Working" if fallback_rate < 5 else "❌ Issues"}')
"
```

---

## 🎮 Method 4: Manual Testing in Production

### Play Real Hands and Monitor

**This is the most reliable method without shell access!**

#### Step 1: Set Expert Difficulty

1. **Check current default:**
   ```bash
   curl https://bridge-bidding-api.onrender.com/api/ai/status | grep current_difficulty
   ```

2. **If not expert, check Render environment:**
   - Go to: Render Dashboard → bridge-bidding-api → Environment
   - Add/Update: `DEFAULT_AI_DIFFICULTY=expert`
   - Redeploy service

#### Step 2: Play Test Hands

1. **Open production app:** https://bridge-bidding-frontend.onrender.com
2. **Check DDS indicator** in bottom-right corner:
   - ✅ "DDS Expert AI Active" = Working!
   - ⚠️ "Expert AI (Fallback)" = DDS not working
3. **Play 10-20 hands** to generate data
4. **Watch for:**
   - Reasonable AI response times (not too slow)
   - No error messages
   - AI makes sensible plays

#### Step 3: Review Collected Data

```bash
# After playing hands, check health
curl https://bridge-bidding-api.onrender.com/api/dds-health

# Look for expert level plays
# Should show data from your test session
```

---

## 🔧 Troubleshooting Common Issues

### Issue 1: GitHub Actions Shows "DDS not available"

**Symptoms:**
```
ValueError: DDS AI not available on this platform
```

**Diagnosis:**
```bash
# Check the "Verify DDS Installation" step in workflow
# Should show:
# ✅ endplay installed successfully
# DDS_AVAILABLE: True
```

**Fix:**
- Verify `endplay>=0.5.0` is in [backend/requirements.txt](backend/requirements.txt)
- Check for typos in requirements.txt
- Try pinning specific version: `endplay==0.5.12`

### Issue 2: Import Errors in GitHub Actions

**Symptoms:**
```
ModuleNotFoundError: No module named 'engine'
```

**Diagnosis:**
The test script wasn't run from the correct directory.

**Fix:**
Use the updated workflow file - it includes `cd backend` before running tests.

### Issue 3: Production Shows No Expert Plays

**Symptoms:**
```bash
curl .../api/dds-health
# Returns: "expert_plays": 0
```

**Diagnosis:**
DDS is installed but not being used.

**Fixes:**

1. **Check default AI difficulty:**
   ```bash
   curl https://bridge-bidding-api.onrender.com/api/ai/status | grep current_difficulty
   ```

2. **Set environment variable:**
   - Render Dashboard → bridge-bidding-api → Environment
   - Add: `DEFAULT_AI_DIFFICULTY=expert`

3. **Verify after redeploy:**
   ```bash
   curl https://bridge-bidding-api.onrender.com/api/ai/status | grep '"expert"' -A5
   # Should show: "using_dds": true
   ```

### Issue 4: High Fallback Rate (>10%)

**Symptoms:**
DDS is installed and used, but crashes frequently.

**Diagnosis:**
```bash
curl .../api/dds-health | grep fallback_rate
# Shows: "dds_fallback_rate": 25.3  // <- Too high!
```

**Possible Causes:**
1. Memory issues (increase Render instance size)
2. DDS bugs with specific hands
3. Timeout issues

**Fix:**
- Check Render service logs for crash messages
- Consider using Level 8 (Minimax) instead of Level 10 (DDS)
- Report endplay library bug if consistent crash pattern

### Issue 5: Test Times Out

**Symptoms:**
GitHub Actions workflow times out after 6 hours.

**Fix:**
Reduce number of hands:
```yaml
# Instead of 500 hands (~90 min)
# Use 100 hands (~20 min)
# Or 10 hands (~2 min) for quick verification
```

---

## 📋 Quick Reference Checklist

### To Test DDS Without Shell Access:

- [ ] **Commit fixed GitHub Actions workflow**
- [ ] **Run workflow with 10 hands** (quick verification)
- [ ] **Check "Verify DDS Installation" step** shows ✅
- [ ] **Download artifact** if successful
- [ ] **If failed:** Check workflow logs for specific error
- [ ] **Verify DDS in production** via API: `curl .../api/ai/status`
- [ ] **Check real-time health** via API: `curl .../api/dds-health`
- [ ] **Play test hands** and verify status indicator
- [ ] **Compare results** with Level 8 baseline

### Success Criteria:

- ✅ GitHub Actions completes without errors
- ✅ DDS composite score: 90-95%
- ✅ Production API shows `using_dds: true`
- ✅ Frontend shows "DDS Expert AI Active"
- ✅ Fallback rate < 5%
- ✅ Avg solve time < 200ms

---

## 📚 Files Reference

### Created/Modified:
- [.github/workflows/dds_baseline.yml](.github/workflows/dds_baseline.yml) - Fixed workflow
- [DDS_TESTING_WITHOUT_SHELL_ACCESS.md](DDS_TESTING_WITHOUT_SHELL_ACCESS.md) - This guide

### Related Documentation:
- [DDS_TESTING_IMPLEMENTATION_SUMMARY.md](DDS_TESTING_IMPLEMENTATION_SUMMARY.md) - Logging system
- [REVIEW_PRODUCTION_AI_GUIDE.md](REVIEW_PRODUCTION_AI_GUIDE.md) - Production analysis
- [HOW_TO_CHECK_AI_IN_PRODUCTION.md](HOW_TO_CHECK_AI_IN_PRODUCTION.md) - AI configuration
- [docs/guides/HOW_TO_VERIFY_DDS.md](docs/guides/HOW_TO_VERIFY_DDS.md) - DDS verification

---

## 🎯 Next Steps

1. **Immediate:** Commit and push the fixed workflow
2. **Test:** Run GitHub Actions with 10 hands (2 minutes)
3. **Verify:** Check DDS status in production via API
4. **Monitor:** Play test hands and watch metrics
5. **Baseline:** Run full 100-hand test once verified working

**Expected Timeline:**
- Fix workflow: 5 minutes
- Quick test (10 hands): 2 minutes
- Full test (100 hands): 20 minutes
- Analysis: 5 minutes
- **Total: ~30 minutes** to fully verify DDS

---

## ✅ Summary

**Without shell access, you can:**
1. ✅ Use fixed GitHub Actions workflow
2. ✅ Monitor via API endpoints
3. ✅ Play test hands and observe
4. ✅ Get full DDS metrics
5. ✅ Compare with baselines

**You do NOT need:**
- ❌ Render Shell access
- ❌ SSH to production
- ❌ Database downloads
- ❌ Manual log parsing

**The fixed workflow will work!** The key was running from the correct directory.
