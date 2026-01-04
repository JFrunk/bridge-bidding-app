#!/usr/bin/env python3
"""
Ratchet Tracker for V2 Schema Regression Prevention

The "ratchet" mechanism ensures that once a test passes, it must NEVER regress.
This prevents the "False Progress" trap where fixing Category A breaks Category B
while the total score appears unchanged.

Principle: "No new failures on previously passing hands."

Usage:
    # Update baseline after verified improvements
    python3 ratchet_tracker.py update results_v2.json

    # Check for regressions (used in CI)
    python3 ratchet_tracker.py check results_v2.json

    # View current baseline
    python3 ratchet_tracker.py status

The ratchet file stores:
- test_id → last_known_status (pass/fail)
- test_id → first_passed_at (timestamp when first passed)
- test_id → rule_id (which rule produced the pass)

CI Integration:
    If check finds regressions → Exit 1 (fail the build)
    If check finds only new passes → Exit 0 (allow the build)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

RATCHET_FILE = Path(__file__).parent / "ratchet_baseline.json"


@dataclass
class RatchetEntry:
    """Entry for a single test in the ratchet baseline."""
    test_id: str
    status: str  # "pass" or "fail"
    first_passed_at: Optional[str]  # ISO timestamp
    rule_id: Optional[str]  # Which rule produced the pass
    expected_bid: str
    our_bid: str
    category: str


def load_ratchet() -> Dict[str, RatchetEntry]:
    """Load the ratchet baseline file."""
    if not RATCHET_FILE.exists():
        return {}

    with open(RATCHET_FILE) as f:
        data = json.load(f)

    return {
        test_id: RatchetEntry(**entry)
        for test_id, entry in data.get('tests', {}).items()
    }


def save_ratchet(entries: Dict[str, RatchetEntry], metadata: Dict = None):
    """Save the ratchet baseline file."""
    data = {
        'updated_at': datetime.now().isoformat(),
        'total_tests': len(entries),
        'passing_tests': sum(1 for e in entries.values() if e.status == 'pass'),
        'metadata': metadata or {},
        'tests': {
            test_id: asdict(entry)
            for test_id, entry in entries.items()
        }
    }

    with open(RATCHET_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Ratchet baseline saved to: {RATCHET_FILE}")


def load_results(filepath: str) -> Dict[str, Dict]:
    """Load test results from JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    results = {}
    for r in data.get('results', []):
        results[r['test_id']] = r

    return results


def check_regressions(
    current_results: Dict[str, Dict],
    baseline: Dict[str, RatchetEntry]
) -> Tuple[List[str], List[str], List[str]]:
    """
    Check for regressions against the ratchet baseline.

    Returns:
        Tuple of (regressions, new_passes, unchanged)
    """
    regressions = []
    new_passes = []
    unchanged = []

    for test_id, baseline_entry in baseline.items():
        if test_id not in current_results:
            # Test no longer exists - could be removed or renamed
            continue

        current = current_results[test_id]
        current_passed = current.get('matched_expected', False)
        baseline_passed = baseline_entry.status == 'pass'

        if baseline_passed and not current_passed:
            # REGRESSION: Was passing, now failing
            regressions.append(test_id)
        elif not baseline_passed and current_passed:
            # IMPROVEMENT: Was failing, now passing
            new_passes.append(test_id)
        else:
            unchanged.append(test_id)

    return regressions, new_passes, unchanged


def update_baseline(results_file: str) -> Dict[str, RatchetEntry]:
    """
    Update the ratchet baseline with current results.

    Only call this after verifying improvements are legitimate!
    """
    current_results = load_results(results_file)
    baseline = load_ratchet()

    now = datetime.now().isoformat()
    updated = 0
    new_entries = 0

    for test_id, result in current_results.items():
        passed = result.get('matched_expected', False)

        if test_id in baseline:
            entry = baseline[test_id]
            if passed and entry.status != 'pass':
                # Test now passes - update and record timestamp
                entry.status = 'pass'
                entry.first_passed_at = now
                entry.rule_id = result.get('rule_id')
                entry.our_bid = result.get('our_bid', '')
                updated += 1
            elif not passed:
                # Test fails - update current state
                entry.status = 'fail'
                entry.our_bid = result.get('our_bid', '')
                entry.rule_id = result.get('rule_id')
        else:
            # New test - add to baseline
            baseline[test_id] = RatchetEntry(
                test_id=test_id,
                status='pass' if passed else 'fail',
                first_passed_at=now if passed else None,
                rule_id=result.get('rule_id'),
                expected_bid=result.get('expected_bid', ''),
                our_bid=result.get('our_bid', ''),
                category=result.get('category', '')
            )
            new_entries += 1

    save_ratchet(baseline, {
        'updated_from': results_file,
        'updated_count': updated,
        'new_entries': new_entries
    })

    return baseline


def print_status():
    """Print current ratchet baseline status."""
    baseline = load_ratchet()

    if not baseline:
        print("No ratchet baseline exists yet.")
        print("Run: python3 ratchet_tracker.py update <results_file.json>")
        return

    passing = [e for e in baseline.values() if e.status == 'pass']
    failing = [e for e in baseline.values() if e.status == 'fail']

    print("\n" + "=" * 60)
    print("RATCHET BASELINE STATUS")
    print("=" * 60)
    print(f"Total tests: {len(baseline)}")
    print(f"Passing (locked): {len(passing)}")
    print(f"Failing (unlocked): {len(failing)}")
    print(f"Pass rate: {len(passing)/len(baseline)*100:.1f}%")

    # Category breakdown
    categories = {}
    for entry in baseline.values():
        cat = entry.category
        if cat not in categories:
            categories[cat] = {'pass': 0, 'fail': 0}
        categories[cat][entry.status] += 1

    print("\nBy Category:")
    print("-" * 40)
    for cat, stats in sorted(categories.items(), key=lambda x: -x[1]['pass']):
        total = stats['pass'] + stats['fail']
        rate = stats['pass'] / total * 100 if total > 0 else 0
        status = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
        print(f"  {status} {cat}: {stats['pass']}/{total} ({rate:.0f}%)")


def run_check(results_file: str) -> int:
    """
    Run regression check against ratchet baseline.

    Returns:
        0 if no regressions, 1 if regressions found
    """
    baseline = load_ratchet()

    if not baseline:
        print("⚠️  No ratchet baseline exists - creating initial baseline")
        update_baseline(results_file)
        return 0

    current_results = load_results(results_file)
    regressions, new_passes, unchanged = check_regressions(current_results, baseline)

    print("\n" + "=" * 60)
    print("RATCHET REGRESSION CHECK")
    print("=" * 60)

    if regressions:
        print(f"\n🚨 REGRESSIONS DETECTED: {len(regressions)}")
        print("-" * 40)
        for test_id in regressions:
            entry = baseline[test_id]
            current = current_results.get(test_id, {})
            print(f"  ❌ {test_id}")
            print(f"     Was: {entry.our_bid} (PASS)")
            print(f"     Now: {current.get('our_bid', '?')} (FAIL)")
            print(f"     Expected: {entry.expected_bid}")
            print(f"     Rule was: {entry.rule_id}")
            print(f"     First passed: {entry.first_passed_at}")

        print("\n⛔ BUILD FAILED: Fix regressions before merging!")
        return 1

    print(f"\n✅ No regressions detected")

    if new_passes:
        print(f"\n🎉 NEW PASSES: {len(new_passes)}")
        for test_id in new_passes[:10]:  # Show first 10
            current = current_results.get(test_id, {})
            print(f"  ✅ {test_id}: {current.get('our_bid')} (was failing)")
        if len(new_passes) > 10:
            print(f"  ... and {len(new_passes) - 10} more")

        print("\n📝 Run 'python3 ratchet_tracker.py update' to lock these improvements")

    print(f"\nUnchanged: {len(unchanged)}")

    return 0


def main():
    parser = argparse.ArgumentParser(description='Ratchet Tracker for V2 Schema')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update baseline with current results')
    update_parser.add_argument('results_file', help='Path to results JSON file')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check for regressions')
    check_parser.add_argument('results_file', help='Path to results JSON file')

    # Status command
    subparsers.add_parser('status', help='Show current baseline status')

    args = parser.parse_args()

    if args.command == 'update':
        update_baseline(args.results_file)
        return 0
    elif args.command == 'check':
        return run_check(args.results_file)
    elif args.command == 'status':
        print_status()
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
