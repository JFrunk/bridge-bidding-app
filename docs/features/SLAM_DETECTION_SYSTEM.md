# Slam Detection System

**Last Updated:** 2026-01-02

## Overview

The slam detection system ensures that partnerships with sufficient combined strength (33+ HCP) properly explore and bid slam contracts. This is implemented through two key mechanisms:

1. **Slam Exploration Safety Net** - Intercepts game bids when slam values exist
2. **Improved Blackwood Signoff** - Correctly bids slam level based on ace count

## Performance

| Metric | Baseline | Current |
|--------|----------|---------|
| Game/Slam Detection | 24.7% | 90.5% |
| Composite Score | 89.7% | 94.2% |

## Slam Exploration Safety Net

### Location
`backend/engine/bidding_engine.py` - `_slam_exploration_safety_net()` method

### Purpose
Intercepts game-level bids (3NT, 4♥, 4♠) when the partnership's combined HCP suggests slam potential, redirecting to Blackwood 4NT to explore for slam.

### Conditions for Activation
All of the following must be true:
1. **Combined HCP >= 33** - Estimated from AuctionContext tracking
2. **Hand has 16+ HCP** - Current bidder has significant strength
3. **Partner showed 10+ HCP** - Partner's bidding indicates game-forcing values
4. **Blackwood not already used** - No 4NT in auction history
5. **4NT is legal** - Must be a valid bid in current auction

### How It Works

```python
def _slam_exploration_safety_net(self, hand, features, auction_history, proposed_game_bid):
    # 1. Get AuctionContext for HCP tracking
    context = AuctionContext.from_auction(auction_history, features)

    # 2. Calculate combined HCP estimate
    my_hcp = hand.hcp
    partner_min = context.ranges.opener_hcp[0] or context.ranges.responder_hcp[0]
    combined_estimate = my_hcp + partner_min

    # 3. If slam values and Blackwood available, redirect to 4NT
    if combined_estimate >= 33 and my_hcp >= 16:
        return True, "4NT", "Checking for aces - slam potential!"
```

### Example Auctions

**Before (missed slam):**
```
North: 1♠ (opener, 15 HCP)
South: 3NT (responder, 18 HCP)
# Combined: 33 HCP - should explore slam but stopped at game
```

**After (slam explored):**
```
North: 1♠ (opener, 15 HCP)
South: 4NT (Blackwood - slam exploration safety net triggered)
North: 5♥ (2 aces)
South: 6♠ (slam with 3 aces total)
```

## Blackwood Signoff Logic

### Location
`backend/engine/ai/conventions/blackwood.py` - `_get_signoff_bid()` and `_find_trump_suit()` methods

### Purpose
After receiving the ace-showing response to Blackwood 4NT, correctly decide between:
- **5-level** (game) - When partnership is missing 2+ aces
- **6-level** (small slam) - When partnership has 3+ aces
- **7-level** (grand slam) - When partnership has all 4 aces (35+ HCP)

### Trump Suit Detection

The `_find_trump_suit()` method scans the auction history to find the agreed trump suit:

**Priority Order:**
1. Most recently bid major suit (♥ or ♠) by partnership
2. Most recently bid minor suit (♣ or ♦) by partnership
3. Notrump (if no suit agreement)

**Excluded from scan:**
- 4NT (Blackwood ask)
- 5-level responses (ace-showing)
- Opponent bids

### Signoff Decision Matrix

| My Aces | Partner's Aces | Total | Signoff Level |
|---------|----------------|-------|---------------|
| 0-1 | 0-1 | 0-2 | 5-level (game) |
| 1-2 | 1-2 | 3 | 6-level (slam) |
| 2 | 2 | 4 | 7-level (grand) |

### Metadata for Validation Bypass

Signoff bids include metadata to bypass standard validation:

```python
signoff_metadata = {
    'bypass_hcp': True,        # Don't check HCP for slam level
    'bypass_suit_length': True, # Don't check suit length
    'convention': 'blackwood_signoff'
}
```

## Integration Points

### BiddingEngine Flow

```
1. Module returns game bid (e.g., "3NT")
2. BiddingEngine checks: Is this a game bid? Not already slam?
3. If yes, call _slam_exploration_safety_net()
4. If slam potential, redirect to "4NT" (Blackwood)
5. Blackwood module handles ace responses
6. _get_signoff_bid() determines final contract
```

### AuctionContext Integration

The safety net relies on `AuctionContext` for HCP tracking:
- `context.ranges.opener_hcp` - Opener's HCP range
- `context.ranges.responder_hcp` - Responder's HCP range
- `context.combined_midpoint` - Estimated combined strength

## Testing

### Diagnostic Script
```bash
cd backend
python3 diagnose_game_slam_failures.py --hands 200
```

### Quality Score Test
```bash
python3 test_bidding_quality_score.py --hands 500
```

### Expected Results
- Game detection: 95%+
- Slam detection: 80%+
- Composite: 94%+ (Grade B)

## Known Limitations

1. **Preemptive Auctions** - Safety net cannot activate when opponents preempt, as HCP estimation becomes unreliable

2. **Strong 2♣ Sequences** - Some complex 2♣ auctions may not properly estimate partner's strength

3. **Minor Suit Slams** - System prioritizes major suits; minor suit slams may be harder to reach

## Related Files

- `backend/engine/bidding_engine.py` - Safety net implementation
- `backend/engine/ai/conventions/blackwood.py` - Blackwood and signoff logic
- `backend/engine/ai/auction_context.py` - HCP tracking
- `backend/engine/ai/sanity_checker.py` - Blackwood sequence detection
