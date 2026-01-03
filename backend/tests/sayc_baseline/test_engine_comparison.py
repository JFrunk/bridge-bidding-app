#!/usr/bin/env python3
"""
Engine Comparison Test Harness

Compares BiddingEngine V1 vs V2 against the saycbridge baseline.
This allows measuring improvement objectively before switching engines.

Usage:
    # Compare both engines against baseline
    python3 test_engine_comparison.py

    # Quick test (first 50 cases)
    python3 test_engine_comparison.py --quick

    # Test specific category
    python3 test_engine_comparison.py --category balancing

    # Export detailed results
    python3 test_engine_comparison.py --output comparison_results.json

    # Show only improvements (V2 better than V1)
    python3 test_engine_comparison.py --show-improvements

    # Show only regressions (V2 worse than V1)
    python3 test_engine_comparison.py --show-regressions
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
from engine.bidding_engine_v2 import BiddingEngineV2
from tests.sayc_baseline.sayc_baseline_parser import (
    SAYCBaselineParser,
    BaselineTestCase,
    parse_baseline
)


@dataclass
class ComparisonResult:
    """Result of comparing V1 vs V2 on a single test case."""
    test_id: str
    category: str
    hand: str
    history: List[str]
    expected_bid: str

    v1_bid: str
    v1_matched: bool
    v1_explanation: str

    v2_bid: str
    v2_matched: bool
    v2_explanation: str

    # Comparison
    same_bid: bool
    improvement: bool  # V2 matched when V1 didn't
    regression: bool   # V1 matched when V2 didn't

    error_message: Optional[str] = None


class EngineComparisonRunner:
    """
    Runs both bidding engines against the saycbridge baseline
    and compares their performance.
    """

    def __init__(self):
        self.engine_v1 = BiddingEngine()
        self.engine_v2 = BiddingEngineV2(comparison_mode=False)
        self.results: List[ComparisonResult] = []
        self.category_stats: Dict[str, Dict] = {}

    def convert_hand_to_our_format(self, hand_str: str) -> Optional[Hand]:
        """
        Convert saycbridge hand notation to our Hand object.

        Args:
            hand_str: "K92.QJT7.KQ4.AJ7" (S.H.D.C)
        """
        try:
            parts = hand_str.split('.')
            if len(parts) != 4:
                return None

            cards = []
            suit_symbols = ['♠', '♥', '♦', '♣']

            for i, suit_cards in enumerate(parts):
                for card_char in suit_cards:
                    if card_char == 'T':
                        rank = 'T'
                    else:
                        rank = card_char
                    cards.append(Card(rank, suit_symbols[i]))

            return Hand(cards)
        except Exception as e:
            print(f"Error converting hand {hand_str}: {e}")
            return None

    def determine_position(self, history: List[str]) -> str:
        """Determine position from history length."""
        positions = ['North', 'East', 'South', 'West']
        return positions[len(history) % 4]

    def normalize_bid(self, bid: str) -> str:
        """Normalize bid for comparison."""
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

    def bids_match(self, bid1: str, bid2: str) -> bool:
        """Check if two bids match."""
        return self.normalize_bid(bid1) == self.normalize_bid(bid2)

    def run_single_test(self, test_case: BaselineTestCase) -> ComparisonResult:
        """Run a single test case through both engines."""
        hand = self.convert_hand_to_our_format(test_case.hand)
        if hand is None:
            return ComparisonResult(
                test_id=test_case.test_id,
                category=test_case.category,
                hand=test_case.hand,
                history=test_case.history,
                expected_bid=test_case.expected_bid,
                v1_bid="ERROR",
                v1_matched=False,
                v1_explanation="",
                v2_bid="ERROR",
                v2_matched=False,
                v2_explanation="",
                same_bid=True,
                improvement=False,
                regression=False,
                error_message="Failed to parse hand"
            )

        position = self.determine_position(test_case.history)

        # Run V1
        try:
            v1_bid, v1_explanation = self.engine_v1.get_next_bid(
                hand=hand,
                auction_history=test_case.history,
                my_position=position,
                vulnerability='None'
            )
        except Exception as e:
            v1_bid, v1_explanation = "ERROR", str(e)

        # Run V2
        try:
            v2_bid, v2_explanation = self.engine_v2.get_next_bid(
                hand=hand,
                auction_history=test_case.history,
                my_position=position,
                vulnerability='None'
            )
        except Exception as e:
            v2_bid, v2_explanation = "ERROR", str(e)

        # Compare results
        v1_matched = self.bids_match(v1_bid, test_case.expected_bid)
        v2_matched = self.bids_match(v2_bid, test_case.expected_bid)
        same_bid = self.bids_match(v1_bid, v2_bid)
        improvement = v2_matched and not v1_matched
        regression = v1_matched and not v2_matched

        return ComparisonResult(
            test_id=test_case.test_id,
            category=test_case.category,
            hand=test_case.hand,
            history=test_case.history,
            expected_bid=test_case.expected_bid,
            v1_bid=v1_bid,
            v1_matched=v1_matched,
            v1_explanation=v1_explanation[:200] if v1_explanation else "",
            v2_bid=v2_bid,
            v2_matched=v2_matched,
            v2_explanation=v2_explanation[:200] if v2_explanation else "",
            same_bid=same_bid,
            improvement=improvement,
            regression=regression
        )

    def run_all_tests(self, test_cases: List[BaselineTestCase], limit: Optional[int] = None) -> Dict:
        """Run all test cases and return summary."""
        if limit:
            test_cases = test_cases[:limit]

        total = len(test_cases)
        v1_matched = 0
        v2_matched = 0
        same_bid = 0
        improvements = 0
        regressions = 0
        errors = 0

        print(f"\n{'='*70}")
        print(f"Running {total} baseline tests through V1 and V2 engines...")
        print(f"{'='*70}\n")

        for i, test_case in enumerate(test_cases):
            if (i + 1) % 25 == 0:
                print(f"Progress: {i+1}/{total} tests completed...")

            result = self.run_single_test(test_case)
            self.results.append(result)

            if result.error_message:
                errors += 1
            else:
                if result.v1_matched:
                    v1_matched += 1
                if result.v2_matched:
                    v2_matched += 1
                if result.same_bid:
                    same_bid += 1
                if result.improvement:
                    improvements += 1
                if result.regression:
                    regressions += 1

            # Update category stats
            cat = result.category
            if cat not in self.category_stats:
                self.category_stats[cat] = {
                    'total': 0,
                    'v1_matched': 0,
                    'v2_matched': 0,
                    'same_bid': 0,
                    'improvements': 0,
                    'regressions': 0,
                }
            self.category_stats[cat]['total'] += 1
            if result.v1_matched:
                self.category_stats[cat]['v1_matched'] += 1
            if result.v2_matched:
                self.category_stats[cat]['v2_matched'] += 1
            if result.same_bid:
                self.category_stats[cat]['same_bid'] += 1
            if result.improvement:
                self.category_stats[cat]['improvements'] += 1
            if result.regression:
                self.category_stats[cat]['regressions'] += 1

        return {
            'total': total,
            'v1_matched': v1_matched,
            'v2_matched': v2_matched,
            'same_bid': same_bid,
            'improvements': improvements,
            'regressions': regressions,
            'errors': errors,
            'v1_rate': v1_matched / total if total > 0 else 0,
            'v2_rate': v2_matched / total if total > 0 else 0,
            'agreement_rate': same_bid / total if total > 0 else 0,
            'category_stats': self.category_stats
        }

    def print_summary(self, summary: Dict):
        """Print summary of comparison."""
        print(f"\n{'='*70}")
        print("ENGINE COMPARISON SUMMARY")
        print(f"{'='*70}")
        print(f"Total tests run: {summary['total']}")
        print()
        print(f"V1 (BiddingEngine) matched expected: {summary['v1_matched']} ({summary['v1_rate']*100:.1f}%)")
        print(f"V2 (BiddingEngineV2) matched expected: {summary['v2_matched']} ({summary['v2_rate']*100:.1f}%)")
        print()
        print(f"Same bid (V1 == V2): {summary['same_bid']} ({summary['agreement_rate']*100:.1f}%)")
        print(f"Improvements (V2 ✓, V1 ✗): {summary['improvements']}")
        print(f"Regressions (V1 ✓, V2 ✗): {summary['regressions']}")
        print(f"Errors: {summary['errors']}")
        print()

        # Net improvement
        net = summary['improvements'] - summary['regressions']
        if net > 0:
            print(f"📈 NET IMPROVEMENT: +{net} cases")
        elif net < 0:
            print(f"📉 NET REGRESSION: {net} cases")
        else:
            print(f"⚖️  NO NET CHANGE")
        print()

        # Category breakdown
        print("Category Breakdown:")
        print("-" * 70)
        print(f"{'Category':<25} {'V1':>6} {'V2':>6} {'Impr':>6} {'Regr':>6}")
        print("-" * 70)

        sorted_cats = sorted(
            summary['category_stats'].items(),
            key=lambda x: -x[1]['total']
        )

        for cat, stats in sorted_cats:
            v1_pct = stats['v1_matched'] / stats['total'] * 100 if stats['total'] > 0 else 0
            v2_pct = stats['v2_matched'] / stats['total'] * 100 if stats['total'] > 0 else 0
            impr = stats['improvements']
            regr = stats['regressions']

            # Indicator
            if impr > regr:
                ind = "📈"
            elif regr > impr:
                ind = "📉"
            else:
                ind = "  "

            print(f"{ind} {cat:<23} {v1_pct:>5.0f}% {v2_pct:>5.0f}% {impr:>6} {regr:>6}")

    def print_improvements(self, limit: int = 20):
        """Print cases where V2 improved over V1."""
        improvements = [r for r in self.results if r.improvement]

        print(f"\n{'='*70}")
        print(f"IMPROVEMENTS (V2 ✓, V1 ✗) - showing {min(limit, len(improvements))} of {len(improvements)}")
        print(f"{'='*70}")

        for i, result in enumerate(improvements[:limit]):
            print(f"\n{i+1}. {result.test_id} [{result.category}]")
            print(f"   Hand: {result.hand}")
            print(f"   History: {' -> '.join(result.history) if result.history else 'Opening'}")
            print(f"   Expected: {result.expected_bid}")
            print(f"   V1: {result.v1_bid} ✗")
            print(f"   V2: {result.v2_bid} ✓")

    def print_regressions(self, limit: int = 20):
        """Print cases where V2 regressed from V1."""
        regressions = [r for r in self.results if r.regression]

        print(f"\n{'='*70}")
        print(f"REGRESSIONS (V1 ✓, V2 ✗) - showing {min(limit, len(regressions))} of {len(regressions)}")
        print(f"{'='*70}")

        for i, result in enumerate(regressions[:limit]):
            print(f"\n{i+1}. {result.test_id} [{result.category}]")
            print(f"   Hand: {result.hand}")
            print(f"   History: {' -> '.join(result.history) if result.history else 'Opening'}")
            print(f"   Expected: {result.expected_bid}")
            print(f"   V1: {result.v1_bid} ✓")
            print(f"   V2: {result.v2_bid} ✗")

    def export_results(self, filepath: str):
        """Export results to JSON."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': len(self.results),
                'v1_matched': sum(1 for r in self.results if r.v1_matched),
                'v2_matched': sum(1 for r in self.results if r.v2_matched),
                'improvements': sum(1 for r in self.results if r.improvement),
                'regressions': sum(1 for r in self.results if r.regression),
            },
            'category_stats': self.category_stats,
            'results': [asdict(r) for r in self.results]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nResults exported to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description='Engine Comparison Test')
    parser.add_argument('--category', type=str, help='Test specific category')
    parser.add_argument('--quick', action='store_true', help='Quick test (first 50)')
    parser.add_argument('--limit', type=int, help='Limit number of tests')
    parser.add_argument('--output', type=str, help='Output JSON file')
    parser.add_argument('--show-improvements', action='store_true', help='Show improvement details')
    parser.add_argument('--show-regressions', action='store_true', help='Show regression details')

    args = parser.parse_args()

    # Parse baseline
    print("Parsing saycbridge baseline...")
    baseline_parser, failed_tests = parse_baseline()

    if not failed_tests:
        print("No test cases found. Make sure z3b_baseline.txt exists.")
        return 1

    print(f"Found {len(failed_tests)} test cases from saycbridge baseline")

    # Create runner
    runner = EngineComparisonRunner()

    # Filter by category if specified
    if args.category:
        failed_tests = [tc for tc in failed_tests if tc.category == args.category]
        print(f"Filtered to {len(failed_tests)} tests in category '{args.category}'")

    # Run tests
    if args.quick:
        summary = runner.run_all_tests(failed_tests, limit=50)
    elif args.limit:
        summary = runner.run_all_tests(failed_tests, limit=args.limit)
    else:
        summary = runner.run_all_tests(failed_tests)

    # Print results
    runner.print_summary(summary)

    if args.show_improvements:
        runner.print_improvements()

    if args.show_regressions:
        runner.print_regressions()

    # Export if requested
    if args.output:
        runner.export_results(args.output)

    # Return code based on net improvement
    net = summary['improvements'] - summary['regressions']
    return 0 if net >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
