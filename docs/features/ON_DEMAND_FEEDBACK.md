# On-Demand Feedback System

**Last Updated:** 2026-01-07

## Overview

The On-Demand Feedback System provides real-time AI hints during bidding and play phases. Users can toggle feedback on/off via the "💡 AI Hints" checkbox, enabling a learning-focused experience without requiring dev mode.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User Action (Bid Selection / Card Drag)                    │
├─────────────────────────────────────────────────────────────┤
│  Hint Controller (React)                                    │
│  ├── hintModeEnabled state                                  │
│  └── Pre-evaluation before commit                           │
├─────────────────────────────────────────────────────────────┤
│  Backend Governor & Auditor                                 │
│  ├── /api/evaluate-bid (existing)                           │
│  └── /api/evaluate-play-intent (new)                        │
├─────────────────────────────────────────────────────────────┤
│  UI Overlay                                                 │
│  ├── BidFeedbackPanel (review mode)                         │
│  └── GovernorConfirmDialog (blocking mode)                  │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. AI Hints Toggle

**Location:** Bidding phase controls, next to "Show All Hands"

```jsx
<label className="show-hands-toggle hint-mode-toggle">
  <input
    type="checkbox"
    checked={hintModeEnabled}
    onChange={() => setHintModeEnabled(!hintModeEnabled)}
  />
  <span>💡 AI Hints</span>
</label>
```

**Persistence:** Stored in `localStorage` as `bridge-hint-mode`

**Default:** Enabled

### 2. Post-Move Feedback (Review Mode)

When AI Hints is enabled, the `BidFeedbackPanel` appears after each user bid:

| Correctness | Icon | Display |
|------------|------|---------|
| Optimal | ✓ | "Excellent! [bid] is perfect here." |
| Acceptable | ✓ | "[bid] is acceptable. (Optimal: [better])" |
| Suboptimal | △ | "Consider [better] would be better" |
| Error | ✗ | "Better bid: [optimal]" |

### 3. Governor Commit Blocking

For bids with `impact === 'critical'` or `impact === 'significant'`:

1. **Pre-evaluation:** Bid is evaluated BEFORE committing
2. **Dialog shown:** `GovernorConfirmDialog` presents warning
3. **User choice:**
   - "Choose Different Bid" - Cancels, returns to bidding box
   - "Proceed Anyway" - Overrides warning, commits bid

**Visual distinction:**
- Critical: Red pulsing border, destructive button
- Significant: Amber border, outline button

### 4. Shadow Play Intent API

**Endpoint:** `POST /api/evaluate-play-intent`

**Purpose:** Evaluate card selection before committing (preview mode)

**Request:**
```json
{
  "user_id": "string",
  "intended_card": {"rank": "A", "suit": "S"},
  "play_state": {...},
  "position": "S"
}
```

**Response:**
```json
{
  "is_optimal": false,
  "equivalence_set": ["A♠", "K♠"],
  "physics_violation": {
    "principle": "conservation",
    "violation_type": "ace_on_king",
    "explanation": "...",
    "severity": "major"
  },
  "partner_deduction_warning": "Partner will assume you lack the King",
  "recommendation": "Play the King instead",
  "score": 6.5
}
```

## Components

### BidFeedbackPanel

**File:** `frontend/src/components/bridge/BidFeedbackPanel.jsx`

**Props:**
- `feedback` - Feedback object from API
- `userBid` - The bid made
- `isVisible` - Show/hide
- `mode` - 'review' (default) or 'consultant'
- `onDismiss` - Callback
- `onOpenGlossary` - Opens glossary drawer

**Modes:**
- **Review mode:** Post-move feedback with solid border
- **Consultant mode:** Pre-move preview with dashed purple border

### GovernorConfirmDialog

**File:** `frontend/src/components/bridge/GovernorConfirmDialog.jsx`

**Props:**
- `isOpen` - Show/hide
- `onClose` - Cancel callback
- `onProceed` - Confirm callback
- `bid` - The blocked bid
- `impact` - 'critical' or 'significant'
- `reasoning` - Warning explanation
- `optimalBid` - Suggested alternative

## State Management

```javascript
// App.js state additions
const [hintModeEnabled, setHintModeEnabled] = useState(() => {
  const saved = localStorage.getItem('bridge-hint-mode');
  return saved !== 'false'; // Default enabled
});

const [pendingBid, setPendingBid] = useState(null);
const [pendingBidFeedback, setPendingBidFeedback] = useState(null);
const [showGovernorDialog, setShowGovernorDialog] = useState(false);
```

## Flow Diagram

### Bidding with Hints Enabled

```
User selects bid
       │
       ▼
┌──────────────────┐
│ Pre-evaluate bid │ ──► /api/evaluate-bid
└──────────────────┘
       │
       ▼
┌──────────────────┐     YES    ┌────────────────────┐
│ Critical impact? │ ──────────►│ GovernorConfirmDialog│
└──────────────────┘            └────────────────────┘
       │ NO                              │
       ▼                      ┌──────────┴──────────┐
┌──────────────────┐          │                     │
│   Commit bid     │ ◄────────│ "Proceed Anyway"    │
└──────────────────┘          │                     │
       │                      │ "Choose Different"  │
       ▼                      │         │           │
┌──────────────────┐          │         ▼           │
│ Show feedback    │          │    Cancel bid       │
│   panel          │          └─────────────────────┘
└──────────────────┘
```

## CSS Classes

| Class | Purpose |
|-------|---------|
| `.hint-mode-toggle` | Toggle styling |
| `.consultant-mode` | Pre-move preview styling |
| `.governor-block` | Critical warning border |
| `.governor-warning` | Warning box styling |
| `.consultant-tag` | "🔮 AI Consultant Preview" badge |

## Testing

### Manual Testing

1. Enable "💡 AI Hints" checkbox
2. Make various bids - verify feedback appears
3. Make a deliberately bad bid (e.g., open 1NT with 10 HCP)
4. Verify Governor dialog blocks the commit
5. Test "Proceed Anyway" and "Choose Different Bid"

### E2E Testing

```javascript
// Test hint toggle
await page.getByTestId('hint-mode-toggle').click();

// Test feedback panel
await expect(page.getByTestId('bid-feedback-panel')).toBeVisible();

// Test governor dialog
await expect(page.getByTestId('governor-confirm-dialog')).toBeVisible();
```

## Configuration

No server-side configuration required. All settings stored client-side:

| Key | Default | Description |
|-----|---------|-------------|
| `bridge-hint-mode` | `'true'` | Enable/disable hints |

## Performance

- Pre-evaluation adds ~100-200ms latency to bid commits
- Feedback reused after pre-evaluation (no double API calls)
- Shadow play intent evaluation: ~50ms
