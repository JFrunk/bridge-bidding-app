# Architectural Improvements Action Plan

**Date:** 2025-10-24
**Priority:** High
**Timeframe:** Phased approach (immediate, short-term, long-term)

## Problem Statement

The 7NT bug revealed four systemic architectural issues:

1. **Copy-Paste Vulnerabilities** - Same bug in 6 places
2. **Missing Central Safety** - Each module implements own validation
3. **Testing Gaps** - Unit tests miss systemic issues
4. **Integration Test Gaps** - Long competitive auctions untested

## Proposed Solutions (Phased Approach)

---

## Phase 1: Immediate Actions (This Week)

### 1.1 Create Centralized Bid Safety Module

**Goal:** DRY (Don't Repeat Yourself) - Single source of truth for bid safety

**Implementation:**

Create `backend/engine/bid_safety.py`:

```python
"""
Centralized bid safety checks to prevent unreasonable bids.
All bidding modules should use these functions instead of rolling their own.
"""

from typing import Optional, Tuple
from engine.hand import Hand

class BidSafety:
    """Centralized safety checks for bid validation and adjustment."""

    # Configuration
    MAX_LEVEL_ADJUSTMENT = 2  # Maximum levels we'll adjust a bid
    SLAM_SMALL_MIN_HCP = 33    # Minimum combined HCP for small slam
    SLAM_GRAND_MIN_HCP = 37    # Minimum combined HCP for grand slam
    GAME_3NT_MIN_HCP = 24      # Minimum combined HCP for 3NT
    GAME_4M_MIN_TRUMP = 8      # Minimum trump cards for 4M contract

    @staticmethod
    def safe_adjust_bid(
        original_bid: str,
        next_legal: str,
        auction_history: list,
        hand: Hand,
        explanation: str
    ) -> Tuple[str, str]:
        """
        Safely adjust a bid with multiple safety checks.

        Args:
            original_bid: The bid we wanted to make
            next_legal: The next legal bid of same strain
            auction_history: Full auction history
            hand: Our hand
            explanation: Original explanation

        Returns:
            (bid, explanation) - Either the adjusted bid or Pass with reason
        """
        # Check 1: Level escalation (most common issue)
        escalation_check = BidSafety._check_level_escalation(original_bid, next_legal)
        if escalation_check:
            return escalation_check

        # Check 2: Point requirements for the adjusted level
        point_check = BidSafety._check_point_requirements(next_legal, hand, auction_history)
        if point_check:
            return point_check

        # Check 3: Trump requirements for suit contracts
        trump_check = BidSafety._check_trump_requirements(next_legal, hand)
        if trump_check:
            return trump_check

        # All checks passed - allow adjustment
        adjusted_explanation = f"{explanation} [Adjusted from {original_bid} to {next_legal} for legality]"
        return (next_legal, adjusted_explanation)

    @staticmethod
    def _check_level_escalation(original_bid: str, next_legal: str) -> Optional[Tuple[str, str]]:
        """Check if adjustment escalates too many levels."""
        try:
            original_level = int(original_bid[0])
            adjusted_level = int(next_legal[0])

            if adjusted_level - original_level > BidSafety.MAX_LEVEL_ADJUSTMENT:
                return (
                    "Pass",
                    f"Cannot make reasonable bid at current auction level "
                    f"(suggested {original_bid}, would need {next_legal})."
                )
        except (ValueError, IndexError):
            # Not a level bid (e.g., Pass, X, XX) - no check needed
            pass

        return None

    @staticmethod
    def _check_point_requirements(bid: str, hand: Hand, auction_history: list) -> Optional[Tuple[str, str]]:
        """
        Check if we have sufficient points for the bid level.

        This is an estimate based on our hand + typical partner range.
        More sophisticated analysis would consider partner's actual bids.
        """
        try:
            level = int(bid[0])

            # For slam bids, check if we could possibly have enough points
            if level == 6:
                # Small slam needs 33+ combined
                # Conservative estimate: assume partner has 15+ (we need 18+)
                if hand.hcp < 18:
                    return (
                        "Pass",
                        f"Insufficient points for small slam (have {hand.hcp} HCP, "
                        f"would need 18+ to make 33 combined likely)."
                    )
            elif level == 7:
                # Grand slam needs 37+ combined
                # Conservative estimate: assume partner has 20+ (we need 17+)
                if hand.hcp < 17:
                    return (
                        "Pass",
                        f"Insufficient points for grand slam (have {hand.hcp} HCP, "
                        f"would need 17+ to make 37 combined likely)."
                    )
        except (ValueError, IndexError):
            pass

        return None

    @staticmethod
    def _check_trump_requirements(bid: str, hand: Hand) -> Optional[Tuple[str, str]]:
        """Check if we have sufficient trump for suit contracts at game level."""
        if len(bid) < 2:
            return None

        try:
            level = int(bid[0])
            strain = bid[1:]

            # For 4-level major suit contracts, check trump
            if level == 4 and strain in ['♥', '♠']:
                # We need a fit - check our holding
                our_trump = hand.suit_lengths.get(strain, 0)

                # If we have fewer than 3, unlikely to have 8+ combined
                if our_trump < 3:
                    return (
                        "Pass",
                        f"Insufficient trump for {bid} contract "
                        f"(have only {our_trump} {strain})."
                    )
        except (ValueError, IndexError):
            pass

        return None

    @staticmethod
    def is_unreasonable_slam(bid: str, hand: Hand, partner_estimated_hcp: int = 15) -> bool:
        """
        Detect if a slam bid is unreasonable given our hand.

        Args:
            bid: The bid to check
            hand: Our hand
            partner_estimated_hcp: Conservative estimate of partner's HCP

        Returns:
            True if slam is unreasonable, False otherwise
        """
        try:
            level = int(bid[0])

            if level >= 6:
                combined_hcp = hand.hcp + partner_estimated_hcp

                if level == 6 and combined_hcp < BidSafety.SLAM_SMALL_MIN_HCP:
                    return True

                if level == 7 and combined_hcp < BidSafety.SLAM_GRAND_MIN_HCP:
                    return True
        except (ValueError, IndexError):
            pass

        return False

    @staticmethod
    def log_bid_adjustment(original_bid: str, adjusted_bid: str, reason: str):
        """
        Log bid adjustments for analysis and debugging.

        This helps identify patterns of problematic adjustments.
        """
        # TODO: Implement proper logging
        # For now, just print to console
        if adjusted_bid != original_bid:
            print(f"[BID ADJUSTMENT] {original_bid} → {adjusted_bid}: {reason}")
```

**Integration:**

Update `ConventionModule` base class:

```python
class ConventionModule:
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Base implementation with centralized safety.
        Subclasses should override _evaluate_internal() instead.
        """
        auction_history = features.get('auction_history', [])

        # Get the raw bid from subclass
        result = self._evaluate_internal(hand, features)

        if not result:
            return None

        bid, explanation = result

        # Always pass Pass bids through
        if bid == "Pass":
            return result

        # Validate the bid is legal
        if BidValidator.is_legal_bid(bid, auction_history):
            return result

        # Bid is illegal - use centralized safety to adjust
        next_legal = get_next_legal_bid(bid, auction_history)
        if next_legal:
            # Use centralized safety checks
            return BidSafety.safe_adjust_bid(
                original_bid=bid,
                next_legal=next_legal,
                auction_history=auction_history,
                hand=hand,
                explanation=explanation
            )

        # No legal bid possible - pass
        return None

    def _evaluate_internal(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Subclasses should override this instead of evaluate().
        This ensures all safety checks are applied consistently.
        """
        raise NotImplementedError("Subclasses must implement _evaluate_internal()")
```

**Migration Strategy:**

1. Create `bid_safety.py` module
2. Update `ConventionModule` base class
3. Gradually migrate modules to use base class implementation
4. Remove duplicated safety code from individual modules

**Estimated Time:** 4-6 hours

---

### 1.2 Add Slam Detection Monitoring

**Goal:** Catch unreasonable slams before they become bug reports

**Implementation:**

Add to `backend/engine/bidding_engine.py`:

```python
class BiddingEngine:
    def __init__(self):
        # ... existing code ...
        self.slam_warnings = []  # Track questionable slams

    def get_next_bid(self, hand: Hand, auction_history: list, my_position: str,
                     vulnerability: str, explanation_level: str = "detailed"):
        """Get the next bid with safety monitoring."""

        # ... existing code to get bid ...

        # SAFETY NET: Monitor for unreasonable slams
        if self._is_unreasonable_slam(bid, hand, auction_history):
            warning = {
                'bid': bid,
                'hand_hcp': hand.hcp,
                'position': my_position,
                'auction': auction_history.copy()
            }
            self.slam_warnings.append(warning)

            # Log warning but DON'T override (might be legitimate)
            print(f"⚠️  WARNING: Potential unreasonable slam: {bid} with {hand.hcp} HCP")

        return (bid, explanation)

    def _is_unreasonable_slam(self, bid: str, hand: Hand, auction_history: list) -> bool:
        """Check if slam bid seems unreasonable."""
        try:
            level = int(bid[0])

            if level >= 6:
                # Conservative check: do we have enough points?
                # Small slam: need 33+ combined, assume partner has 15+, we need 18+
                # Grand slam: need 37+ combined, assume partner has 20+, we need 17+

                if level == 6 and hand.hcp < 18:
                    return True

                if level == 7 and hand.hcp < 17:
                    return True
        except (ValueError, IndexError):
            pass

        return False
```

**Estimated Time:** 1-2 hours

---

### 1.3 Create Basic Integration Test Framework

**Goal:** Test multi-module interactions and long auctions

**Implementation:**

Create `backend/tests/integration/test_competitive_auctions.py`:

```python
"""
Integration tests for competitive auctions.
These test multi-module interactions and long auction sequences.
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

class TestCompetitiveAuctions:
    """Test that AI behaves reasonably in competitive auctions."""

    def test_no_slam_with_insufficient_hcp(self):
        """
        Ensure AI doesn't bid slam with insufficient combined HCP.

        This is a regression test for the 7NT disaster bug.
        """
        # Create hands with only 27 combined HCP (E/W)
        hands = self._create_hands_27_hcp()

        engine = BiddingEngine()
        auction = self._simulate_auction(engine, hands, dealer='North')

        final_contract = self._get_final_contract(auction)

        if final_contract:
            level = int(final_contract[0])

            # With 27 combined HCP, should NOT bid slam
            assert level < 6, (
                f"AI bid {final_contract} with only 27 combined HCP! "
                f"Slam requires 33+ HCP."
            )

    def test_advancer_doesnt_escalate(self):
        """
        Test that advancer doesn't escalate unreasonably in competitive auction.

        Scenario: Partner overcalls, gets doubled, we support with 8 HCP.
        Should not bid to slam level.
        """
        # TODO: Implement
        pass

    def test_blackwood_in_competitive_auction(self):
        """
        Test Blackwood doesn't escalate when opponents interfere.

        Scenario: 4NT asks for aces, opponents bid 5♦, partner shows aces.
        We should NOT automatically bid 7NT just because of adjustment.
        """
        # TODO: Implement
        pass

    def test_long_auction_stability(self):
        """
        Test that long auctions (15+ bids) remain stable.

        Ensures no module gets stuck in a loop or escalates unreasonably.
        """
        # TODO: Implement
        pass

    def _create_hands_27_hcp(self):
        """Create the exact hands from the 7NT bug report."""
        # Implementation from test_bidding_fix.py
        pass

    def _simulate_auction(self, engine, hands, dealer):
        """Simulate a full auction until 3 passes."""
        auction = []
        positions = ['North', 'East', 'South', 'West']
        dealer_index = positions.index(dealer)
        consecutive_passes = 0
        max_bids = 40  # Safety limit

        for _ in range(max_bids):
            current_pos = positions[(dealer_index + len(auction)) % 4]
            current_hand = hands[current_pos]

            bid, _ = engine.get_next_bid(
                current_hand,
                auction,
                current_pos,
                "None"
            )

            auction.append(bid)

            if bid == "Pass":
                consecutive_passes += 1
            else:
                consecutive_passes = 0

            if consecutive_passes >= 3 and len(auction) > 3:
                break

        return auction

    def _get_final_contract(self, auction):
        """Extract final contract from auction."""
        for bid in reversed(auction):
            if bid not in ['Pass', 'X', 'XX']:
                return bid
        return None


class TestBidAdjustmentPatterns:
    """Test that bid adjustments follow safe patterns."""

    def test_no_3_level_adjustments(self):
        """Ensure no module adjusts bids by 3+ levels."""
        # TODO: Run simulation and check logs
        pass

    def test_adjustment_logging(self):
        """Ensure all adjustments are properly logged."""
        # TODO: Implement
        pass
```

Create `backend/tests/integration/test_slam_detection.py`:

```python
"""
Integration tests for slam detection and safety.
"""

import pytest
from engine.bid_safety import BidSafety
from engine.hand import Hand, Card

class TestSlamSafety:
    """Test slam detection and prevention."""

    def test_small_slam_requires_sufficient_hcp(self):
        """6-level contracts should require 33+ combined HCP."""
        # Create hand with 15 HCP (marginal for slam opposite 18+)
        weak_hand = self._create_hand_with_hcp(15)

        # Should flag as potentially unreasonable
        assert BidSafety.is_unreasonable_slam("6♣", weak_hand, partner_estimated_hcp=15)

        # Create hand with 18 HCP (reasonable for slam opposite 15+)
        strong_hand = self._create_hand_with_hcp(18)

        # Should NOT flag
        assert not BidSafety.is_unreasonable_slam("6♣", strong_hand, partner_estimated_hcp=15)

    def test_grand_slam_requires_sufficient_hcp(self):
        """7-level contracts should require 37+ combined HCP."""
        # Create hand with 15 HCP (insufficient for grand slam)
        weak_hand = self._create_hand_with_hcp(15)

        # Should flag as unreasonable
        assert BidSafety.is_unreasonable_slam("7NT", weak_hand, partner_estimated_hcp=20)

        # Create hand with 20 HCP (reasonable for grand opposite 18+)
        strong_hand = self._create_hand_with_hcp(20)

        # Should NOT flag
        assert not BidSafety.is_unreasonable_slam("7NT", strong_hand, partner_estimated_hcp=18)

    def _create_hand_with_hcp(self, target_hcp):
        """Create a hand with approximately target HCP."""
        # TODO: Implement hand generation
        pass
```

**Estimated Time:** 4-6 hours

---

## Phase 2: Short-Term Actions (Next 2 Weeks)

### 2.1 Migrate All Modules to Centralized Safety

**Goal:** Remove all duplicated safety code

**Steps:**

1. Update each module to inherit properly from `ConventionModule`
2. Rename `evaluate()` → `_evaluate_internal()` in each module
3. Remove local safety checks
4. Test each module individually
5. Run full regression suite

**Modules to migrate:**
- ✅ `responses.py`
- ✅ `rebids.py`
- ✅ `responder_rebids.py`
- ✅ `advancer_bids.py`
- ✅ `blackwood.py`
- ✅ `michaels_cuebid.py`
- ✅ `jacoby_transfers.py`
- And ~11 more modules

**Estimated Time:** 8-12 hours (distributed across team)

---

### 2.2 Comprehensive Integration Test Suite

**Goal:** Test all auction types and module interactions

**Test Categories:**

1. **Competitive Auctions** (10-15 tests)
   - Overcalls and advances
   - Doubles and redoubles
   - Preemptive interference
   - Balancing situations

2. **Long Auctions** (5-10 tests)
   - 15+ bid sequences
   - Multiple suit explorations
   - Slam tries with competition

3. **Slam Scenarios** (10-15 tests)
   - Blackwood with interference
   - Cuebidding sequences
   - Quantitative vs conventional 4NT
   - Grand slam force

4. **Convention Interactions** (10-15 tests)
   - Stayman + Jacoby
   - Fourth suit forcing + support
   - Splinters + Blackwood

5. **Edge Cases** (10-15 tests)
   - All pass auctions
   - Psychic bids
   - Unusual distributions
   - Maximum level auctions (7-level)

**Estimated Time:** 20-30 hours

---

### 2.3 Add Comprehensive Logging and Monitoring

**Goal:** Visibility into AI decision-making

**Implementation:**

Create `backend/engine/bidding_monitor.py`:

```python
"""
Monitoring and analytics for bidding decisions.
"""

import json
from datetime import datetime
from typing import Dict, List

class BiddingMonitor:
    """Tracks and analyzes bidding patterns for quality assurance."""

    def __init__(self):
        self.adjustments = []
        self.slams = []
        self.warnings = []

    def log_adjustment(self, original: str, adjusted: str, reason: str, hand_hcp: int):
        """Log a bid adjustment."""
        self.adjustments.append({
            'timestamp': datetime.now().isoformat(),
            'original': original,
            'adjusted': adjusted,
            'reason': reason,
            'hand_hcp': hand_hcp,
            'levels_adjusted': self._calc_level_diff(original, adjusted)
        })

    def log_slam(self, bid: str, hand_hcp: int, auction: List[str]):
        """Log a slam bid for analysis."""
        self.slams.append({
            'timestamp': datetime.now().isoformat(),
            'bid': bid,
            'hand_hcp': hand_hcp,
            'auction_length': len(auction),
            'auction': auction.copy()
        })

    def get_report(self) -> Dict:
        """Generate summary report."""
        return {
            'total_adjustments': len(self.adjustments),
            'large_adjustments': len([a for a in self.adjustments if a['levels_adjusted'] > 2]),
            'total_slams': len(self.slams),
            'questionable_slams': len([s for s in self.slams if s['hand_hcp'] < 18]),
            'total_warnings': len(self.warnings)
        }

    def _calc_level_diff(self, bid1: str, bid2: str) -> int:
        """Calculate level difference between two bids."""
        try:
            return abs(int(bid2[0]) - int(bid1[0]))
        except:
            return 0
```

**Estimated Time:** 4-6 hours

---

## Phase 3: Long-Term Actions (Next Sprint/Month)

### 3.1 Architectural Refactoring

**Goal:** Clean architecture with clear separation of concerns

**Proposed Architecture:**

```
backend/engine/
├── core/
│   ├── bid_safety.py          # Centralized safety (NEW)
│   ├── bid_validator.py        # Legality checks (existing)
│   └── bidding_monitor.py      # Monitoring (NEW)
│
├── base/
│   └── convention_module.py    # Enhanced base class (UPDATED)
│
├── modules/
│   ├── opening/
│   │   └── opening_bids.py
│   ├── responding/
│   │   ├── responses.py
│   │   └── responder_rebids.py
│   ├── competitive/
│   │   ├── overcalls.py
│   │   ├── advancer_bids.py
│   │   └── doubles/
│   └── conventions/
│       ├── stayman.py
│       ├── jacoby.py
│       ├── blackwood.py
│       └── ...
│
└── tests/
    ├── unit/                   # Module-specific tests
    ├── integration/            # Cross-module tests (NEW)
    └── regression/             # Bug regression tests (NEW)
```

**Estimated Time:** 20-40 hours

---

### 3.2 AI Quality Dashboard

**Goal:** Real-time monitoring of AI bidding quality

**Features:**

1. **Live Monitoring**
   - Current game statistics
   - Recent adjustments
   - Warning counts

2. **Historical Analysis**
   - Trend charts over time
   - Most common adjustment patterns
   - Slam bid analysis

3. **Regression Detection**
   - Alert when patterns change
   - Detect new systemic issues early

**Implementation:**
- Web dashboard (React/Vue)
- Backend API for statistics
- Database for historical data

**Estimated Time:** 40-60 hours

---

### 3.3 Property-Based Testing

**Goal:** Catch entire classes of bugs automatically

**Implementation:**

Use Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st
from hypothesis.strategies import composite

@composite
def valid_hands(draw):
    """Strategy for generating valid 13-card hands."""
    # TODO: Implement
    pass

@given(valid_hands(), valid_hands(), valid_hands(), valid_hands())
def test_no_unreasonable_slams(north, east, south, west):
    """
    Property: In any auction, if AI bids slam, combined HCP must be sufficient.
    """
    hands = {'North': north, 'East': east, 'South': south, 'West': west}
    engine = BiddingEngine()

    # Simulate auction
    auction = simulate_full_auction(engine, hands)
    final_contract = get_final_contract(auction)

    if final_contract and int(final_contract[0]) >= 6:
        # Get declarer and partner
        declaring_pair_hcp = get_declaring_pair_hcp(hands, auction)

        # Property: Slam requires sufficient HCP
        if int(final_contract[0]) == 6:
            assert declaring_pair_hcp >= 30, f"Small slam with only {declaring_pair_hcp} HCP"
        elif int(final_contract[0]) == 7:
            assert declaring_pair_hcp >= 34, f"Grand slam with only {declaring_pair_hcp} HCP"
```

**Estimated Time:** 16-24 hours

---

## Implementation Priority

### Priority 1 (Critical) - Week 1
- ✅ Phase 1.1: Centralized Safety Module (6 hours)
- ✅ Phase 1.2: Slam Detection Monitoring (2 hours)
- ✅ Phase 1.3: Basic Integration Tests (6 hours)

**Total: ~14 hours**

### Priority 2 (High) - Week 2-3
- Phase 2.1: Migrate All Modules (12 hours)
- Phase 2.2: Comprehensive Integration Tests (30 hours)
- Phase 2.3: Logging and Monitoring (6 hours)

**Total: ~48 hours**

### Priority 3 (Medium) - Week 4+
- Phase 3.1: Architectural Refactoring (40 hours)
- Phase 3.2: AI Quality Dashboard (60 hours)
- Phase 3.3: Property-Based Testing (24 hours)

**Total: ~124 hours**

---

## Success Metrics

### Immediate (After Phase 1)
- ✅ Zero duplicated safety code
- ✅ All adjustments logged
- ✅ Basic integration tests passing

### Short-Term (After Phase 2)
- ✅ All modules use centralized safety
- ✅ 50+ integration tests covering all auction types
- ✅ Monitoring dashboard showing key metrics

### Long-Term (After Phase 3)
- ✅ Clean architectural separation
- ✅ Real-time quality monitoring
- ✅ Property-based tests catching entire bug classes
- ✅ Zero systemic vulnerabilities

---

## Risk Mitigation

### Risk 1: Refactoring Breaks Existing Functionality
**Mitigation:**
- Phased approach (immediate fixes first)
- Comprehensive regression testing
- Feature flags for new safety checks
- Gradual rollout

### Risk 2: Performance Impact
**Mitigation:**
- Benchmark safety checks
- Optimize hot paths
- Cache expensive calculations
- Profile before/after

### Risk 3: False Positives
**Mitigation:**
- Configurable thresholds
- Warning vs blocking modes
- Logging for analysis
- Iterative tuning

---

## Conclusion

This plan addresses all four architectural issues:

1. ✅ **Copy-Paste Vulnerabilities** → Centralized `BidSafety` module
2. ✅ **Missing Central Safety** → Enhanced `ConventionModule` base class
3. ✅ **Testing Gaps** → Comprehensive integration test suite
4. ✅ **Integration Test Gaps** → Property-based testing + monitoring

**Recommended Approach:**
1. Start with Phase 1 (this week) - immediate value
2. Phase 2 (next 2 weeks) - systematic improvements
3. Phase 3 (next month) - long-term architecture

This gives immediate bug prevention while building toward a robust, maintainable architecture.
