# Convention Practice UI - Feature Documentation

**Last Updated:** 2025-10-14
**Status:** ✅ Complete
**Related Files:**
- Frontend: `frontend/src/App.js` (lines 73-75, 682-689, 1203-1222)
- Backend: `backend/server.py` (/api/scenarios endpoint)
- Data: `backend/scenarios/bidding_scenarios.json`

---

## Overview

The Convention Practice UI provides a user-friendly interface for practicing bridge conventions organized by difficulty level. Conventions are grouped into three tiers (Essential, Intermediate, Advanced) and displayed in a structured dropdown menu for easy selection.

## User-Facing Changes

### 1. Button Label Improvement
**Before:** "Load Scenario"
**After:** "Practice Convention"

**Rationale:** The new label is more descriptive and clearly indicates the purpose of the feature - practicing specific bridge conventions rather than loading arbitrary scenarios.

### 2. Three-Level Convention Organization

Conventions are now visibly organized by difficulty level in the dropdown:

#### Essential Conventions (4)
Must-learn fundamentals for all players:
- Stayman
- Jacoby Transfers
- Weak Two Bids
- Takeout Doubles

#### Intermediate Conventions (5)
Important competitive and slam bidding tools:
- Blackwood (4NT)
- Negative Doubles
- Michaels Cuebid
- Unusual 2NT
- Strong 2♣

#### Advanced Conventions (6)
Expert-level sophisticated techniques:
- Fourth Suit Forcing
- Splinter Bids
- New Minor Forcing
- Responsive Doubles
- Lebensohl
- Gerber (4♣)

### 3. Improved Visibility

**Problem Solved:** Conventions were not initially visible in the dropdown.

**Solution:**
- Added `scenariosByLevel` state to track grouped conventions
- Implemented HTML `<optgroup>` elements for visual grouping
- Backend now returns structured data immediately on load

## Technical Implementation

### Frontend Changes

#### State Management
```javascript
const [scenariosByLevel, setScenariosByLevel] = useState(null);
```

#### Data Loading
```javascript
const response = await fetch(`${API_URL}/api/scenarios`);
const data = await response.json();
setScenariosByLevel(data.scenarios_by_level);
```

#### Dropdown Rendering
```jsx
<select value={selectedScenario} onChange={(e) => setSelectedScenario(e.target.value)}>
  {scenariosByLevel ? (
    <>
      <optgroup label="Essential Conventions">
        {scenariosByLevel.Essential?.map(s =>
          <option key={s.name} value={s.name}>{s.name}</option>
        )}
      </optgroup>
      <optgroup label="Intermediate Conventions">
        {scenariosByLevel.Intermediate?.map(s =>
          <option key={s.name} value={s.name}>{s.name}</option>
        )}
      </optgroup>
      <optgroup label="Advanced Conventions">
        {scenariosByLevel.Advanced?.map(s =>
          <option key={s.name} value={s.name}>{s.name}</option>
        )}
      </optgroup>
    </>
  ) : (
    <option>Loading...</option>
  )}
</select>
```

### Backend Changes

#### API Response Structure
The `/api/scenarios` endpoint now returns:

```json
{
  "scenarios_by_level": {
    "Essential": [
      {
        "name": "Stayman",
        "level": "Essential",
        "description": "North opens 1NT, South gets a hand suitable for Stayman."
      },
      ...
    ],
    "Intermediate": [...],
    "Advanced": [...]
  },
  "scenarios": ["Stayman", "Jacoby Transfers", ...]  // Backward compatibility
}
```

#### Implementation
```python
scenarios_by_level = {
    'Essential': [],
    'Intermediate': [],
    'Advanced': []
}

for s in scenarios:
    level = s.get('level', 'Essential')
    scenario_info = {
        'name': s['name'],
        'level': level,
        'description': s.get('description', '')
    }
    scenarios_by_level[level].append(scenario_info)
```

### Data Structure Updates

Each scenario in `bidding_scenarios.json` now includes:
- `name`: Convention name (e.g., "Stayman")
- `level`: Difficulty tier ("Essential", "Intermediate", or "Advanced")
- `description`: Brief explanation of the convention
- `setup`: Hand generation constraints for practice

**Example:**
```json
{
  "name": "Stayman",
  "level": "Essential",
  "description": "North opens 1NT, South gets a hand suitable for Stayman.",
  "setup": [
    { "position": "North", "constraints": { "hcp_range": [15, 17], "is_balanced": true } },
    { "position": "South", "generate_for_convention": "Stayman" }
  ]
}
```

## Integration with Convention Levels System

This UI improvement aligns with the existing Convention Levels architecture:

- **ConventionRegistry** (`backend/engine/ai/conventions/convention_registry.py`) defines the three-level structure
- **Scenarios** now mirror this structure for consistent user experience
- Future integration: Link practice scenarios to user progress tracking in the Learning Dashboard

## Benefits

1. **Clearer Navigation:** Users can immediately see conventions organized by difficulty
2. **Progressive Learning:** Visual grouping reinforces the learning path progression
3. **Better Discoverability:** All conventions are visible in structured groups
4. **Consistent Naming:** "Practice Convention" clearly communicates purpose
5. **Backward Compatible:** Old code using `scenarios` array continues to work

## Related Documentation

- [Convention Levels Architecture](./CONVENTION_LEVELS_ARCHITECTURE.md)
- [Convention Levels Implementation](./CONVENTION_LEVELS_IMPLEMENTATION.md)
- [Convention Levels Quickstart](./CONVENTION_LEVELS_QUICKSTART.md)
- [Learning Dashboard](../../frontend/src/components/learning/LearningDashboard.js)

## Testing

### Manual Testing Checklist
- [x] Dropdown displays three optgroup sections
- [x] Each section contains correct conventions
- [x] Button displays "Practice Convention" text
- [x] Selecting a convention and clicking loads the practice hand
- [x] Backend returns structured data with `scenarios_by_level`
- [x] Frontend build succeeds without errors

### Browser Compatibility
- Chrome/Edge: ✅ Tested
- Safari: ✅ Tested (optgroup styling may vary)
- Firefox: ✅ Tested

## Future Enhancements

1. **User Progress Integration:** Grey out or lock conventions based on user's learning path progress
2. **Progress Indicators:** Show completion percentage for each level
3. **Tooltips:** Display convention descriptions on hover
4. **Search/Filter:** Allow users to search for specific conventions
5. **Favorites:** Let users mark frequently practiced conventions

---

**See also:**
- Commit: "feat: Improve convention practice UI with three-level learning system"
- Related Issues: Convention visibility, naming clarity
