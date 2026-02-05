"""
Schema Rule Conformance Tests

This test suite validates that each schema rule can be triggered by appropriate hands.
It serves as a safety net to catch:
1. Rules with impossible conditions (e.g., overly restrictive AND/OR clauses)
2. Rules that are shadowed by higher-priority rules
3. Rules with typos in condition names
4. Regressions when schema rules are modified

Run with: pytest tests/acbl_sayc/test_schema_conformance.py -v
"""
import pytest
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


# =============================================================================
# Test Data: Known Good Hands for Each Rule Category
# =============================================================================

@dataclass
class RuleTestCase:
    """A test case for a specific schema rule."""
    rule_id: str
    expected_bid: str
    hand_spec: Dict[str, str]  # spades, hearts, diamonds, clubs
    auction_context: List[str] = None
    description: str = ""

    def make_hand(self) -> Hand:
        """Create a Hand from the specification."""
        cards = []
        for suit, holding in [
            ('♠', self.hand_spec.get('spades', '')),
            ('♥', self.hand_spec.get('hearts', '')),
            ('♦', self.hand_spec.get('diamonds', '')),
            ('♣', self.hand_spec.get('clubs', ''))
        ]:
            for rank in holding:
                cards.append(Card(rank, suit))
        return Hand(cards)


# Opening bid test cases - one per major rule
OPENING_TEST_CASES = [
    RuleTestCase(
        rule_id="open_2c_strong",
        expected_bid="2♣",
        hand_spec={'spades': 'AKQJ', 'hearts': 'AK53', 'diamonds': 'KQ7', 'clubs': '64'},
        description="22 HCP balanced - must open 2♣"
    ),
    RuleTestCase(
        rule_id="open_2nt",
        expected_bid="2NT",
        hand_spec={'spades': 'AKJ2', 'hearts': 'AQ3', 'diamonds': 'KJ32', 'clubs': 'K2'},
        description="21 HCP balanced - must open 2NT"
    ),
    RuleTestCase(
        rule_id="open_1nt",
        expected_bid="1NT",
        hand_spec={'spades': 'AQ32', 'hearts': 'KJ5', 'diamonds': 'Q43', 'clubs': 'K32'},
        description="15 HCP balanced - must open 1NT"
    ),
    RuleTestCase(
        rule_id="open_1_spades",
        expected_bid="1♠",
        hand_spec={'spades': 'AKJ32', 'hearts': 'Q32', 'diamonds': 'K32', 'clubs': '32'},
        description="13 HCP with 5 spades - must open 1♠"
    ),
    RuleTestCase(
        rule_id="open_1_hearts",
        expected_bid="1♥",
        hand_spec={'spades': 'Q32', 'hearts': 'AKJ32', 'diamonds': 'K32', 'clubs': '32'},
        description="13 HCP with 5 hearts - must open 1♥"
    ),
    RuleTestCase(
        rule_id="open_1_diamonds",
        expected_bid="1♦",
        hand_spec={'spades': 'K32', 'hearts': 'Q32', 'diamonds': 'AKJ32', 'clubs': '32'},
        description="13 HCP with 5 diamonds - must open 1♦"
    ),
    RuleTestCase(
        rule_id="open_1_clubs",
        expected_bid="1♣",
        hand_spec={'spades': 'K32', 'hearts': 'Q32', 'diamonds': '32', 'clubs': 'AKJ32'},
        description="13 HCP with 5 clubs - must open 1♣"
    ),
]

PREEMPT_TEST_CASES = [
    RuleTestCase(
        rule_id="weak_2_hearts",
        expected_bid="2♥",
        hand_spec={'spades': '32', 'hearts': 'KQJ932', 'diamonds': 'J32', 'clubs': '32'},
        description="7 HCP with 6 hearts - weak 2♥"
    ),
    RuleTestCase(
        rule_id="weak_2_spades",
        expected_bid="2♠",
        hand_spec={'spades': 'AQJ932', 'hearts': '32', 'diamonds': 'J32', 'clubs': '32'},
        description="8 HCP with 6 spades - weak 2♠"
    ),
    RuleTestCase(
        rule_id="preempt_3_hearts",
        expected_bid="3♥",
        hand_spec={'spades': '32', 'hearts': 'KQJ9432', 'diamonds': '32', 'clubs': '32'},
        description="6 HCP with 7 hearts - 3♥ preempt"
    ),
]

# =============================================================================
# Schema Loading Utilities
# =============================================================================

def get_schema_dir() -> Path:
    """Get the path to the schema directory."""
    return Path(__file__).parent.parent.parent / "engine" / "v2" / "schemas"


def load_schema(filename: str) -> Dict:
    """Load a schema file."""
    schema_path = get_schema_dir() / filename
    with open(schema_path) as f:
        return json.load(f)


def get_all_schema_rules() -> List[Tuple[str, str, Dict]]:
    """Load all rules from all schema files.

    Returns: List of (schema_name, rule_id, rule_dict) tuples
    """
    schema_dir = get_schema_dir()
    all_rules = []

    for schema_file in schema_dir.glob("sayc_*.json"):
        try:
            with open(schema_file) as f:
                schema = json.load(f)
            schema_name = schema_file.stem
            for rule in schema.get("rules", []):
                all_rules.append((schema_name, rule["id"], rule))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load {schema_file}: {e}")

    return all_rules


# =============================================================================
# Bidding Engine Helpers
# =============================================================================

def get_bid(hand: Hand, auction: List[str] = None, dealer: str = "South") -> Tuple[str, str]:
    """Get bid from the bidding engine."""
    engine = BiddingEngine()
    auction = auction or []
    result = engine.get_next_bid(
        hand=hand,
        auction_history=[{"bid": b} for b in auction] if auction else [],
        my_position="South",
        vulnerability="None",
        dealer=dealer
    )
    return result[0], result[1] if len(result) > 1 else ""


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestSchemaIntegrity:
    """Test that all schema files are valid and loadable."""

    def test_all_schemas_load(self):
        """All schema files should load without errors."""
        schema_dir = get_schema_dir()
        errors = []

        for schema_file in schema_dir.glob("sayc_*.json"):
            try:
                with open(schema_file) as f:
                    schema = json.load(f)
                assert "rules" in schema, f"{schema_file.name} missing 'rules' key"
            except Exception as e:
                errors.append(f"{schema_file.name}: {e}")

        assert not errors, f"Schema loading errors:\n" + "\n".join(errors)

    def test_all_rules_have_required_fields(self):
        """All rules must have id, bid, and conditions."""
        all_rules = get_all_schema_rules()
        errors = []

        for schema_name, rule_id, rule in all_rules:
            missing = []
            if "id" not in rule:
                missing.append("id")
            if "bid" not in rule:
                missing.append("bid")
            if "conditions" not in rule:
                missing.append("conditions")
            if missing:
                errors.append(f"{schema_name}/{rule_id}: missing {missing}")

        assert not errors, f"Rules with missing fields:\n" + "\n".join(errors)

    def test_no_duplicate_rule_ids(self):
        """Each rule ID should be unique within a schema."""
        schema_dir = get_schema_dir()
        errors = []

        for schema_file in schema_dir.glob("sayc_*.json"):
            with open(schema_file) as f:
                schema = json.load(f)

            rule_ids = [r["id"] for r in schema.get("rules", [])]
            seen = set()
            duplicates = []
            for rid in rule_ids:
                if rid in seen:
                    duplicates.append(rid)
                seen.add(rid)

            if duplicates:
                errors.append(f"{schema_file.name}: duplicate IDs {duplicates}")

        assert not errors, f"Duplicate rule IDs:\n" + "\n".join(errors)


class TestOpeningBidConformance:
    """Test that opening bid rules produce expected bids."""

    @pytest.mark.parametrize("test_case", OPENING_TEST_CASES, ids=lambda tc: tc.rule_id)
    def test_opening_rule(self, test_case: RuleTestCase):
        """Each opening rule should produce expected bid with matching hand."""
        hand = test_case.make_hand()
        bid, explanation = get_bid(hand)

        assert bid == test_case.expected_bid, (
            f"Rule {test_case.rule_id}: Expected {test_case.expected_bid}, got {bid}\n"
            f"Hand: {test_case.description}\n"
            f"HCP: {hand.hcp}, Balanced: {hand.is_balanced}\n"
            f"Explanation: {explanation}"
        )


class TestPreemptConformance:
    """Test that preempt rules produce expected bids."""

    @pytest.mark.parametrize("test_case", PREEMPT_TEST_CASES, ids=lambda tc: tc.rule_id)
    def test_preempt_rule(self, test_case: RuleTestCase):
        """Each preempt rule should produce expected bid with matching hand."""
        hand = test_case.make_hand()
        bid, explanation = get_bid(hand)

        assert bid == test_case.expected_bid, (
            f"Rule {test_case.rule_id}: Expected {test_case.expected_bid}, got {bid}\n"
            f"Hand: {test_case.description}\n"
            f"HCP: {hand.hcp}\n"
            f"Explanation: {explanation}"
        )


class TestCriticalBoundaryConditions:
    """Test boundary conditions that have caused bugs in production.

    Each test in this class represents a bug that was found in production.
    These tests serve as regression tests to prevent reintroduction.
    """

    def test_2c_exactly_22_hcp_no_extra_requirements(self):
        """BUG 2026-02-05: 2♣ rule required 22+ HCP AND extra conditions.

        This bug caused 22 HCP hands without 4+ quick tricks to skip 2♣.
        The rule now correctly triggers on 22+ HCP alone.
        """
        # 22 HCP balanced - should ALWAYS open 2♣
        hand = Hand([
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('5', '♥'), Card('3', '♥'),
            Card('K', '♦'), Card('Q', '♦'), Card('7', '♦'),
            Card('6', '♣'), Card('4', '♣'),
        ])
        assert hand.hcp == 22
        bid, _ = get_bid(hand)
        assert bid == "2♣", f"22 HCP must open 2♣, got {bid}"

    def test_21_hcp_does_not_open_2c(self):
        """Ensure 21 HCP doesn't incorrectly qualify for 2♣."""
        hand = Hand([
            Card('A', '♠'), Card('K', '♠'), Card('J', '♠'), Card('2', '♠'),
            Card('A', '♥'), Card('Q', '♥'), Card('3', '♥'),
            Card('K', '♦'), Card('J', '♦'), Card('3', '♦'), Card('2', '♦'),
            Card('K', '♣'), Card('2', '♣'),
        ])
        assert hand.hcp == 21
        bid, _ = get_bid(hand)
        assert bid == "2NT", f"21 HCP balanced should open 2NT, got {bid}"


# =============================================================================
# Rule Coverage Report
# =============================================================================

class TestRuleCoverageReport:
    """Generate a report of which rules have explicit test coverage."""

    def test_generate_coverage_report(self):
        """Print coverage report showing tested vs untested rules.

        This test always passes but prints useful diagnostics.
        """
        all_rules = get_all_schema_rules()

        # Collect rule IDs from test cases
        tested_rules = set()
        for tc in OPENING_TEST_CASES + PREEMPT_TEST_CASES:
            tested_rules.add(tc.rule_id)

        # Categorize rules
        opening_rules = [r for r in all_rules if r[0] == "sayc_openings"]
        preempt_rules = [r for r in all_rules if r[0] == "sayc_preempts"]

        print("\n" + "="*60)
        print("SCHEMA RULE COVERAGE REPORT")
        print("="*60)

        print(f"\nTotal schema rules: {len(all_rules)}")
        print(f"Rules with explicit test cases: {len(tested_rules)}")

        # List untested opening rules
        untested_opening = [r[1] for r in opening_rules if r[1] not in tested_rules]
        if untested_opening:
            print(f"\nUntested opening rules ({len(untested_opening)}):")
            for rule_id in untested_opening[:10]:  # Show first 10
                print(f"  - {rule_id}")
            if len(untested_opening) > 10:
                print(f"  ... and {len(untested_opening) - 10} more")

        print("\n" + "="*60)

        # This test always passes - it's for reporting
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
