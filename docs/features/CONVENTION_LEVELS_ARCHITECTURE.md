# Convention Levels - System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│                         (Frontend React)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐        │
│  │ Convention    │  │ Progress      │  │ Practice       │        │
│  │ Learning Page │  │ Dashboard     │  │ Mode           │        │
│  └───────┬───────┘  └───────┬───────┘  └────────┬───────┘        │
│          │                   │                    │                 │
└──────────┼───────────────────┼────────────────────┼─────────────────┘
           │                   │                    │
           ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER                                   │
│                    (learning_path_api.py)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  GET /api/conventions/by-level                                     │
│  GET /api/conventions/<id>                                         │
│  GET /api/conventions/unlocked?user_id=<id>                        │
│  GET /api/conventions/next-recommended?user_id=<id>                │
│  POST /api/conventions/record-practice                             │
│  GET /api/user/convention-progress?user_id=<id>                    │
│  GET /api/skill-tree                                               │
│  GET /api/skill-tree/progress?user_id=<id>                         │
│                                                                     │
└──────────┬─────────────────────────┬────────────────────┬──────────┘
           │                         │                    │
           ▼                         ▼                    ▼
┌──────────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ ConventionRegistry   │  │ SkillTreeManager │  │ Database        │
│ (Metadata)           │  │ (Progression)    │  │ (Persistence)   │
├──────────────────────┤  ├──────────────────┤  ├─────────────────┤
│                      │  │                  │  │                 │
│ • 15 conventions     │  │ • 6 levels       │  │ • conventions   │
│ • Level categories   │  │ • Unlock logic   │  │ • progress      │
│ • Prerequisites      │  │ • Prerequisites  │  │ • history       │
│ • Practice reqs      │  │ • Skills + Convs │  │ • users         │
│ • Recommendations    │  │ • Progression    │  │                 │
│                      │  │                  │  │                 │
└──────────────────────┘  └──────────────────┘  └─────────────────┘
```

## Data Flow Examples

### 1. Loading Convention Learning Page

```
Frontend                API                 Registry              Database
   │                     │                     │                     │
   │──GET /by-level─────>│                     │                     │
   │                     │──get_all()────────>│                     │
   │                     │<──conventions──────│                     │
   │                     │                     │                     │
   │──GET /progress─────>│                     │                     │
   │  ?user_id=1         │────────────────────────────────>SELECT──│
   │                     │<───────────────────────────────progress──│
   │<──JSON response─────│                     │                     │
   │                     │                     │                     │
   │ (Render UI)         │                     │                     │
```

### 2. Recording Practice Result

```
Frontend                API                 Database             Registry
   │                     │                     │                     │
   │──POST /record──────>│                     │                     │
   │  {user_id: 1,       │                     │                     │
   │   conv_id: "stayman"│                     │                     │
   │   correct: true}    │                     │                     │
   │                     │──INSERT history────>│                     │
   │                     │──SELECT progress──>│                     │
   │                     │<───current stats────│                     │
   │                     │                     │                     │
   │                     │──get_convention()───────────>│            │
   │                     │<───passing criteria──────────│            │
   │                     │                     │                     │
   │                     │ (Check mastery)     │                     │
   │                     │                     │                     │
   │                     │──UPDATE progress──>│                     │
   │<──{status: mastered}│                     │                     │
   │                     │                     │                     │
   │ (Show celebration!) │                     │                     │
```

### 3. Checking Unlocked Conventions

```
Frontend                API                 Registry              Database
   │                     │                     │                     │
   │──GET /unlocked─────>│                     │                     │
   │  ?user_id=1         │                     │                     │
   │                     │────────────────────────────────>SELECT──│
   │                     │<───skills + convs mastered─────────────│
   │                     │                     │                     │
   │                     │──get_unlocked()────>│                     │
   │                     │  (skills, convs)    │                     │
   │                     │                     │ (Check prereqs)     │
   │                     │                     │ (Check level locks) │
   │                     │<──unlocked list─────│                     │
   │<──JSON response─────│                     │                     │
   │                     │                     │                     │
   │ (Enable cards)      │                     │                     │
```

## Component Architecture

### Backend Components

```
backend/engine/
│
├── ai/conventions/
│   ├── convention_registry.py ← Metadata system (450 lines)
│   │   ├── ConventionMetadata (dataclass)
│   │   ├── ConventionLevel (enum)
│   │   ├── ConventionCategory (enum)
│   │   └── ConventionRegistry (manager class)
│   │       ├── get_convention(id)
│   │       ├── get_by_level(level)
│   │       ├── get_unlocked_conventions()
│   │       ├── check_prerequisites_met()
│   │       └── get_next_recommended()
│   │
│   ├── stayman.py
│   ├── jacoby_transfers.py
│   └── ... (other convention implementations)
│
└── learning/
    ├── __init__.py ← Module exports
    ├── skill_tree.py ← Learning path (380 lines)
    │   ├── SkillNode (dataclass)
    │   ├── SkillType (enum)
    │   ├── SKILL_TREE (definition)
    │   └── SkillTreeManager (manager class)
    │       ├── get_level(id)
    │       ├── check_level_unlocked()
    │       ├── get_user_skill_tree_progress()
    │       └── get_next_recommended_level()
    │
    └── learning_path_api.py ← API endpoints (470 lines)
        ├── conventions_by_level()
        ├── user_convention_progress()
        ├── unlocked_conventions()
        ├── next_recommended_convention()
        ├── record_convention_practice()
        ├── skill_tree_full()
        └── register_learning_endpoints(app)

backend/database/
├── schema_convention_levels.sql ← Tables & views
└── init_convention_data.py ← Population script
```

### Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│                    conventions                              │
├─────────────────────────────────────────────────────────────┤
│ PK: convention_id                                           │
│     name, level, category, frequency, complexity            │
│     description, short_description                          │
│     practice_hands_required, passing_accuracy               │
│     learning_time_minutes                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              convention_prerequisites                        │
├─────────────────────────────────────────────────────────────┤
│ PK: (convention_id, prerequisite_id)                        │
│     prerequisite_type (skill | convention)                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           user_convention_progress                          │
├─────────────────────────────────────────────────────────────┤
│ PK: (user_id, convention_id)                                │
│     status (locked|unlocked|in_progress|mastered)           │
│     attempts, correct, accuracy                             │
│     started_at, mastered_at, last_practiced                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         convention_practice_history                         │
├─────────────────────────────────────────────────────────────┤
│ PK: id (auto)                                               │
│     user_id, convention_id                                  │
│     hand_id, user_bid, correct_bid                          │
│     was_correct, hints_used, time_taken_seconds             │
│     timestamp                                               │
└─────────────────────────────────────────────────────────────┘
```

## Progression Flow

### User Learning Journey

```
START
  │
  ├─> Level 1: Foundations (5 skills)
  │     │
  │     └─> Complete with 80%+ accuracy
  │           │
  │           ▼
  │   ┌───────────────────────────────┐
  │   │  Level 2: Essential           │
  │   │  Conventions UNLOCK            │
  │   └───────────────────────────────┘
  │           │
  │           ├─> Stayman (10 hands, 80%)
  │           ├─> Jacoby (10 hands, 80%)
  │           ├─> Weak Two (8 hands, 80%)
  │           └─> Takeout Double (12 hands, 80%)
  │                 │
  │                 └─> All mastered?
  │                       │
  │                       ▼
  │   ┌───────────────────────────────┐
  │   │  Level 4: Intermediate        │
  │   │  Conventions UNLOCK            │
  │   └───────────────────────────────┘
  │           │
  │           ├─> Blackwood (12 hands, 80%)
  │           ├─> Negative Double (15 hands, 80%)
  │           ├─> Michaels (12 hands, 80%)
  │           ├─> Unusual 2NT (12 hands, 80%)
  │           └─> Strong 2♣ (10 hands, 80%)
  │                 │
  │                 └─> All mastered?
  │                       │
  │                       ▼
  │   ┌───────────────────────────────┐
  │   │  Level 6: Advanced            │
  │   │  Conventions UNLOCK            │
  │   └───────────────────────────────┘
  │           │
  │           ├─> Fourth Suit Forcing (15 hands, 85%)
  │           ├─> Splinter Bids (15 hands, 85%)
  │           ├─> New Minor Forcing (18 hands, 85%)
  │           ├─> Responsive Double (15 hands, 85%)
  │           ├─> Lebensohl (20 hands, 85%)
  │           └─> Gerber (12 hands, 85%)
  │                 │
  │                 └─> All mastered?
  │                       │
  │                       ▼
  │                   COMPLETE!
  │              All 15 conventions mastered
  │
  └─> Parallel tracks with Levels 3, 5 (bidding skills)
```

## State Transitions

### Convention Status Lifecycle

```
┌──────────┐
│  LOCKED  │ Initial state, prerequisites not met
└────┬─────┘
     │ Prerequisites completed
     ▼
┌──────────┐
│ UNLOCKED │ Available to practice
└────┬─────┘
     │ User starts first practice hand
     ▼
┌─────────────┐
│ IN_PROGRESS │ Actively practicing
└─────┬───────┘
      │ Met passing criteria:
      │ • Completed required hands
      │ • Achieved passing accuracy
      ▼
┌──────────┐
│ MASTERED │ Convention mastered!
└────┬─────┘
     │ Can still practice for review
     └──> (stays mastered)
```

### Accuracy Calculation

```
Total Attempts: A
Correct Attempts: C
Accuracy: C / A

Example:
  Attempts: 10
  Correct: 8
  Accuracy: 0.80 (80%)

Mastery Check:
  IF attempts >= required_hands (10)
  AND accuracy >= passing_accuracy (0.80)
  THEN status = 'mastered'
```

## Integration Points

### Where Frontend Connects

```
┌────────────────────────────────────────────────────────────┐
│                    Frontend App.js                         │
└────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Convention     │  │ Progress       │  │ Practice       │
│ Learning Page  │  │ Dashboard      │  │ Integration    │
└────────────────┘  └────────────────┘  └────────────────┘
        │                   │                   │
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│              API Endpoints (server.py)                  │
│                                                         │
│  register_learning_endpoints(app) ← ADD THIS           │
└─────────────────────────────────────────────────────────┘
```

### Frontend Component Structure (Proposed)

```
src/
├── App.js
└── components/
    └── learning/
        ├── ConventionLearningPath.js ← Main page
        │   ├── ConventionLevelView.js ← Level section
        │   │   └── ConventionCard.js ← Individual card
        │   │       ├── LockIcon (when locked)
        │   │       ├── ProgressBar (when in progress)
        │   │       └── MasteredBadge (when complete)
        │   │
        │   └── LevelUnlockModal.js ← Celebration
        │
        ├── ProgressDashboard.js ← Overall progress
        │   ├── OverallProgressBar.js
        │   ├── LevelProgressCards.js
        │   └── RecommendedNext.js
        │
        └── ConventionPractice.js ← Practice integration
            ├── PracticeHand.js
            ├── FeedbackDisplay.js
            └── MasteryModal.js ← Celebrate mastery
```

## Performance Considerations

### Caching Strategy

```
Frontend Cache:
  └─> Convention metadata (changes rarely)
      • Fetch once on app load
      • Store in React context/state
      • Refresh only on version change

  └─> User progress (changes frequently)
      • Fetch on page load
      • Update optimistically after practice
      • Refresh periodically (every 5 min)
      • Invalidate on mastery

Backend Cache:
  └─> ConventionRegistry (static)
      • Singleton instance
      • Never changes during runtime
      • No database queries needed

  └─> User progress (dynamic)
      • Query database each time
      • Use indexed queries
      • Utilize views for aggregation
```

### Database Optimization

```
Indexes:
  ├─> user_convention_progress(user_id)
  ├─> user_convention_progress(status)
  ├─> convention_practice_history(user_id, convention_id)
  └─> convention_practice_history(timestamp)

Views (Pre-computed):
  ├─> v_user_convention_summary
  │     SELECT user_id, COUNT(*), AVG(accuracy)
  │     GROUP BY user_id
  │
  └─> v_user_level_progress
        SELECT user_id, level, completion_pct
        GROUP BY user_id, level
```

## Testing Strategy

```
Unit Tests:
  ├─> ConventionRegistry
  │     • get_convention()
  │     • check_prerequisites_met()
  │     • get_unlocked_conventions()
  │     • get_next_recommended()
  │
  ├─> SkillTreeManager
  │     • check_level_unlocked()
  │     • get_user_skill_tree_progress()
  │     • get_next_recommended_level()
  │
  └─> Database operations
        • INSERT/UPDATE progress
        • Mastery detection
        • Accuracy calculation

Integration Tests:
  ├─> API endpoints
  │     • /api/conventions/by-level
  │     • /api/conventions/unlocked
  │     • /api/conventions/record-practice
  │
  └─> Complete user flows
        • Start → Practice → Master → Unlock next level
        • Prerequisite checking
        • Level unlocking

E2E Tests (Frontend):
  └─> User journey
        • View conventions page
        • See locked/unlocked states
        • Practice convention
        • See mastery celebration
        • Verify next level unlocks
```

---

**Document Version:** 1.0
**Created:** October 11, 2025
**Purpose:** System architecture reference
