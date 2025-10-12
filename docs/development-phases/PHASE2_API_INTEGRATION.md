# Phase 2 API Integration - Complete

## Overview

Phase 2 Minimax AI has been fully integrated into the backend server. The system now supports multiple AI difficulty levels that can be selected at runtime.

---

## New API Endpoints

### 1. GET /api/ai-difficulties

Get available AI difficulty levels and current selection.

**Request:**
```http
GET /api/ai-difficulties HTTP/1.1
```

**Response:**
```json
{
  "current": "beginner",
  "difficulties": [
    {
      "id": "beginner",
      "name": "Beginner",
      "description": "Simple Rule-Based AI",
      "level": "beginner"
    },
    {
      "id": "intermediate",
      "name": "Intermediate",
      "description": "Minimax AI (depth 2)",
      "level": "intermediate"
    },
    {
      "id": "advanced",
      "name": "Advanced",
      "description": "Minimax AI (depth 3)",
      "level": "advanced"
    },
    {
      "id": "expert",
      "name": "Expert",
      "description": "Minimax AI (depth 4)",
      "level": "expert"
    }
  ]
}
```

**Fields:**
- `current` - Currently selected difficulty ID
- `difficulties` - Array of available difficulty levels:
  - `id` - Unique identifier (use this to set difficulty)
  - `name` - Display name (capitalize for UI)
  - `description` - AI implementation description
  - `level` - AI difficulty level

---

### 2. POST /api/set-ai-difficulty

Set the AI difficulty level.

**Request:**
```http
POST /api/set-ai-difficulty HTTP/1.1
Content-Type: application/json

{
  "difficulty": "advanced"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "difficulty": "advanced",
  "ai_name": "Minimax AI (depth 3)",
  "ai_level": "advanced"
}
```

**Error Response (400):**
```json
{
  "error": "Invalid difficulty. Must be one of: ['beginner', 'intermediate', 'advanced', 'expert']"
}
```

**Parameters:**
- `difficulty` (required) - One of: `beginner`, `intermediate`, `advanced`, `expert`

**Notes:**
- Changes take effect immediately for next AI move
- Setting persists for the session (not saved between server restarts)
- Does not affect current play in progress

---

### 3. GET /api/ai-statistics

Get performance statistics from the last AI move.

**Request:**
```http
GET /api/ai-statistics HTTP/1.1
```

**Response (Minimax AI):**
```json
{
  "has_statistics": true,
  "ai_name": "Minimax AI (depth 3)",
  "difficulty": "advanced",
  "statistics": {
    "nodes": 2051,
    "leaf_nodes": 1342,
    "pruned": 89,
    "time": 0.047,
    "depth": 3,
    "score": 3.2,
    "nps": 43617
  }
}
```

**Response (Simple AI):**
```json
{
  "has_statistics": false,
  "ai_name": "Simple Rule-Based AI",
  "difficulty": "beginner"
}
```

**Statistics Fields:**
- `nodes` - Total positions searched
- `leaf_nodes` - Positions evaluated at depth limit
- `pruned` - Branches eliminated by alpha-beta pruning
- `time` - Search time in seconds
- `depth` - Search depth used
- `score` - Position evaluation (tricks advantage)
- `nps` - Nodes per second (performance metric)

**Notes:**
- Statistics are from the most recent AI move
- Simple AI returns `has_statistics: false` (no search-based stats)
- Minimax AIs return detailed search statistics
- Call this after `/api/get-ai-play` to get stats for that move

---

## AI Difficulty Levels

### Beginner (Simple Rule-Based AI)
- **Implementation:** Rule-based heuristics
- **Strengths:** Fast (<0.1ms), basic bridge principles
- **Weaknesses:** Predictable, misses complex plays
- **Success Rate:** ~33% on test deals
- **Best For:** New players learning the game

### Intermediate (Minimax Depth 2)
- **Implementation:** Minimax with alpha-beta pruning, 2 tricks ahead
- **Strengths:** Tactical awareness, faster than depth 3
- **Weaknesses:** Too shallow for complex positions
- **Performance:** ~2.5ms per move, 8,143 nodes/sec
- **Success Rate:** ~42% on test deals
- **Best For:** Intermediate players, fast play

### Advanced (Minimax Depth 3) ⭐ **Recommended Default**
- **Implementation:** Minimax with alpha-beta pruning, 3 tricks ahead
- **Strengths:** Best balance of strength vs speed
- **Weaknesses:** Some advanced techniques still challenging
- **Performance:** ~5.8ms per move, 8,383 nodes/sec
- **Success Rate:** ~67% on test deals
- **Best For:** Most users, competitive play

### Expert (Minimax Depth 4)
- **Implementation:** Minimax with alpha-beta pruning, 4 tricks ahead
- **Strengths:** Strongest tactical play
- **Weaknesses:** Slower, may be overkill for most positions
- **Performance:** ~15-30ms per move (estimated)
- **Success Rate:** ~75% on test deals (estimated)
- **Best For:** Analysis mode, studying hands

---

## Backend Implementation Details

### Server Changes

**File:** `backend/server.py`

**Added Imports:**
```python
from engine.play.ai.simple_ai import SimplePlayAI as SimplePlayAINew
from engine.play.ai.minimax_ai import MinimaxPlayAI
```

**Global State:**
```python
# AI difficulty settings
current_ai_difficulty = "beginner"
ai_instances = {
    "beginner": SimplePlayAINew(),
    "intermediate": MinimaxPlayAI(max_depth=2),
    "advanced": MinimaxPlayAI(max_depth=3),
    "expert": MinimaxPlayAI(max_depth=4)
}
```

**Backward Compatibility:**
- Old `play_ai = SimplePlayAI()` still exists
- Gets updated when difficulty changes via `set_ai_difficulty()`
- Existing `/api/get-ai-play` endpoint works unchanged

### Integration Points

1. **AI Selection:** `play_ai` global variable points to current AI
2. **Card Play:** `/api/get-ai-play` uses `play_ai.choose_card()`
3. **Statistics:** Minimax AIs track `nodes`, `time`, `pruning`, etc.
4. **Difficulty:** Can be changed anytime via `/api/set-ai-difficulty`

---

## Frontend Integration Guide

### Example: Add AI Difficulty Selector

```javascript
// Fetch available difficulties on component mount
useEffect(() => {
  fetch('http://localhost:5001/api/ai-difficulties')
    .then(res => res.json())
    .then(data => {
      setDifficulties(data.difficulties);
      setCurrentDifficulty(data.current);
    });
}, []);

// Handle difficulty change
const handleDifficultyChange = (difficultyId) => {
  fetch('http://localhost:5001/api/set-ai-difficulty', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ difficulty: difficultyId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      setCurrentDifficulty(data.difficulty);
      console.log(`AI changed to: ${data.ai_name}`);
    }
  });
};

// Render difficulty selector
<select value={currentDifficulty} onChange={e => handleDifficultyChange(e.target.value)}>
  {difficulties.map(diff => (
    <option key={diff.id} value={diff.id}>
      {diff.name} - {diff.description}
    </option>
  ))}
</select>
```

### Example: Display AI Statistics

```javascript
// After AI plays a card
const fetchAIStatistics = async () => {
  const response = await fetch('http://localhost:5001/api/ai-statistics');
  const data = await response.json();

  if (data.has_statistics) {
    const stats = data.statistics;
    console.log(`AI searched ${stats.nodes} positions in ${stats.time}s`);
    console.log(`Performance: ${stats.nps.toLocaleString()} nodes/sec`);
    console.log(`Efficiency: ${stats.pruned} branches pruned`);
  }
};

// Display statistics in UI (optional)
{aiStats && aiStats.has_statistics && (
  <div className="ai-stats">
    <h4>AI Thinking</h4>
    <p>Positions analyzed: {aiStats.statistics.nodes.toLocaleString()}</p>
    <p>Search time: {(aiStats.statistics.time * 1000).toFixed(0)}ms</p>
    <p>Efficiency: {((aiStats.statistics.pruned / aiStats.statistics.nodes) * 100).toFixed(1)}% pruned</p>
  </div>
)}
```

### Recommended UI Placement

**Settings Menu:**
```
⚙️ Settings
  ├─ AI Difficulty
  │   ● Beginner (fastest, basic play)
  │   ○ Intermediate (2-3ms, tactical)
  │   ○ Advanced (5-8ms, strategic) ⭐ Recommended
  │   ○ Expert (15-30ms, strongest)
  │
  ├─ Show AI Statistics [ ] (checkbox)
  └─ ...
```

**In-Game (Optional):**
- Small indicator showing current difficulty (e.g., "AI: Advanced")
- Statistics panel (collapsible) showing search metrics
- "Thinking..." indicator with progress (for Expert mode)

---

## Testing

### Manual API Testing

```bash
# 1. Get available difficulties
curl http://localhost:5001/api/ai-difficulties

# 2. Set difficulty to advanced
curl -X POST http://localhost:5001/api/set-ai-difficulty \
  -H "Content-Type: application/json" \
  -d '{"difficulty":"advanced"}'

# 3. Get current statistics
curl http://localhost:5001/api/ai-statistics
```

### Automated Test Script

```bash
cd backend
source venv/bin/activate
python test_ai_integration.py
```

**Expected Output:**
```
✓ Get AI Difficulties: PASS
✓ Set Difficulty to 'beginner': PASS
✓ Get Statistics (beginner - no stats): PASS
✓ Set Difficulty to 'advanced': PASS
✓ Get Statistics (advanced - has stats): PASS
✓ Set Difficulty to 'expert': PASS
✓ Set Invalid Difficulty: PASS
✓ Set Difficulty back to 'advanced': PASS

Total: 8/8 tests passed
```

---

## Performance Considerations

### Response Times by Difficulty

| Difficulty | Avg Time/Move | Acceptable for Interactive Play? |
|-----------|---------------|----------------------------------|
| Beginner | <0.1ms | ✅ Yes - Instant |
| Intermediate | 2-3ms | ✅ Yes - Imperceptible |
| Advanced | 5-8ms | ✅ Yes - Imperceptible |
| Expert | 15-30ms | ✅ Yes - Just noticeable but acceptable |

### Frontend Implications

- **No loading indicators needed** for Beginner/Intermediate/Advanced
- **Optional indicator** for Expert (very brief, may not be worth it)
- **Statistics display** only useful for Intermediate+ (shows AI "thinking")
- **Default to Advanced** for best user experience

### Server Load

- **Beginner:** Negligible CPU usage
- **Intermediate:** Light CPU usage (~2ms per move)
- **Advanced:** Moderate CPU usage (~6ms per move)
- **Expert:** Heavier CPU usage (~20ms per move)

**Recommendation:** Advanced is optimal for production. Expert is fine for analysis/study mode.

---

## Migration Notes

### Backward Compatibility

✅ **Fully backward compatible:**
- Existing gameplay endpoints unchanged
- Default difficulty is "beginner" (Simple AI)
- Old code continues to work without modifications
- Deprecation warning on old import (not breaking)

### Upgrading Existing Games

If a game is in progress:
- Changing difficulty takes effect on next AI move
- Does not affect current hand state
- No need to restart game

### Future Enhancements

Potential additions (not yet implemented):
- Save difficulty preference per user
- Adaptive difficulty (adjusts based on player skill)
- Difficulty profiles (custom depth/evaluation settings)
- AI "personalities" (aggressive, conservative, etc.)
- Opening lead knowledge base
- Defensive signaling conventions

---

## API Versioning

**Current Version:** 1.0 (Phase 2 Integration)

**Endpoint Stability:**
- `/api/ai-difficulties` - Stable
- `/api/set-ai-difficulty` - Stable
- `/api/ai-statistics` - Stable

**Future Changes:**
- Additional difficulty levels may be added
- New statistics fields may be added
- Existing fields guaranteed to remain

---

## Troubleshooting

### Issue: "Cannot connect to server"
**Solution:** Ensure server is running on port 5001
```bash
cd backend && source venv/bin/activate && python server.py
```

### Issue: "Invalid difficulty" error
**Solution:** Use exact difficulty IDs: `beginner`, `intermediate`, `advanced`, `expert`

### Issue: Statistics show all zeros
**Solution:** Normal if no AI moves have been made yet. Statistics populate after first AI play.

### Issue: Performance slower than expected
**Solution:**
- Check server logs for errors
- Verify Python version (3.8+)
- Consider using lower difficulty for slower machines
- Expert mode is inherently slower (15-30ms is normal)

---

## Summary

**Phase 2 Integration Complete:** ✅

**What Works:**
- ✅ 4 AI difficulty levels (beginner → expert)
- ✅ Runtime difficulty switching
- ✅ Performance statistics API
- ✅ Full backward compatibility
- ✅ Tested and verified

**Ready For:**
- ✅ Frontend UI integration
- ✅ Production deployment
- ✅ User testing

**Next Steps:**
1. Add difficulty selector to frontend UI
2. (Optional) Display AI statistics
3. Test with real users
4. Gather feedback and iterate

**Files Modified:**
- `backend/server.py` - Added 3 new endpoints, AI difficulty management

**Files Created:**
- `backend/test_ai_integration.py` - Automated integration tests
- `PHASE2_API_INTEGRATION.md` - This documentation

**Benchmark Data:**
- See `backend/benchmarks/full_benchmark_results.json`
- See `PHASE2_SESSION2_COMPLETE.md` for analysis

---

**Phase 2 is production-ready!** 🎉
