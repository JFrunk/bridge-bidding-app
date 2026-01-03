#!/usr/bin/env python3
"""
Schema Engine Baseline Test

Tests the new schema-driven V2 engine against the saycbridge baseline.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.hand import Hand, Card
from engine.v2 import BiddingEngineV2Schema
from tests.sayc_baseline.sayc_baseline_parser import parse_baseline


def convert_hand(hand_str: str) -> Hand:
    """Convert saycbridge hand notation to Hand object."""
    parts = hand_str.split('.')
    if len(parts) != 4:
        return None

    cards = []
    suit_symbols = ['♠', '♥', '♦', '♣']

    for i, suit_cards in enumerate(parts):
        for card_char in suit_cards:
            cards.append(Card(card_char, suit_symbols[i]))

    return Hand(cards)


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


def main():
    print("=" * 70)
    print("SCHEMA-DRIVEN V2 ENGINE BASELINE TEST")
    print("=" * 70)

    # Parse baseline
    print("\nParsing saycbridge baseline...")
    parser, test_cases = parse_baseline()

    if not test_cases:
        print("No test cases found!")
        return 1

    print(f"Found {len(test_cases)} test cases")

    # Create schema engine
    engine = BiddingEngineV2Schema()
    print(f"Loaded schemas: {list(engine.interpreter.schemas.keys())}")

    # Run tests
    total = len(test_cases)
    matched = 0
    errors = 0
    no_rule = 0

    positions = ['North', 'East', 'South', 'West']

    # Category tracking
    category_stats = {}

    for i, tc in enumerate(test_cases):
        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{total}...")

        hand = convert_hand(tc.hand)
        if hand is None:
            errors += 1
            continue

        position = positions[len(tc.history) % 4]

        # Reset forcing state for each new test case (each is a new deal)
        engine.new_deal()

        try:
            bid, explanation = engine.get_next_bid(
                hand=hand,
                auction_history=tc.history,
                my_position=position,
                vulnerability='None'
            )
        except Exception as e:
            errors += 1
            continue

        is_match = bids_match(bid, tc.expected_bid)
        if is_match:
            matched += 1

        if 'No applicable bidding rule' in explanation:
            no_rule += 1

        # Track by category
        cat = tc.category
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'matched': 0, 'no_rule': 0}
        category_stats[cat]['total'] += 1
        if is_match:
            category_stats[cat]['matched'] += 1
        if 'No applicable bidding rule' in explanation:
            category_stats[cat]['no_rule'] += 1

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total tests: {total}")
    print(f"Matched expected: {matched} ({matched/total*100:.1f}%)")
    print(f"No rule found: {no_rule} ({no_rule/total*100:.1f}%)")
    print(f"Errors: {errors}")

    # Category breakdown
    print("\nCategory Breakdown:")
    print("-" * 70)
    print(f"{'Category':<30} {'Match%':>10} {'NoRule%':>10} {'Total':>8}")
    print("-" * 70)

    sorted_cats = sorted(category_stats.items(), key=lambda x: -x[1]['total'])
    for cat, stats in sorted_cats:
        match_pct = stats['matched'] / stats['total'] * 100 if stats['total'] > 0 else 0
        no_rule_pct = stats['no_rule'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"{cat:<30} {match_pct:>9.1f}% {no_rule_pct:>9.1f}% {stats['total']:>8}")

    # Show sample failures for debugging
    print("\n" + "=" * 70)
    print("SAMPLE FAILURES (first 10)")
    print("=" * 70)

    failures = 0
    for tc in test_cases:
        if failures >= 10:
            break

        hand = convert_hand(tc.hand)
        if hand is None:
            continue

        position = positions[len(tc.history) % 4]

        # Reset forcing state for each test case
        engine.new_deal()

        try:
            bid, explanation = engine.get_next_bid(
                hand=hand,
                auction_history=tc.history,
                my_position=position,
                vulnerability='None'
            )
        except Exception:
            continue

        if not bids_match(bid, tc.expected_bid):
            failures += 1
            print(f"\n{failures}. [{tc.category}]")
            print(f"   Hand: {tc.hand} ({tc.hcp} HCP)")
            print(f"   History: {' -> '.join(tc.history) if tc.history else 'Opening'}")
            print(f"   Expected: {tc.expected_bid}")
            print(f"   Got: {bid}")
            print(f"   Explanation: {explanation[:60]}...")

    return 0


if __name__ == '__main__':
    sys.exit(main())
