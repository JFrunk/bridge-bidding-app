# Physics-Based Feedback System (V3)

**Last Updated:** 2026-01-06

## Overview

The V3 Physics-Based Feedback system provides human-understandable explanations for bridge decisions by mapping technical analysis to fundamental "physics principles" of the game.

## Architecture

The system uses a four-tier verification architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 4: UI Rendering                                       │
│  ├── HeuristicScorecard (Play feedback)                     │
│  └── BiddingGovernorPanel (Bidding feedback)                │
├─────────────────────────────────────────────────────────────┤
│  Tier 3: Shadow Partner                                     │
│  └── SignalIntegrityAuditor (Deduction confidence)          │
├─────────────────────────────────────────────────────────────┤
│  Tier 2: Logic Adapter                                      │
│  └── HeuristicBackfillAdapter (Physics violation analysis)  │
├─────────────────────────────────────────────────────────────┤
│  Tier 1: Math Engine                                        │
│  ├── DDS (Double Dummy Solver)                              │
│  └── PlayFeedbackGenerator                                  │
└─────────────────────────────────────────────────────────────┘
```

## Physics Principles

### Play Principles

| Principle | Icon | Description | Example Violations |
|-----------|------|-------------|-------------------|
| **Conservation** | 💎 | Preserve high cards for future tricks | Ace-on-king, wasted winner |
| **Fluidity** | 🌊 | Keep suits unblocked for runs | Blocked suit, stranded winners |
| **Signaling** | 📡 | Honest card choices for partner trust | Wrong card from sequence |
| **Resources** | ⚡ | Maintain trick potential | Unnecessary losers |

### Bidding Principles

| Principle | Icon | Description | Example Violations |
|-----------|------|-------------|-------------------|
| **Resources** | 💰 | HCP and point requirements | Insufficient points for level |
| **Shape** | 📐 | Distribution requirements | Wrong shape for bid |
| **Safety** | 🛡️ | Slam safety, control requirements | Missing controls for slam |
| **Communication** | 📡 | Partner signaling conventions | Blackwood violations |

## Components

### 1. HeuristicBackfillAdapter

**File:** `backend/engine/feedback/heuristic_backfill_adapter.py`

Enriches PlayFeedback with physics violation analysis.

```python
@dataclass
class PhysicsViolation:
    principle: str              # "conservation" | "fluidity" | "signaling" | "resources"
    violation_type: str         # e.g., "ace_on_king"
    explanation: str            # Human-readable
    corrective_action: str      # What should have been played
    severity: str = "minor"     # "minor" | "moderate" | "major"
```

**Violation Types:**
- `ace_on_king` - Playing ace when king would win
- `wasted_winner` - Winning trick already won by partner
- `blocked_suit` - Blocking own suit run
- `stranded_winners` - Creating unreachable winners
- `lowest_of_equals` - Not playing lowest from equal cards
- `top_of_sequence` - Not playing top of touching honors

### 2. SignalIntegrityAuditor

**File:** `backend/engine/feedback/signal_integrity_auditor.py`

Generates deduction confidence scores based on signaling consistency.

```python
class DeductionConfidence(Enum):
    EXPERT = "expert"           # 90-100% signal accuracy
    COMPETENT = "competent"     # 70-89% signal accuracy
    INCONSISTENT = "inconsistent"  # 50-69% signal accuracy
    CHAOTIC = "chaotic"         # <50% signal accuracy

@dataclass
class SignalIntegrityReport:
    signal_integrity_score: float
    deduction_confidence: str
    total_signals: int
    optimal_signals: int
    violation_breakdown: Dict[str, int]
    recommendations: List[str]
```

### 3. BiddingGovernorPanel

**File:** `frontend/src/components/learning/BiddingGovernorPanel.js`

React component displaying bidding feedback using physics principles.

```jsx
<BiddingGovernorPanel
  biddingDecisions={decisions}
  showSummary={true}
/>
```

**Sub-components:**
- `PrincipleBadge` - Shows principle with icon and color
- `GovernorExplanation` - Physics-based explanation
- `BidComparison` - User bid vs optimal comparison
- `BiddingDecisionCard` - Complete decision display
- `BiddingSummaryHeader` - Session statistics

### 4. HeuristicScorecard

**File:** `frontend/src/components/learning/HeuristicScorecard.js`

React component displaying play feedback using physics principles.

```jsx
<HeuristicScorecard decision={playDecision} />
```

## Integration Points

### PlayFeedback Enhancement

The `PlayFeedback` dataclass now includes:

```python
@dataclass
class PlayFeedback:
    # ... existing fields ...
    physics_violation: Optional[Dict] = None  # Physics principle violation data
```

### Analytics API

The analytics API returns signal integrity reports:

```python
def get_hand_play_quality_summary(user_id, hand_id):
    # ... existing logic ...

    # Generate signal integrity report
    auditor = SignalIntegrityAuditor()
    signal_report = auditor.generate_report(play_feedback_list)

    return {
        # ... existing fields ...
        'signal_integrity': signal_report.to_dict()
    }
```

## Usage

### Backend

```python
from engine.feedback.heuristic_backfill_adapter import get_heuristic_backfill_adapter
from engine.feedback.signal_integrity_auditor import SignalIntegrityAuditor

# Enrich play feedback with physics analysis
adapter = get_heuristic_backfill_adapter()
enriched_feedback = adapter.enrich(feedback, play_state, user_card, optimal_cards, position)

# Generate signal integrity report
auditor = SignalIntegrityAuditor()
report = auditor.generate_report(play_feedback_list)
```

### Frontend

```jsx
import HeuristicScorecard from './components/learning/HeuristicScorecard';
import BiddingGovernorPanel from './components/learning/BiddingGovernorPanel';

// In HandReviewModal for play feedback
<HeuristicScorecard decision={currentDecision} />

// For bidding feedback summary
<BiddingGovernorPanel
  biddingDecisions={decisions}
  showSummary={true}
/>
```

## Testing

### Unit Tests

```bash
# Run signal integrity auditor tests
cd backend
pytest tests/unit/test_signal_integrity_auditor.py -v
```

### Test Coverage

- Signal integrity scoring thresholds
- Violation breakdown accuracy
- Recommendation generation
- Edge cases (empty data, single play)
- Confidence level boundaries

## Configuration

No configuration required. The system automatically:
- Detects physics violations during play feedback generation
- Generates signal integrity reports when requested
- Falls back gracefully if analysis fails

## Performance

- Physics violation analysis: < 1ms per play
- Signal integrity report: < 10ms for 52 plays
- No additional database queries required
