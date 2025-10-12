# Enhanced Bid Explanation System

## Overview

The bidding engine now uses a **structured explanation system** that directly traces explanations back to the actual decision logic in the code. Instead of hardcoded strings, explanations are built programmatically as the AI evaluates each bid.

## Key Benefits

1. **Explanations match code exactly** - No risk of outdated or incorrect text
2. **Rich contextual information** - Shows actual hand values, requirements, and alternatives
3. **Educational value** - Helps users understand WHY a bid is optimal
4. **Debugging aid** - Makes AI decision logic transparent

## Architecture

### BidExplanation Class

Located in: [`backend/engine/ai/bid_explanation.py`](backend/engine/ai/bid_explanation.py)

This is the core data structure that captures:

```python
class BidExplanation:
    bid: str                    # The bid itself (e.g., "1NT")
    primary_reason: str         # Main explanation
    hand_requirements: Dict     # What the bid requires (e.g., {"HCP": "15-17"})
    actual_hand_values: Dict    # Actual hand characteristics
    alternatives_considered: List[AlternativeBid]  # Other bids rejected
    forcing_status: str         # "Forcing", "Invitational", "Sign-off"
    convention_reference: str   # SAYC rule or convention used
```

### Output Formats

The system supports two output modes:

#### 1. Simple String (Backward Compatible)
```
Balanced hand with 15-17 HCP opens 1NT (Sign-off)
```

#### 2. Detailed String (Educational)
```
📋 Balanced hand with 15-17 HCP opens 1NT

🃏 Your hand:
  • HCP: 16 (requires 15-17)
  • Distribution: 3-3-3-4

🤔 Other bids considered:
  • 1-level suit: Hand is balanced, 1NT more descriptive

⚡ Status: Sign-off (partner may pass)
```

The BiddingEngine automatically converts BidExplanation objects to detailed strings.

## How to Use

### Refactoring a Module

When updating a specialist module to use rich explanations:

1. **Import the class**:
```python
from engine.ai.bid_explanation import BidExplanation
from typing import Optional, Tuple, Dict, Union
```

2. **Update return type**:
```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, Union[str, BidExplanation]]]:
```

3. **Build explanations programmatically**:
```python
explanation = BidExplanation("1NT")
explanation.set_primary_reason("Balanced hand with 15-17 HCP opens 1NT")
explanation.add_requirement("HCP", "15-17")
explanation.add_actual_value("HCP", str(hand.hcp))
explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
explanation.set_forcing_status("Sign-off (partner may pass)")
explanation.add_alternative("1-level suit", "Hand is balanced, 1NT more descriptive")
return ("1NT", explanation)
```

### Example: Opening Bids

See [`backend/engine/opening_bids.py`](backend/engine/opening_bids.py) for a complete example.

Key pattern:
- Check conditions (same as before)
- Build BidExplanation object showing:
  - What was required
  - What the hand actually has
  - Why alternatives were rejected
  - Forcing status

### Example: Response Bids

See [`backend/engine/responses.py`](backend/engine/responses.py#L107-L151) for support raises.

Shows:
- Support points calculation (with shortness bonuses)
- Trump fit length
- Why this level vs others (too weak/strong)

## Feedback Endpoint Enhancement

The `/api/get-feedback` endpoint now provides richer comparisons:

**When user is correct:**
```
✅ Correct! Your bid of 1NT is optimal.

📋 Balanced hand with 15-17 HCP opens 1NT
[detailed explanation...]
```

**When user bid differs:**
```
⚠️ Your bid: 1♠
✅ Recommended: 1NT

Why this bid is recommended:
📋 Balanced hand with 15-17 HCP opens 1NT
[detailed explanation...]

📊 Your hand summary:
  • Total Points: 16 (16 HCP + 0 dist)
  • Shape: 3-3-3-4
  • Suits: ♠3(5), ♥3(4), ♦3(4), ♣4(3)
```

## Migration Status

### ✅ Completed Modules
- **OpeningBidsModule** - All opening bids use rich explanations
- **ResponseModule** - Support raises use rich explanations

### 📝 Legacy Modules (Still using string explanations)
- RebidModule
- AdvancerBidsModule
- OvercallModule
- Most conventions (Stayman, Jacoby, Blackwood, etc.)

These modules will continue to work with simple string explanations. The BiddingEngine handles both types seamlessly.

## Testing

Test examples in this document:

### Test 1: 1NT Opening
```bash
cd backend && python3 -c "
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

cards = [
    Card('A', '♠'), Card('K', '♠'), Card('5', '♠'),
    Card('Q', '♥'), Card('J', '♥'), Card('8', '♥'),
    Card('A', '♦'), Card('7', '♦'), Card('4', '♦'),
    Card('K', '♣'), Card('9', '♣'), Card('3', '♣'), Card('2', '♣')
]
hand = Hand(cards)
engine = BiddingEngine()
bid, explanation = engine.get_next_bid(hand, [], 'North', 'None')
print(f'Bid: {bid}\n\nExplanation:\n{explanation}')
"
```

### Test 2: Game-Forcing Raise
```bash
cd backend && python3 -c "
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

cards = [
    Card('K', '♠'), Card('8', '♠'),
    Card('Q', '♥'), Card('J', '♥'), Card('9', '♥'), Card('7', '♥'),
    Card('A', '♦'), Card('6', '♦'), Card('4', '♦'),
    Card('K', '♣'), Card('5', '♣'), Card('3', '♣'), Card('2', '♣')
]
hand = Hand(cards)
engine = BiddingEngine()
auction = ['1♥', 'Pass', 'Pass']
bid, explanation = engine.get_next_bid(hand, auction, 'South', 'None')
print(f'Bid: {bid}\n\nExplanation:\n{explanation}')
"
```

## Future Enhancements

Potential additions:
1. **JSON API** - Return structured explanation objects to frontend for interactive display
2. **Explanation levels** - Toggle between simple/detailed/expert modes
3. **Alternative analysis** - Show not just rejected bids but *why* each was rejected with scoring
4. **Rule references** - Link to specific SAYC documentation
5. **Historical explanations** - Show reasoning for all past AI bids in auction

## Implementation Tips

1. **Always show actual values** - Don't just say "balanced", show the distribution
2. **Explain comparisons** - When choosing between similar bids, show the deciding factor
3. **Include context** - Support points, shortness bonuses, etc.
4. **Use formatting** - Emojis and structure make explanations scannable
5. **Stay consistent** - Use same terminology as SAYC/bidding rules

## Backward Compatibility

- Modules can return either `str` or `BidExplanation`
- BiddingEngine handles both transparently
- Existing tests continue to work
- Frontend receives strings (for now) via the API

## Questions & Support

For questions about this system, see:
- Code: [`backend/engine/ai/bid_explanation.py`](backend/engine/ai/bid_explanation.py)
- Examples: [`backend/engine/opening_bids.py`](backend/engine/opening_bids.py)
- Feedback endpoint: [`backend/server.py`](backend/server.py#L152-L185)
