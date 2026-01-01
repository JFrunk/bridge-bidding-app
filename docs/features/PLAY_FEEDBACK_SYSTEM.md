# Play Feedback System

**Created:** 2026-01-01
**Status:** Implemented
**Module:** `backend/engine/feedback/play_feedback.py`

## Overview

The Play Feedback System provides real-time evaluation of card play decisions using DDS (Double Dummy Solver) for optimal play analysis. It mirrors the bidding feedback system but for card play.

## Key Features

- **DDS-Based Evaluation**: Uses industry-standard DDS for perfect play analysis
- **Fast Performance**: <1ms per solve on Linux production
- **Scoring System**: 0-10 scale with correctness levels (optimal, good, suboptimal, blunder)
- **Trick Cost Calculation**: Shows exactly how many tricks a suboptimal play costs
- **Educational Feedback**: Provides hints and explanations for learning
- **Database Tracking**: Stores evaluations for dashboard analytics

## Architecture

```
User plays card → PlayFeedbackGenerator.evaluate_play()
                           ↓
              ┌───────────────────────────┐
              │ DDS Available (Linux)?    │
              └───────────┬───────────────┘
                   Yes    │    No
                    ↓     │     ↓
           solve_board()  │  MinimaxPlayAI
                    ↓     │     ↓
              ┌───────────────────────────┐
              │ Compare user card to      │
              │ optimal cards             │
              └───────────────────────────┘
                          ↓
              ┌───────────────────────────┐
              │ Generate PlayFeedback     │
              │ - correctness level       │
              │ - score (0-10)            │
              │ - tricks cost             │
              │ - reasoning/hints         │
              └───────────────────────────┘
```

## API

### Endpoint: `/api/evaluate-play`

**Method:** POST

**Request Body:**
```json
{
  "card": {"rank": "A", "suit": "♠"},
  "position": "S",
  "user_id": 1,
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "dds_available": true,
  "score": 10.0,
  "correctness": "optimal",
  "optimal_cards": ["A♠"],
  "tricks_cost": 0,
  "tricks_with_user_card": 10,
  "tricks_with_optimal": 10,
  "reasoning": "A♠ is the best opening lead.",
  "play_category": "opening_lead",
  "key_concept": "Opening lead principles",
  "difficulty": "intermediate",
  "user_message": "Excellent! A♠ is perfect here."
}
```

## Correctness Levels

| Level | Description | Score Range |
|-------|-------------|-------------|
| `optimal` | Perfect play - achieves maximum tricks | 10 |
| `good` | Close to optimal (0-1 trick cost) | 8 |
| `suboptimal` | Costs tricks but not terrible | 3-5 |
| `blunder` | Significant trick loss (3+) | 0-3 |
| `illegal` | Not a legal play | 0 |

## Play Categories

- `opening_lead` - First card of the hand
- `following_suit` - Must follow suit led
- `discarding` - Void in led suit, no trump
- `trumping` - Ruffing when void
- `overruffing` - Ruff over opponent's ruff
- `sluffing` - Discard when could trump

## Database Schema

```sql
CREATE TABLE play_decisions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id TEXT,
    position TEXT NOT NULL,
    trick_number INTEGER,
    user_card TEXT NOT NULL,
    optimal_card TEXT,
    score REAL NOT NULL,
    rating TEXT NOT NULL,
    tricks_cost INTEGER DEFAULT 0,
    tricks_with_user_card INTEGER,
    tricks_with_optimal INTEGER,
    contract TEXT,
    is_declarer_side BOOLEAN,
    play_category TEXT,
    key_concept TEXT,
    difficulty TEXT,
    feedback TEXT,
    helpful_hint TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Performance

| Platform | AI Type | Speed | Accuracy |
|----------|---------|-------|----------|
| Linux | DDS | <1ms | 100% |
| macOS | Minimax | 50-200ms | 70-80% |

## Usage Example

```python
from engine.feedback.play_feedback import get_play_feedback_generator

# Get the singleton generator
gen = get_play_feedback_generator(use_dds=True)

# Evaluate a play
feedback = gen.evaluate_play(play_state, user_card, position)

# Check results
print(f"Score: {feedback.score}/10")
print(f"Correctness: {feedback.correctness.value}")
print(f"Message: {feedback.to_user_message()}")

# Store in database
feedback = gen.evaluate_and_store(
    user_id=1,
    play_state=play_state,
    user_card=user_card,
    position='S',
    session_id='session-123'
)
```

## Related Files

- `backend/engine/feedback/play_feedback.py` - Main module
- `backend/engine/feedback/__init__.py` - Exports
- `backend/engine/play/ai/dds_ai.py` - DDS integration
- `backend/migrations/006_add_play_decisions_table.sql` - Database schema
- `backend/server.py` - API endpoint at line 3321
