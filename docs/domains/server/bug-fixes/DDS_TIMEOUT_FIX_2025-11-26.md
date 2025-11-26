# DDS Subprocess Isolation Fix - November 26, 2025

## Issue

**Error:** `502 Bad Gateway` when AI tries to play cards on production

**Symptom:** AI not playing cards on production (Render). The AI loop would pause ("AI: ⏸") and the game would be stuck waiting for AI to play. Browser console showed `net::ERR_FAILED 502 (Bad Gateway)`.

**Environment:** Production (Render/Linux) with DDS (expert) AI level

## Root Cause

On Render (Linux), the DDS library (`endplay`) is enabled for expert-level AI play. However, the DDS solver can:

1. **Crash with segfault** - Python exception handlers don't catch these
2. **Hang indefinitely** - Some positions cause the solver to spin
3. **Time out** - Render has a 30-second request timeout

When any of these occur, the Gunicorn worker process dies and Render returns a 502 Bad Gateway error.

## Solution

**Subprocess Isolation** - Run DDS in a separate process so segfaults don't crash the main server.

The `safe_ai_choose_card()` wrapper function now:

1. **For expert (DDS) difficulty:**
   - Serializes PlayState to a dict
   - Spawns subprocess to run DDS
   - Waits with 15-second timeout
   - If subprocess crashes (exitcode != 0) → segfault detected
   - If subprocess hangs → timeout kills it
   - Falls back to Minimax AI on any failure

2. **For other difficulties:**
   - Uses simple SIGALRM timeout
   - Falls back to Minimax on timeout/exception

### Key Components

```python
def _dds_worker(play_state_dict, position, result_queue):
    """Worker function that runs DDS in a separate process."""
    # If DDS segfaults here, only this subprocess dies
    dds_ai = DDSPlayAI()
    card = dds_ai.choose_card(play_state, position)
    result_queue.put({'status': 'success', 'card': {...}})

def safe_ai_choose_card(ai, play_state, position, difficulty, timeout_seconds=15):
    if difficulty == 'expert' and DDS_AVAILABLE:
        # Subprocess isolation
        process = multiprocessing.Process(target=_dds_worker, ...)
        process.start()
        process.join(timeout_seconds)

        if process.exitcode != 0:
            # Segfault detected! Main server survives.
            print("DDS CRASH: Subprocess exited with code", process.exitcode)
            # Fall back to Minimax
```

### Why Subprocess?

| Issue | Signal Handler | Subprocess |
|-------|---------------|------------|
| Timeout | ✅ Catches | ✅ Catches |
| Python Exception | ✅ Catches | ✅ Catches |
| Segfault | ❌ Process dies | ✅ Only subprocess dies |
| Hang | ✅ SIGALRM kills | ✅ terminate() kills |

## Files Changed

- `backend/server.py`:
  - Added `_dds_worker()` - subprocess entry point
  - Added `_serialize_play_state()` - convert PlayState to dict
  - Added `_reconstruct_play_state()` - rebuild PlayState in subprocess
  - Updated `safe_ai_choose_card()` - subprocess isolation for DDS

## Testing

1. Deploy to production
2. Play a game with "expert" AI difficulty
3. If DDS crashes, server logs will show:
   ```
   ⚠️  DDS CRASH: Subprocess exited with code -11 for W
      This was likely a segfault in the DDS library
      Falling back to Minimax AI for W
   ```
4. Game continues with Minimax fallback (no 502!)

## Performance

- Subprocess spawn overhead: ~50-100ms
- Only affects "expert" difficulty with DDS enabled
- Other difficulties use direct call (no overhead)

## Related

- CORS fix: `docs/domains/server/bug-fixes/CORS_AI_PLAY_FIX_2025-11-26.md`
- DDS crashes on macOS: `docs/domains/play/bug-fixes/BUG_DDS_CRASH_2025-10-18.md`
- Previous AI play issues: `docs/domains/play/bug-fixes/AI_PLAY_BUG_ANALYSIS.md`
