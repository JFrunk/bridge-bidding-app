# Production AI Auto-Default - NOW ENABLED

**Status:** ✅ FIXED - System now automatically uses Expert AI (9/10) in production

---

## What Changed

### Before (Problem)
- Default was **hardcoded** to `'advanced'` (8/10)
- Even in production with DDS available, system used 8/10 AI
- Required manual environment variable setting to get 9/10 AI

### After (Fixed)
- Default is now **smart** - automatically detects DDS availability
- **Production (Linux with DDS):** Automatically uses `expert` (9/10) ✅
- **Development (macOS without DDS):** Automatically uses `advanced` (8/10) ✅
- **Can still override** with `DEFAULT_AI_DIFFICULTY` environment variable

---

## How It Works Now

**File:** `backend/core/session_state.py`

```python
def _get_smart_default_ai():
    """
    Smart default AI selection:
    - If DDS is available (production/Linux): use 'expert' for 9/10 play
    - If DDS not available (dev/macOS): use 'advanced' for 8/10 play
    - Can be overridden with DEFAULT_AI_DIFFICULTY env var
    """
    # Check for explicit environment variable first
    env_setting = os.environ.get('DEFAULT_AI_DIFFICULTY')
    if env_setting:
        return env_setting  # Manual override takes priority

    # Auto-detect based on DDS availability
    try:
        from engine.play.ai.dds_ai import DDS_AVAILABLE
        if DDS_AVAILABLE:
            return 'expert'  # Production: 9/10 with DDS
        else:
            return 'advanced'  # Dev: 8/10 without DDS
    except ImportError:
        return 'advanced'  # DDS not installed: 8/10
```

---

## What This Means for Production

### On Linux Production Server (with DDS installed):

**Before:**
```
🎯 Default AI Difficulty: advanced
   Engine: Minimax AI (depth 3)
   Rating: ~8/10
```

**After (Automatic):**
```
🎯 Default AI Difficulty: expert
   Engine: Double Dummy Solver AI
   Rating: ~9/10 ✅
```

### On macOS Development (DDS crashes):

**Stays the same:**
```
🎯 Default AI Difficulty: advanced
   Engine: Minimax AI (depth 3)
   Rating: ~8/10
```

---

## Deployment Instructions

### For Production on Linux:

1. **Install DDS** (one-time setup):
   ```bash
   pip install endplay
   ```

2. **Deploy and start server:**
   ```bash
   python3 server.py
   ```

3. **Verify in logs** (should show):
   ```
   🎯 Default AI Difficulty: expert
      Engine: Double Dummy Solver AI
      Rating: ~expert
   ```

**That's it!** No environment variable needed - it auto-detects.

### Optional: Manual Override

If you want to force a specific level regardless of DDS:

```bash
# In backend/.env
DEFAULT_AI_DIFFICULTY=advanced  # Force 8/10 even with DDS
```

Or:

```bash
export DEFAULT_AI_DIFFICULTY=expert
python3 server.py
```

---

## Verification

### Check Current Default:

```bash
python3 check_ai_config.py
```

### Check via API (server must be running):

```bash
curl http://localhost:5001/api/ai-status | python3 -m json.tool
```

Look for:
```json
{
  "current_difficulty": "expert",
  "difficulties": {
    "expert": {
      "using_dds": true,  // ← Should be true in production
      "rating": "9/10"
    }
  }
}
```

---

## Priority Order

The system checks in this order:

1. **Environment variable** (if set): Uses that value
2. **DDS availability** (auto-detect):
   - DDS available → `expert` (9/10)
   - DDS not available → `advanced` (8/10)

---

## Why This Is Better

### Before
- ❌ Required manual configuration for production
- ❌ Easy to forget to set `DEFAULT_AI_DIFFICULTY=expert`
- ❌ Production might run at 8/10 instead of 9/10

### After
- ✅ Automatic optimization for each environment
- ✅ Production gets best AI by default
- ✅ Development still stable (no DDS crashes)
- ✅ Can still override if needed

---

## Testing

### On Your macOS System (Now):
```
DEFAULT_AI_DIFFICULTY = 'advanced'
DDS Available: False
→ Correctly defaults to advanced (8/10)
```

### On Production Linux (With DDS):
```
DEFAULT_AI_DIFFICULTY = 'expert'
DDS Available: True
→ Will automatically default to expert (9/10)
```

---

## Summary

**Your question:** "Is the DDS not defaulting to playing in production?"

**Answer:**
- **Before this fix:** No, it was defaulting to `advanced` (8/10)
- **After this fix:** Yes, it now **automatically** defaults to `expert` (9/10) when DDS is available ✅

**What you need to do:**
1. On Linux production: Just install `pip install endplay`
2. Deploy the updated code
3. Start the server
4. It will **automatically** use expert (9/10) with DDS!

No environment variables needed. No manual configuration. It just works.
