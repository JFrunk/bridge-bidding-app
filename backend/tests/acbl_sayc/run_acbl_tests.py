#!/usr/bin/env python3
"""
ACBL SAYC Test Suite Runner

This script runs the complete ACBL SAYC test suite and generates a detailed
report of passing and failing tests, organized by bidding category.

Usage:
    python run_acbl_tests.py              # Run all tests
    python run_acbl_tests.py --category opening    # Run only opening bid tests
    python run_acbl_tests.py --verbose    # Verbose output
    python run_acbl_tests.py --report     # Generate detailed JSON report
"""

import subprocess
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path


def run_tests(category=None, verbose=False, report=False):
    """Run ACBL SAYC tests and optionally generate a report."""

    test_dir = Path(__file__).parent

    # Map category names to test files
    categories = {
        'opening': 'test_opening_bids.py',
        'responses': 'test_responses.py',
        'rebids': 'test_rebids.py',
        'notrump': 'test_notrump.py',
        'slam': 'test_slam_bidding.py',
        'competitive': 'test_competitive.py',
    }

    # Build pytest command
    cmd = ['python', '-m', 'pytest']

    if category:
        if category not in categories:
            print(f"Unknown category: {category}")
            print(f"Available categories: {', '.join(categories.keys())}")
            return 1
        cmd.append(str(test_dir / categories[category]))
    else:
        cmd.append(str(test_dir))

    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-v')  # Always use verbose for better output

    if report:
        # Generate JSON report
        report_file = test_dir / f"acbl_sayc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        cmd.extend(['--tb=short', f'--json-report', f'--json-report-file={report_file}'])

    # Add color output
    cmd.append('--color=yes')

    print("=" * 70)
    print("ACBL SAYC Test Suite")
    print("=" * 70)
    print(f"Running: {' '.join(cmd)}")
    print()

    # Run pytest
    result = subprocess.run(cmd, cwd=test_dir.parent.parent)

    return result.returncode


def generate_summary():
    """Generate a summary of test coverage by SAYC topic."""

    test_dir = Path(__file__).parent

    summary = {
        "Opening Bids": {
            "file": "test_opening_bids.py",
            "topics": [
                "1NT Opening (15-17 HCP balanced)",
                "2NT Opening (20-21 HCP balanced)",
                "Strong 2♣ Opening (22+ HCP)",
                "Weak Two Bids (5-11 HCP, 6-card suit)",
                "One-Level Suit Openings (13+ points)",
                "Preemptive Openings (3-level)",
                "Pass with insufficient values",
            ]
        },
        "Responses": {
            "file": "test_responses.py",
            "topics": [
                "Responses to 1♥ Opening",
                "Responses to 1♠ Opening",
                "Responses to 1♣ Opening",
                "Responses to 1♦ Opening",
                "Responses to 1NT Opening",
                "Responses to Strong 2♣",
                "Responses to Weak Two Bids",
            ]
        },
        "Rebids": {
            "file": "test_rebids.py",
            "topics": [
                "Opener's Rebid after 1-level response",
                "Opener's Rebid after 2-level response",
                "Opener's Rebid after raise",
                "Responder's Rebid",
                "Opener's Rebid after 1NT response",
            ]
        },
        "Notrump Bidding": {
            "file": "test_notrump.py",
            "topics": [
                "Stayman Convention (2♣)",
                "Jacoby Transfers (2♦/2♥)",
                "Direct Notrump Raises",
                "2NT Opening and Responses",
                "1NT Opener's Rebid",
            ]
        },
        "Slam Bidding": {
            "file": "test_slam_bidding.py",
            "topics": [
                "Blackwood Convention (4NT)",
                "King Ask (5NT)",
                "Slam Decisions without Blackwood",
                "Gerber Convention (4♣) over NT",
                "Control Bids (Cuebids)",
            ]
        },
        "Competitive Bidding": {
            "file": "test_competitive.py",
            "topics": [
                "Simple Overcalls",
                "1NT Overcall",
                "Takeout Doubles",
                "Responding to Takeout Double",
                "Negative Doubles",
                "Michaels Cuebid",
                "Unusual 2NT",
                "Advancing Partner's Overcall",
                "Balancing",
            ]
        }
    }

    print("\n" + "=" * 70)
    print("ACBL SAYC Test Coverage Summary")
    print("=" * 70)

    for category, info in summary.items():
        print(f"\n{category} ({info['file']}):")
        for topic in info['topics']:
            print(f"  • {topic}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Run ACBL SAYC test suite')
    parser.add_argument('--category', '-c',
                        choices=['opening', 'responses', 'rebids', 'notrump', 'slam', 'competitive'],
                        help='Run only tests for a specific category')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--report', '-r', action='store_true',
                        help='Generate JSON report')
    parser.add_argument('--summary', '-s', action='store_true',
                        help='Show test coverage summary')

    args = parser.parse_args()

    if args.summary:
        generate_summary()
        return 0

    return run_tests(args.category, args.verbose, args.report)


if __name__ == '__main__':
    sys.exit(main())
