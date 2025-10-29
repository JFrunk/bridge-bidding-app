# Bid Adjustment Validation Issue - Analysis

## Executive Summary

**Problem:** The auto-raise mechanism validates bid **legality** (auction rules) but not bid **appropriateness** (convention requirements). When a bid is adjusted upward for legality, the system doesn't check whether the adjusted bid still makes sense for the hand strength and shape.

**Hand Analyzed:** `hand_2025-10-28_21-46-15.json`

## The Hands

```
North (12 HCP, 14 total): ♠ 9 7 3       ♥ A Q T 5 4 3    ♦ A Q 8 5    ♣ -
South (11 HCP, 13 total): ♠ A 8         ♥ 8 7            ♦ 6 4 2      ♣ A Q J T 7 6
East  (10 HCP, 11 total): ♠ K Q J T 5   ♥ J 6            ♦ K T 9 3    ♣ 3 2
West  ( 7 HCP,  8 total): ♠ 6 4 2       ♥ K 9 2          ♦ J 7        ♣ K 9 8 5 4
```

## The Auction (with problems identified)

| # | Player | Bid | Comment |
|---|--------|-----|---------|
| 1 | North  | 1♥  | Correct: 14 points, 6 hearts |
| 2 | East   | 1♠  | Correct: 10 HCP, 5 spades |
| 3 | South  | 2♣  | User bid (forcing, 6-card suit) |
| 4 | West   | **3♣** | ❌ **ERROR #1**: Intended 2♣, auto-raised to 3♣ |
| 5 | North  | Pass | Opener has no clear action |
| 6 | East   | Pass | Partner already described hand |
| 7 | South  | X | User bid (penalty double) |
| 8 | West   | Pass | |
| 9 | North  | **3♠** | ❌ **ERROR #2**: Intended 1♠, auto-raised to 3♠ |
| 10| East   | Pass | |

## Error #1: West's 3♣ Bid

### What Happened
```
West intended: 2♣ (simple raise of partner's overcall)
System adjusted: 3♣ (illegal to bid 2♣ after South's 2♣)
```

### The Problem
**Legality:** ✅ 3♣ is legal (higher than South's 2♣)
**Appropriateness:** ❌ 3♣ is inappropriate for West's hand

**West's hand:**
- 7 HCP (counted as 8 total with distribution)
- 5 clubs (K-9-8-5-4)

**What 3♣ promises in SAYC:**
- **Constructive new suit at 3-level:** 10+ HCP with 5+ card suit
- **OR Preemptive jump:** Weak hand with very long suit (6+ cards)

**Why West's 3♣ is wrong:**
- West has only 7 HCP (too weak for constructive 3♣)
- West has only 5 clubs (too short for preemptive 3♣)
- West wanted simple raise (8-10 points) but was forced higher

**Correct action:** West should **PASS**
- Hand is too weak to compete at 3-level
- No game prospects
- Let South play in 2♣

### Code Location
[advancer_bids.py:161-164](backend/engine/advancer_bids.py#L161-L164)

```python
# 3. Simple raise with 8-10 points and 3+ support
if support >= 3 and 8 <= support_points <= 10:
    simple_raise_level = overcall_level + 1
    return (f"{simple_raise_level}{overcall_suit}", ...)
```

**Issue:** This code generates `2♣` (overcall_level=1, so simple_raise=2), which gets auto-adjusted to `3♣` without checking if 3♣ is still appropriate.

## Error #2: North's 3♠ Bid

### What Happened
```
North intended: 1♠ (supporting partner's "negative double")
System adjusted: 3♠ (illegal to bid 1♠ after East's 1♠)
```

### The Problems (Multiple!)

**Problem 2a: Misidentified Double Type**

North thinks South made a "negative double" but:
- Negative doubles happen **immediately after opponent's overcall**
- South already bid 2♣ (new suit, forcing)
- After auction: 1♥ - 1♠ - 2♣ - 3♣ - P - P - **X**
- This is a **penalty double**, not negative!
- South has 6 clubs and is doubling 3♣ for penalty

**Problem 2b: Wrong Suit (Even If Double Were Negative)**

North has:
- ♠ 9 7 3 (only 3 spades!)
- ♥ A Q T 5 4 3 (6 hearts, opening suit)

Even if South's X were negative (showing spades):
- Need 4+ spades to support negative double
- North has only 3 spades
- Should bid 3♥ (rebid 6-card suit with extras)

**Problem 2c: Illegal Adjustment Makes It Worse**

North wants: 1♠ (already questionable)
System adjusts: 3♠ (disastrous)

What 3♠ promises:
- 4+ spades
- Competitive values (9-11 HCP)
- Willingness to play in 3♠

North has:
- Only 3 spades (inadequate)
- No fit with South's actual hand
- Should support hearts or pass

**Correct action:** North should bid **3♥** or **Pass**
- 3♥ shows 6+ hearts with extras (perfect description)
- Pass lets partner collect penalty from 3♣X

### Code Location
This appears to be in the rebids or responses module where North is interpreting South's double.

## Root Cause Analysis

### The Auto-Raise Process

Current logic ([advancer_bids.py:38-55](backend/engine/advancer_bids.py#L38-L55)):

```python
# Bid is illegal - try to find next legal bid of same strain
next_legal = get_next_legal_bid(bid, auction_history)
if next_legal:
    # SANITY CHECK: If adjustment is more than 2 levels, something is wrong
    try:
        original_level = int(bid[0])
        adjusted_level = int(next_legal[0])

        if adjusted_level - original_level > 2:
            # Pass instead of making unreasonable bid
            return ("Pass", ...)
    except (ValueError, IndexError):
        pass

    adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
    return (next_legal, adjusted_explanation)
```

### What's Missing

The sanity check only prevents adjustments **more than 2 levels**. It doesn't check:

1. **Strength requirements** - Does the hand meet the HCP requirements for the adjusted level?
2. **Shape requirements** - Does the hand meet the suit length requirements for the adjusted bid?
3. **Convention semantics** - Does the adjusted bid mean something different from the intended bid?

### Example Failure Modes

| Intended Bid | Hand Requirements | Adjusted Bid | New Requirements | Hand Qualifies? |
|--------------|-------------------|--------------|------------------|-----------------|
| 2♣ (simple raise) | 8-10 HCP, 3+ clubs | 3♣ (constructive) | 10+ HCP, 5+ clubs | ❌ No (7 HCP) |
| 1♠ (support) | 4+ spades | 3♠ (competitive) | 4+ spades, 9-11 HCP | ❌ No (3 spades) |
| 2NT (invitational) | 11-12 HCP, stopper | 3NT (game) | 13+ HCP | ❌ Maybe |
| 3♥ (invitational) | 10-11 HCP, 6+ hearts | 4♥ (game) | 13+ HCP or extreme shape | ❌ Maybe |

## Proposed Solution

### Option 1: Validate Adjusted Bid (Recommended)

After adjusting a bid for legality, re-validate against convention requirements:

```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    """Main entry point for advancer actions with bid validation."""
    auction_history = features['auction_history']

    # Get the raw advancer suggestion
    result = self._evaluate_advance(hand, features)

    if not result:
        return None

    bid, explanation = result

    # Always pass Pass bids through
    if bid == "Pass":
        return result

    # Validate the bid is legal
    if BidValidator.is_legal_bid(bid, auction_history):
        return result

    # Bid is illegal - try to find next legal bid of same strain
    next_legal = get_next_legal_bid(bid, auction_history)
    if next_legal:
        # SANITY CHECK: If adjustment is more than 2 levels, pass
        try:
            original_level = int(bid[0])
            adjusted_level = int(next_legal[0])

            if adjusted_level - original_level > 2:
                return ("Pass", f"Cannot make reasonable bid at current auction level.")

            # NEW: Validate the adjusted bid is still appropriate
            if not self._is_adjusted_bid_appropriate(hand, bid, next_legal, features):
                return ("Pass", f"Hand not suitable for {next_legal} (wanted {bid} but illegal).")

        except (ValueError, IndexError):
            pass

        adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
        return (next_legal, adjusted_explanation)

    # No legal bid possible - pass
    return None

def _is_adjusted_bid_appropriate(self, hand: Hand, original_bid: str,
                                 adjusted_bid: str, features: Dict) -> bool:
    """
    Check if an adjusted bid is still appropriate for the hand.

    Args:
        hand: The hand being evaluated
        original_bid: The originally intended bid
        adjusted_bid: The adjusted bid for legality
        features: Auction features

    Returns:
        True if adjusted bid is still appropriate, False otherwise
    """
    try:
        orig_level = int(original_bid[0])
        adj_level = int(adjusted_bid[0])
        strain = adjusted_bid[1:]

        # If bid was raised by 1+ levels, check strength requirements
        level_increase = adj_level - orig_level

        if level_increase == 0:
            return True  # Same level, just different strain - usually OK

        if level_increase == 1:
            # Raised one level - need extra values
            # For raises: need +2-3 HCP per level
            # For new suits: need minimum constructive values

            partner_overcall = features['auction_features'].get('partner_last_bid', '')
            if strain in partner_overcall:
                # This is a raise of partner's suit
                support = hand.suit_lengths.get(strain, 0)

                # Check if we have enough for the higher level
                if adj_level == 3:
                    # 3-level raise needs 10+ HCP or 4+ support with 8+
                    if hand.total_points < 10 and not (support >= 4 and hand.total_points >= 8):
                        return False
                elif adj_level == 4:
                    # 4-level needs game values (12+) or extreme distribution
                    if hand.total_points < 12 and support < 5:
                        return False
            else:
                # This is a new suit
                suit_length = hand.suit_lengths.get(strain, 0)

                if adj_level == 3:
                    # New suit at 3-level needs 10+ HCP and 5+ card suit
                    if hand.total_points < 10 or suit_length < 5:
                        return False
                elif adj_level >= 4:
                    # New suit at 4-level needs game values
                    if hand.total_points < 12:
                        return False

        elif level_increase >= 2:
            # Raised two levels - generally should pass (caught by earlier check)
            return False

        return True

    except (ValueError, IndexError):
        # Can't parse bid levels - be conservative
        return True  # Let it through if we can't validate
```

### Option 2: Prevention at Source

Modify the bidding logic to consider auction state **before** generating candidate bids:

```python
def _advance_suit_overcall(self, hand: Hand, partner_overcall: str,
                          opener_bid: str, features: Dict) -> Optional[Tuple[str, str]]:
    """
    Advance partner's suit overcall.
    """
    overcall_suit = partner_overcall[1]
    overcall_level = int(partner_overcall[0])
    support = hand.suit_lengths.get(overcall_suit, 0)
    auction_history = features['auction_history']

    # Calculate what level a simple raise would actually be at
    simple_raise_level = overcall_level + 1
    actual_raise_bid = f"{simple_raise_level}{overcall_suit}"

    # Check if simple raise would be legal
    if not BidValidator.is_legal_bid(actual_raise_bid, auction_history):
        # Find what level we'd actually need to bid at
        next_legal = get_next_legal_bid(actual_raise_bid, auction_history)
        if next_legal:
            actual_raise_level = int(next_legal[0])
        else:
            actual_raise_level = 8  # Can't raise at all
    else:
        actual_raise_level = simple_raise_level

    # Now use actual_raise_level in decision making
    # 3. Simple raise with 8-10 points and 3+ support
    if support >= 3 and 8 <= support_points <= 10:
        # Check if we can afford the actual level
        if actual_raise_level <= 2:
            # 2-level raise OK with 8-10
            return (f"{actual_raise_level}{overcall_suit}",
                   f"Simple raise showing {support_points} support points.")
        elif actual_raise_level == 3:
            # 3-level raise needs 10+ - we only have 8-10
            if support_points < 10:
                # Too weak - pass instead
                return None  # Continue to other options (likely Pass)
        else:
            # 4+ level - way too high for simple raise
            return None
```

## Recommendation

**Implement Option 1** (validation after adjustment) because:

1. ✅ **Centralized:** Fix applies to all bidding modules
2. ✅ **Safe:** Doesn't change bid generation logic
3. ✅ **Clear:** Easy to understand what's happening
4. ✅ **Extensible:** Can add more sophisticated checks later

Then **refactor to Option 2** incrementally for:
- Better AI explanations
- More sophisticated competitive bidding
- Cleaner code

## Testing Strategy

Create test cases for:

1. **Simple raises that need adjustment:**
   - 2♣ → 3♣ with 8 HCP (should Pass)
   - 2♥ → 3♥ with 9 HCP (might be OK with fit)
   - 3♦ → 4♦ with 10 HCP (should Pass unless great fit)

2. **New suits that need adjustment:**
   - 2♦ → 3♦ with 9 HCP (should Pass)
   - 2NT → 3NT with 11 HCP (should Pass)

3. **Bids that should go through:**
   - 2♣ → 3♣ with 11 HCP and 4-card support (OK)
   - 3♥ → 4♥ with 10 HCP and 5-card support (OK - game)

## Implementation Priority

**HIGH** - This causes the AI to make nonsensical bids in competitive auctions, which damages user trust and learning experience.

## Files to Modify

1. `backend/engine/advancer_bids.py` - Add `_is_adjusted_bid_appropriate()` method
2. `backend/engine/responder_rebids.py` - Same fix
3. `backend/engine/rebids.py` - Same fix
4. `backend/engine/responses.py` - Same fix
5. Any other modules using `get_next_legal_bid()`

## Related Issues

- Negative double detection needs improvement (Error #2a)
- Opener rebid logic may have similar issues
- Need better auction context tracking
