"""
SAYC Test Generator Integration Tests

Uses sayc_test_generator.py to generate hands for each SAYC rule and validates
that the bidding engine produces the expected bid.

This test:
1. Generates random hands that satisfy each rule's requirements
2. Runs the bidding engine on each hand
3. Verifies the expected bid is produced
4. Reports pass/fail rate per rule

Run with: pytest tests/acbl_sayc/test_generated_hands.py -v
"""
import pytest
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sayc_test_generator import SAYCTestGenerator, SAYC_OPENING_RULES, SAYC_RESPONSE_RULES
from engine.bidding_engine import BiddingEngine


# =============================================================================
# Test Configuration
# =============================================================================

# Number of hands to generate per rule
HANDS_PER_RULE = 5

# Acceptable pass rate threshold (0.0 to 1.0)
MIN_PASS_RATE = 0.6  # At least 60% of hands should match


# =============================================================================
# Test Helpers
# =============================================================================

def run_bid_test(hand, expected_bid: str, auction_context: List[str] = None) -> Tuple[bool, str, str]:
    """Test a single hand against the expected bid.

    Returns: (passed, actual_bid, explanation)
    """
    engine = BiddingEngine()

    # Build auction history
    auction_history = []
    if auction_context:
        for bid in auction_context:
            auction_history.append({"bid": bid})

    try:
        result = engine.get_next_bid(
            hand=hand,
            auction_history=auction_history,
            my_position="South",
            vulnerability="None",
            dealer="North" if auction_context else "South"
        )
        actual_bid = result[0]
        explanation = result[1] if len(result) > 1 else ""

        # Check if bid matches
        passed = actual_bid == expected_bid

        return passed, actual_bid, explanation

    except Exception as e:
        return False, "ERROR", str(e)


# =============================================================================
# Opening Bid Tests
# =============================================================================

class TestGeneratedOpeningBids:
    """Test opening bids using generated hands."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the test generator."""
        self.generator = SAYCTestGenerator()

    @pytest.mark.parametrize("rule", SAYC_OPENING_RULES, ids=lambda r: r.name)
    def test_opening_rule(self, rule):
        """Test that generated hands for each opening rule produce the expected bid."""
        passed_count = 0
        failed_hands = []

        for i in range(HANDS_PER_RULE):
            # Generate a hand matching this rule
            hand = self.generator.generate_hand_for_rule(rule, seed=42 + i)

            if hand is None:
                # Skip if generator couldn't create a valid hand
                continue

            # Verify the hand meets rule requirements
            if not self.generator._hand_satisfies_rule(hand, rule):
                continue

            # Test the bid
            passed, actual_bid, explanation = run_bid_test(hand, rule.expected_bid)

            if passed:
                passed_count += 1
            else:
                failed_hands.append({
                    'hcp': hand.hcp,
                    'expected': rule.expected_bid,
                    'actual': actual_bid,
                    'shape': f"{hand.suit_lengths}"
                })

        # Calculate pass rate
        total_tested = passed_count + len(failed_hands)
        if total_tested == 0:
            pytest.skip(f"Could not generate valid hands for rule {rule.name}")

        pass_rate = passed_count / total_tested

        # Report failures
        if failed_hands:
            failure_msg = f"\nRule: {rule.name} (expected: {rule.expected_bid})\n"
            failure_msg += f"Pass rate: {pass_rate:.0%} ({passed_count}/{total_tested})\n"
            failure_msg += "Failed hands:\n"
            for fh in failed_hands[:3]:  # Show first 3 failures
                failure_msg += f"  HCP={fh['hcp']}, got {fh['actual']}, shape={fh['shape']}\n"

            # Only fail if pass rate is below threshold
            if pass_rate < MIN_PASS_RATE:
                pytest.fail(failure_msg)
            else:
                # Warn but don't fail
                print(failure_msg)


class TestGeneratedResponses:
    """Test response bids using generated hands."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the test generator."""
        self.generator = SAYCTestGenerator()

    @pytest.mark.parametrize("rule", SAYC_RESPONSE_RULES, ids=lambda r: r.name)
    def test_response_rule(self, rule):
        """Test that generated hands for response rules produce the expected bid."""
        if not rule.auction_context:
            pytest.skip(f"Rule {rule.name} has no auction context")

        passed_count = 0
        failed_hands = []

        for i in range(HANDS_PER_RULE):
            # Generate a hand matching this rule
            hand = self.generator.generate_hand_for_rule(rule, seed=100 + i)

            if hand is None:
                continue

            if not self.generator._hand_satisfies_rule(hand, rule):
                continue

            # Test the bid with auction context
            passed, actual_bid, explanation = run_bid_test(
                hand,
                rule.expected_bid,
                auction_context=rule.auction_context
            )

            if passed:
                passed_count += 1
            else:
                failed_hands.append({
                    'hcp': hand.hcp,
                    'expected': rule.expected_bid,
                    'actual': actual_bid,
                    'auction': rule.auction_context
                })

        total_tested = passed_count + len(failed_hands)
        if total_tested == 0:
            pytest.skip(f"Could not generate valid hands for rule {rule.name}")

        pass_rate = passed_count / total_tested

        if pass_rate < MIN_PASS_RATE:
            failure_msg = f"\nRule: {rule.name}\n"
            failure_msg += f"Pass rate: {pass_rate:.0%} ({passed_count}/{total_tested})\n"
            failure_msg += f"Auction context: {rule.auction_context}\n"
            pytest.fail(failure_msg)


# =============================================================================
# Comprehensive Coverage Test
# =============================================================================

class TestOverallCoverage:
    """Test overall coverage of SAYC rules."""

    def test_opening_rules_coverage_summary(self):
        """Generate a summary of opening rule test coverage."""
        generator = SAYCTestGenerator()

        results = []
        for rule in SAYC_OPENING_RULES:
            passed = 0
            tested = 0

            for i in range(HANDS_PER_RULE):
                hand = generator.generate_hand_for_rule(rule, seed=200 + i)
                if hand is None:
                    continue
                if not generator._hand_satisfies_rule(hand, rule):
                    continue

                tested += 1
                success, actual, _ = run_bid_test(hand, rule.expected_bid)
                if success:
                    passed += 1

            if tested > 0:
                results.append({
                    'rule': rule.name,
                    'expected': rule.expected_bid,
                    'pass_rate': passed / tested,
                    'passed': passed,
                    'tested': tested
                })

        # Print summary
        print("\n" + "="*70)
        print("OPENING RULES COVERAGE SUMMARY")
        print("="*70)
        print(f"{'Rule':<30} {'Expected':<10} {'Pass Rate':<15} {'P/T':<10}")
        print("-"*70)

        total_passed = 0
        total_tested = 0

        for r in sorted(results, key=lambda x: x['pass_rate']):
            rate_str = f"{r['pass_rate']:.0%}"
            status = "OK" if r['pass_rate'] >= MIN_PASS_RATE else "LOW"
            print(f"{r['rule']:<30} {r['expected']:<10} {rate_str:<15} {r['passed']}/{r['tested']} {status}")
            total_passed += r['passed']
            total_tested += r['tested']

        print("-"*70)
        overall_rate = total_passed / total_tested if total_tested > 0 else 0
        print(f"{'OVERALL':<30} {'':<10} {overall_rate:.0%:<15} {total_passed}/{total_tested}")
        print("="*70)

        # Test passes if overall rate is acceptable
        assert overall_rate >= MIN_PASS_RATE, f"Overall pass rate {overall_rate:.0%} below threshold {MIN_PASS_RATE:.0%}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
