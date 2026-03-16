#!/usr/bin/env python3
"""
CLI runner for the Bidding QA Differential Testing Pipeline.

Usage:
    # Generate test PBN file and run against MBB engine
    python -m qa.run_qa generate --type balanced --count 100 --output /tmp/qa_balanced.pbn
    python -m qa.run_qa test --pbn /tmp/qa_balanced.pbn --seats South --output /tmp/qa_results.json

    # Run ground truth suite against MBB (all tiers)
    python -m qa.run_qa suite --data data/ground_truth/

    # Run ground truth with quality gate threshold
    python -m qa.run_qa suite --data data/ground_truth/ --fail-under 95.0

    # Run only specific tier
    python -m qa.run_qa suite --data data/ground_truth/ --filter "Tier 1"

    # Analyze discrepancies from a previous run
    python -m qa.run_qa analyze --results /tmp/qa_results.json

    # Full pipeline: generate + test + report
    python -m qa.run_qa full --type mixed --count 200 --output /tmp/qa_full.json
"""

import argparse
import json
import os
import sys
import tempfile
from typing import Dict

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa.pbn_generator import PBNTestGenerator
from qa.bidding_qa_harness import (
    BiddingQAHarness, HarnessResult, BoardResult, BidComparison,
)


def cmd_generate(args):
    """Generate a PBN test suite."""
    gen = PBNTestGenerator(seed=args.seed)
    output = args.output or f'/tmp/qa_{args.type}_suite.pbn'

    generator_map = {
        'balanced': gen.generate_balanced_suite,
        'competitive': gen.generate_competitive_suite,
        'slam': gen.generate_slam_suite,
        'mixed': gen.generate_mixed_suite,
    }

    func = generator_map.get(args.type)
    if not func:
        print(f"Unknown suite type: {args.type}. Use: balanced, competitive, slam, mixed")
        return 1

    count = func(args.count, output)
    print(f"Generated {count} boards → {output}")
    return 0


def cmd_test(args):
    """Run differential testing on a PBN file."""
    if not os.path.exists(args.pbn):
        print(f"PBN file not found: {args.pbn}")
        return 1

    harness = BiddingQAHarness()
    seats = args.seats.split(',') if args.seats else None

    result = harness.run_pbn_file(
        pbn_path=args.pbn,
        seats=seats,
        max_boards=args.max_boards,
        include_features=args.features,
    )

    harness.print_summary(result)

    if args.output:
        result.save(args.output)
        print(f"\nDetailed results saved to: {args.output}")

    # Categorize discrepancies
    if result.discrepancy_count > 0:
        categories = harness.analyze_discrepancies(result)
        print(f"\nDiscrepancy Categories:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  {cat}: {count}")

        harness.print_phase_analysis(result)

    return 0


def cmd_suite(args):
    """Run ground truth suite against MBB engine."""
    if not os.path.isdir(args.data):
        print(f"Directory not found: {args.data}")
        return 1

    harness = BiddingQAHarness()
    seats = args.seats.split(',') if args.seats else None

    tier_results = harness.run_directory(
        dir_path=args.data,
        seats=seats,
        max_boards=args.max_boards,
        include_features=args.features,
        event_filter=args.filter,
    )

    if not tier_results:
        print("No PBN files found in directory.")
        return 1

    overall_accuracy = harness.print_tier_report(tier_results)

    # Save combined results if requested
    if args.output:
        combined = {
            'tiers': {},
            'overall_accuracy': round(overall_accuracy / 100, 4),
        }
        for filename, result in tier_results.items():
            combined['tiers'][filename] = result.to_dict()
        with open(args.output, 'w') as f:
            json.dump(combined, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {args.output}")

    # Quality gate check
    if args.fail_under is not None:
        threshold = args.fail_under
        if overall_accuracy < threshold:
            print(f"\nFAILED: Accuracy {overall_accuracy:.1f}% < threshold {threshold:.1f}%")
            return 1
        else:
            print(f"\nPASSED: Accuracy {overall_accuracy:.1f}% >= threshold {threshold:.1f}%")

    return 0


def _reconstruct_result(data: Dict) -> HarnessResult:
    """Reconstruct a HarnessResult from saved JSON for re-analysis."""
    summary = data.get('summary', {})
    result = HarnessResult(
        total_boards=summary.get('total_boards', 0),
        boards_with_hands=summary.get('boards_with_hands', 0),
        boards_with_auctions=summary.get('boards_with_auctions', 0),
        total_bids_compared=summary.get('total_bids_compared', 0),
        total_matches=summary.get('total_matches', 0),
        duration_seconds=summary.get('duration_seconds', 0.0),
    )
    for b in data.get('boards', []):
        board = BoardResult(
            board=b['board'],
            dealer=b['dealer'],
            vulnerability=b['vulnerability'],
            total_bids_compared=b.get('total_bids_compared', 0),
            matches=b.get('matches', 0),
            error=b.get('error'),
        )
        for d in b.get('discrepancies', []):
            board.discrepancies.append(BidComparison(
                board=d['board'],
                seat=d['seat'],
                bid_index=d['bid_index'],
                auction_so_far=d.get('auction_so_far', []),
                mbb_bid=d['mbb_bid'],
                reference_bid=d['reference_bid'],
                match=d.get('match', False),
                mbb_explanation=d.get('mbb_explanation', ''),
                hand_pbn=d.get('hand_pbn', ''),
            ))
        result.board_results.append(board)
    return result


def cmd_analyze(args):
    """Analyze results from a previous QA run."""
    if not os.path.exists(args.results):
        print(f"Results file not found: {args.results}")
        return 1

    with open(args.results) as f:
        data = json.load(f)

    summary = data.get('summary', {})
    print(f"\n{'='*60}")
    print(f"  QA Results Analysis")
    print(f"{'='*60}")
    print(f"  Accuracy:       {summary.get('overall_accuracy', 0)*100:.1f}%")
    print(f"  Bids compared:  {summary.get('total_bids_compared', 0)}")
    print(f"  Discrepancies:  {summary.get('discrepancy_count', 0)}")

    # Show boards with most discrepancies
    boards = data.get('boards', [])
    problem_boards = sorted(boards, key=lambda b: len(b.get('discrepancies', [])), reverse=True)

    print(f"\n  Boards with most discrepancies:")
    for board in problem_boards[:10]:
        disc_count = len(board.get('discrepancies', []))
        if disc_count == 0:
            break
        print(f"    Board {board['board']:>3}: {disc_count} discrepancies "
              f"(accuracy: {board.get('accuracy', 0)*100:.0f}%)")

    # Phase analysis from reconstructed result
    result = _reconstruct_result(data)
    if result.discrepancy_count > 0:
        harness = BiddingQAHarness()
        harness.print_phase_analysis(result)

    return 0


def cmd_full(args):
    """Full pipeline: generate → test → report."""
    pbn_path = tempfile.mktemp(suffix='.pbn', prefix='qa_')

    gen = PBNTestGenerator(seed=args.seed)
    generator_map = {
        'balanced': gen.generate_balanced_suite,
        'competitive': gen.generate_competitive_suite,
        'slam': gen.generate_slam_suite,
        'mixed': gen.generate_mixed_suite,
    }

    func = generator_map.get(args.type, gen.generate_mixed_suite)
    count = func(args.count, pbn_path)
    print(f"Generated {count} boards → {pbn_path}")

    harness = BiddingQAHarness()
    seats = args.seats.split(',') if args.seats else None

    result = harness.run_pbn_file(
        pbn_path=pbn_path,
        seats=seats,
        max_boards=args.max_boards,
        include_features=True,
    )

    harness.print_summary(result)

    if args.output:
        result.save(args.output)
        print(f"\nDetailed results saved to: {args.output}")

    if result.discrepancy_count > 0:
        categories = harness.analyze_discrepancies(result)
        print(f"\nDiscrepancy Categories:")
        for cat, count_val in sorted(categories.items(), key=lambda x: -x[1]):
            if count_val > 0:
                print(f"  {cat}: {count_val}")

        harness.print_phase_analysis(result)

    # Cleanup temp PBN
    try:
        os.unlink(pbn_path)
    except OSError:
        pass

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Bidding QA Differential Testing Pipeline'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate PBN test suite')
    gen_parser.add_argument('--type', default='mixed',
                           choices=['balanced', 'competitive', 'slam', 'mixed'])
    gen_parser.add_argument('--count', type=int, default=100)
    gen_parser.add_argument('--output', help='Output PBN file path')
    gen_parser.add_argument('--seed', type=int, default=42)

    # Test command
    test_parser = subparsers.add_parser('test', help='Run QA on PBN file')
    test_parser.add_argument('--pbn', required=True, help='PBN file to test')
    test_parser.add_argument('--seats', help='Comma-separated seats (e.g., South,North)')
    test_parser.add_argument('--max-boards', type=int, help='Max boards to test')
    test_parser.add_argument('--features', action='store_true',
                            help='Include feature vectors in output')
    test_parser.add_argument('--output', help='Output JSON file path')

    # Suite command (ground truth directory)
    suite_parser = subparsers.add_parser('suite', help='Run ground truth suite')
    suite_parser.add_argument('--data', required=True,
                             help='Directory containing ground truth PBN files')
    suite_parser.add_argument('--seats', help='Comma-separated seats')
    suite_parser.add_argument('--max-boards', type=int)
    suite_parser.add_argument('--features', action='store_true')
    suite_parser.add_argument('--filter', help='Only test boards with matching [Event] text')
    suite_parser.add_argument('--fail-under', type=float,
                             help='Fail if accuracy below this threshold (0-100)')
    suite_parser.add_argument('--output', help='Output JSON file path')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze previous results')
    analyze_parser.add_argument('--results', required=True, help='Results JSON file')

    # Full pipeline command
    full_parser = subparsers.add_parser('full', help='Full pipeline: generate + test')
    full_parser.add_argument('--type', default='mixed',
                            choices=['balanced', 'competitive', 'slam', 'mixed'])
    full_parser.add_argument('--count', type=int, default=100)
    full_parser.add_argument('--seats', help='Comma-separated seats')
    full_parser.add_argument('--max-boards', type=int)
    full_parser.add_argument('--output', help='Output JSON file path')
    full_parser.add_argument('--seed', type=int, default=42)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'generate': cmd_generate,
        'test': cmd_test,
        'suite': cmd_suite,
        'analyze': cmd_analyze,
        'full': cmd_full,
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
