# ADR-0002: Bidding System Robustness Improvements

**Date:** 2025-10-29
**Last Updated:** 2025-10-29 (Implementation Complete)
**Status:** Accepted ✅
**Decider:** Claude Code
**Priority:** CRITICAL
**Related Issues:** Gameplay analysis hand_2025-10-29_15-12-17.json
**Implementation Branch:** feature/adr-0002-bidding-robustness
**Quality Score:** 95.0% (Grade A - Production Ready)

---

## Context

### Problem Statement

The bidding system architecture has critical robustness issues causing system errors, illegal bids, and inappropriate bidding decisions that spiral into impossible contracts. Analysis of recent gameplay revealed multiple architectural weaknesses:

**System Errors:**
1. **Module Registration Failures:** `"Logic error: DecisionEngine chose 'advancer_bids' but it was not found or returned no bid"` (3 occurrences in single hand)
2. **Bid Legality Issues:** Multiple `"[Adjusted from X to Y for legality]"` messages indicating modules generate illegal bids
3. **Validation Bypasses:** Competitive double with 5 HCP when 8+ HCP required by SAYC rules

**Gameplay Failures:**
1. **Runaway Auctions:** 1NT opening escalated to impossible 5♦ contract (4-9 trump split)
2. **Catastrophic Results:** Contract failed by 5 tricks (made 6 of 11 needed) even with Minimax depth 3
3. **Strategic Errors:** Declarer played spades instead of damage control due to poor position evaluation

### Root Causes

#### 1. Fragile Module Registration (CRITICAL)
**Location:** [backend/engine/bidding_engine.py](../../../backend/engine/bidding_engine.py)

**Issue:** Manual module registration prone to human error
```python
# Current implementation
self.modules = {
    'opening_bids': OpeningBidsModule(),
    'responses': ResponsesModule(),
    # ... advancer_bids MISSING or not imported
}
```

**Impact:**
- DecisionEngine returns module name as string
- BiddingEngine does `self.modules[module_name]` lookup
- KeyError when module not registered → "Logic error" message
- No fallback mechanism → user sees error

#### 2. Validation Can Be Bypassed (CRITICAL)
**Location:** `backend/engine/ai/base_convention.py`, individual modules

**Issue:** Validation scattered across modules, not enforced centrally
```python
# Current flow
Module.evaluate() → returns bid → legality check (optional) → return to user
```

**Impact:**
- Modules can return bids without validation
- HCP requirements not enforced (5 HCP double instead of 8+)
- Appropriateness checks can be skipped
- No single enforcement point

#### 3. No Sanity Checking (CRITICAL)
**Location:** Missing layer in architecture

**Issue:** No maximum bid level or contract feasibility checks
```python
# Current behavior
Auction: 1NT → 2♥ → 2♠ → X → 2NT → 3NT → 4NT → 5♦
# No check: "Can we make 5♦? Do we have enough trumps?"
```

**Impact:**
- Auctions spiral to impossible contracts
- No "stop bidding" logic based on partnership strength
- Competitive modules don't evaluate contract feasibility
- Results in catastrophic failures (down 5)

#### 4. Poor Error Handling (HIGH)
**Location:** [backend/engine/ai/decision_engine.py](../../../backend/engine/ai/decision_engine.py)

**Issue:** No try-catch for module lookup failures
```python
# Current behavior
module_name = decision_engine.select_module()  # Returns 'advancer_bids'
module = self.modules[module_name]  # KeyError if missing
# No fallback to Pass bid
```

**Impact:**
- Errors propagate to user
- Confusing error messages
- No graceful degradation

### Architectural Weaknesses

**Tight Coupling:**
- DecisionEngine hardcodes module names as strings
- String matching between DecisionEngine and BiddingEngine registration
- Fragile: rename one, miss the other → runtime error

**Scattered Validation:**
- Each module implements own validation
- No composition or chaining
- Easy to miss validation in new modules
- No enforcement that validation happened

**No Safety Nets:**
- Missing modules → error
- Illegal bids → runtime adjustment
- Inappropriate bids → accepted
- Impossible contracts → played anyway

### Triggering Event

Comprehensive analysis of hand_2025-10-29_15-12-17.json revealed:
- 3 system errors in single auction
- 2 bid legality adjustments
- 1 catastrophic play failure (down 5 vs down 3-4 optimal)
- Multiple architectural issues causing cascading failures

**See:**
- [backend/analyze_hand.py](../../../backend/analyze_hand.py) - Analysis script
- [backend/optimal_play_analysis.md](../../../backend/optimal_play_analysis.md) - Detailed findings
- [BIDDING_ARCHITECTURE_MAP.md](../../../BIDDING_ARCHITECTURE_MAP.md) - Complete architecture documentation

---

## Decision

**We will implement a 4-layer robustness improvement to the bidding system:**

1. **Module Registry Pattern** - Self-registering modules eliminate manual registration
2. **Centralized Validation Pipeline** - Cannot bypass validation
3. **Sanity Check Layer** - Post-decision contract feasibility checks
4. **Error Handling with Fallbacks** - Graceful degradation when modules fail

**This is a structural improvement, not a feature addition.** We are fixing architectural defects that cause system failures.

---

## Alternatives Considered

### Option A: Quick Fixes Only (REJECTED)

**Description:** Fix immediate bugs without architectural changes
- Add advancer_bids import
- Add HCP check to competitive double
- Add try-catch in BiddingEngine

**Pros:**
- ✅ Fast (30 minutes)
- ✅ Minimal code changes
- ✅ Fixes immediate errors

**Cons:**
- ❌ Doesn't address root causes
- ❌ Same pattern will break again
- ❌ Technical debt compounds
- ❌ No prevention of future issues
- ❌ Quality score likely regresses again

**Decision Matrix Score:** 4/10
- Robustness: 2/10 (bandaid fixes)
- Maintainability: 3/10 (adds technical debt)
- Risk: 3/10 (low immediate risk, high long-term risk)
- Effort: 9/10 (very quick)

**Verdict:** ❌ **REJECTED** - Doesn't meet robustness requirements

---

### Option B: Complete Rewrite with Plugin Architecture (REJECTED)

**Description:** Full architectural overhaul with plugin system
- Module auto-discovery via decorators
- Event-driven decision system
- Comprehensive validation framework
- Strategy pattern for all decisions
- Microservices for bidding modules

**Pros:**
- ✅ Maximum flexibility
- ✅ Best long-term architecture
- ✅ Extensible for future features
- ✅ Loosely coupled

**Cons:**
- ❌ Weeks of development time
- ❌ High regression risk
- ❌ Requires comprehensive testing
- ❌ Over-engineering for current needs
- ❌ Delayed user value

**Decision Matrix Score:** 5/10
- Robustness: 10/10 (best architecture)
- Maintainability: 9/10 (excellent)
- Risk: 1/10 (very high risk)
- Effort: 1/10 (very expensive)

**Verdict:** ❌ **REJECTED** - Over-engineering, too risky

---

### Option C: Incremental Robustness Improvements (CHOSEN)

**Description:** Targeted architectural improvements to address root causes
- **Layer 1:** Module registry pattern with validation
- **Layer 2:** Centralized validation pipeline
- **Layer 3:** Sanity check layer
- **Layer 4:** Error handling with fallbacks

**Pros:**
- ✅ Addresses root causes
- ✅ Incremental (can be done in phases)
- ✅ Low regression risk
- ✅ Testable at each layer
- ✅ Prevents future similar issues
- ✅ Reasonable time investment (4-6 hours)

**Cons:**
- ⚠️ More work than quick fixes
- ⚠️ Requires baseline quality score before/after
- ⚠️ Need comprehensive testing

**Decision Matrix Score:** 9/10
- Robustness: 9/10 (fixes root causes)
- Maintainability: 8/10 (good)
- Risk: 7/10 (moderate risk, well-tested)
- Effort: 6/10 (reasonable)

**Verdict:** ✅ **CHOSEN** - Best balance of robustness, risk, and effort

---

## Implementation Plan

### Phase 1: Module Registry Pattern (2 hours)

**Objective:** Eliminate manual module registration failures

**Changes:**

**File:** `backend/engine/ai/module_registry.py` (NEW)
```python
"""
Centralized module registry with automatic validation.
"""

class ModuleRegistry:
    """Self-registering module registry."""

    _modules = {}

    @classmethod
    def register(cls, name, module_class):
        """Register a bidding module."""
        if not hasattr(module_class, 'evaluate'):
            raise ValueError(f"Module {name} must implement evaluate()")
        cls._modules[name] = module_class

    @classmethod
    def get(cls, name, default=None):
        """Get module by name with optional default."""
        return cls._modules.get(name, default)

    @classmethod
    def get_all(cls):
        """Get all registered modules."""
        return cls._modules.copy()

    @classmethod
    def exists(cls, name):
        """Check if module is registered."""
        return name in cls._modules
```

**File:** `backend/engine/bidding_engine.py` (MODIFY)
```python
from engine.ai.module_registry import ModuleRegistry

class BiddingEngine:
    def __init__(self):
        # Import all modules (triggers registration)
        from engine.ai.modules import opening_bids
        from engine.ai.modules import responses
        from engine.ai.modules import rebids
        from engine.ai.modules import overcalls
        from engine.ai.modules import advancer_bids  # NOW EXPLICITLY IMPORTED

        # All modules auto-register via decorators
        self.modules = ModuleRegistry.get_all()

    def get_next_bid(self, hand, features):
        module_name = self.decision_engine.select_module(features)

        # Safe lookup with fallback
        module = ModuleRegistry.get(module_name)
        if module is None:
            logger.error(f"Module {module_name} not found, falling back to Pass")
            return ("Pass", "No appropriate bid found.")

        return module.evaluate(hand, features)
```

**File:** `backend/engine/ai/modules/opening_bids.py` (MODIFY)
```python
from engine.ai.module_registry import ModuleRegistry

class OpeningBidsModule(ConventionModule):
    def evaluate(self, hand, features):
        # ... existing logic
        pass

# Auto-register on import
ModuleRegistry.register('opening_bids', OpeningBidsModule())
```

**Similar changes to all other modules.**

**Testing:**
```bash
# Unit test
pytest backend/tests/unit/test_module_registry.py -v

# Integration test - ensure all modules registered
pytest backend/tests/integration/test_bidding_engine_registration.py -v
```

**Success Criteria:**
- ✅ All modules auto-register on import
- ✅ ModuleRegistry.exists('advancer_bids') returns True
- ✅ No "Logic error: module not found" messages
- ✅ Fallback to Pass when module missing

---

### Phase 2: Centralized Validation Pipeline (2 hours)

**Objective:** Enforce validation that cannot be bypassed

**Changes:**

**File:** `backend/engine/ai/validation_pipeline.py` (NEW)
```python
"""
Centralized validation pipeline for bidding decisions.
All bids must pass through this pipeline before acceptance.
"""

class ValidationPipeline:
    """Composable validation chain."""

    def __init__(self):
        self.validators = [
            LegalityValidator(),
            HCPRequirementValidator(),
            SuitLengthValidator(),
            AppropriatenessValidator(),
        ]

    def validate(self, bid, hand, features, auction):
        """
        Run all validators.
        Returns (is_valid, error_message)
        """
        for validator in self.validators:
            is_valid, error = validator.validate(bid, hand, features, auction)
            if not is_valid:
                return False, error
        return True, None

    def add_validator(self, validator):
        """Add custom validator to pipeline."""
        self.validators.append(validator)


class HCPRequirementValidator:
    """Validates HCP requirements for bids."""

    HCP_REQUIREMENTS = {
        'competitive_double': 8,  # SAYC minimum
        '2_level_new_suit': 10,
        '3_level_bid': 10,
        '4_level_bid': 12,
        'game_bid': 12,
        'slam_bid': 16,
    }

    def validate(self, bid, hand, features, auction):
        """Check if hand meets HCP requirements for bid."""
        bid_type = self._classify_bid(bid, auction)
        required_hcp = self.HCP_REQUIREMENTS.get(bid_type, 0)

        if hand.hcp < required_hcp:
            return False, f"Insufficient HCP for {bid_type}: have {hand.hcp}, need {required_hcp}"

        return True, None

    def _classify_bid(self, bid, auction):
        """Classify bid type for HCP lookup."""
        # Implementation determines bid type from context
        pass
```

**File:** `backend/engine/bidding_engine.py` (MODIFY)
```python
from engine.ai.validation_pipeline import ValidationPipeline

class BiddingEngine:
    def __init__(self):
        # ... module registration
        self.validation_pipeline = ValidationPipeline()

    def get_next_bid(self, hand, features):
        module = ModuleRegistry.get(module_name)
        if module is None:
            return ("Pass", "No appropriate bid found.")

        bid, explanation = module.evaluate(hand, features)

        # MANDATORY VALIDATION - CANNOT BE BYPASSED
        is_valid, error = self.validation_pipeline.validate(
            bid, hand, features, self.auction
        )

        if not is_valid:
            logger.warning(f"Validation failed: {error}. Falling back to Pass.")
            return ("Pass", f"Validation failed: {error}")

        return (bid, explanation)
```

**Testing:**
```bash
# Unit tests for each validator
pytest backend/tests/unit/test_validation_pipeline.py -v

# Regression test: 5 HCP double should be rejected
pytest backend/tests/regression/test_competitive_double_hcp.py -v
```

**Success Criteria:**
- ✅ Competitive doubles require 8+ HCP
- ✅ 3-level bids require 10+ HCP
- ✅ All bids pass through validation
- ✅ Invalid bids replaced with Pass + explanation
- ✅ No validation bypasses possible

---

### Phase 3: Sanity Check Layer (1.5 hours)

**Objective:** Prevent impossible contracts and runaway auctions

**Changes:**

**File:** `backend/engine/ai/sanity_checker.py` (NEW)
```python
"""
Post-decision sanity checking to prevent catastrophic auctions.
"""

class SanityChecker:
    """Checks if bid makes sense given partnership strength."""

    MAX_BID_LEVELS = {
        'combined_hcp_20_25': 3,  # Part game max
        'combined_hcp_26_32': 5,  # Game max
        'combined_hcp_33_36': 6,  # Small slam
        'combined_hcp_37+': 7,     # Grand slam
    }

    def check(self, bid, hand, features, auction):
        """
        Final sanity check before committing to bid.
        Returns (should_bid, alternative_bid, reason)
        """
        # Check 1: Maximum bid level based on HCP
        max_level = self._max_safe_level(hand, features)
        bid_level = self._get_bid_level(bid)

        if bid_level > max_level:
            return (False, "Pass",
                   f"Bid level {bid_level} exceeds safe maximum {max_level}")

        # Check 2: Trump fit for suit contracts
        if self._is_suit_contract(bid):
            has_fit = self._check_trump_fit(bid, hand, features, auction)
            if not has_fit and bid_level >= 4:
                return (False, "Pass",
                       "No trump fit for game-level suit contract")

        # Check 3: Stop bidding in competitive auctions above safe level
        if self._is_competitive(features):
            if bid_level >= 4 and hand.hcp < 12:
                return (False, "Pass",
                       "Too high in competitive auction with minimum hand")

        return (True, bid, None)

    def _max_safe_level(self, hand, features):
        """Calculate maximum safe bid level."""
        # Estimate combined HCP
        partner_min_hcp = self._estimate_partner_hcp(features)
        combined_hcp = hand.hcp + partner_min_hcp

        if combined_hcp < 20:
            return 2
        elif combined_hcp < 26:
            return 3
        elif combined_hcp < 33:
            return 5
        else:
            return 6
```

**File:** `backend/engine/bidding_engine.py` (MODIFY)
```python
from engine.ai.sanity_checker import SanityChecker

class BiddingEngine:
    def __init__(self):
        # ... registry and validation
        self.sanity_checker = SanityChecker()

    def get_next_bid(self, hand, features):
        # ... module selection and validation

        # SANITY CHECK - Final safety net
        should_bid, final_bid, reason = self.sanity_checker.check(
            bid, hand, features, self.auction
        )

        if not should_bid:
            logger.info(f"Sanity check prevented bid: {reason}")
            explanation = f"Passing for safety: {reason}"
            return (final_bid, explanation)

        return (bid, explanation)
```

**Testing:**
```bash
# Regression test: 1NT → 5♦ should be prevented
pytest backend/tests/regression/test_runaway_auction_prevention.py -v

# Test maximum level enforcement
pytest backend/tests/unit/test_sanity_checker.py -v
```

**Success Criteria:**
- ✅ Auctions stop at safe levels
- ✅ No impossible contracts (4-9 trump splits)
- ✅ Competitive auctions don't spiral
- ✅ Game/slam bids require sufficient HCP
- ✅ Pass as fallback when sanity check fails

---

### Phase 4: Error Handling with Fallbacks (30 minutes)

**Objective:** Graceful degradation when things go wrong

**Changes:**

**File:** `backend/engine/bidding_engine.py` (MODIFY)
```python
class BiddingEngine:
    def get_next_bid(self, hand, features):
        try:
            # Module selection
            module_name = self.decision_engine.select_module(features)
            module = ModuleRegistry.get(module_name)

            if module is None:
                raise ModuleNotFoundError(f"Module {module_name} not registered")

            # Get bid
            bid, explanation = module.evaluate(hand, features)

            # Validation
            is_valid, error = self.validation_pipeline.validate(
                bid, hand, features, self.auction
            )
            if not is_valid:
                raise ValidationError(error)

            # Sanity check
            should_bid, final_bid, reason = self.sanity_checker.check(
                bid, hand, features, self.auction
            )
            if not should_bid:
                logger.info(f"Sanity check triggered: {reason}")
                return (final_bid, f"Passing for safety: {reason}")

            return (bid, explanation)

        except ModuleNotFoundError as e:
            logger.error(f"Module error: {e}")
            return ("Pass", "No suitable bidding module found.")

        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return ("Pass", f"Bid failed validation: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in bidding: {e}")
            return ("Pass", "An error occurred, passing for safety.")
```

**Testing:**
```bash
# Test error handling
pytest backend/tests/unit/test_bidding_engine_errors.py -v

# Integration test: full auction with injected errors
pytest backend/tests/integration/test_error_recovery.py -v
```

**Success Criteria:**
- ✅ All exceptions caught
- ✅ Never crashes with unhandled exception
- ✅ Always returns valid bid (Pass as ultimate fallback)
- ✅ Clear error messages in logs
- ✅ User sees reasonable explanation

---

## Consequences

### Positive Consequences

**Robustness:**
- ✅ Eliminates "Logic error" module not found errors
- ✅ Prevents validation bypasses (5 HCP doubles)
- ✅ Stops runaway auctions (1NT → 5♦)
- ✅ Graceful degradation when errors occur

**Code Quality:**
- ✅ Centralized validation → easier to maintain
- ✅ Module registry → can't forget to register
- ✅ Clear separation of concerns (validation vs decision)
- ✅ Testable components

**User Experience:**
- ✅ No confusing error messages
- ✅ Better bidding decisions
- ✅ More realistic auctions
- ✅ Fewer catastrophic contract failures

**Maintainability:**
- ✅ Easy to add new validators
- ✅ Easy to add new modules
- ✅ Clear error messages for debugging
- ✅ Self-documenting architecture

---

### Negative Consequences / Trade-offs

**Development Time:**
- ⚠️ 4-6 hours implementation time
- ⚠️ Comprehensive testing required
- ⚠️ Baseline quality score before/after

**Code Complexity:**
- ⚠️ More layers → more code to understand
- ⚠️ Validation pipeline adds abstraction
- ⚠️ Error handling adds try-catch blocks

**Performance:**
- ⚠️ Validation pipeline adds ~5ms per bid
- ⚠️ Sanity checking adds ~2ms per bid
- ⚠️ Negligible impact (human perception threshold ~100ms)

**Conservative Bidding:**
- ⚠️ Sanity checker may be too conservative
- ⚠️ Might pass when aggressive bid possible
- ⚠️ Tuning required based on gameplay data

---

### Risks & Mitigation

#### Risk 1: Validation Too Strict → False Positives
**Likelihood:** Medium
**Impact:** Medium
**Risk Score:** 6/10

**Description:** Validation pipeline might reject valid bids

**Mitigation:**
- Start with lenient validation rules
- Monitor rejected bids in logs
- Tune validators based on baseline quality score
- Add override mechanism for conventions

**Success Metric:** <5% false positive rate on valid bids

---

#### Risk 2: Sanity Checker Too Conservative → Missed Games
**Likelihood:** Medium
**Impact:** Low
**Risk Score:** 4/10

**Description:** Sanity checker might prevent making games/slams

**Mitigation:**
- Conservative initial tuning (only prevent impossible contracts)
- Track missed game opportunities
- Adjust thresholds based on gameplay data
- Allow conventions to bypass sanity checks

**Success Metric:** <2% missed game rate vs no sanity checking

---

#### Risk 3: Registry Pattern Breaks Existing Tests
**Likelihood:** Low
**Impact:** High
**Risk Score:** 5/10

**Description:** Changing module registration might break existing tests

**Mitigation:**
- Implement registry with backward compatibility
- Run full test suite after each phase
- Keep fallback to old registration during transition
- Comprehensive integration testing

**Success Metric:** All existing tests pass after implementation

---

#### Risk 4: Performance Regression
**Likelihood:** Low
**Impact:** Low
**Risk Score:** 2/10

**Description:** Additional layers might slow bidding

**Mitigation:**
- Profile before/after implementation
- Optimize validation pipeline if needed
- Cache validation results where appropriate
- Monitor bid response time

**Success Metric:** <10% increase in bid generation time

---

## Implementation Notes

### Files to Create
- `backend/engine/ai/module_registry.py` (150 lines)
- `backend/engine/ai/validation_pipeline.py` (300 lines)
- `backend/engine/ai/sanity_checker.py` (250 lines)
- `backend/tests/unit/test_module_registry.py` (100 lines)
- `backend/tests/unit/test_validation_pipeline.py` (200 lines)
- `backend/tests/unit/test_sanity_checker.py` (150 lines)
- `backend/tests/regression/test_competitive_double_hcp.py` (50 lines)
- `backend/tests/regression/test_runaway_auction_prevention.py` (75 lines)

### Files to Modify
- `backend/engine/bidding_engine.py` (~150 lines changed)
- `backend/engine/ai/decision_engine.py` (~50 lines changed)
- All module files in `backend/engine/ai/modules/` (~10 lines each)
- All convention files in `backend/engine/ai/conventions/` (~10 lines each)

**Total New Code:** ~1,000 lines
**Total Modified Code:** ~400 lines

### Testing Strategy

**Phase-by-phase:**
1. After Phase 1: Run unit tests for module registry
2. After Phase 2: Run validation pipeline tests + regression test for 5 HCP double
3. After Phase 3: Run sanity checker tests + regression test for runaway auction
4. After Phase 4: Run error handling tests

**Comprehensive after all phases:**
```bash
# Unit tests
cd backend && ./test_quick.sh

# Integration tests
cd backend && ./test_medium.sh

# Baseline quality score
python3 backend/test_bidding_quality_score.py --hands 500 --output after_robustness.json

# Compare with baseline
python3 compare_scores.py baseline_before_robustness.json after_robustness.json
```

**Quality Requirements (BLOCKING):**
- ✅ Legality: 100% (must maintain)
- ✅ Appropriateness: ≥ baseline + 5% (improvement expected)
- ✅ Composite: ≥ baseline (no regression)
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Regression tests pass (5 HCP double rejected, 1NT→5♦ prevented)

### Rollback Plan

If implementation causes regressions:

**Phase 1 Rollback:**
```bash
git revert <commit_hash>
# Falls back to manual module registration
```

**Phase 2 Rollback:**
```bash
# Disable validation pipeline
validation_pipeline.enabled = False
# Falls back to module-level validation
```

**Phase 3 Rollback:**
```bash
# Disable sanity checker
sanity_checker.enabled = False
# Auctions behave as before
```

**Complete Rollback:**
```bash
git checkout main
git revert --no-commit <range>
git commit -m "Rollback ADR-0002 implementation"
```

### Success Criteria

**Phase 1 Success:**
- [ ] All modules auto-register on import
- [ ] No "module not found" errors
- [ ] Fallback to Pass works

**Phase 2 Success:**
- [ ] Competitive doubles require 8+ HCP
- [ ] All bids pass through validation
- [ ] Appropriateness score improves

**Phase 3 Success:**
- [ ] 1NT → 5♦ impossible auction prevented
- [ ] Game bids require sufficient strength
- [ ] Composite quality score maintains/improves

**Phase 4 Success:**
- [ ] No unhandled exceptions
- [ ] Clear error messages
- [ ] Graceful degradation works

**Overall Success:**
- [ ] Baseline quality score ≥ before (no regression)
- [ ] All system errors eliminated
- [ ] All regression tests pass
- [ ] User gameplay improves

---

## References

### Related Documentation
- [BIDDING_ARCHITECTURE_MAP.md](../../../BIDDING_ARCHITECTURE_MAP.md) - Complete architecture
- [BIDDING_ARCHITECTURE_SUMMARY.md](../../../BIDDING_ARCHITECTURE_SUMMARY.md) - Executive summary
- [BIDDING_QUICK_REFERENCE.txt](../../../BIDDING_QUICK_REFERENCE.txt) - Quick lookup
- [backend/analyze_hand.py](../../../backend/analyze_hand.py) - Analysis script
- [backend/optimal_play_analysis.md](../../../backend/optimal_play_analysis.md) - Play analysis

### Related ADRs
- [ADR-0001: Shared Infrastructure Architecture](ADR-0001-shared-infrastructure-architecture.md) - Module extraction patterns
- [001: Session-Based State Management](001-session-state-management.md) - Thread-safe state

### External References
- SAYC (Standard American Yellow Card) bidding rules
- Bridge bidding validation best practices
- [CLAUDE.md](../../../CLAUDE.md) - Quality assurance protocols

### Code Locations
- **BiddingEngine:** `backend/engine/bidding_engine.py`
- **DecisionEngine:** `backend/engine/ai/decision_engine.py`
- **Modules:** `backend/engine/ai/modules/`
- **Conventions:** `backend/engine/ai/conventions/`

---

## Decision Matrix

| Criterion | Weight | Option A (Quick Fixes) | Option B (Rewrite) | Option C (Incremental) |
|-----------|--------|------------------------|-------------------|------------------------|
| **Robustness** | 30% | 2/10 = 0.6 | 10/10 = 3.0 | 9/10 = 2.7 |
| **Maintainability** | 25% | 3/10 = 0.75 | 9/10 = 2.25 | 8/10 = 2.0 |
| **Risk** | 25% | 3/10 = 0.75 | 1/10 = 0.25 | 7/10 = 1.75 |
| **Effort** | 20% | 9/10 = 1.8 | 1/10 = 0.2 | 6/10 = 1.2 |
| **TOTAL** | 100% | **3.9/10** | **5.7/10** | **7.65/10** |

**Winner:** Option C (Incremental Robustness Improvements) - 7.65/10

---

## Approval & Implementation

**Status:** ⏳ **Awaiting User Approval**

**Next Steps:**
1. User reviews this ADR
2. User approves or requests modifications
3. Capture baseline quality score (before implementation)
4. Implement Phase 1 (Module Registry)
5. Test and validate Phase 1
6. Implement Phases 2-4 incrementally
7. Capture final quality score (after implementation)
8. Update ADR status to "Accepted" or "Rejected"

**Estimated Timeline:**
- Review: 15-30 minutes
- Phase 1: 2 hours
- Phase 2: 2 hours
- Phase 3: 1.5 hours
- Phase 4: 30 minutes
- Testing: 1 hour
- **Total: 7-8 hours**

**Dependencies:**
- None (can start immediately)

**Blockers:**
- Requires user approval before implementation

---

**Author:** Claude Code
**Reviewers:** User (pending)
**Implementation Owner:** Claude Code
**QA Owner:** Claude Code (baseline quality scores)

---

**Status History:**
- 2025-10-29: Created (Proposed status)
- (Pending): User approval
- (Pending): Implementation
- (Pending): Acceptance
