# Hand History & DDS Analysis Replay

## Overview

The Hand History feature allows users to review their recent hands and analyze any play using the Double Dummy Solver (DDS). This provides detailed feedback on opening leads and card play decisions.

## Features

### Hand History List
- Shows the last 15 completed hands in My Progress dashboard
- Each hand displays:
  - Contract (e.g., "4♠ by S")
  - Result (e.g., "=", "+1", "-2")
  - User's role (Declarer, Defender, or Dummy)
  - Score
  - Timestamp
- Click any hand to open the replay modal

### Hand Review Modal
- Displays all 4 hands in compass layout
- Shows contract, vulnerability, and dealer
- User's hand is highlighted
- Trick-by-trick navigation
- "Analyze Opening Lead" button for quick opening lead analysis

### DDS Analysis
- Click any card in any trick to analyze that play
- Shows:
  - Rating (Optimal, Good, Suboptimal, Blunder)
  - Tricks lost compared to optimal
  - All alternative plays ranked by DDS evaluation
- DDS runs on-demand (not pre-computed)
- Note: DDS only available on Linux production server

## API Endpoints

### GET /api/hand-history
Get recent hands for a user.

**Query Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Max hands to return (default 15, max 50)

**Response:**
```json
{
  "user_id": 1,
  "hands": [
    {
      "id": 123,
      "contract": "4♠ by S",
      "result": "+1",
      "made": true,
      "score": 450,
      "user_was_declarer": true,
      "can_replay": true,
      "played_at": "2024-01-01T12:00:00"
    }
  ],
  "count": 15
}
```

### GET /api/hand-detail
Get full detail for a specific hand.

**Query Parameters:**
- `hand_id` (required): Hand ID

**Response:**
```json
{
  "hand_id": 123,
  "contract": "4♠ by S",
  "deal": {
    "N": {"hand": [{"rank": "A", "suit": "S"}, ...]},
    "E": {...},
    "S": {...},
    "W": {...}
  },
  "auction": [...],
  "play_history": [
    {"player": "W", "rank": "5", "suit": "H"},
    ...
  ]
}
```

### POST /api/analyze-play
Analyze a specific play using DDS.

**Request Body:**
```json
{
  "hand_id": 123,
  "trick_number": 1,
  "play_index": 0
}
```

Or for opening lead:
```json
{
  "hand_id": 123,
  "opening_lead": true
}
```

**Response:**
```json
{
  "hand_id": 123,
  "trick_number": 1,
  "actual_play": {"rank": "5", "suit": "H"},
  "dds_available": true,
  "optimal_tricks": 10,
  "actual_tricks": 9,
  "tricks_lost": 1,
  "rating": "suboptimal",
  "alternatives": [
    {"card": {"rank": "K", "suit": "H"}, "tricks": 10, "is_actual": false},
    {"card": {"rank": "5", "suit": "H"}, "tricks": 9, "is_actual": true}
  ]
}
```

## Database

Uses existing `session_hands` table - no new tables required.

**Relevant columns:**
- `deal_data` (JSON): All 4 hands
- `auction_history` (JSON): Bidding sequence
- `play_history` (JSON): All 52 cards played in order

**Storage:** ~2.5 KB per hand (already being stored)

## Components

### Frontend
- `HandHistoryCard.js` - Individual hand card display
- `HandHistoryCard.css` - Card styling
- `HandReviewModal.js` - Full hand replay modal
- `HandReviewModal.css` - Modal styling
- Integration in `LearningDashboard.js`

### Backend
- `analytics_api.py` - API endpoint handlers
  - `get_hand_history()` - List recent hands
  - `get_hand_detail()` - Get full hand data
  - `analyze_play()` - DDS analysis

## Limitations

1. **DDS on macOS**: DDS crashes on macOS M1/M2 chips. Analysis returns a graceful fallback message instead.

2. **Data Availability**: Hands must be played through the complete flow (bidding + all 13 tricks) to have replay data available.

3. **Opening Lead Analysis**: Most reliable analysis. Other trick analyses work but leader determination for non-opening tricks is simplified.

## Future Enhancements

- Pre-compute opening lead analysis on hand completion
- Add opening lead analysis prompt after each hand
- Export hand records in PBN format
- Share hands with other users
