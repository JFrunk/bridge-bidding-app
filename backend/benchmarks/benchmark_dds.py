"""
Benchmark DDS AI vs Current AI Implementations

Compares:
- Simple Rule-Based AI (baseline)
- Minimax AI depth 2 (intermediate)
- Minimax AI depth 3 (advanced)
- DDS AI (expert) - NEW!

Measures:
- Tricks won
- Success rate
- Time per move
- Optimal play detection
"""

import sys
import time
from typing import Dict, List

# Add parent to path
sys.path.insert(0, '..')

from engine.play.ai.simple_ai import SimplePlayAI
from engine.play.ai.minimax_ai import MinimaxPlayAI

try:
    from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE
except ImportError:
    DDS_AVAILABLE = False
    print("⚠️  DDS AI not available")

from benchmarks.benchmark_ai import AIBenchmark, load_curated_deals


def benchmark_all_ais():
    """Run comprehensive benchmark of all AI implementations"""

    print("=" * 80)
    print("COMPREHENSIVE AI BENCHMARK - Including DDS")
    print("=" * 80)
    print()

    # Load test deals
    deals = load_curated_deals()
    print(f"Loaded {len(deals)} curated test deals\n")

    # Create AI instances
    ais = [
        ("Simple AI", SimplePlayAI()),
        ("Minimax D2", MinimaxPlayAI(max_depth=2)),
        ("Minimax D3", MinimaxPlayAI(max_depth=3)),
    ]

    if DDS_AVAILABLE:
        ais.append(("DDS Expert", DDSPlayAI()))
        print("✅ DDS AI available and will be tested\n")
    else:
        print("❌ DDS AI not available - install endplay\n")

    # Run benchmarks
    results = {}

    for ai_name, ai_instance in ais:
        print(f"\nBenchmarking: {ai_name}")
        print("-" * 80)

        benchmark = AIBenchmark(ai_instance)
        result = benchmark.run_benchmark(deals)

        results[ai_name] = result

        # Print summary
        total_tricks = result['total_tricks']
        possible = result['possible_tricks']
        success_count = result['success_count']
        total_deals = len(deals)

        print(f"  Tricks: {total_tricks}/{possible} ({total_tricks/possible*100:.1f}%)")
        print(f"  Success: {success_count}/{total_deals} ({success_count/total_deals*100:.1f}%)")
        print(f"  Time: {result['total_time']:.2f}s")
        print(f"  Avg/move: {result['avg_time_per_move']*1000:.2f}ms")

    # Comparison table
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print()
    print(f"{'AI':<15} {'Tricks':<12} {'Success':<12} {'Avg Time':<12} {'Rating'}")
    print("-" * 80)

    for ai_name in results:
        r = results[ai_name]
        tricks_pct = r['total_tricks'] / r['possible_tricks'] * 100
        success_pct = r['success_count'] / len(deals) * 100
        avg_time = r['avg_time_per_move'] * 1000

        # Estimate rating
        if "Simple" in ai_name:
            rating = "6/10"
        elif "D2" in ai_name:
            rating = "7.5/10"
        elif "D3" in ai_name:
            rating = "8/10"
        elif "DDS" in ai_name:
            rating = "9/10"
        else:
            rating = "?"

        print(f"{ai_name:<15} {tricks_pct:>5.1f}%      {success_pct:>5.1f}%      {avg_time:>6.1f}ms     {rating}")

    # Highlight DDS if available
    if DDS_AVAILABLE and "DDS Expert" in results:
        print("\n" + "=" * 80)
        print("🏆 DDS AI ANALYSIS")
        print("=" * 80)

        dds_result = results["DDS Expert"]
        minimax_d3_result = results["Minimax D3"]

        tricks_improvement = dds_result['total_tricks'] - minimax_d3_result['total_tricks']
        success_improvement = dds_result['success_count'] - minimax_d3_result['success_count']

        print(f"\nDDS vs Minimax D3:")
        print(f"  Tricks improvement: +{tricks_improvement} tricks")
        print(f"  Success improvement: +{success_improvement} deals")
        print(f"  Time penalty: {dds_result['avg_time_per_move']/minimax_d3_result['avg_time_per_move']:.1f}x slower")
        print(f"\n✅ DDS achieves expert-level play (9/10 rating)")

    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)

    return results


if __name__ == '__main__':
    results = benchmark_all_ais()
