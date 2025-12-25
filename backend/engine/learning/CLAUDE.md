# Learning & Analytics System

**Specialist Area:** User progress tracking, bid evaluation, feedback, dashboard analytics

## Scope

This area covers the learning and feedback systems. You are responsible for:

- **Bid evaluation:** Scoring user bids (0-10), optimal/acceptable/error ratings
- **Feedback generation:** Improvement hints, mistake explanations
- **Analytics:** Dashboard statistics, skill progression
- **Achievements:** Celebration notifications, milestones
- **User tracking:** Per-user progress isolation

## Key Files

### Backend
```
backend/engine/
├── feedback/
│   └── bidding_feedback.py    # Bid evaluation (0-10 scoring)
└── learning/
    ├── analytics_api.py       # Dashboard endpoint
    ├── learning_path_api.py   # Skill progression API
    ├── skill_tree.py          # Convention mastery tracking
    ├── mistake_analyzer.py    # Error pattern detection
    ├── error_categorizer.py   # Categorize mistake types
    ├── celebration_manager.py # Achievement notifications
    └── user_manager.py        # User progress tracking
```

### Frontend
```
frontend/src/components/learning/
├── LearningDashboard.js       # Main dashboard modal
├── BiddingQualityBar.js       # Quality visualization
├── RecentDecisionsCard.js     # Last 10 bids display
└── CelebrationNotification.js # Achievement popups
```

### Database Tables
```sql
bidding_decisions  -- User bid history with scores
hand_analyses      -- Hand evaluation records
game_sessions      -- Session tracking
session_hands      -- Individual hand results
```

## Architecture

### Bid Evaluation Flow
```
User submits bid → /api/evaluate-bid
  → bidding_feedback.py.evaluate_bid()
  → Get optimal bid from BiddingEngine
  → Compare user bid vs optimal
  → Calculate score (0-10)
  → Generate feedback hints
  → Store in bidding_decisions table
  → Return evaluation to frontend
```

### Dashboard Flow
```
User opens dashboard → /api/analytics/dashboard?user_id=X
  → analytics_api.py.get_dashboard_data()
  → Query bidding_decisions for user
  → Calculate statistics:
      - Optimal rate (score 10)
      - Average score
      - Error rate (score < 4)
      - Trend analysis
  → Return to LearningDashboard component
```

### Scoring System

| Score | Rating | Meaning |
|-------|--------|---------|
| 10 | Optimal | Perfect bid |
| 7-9 | Acceptable | Reasonable alternative |
| 4-6 | Suboptimal | Works but not ideal |
| 0-3 | Error | Significant mistake |

## Common Tasks

### Improve Feedback Quality
1. Identify feedback type (hint, explanation, correction)
2. Update `bidding_feedback.py` feedback generation
3. Test with various bid scenarios
4. Verify frontend displays correctly

### Fix Dashboard Statistics
1. Check `analytics_api.py` query logic
2. Verify SQL aggregations
3. Test with multiple users
4. Confirm user isolation

### Add New Achievement
1. Define achievement in `celebration_manager.py`
2. Add trigger condition
3. Create frontend notification in `CelebrationNotification.js`
4. Test achievement flow

### Fix Mistake Analysis
1. Review `mistake_analyzer.py` patterns
2. Update `error_categorizer.py` categories
3. Verify correct categorization
4. Test edge cases

## Testing

```bash
# Backend tests
cd backend
pytest tests/unit/test_bidding_feedback.py -v
pytest tests/integration/test_analytics*.py -v

# Frontend tests
cd frontend
npm test -- --testPathPattern=learning
npm run test:e2e -- --grep "dashboard"
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/evaluate-bid` | POST | Evaluate user's bid |
| `/api/analytics/dashboard` | GET | Dashboard statistics |
| `/api/learning/skill-tree` | GET | Convention mastery |
| `/api/learning/progress` | GET | Overall progress |

### Evaluate Bid Request
```json
{
  "user_id": "user123",
  "user_bid": "2♠",
  "hand": [...],
  "auction_history": [...],
  "position": "South",
  "vulnerability": "None"
}
```

### Evaluate Bid Response
```json
{
  "score": 7,
  "rating": "acceptable",
  "optimal_bid": "3♠",
  "feedback": "Good bid! A jump to 3♠ would show extra values.",
  "hints": ["Consider your point count", "Partner showed 15-17 HCP"]
}
```

## Dependencies

- **Uses:** BiddingEngine (for optimal bid calculation)
- **Uses:** Database (bidding_decisions, users tables)
- **Used by:** server.py endpoints, frontend dashboard

## Multi-User Isolation

**Critical:** All queries must filter by `user_id`:
```python
# CORRECT
cursor.execute(
    "SELECT * FROM bidding_decisions WHERE user_id = ?",
    (user_id,)
)

# WRONG - leaks data between users
cursor.execute("SELECT * FROM bidding_decisions")
```

## Gotchas

- Dashboard uses `key={Date.now()}` for forced remount - ensures fresh data
- Bid evaluation depends on BiddingEngine's optimal bid accuracy
- Statistics calculated on-demand, not cached
- Achievement triggers should be idempotent (don't double-award)
- Error categorization affects learning path recommendations

## Reference Documents

- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Bidding system (for feedback accuracy)
- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Play mechanics reference
