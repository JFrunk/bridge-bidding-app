# Enhanced Explanation System - Complete Guide

## Overview

The bidding engine now supports **three levels of explanation detail** and includes **SAYC rule references** with links to official documentation. Additionally, a **JSON API endpoint** allows frontends to render custom explanation UIs.

## Features

### 1. Explanation Levels

Choose between three levels of detail:

| Level | Description | Use Case |
|-------|-------------|----------|
| **Simple** | One-line summary | Quick reference, casual play |
| **Detailed** | Hand values, alternatives, forcing status | Learning and training (default) |
| **Expert** | SAYC rules, decision trace, complete analysis | Deep study, rule verification |

### 2. SAYC Rule References

Every bid that follows a SAYC convention includes:
- Rule name (e.g., "1NT Opening")
- Description of requirements
- Link to official SAYC documentation
- Rule category (Opening Bids, Responses, Conventions, etc.)

### 3. JSON API

Structured explanation data for building custom UIs:
- All explanation fields as JSON
- SAYC rule metadata included
- Hand requirements vs. actual values
- Alternatives considered with rejection reasons

## API Usage

### Endpoint 1: `/api/get-next-bid` (String Response)

**Request:**
```json
{
  "auction_history": ["1♥", "Pass", "Pass"],
  "current_player": "South",
  "explanation_level": "expert"  // optional: "simple", "detailed", or "expert"
}
```

**Response:**
```json
{
  "bid": "1NT",
  "explanation": "📋 Balanced hand with 15-17 HCP opens 1NT\n\n📖 SAYC Rule: 1NT Opening..."
}
```

### Endpoint 2: `/api/get-next-bid-structured` (JSON Response)

**Request:**
```json
{
  "auction_history": ["1♥", "Pass", "Pass"],
  "current_player": "South"
}
```

**Response:**
```json
{
  "bid": "1NT",
  "explanation": {
    "bid": "1NT",
    "primary_reason": "Balanced hand with 15-17 HCP opens 1NT",
    "hand_requirements": {
      "HCP": "15-17",
      "Shape": "Balanced (no singleton/void, at most 1 doubleton)"
    },
    "actual_hand_values": {
      "HCP": "16",
      "Distribution": "3-3-3-4"
    },
    "alternatives_considered": [
      {
        "bid": "1-level suit",
        "reason": "Hand is balanced, 1NT more descriptive"
      }
    ],
    "forcing_status": "Sign-off (partner may pass)",
    "sayc_rule_id": "1nt_opening",
    "sayc_rule": {
      "id": "1nt_opening",
      "name": "1NT Opening",
      "description": "15-17 HCP, balanced distribution...",
      "url": "https://web2.acbl.org/documentlibrary/play/sayc.pdf",
      "category": "Opening Bids"
    }
  }
}
```

### Endpoint 3: `/api/get-feedback` (Enhanced)

Now supports `explanation_level` parameter:

**Request:**
```json
{
  "auction_history": ["1♥", "Pass", "1♠"],
  "explanation_level": "expert"  // optional
}
```

## Example Outputs

### Simple Level
```
Balanced hand with 15-17 HCP opens 1NT (Sign-off (partner may pass))
```

### Detailed Level
```
📋 Balanced hand with 15-17 HCP opens 1NT

🃏 Your hand:
  • HCP: 16 (requires 15-17)
  • Distribution: 3-3-3-4

🤔 Other bids considered:
  • 1-level suit: Hand is balanced, 1NT more descriptive

⚡ Status: Sign-off (partner may pass)
```

### Expert Level
```
📋 Balanced hand with 15-17 HCP opens 1NT

📖 SAYC Rule: 1NT Opening
   15-17 HCP, balanced distribution (no singleton/void, at most one doubleton)
   📚 Reference: https://web2.acbl.org/documentlibrary/play/sayc.pdf

🃏 Hand Analysis:
  ✓ HCP: 16 (requires 15-17)
  • Distribution: 3-3-3-4

🤔 Alternatives Rejected:
  ✗ 1-level suit: Hand is balanced, 1NT more descriptive

⚡ Status: Sign-off (partner may pass)
```

## SAYC Rules Database

Located in: [`backend/engine/ai/sayc_rules.py`](backend/engine/ai/sayc_rules.py)

### Available Rules

#### Opening Bids
- `1nt_opening` - 1NT Opening (15-17 HCP)
- `2nt_opening` - 2NT Opening (20-21 HCP)
- `3nt_opening` - 3NT Opening (25-27 HCP)
- `2c_opening` - Strong 2♣ (22+ points)
- `one_level_major` - 1♥/1♠ (13+ with 5+ major)
- `one_level_minor` - 1♣/1♦ (13+ with better minor)
- `weak_two` - 2♦/2♥/2♠ (6-10 HCP, 6-card suit)

#### Responses
- `simple_raise` - Raise partner one level (6-9 support points)
- `invitational_raise` - Jump raise (10-12 support points)
- `game_forcing_raise` - Jump to game (13+ support points)
- `jump_shift` - Jump in new suit (17+ HCP)
- `new_suit_forcing` - New suit forcing (varies by level)
- `1nt_response` - 1NT response (6-10 HCP, balanced)
- `2nt_response` - 2NT response (11-12 HCP, invitational)

#### Conventions
- `stayman` - Stayman (2♣ asks for major)
- `jacoby_transfer` - Jacoby Transfers (2♦→♥, 2♥→♠)
- `blackwood` - Blackwood 4NT (asks for aces)
- `takeout_double` - Takeout Double
- `negative_double` - Negative Double

#### Hand Evaluation
- `support_points` - Support point calculation
- `distribution_points` - Long suit points

### Adding New Rules

```python
from engine.ai.sayc_rules import SAYC_RULES, SAYCRule

SAYC_RULES["my_rule"] = SAYCRule(
    id="my_rule",
    name="My Rule Name",
    description="Detailed description of the rule",
    url="https://link-to-documentation.com",
    category="Opening Bids"  # or Responses, Conventions, etc.
)
```

## Implementation Guide

### Adding SAYC References to Bids

When creating a `BidExplanation`, simply call `.set_sayc_rule()`:

```python
explanation = BidExplanation("1NT")
explanation.set_primary_reason("Balanced hand with 15-17 HCP opens 1NT")
explanation.add_requirement("HCP", "15-17")
explanation.add_actual_value("HCP", str(hand.hcp))
explanation.set_sayc_rule("1nt_opening")  # ← Add this
return ("1NT", explanation)
```

The SAYC rule will automatically appear in:
- Expert-level string explanations
- JSON responses via `/api/get-next-bid-structured`

### Using Explanation Levels in Frontend

**Option 1: Let user choose**
```javascript
const level = userPreference; // "simple", "detailed", or "expert"

fetch('/api/get-next-bid', {
  method: 'POST',
  body: JSON.stringify({
    auction_history: [...],
    current_player: 'North',
    explanation_level: level
  })
});
```

**Option 2: Render custom UI from JSON**
```javascript
// Get structured data
const response = await fetch('/api/get-next-bid-structured', {...});
const { bid, explanation } = await response.json();

// Render with custom UI
<BidCard bid={explanation.bid}>
  <Reason>{explanation.primary_reason}</Reason>

  {explanation.sayc_rule && (
    <SAYCReference
      name={explanation.sayc_rule.name}
      url={explanation.sayc_rule.url}
    />
  )}

  <HandAnalysis
    requirements={explanation.hand_requirements}
    actuals={explanation.actual_hand_values}
  />

  <Alternatives>
    {explanation.alternatives_considered.map(alt => (
      <Alternative bid={alt.bid} reason={alt.reason} />
    ))}
  </Alternatives>
</BidCard>
```

## Testing

### Command-Line Tests

**Test all levels:**
```bash
cd backend && python3 << 'EOF'
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

cards = [
    Card('A', '♠'), Card('K', '♠'), Card('5', '♠'),
    Card('Q', '♥'), Card('5', '♥'), Card('3', '♥'),
    Card('A', '♦'), Card('K', '♦'), Card('3', '♦'),
    Card('7', '♣'), Card('6', '♣'), Card('4', '♣'), Card('2', '♣')
]
hand = Hand(cards)
engine = BiddingEngine()

for level in ['simple', 'detailed', 'expert']:
    print(f'\n=== {level.upper()} ===')
    bid, expl = engine.get_next_bid(hand, [], 'North', 'None', level)
    print(expl)
EOF
```

**Test JSON API:**
```bash
cd backend && python3 << 'EOF'
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
import json

cards = [
    Card('A', '♠'), Card('K', '♠'), Card('5', '♠'),
    Card('Q', '♥'), Card('5', '♥'), Card('3', '♥'),
    Card('A', '♦'), Card('K', '♦'), Card('3', '♦'),
    Card('7', '♣'), Card('6', '♣'), Card('4', '♣'), Card('2', '♣')
]
hand = Hand(cards)
engine = BiddingEngine()

bid, explanation_dict = engine.get_next_bid_structured(hand, [], 'North', 'None')
print(json.dumps(explanation_dict, indent=2))
EOF
```

### Integration Tests

Run existing tests to ensure backward compatibility:
```bash
cd backend
source venv/bin/activate
pytest tests/test_opening_bids.py -v
pytest tests/test_responses.py -v
```

## Migration Path

### For Existing Modules

Modules that haven't been updated continue to work with string explanations:

```python
# Old style (still works)
return ("1♣", "Shows 13+ points, clubs is the longer minor")

# New style (enhanced)
explanation = BidExplanation("1♣")
explanation.set_primary_reason("...")
explanation.set_sayc_rule("one_level_minor")
return ("1♣", explanation)
```

### Current Status

**✅ Using Rich Explanations:**
- OpeningBidsModule (with SAYC rules)
- ResponseModule (partial - raises only)

**📝 Legacy String Explanations:**
- RebidModule
- AdvancerBidsModule
- OvercallModule
- Most conventions

## Frontend Integration Examples

### React Component Example

```jsx
function ExplanationDisplay({ explanation, level = "detailed" }) {
  if (level === "simple") {
    return <p>{explanation.primary_reason}</p>;
  }

  return (
    <div className="explanation">
      <h3>{explanation.primary_reason}</h3>

      {explanation.sayc_rule && (
        <div className="sayc-rule">
          <strong>{explanation.sayc_rule.name}</strong>
          <p>{explanation.sayc_rule.description}</p>
          <a href={explanation.sayc_rule.url} target="_blank">
            Learn more →
          </a>
        </div>
      )}

      <div className="hand-analysis">
        <h4>Your Hand</h4>
        {Object.entries(explanation.actual_hand_values).map(([k, v]) => (
          <div key={k}>
            {k}: {v}
            {explanation.hand_requirements[k] &&
              <span>(requires {explanation.hand_requirements[k]})</span>
            }
          </div>
        ))}
      </div>

      {explanation.alternatives_considered?.length > 0 && (
        <div className="alternatives">
          <h4>Other Bids Considered</h4>
          {explanation.alternatives_considered.map(alt => (
            <div key={alt.bid}>
              <strong>{alt.bid}:</strong> {alt.reason}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Settings UI Example

```jsx
function ExplanationSettings() {
  const [level, setLevel] = useState('detailed');

  return (
    <select value={level} onChange={e => setLevel(e.target.value)}>
      <option value="simple">Simple - Quick summary</option>
      <option value="detailed">Detailed - Learning mode (default)</option>
      <option value="expert">Expert - With SAYC rules</option>
    </select>
  );
}
```

## Performance Considerations

- **String explanations** are generated on-demand via `.format(level)`
- **JSON responses** include full data regardless of level (frontend filters)
- **SAYC rule lookups** are O(1) dictionary lookups (negligible overhead)
- **Backward compatible** - no performance impact on legacy modules

## Future Enhancements

Potential additions:
1. **Interactive rule explorer** - Browse all SAYC rules by category
2. **Explanation history** - Show reasoning for all AI bids in auction
3. **Custom rule sets** - Support 2/1, Precision, etc.
4. **Rule conflict detection** - Flag when hand doesn't perfectly match rule
5. **Learning analytics** - Track which rules user struggles with

## References

- [SAYC Official Card](https://web2.acbl.org/documentlibrary/play/sayc.pdf)
- [BidExplanation Class](backend/engine/ai/bid_explanation.py)
- [SAYC Rules Database](backend/engine/ai/sayc_rules.py)
- [BiddingEngine Implementation](backend/engine/bidding_engine.py)
- [API Endpoints](backend/server.py)
