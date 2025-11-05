# How to Verify DDS is Running in Production

**Quick Answer:** Use the 3-step verification protocol below.

**Last Updated:** 2025-11-03

---

## 3-Step Verification Protocol

### ✅ Step 1: Check Backend Logs (2 minutes)

**Where:** Render Dashboard → Your backend service → Logs

**What to look for:**
```
✅ DDS AI loaded for expert difficulty (9/10 rating)
```

**Good signs:**
- ✅ `Successfully installed endplay-0.5.12` in build logs
- ✅ `DDS AI loaded` message in startup logs
- ✅ No import errors or warnings about DDS

**Bad signs:**
- ❌ `⚠️ Using Minimax D4 for expert (DDS not available)`
- ❌ `ImportError: endplay` or `ModuleNotFoundError`
- ❌ No mention of DDS in logs

---

### ✅ Step 2: Test the API Endpoint (30 seconds)

**Method A: Using curl (command line)**

```bash
# Replace with your actual backend URL
curl https://your-backend-url.onrender.com/api/ai/status
```

**Method B: Using browser**

Open this URL directly in your browser:
```
https://your-backend-url.onrender.com/api/ai/status
```

**Expected Response:**
```json
{
  "dds_available": true,
  "difficulties": {
    "beginner": {
      "name": "Simple Play AI",
      "rating": "6/10",
      "description": "Basic card play heuristics",
      "using_dds": false
    },
    "intermediate": {
      "name": "Minimax AI (Depth 1)",
      "rating": "7.5/10",
      "description": "Lookahead search (1 trick)",
      "using_dds": false
    },
    "advanced": {
      "name": "Minimax AI (Depth 2)",
      "rating": "8/10",
      "description": "Lookahead search (2 tricks)",
      "using_dds": false
    },
    "expert": {
      "name": "Double Dummy Solver AI",
      "rating": "9/10",
      "description": "Double Dummy Solver (perfect play)",
      "using_dds": true
    }
  }
}
```

**Key Verification Points:**
- ✅ `"dds_available": true` at top level
- ✅ `"expert.using_dds": true`
- ✅ `"expert.name": "Double Dummy Solver AI"`
- ✅ `"expert.rating": "9/10"`

**If DDS is NOT working, you'll see:**
```json
{
  "dds_available": false,
  "difficulties": {
    "expert": {
      "name": "Minimax AI (Depth 4)",
      "rating": "8+/10",
      "description": "Lookahead search (4 tricks) - DDS fallback",
      "using_dds": false
    }
  }
}
```

---

### ✅ Step 3: Verify in Frontend (1 minute)

**Where:** Bottom-right corner of the app UI

**What you should see:**

```
┌─────────────────────────────┐
│ ✅ DDS Expert AI Active  ▶ │
└─────────────────────────────┘
```

**Click to expand for detailed status:**

```
┌────────────────────────────────────┐
│ ✅ DDS Expert AI Active        ▼  │
├────────────────────────────────────┤
│ EXPERT AI STATUS                   │
│ Name: Double Dummy Solver AI       │
│ Rating: 9/10                       │
│ DDS: Enabled ✓                     │
│ Double Dummy Solver (perfect play) │
│                                    │
│ DDS PERFORMANCE                    │
│ Solves: 47                         │
│ Avg Time: 45.3ms                   │
└────────────────────────────────────┘
```

**If DDS is NOT working, you'll see:**

```
┌─────────────────────────────┐
│ ⚠️ Expert AI (Fallback)  ▶ │
└─────────────────────────────┘
```

---

## Functional Testing (5 minutes)

Once you've verified DDS is loaded, test it actually works:

### Test 1: Play a Hand with Expert Difficulty

1. **Start a new hand** in your production app
2. **Select Expert difficulty**
3. **Play through bidding** (doesn't use DDS)
4. **Start card play phase**
5. **Observe AI's play:**
   - ✅ Responds within 10-200ms per card
   - ✅ Makes intelligent plays
   - ✅ No timeout errors
   - ✅ No fallback warnings

### Test 2: Check Performance Metrics

1. **Expand the status indicator** (bottom-right)
2. **Watch DDS Performance section:**
   - Solve count should increase as AI plays cards
   - Average time should be < 200ms
   - If solve count stays at 0, DDS is not actually being called

### Test 3: Compare with Lower Difficulties

1. **Play the same hand on Expert** (DDS)
2. **Play similar hand on Advanced** (Minimax depth 2)
3. **Compare play quality:**
   - Expert should consistently find optimal plays
   - Expert may play differently (better) than Advanced
   - Expert timing should be faster than you'd expect for perfect play

---

## Environment Variables (Production)

DDS doesn't require special environment variables, but these may be useful:

### Backend Environment Variables

**In Render Dashboard → Backend Service → Environment:**

| Variable | Value | Purpose |
|----------|-------|---------|
| `PYTHON_VERSION` | `3.10.0` | Minimum Python 3.8+ for endplay |
| `DDS_ENABLED` | `true` | Optional: Explicitly enable DDS |
| `DDS_TIMEOUT` | `5000` | Optional: DDS solve timeout (ms) |

**Note:** By default, DDS auto-enables if endplay is installed. No explicit env var needed.

---

## Common Issues & Solutions

### Issue 1: "dds_available": false

**Symptoms:**
- API endpoint shows `"dds_available": false`
- Backend logs show: `⚠️ Using Minimax D4 for expert`

**Causes & Fixes:**

1. **endplay not installed**
   - Check build logs for: `Successfully installed endplay`
   - If missing, verify `backend/requirements.txt` contains: `endplay>=0.5.0`
   - Trigger manual redeploy in Render dashboard

2. **Import error on startup**
   - Check service logs for Python errors
   - Look for: `ImportError: endplay` or similar
   - May need to clear build cache and redeploy

3. **Platform incompatibility**
   - DDS requires Linux (Render uses Ubuntu - should work)
   - Check Python version: Must be 3.8+
   - Check architecture: x86_64 (ARM not supported by endplay)

### Issue 2: DDS Loaded But Not Being Used

**Symptoms:**
- `"dds_available": true` but expert difficulty not using it
- Solve count stays at 0 during gameplay

**Causes & Fixes:**

1. **AI selection logic issue**
   - Check backend code: `server.py` AI initialization
   - Verify expert difficulty maps to DDSPlayAI, not MinimaxPlayAI

2. **Frontend not requesting expert**
   - Check network tab: Is `difficulty=expert` being sent?
   - Verify frontend UI correctly selects expert level

3. **DDS initialization failed silently**
   - Check for exceptions in backend logs
   - Add debug logging: Enable verbose DDS logs

### Issue 3: Slow DDS Performance

**Symptoms:**
- DDS works but takes > 1 second per solve
- Timeouts during gameplay

**Causes & Fixes:**

1. **Render free tier CPU limits**
   - Free tier may throttle CPU
   - Consider upgrading to paid tier for better performance
   - DDS is CPU-intensive

2. **Complex positions**
   - Some positions take longer to solve (normal)
   - Check if all positions are slow or just some
   - May need to implement timeout fallback

3. **Memory constraints**
   - Render free tier: 512MB RAM
   - DDS needs memory for search
   - Monitor memory usage in Render dashboard

---

## Performance Benchmarks

### Expected DDS Performance (Production)

| Metric | Expected | Acceptable | Concerning |
|--------|----------|------------|------------|
| **Solve Time** | 10-100ms | 100-200ms | > 500ms |
| **Success Rate** | 100% | > 95% | < 90% |
| **Memory Usage** | < 200MB | < 400MB | > 450MB |
| **CPU Usage** | < 50% | < 80% | > 90% sustained |

### Testing Benchmarks

Run the baseline test on production server (requires SSH/shell access):

```bash
cd backend
python3 test_play_quality_integrated.py --hands 10 --ai dds
```

**Expected Results:**
```
Hands Tested:      10
Contracts Played:  8-9
Success Rate:      85-95%
Composite Score:   90-95% (Grade A)
Timing:            15-30s per hand
```

**If you don't have shell access:** Use GitHub Actions (see below)

---

## Using GitHub Actions to Test Production

**Best approach when you don't have Render shell access:**

### Option 1: Run DDS Baseline Workflow

1. Go to: https://github.com/your-username/bridge-bidding-app/actions
2. Select **"DDS Play Quality Baseline"** workflow
3. Click "Run workflow"
4. Settings:
   - **Branch:** main (or whichever branch is deployed)
   - **hands:** 10
   - **ai_level:** dds
5. Review results:
   - Should show 85-95% success rate
   - Should show realistic timing (15-30s per hand)
   - Should show 0 illegal moves

### Option 2: Create Production Test Endpoint

Add this endpoint to your backend:

```python
@app.route('/api/test/dds', methods=['GET'])
def test_dds():
    """Test endpoint to verify DDS is working"""
    from engine.play.ai.dds_ai import DDS_AVAILABLE

    if not DDS_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'DDS not available'}), 500

    try:
        # Quick DDS test
        from engine.play.ai.dds_ai import DDSPlayAI
        ai = DDSPlayAI()

        return jsonify({
            'status': 'success',
            'dds_available': True,
            'ai_name': ai.get_name(),
            'ai_difficulty': ai.get_difficulty(),
            'message': 'DDS is operational'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'dds_available': False,
            'error': str(e)
        }), 500
```

Then test with:
```bash
curl https://your-backend-url.onrender.com/api/test/dds
```

---

## Monitoring DDS in Production

### Logs to Monitor

**1. Startup Logs (every deployment):**
```
✅ DDS AI loaded for expert difficulty (9/10 rating)
```

**2. Gameplay Logs (during play):**
```
DDS solve for position N: 3♠
DDS solve time: 45ms
```

**3. Error Logs (if issues occur):**
```
⚠️  DDS solve timeout after 5000ms
⚠️  DDS fallback to SimplePlayAI
```

### Metrics to Track

If you implement application monitoring (e.g., Sentry, Datadog):

- **DDS Success Rate:** % of solves that complete
- **DDS Average Time:** Mean solve time
- **DDS Timeout Rate:** % of solves that timeout
- **Expert Difficulty Usage:** How often users choose expert

---

## Quick Reference Checklist

### Initial Deployment Verification

- [ ] Backend build logs show `Successfully installed endplay`
- [ ] Backend startup logs show `✅ DDS AI loaded`
- [ ] API endpoint `/api/ai/status` returns `"dds_available": true`
- [ ] Frontend status indicator shows green ✅
- [ ] Can complete a hand with expert difficulty
- [ ] DDS solve count increases during play

### Ongoing Monitoring

- [ ] No DDS timeout errors in logs
- [ ] Expert difficulty responds quickly (< 200ms)
- [ ] Solve count increases as expected
- [ ] No fallback warnings in logs

---

## Related Documentation

- **User Guide:** `docs/guides/HOW_TO_VERIFY_DDS.md` - End-user verification
- **Deployment:** `docs/project-overview/PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Troubleshooting:** `docs/bug-fixes/DDS_CRASH_FIX.md`
- **Performance:** `.claude/CODING_GUIDELINES.md` - Play quality protocol

---

## Summary

**To verify DDS is running in production:**

1. ✅ **Check logs** for "DDS AI loaded" message
2. ✅ **Test API** endpoint shows `"dds_available": true`
3. ✅ **Verify UI** indicator shows green checkmark
4. ✅ **Play a hand** with expert difficulty and confirm it works

**If any step fails**, see the Common Issues section above or review the troubleshooting documentation.

**Pro Tip:** Keep the frontend status indicator expanded during your first production game to watch DDS statistics update in real-time!
