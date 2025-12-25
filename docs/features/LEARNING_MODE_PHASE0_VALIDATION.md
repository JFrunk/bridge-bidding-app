# Learning Mode Phase 0: Infrastructure Validation Results

**Date:** 2025-12-25
**Status:** Complete
**Outcome:** Infrastructure validated with 3 bugs fixed

---

## Summary

Phase 0 validated the existing learning infrastructure before building Learning Mode. The infrastructure is **mostly functional** with several bugs identified and fixed during validation.

---

## Validation Results

### Endpoints Tested

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/skill-tree` | ✅ Working (after fix) | Returns 6-level skill tree |
| `GET /api/conventions/by-level` | ✅ Working | Returns 15 conventions in 3 levels |
| `GET /api/analytics/dashboard` | ✅ Working | Returns comprehensive dashboard |
| `GET /api/conventions/next-recommended` | ✅ Working | Returns null (expected - skills not tracked) |
| `GET /api/user/convention-progress` | ✅ Working | Tracks per-convention mastery |
| `POST /api/conventions/record-practice` | ✅ Working (after fix) | Records practice, updates progress |

### Database Tables Verified

All required tables exist in PostgreSQL:
- `conventions` (15 records after init)
- `convention_prerequisites`
- `user_convention_progress`
- `convention_practice_history`
- `user_gamification`
- `users`
- `mistake_patterns`
- `milestones`

### Mastery System Verified

Test: 10 correct Stayman practices
Result: Convention marked as "mastered" after reaching threshold

```
Attempt 1: in_progress (100%)
...
Attempt 10: mastered (100%)
```

---

## Bugs Found & Fixed

### 1. SkillType Enum Serialization Bug

**File:** `backend/engine/learning/skill_tree.py`

**Issue:** `get_all_levels()` returned raw `SkillNode` dataclass objects and `SkillType` enum values that aren't JSON serializable.

**Error:**
```json
{"error": "Object of type SkillType is not JSON serializable"}
```

**Fix:** Added `to_dict()` method to `SkillNode` dataclass and updated `get_all_levels()` to serialize properly.

### 2. Missing user_progress Table Reference

**File:** `backend/engine/learning/learning_path_api.py`

**Issue:** `get_user_completed_skills()` queried non-existent `user_progress` table.

**Error:**
```json
{"error": "relation \"user_progress\" does not exist"}
```

**Fix:** Updated to query `user_skill_progress` (future table) with try/except to return empty list gracefully. This is expected behavior - skills tracking isn't implemented yet.

### 3. db.py RETURNING id Bug

**File:** `backend/db.py`

**Issue:** PostgreSQL wrapper incorrectly added `RETURNING id` to INSERT statements for tables without explicit `id` column, triggered by column names containing 'id' (e.g., `user_id`, `convention_id`).

**Error:**
```json
{"error": "column \"id\" does not exist\nLINE 6: RETURNING id"}
```

**Fix:** Updated logic to only add `RETURNING id` when explicit `id` column pattern is detected (e.g., `(ID,` or `SERIAL`).

---

## Additional Setup Required

### Convention Data Initialization

The conventions table in PostgreSQL was empty. Required manual initialization:

```python
# Run against PostgreSQL to populate conventions
from engine.ai.conventions.convention_registry import get_convention_registry
registry = get_convention_registry()
# Insert 15 conventions with correct level strings ('essential', not '1')
```

**Note:** The `init_convention_data.py` script uses SQLite directly. For PostgreSQL, conventions must be initialized separately or the script updated.

---

## Gaps Identified (Expected)

### 1. Skills Not Tracked

The curriculum requires Levels 0-4 (fundamentals) before conventions. Currently:
- No `user_skill_progress` table exists
- No hand generation for fundamental topics
- `next-recommended` returns null because skill prerequisites aren't met

**Status:** Expected gap - Phase 1 work

### 2. Convention Prerequisites Require Skills

Essential conventions have prerequisites like `1nt_opening` and `opening_bids_basic` which are skills, not conventions. Until skills are tracked, these prerequisites can't be met.

**Status:** Expected behavior per curriculum design

---

## Infrastructure Ready for Phase 1

The following is confirmed working and ready to extend:

| Component | Status | Location |
|-----------|--------|----------|
| ConventionRegistry | ✅ Ready | `engine/ai/conventions/convention_registry.py` |
| SkillTree | ✅ Ready | `engine/learning/skill_tree.py` |
| Learning Path API | ✅ Ready | `engine/learning/learning_path_api.py` |
| Analytics API | ✅ Ready | `engine/learning/analytics_api.py` |
| Progress Tracking | ✅ Ready | Database tables + API |
| Mastery Detection | ✅ Ready | Tested with Stayman |

---

## Files Modified During Validation

1. `backend/engine/learning/skill_tree.py`
   - Added `SkillNode.to_dict()` method
   - Updated `SkillTreeManager.get_all_levels()` for JSON serialization

2. `backend/engine/learning/learning_path_api.py`
   - Updated `get_user_completed_skills()` to handle missing table gracefully

3. `backend/db.py`
   - Fixed `RETURNING id` detection logic

---

## Next Steps

Phase 1: Extend Curriculum Structure
- Add Levels 0-4 topics to skill_tree.py
- Create `user_skill_progress` table
- Add hand generation for fundamental topics

---

## Validation Script

A test script was created for future use:

```bash
#!/bin/bash
# test_learning_infrastructure.sh

BASE_URL="http://localhost:5001"

echo "Testing Learning Infrastructure..."

echo -n "1. Skill Tree API: "
curl -s "$BASE_URL/api/skill-tree" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'{len(d)} levels')" 2>/dev/null || echo "FAILED"

echo -n "2. Conventions by Level: "
curl -s "$BASE_URL/api/conventions/by-level" | python3 -c "
import sys,json
d=json.load(sys.stdin)
total = len(d.get('essential',[])) + len(d.get('intermediate',[])) + len(d.get('advanced',[]))
print(f'{total} conventions')" 2>/dev/null || echo "FAILED"

echo -n "3. Analytics Dashboard: "
curl -s "$BASE_URL/api/analytics/dashboard?user_id=1" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('OK' if 'bidding_feedback_stats' in d else 'FAILED')" 2>/dev/null || echo "FAILED"

echo -n "4. Record Practice: "
curl -s -X POST "$BASE_URL/api/conventions/record-practice" \
  -H "Content-Type: application/json" \
  -d '{"user_id":99,"convention_id":"stayman","was_correct":true}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('OK' if d.get('success') else 'FAILED')" 2>/dev/null || echo "FAILED"

echo "Done."
```
