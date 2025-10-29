#!/usr/bin/env python3
"""
AI Levels Baseline Testing

Tests all AI difficulty levels to establish baseline performance metrics.
Tests both bidding and play quality for each AI level.

Usage:
    python3 test_ai_levels_baseline.py --hands 500
    python3 test_ai_levels_baseline.py --hands 100 --fast
    python3 test_ai_levels_baseline.py --level 8  # Test specific level only
"""

import json
import argparse
import sys
import os
import subprocess
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_ai_level(level: int, num_hands: int, output_dir: str = "ai_baselines"):
    """Test a specific AI level for both bidding and play."""
    print()
    print("=" * 80)
    print(f"TESTING AI LEVEL {level}/10")
    print("=" * 80)
    print()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Determine AI configuration for this level
    ai_config = get_ai_config(level)

    results = {
        'level': level,
        'timestamp': datetime.now().isoformat(),
        'num_hands': num_hands,
        'ai_config': ai_config
    }

    # Test bidding quality
    print(f"📊 Testing BIDDING quality for level {level}/10...")
    print(f"   Configuration: {ai_config['bidding']['description']}")
    print()

    bidding_output = f"{output_dir}/bidding_level_{level}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        result = subprocess.run([
            'python3', 'backend/test_bidding_quality_score.py',
            '--hands', str(num_hands),
            '--output', bidding_output
        ], capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            with open(bidding_output) as f:
                results['bidding'] = json.load(f)['scores']
            print(f"✅ Bidding test complete: {results['bidding']['scores']['composite']:.1f}%")
        else:
            print(f"⚠️  Bidding test had issues: {result.stderr}")
            results['bidding'] = None
    except Exception as e:
        print(f"❌ Bidding test failed: {e}")
        results['bidding'] = None

    # Test play quality
    print()
    print(f"🎴 Testing PLAY quality for level {level}/10...")
    print(f"   Configuration: {ai_config['play']['description']}")
    print()

    play_output = f"{output_dir}/play_level_{level}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        cmd = [
            'python3', 'backend/test_play_quality_score.py',
            '--hands', str(num_hands),
            '--ai', ai_config['play']['type'],
            '--output', play_output
        ]

        if ai_config['play']['type'] == 'minimax':
            cmd.extend(['--depth', str(ai_config['play']['depth'])])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

        if result.returncode == 0:
            with open(play_output) as f:
                results['play'] = json.load(f)['scores']
            print(f"✅ Play test complete: {results['play']['scores']['composite']:.1f}%")
        else:
            print(f"⚠️  Play test had issues: {result.stderr}")
            results['play'] = None
    except Exception as e:
        print(f"❌ Play test failed: {e}")
        results['play'] = None

    # Calculate combined score
    if results['bidding'] and results['play']:
        combined_score = (
            results['bidding']['scores']['composite'] * 0.5 +
            results['play']['scores']['composite'] * 0.5
        )
        results['combined_score'] = round(combined_score, 1)
        results['grade'] = get_combined_grade(combined_score)
    else:
        results['combined_score'] = None
        results['grade'] = 'Incomplete'

    # Save combined results
    combined_output = f"{output_dir}/ai_level_{level}_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(combined_output, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print(f"📄 Combined results saved to: {combined_output}")

    return results


def get_ai_config(level: int) -> dict:
    """Get AI configuration for a given difficulty level."""
    configs = {
        1: {  # Beginner
            'bidding': {'description': 'Basic SAYC, simple bidding', 'complexity': 'low'},
            'play': {'type': 'simple', 'description': 'Simple card play', 'depth': None}
        },
        2: {  # Novice
            'bidding': {'description': 'Basic SAYC, simple bidding', 'complexity': 'low'},
            'play': {'type': 'simple', 'description': 'Simple card play', 'depth': None}
        },
        3: {  # Easy
            'bidding': {'description': 'Standard SAYC', 'complexity': 'standard'},
            'play': {'type': 'minimax', 'description': 'Minimax depth 1', 'depth': 1}
        },
        4: {  # Intermediate-
            'bidding': {'description': 'Standard SAYC', 'complexity': 'standard'},
            'play': {'type': 'minimax', 'description': 'Minimax depth 1', 'depth': 1}
        },
        5: {  # Intermediate
            'bidding': {'description': 'Standard SAYC', 'complexity': 'standard'},
            'play': {'type': 'minimax', 'description': 'Minimax depth 2', 'depth': 2}
        },
        6: {  # Intermediate+
            'bidding': {'description': 'Standard SAYC', 'complexity': 'standard'},
            'play': {'type': 'minimax', 'description': 'Minimax depth 2', 'depth': 2}
        },
        7: {  # Advanced-
            'bidding': {'description': 'Standard SAYC with conventions', 'complexity': 'standard'},
            'play': {'type': 'minimax', 'description': 'Minimax depth 2', 'depth': 2}
        },
        8: {  # Advanced (8/10 - your current level)
            'bidding': {'description': 'Standard SAYC with all conventions', 'complexity': 'full'},
            'play': {'type': 'minimax', 'description': 'Minimax depth 2-3', 'depth': 2}
        },
        9: {  # Expert- (production with DDS)
            'bidding': {'description': 'Standard SAYC with all conventions', 'complexity': 'full'},
            'play': {'type': 'dds', 'description': 'DDS (Double Dummy Solver)', 'depth': None}
        },
        10: {  # Expert (production with DDS)
            'bidding': {'description': 'Standard SAYC with all conventions + advanced judgment', 'complexity': 'expert'},
            'play': {'type': 'dds', 'description': 'DDS (Double Dummy Solver)', 'depth': None}
        }
    }

    return configs.get(level, configs[8])  # Default to level 8


def get_combined_grade(score: float) -> str:
    """Get grade for combined score."""
    if score >= 95:
        return 'A (Excellent)'
    elif score >= 90:
        return 'B (Good)'
    elif score >= 85:
        return 'C (Acceptable)'
    elif score >= 80:
        return 'D (Poor)'
    else:
        return 'F (Failing)'


def print_summary(all_results: list):
    """Print summary of all AI levels tested."""
    print()
    print("=" * 80)
    print("AI LEVELS BASELINE SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Level':<8} {'Bidding':>10} {'Play':>10} {'Combined':>10} {'Grade':<20}")
    print("-" * 80)

    for result in sorted(all_results, key=lambda x: x['level']):
        level = result['level']

        if result['bidding']:
            bidding_score = f"{result['bidding']['scores']['composite']:.1f}%"
        else:
            bidding_score = "N/A"

        if result['play']:
            play_score = f"{result['play']['scores']['composite']:.1f}%"
        else:
            play_score = "N/A"

        if result['combined_score']:
            combined_score = f"{result['combined_score']:.1f}%"
            grade = result['grade']
        else:
            combined_score = "N/A"
            grade = "Incomplete"

        print(f"{level}/10{'':<4} {bidding_score:>10} {play_score:>10} {combined_score:>10} {grade:<20}")

    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='AI Levels Baseline Testing')
    parser.add_argument('--hands', type=int, default=500, help='Number of hands to test per level (default: 500)')
    parser.add_argument('--fast', action='store_true', help='Fast mode (100 hands)')
    parser.add_argument('--level', type=int, choices=range(1, 11), help='Test specific level only (1-10)')
    parser.add_argument('--output-dir', type=str, default='ai_baselines', help='Output directory')

    args = parser.parse_args()

    num_hands = 100 if args.fast else args.hands

    # Determine which levels to test
    if args.level:
        levels_to_test = [args.level]
    else:
        # By default, test key levels: 1, 3, 5, 8, 9 (if DDS available)
        levels_to_test = [1, 3, 5, 8]
        # Check if DDS is available for level 9
        try:
            from engine.play.ai.dds_ai import DDS_AVAILABLE
            if DDS_AVAILABLE:
                levels_to_test.append(9)
                print("✅ DDS available - will test level 9 (Expert)")
            else:
                print("⚠️  DDS not available - skipping level 9")
        except:
            print("⚠️  DDS not available - skipping level 9")

    print()
    print("=" * 80)
    print("AI LEVELS BASELINE TESTING")
    print("=" * 80)
    print()
    print(f"Testing levels: {', '.join(str(l) for l in levels_to_test)}")
    print(f"Hands per level: {num_hands}")
    print(f"Output directory: {args.output_dir}")
    print()

    all_results = []

    for level in levels_to_test:
        try:
            result = test_ai_level(level, num_hands, args.output_dir)
            all_results.append(result)
        except Exception as e:
            print(f"❌ Error testing level {level}: {e}")
            continue

    # Print summary
    if all_results:
        print_summary(all_results)

        # Save master summary
        summary_file = f"{args.output_dir}/baseline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'num_hands': num_hands,
                'levels_tested': levels_to_test,
                'results': all_results
            }, f, indent=2)

        print()
        print(f"📄 Master summary saved to: {summary_file}")
        print()

        return 0
    else:
        print("❌ No results to report")
        return 1


if __name__ == '__main__':
    exit(main())
