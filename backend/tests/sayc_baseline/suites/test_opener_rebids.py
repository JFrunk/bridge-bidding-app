#!/usr/bin/env python3
"""
Opener Rebids Test Suite (Priority 1)

Focused test suite for opener's rebid situations - the highest priority
category for V2 Schema improvement.

Categories covered:
- minimum_rebid_by_opener (12-14 HCP)
- invitational_rebid_by_opener (15-17 HCP)
- game_forcing_rebid_by_opener (18+ HCP)

Test structure follows the "Power Band" concept:
- MINIMUM: 12-15 HCP - Pass/simple rebid
- MEDIUM: 16-18 HCP - Invitational actions
- MAXIMUM: 19+ HCP - Game forcing

Usage:
    python3 test_opener_rebids.py                    # Run all opener rebid tests
    python3 test_opener_rebids.py --subcategory minimum  # Run minimum only
    python3 test_opener_rebids.py --verbose          # Detailed output
    python3 test_opener_rebids.py --failures-only    # Show only failures
"""

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from engine.hand import Hand, Card
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from tests.sayc_baseline.sayc_baseline_parser import parse_baseline, BaselineTestCase


# Define subcategories
OPENER_REBID_CATEGORIES = [
    'minimum_rebid_by_opener',
    'invitational_rebid_by_opener',
    'game_forcing_rebid_by_opener'
]


@dataclass
class OpenerRebidResult:
    """Result for opener rebid test."""
    test_id: str
    subcategory: str
    hand: str
    hcp: int
    history: List[str]
    expected_bid: str
    our_bid: str
    matched: bool
    rule_id: Optional[str]
    explanation: str
    power_band: str  # MINIMUM, MEDIUM, MAXIMUM
    partner_response_type: str  # raise, new_suit, 1nt, 2nt
    error: Optional[str] = None


@dataclass
class SubcategoryAnalysis:
    """Analysis of a subcategory."""
    name: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    by_power_band: Dict[str, Dict] = field(default_factory=dict)
    by_response_type: Dict[str, Dict] = field(default_factory=dict)
    failures: List[OpenerRebidResult] = field(default_factory=list)
    common_patterns: Dict[str, int] = field(default_factory=dict)


class OpenerRebidsTestSuite:
    """
    Specialized test suite for opener rebid situations.

    This is the highest priority test category because:
    1. Rebids occur in every auction where partner responds
    2. The "Power Band" concept is fundamental to SAYC
    3. Most rebid failures are systematic (missing rules)
    """

    def __init__(self, verbose: bool = False):
        self.engine = BiddingEngineV2Schema(use_v1_fallback=False)  # Pure V2 testing
        self.results: List[OpenerRebidResult] = []
        self.verbose = verbose

    def classify_power_band(self, hcp: int) -> str:
        """Classify hand into power band."""
        if hcp <= 15:
            return "MINIMUM"
        elif hcp <= 18:
            return "MEDIUM"
        else:
            return "MAXIMUM"

    def classify_partner_response(self, history: List[str]) -> str:
        """Classify partner's response type."""
        if len(history) < 2:
            return "unknown"

        # Partner's response is at index 2 (opener-0, pass-1, response-2)
        if len(history) >= 3:
            response = history[2]
        elif len(history) >= 2:
            response = history[1]
        else:
            return "unknown"

        if response == 'Pass':
            return "pass"
        elif response in ['1NT', '2NT']:
            return "nt_response"
        elif response.startswith('2') and len(history) >= 1 and history[0][1:] == response[1:]:
            return "single_raise"
        elif response.startswith('3') and len(history) >= 1 and history[0][1:] == response[1:]:
            return "limit_raise"
        elif 'NT' not in response:
            return "new_suit"
        else:
            return "other"

    def convert_hand(self, hand_str: str) -> Optional[Hand]:
        """Convert hand notation to Hand object."""
        try:
            parts = hand_str.split('.')
            if len(parts) != 4:
                return None

            cards = []
            suits = ['♠', '♥', '♦', '♣']
            for i, suit_cards in enumerate(parts):
                for card_char in suit_cards:
                    rank = 'T' if card_char == 'T' else card_char
                    cards.append(Card(rank, suits[i]))

            return Hand(cards)
        except Exception:
            return None

    def run_single_test(self, test_case: BaselineTestCase) -> OpenerRebidResult:
        """Run a single opener rebid test."""
        hand = self.convert_hand(test_case.hand)
        if hand is None:
            return OpenerRebidResult(
                test_id=test_case.test_id,
                subcategory=test_case.category,
                hand=test_case.hand,
                hcp=test_case.hcp,
                history=test_case.history,
                expected_bid=test_case.expected_bid,
                our_bid="ERROR",
                matched=False,
                rule_id=None,
                explanation="",
                power_band=self.classify_power_band(test_case.hcp),
                partner_response_type=self.classify_partner_response(test_case.history),
                error="Failed to parse hand"
            )

        # Reset engine state
        self.engine.new_deal()

        # Determine position (opener is always position 0 in these tests)
        positions = ['North', 'East', 'South', 'West']
        position = positions[len(test_case.history) % 4]

        try:
            our_bid, explanation = self.engine.get_next_bid(
                hand=hand,
                auction_history=test_case.history,
                my_position=position,
                vulnerability='None',
                dealer='North'
            )
        except Exception as e:
            return OpenerRebidResult(
                test_id=test_case.test_id,
                subcategory=test_case.category,
                hand=test_case.hand,
                hcp=test_case.hcp,
                history=test_case.history,
                expected_bid=test_case.expected_bid,
                our_bid="ERROR",
                matched=False,
                rule_id=None,
                explanation="",
                power_band=self.classify_power_band(test_case.hcp),
                partner_response_type=self.classify_partner_response(test_case.history),
                error=str(e)
            )

        # Get rule info
        candidates = self.engine.get_bid_candidates(
            hand, test_case.history, position, 'None', 'North'
        )
        rule_id = candidates[0].rule_id if candidates else None

        # Compare bids
        matched = self._bids_match(our_bid, test_case.expected_bid)

        return OpenerRebidResult(
            test_id=test_case.test_id,
            subcategory=test_case.category,
            hand=test_case.hand,
            hcp=test_case.hcp,
            history=test_case.history,
            expected_bid=test_case.expected_bid,
            our_bid=our_bid,
            matched=matched,
            rule_id=rule_id,
            explanation=explanation,
            power_band=self.classify_power_band(test_case.hcp),
            partner_response_type=self.classify_partner_response(test_case.history)
        )

    def _bids_match(self, bid1: str, bid2: str) -> bool:
        """Check if two bids match."""
        if not bid1 or not bid2:
            return False
        b1 = bid1.replace('♠', 'S').replace('♥', 'H').replace('♦', 'D').replace('♣', 'C').upper()
        b2 = bid2.replace('♠', 'S').replace('♥', 'H').replace('♦', 'D').replace('♣', 'C').upper()
        b1 = b1.replace('NT', 'N').replace('PASS', 'PASS')
        b2 = b2.replace('NT', 'N').replace('PASS', 'PASS')
        return b1 == b2

    def run_tests(
        self,
        test_cases: List[BaselineTestCase],
        subcategory: Optional[str] = None
    ) -> Dict:
        """Run opener rebid tests."""
        # Filter to opener rebid categories
        filtered = [
            tc for tc in test_cases
            if tc.category in OPENER_REBID_CATEGORIES
            and (subcategory is None or tc.category == f"{subcategory}_rebid_by_opener")
        ]

        print(f"\n{'='*60}")
        print(f"OPENER REBIDS TEST SUITE")
        print(f"Running {len(filtered)} tests...")
        print(f"{'='*60}\n")

        for i, tc in enumerate(filtered):
            if self.verbose and (i + 1) % 10 == 0:
                print(f"Progress: {i+1}/{len(filtered)}")

            result = self.run_single_test(tc)
            self.results.append(result)

        return self._generate_summary()

    def _generate_summary(self) -> Dict:
        """Generate summary of results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.matched)

        # Subcategory breakdown
        subcategory_stats = {}
        for cat in OPENER_REBID_CATEGORIES:
            cat_results = [r for r in self.results if r.subcategory == cat]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r.matched)
                subcategory_stats[cat] = {
                    'total': len(cat_results),
                    'passed': cat_passed,
                    'pass_rate': cat_passed / len(cat_results)
                }

        # Power band breakdown
        power_band_stats = {}
        for band in ['MINIMUM', 'MEDIUM', 'MAXIMUM']:
            band_results = [r for r in self.results if r.power_band == band]
            if band_results:
                band_passed = sum(1 for r in band_results if r.matched)
                power_band_stats[band] = {
                    'total': len(band_results),
                    'passed': band_passed,
                    'pass_rate': band_passed / len(band_results)
                }

        # Response type breakdown
        response_stats = {}
        for resp_type in ['single_raise', 'limit_raise', 'new_suit', 'nt_response', 'other']:
            resp_results = [r for r in self.results if r.partner_response_type == resp_type]
            if resp_results:
                resp_passed = sum(1 for r in resp_results if r.matched)
                response_stats[resp_type] = {
                    'total': len(resp_results),
                    'passed': resp_passed,
                    'pass_rate': resp_passed / len(resp_results)
                }

        return {
            'total': total,
            'passed': passed,
            'pass_rate': passed / total if total > 0 else 0,
            'subcategory_stats': subcategory_stats,
            'power_band_stats': power_band_stats,
            'response_type_stats': response_stats
        }

    def analyze_subcategory(self, subcategory: str) -> SubcategoryAnalysis:
        """Detailed analysis of a subcategory."""
        cat_results = [r for r in self.results if r.subcategory == subcategory]
        failures = [r for r in cat_results if not r.matched and not r.error]

        # Analyze by power band
        by_power_band = {}
        for band in ['MINIMUM', 'MEDIUM', 'MAXIMUM']:
            band_results = [r for r in cat_results if r.power_band == band]
            if band_results:
                by_power_band[band] = {
                    'total': len(band_results),
                    'passed': sum(1 for r in band_results if r.matched),
                    'pass_rate': sum(1 for r in band_results if r.matched) / len(band_results)
                }

        # Analyze by response type
        by_response = {}
        for resp in ['single_raise', 'limit_raise', 'new_suit', 'nt_response']:
            resp_results = [r for r in cat_results if r.partner_response_type == resp]
            if resp_results:
                by_response[resp] = {
                    'total': len(resp_results),
                    'passed': sum(1 for r in resp_results if r.matched),
                    'pass_rate': sum(1 for r in resp_results if r.matched) / len(resp_results)
                }

        # Common failure patterns
        patterns = {}
        for f in failures:
            pattern = f"{f.expected_bid} → {f.our_bid}"
            patterns[pattern] = patterns.get(pattern, 0) + 1

        return SubcategoryAnalysis(
            name=subcategory,
            total=len(cat_results),
            passed=sum(1 for r in cat_results if r.matched),
            failed=len(failures),
            pass_rate=sum(1 for r in cat_results if r.matched) / len(cat_results) if cat_results else 0,
            by_power_band=by_power_band,
            by_response_type=by_response,
            failures=failures,
            common_patterns=dict(sorted(patterns.items(), key=lambda x: -x[1])[:10])
        )

    def print_summary(self, summary: Dict):
        """Print test summary."""
        print(f"\n{'='*60}")
        print("OPENER REBIDS TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {summary['total']}")
        print(f"Passed: {summary['passed']} ({summary['pass_rate']*100:.1f}%)")

        print("\nBy Subcategory:")
        print("-" * 40)
        for cat, stats in summary['subcategory_stats'].items():
            status = "✅" if stats['pass_rate'] >= 0.8 else "⚠️" if stats['pass_rate'] >= 0.5 else "❌"
            short_name = cat.replace('_rebid_by_opener', '').replace('_', ' ').title()
            print(f"  {status} {short_name}: {stats['passed']}/{stats['total']} ({stats['pass_rate']*100:.0f}%)")

        print("\nBy Power Band:")
        print("-" * 40)
        for band, stats in summary['power_band_stats'].items():
            status = "✅" if stats['pass_rate'] >= 0.8 else "⚠️" if stats['pass_rate'] >= 0.5 else "❌"
            print(f"  {status} {band}: {stats['passed']}/{stats['total']} ({stats['pass_rate']*100:.0f}%)")

        print("\nBy Partner's Response:")
        print("-" * 40)
        for resp, stats in summary['response_type_stats'].items():
            status = "✅" if stats['pass_rate'] >= 0.8 else "⚠️" if stats['pass_rate'] >= 0.5 else "❌"
            print(f"  {status} {resp.replace('_', ' ').title()}: {stats['passed']}/{stats['total']} ({stats['pass_rate']*100:.0f}%)")

    def print_failures(self, limit: int = 20, subcategory: Optional[str] = None):
        """Print failure details."""
        failures = [
            r for r in self.results
            if not r.matched and not r.error
            and (subcategory is None or r.subcategory == subcategory)
        ]

        if not failures:
            print("\n✅ No failures!")
            return

        print(f"\n{'='*60}")
        print(f"FAILURES (showing {min(limit, len(failures))} of {len(failures)})")
        print(f"{'='*60}")

        for i, f in enumerate(failures[:limit]):
            print(f"\n{i+1}. {f.test_id}")
            print(f"   Subcategory: {f.subcategory}")
            print(f"   Hand: {f.hand} ({f.hcp} HCP - {f.power_band})")
            print(f"   History: {' -> '.join(f.history)}")
            print(f"   Partner response: {f.partner_response_type}")
            print(f"   Expected: {f.expected_bid}")
            print(f"   Got: {f.our_bid}")
            print(f"   Rule: {f.rule_id or 'N/A'}")
            print(f"   Explanation: {f.explanation[:60]}...")

    def export_results(self, filepath: str):
        """Export results to JSON."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'suite': 'opener_rebids',
            'summary': self._generate_summary(),
            'results': [asdict(r) for r in self.results]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nResults exported to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description='Opener Rebids Test Suite')
    parser.add_argument('--subcategory', choices=['minimum', 'invitational', 'game_forcing'],
                        help='Run specific subcategory')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--failures-only', action='store_true', help='Show only failures')
    parser.add_argument('--output', type=str, help='Export results to JSON')
    parser.add_argument('--limit', type=int, default=20, help='Number of failures to show')

    args = parser.parse_args()

    # Parse baseline
    print("Loading baseline test cases...")
    _, all_tests = parse_baseline()

    if not all_tests:
        print("No test cases found")
        return 1

    # Create and run test suite
    suite = OpenerRebidsTestSuite(verbose=args.verbose)
    summary = suite.run_tests(all_tests, subcategory=args.subcategory)

    # Print results
    if not args.failures_only:
        suite.print_summary(summary)

    suite.print_failures(limit=args.limit, subcategory=args.subcategory)

    # Export if requested
    if args.output:
        suite.export_results(args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
