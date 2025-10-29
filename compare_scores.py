#!/usr/bin/env python3
"""
Compare two quality score reports.

Usage:
    python3 compare_scores.py baseline.json new.json
"""
import json
import sys


def compare_scores(baseline_file, new_file):
    """Compare two quality score reports and detect regressions."""
    try:
        with open(baseline_file) as f:
            baseline = json.load(f)
        with open(new_file) as f:
            new = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return 1

    b_scores = baseline['scores']['scores']
    n_scores = new['scores']['scores']
    b_errors = baseline['scores']['error_counts']
    n_errors = new['scores']['error_counts']

    print("=" * 80)
    print("QUALITY SCORE COMPARISON")
    print("=" * 80)
    print()
    print(f"Baseline: {baseline_file}")
    print(f"New:      {new_file}")
    print()
    print(f"Baseline: {baseline['scores']['total_hands']} hands, "
          f"{baseline['scores']['total_bids']} bids")
    print(f"New:      {new['scores']['total_hands']} hands, "
          f"{new['scores']['total_bids']} bids")
    print()
    print("-" * 80)
    print(f"{'Metric':<20} {'Baseline':>10} {'New':>10} {'Delta':>10} {'Status':>10}")
    print("-" * 80)

    metrics = ['legality', 'appropriateness', 'conventions', 'reasonableness', 'game_slam', 'composite']
    regression = False
    improvement = False

    for metric in metrics:
        baseline_score = b_scores[metric]
        new_score = n_scores[metric]
        delta = new_score - baseline_score

        # Determine status
        if metric == 'legality' and new_score < 100:
            status = "❌ FAIL"
            regression = True
        elif metric == 'composite' and delta < -2:
            status = "❌ REGR"
            regression = True
        elif metric == 'appropriateness' and delta < -5:
            status = "❌ REGR"
            regression = True
        elif delta >= 5:
            status = "✅ IMPR"
            improvement = True
        elif delta >= 0:
            status = "✅ OK"
        elif delta >= -2:
            status = "⚠️  MINOR"
        else:
            status = "⚠️  REGR"
            regression = True

        print(f"{metric.capitalize():<20} {baseline_score:>9.1f}% {new_score:>9.1f}% {delta:>+9.1f}% {status:>10}")

    print("-" * 80)
    print()

    # Error count comparison
    print("-" * 80)
    print(f"{'Error Type':<20} {'Baseline':>10} {'New':>10} {'Delta':>10}")
    print("-" * 80)

    error_types = ['legality', 'appropriateness', 'conventions', 'game_slam']
    for error_type in error_types:
        baseline_count = b_errors.get(error_type, 0)
        new_count = n_errors.get(error_type, 0)
        delta = new_count - baseline_count
        delta_str = f"{delta:+d}" if delta != 0 else "0"
        print(f"{error_type.capitalize():<20} {baseline_count:>10d} {new_count:>10d} {delta_str:>10}")

    print("-" * 80)
    print()

    # Grade comparison
    b_grade = baseline['scores']['grade']
    n_grade = new['scores']['grade']

    print(f"Grade: {b_grade} → {n_grade}")
    print()

    # Final verdict
    if regression:
        print("⛔ REGRESSION DETECTED - Do not commit!")
        print()
        print("Regression criteria:")
        if b_scores['legality'] == 100 and n_scores['legality'] < 100:
            print(f"  - Legality dropped below 100% ({n_scores['legality']:.1f}%)")
        if n_scores['composite'] < b_scores['composite'] - 2:
            print(f"  - Composite dropped more than 2% ({b_scores['composite']:.1f}% → {n_scores['composite']:.1f}%)")
        if n_scores['appropriateness'] < b_scores['appropriateness'] - 5:
            print(f"  - Appropriateness dropped more than 5% ({b_scores['appropriateness']:.1f}% → {n_scores['appropriateness']:.1f}%)")
        print()
        return 1
    elif improvement:
        print("✅ IMPROVEMENT DETECTED!")
        print()
        print("Quality improvements:")
        for metric in metrics:
            delta = n_scores[metric] - b_scores[metric]
            if delta >= 5:
                print(f"  - {metric.capitalize()}: +{delta:.1f}% ({b_scores[metric]:.1f}% → {n_scores[metric]:.1f}%)")
        print()
        print("🎉 Safe to commit - quality improved!")
        return 0
    else:
        print("✅ Quality score acceptable - no significant regression")
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python3 compare_scores.py baseline.json new.json")
        print()
        print("Example:")
        print("  python3 compare_scores.py baseline_before.json baseline_after.json")
        sys.exit(1)

    result = compare_scores(sys.argv[1], sys.argv[2])
    sys.exit(result)


if __name__ == '__main__':
    main()
