# Bidding API Contract

**Last Updated:** 2025-12-30
**Status:** Authoritative specification for bidding-related API endpoints

---

## Overview

This document defines the **request and response formats** for all bidding-related API endpoints. Both frontend and backend code MUST conform to these specifications.

---

## Data Formats

### Auction History Format

The backend accepts auction history in **two formats** for backward compatibility:

#### Format 1: String Array (Preferred)
```json
["1NT", "Pass", "2♣", "Pass"]
```

#### Format 2: Object Array (Accepted)
```json
[
  {"bid": "1NT", "explanation": "Opening 1NT with 15-17 HCP"},
  {"bid": "Pass", "explanation": ""},
  {"bid": "2♣", "explanation": "Stayman convention"}
]
```

**Backend Normalization:** The server normalizes object format to string format internally:
```python
auction_history = [
    item.get('bid', 'Pass') if isinstance(item, dict) else item
    for item in auction_history_raw
]
```

### Bid String Format

Valid bid strings:
- **Suit bids:** `1♣`, `1♦`, `1♥`, `1♠`, `2♣`, ... `7♠`
- **No Trump:** `1NT`, `2NT`, `3NT`, `4NT`, `5NT`, `6NT`, `7NT`
- **Pass:** `Pass`
- **Double:** `X`
- **Redouble:** `XX`

**Suit symbols:** Use Unicode symbols `♣`, `♦`, `♥`, `♠` (not letters C, D, H, S)

---

## Endpoints

### POST /api/get-next-bid

Get the AI's next bid for a given position.

#### Request

```json
{
  "auction_history": ["1NT", "Pass"],
  "current_player": "South",
  "dealer": "North",
  "explanation_level": "detailed"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `auction_history` | array | Yes | Bids made so far (strings or objects) |
| `current_player` | string | Yes | Position making the bid: `North`, `East`, `South`, `West` |
| `dealer` | string | No | Who dealt. Default: inferred from auction length |
| `explanation_level` | string | No | `simple`, `detailed`, `expert`, `convention_only` |

#### Response (200 OK)

```json
{
  "bid": "2♣",
  "explanation": "Stayman convention asking for 4-card major",
  "player": "South"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `bid` | string | The AI's bid |
| `explanation` | string | Human-readable explanation |
| `player` | string | Position that made the bid |

#### Errors

| Code | Condition |
|------|-----------|
| 400 | Deal not made yet |
| 500 | Server error (check logs) |

---

### POST /api/get-next-bid-structured

Get the AI's next bid with structured explanation data.

#### Request

```json
{
  "auction_history": ["1NT"],
  "current_player": "East"
}
```

#### Response (200 OK)

```json
{
  "bid": "Pass",
  "explanation": {
    "primary_reason": "Insufficient points for action",
    "convention": null,
    "forcing_status": null,
    "hand_evaluation": {
      "hcp": 8,
      "total_points": 9
    }
  }
}
```

---

### POST /api/evaluate-bid

Evaluate a user's bid and provide feedback. Does NOT modify game state.

#### Request

```json
{
  "user_bid": "2♣",
  "auction_history": ["1NT", "Pass"],
  "current_player": "South",
  "user_id": 1,
  "session_id": "abc123",
  "feedback_level": "intermediate"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_bid` | string | Yes | The bid the user made |
| `auction_history` | array | Yes | Bids BEFORE user's bid |
| `current_player` | string | No | Default: `South` |
| `user_id` | int | No | For analytics tracking |
| `session_id` | string | No | Current session ID |
| `feedback_level` | string | No | `beginner`, `intermediate`, `expert` |

#### Response (200 OK)

```json
{
  "is_correct": true,
  "score": 10,
  "rating": "optimal",
  "optimal_bid": "2♣",
  "user_message": "Correct! Stayman is the right call here.",
  "decision_id": 12345
}
```

| Field | Type | Description |
|-------|------|-------------|
| `is_correct` | bool | Whether user's bid matches optimal |
| `score` | int | 0-10 score |
| `rating` | string | `optimal`, `acceptable`, `suboptimal`, `error` |
| `optimal_bid` | string | What AI would have bid |
| `user_message` | string | Feedback message for display |
| `decision_id` | int | Database ID for analytics |

---

### POST /api/get-feedback

Legacy feedback endpoint. Returns feedback on user's last bid.

#### Request

```json
{
  "auction_history": ["1NT", "Pass", "2♣"],
  "explanation_level": "detailed"
}
```

**Note:** The last bid in `auction_history` is treated as the user's bid.

#### Response (200 OK)

```json
{
  "feedback": "✅ Correct! Your bid of 2♣ is optimal.\n\nStayman convention..."
}
```

---

## Frontend Implementation Guide

### Sending Auction History

**Always extract bid strings when calling API:**

```javascript
// CORRECT - extract bid strings
const response = await fetch('/api/get-next-bid', {
  body: JSON.stringify({
    auction_history: auction.map(a => a.bid),  // ✅ Extract strings
    current_player: currentPlayer
  })
});

// ALSO WORKS - backend normalizes objects
const response = await fetch('/api/get-next-bid', {
  body: JSON.stringify({
    auction_history: auction,  // Objects will be normalized
    current_player: currentPlayer
  })
});
```

### Storing Auction State

Frontend stores auction as objects for display purposes:

```javascript
const [auction, setAuction] = useState([]);

// When user bids
setAuction([...auction, {
  bid: userBid,
  explanation: 'Your bid.',
  player: 'South'
}]);

// When AI bids (response from server)
setAuction([...auction, data]);  // data = {bid, explanation, player}
```

---

## Testing Requirements

### Regression Tests

The following test file verifies format handling:
```
backend/tests/regression/test_auction_history_format_bug_12302025.py
```

Run with:
```bash
cd backend
source venv/bin/activate
pytest tests/regression/test_auction_history_format_bug_12302025.py -v
```

### Format Compatibility Matrix

| Input Format | /api/get-next-bid | /api/evaluate-bid | /api/get-feedback |
|--------------|-------------------|-------------------|-------------------|
| String array | ✅ | ✅ | ✅ |
| Object array | ✅ | ✅ | ✅ |
| Mixed array | ✅ | ✅ | ✅ |
| Empty array | ✅ | ✅ | ✅ |

---

## Error Handling

### Common Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Deal has not been made yet` | Called before `/api/deal-hands` | Call deal-hands first |
| `unhashable type: 'dict'` | Backend not normalizing (old code) | Update server.py |
| `'dict' object has no attribute 'endswith'` | Same as above | Update server.py |

### Debugging

Check error logs:
```bash
cd backend
python3 analyze_errors.py --recent 10
```

Error logs include `request_data` showing exact format received.

---

## Version History

| Date | Change |
|------|--------|
| 2025-12-30 | Added format normalization to handle object arrays |
| 2025-11-02 | Initial implementation (string format only) |

---

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Project overview
- [Error Logging System](ERROR_LOGGING_SYSTEM.md) - Debugging errors
- [Michaels Cuebid Fix](../bug-fixes/2025-11/MICHAELS_CUEBID_FIX_2025-11-02.md) - Related bug fix
