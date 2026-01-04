#!/usr/bin/env python3
"""
V2 Schema Engine Baseline Compliance Test Runner

Compares the V2 Schema-Driven bidding engine against the saycbridge baseline
to measure SAYC compliance and track improvement progress.

This is the primary test runner for systematic QA of the V2 Schema approach.

Usage:
    # Run all tests with V2 engine
    python3 test_baseline_v2.py

    # Run specific category
    python3 test_baseline_v2.py --category invitational_rebid_by_opener

    # Quick test (first 50)
    python3 test_baseline_v2.py --quick

    # Export results to JSON
    python3 test_baseline_v2.py --output results_v2.json

    # Show verbose output for analysis
    python3 test_baseline_v2.py --verbose
"""

import sys
import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.hand import Hand, Card
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from tests.sayc_baseline.sayc_baseline_parser import (
    SAYCBaselineParser,
    BaselineTestCase,
    parse_baseline
)


@dataclass
class V2ComplianceResult:
    """Result of comparing V2 Schema bid to expected."""
    test_id: str
    category: str
    hand: str
    history: List[str]
    expected_bid: str
    our_bid: str
    matched_expected: bool
    our_explanation: str
    rule_id: Optional[str] = None
    rule_priority: Optional[int] = None
    used_v1_fallback: bool = False
    error_message: Optional[str] = None


@dataclass
class CategoryAnalysis:
    """Detailed analysis of a single category."""
    category: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    v1_fallback_count: int
    schema_hit_count: int
    failures: List[V2ComplianceResult] = field(default_factory=list)
    common_failure_patterns: Dict[str, int] = field(default_factory=dict)


class V2BaselineComplianceRunner:
    """
    Runs V2 Schema bidding engine against the saycbridge baseline.

    This provides systematic testing to track V2 Schema improvement
    as we add more rules to the JSON schema files.
    """

    def __init__(self, verbose: bool = False):
        self.engine = BiddingEngineV2Schema(use_v1_fallback=True)
        self.results: List[V2ComplianceResult] = []
        self.category_stats: Dict[str, Dict] = {}
        self.verbose = verbose

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
                    elif card_char in ['A', 'K', 'Q', 'J']:
                        rank = card_char
                    else:
                        rank = card_char

                    cards.append(Card(rank, suit_symbols[i]))

            return Hand(cards)
        except Exception as e:
            if self.verbose:
                print(f"Error converting hand {hand_str}: {e}")
            return None

    def determine_position(self, history: List[str]) -> str:
        """Determine which position we're bidding from based on history length."""
        positions = ['North', 'East', 'South', 'West']
        return positions[len(history) % 4]

    def run_single_test(self, test_case: BaselineTestCase) -> V2ComplianceResult:
        """
        Run a single test case with V2 Schema engine.

        Args:
            test_case: BaselineTestCase from parser

        Returns:
            V2ComplianceResult with comparison
        """
        # Convert hand
        hand = self.convert_hand_to_our_format(test_case.hand)
        if hand is None:
            return V2ComplianceResult(
                test_id=test_case.test_id,
                category=test_case.category,
                hand=test_case.hand,
                history=test_case.history,
                expected_bid=test_case.expected_bid,
                our_bid="ERROR",
                matched_expected=False,
                our_explanation="",
                error_message="Failed to parse hand"
            )

        # Reset engine state for new deal
        self.engine.new_deal()

        # Determine position
        position = self.determine_position(test_case.history)

        # Track V1 fallback usage before this bid
        fallback_before = self.engine._v1_fallback_count

        # Get our bid using V2 Schema engine
        try:
            our_bid, explanation = self.engine.get_next_bid(
                hand=hand,
                auction_history=test_case.history,
                my_position=position,
                vulnerability='None',
                dealer='North'
            )
        except Exception as e:
            return V2ComplianceResult(
                test_id=test_case.test_id,
                category=test_case.category,
                hand=test_case.hand,
                history=test_case.history,
                expected_bid=test_case.expected_bid,
                our_bid="ERROR",
                matched_expected=False,
                our_explanation="",
                error_message=str(e)
            )

        # Check if V1 fallback was used
        used_v1_fallback = self.engine._v1_fallback_count > fallback_before

        # Get rule info if available (from schema engine)
        rule_id = None
        rule_priority = None
        if not used_v1_fallback:
            # Try to get the matching rule details
            candidates = self.engine.get_bid_candidates(
                hand, test_case.history, position, 'None', 'North'
            )
            if candidates:
                rule_id = candidates[0].rule_id
                rule_priority = candidates[0].priority

        # Compare results
        matched_expected = self._bids_match(our_bid, test_case.expected_bid)

        return V2ComplianceResult(
            test_id=test_case.test_id,
            category=test_case.category,
            hand=test_case.hand,
            history=test_case.history,
            expected_bid=test_case.expected_bid,
            our_bid=our_bid,
            matched_expected=matched_expected,
            our_explanation=explanation,
            rule_id=rule_id,
            rule_priority=rule_priority,
            used_v1_fallback=used_v1_fallback
        )

    def _bids_match(self, bid1: str, bid2: str) -> bool:
        """Check if two bids match (handling notation differences)."""
        if bid1 is None or bid2 is None:
            return False
        b1 = self._normalize_bid(bid1)
        b2 = self._normalize_bid(bid2)
        return b1 == b2

    def _normalize_bid(self, bid: str) -> str:
        """Normalize bid notation for comparison."""
        if bid is None:
            return ""
        if bid.lower() in ['pass', 'p']:
            return 'Pass'
        if bid.upper() == 'X':
            return 'X'
        if bid.upper() == 'XX':
            return 'XX'
        bid = bid.replace('♠', 'S').replace('♥', 'H').replace('♦', 'D').replace('♣', 'C')
        bid = bid.replace('NT', 'N')
        return bid.upper()

    def run_all_tests(
        self,
        test_cases: List[BaselineTestCase],
        limit: Optional[int] = None
    ) -> Dict:
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
        v1_fallbacks = 0
        schema_hits = 0
        errors = 0

        print(f"\n{'='*60}")
        print(f"Running {total} V2 Schema baseline compliance tests...")
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

            if result.used_v1_fallback:
                v1_fallbacks += 1
            else:
                schema_hits += 1

            # Update category stats
            cat = result.category
            if cat not in self.category_stats:
                self.category_stats[cat] = {
                    'total': 0,
                    'matched_expected': 0,
                    'v1_fallbacks': 0,
                    'schema_hits': 0,
                    'errors': 0
                }
            self.category_stats[cat]['total'] += 1
            if result.matched_expected:
                self.category_stats[cat]['matched_expected'] += 1
            if result.used_v1_fallback:
                self.category_stats[cat]['v1_fallbacks'] += 1
            else:
                self.category_stats[cat]['schema_hits'] += 1
            if result.error_message:
                self.category_stats[cat]['errors'] += 1

        return {
            'total': total,
            'matched_expected': matched_expected,
            'v1_fallbacks': v1_fallbacks,
            'schema_hits': schema_hits,
            'errors': errors,
            'compliance_rate': matched_expected / total if total > 0 else 0,
            'schema_coverage': schema_hits / total if total > 0 else 0,
            'category_stats': self.category_stats
        }

    def run_category(
        self,
        test_cases: List[BaselineTestCase],
        category: str
    ) -> Dict:
        """Run tests for a specific category."""
        filtered = [tc for tc in test_cases if tc.category == category]
        return self.run_all_tests(filtered)

    def analyze_category(self, category: str) -> CategoryAnalysis:
        """
        Detailed analysis of a category for improvement prioritization.

        Args:
            category: Category name to analyze

        Returns:
            CategoryAnalysis with detailed breakdown
        """
        cat_results = [r for r in self.results if r.category == category]

        failures = [r for r in cat_results if not r.matched_expected and not r.error_message]

        # Analyze failure patterns
        patterns = {}
        for f in failures:
            # Pattern: expected_bid -> our_bid
            pattern = f"{f.expected_bid} → {f.our_bid}"
            patterns[pattern] = patterns.get(pattern, 0) + 1

        return CategoryAnalysis(
            category=category,
            total_tests=len(cat_results),
            passed=sum(1 for r in cat_results if r.matched_expected),
            failed=len(failures),
            pass_rate=sum(1 for r in cat_results if r.matched_expected) / len(cat_results) if cat_results else 0,
            v1_fallback_count=sum(1 for r in cat_results if r.used_v1_fallback),
            schema_hit_count=sum(1 for r in cat_results if not r.used_v1_fallback),
            failures=failures,
            common_failure_patterns=dict(sorted(patterns.items(), key=lambda x: -x[1])[:10])
        )

    def print_summary(self, summary: Dict):
        """Print summary of results."""
        print(f"\n{'='*60}")
        print("V2 SCHEMA BASELINE COMPLIANCE SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests run: {summary['total']}")
        print(f"Matched SAYC expected: {summary['matched_expected']} ({summary['compliance_rate']*100:.1f}%)")
        print(f"Schema engine hits: {summary['schema_hits']} ({summary['schema_coverage']*100:.1f}%)")
        print(f"V1 fallbacks: {summary['v1_fallbacks']}")
        print(f"Errors: {summary['errors']}")
        print()

        # Category breakdown
        print("Category Breakdown (sorted by priority for V2 improvement):")
        print("-" * 60)

        # Sort by: 1) Most failures, 2) Lowest schema coverage
        sorted_cats = sorted(
            summary['category_stats'].items(),
            key=lambda x: (-(x[1]['total'] - x[1]['matched_expected']), x[1]['schema_hits'] / max(1, x[1]['total']))
        )

        for cat, stats in sorted_cats:
            rate = stats['matched_expected'] / stats['total'] * 100 if stats['total'] > 0 else 0
            schema_rate = stats['schema_hits'] / stats['total'] * 100 if stats['total'] > 0 else 0
            status = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
            print(f"  {status} {cat}:")
            print(f"      Compliance: {stats['matched_expected']}/{stats['total']} ({rate:.0f}%)")
            print(f"      Schema coverage: {stats['schema_hits']}/{stats['total']} ({schema_rate:.0f}%)")

    def print_failures(self, limit: int = 20, category: Optional[str] = None):
        """Print sample failures for analysis."""
        failures = [
            r for r in self.results
            if not r.matched_expected and not r.error_message
            and (category is None or r.category == category)
        ]

        print(f"\n{'='*60}")
        title = f"FAILURES FOR {category}" if category else "SAMPLE FAILURES"
        print(f"{title} (showing {min(limit, len(failures))} of {len(failures)})")
        print(f"{'='*60}")

        for i, result in enumerate(failures[:limit]):
            print(f"\n{i+1}. {result.test_id}")
            print(f"   Category: {result.category}")
            print(f"   Hand: {result.hand}")
            print(f"   History: {' -> '.join(result.history) if result.history else 'Opening'}")
            print(f"   Expected: {result.expected_bid}")
            print(f"   Our bid: {result.our_bid}")
            print(f"   V1 Fallback: {'Yes' if result.used_v1_fallback else 'No'}")
            print(f"   Rule ID: {result.rule_id or 'N/A'}")
            print(f"   Explanation: {result.our_explanation[:80]}...")

    def export_results(self, filepath: str):
        """Export results to JSON."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'engine': 'V2 Schema',
            'summary': {
                'total': len(self.results),
                'matched_expected': sum(1 for r in self.results if r.matched_expected),
                'v1_fallbacks': sum(1 for r in self.results if r.used_v1_fallback),
                'schema_hits': sum(1 for r in self.results if not r.used_v1_fallback),
                'errors': sum(1 for r in self.results if r.error_message),
                'compliance_rate': sum(1 for r in self.results if r.matched_expected) / max(1, len(self.results))
            },
            'category_stats': self.category_stats,
            'results': [asdict(r) for r in self.results]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nResults exported to: {filepath}")

    def get_priority_categories(self) -> List[Tuple[str, CategoryAnalysis]]:
        """
        Get categories sorted by improvement priority.

        Priority is based on:
        1. Categories with most impact (high failure count)
        2. Categories with low schema coverage (need more rules)
        3. Categories with specific rebid patterns (opener rebids first)

        Returns:
            List of (category_name, analysis) tuples sorted by priority
        """
        analyses = []
        for cat in self.category_stats.keys():
            analysis = self.analyze_category(cat)
            analyses.append((cat, analysis))

        # Sort by improvement potential
        # Priority: High failures + Low schema coverage + Rebid categories first
        def priority_score(item):
            cat, analysis = item
            failures = analysis.total_tests - analysis.passed
            schema_rate = analysis.schema_hit_count / max(1, analysis.total_tests)

            # Boost opener rebid categories
            rebid_boost = 100 if 'rebid' in cat.lower() and 'opener' in cat.lower() else 0

            return -(failures * (1 - schema_rate) + rebid_boost)

        return sorted(analyses, key=priority_score)


def main():
    parser = argparse.ArgumentParser(description='V2 Schema Baseline Compliance Test')
    parser.add_argument('--category', type=str, help='Test specific category')
    parser.add_argument('--quick', action='store_true', help='Quick test (first 50)')
    parser.add_argument('--limit', type=int, help='Limit number of tests')
    parser.add_argument('--output', type=str, help='Output JSON file')
    parser.add_argument('--failures', type=int, default=20, help='Number of failures to show')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--analyze', action='store_true', help='Show priority analysis')

    args = parser.parse_args()

    # Parse baseline
    print("Parsing saycbridge baseline...")
    baseline_parser, failed_tests = parse_baseline()

    if not failed_tests:
        print("No test cases found. Make sure z3b_baseline.txt exists.")
        return 1

    print(f"Found {len(failed_tests)} failed test cases from saycbridge baseline")

    # Create V2 runner
    runner = V2BaselineComplianceRunner(verbose=args.verbose)

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
    runner.print_failures(limit=args.failures, category=args.category)

    # Priority analysis
    if args.analyze:
        print(f"\n{'='*60}")
        print("IMPROVEMENT PRIORITY ANALYSIS")
        print(f"{'='*60}")

        priorities = runner.get_priority_categories()
        for i, (cat, analysis) in enumerate(priorities[:5], 1):
            print(f"\n{i}. {cat}")
            print(f"   Failures: {analysis.failed}")
            print(f"   Schema coverage: {analysis.schema_hit_count}/{analysis.total_tests}")
            print(f"   Common patterns:")
            for pattern, count in list(analysis.common_failure_patterns.items())[:3]:
                print(f"     - {pattern}: {count} occurrences")

    # Export if requested
    if args.output:
        runner.export_results(args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
