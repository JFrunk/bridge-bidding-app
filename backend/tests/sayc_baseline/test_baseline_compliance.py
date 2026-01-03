#!/usr/bin/env python3
"""
SAYC Baseline Compliance Test Runner

Compares our bidding engine against the saycbridge baseline
to measure SAYC compliance and identify gaps.

Usage:
    # Run all tests
    python3 test_baseline_compliance.py

    # Run specific category
    python3 test_baseline_compliance.py --category balancing

    # Quick test (first 50)
    python3 test_baseline_compliance.py --quick

    # Export results to JSON
    python3 test_baseline_compliance.py --output results.json
"""

import sys
import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from tests.sayc_baseline.sayc_baseline_parser import (
    SAYCBaselineParser,
    BaselineTestCase,
    parse_baseline
)


@dataclass
class ComplianceResult:
    """Result of comparing our bid to expected."""
    test_id: str
    category: str
    hand: str
    history: List[str]
    expected_bid: str
    our_bid: str
    saycbridge_bid: Optional[str]
    matched_expected: bool
    matched_saycbridge: bool
    our_explanation: str
    error_message: Optional[str] = None


class BaselineComplianceRunner:
    """
    Runs our bidding engine against the saycbridge baseline
    and compares results.
    """

    def __init__(self):
        self.engine = BiddingEngine()
        self.results: List[ComplianceResult] = []
        self.category_stats: Dict[str, Dict] = {}

    def convert_hand_to_our_format(self, hand_str: str) -> Optional[Hand]:
        """
        Convert saycbridge hand notation to our Hand object.

        Args:
            hand_str: "K92.QJT7.KQ4.AJ7" (S.H.D.C)

        Returns:
            Hand object or None if invalid
        """
        try:
            parts = hand_str.split('.')
            if len(parts) != 4:
                return None

            cards = []
            suit_symbols = ['♠', '♥', '♦', '♣']

            for i, suit_cards in enumerate(parts):
                for card_char in suit_cards:
                    # Convert card notation
                    if card_char == 'T':
                        rank = 'T'
                    elif card_char == 'A':
                        rank = 'A'
                    elif card_char == 'K':
                        rank = 'K'
                    elif card_char == 'Q':
                        rank = 'Q'
                    elif card_char == 'J':
                        rank = 'J'
                    else:
                        rank = card_char

                    cards.append(Card(rank, suit_symbols[i]))

            if len(cards) != 13:
                # Some hands may have voids, that's OK
                pass

            return Hand(cards)
        except Exception as e:
            print(f"Error converting hand {hand_str}: {e}")
            return None

    def determine_position(self, history: List[str]) -> str:
        """
        Determine which position we're bidding from based on history length.

        In saycbridge tests, dealer is typically North (position 0).
        Position = len(history) % 4
        0 = North, 1 = East, 2 = South, 3 = West
        """
        positions = ['North', 'East', 'South', 'West']
        return positions[len(history) % 4]

    def run_single_test(self, test_case: BaselineTestCase) -> ComplianceResult:
        """
        Run a single test case and compare results.

        Args:
            test_case: BaselineTestCase from parser

        Returns:
            ComplianceResult with comparison
        """
        # Convert hand
        hand = self.convert_hand_to_our_format(test_case.hand)
        if hand is None:
            return ComplianceResult(
                test_id=test_case.test_id,
                category=test_case.category,
                hand=test_case.hand,
                history=test_case.history,
                expected_bid=test_case.expected_bid,
                our_bid="ERROR",
                saycbridge_bid=test_case.actual_bid,
                matched_expected=False,
                matched_saycbridge=False,
                our_explanation="",
                error_message="Failed to parse hand"
            )

        # Determine position
        position = self.determine_position(test_case.history)

        # Get our bid
        try:
            our_bid, explanation = self.engine.get_next_bid(
                hand=hand,
                auction_history=test_case.history,
                my_position=position,
                vulnerability='None'  # Default vulnerability
            )
        except Exception as e:
            return ComplianceResult(
                test_id=test_case.test_id,
                category=test_case.category,
                hand=test_case.hand,
                history=test_case.history,
                expected_bid=test_case.expected_bid,
                our_bid="ERROR",
                saycbridge_bid=test_case.actual_bid,
                matched_expected=False,
                matched_saycbridge=False,
                our_explanation="",
                error_message=str(e)
            )

        # Compare results
        matched_expected = self._bids_match(our_bid, test_case.expected_bid)
        matched_saycbridge = self._bids_match(our_bid, test_case.actual_bid) if test_case.actual_bid else False

        return ComplianceResult(
            test_id=test_case.test_id,
            category=test_case.category,
            hand=test_case.hand,
            history=test_case.history,
            expected_bid=test_case.expected_bid,
            our_bid=our_bid,
            saycbridge_bid=test_case.actual_bid,
            matched_expected=matched_expected,
            matched_saycbridge=matched_saycbridge,
            our_explanation=explanation
        )

    def _bids_match(self, bid1: str, bid2: str) -> bool:
        """
        Check if two bids match (handling notation differences).
        """
        if bid1 is None or bid2 is None:
            return False

        # Normalize bids
        b1 = self._normalize_bid(bid1)
        b2 = self._normalize_bid(bid2)

        return b1 == b2

    def _normalize_bid(self, bid: str) -> str:
        """Normalize bid notation for comparison."""
        if bid is None:
            return ""

        # Handle Pass
        if bid.lower() in ['pass', 'p']:
            return 'Pass'

        # Handle doubles
        if bid.upper() == 'X':
            return 'X'
        if bid.upper() == 'XX':
            return 'XX'

        # Handle suit symbols - convert to standard
        bid = bid.replace('♠', 'S').replace('♥', 'H').replace('♦', 'D').replace('♣', 'C')
        bid = bid.replace('NT', 'N').replace('N', 'N')

        return bid.upper()

    def run_all_tests(self, test_cases: List[BaselineTestCase], limit: Optional[int] = None) -> Dict:
        """
        Run all test cases and return summary.

        Args:
            test_cases: List of test cases to run
            limit: Optional limit on number of tests

        Returns:
            Summary dict with results
        """
        if limit:
            test_cases = test_cases[:limit]

        total = len(test_cases)
        matched_expected = 0
        matched_saycbridge = 0
        errors = 0

        print(f"\n{'='*60}")
        print(f"Running {total} baseline compliance tests...")
        print(f"{'='*60}\n")

        for i, test_case in enumerate(test_cases):
            if (i + 1) % 25 == 0:
                print(f"Progress: {i+1}/{total} tests completed...")

            result = self.run_single_test(test_case)
            self.results.append(result)

            if result.error_message:
                errors += 1
            elif result.matched_expected:
                matched_expected += 1
            if result.matched_saycbridge:
                matched_saycbridge += 1

            # Update category stats
            cat = result.category
            if cat not in self.category_stats:
                self.category_stats[cat] = {
                    'total': 0,
                    'matched_expected': 0,
                    'matched_saycbridge': 0,
                    'errors': 0
                }
            self.category_stats[cat]['total'] += 1
            if result.matched_expected:
                self.category_stats[cat]['matched_expected'] += 1
            if result.matched_saycbridge:
                self.category_stats[cat]['matched_saycbridge'] += 1
            if result.error_message:
                self.category_stats[cat]['errors'] += 1

        return {
            'total': total,
            'matched_expected': matched_expected,
            'matched_saycbridge': matched_saycbridge,
            'errors': errors,
            'compliance_rate': matched_expected / total if total > 0 else 0,
            'saycbridge_agreement': matched_saycbridge / total if total > 0 else 0,
            'category_stats': self.category_stats
        }

    def run_category(self, test_cases: List[BaselineTestCase], category: str) -> Dict:
        """Run tests for a specific category."""
        filtered = [tc for tc in test_cases if tc.category == category]
        return self.run_all_tests(filtered)

    def print_summary(self, summary: Dict):
        """Print summary of results."""
        print(f"\n{'='*60}")
        print("BASELINE COMPLIANCE SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests run: {summary['total']}")
        print(f"Matched SAYC expected: {summary['matched_expected']} ({summary['compliance_rate']*100:.1f}%)")
        print(f"Matched saycbridge: {summary['matched_saycbridge']} ({summary['saycbridge_agreement']*100:.1f}%)")
        print(f"Errors: {summary['errors']}")
        print()

        # Category breakdown
        print("Category Breakdown:")
        print("-" * 60)
        sorted_cats = sorted(
            summary['category_stats'].items(),
            key=lambda x: -x[1]['total']
        )
        for cat, stats in sorted_cats:
            rate = stats['matched_expected'] / stats['total'] * 100 if stats['total'] > 0 else 0
            status = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
            print(f"  {status} {cat}: {stats['matched_expected']}/{stats['total']} ({rate:.0f}%)")

    def print_failures(self, limit: int = 20):
        """Print sample failures for analysis."""
        failures = [r for r in self.results if not r.matched_expected and not r.error_message]

        print(f"\n{'='*60}")
        print(f"SAMPLE FAILURES (showing {min(limit, len(failures))} of {len(failures)})")
        print(f"{'='*60}")

        for i, result in enumerate(failures[:limit]):
            print(f"\n{i+1}. {result.test_id}")
            print(f"   Category: {result.category}")
            print(f"   Hand: {result.hand}")
            print(f"   History: {' -> '.join(result.history) if result.history else 'Opening'}")
            print(f"   Expected: {result.expected_bid}")
            print(f"   Our bid: {result.our_bid}")
            print(f"   saycbridge: {result.saycbridge_bid}")
            print(f"   Our reason: {result.our_explanation[:80]}...")

    def export_results(self, filepath: str):
        """Export results to JSON."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': len(self.results),
                'matched_expected': sum(1 for r in self.results if r.matched_expected),
                'errors': sum(1 for r in self.results if r.error_message)
            },
            'category_stats': self.category_stats,
            'results': [asdict(r) for r in self.results]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nResults exported to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description='SAYC Baseline Compliance Test')
    parser.add_argument('--category', type=str, help='Test specific category')
    parser.add_argument('--quick', action='store_true', help='Quick test (first 50)')
    parser.add_argument('--limit', type=int, help='Limit number of tests')
    parser.add_argument('--output', type=str, help='Output JSON file')
    parser.add_argument('--failures', type=int, default=20, help='Number of failures to show')

    args = parser.parse_args()

    # Parse baseline
    print("Parsing saycbridge baseline...")
    baseline_parser, failed_tests = parse_baseline()

    if not failed_tests:
        print("No test cases found. Make sure z3b_baseline.txt exists.")
        return 1

    print(f"Found {len(failed_tests)} failed test cases from saycbridge baseline")

    # Create runner
    runner = BaselineComplianceRunner()

    # Run tests
    if args.category:
        summary = runner.run_category(failed_tests, args.category)
    elif args.quick:
        summary = runner.run_all_tests(failed_tests, limit=50)
    elif args.limit:
        summary = runner.run_all_tests(failed_tests, limit=args.limit)
    else:
        summary = runner.run_all_tests(failed_tests)

    # Print results
    runner.print_summary(summary)
    runner.print_failures(limit=args.failures)

    # Export if requested
    if args.output:
        runner.export_results(args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
