# Convention Levels - Quick Start Guide

## Overview

The **Convention Levels system** provides a structured, progressive learning path for bridge conventions. Conventions are organized into three tiers (Essential → Intermediate → Advanced) with automatic unlocking based on prerequisites and mastery.

**Status:** ✅ Backend Complete | ⏳ Frontend In Progress

---

## What's Been Built

### ✅ Backend Components (Complete)

1. **ConventionRegistry** (`backend/engine/ai/conventions/convention_registry.py`)
   - Metadata for all 15 conventions
   - Level categorization (Essential/Intermediate/Advanced)
   - Prerequisites and dependencies
   - Learning characteristics (frequency, complexity, practice requirements)

2. **SkillTree** (`backend/engine/learning/skill_tree.py`)
   - 6-level progression structure
   - Integration of basic skills and convention groups
   - Unlock requirements and completion criteria

3. **Database Schema** (`backend/database/schema_convention_levels.sql`)
   - Convention definitions table
   - Prerequisites table
   - User progress tracking
   - Practice history logging

4. **API Endpoints** (`backend/engine/learning/learning_path_api.py`)
   - Query conventions by level
   - Get user progress
   - Check unlocked conventions
   - Get recommendations
   - Record practice results

---

## Quick Start

### Step 1: Initialize Database

```bash
cd backend

# Create tables and populate convention data
python database/init_convention_data.py

# Optional: Initialize test user
python database/init_convention_data.py --init-test-user
```

**Output:**
```
============================================================
CONVENTION DATA INITIALIZATION
============================================================

Creating convention tables...
✓ Tables created successfully

Populating convention data...
✓ Inserted 15 conventions
✓ Inserted 43 prerequisites

============================================================
CONVENTION SUMMARY
============================================================

ESSENTIAL (4):
  Stayman, Jacoby Transfers, Weak Two Bids, Takeout Doubles

INTERMEDIATE (5):
  Blackwood (4NT), Negative Doubles, Michaels Cuebid, Unusual 2NT, Strong 2♣

ADVANCED (6):
  Fourth Suit Forcing, Splinter Bids, New Minor Forcing, Responsive Doubles, Lebensohl, Gerber (4♣)

============================================================
✓ Convention data initialization complete!
============================================================
```

### Step 2: Register API Endpoints

Add to `backend/server.py`:

```python
# Add import at top
from engine.learning.learning_path_api import register_learning_endpoints

# After creating Flask app
app = Flask(__name__)
CORS(app)
engine = BiddingEngine()

# Register learning endpoints
register_learning_endpoints(app)
```

### Step 3: Test API Endpoints

```bash
# Start backend server
python server.py

# In another terminal, test endpoints:

# Get all conventions by level
curl http://localhost:5001/api/conventions/by-level

# Get specific convention
curl http://localhost:5001/api/conventions/stayman

# Get user's convention progress (assuming user_id=1)
curl http://localhost:5001/api/user/convention-progress?user_id=1

# Get unlocked conventions
curl http://localhost:5001/api/conventions/unlocked?user_id=1

# Get next recommended convention
curl http://localhost:5001/api/conventions/next-recommended?user_id=1

# Get skill tree
curl http://localhost:5001/api/skill-tree

# Get user's skill tree progress
curl http://localhost:5001/api/skill-tree/progress?user_id=1
```

---

## Convention Structure

### Level 1: Essential Conventions (Must Learn)

| Convention | Frequency | Complexity | Practice Hands | Passing % |
|------------|-----------|------------|----------------|-----------|
| Stayman | Very High | Low | 10 | 80% |
| Jacoby Transfers | Very High | Low | 10 | 80% |
| Weak Two Bids | High | Low | 8 | 80% |
| Takeout Doubles | High | Medium | 12 | 80% |

**Unlock:** After completing Level 1 Foundations (Basic Skills)

### Level 2: Intermediate Conventions (Should Learn)

| Convention | Frequency | Complexity | Practice Hands | Passing % |
|------------|-----------|------------|----------------|-----------|
| Blackwood (4NT) | Medium | Medium | 12 | 80% |
| Negative Doubles | Medium | High | 15 | 80% |
| Michaels Cuebid | Medium | Medium | 12 | 80% |
| Unusual 2NT | Medium | Medium | 12 | 80% |
| Strong 2♣ | Low | Medium | 10 | 80% |

**Unlock:** After mastering ALL Essential conventions

### Level 3: Advanced Conventions (Expert Tools)

| Convention | Frequency | Complexity | Practice Hands | Passing % |
|------------|-----------|------------|----------------|-----------|
| Fourth Suit Forcing | Medium | High | 15 | 85% |
| Splinter Bids | Low | High | 15 | 85% |
| New Minor Forcing | Medium | High | 18 | 85% |
| Responsive Doubles | Low | High | 15 | 85% |
| Lebensohl | Low | Very High | 20 | 85% |
| Gerber (4♣) | Low | Medium | 12 | 85% |

**Unlock:** After mastering ALL Intermediate conventions

---

## API Reference

### GET /api/conventions/by-level

Get all conventions grouped by level.

**Response:**
```json
{
  "essential": [
    {
      "id": "stayman",
      "name": "Stayman",
      "level": "essential",
      "category": "1NT System",
      "frequency": "Very High",
      "complexity": "Low",
      "prerequisites": ["1nt_opening"],
      "practice_hands_required": 10,
      "passing_accuracy": 0.8,
      "description": "2♣ bid after partner opens 1NT...",
      "short_description": "2♣ asks for majors after 1NT",
      "learning_time_minutes": 15
    },
    ...
  ],
  "intermediate": [...],
  "advanced": [...]
}
```

### GET /api/conventions/<convention_id>

Get detailed information about a specific convention.

**Example:** `/api/conventions/stayman`

### GET /api/user/convention-progress?user_id=<id>

Get user's overall progress and status for each convention.

**Response:**
```json
{
  "user_id": 1,
  "summary": {
    "essential": {
      "total": 4,
      "mastered": 2,
      "ids": ["stayman", "jacoby_transfers", "weak_two", "takeout_double"]
    },
    "intermediate": {
      "total": 5,
      "mastered": 0,
      "ids": [...]
    },
    "advanced": {
      "total": 6,
      "mastered": 0,
      "ids": [...]
    },
    "overall": {
      "total": 15,
      "mastered": 2,
      "percentage": 13.3
    }
  },
  "conventions": {
    "stayman": {
      "status": "mastered",
      "accuracy": 0.85,
      "attempts": 12,
      "last_practiced": "2025-10-11T14:30:00"
    },
    ...
  }
}
```

### GET /api/conventions/unlocked?user_id=<id>

Get conventions currently unlocked and available for the user.

**Response:**
```json
{
  "user_id": 1,
  "unlocked": [
    {
      "id": "stayman",
      "name": "Stayman",
      ...
    }
  ],
  "count": 4
}
```

### GET /api/conventions/next-recommended?user_id=<id>

Get the next convention user should learn (based on priorities).

**Response:**
```json
{
  "recommended": {
    "id": "takeout_double",
    "name": "Takeout Doubles",
    ...
  },
  "message": "We recommend learning Takeout Doubles next"
}
```

### POST /api/conventions/record-practice

Record a practice attempt for a convention.

**Request Body:**
```json
{
  "user_id": 1,
  "convention_id": "stayman",
  "was_correct": true,
  "hints_used": 0,
  "time_taken_seconds": 45
}
```

**Response:**
```json
{
  "success": true,
  "progress": {
    "user_id": 1,
    "convention_id": "stayman",
    "status": "in_progress",
    "attempts": 5,
    "correct": 4,
    "accuracy": 0.8,
    "last_practiced": "2025-10-11T15:00:00"
  }
}
```

### GET /api/skill-tree

Get the complete skill tree structure (all 6 levels).

### GET /api/skill-tree/progress?user_id=<id>

Get user's progress through the skill tree.

**Response:**
```json
{
  "user_id": 1,
  "levels": {
    "level_1_foundations": {
      "level_number": 1,
      "name": "Level 1: Foundations",
      "unlocked": true,
      "total": 5,
      "completed": 5,
      "percentage": 100.0,
      "is_convention_group": false
    },
    "level_2_essential_conventions": {
      "level_number": 2,
      "name": "Level 2: Essential Conventions",
      "unlocked": true,
      "total": 4,
      "completed": 2,
      "percentage": 50.0,
      "is_convention_group": true
    },
    ...
  },
  "next_recommended_level": "level_2_essential_conventions"
}
```

---

## Integration with Frontend

### Example: Display Convention Levels

```javascript
// Fetch conventions by level
const response = await fetch('http://localhost:5001/api/conventions/by-level');
const { essential, intermediate, advanced } = await response.json();

// Display essential conventions
<div className="convention-level essential">
  <h2>⭐ Essential Conventions</h2>
  {essential.map(conv => (
    <ConventionCard key={conv.id} convention={conv} />
  ))}
</div>
```

### Example: Track User Progress

```javascript
// Get user's progress
const response = await fetch(`http://localhost:5001/api/user/convention-progress?user_id=${userId}`);
const { summary, conventions } = await response.json();

// Display progress
<ProgressBar
  current={summary.overall.mastered}
  total={summary.overall.total}
  percentage={summary.overall.percentage}
/>
```

### Example: Record Practice

```javascript
// After user completes a practice hand
const recordPractice = async (conventionId, wasCorrect, timeInSeconds) => {
  const response = await fetch('http://localhost:5001/api/conventions/record-practice', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      convention_id: conventionId,
      was_correct: wasCorrect,
      hints_used: 0,
      time_taken_seconds: timeInSeconds
    })
  });

  const { success, progress } = await response.json();

  if (success && progress.status === 'mastered') {
    // Show mastery celebration!
    showMasteryModal(conventionId);
  }
};
```

---

## Database Schema

### Key Tables

**conventions**
- Stores convention metadata
- Fields: convention_id, name, level, category, frequency, complexity, etc.

**convention_prerequisites**
- Defines dependencies between conventions and skills
- Fields: convention_id, prerequisite_id, prerequisite_type

**user_convention_progress**
- Tracks user's progress for each convention
- Fields: user_id, convention_id, status, attempts, correct, accuracy
- Status values: 'locked', 'unlocked', 'in_progress', 'mastered'

**convention_practice_history**
- Detailed log of each practice attempt
- Fields: id, user_id, convention_id, was_correct, hints_used, time_taken_seconds

### Views

**v_user_convention_summary**
- Aggregated user progress summary
- Total conventions, mastered count, average accuracy

**v_user_level_progress**
- Progress breakdown by level
- Shows completion percentage for each level

---

## Testing

### Manual Testing Checklist

```bash
# 1. Initialize database
python backend/database/init_convention_data.py

# 2. Verify data
sqlite3 backend/bridge.db
> SELECT COUNT(*) FROM conventions;  # Should be 15
> SELECT level, COUNT(*) FROM conventions GROUP BY level;
> SELECT * FROM conventions WHERE level = 'essential';

# 3. Test API endpoints
python backend/server.py

# In another terminal:
curl http://localhost:5001/api/conventions/by-level | python -m json.tool
curl http://localhost:5001/api/conventions/stayman | python -m json.tool
curl http://localhost:5001/api/skill-tree | python -m json.tool

# 4. Test user progress (create test user first)
python backend/database/init_convention_data.py --init-test-user
curl 'http://localhost:5001/api/user/convention-progress?user_id=1' | python -m json.tool
curl 'http://localhost:5001/api/conventions/unlocked?user_id=1' | python -m json.tool
```

### Automated Test Script

Create `backend/test_convention_levels.py`:

```python
import requests

BASE_URL = 'http://localhost:5001/api'

def test_conventions_by_level():
    response = requests.get(f'{BASE_URL}/conventions/by-level')
    data = response.json()

    assert len(data['essential']) == 4
    assert len(data['intermediate']) == 5
    assert len(data['advanced']) == 6
    print("✓ Conventions by level test passed")

def test_convention_detail():
    response = requests.get(f'{BASE_URL}/conventions/stayman')
    data = response.json()

    assert data['id'] == 'stayman'
    assert data['level'] == 'essential'
    assert data['category'] == '1NT System'
    print("✓ Convention detail test passed")

def test_skill_tree():
    response = requests.get(f'{BASE_URL}/skill-tree')
    data = response.json()

    assert 'level_1_foundations' in data
    assert 'level_2_essential_conventions' in data
    print("✓ Skill tree test passed")

if __name__ == '__main__':
    print("Testing Convention Levels API...")
    test_conventions_by_level()
    test_convention_detail()
    test_skill_tree()
    print("\n✅ All tests passed!")
```

---

## Next Steps

### For Backend:
1. ✅ Convention metadata system (COMPLETE)
2. ✅ Database schema (COMPLETE)
3. ✅ API endpoints (COMPLETE)
4. ⏳ Integration with server.py
5. ⏳ User authentication/accounts

### For Frontend:
1. ⏳ ConventionLevelView component
2. ⏳ ConventionCard component
3. ⏳ Progress tracking UI
4. ⏳ Unlock animations
5. ⏳ Integration with main app

### For Both:
1. ⏳ Practice mode integration
2. ⏳ Scenario system updates
3. ⏳ Spaced repetition for conventions
4. ⏳ Achievement badges for convention mastery

---

## Troubleshooting

**Q: Database not found error**
A: Run `python backend/database/init_convention_data.py` first

**Q: API endpoints return 404**
A: Make sure you called `register_learning_endpoints(app)` in server.py

**Q: All conventions showing as 'locked'**
A: Initialize user progress with `--init-test-user` flag or complete prerequisite skills

**Q: How do I add a new convention?**
A:
1. Add to `CONVENTION_REGISTRY` in `convention_registry.py`
2. Run `python database/init_convention_data.py` to update database
3. Add to appropriate level in `skill_tree.py`

---

## Summary

**What You Have:**
- ✅ 15 conventions categorized into 3 levels
- ✅ Automatic prerequisite checking
- ✅ Progress tracking with mastery detection
- ✅ Unlock system based on completion
- ✅ Recommendation engine
- ✅ Complete API for frontend integration

**What's Next:**
- Build frontend UI components
- Integrate with existing practice system
- Add spaced repetition for review
- Create convention-specific tutorials

**Estimated Time to Frontend Complete:** 2-3 weeks

---

**Document Version:** 1.0
**Created:** October 11, 2025
**Status:** Backend Complete, Frontend In Progress
