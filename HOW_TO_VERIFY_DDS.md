# How to Verify DDS is Running

**Quick Answer:** Look for the status indicator in the bottom-right corner of your app!

---

## Visual Indicators

### ✅ DDS is Working (What You Want to See)

When DDS is successfully loaded, you'll see in the **bottom-right corner**:

```
┌─────────────────────────────┐
│ ✅ DDS Expert AI Active  ▶ │
└─────────────────────────────┘
```

**What this means:**
- Expert difficulty is using the Double Dummy Solver
- You have the 9/10 rating AI
- Perfect play with complete information

### ⚠️ DDS Not Available (Fallback Mode)

If DDS isn't loaded, you'll see:

```
┌─────────────────────────────┐
│ ⚠️ Expert AI (Fallback)  ▶ │
└─────────────────────────────┘
```

**What this means:**
- Expert difficulty is using Minimax AI (depth 4)
- You still have 8+/10 rating AI (very good!)
- endplay library not installed or failed to load

---

## Detailed Status View

Click on the indicator to expand it and see full details:

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
│                                    │
│ ALL DIFFICULTY LEVELS              │
│ beginner:      6/10                │
│ intermediate:  7.5/10              │
│ advanced:      8/10                │
│ expert:        9/10                │
└────────────────────────────────────┘
```

---

## Backend Verification

### Method 1: Check Server Logs (Easiest)

When your backend starts, look for this message:

```
✅ DDS AI loaded for expert difficulty (9/10 rating)
```

**If DDS is not available, you'll see:**
```
⚠️  Using Minimax D4 for expert (DDS not available)
```

### Method 2: Test the API Endpoint

```bash
curl https://your-backend-url.onrender.com/api/ai/status
```

Look for:
```json
{
  "dds_available": true,
  "difficulties": {
    "expert": {
      "name": "Double Dummy Solver AI",
      "rating": "9/10",
      "description": "Double Dummy Solver (perfect play)",
      "using_dds": true
    }
  }
}
```

**Key fields:**
- `dds_available: true` ✅ DDS library loaded
- `expert.using_dds: true` ✅ Expert AI using DDS
- `expert.name: "Double Dummy Solver AI"` ✅ Correct AI class

---

## What You'll See in Production

### On Render (After Deployment)

1. **During Build (Render Dashboard → Logs):**
   ```
   Installing dependencies from requirements.txt
   ...
   Successfully installed endplay-0.5.12
   ...
   Build succeeded
   ```

2. **During Startup (Service → Logs):**
   ```
   ✅ DDS AI loaded for expert difficulty (9/10 rating)
   ✓ Learning path API endpoints registered
   ✓ Analytics API endpoints registered
   * Running on http://0.0.0.0:10000
   ```

3. **In Your App (Frontend):**
   - Status indicator in bottom-right corner shows green ✅
   - Click it to expand and verify "DDS: Enabled ✓"

---

## Troubleshooting

### If DDS is Not Working

**Symptom:** Status indicator shows ⚠️ warning icon

**Possible Causes & Fixes:**

1. **endplay not installed**
   - Check Render build logs for installation errors
   - Verify `endplay>=0.5.0` is in `backend/requirements.txt`
   - Trigger redeploy from Render dashboard

2. **Import error**
   - Check Render service logs for Python errors
   - Look for ImportError or ModuleNotFoundError
   - May need to upgrade Python version (requires 3.8+)

3. **Platform incompatibility**
   - DDS library uses C extensions
   - Should work on Linux (Render uses Ubuntu)
   - If issues persist, check endplay compatibility

### Testing Locally

**Before deploying**, test DDS works on your machine:

```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install endplay
python test_dds_simple.py
```

Expected output:
```
================================================================================
DDS AI Simple Test
================================================================================

DDS_AVAILABLE: True
✅ DDS library available

Creating DDS AI instance...
✅ AI created successfully
   Name: Double Dummy Solver AI
   Difficulty: expert

Testing endplay library directly...
✅ Created test deal from PBN
✅ Calculated double dummy table
   DD table calculated successfully

================================================================================
✅ ALL TESTS PASSED - DDS AI OPERATIONAL
================================================================================
```

---

## Performance Indicators

### DDS is Working Well

When playing with expert difficulty:

- **Response Time:** 10-200ms per move
- **No Errors:** No timeout messages
- **Smart Play:** AI makes optimal moves consistently

### DDS Statistics

The expanded status panel shows:
- **Solve Count:** How many positions DDS has evaluated
- **Avg Time:** Average time per solve (should be < 100ms typically)
- **Min/Max Time:** Range of solve times

These numbers increase as you play more hands with expert AI.

---

## Quick Reference

| Indicator | Meaning | Action Needed |
|-----------|---------|---------------|
| ✅ DDS Expert AI Active | Perfect! DDS is working | None - enjoy expert play! |
| ⚠️ Expert AI (Fallback) | Using Minimax instead | Check backend logs, verify endplay installed |
| ⋯ Loading AI... | Fetching status | Wait a few seconds |
| ⚠️ AI Status Unknown | Can't reach backend | Check backend is running, check CORS |

---

## Summary

**You'll know DDS is running when:**

1. ✅ Bottom-right indicator shows green checkmark
2. ✅ Backend logs show "DDS AI loaded"
3. ✅ API endpoint returns `"dds_available": true`
4. ✅ Expanded view shows "DDS: Enabled ✓"
5. ✅ Expert AI responds quickly (10-200ms) with smart moves

**If any of these are missing**, check the troubleshooting section above.

---

**Pro Tip:** Keep the status indicator expanded during your first few games with expert difficulty to watch the DDS statistics increase and verify it's working!
