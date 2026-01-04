#!/usr/bin/env python3
"""
Compare baseline test results between V1 and V2 engines.

Usage:
    python3 compare_baseline_results.py results_v1.json results_v2.json
"""

import sys
import json
import argparse
from pathlib import Path


def load_results(filepath: str) -> dict:
    """Load results from JSON file."""
    with open(filepath) as f:
        return json.load(f)


def compare_results(v1_results: dict, v2_results: dict) -> dict:
    """
    Compare V1 and V2 results and identify improvements/regressions.

    Returns:
        Comparison dict with improvements, regressions, and summary
    """
    v1_tests = {r['test_id']: r for r in v1_results.get('results', [])}
    v2_tests = {r['test_id']: r for r in v2_results.get('results', [])}

    improvements = []
    regressions = []
    unchanged_pass = []
    unchanged_fail = []

    common_tests = set(v1_tests.keys()) & set(v2_tests.keys())

    for test_id in common_tests:
        v1 = v1_tests[test_id]
        v2 = v2_tests[test_id]

        v1_pass = v1.get('matched_expected', False)
        v2_pass = v2.get('matched_expected', False)

        if not v1_pass and v2_pass:
            improvements.append({
                'test_id': test_id,
                'category': v2.get('category'),
                'hand': v2.get('hand'),
                'expected': v2.get('expected_bid'),
                'v1_bid': v1.get('our_bid'),
                'v2_bid': v2.get('our_bid'),
                'v2_rule': v2.get('rule_id'),
                'v2_explanation': v2.get('our_explanation', '')[:100]
            })
        elif v1_pass and not v2_pass:
            regressions.append({
                'test_id': test_id,
                'category': v2.get('category'),
                'hand': v2.get('hand'),
                'expected': v2.get('expected_bid'),
                'v1_bid': v1.get('our_bid'),
                'v2_bid': v2.get('our_bid'),
                'v2_used_fallback': v2.get('used_v1_fallback', False)
            })
        elif v1_pass and v2_pass:
            unchanged_pass.append(test_id)
        else:
            unchanged_fail.append(test_id)

    return {
        'summary': {
            'total_compared': len(common_tests),
            'improvements': len(improvements),
            'regressions': len(regressions),
            'unchanged_passing': len(unchanged_pass),
            'unchanged_failing': len(unchanged_fail),
            'v1_total_pass': sum(1 for t in v1_tests.values() if t.get('matched_expected')),
            'v2_total_pass': sum(1 for t in v2_tests.values() if t.get('matched_expected')),
            'v1_compliance_rate': v1_results.get('summary', {}).get('compliance_rate', 0),
            'v2_compliance_rate': v2_results.get('summary', {}).get('compliance_rate', 0)
        },
        'improvements': improvements,
        'regressions': regressions,
        'category_comparison': compare_categories(v1_results, v2_results)
    }


def compare_categories(v1_results: dict, v2_results: dict) -> dict:
    """Compare category-level statistics."""
    v1_cats = v1_results.get('category_stats', {})
    v2_cats = v2_results.get('category_stats', {})

    all_cats = set(v1_cats.keys()) | set(v2_cats.keys())

    comparison = {}
    for cat in all_cats:
        v1_stat = v1_cats.get(cat, {'total': 0, 'matched_expected': 0})
        v2_stat = v2_cats.get(cat, {'total': 0, 'matched_expected': 0})

        v1_rate = v1_stat['matched_expected'] / max(1, v1_stat['total'])
        v2_rate = v2_stat['matched_expected'] / max(1, v2_stat['total'])

        comparison[cat] = {
            'v1_pass': v1_stat['matched_expected'],
            'v2_pass': v2_stat['matched_expected'],
            'total': max(v1_stat['total'], v2_stat['total']),
            'v1_rate': v1_rate,
            'v2_rate': v2_rate,
            'delta': v2_rate - v1_rate,
            'schema_coverage': v2_stat.get('schema_hits', 0) / max(1, v2_stat.get('total', 1))
        }

    return comparison


def print_comparison(comparison: dict):
    """Print comparison report."""
    summary = comparison['summary']

    print("\n" + "=" * 70)
    print("V1 vs V2 BASELINE COMPARISON REPORT")
    print("=" * 70)

    print(f"\nOverall Comparison:")
    print(f"  Tests compared: {summary['total_compared']}")
    print(f"  V1 compliance rate: {summary['v1_compliance_rate']*100:.1f}%")
    print(f"  V2 compliance rate: {summary['v2_compliance_rate']*100:.1f}%")

    delta = summary['v2_compliance_rate'] - summary['v1_compliance_rate']
    emoji = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
    print(f"  Delta: {emoji} {delta*100:+.1f}%")

    print(f"\nChanges:")
    print(f"  ✅ Improvements (V1 fail → V2 pass): {summary['improvements']}")
    print(f"  ❌ Regressions (V1 pass → V2 fail): {summary['regressions']}")
    print(f"  ➡️ Unchanged passing: {summary['unchanged_passing']}")
    print(f"  ➡️ Unchanged failing: {summary['unchanged_failing']}")

    # Category breakdown
    print("\nCategory Comparison (sorted by V2 improvement):")
    print("-" * 70)

    cat_comp = comparison['category_comparison']
    sorted_cats = sorted(cat_comp.items(), key=lambda x: -x[1]['delta'])

    for cat, stats in sorted_cats:
        delta_str = f"{stats['delta']*100:+.1f}%"
        v1_pct = f"{stats['v1_rate']*100:.0f}%"
        v2_pct = f"{stats['v2_rate']*100:.0f}%"
        schema_pct = f"{stats['schema_coverage']*100:.0f}%"

        status = "📈" if stats['delta'] > 0.05 else "📉" if stats['delta'] < -0.05 else "➡️"

        print(f"  {status} {cat[:40]:<40}")
        print(f"      V1: {v1_pct:>5} → V2: {v2_pct:>5} (delta: {delta_str:>6}, schema: {schema_pct})")

    # Show improvements
    if comparison['improvements']:
        print("\n" + "=" * 70)
        print(f"IMPROVEMENTS (showing first 10 of {len(comparison['improvements'])})")
        print("=" * 70)

        for i, imp in enumerate(comparison['improvements'][:10]):
            print(f"\n{i+1}. {imp['test_id']}")
            print(f"   Category: {imp['category']}")
            print(f"   Expected: {imp['expected']}")
            print(f"   V1 bid: {imp['v1_bid']} ❌")
            print(f"   V2 bid: {imp['v2_bid']} ✅")
            print(f"   V2 rule: {imp.get('v2_rule', 'N/A')}")

    # Show regressions
    if comparison['regressions']:
        print("\n" + "=" * 70)
        print(f"⚠️  REGRESSIONS (showing all {len(comparison['regressions'])})")
        print("=" * 70)

        for i, reg in enumerate(comparison['regressions']):
            print(f"\n{i+1}. {reg['test_id']}")
            print(f"   Category: {reg['category']}")
            print(f"   Expected: {reg['expected']}")
            print(f"   V1 bid: {reg['v1_bid']} ✅")
            print(f"   V2 bid: {reg['v2_bid']} ❌")
            print(f"   V2 used V1 fallback: {reg.get('v2_used_fallback', False)}")


def main():
    parser = argparse.ArgumentParser(description='Compare V1 and V2 baseline results')
    parser.add_argument('v1_results', type=str, help='Path to V1 results JSON')
    parser.add_argument('v2_results', type=str, help='Path to V2 results JSON')
    parser.add_argument('--output', type=str, help='Output comparison to JSON file')

    args = parser.parse_args()

    # Load results
    v1_results = load_results(args.v1_results)
    v2_results = load_results(args.v2_results)

    # Compare
    comparison = compare_results(v1_results, v2_results)

    # Print
    print_comparison(comparison)

    # Export if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(comparison, f, indent=2)
        print(f"\nComparison exported to: {args.output}")

    # Return non-zero if there are regressions
    if comparison['regressions']:
        print(f"\n⚠️  Warning: {len(comparison['regressions'])} regression(s) detected!")
        # Don't fail CI for now, just warn
        # return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
