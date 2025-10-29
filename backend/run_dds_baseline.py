#!/usr/bin/env python3
"""
Run DDS baseline via web endpoint (for production servers without shell access)

This allows you to trigger DDS baseline testing via a web request
"""
import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the test framework
from test_play_quality_integrated import IntegratedPlayQualityScorer

def main():
    """Run DDS baseline and save results"""
    print("🎯 Starting DDS Baseline Test...")
    print(f"⏰ Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create scorer with DDS AI
    scorer = IntegratedPlayQualityScorer(ai_type='dds')

    # Run test (start with 10 hands to verify it works)
    num_hands = int(os.environ.get('DDS_TEST_HANDS', '10'))
    print(f"Testing {num_hands} hands with DDS AI...")

    results = scorer.run_full_test(num_hands=num_hands)

    # Save results
    output_file = f"dds_baseline_{num_hands}hands_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print(f"✅ Results saved to: {output_file}")
    print()

    # Print summary
    scores = results['scores']['scores']
    print("=" * 80)
    print(f"COMPOSITE SCORE: {scores['composite']:.1f}%")
    print(f"SUCCESS RATE: {scores['success_rate']:.1f}%")
    print(f"GRADE: {results['scores']['grade']}")
    print("=" * 80)

    return results

if __name__ == '__main__':
    main()
