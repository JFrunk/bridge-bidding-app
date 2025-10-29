# Implementation Plan - Bid Appropriateness Fix

## Overview

This document provides a step-by-step implementation plan for the systemic bid appropriateness fix. Each step includes code examples and verification steps.

---

## Phase 1: Base Class Implementation

### Step 1.1: Enhance `base_convention.py`

**File:** `backend/engine/ai/conventions/base_convention.py`

**Changes:**

```python
from engine.hand import Hand
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict
from engine.bidding_validation import BidValidator, get_next_legal_bid

class ConventionModule(ABC):
    """Base class for all bidding conventions."""

    @abstractmethod
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Return (bid, explanation) or None if convention doesn't apply."""
        pass

    # ========================================================================
    # NEW METHODS - Core appropriateness validation
    # ========================================================================

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

        Flow:
        1. Check if bid is Pass/X/XX (always OK)
        2. Check if bid is legal as-is → return it
        3. Try to adjust bid for legality
        4. Check if adjustment is reasonable (<= 2 levels)
        5. **KEY STEP:** Check if adjusted bid is still appropriate
        6. Return adjusted bid or None

        Args:
            bid: The intended bid
            explanation: The bid explanation
            hand: The hand being evaluated
            features: Auction features

        Returns:
            (bid, explanation) if appropriate, None if not
        """
        auction_history = features.get('auction_history', [])

        # Pass/X/XX are always OK
        if bid in ['Pass', 'X', 'XX']:
            return (bid, explanation)

        # Check if bid is legal as-is
        if BidValidator.is_legal_bid(bid, auction_history):
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
            # Not a level bid (e.g., Pass, X, XX) - allow adjustment
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

        Logic:
        1. Parse bid levels
        2. Determine if same level (different strain) → usually OK
        3. Determine if raise or new suit
        4. Apply appropriate validation rules

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
            # Example: 2♣ → 2♦ (same strength requirements)
            if adj_level == orig_level:
                return True

            level_increase = adj_level - orig_level

            # Get auction context
            auction_features = features.get('auction_features', {})
            partner_last_bid = auction_features.get('partner_last_bid', '')
            opening_bid = auction_features.get('opening_bid', '')

            # Determine bid type
            is_raise = self._is_raise_of_partner(strain, partner_last_bid, opening_bid, features)
            is_new_suit = not is_raise

            # Get suit length
            suit_length = hand.suit_lengths.get(strain, 0)

            # Apply appropriate validation
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
                # Require 10 HCP + 2 per level of increase
                return adj_level <= 3 and hand.total_points >= 10 + (level_increase * 2)

        except (ValueError, IndexError, KeyError):
            # Can't parse bid - be conservative
            return False

    def _is_raise_of_partner(
        self,
        strain: str,
        partner_last_bid: str,
        opening_bid: str,
        features: Dict
    ) -> bool:
        """
        Determine if this bid is a raise of partner's suit.

        Args:
            strain: The strain being bid (♠, ♥, ♦, ♣)
            partner_last_bid: Partner's last bid
            opening_bid: The opening bid
            features: Auction features

        Returns:
            True if this is a raise of partner's suit
        """
        # Check if strain is in partner's last bid
        if strain in partner_last_bid:
            return True

        # Check if we opened and partner is raising us
        auction_features = features.get('auction_features', {})
        opener_relationship = auction_features.get('opener_relationship', '')

        if opener_relationship == 'Self' and strain in opening_bid:
            return True

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

        SAYC Standards for Raises:
        ┌─────────┬──────────────────────────────────────────────────┐
        │ Level   │ Requirements                                     │
        ├─────────┼──────────────────────────────────────────────────┤
        │ 2-level │ 8-10 HCP, 3+ card support                       │
        │ 3-level │ 10+ HCP, 3+ support OR 8+ HCP with 4+ support   │
        │ 4-level │ 12+ HCP, 3+ support OR 10+ HCP with 5+ trumps   │
        │ 5-level │ 14+ HCP or extreme distribution (6+ trumps)     │
        └─────────┴──────────────────────────────────────────────────┘

        Args:
            level: The level being bid (2-7)
            hand: The hand being evaluated
            suit: The suit being raised
            suit_length: Number of cards in the suit
            level_increase: How many levels above original bid

        Returns:
            True if raise is appropriate, False otherwise
        """
        # Minimum support check - ALWAYS need 3+ cards
        if suit_length < 3:
            return False

        if level == 2:
            # 2-level raise: 8-10 HCP minimum, 3+ support
            return hand.total_points >= 8

        elif level == 3:
            # 3-level raise: Two scenarios
            # A) 10+ HCP, 3+ support (invitational)
            if hand.total_points >= 10:
                return True
            # B) 8+ HCP with 4+ support (competitive)
            if hand.total_points >= 8 and suit_length >= 4:
                return True
            return False

        elif level == 4:
            # 4-level: Game level
            if suit in ['♥', '♠']:
                # Major suit game: Two scenarios
                # A) 12+ HCP, 3+ support (normal game)
                if hand.total_points >= 12:
                    return True
                # B) 10+ HCP with 5+ trumps (distributional game)
                if hand.total_points >= 10 and suit_length >= 5:
                    return True
                return False
            else:
                # Minor suit at 4-level: need game values
                # This is rare (usually bid 3NT instead)
                return hand.total_points >= 12

        elif level >= 5:
            # 5-level: Need game/slam values
            # Either strong (14+ HCP) or extreme distribution (6+ trumps)
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

        SAYC Standards for New Suits:
        ┌─────────┬──────────────────────────────────────────────────┐
        │ Level   │ Requirements                                     │
        ├─────────┼──────────────────────────────────────────────────┤
        │ 1-level │ 6+ HCP, 4+ cards (responding values)            │
        │ 2-level │ 8-10+ HCP, 5+ cards (constructive)              │
        │         │ OR 12+ HCP, 4+ cards (strong)                   │
        │ 3-level │ 10+ HCP, 5+ cards (constructive)                │
        │         │ OR 6+ HCP, 6+ cards + 2 honors (preemptive)     │
        │ 4-level │ 12+ HCP (game values)                           │
        │ 5-level │ 14+ HCP or 7+ card suit (game/slam values)     │
        └─────────┴──────────────────────────────────────────────────┘

        Args:
            level: The level being bid (1-7)
            hand: The hand being evaluated
            suit: The suit being bid
            suit_length: Number of cards in the suit
            level_increase: How many levels above original bid

        Returns:
            True if new suit is appropriate, False otherwise
        """
        # Minimum length check - ALWAYS need 4+ cards for new suit
        if suit_length < 4:
            return False

        if level == 1:
            # 1-level: Very wide range (6-17 HCP)
            # Just need 4+ cards and responding values
            return hand.total_points >= 6 and suit_length >= 4

        elif level == 2:
            # 2-level: Two scenarios
            # A) Constructive (8-10+ HCP, 5+ cards)
            if suit_length >= 5 and hand.total_points >= 8:
                return True
            # B) Strong (12+ HCP, 4+ cards)
            if suit_length >= 4 and hand.total_points >= 12:
                return True
            return False

        elif level == 3:
            # 3-level: Two scenarios
            # A) Constructive (10+ HCP, 5+ cards)
            if suit_length >= 5 and hand.total_points >= 10:
                return True

            # B) Preemptive (6+ HCP, 6+ cards with good suit)
            if suit_length >= 6 and hand.total_points >= 6:
                # Check suit quality (should have 2+ honors)
                suit_hcp = hand.suit_hcp.get(suit, 0)
                if suit_hcp >= 3:  # At least Q-J (2) or K (3)
                    return True

            return False

        elif level == 4:
            # 4-level: Game values required
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

**Verification:**
```bash
# Run unit tests for base class
python3 -m pytest backend/tests/unit/test_base_convention_appropriateness.py -v
```

---

## Phase 2: Module Refactoring Pattern

### Step 2.1: Refactor Pattern (Apply to Each Module)

**Example: `backend/engine/advancer_bids.py`**

**BEFORE:**
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
        # SANITY CHECK: If adjustment is more than 2 levels, something is wrong
        try:
            original_level = int(bid[0])
            adjusted_level = int(next_legal[0])

            if adjusted_level - original_level > 2:
                return ("Pass", f"Cannot make reasonable bid at current auction level.")
        except (ValueError, IndexError):
            pass

        adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
        return (next_legal, adjusted_explanation)

    # No legal bid possible - pass
    return None
```

**AFTER:**
```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    """Main entry point for advancer actions with bid validation."""

    # Generate candidate bid using internal logic
    result = self._evaluate_advance(hand, features)

    if not result:
        return None

    bid, explanation = result

    # Use centralized validation from base class
    return self.validate_and_adjust_bid(bid, explanation, hand, features)

# Rename existing _evaluate_advance to keep logic intact
# (No changes to this method - just called by new evaluate())
def _evaluate_advance(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    """Internal method that calculates advance bid without validation."""
    # ... existing logic unchanged ...
```

**Changes Summary:**
1. Simplify `evaluate()` to call base class validation
2. Keep all existing bid generation logic in `_evaluate_advance()` (or rename existing method)
3. Remove module-specific adjustment logic (now handled by base class)

---

### Step 2.2: Module Priority Order

Refactor in this order (high-impact first):

1. ✅ **advancer_bids.py** - West's 3♣ error
2. ✅ **rebids.py** - North's 3♠ error
3. ✅ **responder_rebids.py** - Common competitive scenarios
4. ✅ **responses.py** - Core responding logic
5. ✅ **overcalls.py** - Interference bidding
6. ✅ **opening_bids.py** - Usually safe, but needs consistency
7-16. **Convention modules** - Lower priority (less likely to have issues)

---

## Phase 3: Testing Strategy

### Step 3.1: Unit Tests for Base Class

**File:** `backend/tests/unit/test_base_convention_appropriateness.py`

```python
import pytest
from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Dict, Optional, Tuple

class TestConventionModule(ConventionModule):
    """Concrete implementation for testing base class."""

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Dummy implementation."""
        return ("Pass", "Test bid")

class TestBidAppropriatenessValidation:
    """Test suite for bid appropriateness validation."""

    def test_raise_2level_appropriate(self):
        """2-level raise with 8+ HCP should be OK"""
        hand = self._create_hand(hcp=8, shape=(3,3,3,4), clubs="K954")
        features = self._create_features(
            auction=['1♠', '2♣'],
            partner_last_bid='1♠'
        )

        module = TestConventionModule()
        result = module.validate_and_adjust_bid('2♠', 'Simple raise', hand, features)

        assert result is not None
        assert result[0] == '2♠'

    def test_raise_3level_inappropriate_weak(self):
        """3-level raise with only 7 HCP should fail"""
        hand = self._create_hand(hcp=7, shape=(3,3,2,5), clubs="K9854")
        features = self._create_features(
            auction=['1♠', '2♣'],  # South bid 2♣, so 2♠ becomes 3♠
            partner_last_bid='1♠'
        )

        module = TestConventionModule()
        # Intended 2♠, but illegal, becomes 3♠
        result = module.validate_and_adjust_bid('2♠', 'Simple raise', hand, features)

        # Should reject 3♠ (7 HCP too weak for 3-level)
        assert result is None

    def test_raise_3level_appropriate_with_fit(self):
        """3-level raise with 8 HCP + 4-card support should be OK"""
        hand = self._create_hand(hcp=8, shape=(3,3,2,5), clubs="KQ954")
        features = self._create_features(
            auction=['1♣', '2♥'],
            partner_last_bid='1♣'
        )

        module = TestConventionModule()
        result = module.validate_and_adjust_bid('3♣', 'Raise with fit', hand, features)

        # 8 HCP + 5-card support = OK for 3-level
        assert result is not None
        assert result[0] == '3♣'

    def test_new_suit_3level_inappropriate(self):
        """New suit at 3-level with 9 HCP should fail"""
        hand = self._create_hand(hcp=9, shape=(3,3,5,2), diamonds="AQT42")
        features = self._create_features(
            auction=['1♣', '2♥'],
            partner_last_bid='1♣'
        )

        module = TestConventionModule()
        result = module.validate_and_adjust_bid('3♦', 'New suit', hand, features)

        # 9 HCP too weak for constructive 3♦
        assert result is None

    def test_new_suit_3level_appropriate(self):
        """New suit at 3-level with 10+ HCP should be OK"""
        hand = self._create_hand(hcp=10, shape=(3,3,5,2), diamonds="AQT42")
        features = self._create_features(
            auction=['1♣', '2♥'],
            partner_last_bid='1♣'
        )

        module = TestConventionModule()
        result = module.validate_and_adjust_bid('3♦', 'New suit', hand, features)

        # 10 HCP = OK for constructive 3♦
        assert result is not None
        assert result[0] == '3♦'

    def test_game_level_adjustment_appropriate(self):
        """3♥→4♥ with 12 HCP should be OK (game)"""
        hand = self._create_hand(hcp=12, shape=(2,4,4,3), hearts="KQT5")
        features = self._create_features(
            auction=['1♥', '3♠'],  # Preempt forces us to 4♥
            partner_last_bid='1♥'
        )

        module = TestConventionModule()
        result = module.validate_and_adjust_bid('3♥', 'Game raise', hand, features)

        # Should allow 4♥ with 12 HCP (game values)
        assert result is not None
        # Either 4♥ or adjusted to 4♥
        assert result[0] in ['3♥', '4♥']

    def test_adjustment_over_2_levels_rejected(self):
        """Adjustment >2 levels should be rejected"""
        hand = self._create_hand(hcp=8, shape=(3,3,3,4), clubs="K954")
        features = self._create_features(
            auction=['1♣', '4♠'],  # Opponent preempts to 4♠
            partner_last_bid='1♣'
        )

        module = TestConventionModule()
        # Want 2♣, but would need 5♣ (3+ level jump)
        result = module.validate_and_adjust_bid('2♣', 'Raise', hand, features)

        # Should reject (too big a jump)
        assert result is None

    # Helper methods
    def _create_hand(self, hcp: int, shape: tuple, **kwargs) -> Hand:
        """Create a hand for testing."""
        # ... implementation ...
        pass

    def _create_features(self, auction: list, partner_last_bid: str) -> Dict:
        """Create auction features for testing."""
        # ... implementation ...
        pass
```

**Run:**
```bash
python3 -m pytest backend/tests/unit/test_base_convention_appropriateness.py -v
```

---

### Step 3.2: Integration Test - Problematic Hand

**File:** `backend/tests/integration/test_hand_2025_10_28_fix.py`

```python
import json
import pytest
from engine.hand import Hand
from engine.bidding_engine import BiddingEngine

class TestProblematicHandFix:
    """Test that hand_2025-10-28_21-46-15.json now bids correctly."""

    def test_west_does_not_bid_3clubs(self):
        """
        West should NOT bid 3♣ with only 7 HCP.

        Context:
        - East overcalled 1♠
        - South bid 2♣
        - West has 7 HCP, 5 clubs
        - Old behavior: Bid 3♣ (inappropriate)
        - New behavior: Pass (correct)
        """
        # Load the hand data
        with open('backend/review_requests/hand_2025-10-28_21-46-15.json') as f:
            hand_data = json.load(f)

        # Create West's hand
        west_hand = self._create_hand_from_data(hand_data['all_hands']['West'])

        # Auction at West's turn: 1♥ - 1♠ - 2♣ - ?
        auction = ['1♥', '1♠', '2♣']

        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(
            hand=west_hand,
            auction_history=auction,
            my_position='West',
            vulnerability='None'
        )

        # West should Pass (not 3♣)
        assert bid == 'Pass', f"West bid {bid} but should Pass with only 7 HCP"
        assert '3♣' not in explanation

    def test_north_does_not_bid_3spades(self):
        """
        North should NOT bid 3♠ with only 3 spades.

        Context:
        - North opened 1♥
        - South bid 2♣
        - South doubled 3♣
        - North has 3 spades, 6 hearts
        - Old behavior: Bid 3♠ (inappropriate)
        - New behavior: Bid 3♥ or Pass
        """
        # Load the hand data
        with open('backend/review_requests/hand_2025-10-28_21-46-15.json') as f:
            hand_data = json.load(f)

        # Create North's hand
        north_hand = self._create_hand_from_data(hand_data['all_hands']['North'])

        # Auction at North's turn: 1♥ - 1♠ - 2♣ - 3♣ - Pass - Pass - X - Pass - ?
        auction = ['1♥', '1♠', '2♣', '3♣', 'Pass', 'Pass', 'X', 'Pass']

        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(
            hand=north_hand,
            auction_history=auction,
            my_position='North',
            vulnerability='None'
        )

        # North should NOT bid 3♠ (only 3 spades)
        assert bid != '3♠', f"North bid 3♠ with only 3 spades (should bid 3♥ or Pass)"

        # Should bid 3♥ (6-card suit) or Pass
        assert bid in ['3♥', 'Pass'], f"North bid {bid} but should bid 3♥ or Pass"

    def _create_hand_from_data(self, hand_data: dict) -> Hand:
        """Create Hand object from JSON data."""
        # ... implementation ...
        pass
```

**Run:**
```bash
python3 -m pytest backend/tests/integration/test_hand_2025_10_28_fix.py -v
```

---

## Phase 4: Rollout Strategy

### Step 4.1: Incremental Rollout

```bash
# 1. Implement base class
# 2. Update advancer_bids.py (West's case)
# 3. Test against problematic hand
pytest backend/tests/integration/test_hand_2025_10_28_fix.py::test_west_does_not_bid_3clubs -v

# 4. Update rebids.py (North's case)
# 5. Test against problematic hand
pytest backend/tests/integration/test_hand_2025_10_28_fix.py::test_north_does_not_bid_3spades -v

# 6. Update remaining high-priority modules (responses, responder_rebids, overcalls)
# 7. Run full test suite
pytest backend/tests/ -v

# 8. Update convention modules
# 9. Run full test suite again
pytest backend/tests/ -v

# 10. Run 500-hand simulation (see below)
python3 backend/test_bidding_quality_score.py
```

### Step 4.2: Rollback Plan

**If issues arise:**

1. **Git tags:** Tag each working state
   ```bash
   git tag -a "bid-appropriateness-base-class" -m "Base class implemented"
   git tag -a "bid-appropriateness-advancer" -m "Advancer module updated"
   ```

2. **Feature flag:** Add environment variable
   ```python
   # In base_convention.py
   USE_APPROPRIATENESS_VALIDATION = os.getenv('USE_BID_APPROPRIATENESS', 'true').lower() == 'true'

   def validate_and_adjust_bid(self, ...):
       if not USE_APPROPRIATENESS_VALIDATION:
           # Fall back to old behavior
           return self._old_validate_and_adjust_bid(...)
       # New behavior
       ...
   ```

3. **Quick revert:** Keep old methods as `_legacy_validate()`
   ```python
   def evaluate(self, hand, features):
       if USE_APPROPRIATENESS_VALIDATION:
           return self._new_evaluate(hand, features)
       else:
           return self._legacy_evaluate(hand, features)
   ```

---

## Success Criteria

### Must Pass:
- ✅ All existing unit tests pass
- ✅ All existing integration tests pass
- ✅ New appropriateness tests pass
- ✅ Problematic hand (2025-10-28) fixed:
  - West passes instead of 3♣
  - North bids 3♥ or passes (not 3♠)
- ✅ Bidding Quality Score ≥ 95% (see below)
- ✅ No performance regression (bid generation <50ms)

### Should Achieve:
- 🎯 Zero inappropriate bids in 500-hand simulation
- 🎯 Bidding Quality Score ≥ 98%
- 🎯 All modules using centralized validation
- 🎯 Code coverage ≥ 85% for new methods

---

## Timeline

| Phase | Tasks | Time | Cumulative |
|-------|-------|------|------------|
| Phase 1 | Base class implementation + tests | 2 hours | 2 hours |
| Phase 2 | Update 6 high-priority modules | 3 hours | 5 hours |
| Phase 3 | Integration testing | 1 hour | 6 hours |
| Phase 4 | Update 10 convention modules | 3 hours | 9 hours |
| Phase 5 | 500-hand validation | 1 hour | 10 hours |
| Buffer | Bug fixes, edge cases | 2 hours | 12 hours |

**Total: 10-12 hours**

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing tests | Medium | High | Incremental rollout, run tests after each module |
| Over-conservative validation | Medium | Medium | Start with permissive thresholds, tune based on data |
| Performance regression | Low | Low | Profile before/after, optimize if needed |
| Edge case bugs | Medium | Medium | Comprehensive test suite, 500-hand validation |

---

## Next Steps

1. **Review this plan** - Get approval before implementation
2. **Set up bidding quality score** - See companion document
3. **Implement Phase 1** - Base class + tests
4. **Get checkpoint approval** - Verify base class works
5. **Implement Phase 2** - High-priority modules
6. **Validate against problematic hand** - Ensure fix works
7. **Complete rollout** - Remaining modules
8. **Final validation** - 500-hand quality score

---

## Questions for Review

1. **Thresholds:** Are the HCP thresholds correct for SAYC?
   - 2-level raise: 8+ HCP
   - 3-level raise: 10+ HCP (or 8+ with 4+ support)
   - 4-level raise: 12+ HCP (or 10+ with 5+ support)

2. **Preemptive logic:** Should we allow 3-level bids with 6+ card suits and <10 HCP?
   - Currently: Yes, if 6+ cards and 2+ honors in suit
   - Concern: Might be too liberal?

3. **NT bids:** Should we add special logic for NT bids?
   - Currently: Generic "10 + 2*level_increase" HCP
   - Should we be more specific?

4. **Override policy:** Should convention modules be ALLOWED to override validation?
   - Currently: Yes (can override `_is_bid_appropriate_after_adjustment`)
   - Concern: Might bypass validation?

5. **Adjustment limit:** Is 2 levels the right limit?
   - Currently: Reject adjustments >2 levels
   - Should it be 1 level? 3 levels?

Please review and approve/modify before implementation begins.
