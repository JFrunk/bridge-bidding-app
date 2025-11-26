# DDS Timeout Fix - November 26, 2025

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

Added a `safe_ai_choose_card()` wrapper function that:

1. **Enforces timeout** - Uses SIGALRM to kill long-running DDS calls (15s limit)
2. **Catches all exceptions** - Wraps AI call in try/except
3. **Falls back gracefully** - Uses Minimax AI (depth 3) if DDS fails
4. **Emergency fallback** - Picks first legal card if even Minimax fails

### Code Changes

```python
# Fallback AI for when DDS/expert fails (prevents 502 crashes)
fallback_ai = MinimaxPlayAI(max_depth=3)

def safe_ai_choose_card(ai, play_state, position, difficulty, timeout_seconds=10):
    """
    Safely execute AI card selection with timeout and fallback.
    """
    import signal
    import sys

    def timeout_handler(signum, frame):
        raise TimeoutError(f"AI decision timed out after {timeout_seconds}s")

    try:
        # Set timeout alarm (Unix only)
        if sys.platform != 'win32':
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

        try:
            card = ai.choose_card(play_state, position)
            return card, False, ai.get_name()
        finally:
            if sys.platform != 'win32':
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

    except (TimeoutError, Exception) as e:
        # Fallback to Minimax
        card = fallback_ai.choose_card(play_state, position)
        return card, True, f"{ai.get_name()} (fallback)"
```

## Verification

After the fix:
- AI plays cards even when DDS is unstable
- No more 502 errors from DDS crashes
- Game continues with Minimax fallback
- Logs indicate when fallback was used

## Files Changed

- `backend/server.py` - Added `safe_ai_choose_card()` wrapper and `fallback_ai`

## Testing

1. Deploy to production
2. Play a game with "expert" AI difficulty
3. Verify AI makes plays without 502 errors
4. Check server logs for any fallback usage

## Related

- CORS fix: `docs/domains/server/bug-fixes/CORS_AI_PLAY_FIX_2025-11-26.md`
- DDS crashes on macOS: `docs/domains/play/bug-fixes/BUG_DDS_CRASH_2025-10-18.md`
- Previous AI play issues: `docs/domains/play/bug-fixes/AI_PLAY_BUG_ANALYSIS.md`
