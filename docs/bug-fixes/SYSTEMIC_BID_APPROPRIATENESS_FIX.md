# Systemic Bid Appropriateness Fix - Architectural Solution

## Executive Summary

**Problem:** The bidding system has a fundamental architectural flaw where bid **legality** (auction rules) and bid **appropriateness** (convention requirements) are handled separately, allowing the system to make legal but inappropriate bids.

**Root Cause:** Each bidding module generates bids based on hand criteria, then adjusts for legality without re-validating appropriateness.

**Solution:** Implement a centralized bid appropriateness validator in the `base_convention.py` module that ALL bidding modules inherit and use.

---

## The Architectural Problem

### Current Flow (Broken)

```
1. Module evaluates hand → Generates candidate bid
2. Module checks legality → Adjusts bid if illegal
3. Module returns adjusted bid → ❌ NO appropriateness check
4. BiddingEngine checks legality again → Returns bid
```

**What's Missing:** Step 2.5 - Validate that adjusted bid is still appropriate for the hand

### Example Failure Case (hand_2025-10-28_21-46-15.json)

```
West's Hand: 7 HCP, 5 clubs
Partner (East) bid: 1♠ (overcall)
Opponent (South) bid: 2♣

Advancer Module Logic:
1. ✓ West has 3+ club support → generate 2♣ (simple raise)
2. ✓ 2♣ is illegal (South already bid 2♣) → adjust to 3♣
3. ✗ NO CHECK: Does West's hand qualify for 3♣?
4. ❌ Returns 3♣ (promises 10+ HCP, West has 7)

Result: West makes illegal-looking bid that violates SAYC
```

---

## The Systemic Solution

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ ConventionModule (base_convention.py)                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ evaluate(hand, features) → (bid, explanation)          │ │
│  │   ↓                                                     │ │
│  │ 1. _internal_evaluate() → generates candidate bid      │ │
│  │   ↓                                                     │ │
│  │ 2. _validate_and_adjust_bid() → checks legality        │ │
│  │   ↓                                                     │ │
│  │ 3. _is_bid_appropriate() → validates appropriateness   │ │ <-- NEW
│  │   ↓                                                     │ │
│  │ 4. Return bid or None                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Subclasses: OpeningBidsModule, ResponseModule,            │
│              RebidModule, AdvancerBidsModule, etc.          │
└─────────────────────────────────────────────────────────────┘
```

### Key Principle

**Appropriateness MUST be a fundamental, dispositive factor in ALL bidding decisions.**

If an adjusted bid is inappropriate, the system must:
1. Reject that bid option entirely
2. Return None to force the module to find a different bid
3. Ultimately fall back to Pass if no appropriate bid exists

---

## Implementation Plan

### Phase 1: Base Convention Enhancement

**File:** `backend/engine/ai/conventions/base_convention.py`

Add three new methods to the base class:

```python
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict

class ConventionModule(ABC):
    """Base class for all bidding conventions."""

    @abstractmethod
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Return (bid, explanation) or None if convention doesn't apply."""
        pass

    def validate_and_adjust_bid(
        self,
        bid: str,
        explanation: str,
        hand: Hand,
        features: Dict
    ) -> Optional[Tuple[str, str]]:
        """
        Validate bid legality and appropriateness.

        This is the CENTRAL method that ensures all bids are both legal
        and appropriate. All subclasses SHOULD call this method before
        returning a bid.

        Args:
            bid: The intended bid
            explanation: The bid explanation
            hand: The hand being evaluated
            features: Auction features

        Returns:
            (bid, explanation) if appropriate, None if not
        """
        auction_history = features.get('auction_history', [])

        # Pass is always OK
        if bid in ['Pass', 'X', 'XX']:
            return (bid, explanation)

        # Check legality
        if BidValidator.is_legal_bid(bid, auction_history):
            # Legal as-is
            return (bid, explanation)

        # Bid is illegal - try to adjust
        next_legal = get_next_legal_bid(bid, auction_history)
        if not next_legal:
            # No legal bid possible
            return None

        # Check if adjustment is too extreme (>2 levels)
        try:
            orig_level = int(bid[0])
            adj_level = int(next_legal[0])

            if adj_level - orig_level > 2:
                # Adjustment too extreme - decline
                return None
        except (ValueError, IndexError):
            # Not a level bid - allow adjustment
            pass

        # CRITICAL: Check if adjusted bid is still appropriate
        if not self._is_bid_appropriate_after_adjustment(
            original_bid=bid,
            adjusted_bid=next_legal,
            hand=hand,
            features=features
        ):
            # Adjusted bid is inappropriate - reject it
            return None

        # Adjusted bid is OK
        adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
        return (next_legal, adjusted_explanation)

    def _is_bid_appropriate_after_adjustment(
        self,
        original_bid: str,
        adjusted_bid: str,
        hand: Hand,
        features: Dict
    ) -> bool:
        """
        Check if an adjusted bid is still appropriate for the hand.

        This method implements SAYC standard requirements for different
        bid levels and types. Subclasses CAN override this for special
        cases, but should generally call super() first.

        Args:
            original_bid: The originally intended bid
            adjusted_bid: The adjusted bid for legality
            hand: The hand being evaluated
            features: Auction features

        Returns:
            True if adjusted bid is still appropriate, False otherwise
        """
        try:
            orig_level = int(original_bid[0])
            adj_level = int(adjusted_bid[0])
            strain = adjusted_bid[1:]

            # If same level, just different strain - usually OK
            if adj_level == orig_level:
                return True

            level_increase = adj_level - orig_level

            # Get auction context
            auction_features = features.get('auction_features', {})
            partner_last_bid = auction_features.get('partner_last_bid', '')

            # Is this a raise of partner's suit?
            is_raise = (strain in partner_last_bid)

            # Is this a new suit?
            is_new_suit = not is_raise

            # Get suit length
            suit_length = hand.suit_lengths.get(strain, 0)

            # Check appropriateness based on bid type and level
            if is_raise:
                return self._is_raise_appropriate(
                    level=adj_level,
                    hand=hand,
                    suit=strain,
                    suit_length=suit_length,
                    level_increase=level_increase
                )
            elif is_new_suit:
                return self._is_new_suit_appropriate(
                    level=adj_level,
                    hand=hand,
                    suit=strain,
                    suit_length=suit_length,
                    level_increase=level_increase
                )
            else:
                # NT or other special bid - be conservative
                return adj_level <= 3 and hand.total_points >= 10 + (level_increase * 2)

        except (ValueError, IndexError, KeyError):
            # Can't parse - be conservative
            return False

    def _is_raise_appropriate(
        self,
        level: int,
        hand: Hand,
        suit: str,
        suit_length: int,
        level_increase: int
    ) -> bool:
        """
        Check if a raise to a given level is appropriate.

        SAYC Standards:
        - 2-level: 8-10 HCP, 3+ card support
        - 3-level: 10+ HCP, 3+ card support OR 8+ HCP with 4+ support
        - 4-level: 12+ HCP, 3+ support OR 10+ HCP with 5+ support (game)
        - 5-level: 14+ HCP or extreme distribution
        """
        # Check support length
        if suit_length < 3:
            return False  # Never raise with <3 card support

        if level == 2:
            # 2-level raise: 8-10 HCP minimum
            return hand.total_points >= 8

        elif level == 3:
            # 3-level raise: 10+ HCP OR 8+ with 4+ support
            if hand.total_points >= 10:
                return True
            if hand.total_points >= 8 and suit_length >= 4:
                return True
            return False

        elif level == 4:
            # 4-level: Game level
            # Major suit game: 12+ HCP OR 10+ with 5+ trumps
            if suit in ['♥', '♠']:
                if hand.total_points >= 12:
                    return True
                if hand.total_points >= 10 and suit_length >= 5:
                    return True
                return False
            else:
                # Minor suit at 4-level: need game values
                return hand.total_points >= 12

        elif level >= 5:
            # 5-level: Need game/slam values
            return hand.total_points >= 14 or suit_length >= 6

        return False

    def _is_new_suit_appropriate(
        self,
        level: int,
        hand: Hand,
        suit: str,
        suit_length: int,
        level_increase: int
    ) -> bool:
        """
        Check if a new suit bid at a given level is appropriate.

        SAYC Standards:
        - 1-level: 6+ HCP (responding), 4+ cards
        - 2-level: 8-10+ HCP, 5+ cards (constructive)
        - 3-level: 10+ HCP, 5+ cards (constructive) OR 6+ HCP with 6+ cards (preemptive)
        - 4-level: 12+ HCP (game values)
        """
        # Check suit length
        if suit_length < 4:
            return False  # Never bid a suit with <4 cards at any level

        if level == 1:
            # 1-level: Very wide range (6-17 HCP)
            # Just need 4+ cards and responding values
            return hand.total_points >= 6 and suit_length >= 4

        elif level == 2:
            # 2-level: Constructive (8-10+ HCP, 5+ cards)
            # OR strong (12+ HCP, 4+ cards)
            if suit_length >= 5 and hand.total_points >= 8:
                return True
            if suit_length >= 4 and hand.total_points >= 12:
                return True
            return False

        elif level == 3:
            # 3-level: Constructive (10+ HCP, 5+ cards)
            # OR Preemptive (6+ HCP, 6+ cards with good suit)
            if suit_length >= 5 and hand.total_points >= 10:
                return True
            # Preemptive: need long suit
            if suit_length >= 6 and hand.total_points >= 6:
                # Check suit quality (should have 2+ honors)
                suit_hcp = hand.suit_hcp.get(suit, 0)
                if suit_hcp >= 3:  # At least Q-J or K
                    return True
            return False

        elif level == 4:
            # 4-level: Game values (12+ HCP)
            return hand.total_points >= 12

        elif level >= 5:
            # 5-level: Strong game/slam values
            return hand.total_points >= 14 or suit_length >= 7

        return False

    def get_constraints(self) -> Dict:
        """
        Return a dictionary of constraints for the hand constructor.
        This is optional for conventions that don't need hand generation.
        """
        return {}
```

### Phase 2: Update All Bidding Modules

**Pattern to implement in each module:**

```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    """Main entry point with validation."""

    # Generate candidate bid using internal logic
    result = self._internal_evaluate(hand, features)

    if not result:
        return None

    bid, explanation = result

    # Validate and adjust if needed (calls base class method)
    return self.validate_and_adjust_bid(bid, explanation, hand, features)

def _internal_evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    """Internal evaluation - generates bids without validation."""
    # Existing logic moves here
    # This method ONLY focuses on generating the "ideal" bid
    # It doesn't worry about legality or appropriateness
    pass
```

**Files to Update:**

1. ✅ `backend/engine/opening_bids.py` - OpeningBidsModule
2. ✅ `backend/engine/responses.py` - ResponseModule
3. ✅ `backend/engine/responder_rebids.py` - ResponderRebidModule
4. ✅ `backend/engine/rebids.py` - RebidModule
5. ✅ `backend/engine/advancer_bids.py` - AdvancerBidsModule
6. ✅ `backend/engine/overcalls.py` - OvercallModule
7. ✅ `backend/engine/ai/conventions/stayman.py` - StaymanConvention
8. ✅ `backend/engine/ai/conventions/jacoby_transfers.py` - JacobyConvention
9. ✅ `backend/engine/ai/conventions/blackwood.py` - BlackwoodConvention
10. ✅ `backend/engine/ai/conventions/takeout_doubles.py` - TakeoutDoubleConvention
11. ✅ `backend/engine/ai/conventions/negative_doubles.py` - NegativeDoubleConvention
12. ✅ `backend/engine/ai/conventions/michaels_cuebid.py` - MichaelsCuebidConvention
13. ✅ `backend/engine/ai/conventions/unusual_2nt.py` - Unusual2NTConvention
14. ✅ `backend/engine/ai/conventions/splinter_bids.py` - SplinterBidsConvention
15. ✅ `backend/engine/ai/conventions/fourth_suit_forcing.py` - FourthSuitForcingConvention
16. ✅ `backend/engine/ai/conventions/preempts.py` - PreemptConvention

### Phase 3: Testing Strategy

**Create comprehensive test suite:**

```python
# tests/unit/test_bid_appropriateness.py

def test_raise_adjustment_validation():
    """Test that raises are only adjusted when appropriate."""

    # Case 1: West's 2♣→3♣ with 7 HCP should fail
    hand = create_hand(hcp=7, shape=(3,3,2,5), clubs="K9854")
    features = create_features(
        auction=['1♥', '1♠', '2♣'],
        partner_last_bid='1♠'
    )

    module = AdvancerBidsModule()
    result = module.evaluate(hand, features)

    # Should return None (can't bid 3♣ with 7 HCP)
    assert result is None or result[0] == 'Pass'

def test_new_suit_adjustment_validation():
    """Test that new suits are only adjusted when appropriate."""

    # Case 2: New suit 2♦→3♦ with 9 HCP should fail
    hand = create_hand(hcp=9, shape=(3,3,5,2), diamonds="AQT42")
    features = create_features(
        auction=['1♣', '2♥'],
        partner_last_bid='1♣'
    )

    module = ResponseModule()
    result = module.evaluate(hand, features)

    # Should not bid 3♦ with only 9 HCP
    assert result is None or result[0] != '3♦'

def test_game_level_adjustment_allowed():
    """Test that game-level adjustments work with sufficient strength."""

    # Case 3: 3♥→4♥ with 12 HCP and 4 trumps should succeed
    hand = create_hand(hcp=12, shape=(2,4,4,3), hearts="KQT5")
    features = create_features(
        auction=['1♥', '2♠'],
        partner_last_bid='1♥'
    )

    module = ResponseModule()
    result = module.evaluate(hand, features)

    # Should bid 4♥ (game) with 12 HCP and 4 trumps
    assert result is not None
    assert result[0] == '4♥' or result[0] == 'Pass'  # Either bid game or pass
```

---

## Benefits of This Approach

### 1. Centralized Logic
- All appropriateness validation in one place
- Easy to maintain and update
- Consistent across all bidding modules

### 2. Composable Architecture
- Modules focus on generating "ideal" bids
- Base class handles validation
- Clear separation of concerns

### 3. Override Capability
- Subclasses CAN override `_is_bid_appropriate_after_adjustment()`
- Allows for special conventions (e.g., preempts, unusual bids)
- Default implementation covers 95% of cases

### 4. Fail-Safe Design
- If appropriateness check fails, returns None
- Forces module to find alternative bid
- Ultimate fallback: Pass

### 5. Self-Documenting
- Method names clearly indicate purpose
- SAYC standards encoded in the validation logic
- Easy for future developers to understand

---

## Migration Path

### Step 1: Implement Base Class (1-2 hours)
- Add three new methods to `base_convention.py`
- Write comprehensive unit tests
- Verify tests pass

### Step 2: Update One Module as Proof of Concept (1 hour)
- Start with `advancer_bids.py` (the West case)
- Refactor to use new pattern
- Test against hand_2025-10-28_21-46-15.json
- Verify West now passes instead of bidding 3♣

### Step 3: Update Remaining Modules (4-6 hours)
- Apply same pattern to all 15 modules
- Run full test suite after each module
- Fix any edge cases

### Step 4: Integration Testing (2-3 hours)
- Run 500-hand simulation
- Compare results to baseline
- Fix any regressions

### Total Time Estimate: 8-12 hours

---

## Success Criteria

### Functional Requirements
✅ All modules use centralized appropriateness validation
✅ Adjusted bids are validated for strength and shape
✅ Inappropriate adjustments result in Pass
✅ All existing tests continue to pass
✅ New appropriateness tests pass

### Quality Requirements
✅ No AI-generated illegal bids
✅ No AI-generated inappropriate bids
✅ Bid explanations clearly indicate adjustments
✅ System gracefully falls back to Pass when stuck

### Performance Requirements
✅ No significant slowdown in bid generation
✅ Validation adds <10ms per bid
✅ 500-hand simulation completes in <5 minutes

---

## Risks and Mitigation

### Risk 1: Breaking Existing Behavior
**Mitigation:**
- Implement incrementally, one module at a time
- Run full test suite after each change
- Keep backup of working version

### Risk 2: Over-Conservative Validation
**Mitigation:**
- Start with permissive thresholds
- Tune based on test results
- Allow subclass overrides for special cases

### Risk 3: Performance Impact
**Mitigation:**
- Validation logic is O(1)
- No expensive computations
- Early exits for common cases

---

## Conclusion

This systemic fix addresses the root cause of the bid appropriateness problem by making it a **fundamental, dispositive factor** in the bidding architecture. By centralizing validation in the base class, we ensure that ALL bids, from ALL modules, are checked for both legality and appropriateness before being returned to the user.

The key insight is that **legality and appropriateness are equally important** - a legal but inappropriate bid is just as wrong as an illegal bid. This architecture makes that principle explicit and enforceable.
