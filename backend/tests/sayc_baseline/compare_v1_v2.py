#!/usr/bin/env python3
"""
V1 vs V2 Engine Comparison

Runs both the V1 (Python module-based) and V2 (Schema-driven) bidding engines
against the saycbridge baseline and compares their performance.

Usage:
    python3 compare_v1_v2.py
    python3 compare_v1_v2.py --quick  # First 50 tests only
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine  # V1
from engine.v2 import BiddingEngineV2Schema  # V2
from tests.sayc_baseline.sayc_baseline_parser import parse_baseline


def convert_hand(hand_str: str) -> Optional[Hand]:
    """Convert saycbridge hand notation to Hand object."""
    try:
        parts = hand_str.split('.')
        if len(parts) != 4:
            return None

        cards = []
        suit_symbols = ['♠', '♥', '♦', '♣']

        for i, suit_cards in enumerate(parts):
            for card_char in suit_cards:
                cards.append(Card(card_char, suit_symbols[i]))

        return Hand(cards)
    except Exception:
        return None


def normalize_bid(bid: str) -> str:
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


def bids_match(bid1: str, bid2: str) -> bool:
    """Check if two bids match."""
    return normalize_bid(bid1) == normalize_bid(bid2)


def run_comparison(test_cases, limit: Optional[int] = None):
    """Run V1 and V2 engines against test cases and compare."""

    if limit:
        test_cases = test_cases[:limit]

    # Initialize engines
    v1_engine = BiddingEngine()
    v2_engine = BiddingEngineV2Schema()

    positions = ['North', 'East', 'South', 'West']

    # Statistics
    total = len(test_cases)
    v1_matched = 0
    v2_matched = 0
    both_matched = 0
    v1_only = 0
    v2_only = 0
    neither = 0
    v1_errors = 0
    v2_errors = 0
    v2_no_rule = 0

    # Category stats
    v1_cat_stats = {}
    v2_cat_stats = {}

    # Detailed results for analysis
    v1_wins = []  # Cases where V1 matched but V2 didn't
    v2_wins = []  # Cases where V2 matched but V1 didn't

    print("=" * 70)
    print("V1 vs V2 ENGINE COMPARISON")
    print("=" * 70)
    print(f"\nRunning {total} test cases...")

    for i, tc in enumerate(test_cases):
        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{total}...")

        hand = convert_hand(tc.hand)
        if hand is None:
            v1_errors += 1
            v2_errors += 1
            continue

        position = positions[len(tc.history) % 4]

        # Reset V2 engine for new deal
        v2_engine.new_deal()

        # Get V1 bid
        try:
            v1_bid, v1_exp = v1_engine.get_next_bid(
                hand=hand,
                auction_history=tc.history,
                my_position=position,
                vulnerability='None'
            )
        except Exception as e:
            v1_bid, v1_exp = 'ERROR', str(e)
            v1_errors += 1

        # Get V2 bid
        try:
            v2_bid, v2_exp = v2_engine.get_next_bid(
                hand=hand,
                auction_history=tc.history,
                my_position=position,
                vulnerability='None'
            )
        except Exception as e:
            v2_bid, v2_exp = 'ERROR', str(e)
            v2_errors += 1

        # Check for no rule found
        if 'No applicable bidding rule' in v2_exp:
            v2_no_rule += 1

        # Compare to expected
        v1_match = bids_match(v1_bid, tc.expected_bid)
        v2_match = bids_match(v2_bid, tc.expected_bid)

        if v1_match:
            v1_matched += 1
        if v2_match:
            v2_matched += 1

        if v1_match and v2_match:
            both_matched += 1
        elif v1_match and not v2_match:
            v1_only += 1
            v1_wins.append({
                'category': tc.category,
                'hand': tc.hand,
                'history': tc.history,
                'expected': tc.expected_bid,
                'v1_bid': v1_bid,
                'v2_bid': v2_bid,
                'v1_exp': v1_exp[:60],
                'v2_exp': v2_exp[:60]
            })
        elif v2_match and not v1_match:
            v2_only += 1
            v2_wins.append({
                'category': tc.category,
                'hand': tc.hand,
                'history': tc.history,
                'expected': tc.expected_bid,
                'v1_bid': v1_bid,
                'v2_bid': v2_bid,
                'v1_exp': v1_exp[:60],
                'v2_exp': v2_exp[:60]
            })
        else:
            neither += 1

        # Category tracking
        cat = tc.category
        if cat not in v1_cat_stats:
            v1_cat_stats[cat] = {'total': 0, 'matched': 0}
            v2_cat_stats[cat] = {'total': 0, 'matched': 0, 'no_rule': 0}

        v1_cat_stats[cat]['total'] += 1
        v2_cat_stats[cat]['total'] += 1

        if v1_match:
            v1_cat_stats[cat]['matched'] += 1
        if v2_match:
            v2_cat_stats[cat]['matched'] += 1
        if 'No applicable bidding rule' in v2_exp:
            v2_cat_stats[cat]['no_rule'] += 1

    # Print results
    print("\n" + "=" * 70)
    print("OVERALL RESULTS")
    print("=" * 70)
    print(f"Total tests: {total}")
    print()
    print(f"V1 (Python modules) matched: {v1_matched} ({v1_matched/total*100:.1f}%)")
    print(f"V2 (Schema-driven) matched:  {v2_matched} ({v2_matched/total*100:.1f}%)")
    print()
    print(f"Both matched:     {both_matched} ({both_matched/total*100:.1f}%)")
    print(f"V1 only matched:  {v1_only} ({v1_only/total*100:.1f}%)")
    print(f"V2 only matched:  {v2_only} ({v2_only/total*100:.1f}%)")
    print(f"Neither matched:  {neither} ({neither/total*100:.1f}%)")
    print()
    print(f"V1 errors: {v1_errors}")
    print(f"V2 errors: {v2_errors}")
    print(f"V2 no-rule-found: {v2_no_rule} ({v2_no_rule/total*100:.1f}%)")

    # Comparison verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    diff = v2_matched - v1_matched
    if diff > 0:
        print(f"✅ V2 wins by {diff} tests ({diff/total*100:.1f}% improvement)")
    elif diff < 0:
        print(f"⚠️  V1 wins by {-diff} tests")
    else:
        print("🔄 Engines are tied")

    # Category breakdown
    print("\n" + "=" * 70)
    print("CATEGORY BREAKDOWN")
    print("=" * 70)
    print(f"{'Category':<35} {'V1 Match%':>10} {'V2 Match%':>10} {'V2 NoRule%':>10} {'Winner':>8}")
    print("-" * 70)

    sorted_cats = sorted(v1_cat_stats.items(), key=lambda x: -x[1]['total'])
    for cat, v1_stats in sorted_cats:
        v2_stats = v2_cat_stats[cat]
        v1_pct = v1_stats['matched'] / v1_stats['total'] * 100
        v2_pct = v2_stats['matched'] / v2_stats['total'] * 100
        no_rule_pct = v2_stats['no_rule'] / v2_stats['total'] * 100

        if v2_pct > v1_pct:
            winner = "V2"
        elif v1_pct > v2_pct:
            winner = "V1"
        else:
            winner = "TIE"

        print(f"{cat:<35} {v1_pct:>9.1f}% {v2_pct:>9.1f}% {no_rule_pct:>9.1f}% {winner:>8}")

    # Show V2 wins (where V2 improved over V1)
    if v2_wins:
        print("\n" + "=" * 70)
        print(f"V2 WINS (first 10 of {len(v2_wins)} cases where V2 beat V1)")
        print("=" * 70)
        for i, case in enumerate(v2_wins[:10]):
            print(f"\n{i+1}. [{case['category']}]")
            print(f"   Hand: {case['hand']}")
            print(f"   History: {' -> '.join(case['history']) if case['history'] else 'Opening'}")
            print(f"   Expected: {case['expected']}")
            print(f"   V1: {case['v1_bid']} ({case['v1_exp']}...)")
            print(f"   V2: {case['v2_bid']} ✅ ({case['v2_exp']}...)")

    # Show V1 wins (where V1 was better - areas for V2 improvement)
    if v1_wins:
        print("\n" + "=" * 70)
        print(f"V1 WINS (first 10 of {len(v1_wins)} cases where V1 beat V2)")
        print("=" * 70)
        for i, case in enumerate(v1_wins[:10]):
            print(f"\n{i+1}. [{case['category']}]")
            print(f"   Hand: {case['hand']}")
            print(f"   History: {' -> '.join(case['history']) if case['history'] else 'Opening'}")
            print(f"   Expected: {case['expected']}")
            print(f"   V1: {case['v1_bid']} ✅ ({case['v1_exp']}...)")
            print(f"   V2: {case['v2_bid']} ({case['v2_exp']}...)")

    return {
        'total': total,
        'v1_matched': v1_matched,
        'v2_matched': v2_matched,
        'both_matched': both_matched,
        'v1_only': v1_only,
        'v2_only': v2_only,
        'neither': neither,
        'v2_no_rule': v2_no_rule
    }


def main():
    parser = argparse.ArgumentParser(description='Compare V1 and V2 bidding engines')
    parser.add_argument('--quick', action='store_true', help='Quick test (first 50)')
    parser.add_argument('--limit', type=int, help='Limit number of tests')
    args = parser.parse_args()

    # Parse baseline
    print("Parsing saycbridge baseline...")
    _, test_cases = parse_baseline()

    if not test_cases:
        print("No test cases found!")
        return 1

    print(f"Found {len(test_cases)} test cases")

    # Run comparison
    limit = 50 if args.quick else args.limit
    results = run_comparison(test_cases, limit)

    return 0


if __name__ == '__main__':
    sys.exit(main())
