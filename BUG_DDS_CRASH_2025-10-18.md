# DDS Crash Bug Report - Production Critical
**Bug ID:** BUG-C002
**Status:** 🔴 CRITICAL - Active
**Discovered:** 2025-10-18 at 18:17
**Severity:** CRITICAL - System crash during gameplay
**Area:** Card Play AI / DDS Integration
**Platform:** macOS Development (also affects production if DDS has similar issues)

---

## Executive Summary

**CRITICAL ISSUE:** DDS (Double Dummy Solver) crashes during gameplay with Error Code -14 ("Too few cards" or invalid deal structure). This crash occurred TODAY (Oct 18, 2025 at 18:17) on the user's macOS development machine during active gameplay.

**Root Cause:** DDS library initialized at server startup even though documentation states it's unstable on macOS. User was able to select "Expert" AI mode through UI, triggering DDS usage, which then crashed.

**Impact:**
- 🔴 **Local Development:** System crashes during gameplay, unusable
- 🔴 **Production Risk:** Same crash could occur on production if DDS encounters invalid deal state
- 🔴 **User Experience:** Total game failure mid-hand

---

## The Problem

### What Happened

1. **User played a hand** with gameplay AI
2. **DDS was active** (either defaulted to Expert or manually selected)
3. **DDS crashed** with Error Code -14 during card play decision
4. **System generated dump.txt** with crash details
5. **Game became unusable**

### Evidence: dump.txt (Created Oct 18, 2025 at 18:17)

```
Error code=-14

Deal data:
trump=H
first=N
[card distribution data...]

        S Q753
        H JT6
        D JT76
        C J2
S J942          S T8
H Q7            H 9852
D 32            D 985
C Q854          C T763
        S A6
        H AK43
        D AKQ4
        C AK9
```

**DDS Error Code -14:** Indicates "Too few cards" or invalid deal structure passed to DDS solver.

### Current Configuration Status

```bash
DDS_AVAILABLE: False  # Disabled after crash
DEFAULT_AI_DIFFICULTY: advanced  # Currently safe mode
```

---

## Root Cause Analysis

### 1. DDS Initialization at Server Startup

**File:** `backend/server.py:66-73`

```python
# AI instances for different difficulty levels
# Expert level uses DDS when available (9/10 rating), falls back to deep Minimax (8+/10)
ai_instances = {
    'beginner': SimplePlayAINew(),
    'intermediate': MinimaxPlayAI(max_depth=2),
    'advanced': MinimaxPlayAI(max_depth=3),
    'expert': DDSPlayAI() if DDS_AVAILABLE else MinimaxPlayAI(max_depth=4)
}
```

**Problem:** This creates `DDSPlayAI()` instance at startup if `DDS_AVAILABLE=True`, even on macOS where DDS is known to be unstable.

### 2. User Can Select Expert Mode

**File:** `backend/server.py:510-540`

```python
@app.route('/api/set-ai-difficulty', methods=['POST'])
def set_ai_difficulty():
    state.ai_difficulty = difficulty  # User can set to 'expert'
    play_ai = ai_instances[difficulty]  # Uses pre-initialized DDSPlayAI
```

**Problem:** User can manually select Expert mode through UI, triggering DDS usage even when it's unstable.

### 3. Smart Default May Enable DDS on macOS

**File:** `backend/core/session_state.py:47-72`

```python
def _get_smart_default_ai():
    try:
        from engine.play.ai.dds_ai import DDS_AVAILABLE
        if DDS_AVAILABLE:
            return 'expert'  # ❌ Problem: Enables DDS even on unstable macOS
        else:
            return 'advanced'
    except ImportError:
        return 'advanced'
```

**Problem:** If endplay is installed and initially appears to work (DDS_AVAILABLE=True), smart default enables Expert mode automatically, even on macOS.

### 4. Contradictory Documentation

**Documentation says:**
- Production should default to Expert (9/10) with DDS
- Local dev should default to Advanced (8/10) without DDS
- DDS is unstable on macOS M1/M2 and should not be used

**Code does:**
- Initializes DDS at startup if available
- Allows user to select Expert mode
- Smart default enables Expert if DDS appears available

**Result:** DDS gets used on macOS → Crash

---

## Why This Happened

### Timeline of Events

1. **Earlier:** endplay was installed (perhaps for testing)
2. **Server starts:** DDS_AVAILABLE initially detected as True
3. **Server initializes:** DDSPlayAI() instance created at startup
4. **User plays:** Either default was Expert OR user manually selected Expert
5. **During gameplay:** DDS encountered invalid deal structure
6. **CRASH:** DDS Error Code -14, dump.txt created
7. **Now:** DDS_AVAILABLE=False (disabled after crash)

### The Core Issue

**DDS is fundamentally unstable on macOS M1/M2:**

From [DDS_MACOS_INSTABILITY_REPORT.md](DDS_MACOS_INSTABILITY_REPORT.md):
- Segmentation faults in libdds.dylib
- Multi-threading crashes
- ARM64 compatibility issues
- Success rate: 40-60% (not acceptable)

**Yet the code still allows DDS usage on macOS:**
- Initializes DDS at startup if library present
- Smart default enables Expert mode if DDS detected
- UI allows manual Expert selection
- No platform-based blocking

---

## Impact Assessment

### Development (macOS)
🔴 **CRITICAL**
- Cannot use Expert mode without crashes
- Unpredictable failures during testing
- Game becomes unusable mid-hand
- No graceful degradation

### Production (Linux)
⚠️ **HIGH RISK**
- Same error code could occur on production
- If DDS encounters invalid deal state → crash
- Affects all users in Expert mode
- No fallback recovery

### User Trust
🔴 **SEVERE**
- Mid-game crashes destroy confidence
- "System crashed" is worst UX possible
- Users lose current hand progress

---

## Expected vs Actual Behavior

### Expected Behavior

**Local Development (macOS):**
- ✅ Default: Advanced (8/10) with Minimax
- ✅ Expert mode: DISABLED or uses Minimax fallback
- ✅ DDS: NOT initialized, not available
- ✅ User cannot trigger DDS crashes

**Production (Linux):**
- ✅ Default: Expert (9/10) with DDS
- ✅ DDS: Tested and verified stable
- ✅ Fallback: Minimax if DDS fails
- ✅ Graceful degradation on errors

### Actual Behavior

**Local Development (macOS):**
- ❌ DDS: Initialized if endplay installed
- ❌ Expert mode: Available and uses DDS
- ❌ Smart default: May enable Expert
- ❌ User CAN trigger DDS crashes
- ❌ Crash dump generated
- ❌ No graceful recovery

---

## The Fix Required

### 1. Platform-Based DDS Blocking

**Prevent DDS initialization on macOS entirely:**

```python
import platform

# Only allow DDS on Linux (production)
PLATFORM_ALLOWS_DDS = platform.system() == 'Linux'

try:
    from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE
    if DDS_AVAILABLE and PLATFORM_ALLOWS_DDS:
        print("✅ DDS available for Expert AI (9/10)")
    elif DDS_AVAILABLE and not PLATFORM_ALLOWS_DDS:
        print("⚠️  DDS detected but disabled on macOS (unstable)")
        DDS_AVAILABLE = False
    else:
        print("⚠️  DDS not available")
except ImportError:
    DDS_AVAILABLE = False
    PLATFORM_ALLOWS_DDS = False
```

### 2. Safe AI Instance Initialization

**Never create DDSPlayAI on macOS:**

```python
ai_instances = {
    'beginner': SimplePlayAINew(),
    'intermediate': MinimaxPlayAI(max_depth=2),
    'advanced': MinimaxPlayAI(max_depth=3),
    'expert': DDSPlayAI() if (DDS_AVAILABLE and PLATFORM_ALLOWS_DDS)
              else MinimaxPlayAI(max_depth=4)
}
```

### 3. Force Advanced Default on macOS

**Override smart default for macOS:**

```python
def _get_smart_default_ai():
    # Force advanced on macOS regardless of DDS availability
    if platform.system() == 'Darwin':  # macOS
        return 'advanced'

    # Linux/Windows: Use smart detection
    env_setting = os.environ.get('DEFAULT_AI_DIFFICULTY')
    if env_setting:
        return env_setting

    try:
        from engine.play.ai.dds_ai import DDS_AVAILABLE
        return 'expert' if DDS_AVAILABLE else 'advanced'
    except ImportError:
        return 'advanced'
```

### 4. UI Indicator for Disabled Expert Mode

**Show user why Expert is using Minimax:**

```json
{
  "expert": {
    "available": true,
    "engine": "Minimax AI (depth 4)",
    "rating": "8+/10",
    "note": "DDS disabled on macOS (unstable)",
    "using_dds": false
  }
}
```

---

## Testing the Fix

### Test 1: Verify DDS Blocked on macOS

```bash
PYTHONPATH=backend python3 -c "
import platform
print(f'Platform: {platform.system()}')

from core.session_state import DEFAULT_AI_DIFFICULTY
print(f'Default AI: {DEFAULT_AI_DIFFICULTY}')

from server import DDS_AVAILABLE, ai_instances
print(f'DDS Available: {DDS_AVAILABLE}')
print(f'Expert AI: {ai_instances[\"expert\"].get_name()}')
"

# Expected output on macOS:
# Platform: Darwin
# Default AI: advanced
# DDS Available: False
# Expert AI: Minimax AI (depth 4)
```

### Test 2: Verify No DDS Crashes

```bash
# Play 10 hands at Expert mode
# Should use Minimax fallback, no crashes
for i in {1..10}; do
  echo "Test $i: Playing hand with Expert AI"
  # ... play complete hand ...
  echo "✅ Passed"
done

# ✅ PASS: 10/10 hands complete without crashes
# ❌ FAIL: Any DDS crash or dump.txt created
```

### Test 3: Verify Production Still Uses DDS

```bash
# On Linux production:
PYTHONPATH=backend python3 -c "
import platform
print(f'Platform: {platform.system()}')

from server import DDS_AVAILABLE, ai_instances
print(f'DDS Available: {DDS_AVAILABLE}')
print(f'Expert AI: {ai_instances[\"expert\"].get_name()}')
"

# Expected output on Linux:
# Platform: Linux
# DDS Available: True
# Expert AI: Double Dummy Solver AI
```

---

## Files to Modify

1. **backend/server.py** (lines 27-38, 66-73)
   - Add platform detection
   - Block DDS on macOS
   - Safe AI instance initialization

2. **backend/core/session_state.py** (lines 47-72)
   - Force 'advanced' default on macOS
   - Document platform-based logic

3. **backend/.env.example**
   - Update documentation
   - Clarify platform differences

4. **render.yaml**
   - Already correct (Expert for Linux production)

---

## Priority and Urgency

**Priority:** 🔴 **CRITICAL**

**Why Critical:**
1. Crash happened TODAY during active use
2. Affects both development AND potentially production
3. Total system failure (worst possible UX)
4. User trust severely damaged
5. No graceful degradation

**Timeline:**
- 🔴 **Immediate:** Implement fix (< 1 hour)
- 🔴 **Today:** Test locally on macOS
- 🟡 **Before deploy:** Test on Linux staging
- 🟡 **Production:** Deploy with confidence

---

## Recommendations

### Immediate Actions

1. ✅ **Disable DDS on macOS** (platform check)
2. ✅ **Force Advanced default on macOS** (override smart default)
3. ✅ **Test Expert mode** (verify Minimax fallback works)
4. ✅ **Document platform differences** (clear expectations)

### Before Production Deploy

1. ✅ **Test DDS on Linux staging** (verify stability)
2. ✅ **Load test with Expert AI** (ensure DDS handles production load)
3. ✅ **Monitor error logs** (watch for Error Code -14)
4. ✅ **Add DDS health check** (detect issues early)

### Long-term Improvements

1. ⚠️ **DDS error recovery** (graceful fallback mid-game)
2. ⚠️ **Deal validation** (prevent invalid structures)
3. ⚠️ **DDS timeout handling** (prevent hangs)
4. ⚠️ **Telemetry** (track DDS success/failure rates)

---

## Related Documentation

- [DDS_MACOS_INSTABILITY_REPORT.md](DDS_MACOS_INSTABILITY_REPORT.md) - Known macOS issues
- [PRODUCTION_AI_AUTO_DEFAULT.md](PRODUCTION_AI_AUTO_DEFAULT.md) - Smart default logic
- [AI_LEVEL_CONFIGURATION_VERIFIED.md](AI_LEVEL_CONFIGURATION_VERIFIED.md) - Configuration guide
- [BUG_TRACKING_SYSTEM.md](BUG_TRACKING_SYSTEM.md) - Add this bug

---

## Conclusion

**The system currently allows DDS usage on macOS despite knowing it's unstable.** This resulted in a crash TODAY during active gameplay. The fix is straightforward: **use platform detection to completely disable DDS on macOS**, forcing Expert mode to use the stable Minimax fallback instead.

**Next Steps:**
1. Implement platform-based DDS blocking
2. Test locally (should use Minimax for Expert)
3. Add to BUG_TRACKING_SYSTEM.md as BUG-C002
4. Deploy with confidence

---

**Report Created:** 2025-10-18
**Crash Evidence:** dump.txt (Oct 18, 2025 at 18:17)
**Current Status:** DDS disabled, Advanced default active
**Fix Required:** Platform-based DDS blocking + forced Advanced on macOS
