# Bidding Feedback System

**Last Updated:** 2026-01-02

## Overview

The bidding feedback system provides real-time educational feedback after each user bid. It evaluates bids against optimal play and provides:
- Correctness ratings (optimal, acceptable, suboptimal, error)
- Score (0-10 scale)
- Error categorization for learning insights
- Helpful hints with glossary-linked bridge terms

## Components

### Frontend

**BidFeedbackPanel** (`frontend/src/components/bridge/BidFeedbackPanel.jsx`)

Displays structured feedback after each user bid with:
- Color-coded correctness levels
- Auto-linked bridge terms via TermHighlight component
- Key concept display for educational context
- Dismissible interface with smooth animations

### Backend

**BiddingFeedbackGenerator** (`backend/engine/feedback/bidding_feedback.py`)

Core feedback evaluation logic:
- Compares user bid against optimal bid from AI engine
- Categorizes errors (wrong level, wrong strain, missed opportunity, etc.)
- Generates educational hints based on error type
- Stores decisions in database for analytics

**ErrorCategorizer** (`backend/engine/learning/error_categorizer.py`)

Classifies bidding mistakes into actionable categories:
- `wrong_level`: Too high or too low
- `wrong_strain`: NT vs suit, major vs minor
- `missed_opportunity`: Passed when should bid
- `slam_bidding`: Missed slam, overbid, missed Blackwood
- `strength_evaluation`: Overvalue or undervalue

## API

### POST /api/evaluate-bid

Evaluates a user's bid and returns structured feedback.

**Request:**
```json
{
  "user_bid": "1NT",
  "auction_history": ["1♠"],
  "current_player": "South",
  "user_id": 1,
  "feedback_level": "intermediate"
}
```

**Response:**
```json
{
  "feedback": {
    "correctness": "suboptimal",
    "score": 6.0,
    "optimal_bid": "2♠",
    "helpful_hint": "With 4+ card support, raise partner's major suit.",
    "key_concept": "Trump support",
    "error_category": "wrong_strain",
    "error_subcategory": "major_vs_minor"
  },
  "user_message": "✗ 2♠ would be better than 1NT...",
  "was_correct": false
}
```

## Correctness Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| optimal | 10 | Perfect bid |
| acceptable | 7-9 | Good alternative, slight variation |
| suboptimal | 4-6 | Not recommended, better options exist |
| error | 0-3 | Significant mistake |

## Error Categories

### Slam Bidding Errors

Added in 2026-01-02 update to support improved slam detection:

- `missed_slam`: Stopped at game with slam values
- `overbid_slam`: Bid slam with insufficient values
- `missed_blackwood`: Jumped to slam without ace-asking
- `overbid_grand`: Bid grand slam without sufficient controls
- `missed_grand`: Stopped at small slam with grand slam values

### Standard Errors

- `wrong_level`: Bid too high or too low
- `wrong_strain`: Wrong suit or NT vs suit
- `missed_opportunity`: Passed a biddable hand
- `premature_bid`: Bid when should pass
- `wrong_meaning`: Misunderstood convention

## Integration

### Glossary Integration

The BidFeedbackPanel uses TermHighlight to auto-detect and link bridge terms:
- Recognizes convention names (Blackwood, Stayman, etc.)
- Links concepts (HCP, balanced hand, etc.)
- Opens glossary drawer on click

### Dashboard Analytics

All evaluated bids are stored in `bidding_decisions` table:
- Tracks user progress over time
- Identifies recurring error patterns
- Powers learning insights in dashboard

## Related Files

- `frontend/src/components/bridge/BidFeedbackPanel.jsx` - UI component
- `frontend/src/components/bridge/BidFeedbackPanel.css` - Styling
- `backend/engine/feedback/bidding_feedback.py` - Core feedback logic
- `backend/engine/learning/error_categorizer.py` - Error classification
- `backend/server.py` - API endpoint
