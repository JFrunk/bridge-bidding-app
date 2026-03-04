---
description: Scaffold a new SAYC bidding convention
---

---
description: Scaffold a new SAYC bidding convention
---

Scaffold a new SAYC bidding convention: $ARGUMENTS

Convention name/description: $ARGUMENTS

---

## Overview

Follow the 6-step convention integration process. Run quality baselines BEFORE and AFTER.

---

## Step 1: Capture Baseline

```bash
cd backend && source venv/bin/activate
python3 test_bidding_quality_score.py --hands 100 --output convention_before.json
```

---

## Step 2: Create Convention File

Create `backend/engine/ai/conventions/<convention_name>.py` using this template:

```python
from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.ai.module_registry import ModuleRegistry
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class <ConventionName>Convention(ConventionModule):
    """<Convention description> - SAYC implementation."""

    def get_constraints(self) -> Dict:
        """Hand generation constraints for testing."""
        return {
            'hcp_range': (X, Y),
            # 'suit_length_req': (['suit1', 'suit2'], min_length, 'any_of'|'all_of')
        }

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Return (bid, explanation) if convention applies, None otherwise."""
        auction_features = features.get('auction_features', {})

        # Check preconditions
        if not self._applies(hand, features, auction_features):
            return None

        # Determine bid
        return self._make_bid(hand, features, auction_features)

    def _applies(self, hand: Hand, features: Dict, auction_features: Dict) -> bool:
        """Check whether this convention should activate."""
        # TODO: Implement precondition checks
        # - Partner's last bid?
        # - Opener relationship?
        # - HCP range?
        # - Suit lengths?
        return False

    def _make_bid(self, hand: Hand, features: Dict, auction_features: Dict) -> Tuple[str, str]:
        """Select the bid and generate explanation."""
        # TODO: Implement bid selection
        # For artificial bids, return 3-tuple with metadata:
        # return ("bid", "explanation", {'bypass_suit_length': True, 'bypass_hcp': True})
        pass


# Auto-register on import
ModuleRegistry.register('<convention_name>', <ConventionName>Convention())
```

**Reference files:**
- Base class: `backend/engine/ai/conventions/base_convention.py`
- Example (Stayman): `backend/engine/ai/conventions/stayman.py`
- Example (Jacoby): `backend/engine/ai/conventions/jacoby_transfers.py`
- Module registry: `backend/engine/ai/module_registry.py`

---

## Step 3: Register in Bidding Engine

Edit `backend/engine/bidding_engine.py`:

1. Add import at top with other convention imports:
   ```python
   from engine.ai.conventions.<convention_name> import <ConventionName>Convention
   ```

2. Add to `expected_modules` list in `BiddingEngine.__init__()`:
   ```python
   expected_modules = [
       # ... existing modules ...
       '<convention_name>',
   ]
   ```

---

## Step 4: Add Routing in Decision Engine

Edit `backend/engine/ai/decision_engine.py` `select_bidding_module()`:

- Determine where in the priority order this convention belongs
- Opening situation: Preempts -> Opening Bids
- Competitive: Michaels -> Unusual 2NT -> Overcalls -> Takeout Doubles
- Partnership: Conventions (Stayman, Jacoby, Blackwood, ...) -> Natural responses/rebids

Add the routing check at the appropriate priority level:
```python
convention = <ConventionName>Convention()
if convention.evaluate(features['hand'], features):
    return '<convention_name>'
```

---

## Step 5: Create Tests

Create `backend/tests/unit/test_<convention_name>.py`:

```python
import pytest
from engine.hand import Hand
from engine.ai.conventions.<convention_name> import <ConventionName>Convention


class Test<ConventionName>Convention:
    def setup_method(self):
        self.convention = <ConventionName>Convention()

    def test_applies_when_conditions_met(self):
        """Convention activates with correct hand/auction state."""
        # TODO: Create hand and features that trigger the convention
        pass

    def test_does_not_apply_when_conditions_not_met(self):
        """Convention stays silent when preconditions fail."""
        # TODO: Create hand/features where convention should NOT apply
        pass

    def test_correct_bid_selected(self):
        """Correct bid and explanation returned."""
        # TODO: Verify specific bid output
        pass

    def test_hcp_boundaries(self):
        """Convention respects HCP requirements."""
        pass
```

Run tests:
```bash
cd backend && pytest tests/unit/test_<convention_name>.py -v
```

---

## Step 6: Compare Quality

```bash
cd backend && source venv/bin/activate
python3 test_bidding_quality_score.py --hands 100 --output convention_after.json
python3 ../compare_scores.py convention_before.json convention_after.json
```

**Quality gates:**
- Legality: must remain 100%
- Appropriateness: no regression > 5%
- Composite: no regression > 2%

---

## Success Criteria

- [ ] Convention file created extending `ConventionModule`
- [ ] `evaluate()` returns `(bid, explanation)` or `None`
- [ ] Registered via `ModuleRegistry.register()` at module level
- [ ] Imported in `bidding_engine.py`, added to `expected_modules`
- [ ] Routing added in `decision_engine.py` at correct priority
- [ ] Unit tests written and passing
- [ ] Quality baseline shows no regression
- [ ] Documentation in `docs/features/` if user-facing

Reference: CLAUDE.md "Adding New Conventions", .claude/SAYC_REFERENCE.md
