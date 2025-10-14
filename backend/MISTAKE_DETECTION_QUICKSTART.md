# Common Mistake Detection System - Quick Start Guide

**Status:** Backend Complete ✅
**Last Updated:** 2025-10-13

---

## 🚀 Getting Started

### 1. Initialize the Database

```bash
cd backend
sqlite3 bridge.db < database/schema_user_management.sql
```

This creates all necessary tables:
- `users`, `user_settings`, `user_gamification`
- `practice_sessions`, `practice_history`
- `mistake_patterns`, `improvement_milestones`
- `error_categories`, `celebration_templates`
- `streak_history`

### 2. Register API Endpoints in server.py

Add these lines to `server.py`:

```python
from engine.learning.analytics_api import register_analytics_endpoints

# After creating Flask app
register_analytics_endpoints(app)
```

### 3. Create Your First User

**Using the API:**
```bash
curl -X POST http://localhost:5000/api/user/create \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "email": "player@example.com", "display_name": "Player One"}'
```

**Or in Python:**
```python
from engine.learning.user_manager import get_user_manager

user_manager = get_user_manager()
user_id = user_manager.create_user("player1", "player@example.com", "Player One")
print(f"Created user: {user_id}")
```

---

## 📋 API Endpoints

### Practice Recording

**POST /api/practice/record**
Record a practice hand with automatic error categorization and pattern analysis.

```json
{
  "user_id": 1,
  "convention_id": "stayman",
  "hand": {...},
  "user_bid": "2♦",
  "correct_bid": "2♣",
  "was_correct": false,
  "auction_context": {...},
  "hints_used": 0,
  "time_taken_seconds": 45
}
```

**Response:**
```json
{
  "success": true,
  "practice_id": 123,
  "xp_earned": 5,
  "user_stats": {
    "total_xp": 505,
    "current_level": 2,
    "current_streak": 3,
    "total_hands": 45,
    "overall_accuracy": 0.82
  },
  "feedback": {
    "category": "wrong_strain",
    "subcategory": "chose_wrong_suit",
    "hint": "With 4+ clubs and only 3 diamonds, prefer the longer suit!"
  }
}
```

### Dashboard Data

**GET /api/analytics/dashboard?user_id=1**
Get comprehensive dashboard summary including stats, insights, celebrations, and recommendations.

**Response:**
```json
{
  "user_id": 1,
  "user_stats": {
    "total_xp": 1250,
    "current_level": 3,
    "current_streak": 7,
    "total_hands": 120,
    "overall_accuracy": 0.78,
    "recent_accuracy": 0.85
  },
  "insights": {
    "total_patterns": 8,
    "active_patterns": 3,
    "improving_patterns": 2,
    "resolved_patterns": 3,
    "needs_attention_patterns": 1,
    "overall_trend": "improving",
    "top_growth_areas": [
      {
        "category": "wrong_level",
        "category_name": "Getting comfortable with when to bid higher",
        "recent_occurrences": 5,
        "accuracy": 0.65,
        "recommended_hands": 15
      }
    ],
    "recent_wins": [
      {
        "category": "wrong_strain",
        "category_name": "Learning which suit to bid",
        "accuracy": 0.92,
        "improvement_rate": 0.35,
        "status": "resolved"
      }
    ],
    "recommended_focus": "Getting comfortable with when to bid higher"
  },
  "pending_celebrations": [
    {
      "id": 42,
      "milestone_type": "streak_milestone",
      "title": "7-Day Streak!",
      "message": "A full week of practice! You're dedicated!",
      "emoji": "🔥",
      "xp_reward": 50,
      "achieved_at": "2025-10-13T14:30:00"
    }
  ],
  "practice_recommendations": [
    {
      "convention_id": "jacoby_transfers",
      "error_category": "wrong_level",
      "category_name": "Getting comfortable with when to bid higher",
      "recommended_hands": 15,
      "status": "needs_attention",
      "accuracy": 0.65,
      "priority": 1,
      "reason": "Let's work on Bid Level - you're at 65% and improving!"
    }
  ]
}
```

### Mistake Analysis

**GET /api/analytics/mistakes?user_id=1&status=needs_attention**
Get mistake patterns filtered by status.

Status options: `active`, `improving`, `resolved`, `needs_attention`

### Celebrations

**GET /api/analytics/celebrations?user_id=1&pending_only=true**
Get pending (unshown) celebrations.

**POST /api/analytics/acknowledge-celebration**
Mark celebration as acknowledged.

```json
{
  "milestone_id": 42
}
```

### Practice Recommendations

**GET /api/practice/recommended?user_id=1&max=5**
Get personalized practice recommendations based on mistake patterns.

---

## 🔧 Python Usage Examples

### Recording Practice with Error Categorization

```python
from engine.learning.error_categorizer import get_error_categorizer
from engine.learning.mistake_analyzer import get_mistake_analyzer
from engine.hand import Hand

# Categorize an error
error_categorizer = get_error_categorizer()
categorized = error_categorizer.categorize(
    hand=my_hand,
    user_bid="Pass",
    correct_bid="1♥",
    convention_id="opening_bids",
    auction_context=context
)

print(f"Category: {categorized.category}")
print(f"Hint: {categorized.hint}")

# After recording in database, analyze pattern
mistake_analyzer = get_mistake_analyzer()
pattern_id = mistake_analyzer.analyze_practice_hand(user_id=1, practice_id=123)
```

### Creating Celebrations

```python
from engine.learning.celebration_manager import get_celebration_manager

celebration_manager = get_celebration_manager()

# Celebrate a 7-day streak
milestone_id = celebration_manager.create_streak_milestone(
    user_id=1,
    streak_days=7
)

# Celebrate pattern resolution
milestone_id = celebration_manager.create_pattern_resolved_milestone(
    user_id=1,
    error_category="wrong_level",
    category_name="Bid Level",
    old_accuracy=0.65,
    new_accuracy=0.92
)

# Get pending celebrations
pending = celebration_manager.get_pending_celebrations(user_id=1)
for celebration in pending:
    print(f"{celebration.emoji} {celebration.title}: {celebration.message}")
```

### Generating Insights

```python
from engine.learning.mistake_analyzer import get_mistake_analyzer

analyzer = get_mistake_analyzer()

# Get comprehensive insights
insights = analyzer.get_insight_summary(user_id=1)
print(f"Overall trend: {insights.overall_trend}")
print(f"Patterns resolved: {insights.resolved_patterns}")

# Get practice recommendations
recommendations = analyzer.get_practice_recommendations(user_id=1, max_recommendations=5)
for rec in recommendations:
    print(f"- {rec['category_name']}: {rec['reason']}")
```

### User Management

```python
from engine.learning.user_manager import get_user_manager

user_manager = get_user_manager()

# Create user
user_id = user_manager.create_user("player1", "player@example.com")

# Update streak
user_manager.update_streak(user_id)

# Add XP (handles level-ups automatically)
user_manager.add_xp(user_id, xp_amount=50)

# Get stats
stats = user_manager.get_user_stats(user_id)
print(f"Level {stats.current_level} - {stats.total_xp} XP")
print(f"Streak: {stats.current_streak_days} days")
```

---

## 🎯 Error Categories

The system comes with 8 pre-defined error categories (extensible via database):

1. **wrong_level** - "Getting comfortable with when to bid higher"
2. **wrong_strain** - "Learning which suit to bid"
3. **wrong_meaning** - "Clarifying what bids mean"
4. **missed_fit** - "Spotting when you have a great fit with partner"
5. **strength_evaluation** - "Getting better at counting your hand strength"
6. **distribution_awareness** - "Understanding how shape affects bidding"
7. **premature_bid** - "Learning the right time to make your bid"
8. **missed_opportunity** - "Remembering when to use conventions"

### Adding New Categories

```sql
INSERT INTO error_categories (category_id, display_name, friendly_name, description, sort_order)
VALUES ('new_category', 'Display Name', 'Friendly encouraging name', 'Description', 9);
```

---

## 🎉 Celebration Templates

Pre-defined templates for milestones:

- **First correct** - First time getting a convention right (25 XP)
- **Pattern resolved** - Mastered a mistake pattern (50 XP)
- **Accuracy milestones** - 70%, 80%, 90%, 95% accuracy (30 XP)
- **Streak milestones** - 3, 7, 14, 30, 60, 100 day streaks (20-150 XP)
- **Hands milestones** - 10, 25, 50, 100, 250, 500, 1000 hands (20-100 XP)
- **Improvement** - 20%+ improvement in category (35 XP)

### Adding New Templates

```sql
INSERT INTO celebration_templates (template_id, milestone_type, title_template, message_template, emoji, xp_reward)
VALUES ('custom_milestone', 'achievement_type', 'Title with {variable}', 'Message with {variable}', '🎊', 50);
```

---

## 🔍 Testing the System

### 1. Test User Creation

```bash
curl -X POST http://localhost:5000/api/user/create \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "display_name": "Test User"}'
```

### 2. Test Practice Recording

```bash
curl -X POST http://localhost:5000/api/practice/record \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "convention_id": "stayman",
    "user_bid": "Pass",
    "correct_bid": "2♣",
    "was_correct": false,
    "hints_used": 0
  }'
```

### 3. Test Dashboard

```bash
curl http://localhost:5000/api/analytics/dashboard?user_id=1
```

### 4. Test Celebrations

```bash
curl http://localhost:5000/api/analytics/celebrations?user_id=1
```

---

## 📊 Database Views

Pre-built views for common queries:

### v_user_progress_summary
Complete user progress overview with patterns resolved, hands practiced, etc.

```sql
SELECT * FROM v_user_progress_summary WHERE user_id = 1;
```

### v_recent_activity
Activity summary for last 7 days.

```sql
SELECT * FROM v_recent_activity WHERE user_id = 1;
```

### v_active_mistake_patterns
Active patterns that need attention.

```sql
SELECT * FROM v_active_mistake_patterns WHERE user_id = 1;
```

### v_pending_celebrations
Unshown celebrations.

```sql
SELECT * FROM v_pending_celebrations WHERE user_id = 1;
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LEARNING ANALYTICS SYSTEM                │
└─────────────────────────────────────────────────────────────┘

┌───────────────┐     ┌────────────────┐     ┌──────────────────┐
│               │     │                │     │                  │
│ User Manager  │────▶│ Practice       │────▶│ Error           │
│               │     │ Recording      │     │ Categorizer     │
│ - Users       │     │ - Sessions     │     │ - Categorize    │
│ - Settings    │     │ - History      │     │ - Context       │
│ - Stats       │     │ - XP tracking  │     │ - Hints         │
│               │     │                │     │                  │
└───────────────┘     └────────────────┘     └──────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │                 │
                    │ Mistake Pattern │
                    │ Analyzer        │
                    │                 │
                    │ - Aggregate     │
                    │ - Analyze       │
                    │ - Recommend     │
                    │                 │
                    └─────────────────┘
                              │
              ┌───────────────┴────────────────┐
              ▼                                ▼
    ┌──────────────────┐            ┌────────────────────┐
    │                  │            │                    │
    │ Celebration      │            │ Analytics API      │
    │ Manager          │            │                    │
    │                  │            │ - Dashboard        │
    │ - Milestones     │            │ - Insights         │
    │ - Templates      │            │ - Practice Queue   │
    │ - Rewards        │            │ - Celebrations     │
    │                  │            │                    │
    └──────────────────┘            └────────────────────┘
```

---

## ⚙️ Configuration

### User Settings

Users can configure:
- `tracking_enabled` - Enable/disable mistake tracking (default: TRUE)
- `email_weekly_summary` - Weekly email summaries (default: TRUE)
- `celebrate_achievements` - Show celebrations (default: TRUE)
- `difficulty_preference` - 'easy', 'adaptive', 'challenge' (default: 'adaptive')
- `daily_goal_hands` - Target hands per day (default: 10)

### XP and Leveling

- **Practice XP**: 10 XP for correct, 5 XP for attempt
- **Level progression**: Level 1→2 = 500 XP, 2→3 = 700 XP, 3→4 = 900 XP, etc.
- **Milestone XP**: 20-150 XP depending on achievement

### Pattern Status Thresholds

- **Resolved**: 90%+ accuracy with 10+ attempts
- **Needs Attention**: 5+ recent occurrences and <60% accuracy
- **Improving**: 10%+ improvement rate
- **Active**: Default status for new patterns

---

## 🐛 Troubleshooting

### Database Not Found

```bash
# Make sure you're in the backend directory
cd backend
# Initialize the database
sqlite3 bridge.db < database/schema_user_management.sql
```

### API Endpoints Not Working

```python
# Verify endpoints are registered in server.py
from engine.learning.analytics_api import register_analytics_endpoints
register_analytics_endpoints(app)
```

### Tables Already Exist

The schema uses `CREATE TABLE IF NOT EXISTS`, so it's safe to run multiple times.
If you need to reset:

```bash
# Backup existing data first!
sqlite3 bridge.db ".dump" > backup.sql

# Drop and recreate (WARNING: deletes all data)
sqlite3 bridge.db "DROP TABLE IF EXISTS users; DROP TABLE IF EXISTS practice_history; ..."
sqlite3 bridge.db < database/schema_user_management.sql
```

---

## 📚 Further Reading

- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Complete implementation details
- [COMMON_MISTAKE_SYSTEM_DESIGN.md](../COMMON_MISTAKE_SYSTEM_DESIGN.md) - Original design document
- [LEARNING_PLATFORM_STRATEGY.md](../docs/LEARNING_PLATFORM_STRATEGY.md) - Learning principles

---

**Questions?** Check the implementation status document or API code comments for detailed information about each component.
