#!/usr/bin/env python3
"""
Compare two play quality score reports.

Usage:
    python3 compare_play_scores.py baseline.json new.json
"""
import json
import sys


def compare_play_scores(baseline_file, new_file):
    """Compare two play quality score reports and detect regressions."""
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
    b_stats = baseline['scores']
    n_stats = new['scores']

    print("=" * 80)
    print("PLAY QUALITY SCORE COMPARISON")
    print("=" * 80)
    print()
    print(f"Baseline: {baseline_file}")
    print(f"New:      {new_file}")
    print()
    print(f"Baseline AI: {b_stats['ai_type'].upper()}{f\" (depth {b_stats['depth']})\" if b_stats.get('depth') else ''}")
    print(f"New AI:      {n_stats['ai_type'].upper()}{f\" (depth {n_stats['depth']})\" if n_stats.get('depth') else ''}")
    print()
    print(f"Baseline: {b_stats['total_hands']} hands, {b_stats['contracts_played']} contracts")
    print(f"New:      {n_stats['total_hands']} hands, {n_stats['contracts_played']} contracts")
    print()
    print("-" * 80)
    print(f"{'Metric':<20} {'Baseline':>10} {'New':>10} {'Delta':>10} {'Status':>10}")
    print("-" * 80)

    metrics = ['legality', 'success_rate', 'efficiency', 'tactical', 'timing', 'composite']
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
        elif metric == 'success_rate' and delta < -5:
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

        metric_display = metric.replace('_', ' ').capitalize()
        print(f"{metric_display:<20} {baseline_score:>9.1f}% {new_score:>9.1f}% {delta:>+9.1f}% {status:>10}")

    print("-" * 80)
    print()

    # Performance metrics comparison
    print("-" * 80)
    print(f"{'Performance':<20} {'Baseline':>10} {'New':>10} {'Delta':>10}")
    print("-" * 80)

    # Contracts made
    b_made_pct = (b_stats['contracts_made'] / max(1, b_stats['contracts_played']) * 100)
    n_made_pct = (n_stats['contracts_made'] / max(1, n_stats['contracts_played']) * 100)
    delta_made = n_made_pct - b_made_pct

    print(f"{'Contracts Made %':<20} {b_made_pct:>9.1f}% {n_made_pct:>9.1f}% {delta_made:>+9.1f}%")

    # Overtricks
    b_over = b_stats['overtricks']
    n_over = n_stats['overtricks']
    delta_over = n_over - b_over

    print(f"{'Overtricks':<20} {b_over:>10d} {n_over:>10d} {delta_over:>+10d}")

    # Undertricks
    b_under = b_stats['undertricks']
    n_under = n_stats['undertricks']
    delta_under = n_under - b_under

    print(f"{'Undertricks':<20} {b_under:>10d} {n_under:>10d} {delta_under:>+10d}")

    # Timing
    b_time = baseline['scores']['timing']['avg_time_per_hand']
    n_time = new['scores']['timing']['avg_time_per_hand']
    delta_time = n_time - b_time

    print(f"{'Avg Time/Hand (s)':<20} {b_time:>10.3f} {n_time:>10.3f} {delta_time:>+10.3f}")

    print("-" * 80)
    print()

    # Grade comparison
    b_grade = b_stats['grade']
    n_grade = n_stats['grade']

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
        if n_scores['success_rate'] < b_scores['success_rate'] - 5:
            print(f"  - Success rate dropped more than 5% ({b_scores['success_rate']:.1f}% → {n_scores['success_rate']:.1f}%)")
        if n_time > b_time * 1.5:
            print(f"  - Timing increased more than 50% ({b_time:.3f}s → {n_time:.3f}s)")
        print()
        return 1
    elif improvement:
        print("✅ IMPROVEMENT DETECTED!")
        print()
        print("Quality improvements:")
        for metric in metrics:
            delta = n_scores[metric] - b_scores[metric]
            if delta >= 5:
                metric_display = metric.replace('_', ' ').capitalize()
                print(f"  - {metric_display}: +{delta:.1f}% ({b_scores[metric]:.1f}% → {n_scores[metric]:.1f}%)")
        print()
        print("🎉 Safe to commit - quality improved!")
        return 0
    else:
        print("✅ Quality score acceptable - no significant regression")
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python3 compare_play_scores.py baseline.json new.json")
        print()
        print("Example:")
        print("  python3 compare_play_scores.py play_baseline_before.json play_baseline_after.json")
        sys.exit(1)

    result = compare_play_scores(sys.argv[1], sys.argv[2])
    sys.exit(result)


if __name__ == '__main__':
    main()
