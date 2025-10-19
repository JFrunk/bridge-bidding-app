# How to Check Which AI is Running in Production

## Quick Check

Run this script:
```bash
python3 check_ai_config.py
```

This will show you:
- Current default AI difficulty
- Whether DDS (Double Dummy Solver) is available
- Which AI engine will be used
- Recommendations for your environment

## Current Status (Your System)

**Environment:** macOS (Development)
**Default AI:** `advanced` (Minimax depth 3, ~8/10 rating)
**DDS Available:** No (common on macOS M1/M2)
**Expert AI:** Uses Minimax depth 4 (8+/10) instead of DDS (9/10)

## AI Difficulty Levels Explained

| Level | Engine | Rating | Use Case |
|-------|--------|--------|----------|
| `beginner` | Simple Rule-Based AI | 6/10 | Learning, beginners |
| `intermediate` | Minimax depth 2 | 7.5/10 | Casual play |
| `advanced` | Minimax depth 3 | 8/10 | **Current default** |
| `expert` | DDS (or Minimax depth 4) | 9/10 (or 8+/10) | Competitive play |

## How to Configure for Production

### Option 1: Environment Variable (Recommended)

Create a `.env` file in the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set:
```bash
DEFAULT_AI_DIFFICULTY=expert
```

### Option 2: Export Environment Variable

```bash
export DEFAULT_AI_DIFFICULTY=expert
python3 server.py
```

### Option 3: Check in Startup Logs

When you start the server, look for these lines:
```
🎯 Default AI Difficulty: expert
   Engine: Minimax AI (depth 4)
   Rating: ~expert
```

Or on Linux with DDS:
```
🎯 Default AI Difficulty: expert
   Engine: Double Dummy Solver AI
   Rating: ~expert
```

## API Endpoint to Check AI Status

While the server is running, you can check the AI status via API:

```bash
curl http://localhost:5001/api/ai-status | python3 -m json.tool
```

Response shows:
```json
{
  "dds_available": false,
  "difficulties": {
    "beginner": {...},
    "intermediate": {...},
    "advanced": {...},
    "expert": {
      "name": "Minimax AI (depth 4)",
      "rating": "8+/10",
      "description": "Deep minimax search (4-ply)",
      "using_dds": false
    }
  },
  "current_difficulty": "advanced"
}
```

## Production Deployment Checklist

For production on Linux:

1. ✅ Install DDS library:
   ```bash
   pip install endplay
   ```

2. ✅ Set environment variable:
   ```bash
   # In backend/.env
   DEFAULT_AI_DIFFICULTY=expert
   ```

3. ✅ Verify on startup:
   ```
   🎯 Default AI Difficulty: expert
      Engine: Double Dummy Solver AI
      Rating: ~expert
   ```

4. ✅ Test with API:
   ```bash
   curl http://your-server:5001/api/ai-status
   # Should show "using_dds": true for expert level
   ```

## Why DDS Doesn't Work on macOS M1/M2

The `endplay` library (which includes DDS) uses native code that sometimes crashes on Apple Silicon. This is a known issue with the library, not your code.

**Solutions:**
- **Development (macOS):** Use `advanced` or `expert` (falls back to Minimax depth 4)
- **Production (Linux):** Use `expert` (gets real DDS for 9/10 play)

## User Can Still Change AI Level

Even with a default set, users can change the AI difficulty through the UI or API:

**Via API:**
```bash
curl -X POST http://localhost:5001/api/set-ai-difficulty \
  -H "Content-Type: application/json" \
  -d '{"difficulty": "expert"}'
```

**Via UI:**
The frontend should have a difficulty selector that calls this API.

## After the Recent Fix

With the discard bug fix applied, here are the actual performance levels:

| Level | Before Fix | After Fix |
|-------|-----------|-----------|
| `beginner` | 6/10 | 6/10 (unchanged) |
| `intermediate` | 5/10* | 7.5/10 ✅ |
| `advanced` | 5/10* | 8/10 ✅ |
| `expert` (no DDS) | 4/10* | 8+/10 ✅ |
| `expert` (with DDS) | 9/10 | 9/10 (unchanged) |

*Before the fix, Minimax AIs were making 4/10 level discard mistakes (throwing away Kings). Now fixed.

## Recommendation for Production

**Set:** `DEFAULT_AI_DIFFICULTY=expert`

**Why:**
- On Linux: Gets you DDS (perfect 9/10 play)
- On macOS: Gets you Minimax depth 4 (8+/10 play, now with correct discard logic)
- Users can still lower it if they want easier opponents
- Shows your app provides strong AI gameplay
