#!/usr/bin/env python3
"""
Quick Baseline Status Checker
Usage: python3 quick_baseline_check.py [--csv] [--json]
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
BOLD = '\033[1m'
NC = '\033[0m'  # No Color

# Current baseline files
BIDDING_BASELINE = "quality_scores/baseline_20251030_145945.json"
PLAY_BASELINE = "quality_scores/play_baseline_20251030_151213.json"


def load_baseline(filepath):
    """Load baseline JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def display_bidding_status():
    """Display current bidding baseline status."""
    print(f"\n{BLUE}{BOLD}📊 BIDDING QUALITY BASELINE{NC}")
    print("=" * 80)

    baseline = load_baseline(BIDDING_BASELINE)

    if not baseline:
        print(f"{RED}❌ Baseline file not found: {BIDDING_BASELINE}{NC}")
        return

    # Extract key data from actual JSON structure
    timestamp = baseline.get('timestamp', 'Unknown')
    scores_section = baseline.get('scores', {})
    total_hands = scores_section.get('total_hands', 'N/A')
    total_bids = scores_section.get('total_bids', 'N/A')
    scores = scores_section.get('scores', {})
    error_counts = scores_section.get('error_counts', {})

    composite = scores.get('composite', 0)

    # Determine grade
    if composite >= 95:
        grade = 'A'
    elif composite >= 90:
        grade = 'B'
    elif composite >= 80:
        grade = 'C'
    elif composite >= 70:
        grade = 'D'
    else:
        grade = 'F'

    print(f"\n{BOLD}Composite Score: {composite:.1f}% (Grade {grade}){NC}")
    print(f"Date: {timestamp}")
    print(f"Test: {total_hands} hands, {total_bids} bids")
    print(f"File: {BIDDING_BASELINE}")

    print(f"\n{BOLD}Breakdown:{NC}")

    # Display individual scores
    for metric_name, metric_label in [
        ('legality', 'Legality'),
        ('appropriateness', 'Appropriateness'),
        ('conventions', 'Conventions'),
        ('reasonableness', 'Reasonableness'),
        ('game_slam', 'Game/Slam')
    ]:
        score = scores.get(metric_name, 0)
        errors = error_counts.get(metric_name, 0)

        # Status indicator
        if score >= 95:
            status = f"{GREEN}✅{NC}"
        elif score >= 90:
            status = f"{YELLOW}⚠️ {NC}"
        else:
            status = f"{RED}❌{NC}"

        print(f"  {status} {metric_label:18s} {score:6.1f}%  ({errors} errors)")

    # Production readiness
    print(f"\n{BOLD}Production Readiness:{NC}")

    checks = [
        (scores.get('legality', 0) == 100, "Legality: 100%"),
        (scores.get('appropriateness', 0) >= 95, "Appropriateness: ≥95%"),
        (scores.get('conventions', 0) >= 98, "Conventions: ≥98%"),
        (composite >= 95, "Composite: ≥95%")
    ]

    passed = sum(1 for check, _ in checks if check)

    for check, label in checks:
        icon = f"{GREEN}✅{NC}" if check else f"{RED}❌{NC}"
        print(f"  {icon} {label}")

    if passed == len(checks):
        print(f"\n{GREEN}{BOLD}✅ PRODUCTION READY{NC}")
    elif passed >= len(checks) - 1:
        print(f"\n{YELLOW}{BOLD}⚠️  NEAR PRODUCTION READY (needs minor fixes){NC}")
    else:
        print(f"\n{RED}{BOLD}❌ NOT PRODUCTION READY{NC}")


def display_play_status():
    """Display current play baseline status."""
    print(f"\n{BLUE}{BOLD}🃏 PLAY QUALITY BASELINE{NC}")
    print("=" * 80)

    baseline = load_baseline(PLAY_BASELINE)

    if not baseline:
        print(f"{RED}❌ Baseline file not found: {PLAY_BASELINE}{NC}")
        return

    # Extract key data from actual JSON structure
    timestamp = baseline.get('timestamp', 'Unknown')
    scores_section = baseline.get('scores', {})
    ai_type = scores_section.get('ai_type', 'Unknown')
    depth = scores_section.get('depth', 'N/A')
    total_hands = scores_section.get('total_hands', 'N/A')
    total_contracts = scores_section.get('total_contracts', 'N/A')
    contracts_made = scores_section.get('contracts_made', 0)
    contracts_failed = scores_section.get('contracts_failed', 0)
    overtricks = scores_section.get('overtricks', 0)
    undertricks = scores_section.get('undertricks', 0)
    scores = scores_section.get('scores', {})

    composite = scores.get('composite', 0)

    # Determine grade
    if composite >= 95:
        grade = 'A'
    elif composite >= 90:
        grade = 'B'
    elif composite >= 80:
        grade = 'C'
    elif composite >= 70:
        grade = 'D'
    else:
        grade = 'F'

    print(f"\n{BOLD}Composite Score: {composite:.1f}% (Grade {grade}){NC}")
    print(f"Date: {timestamp}")
    print(f"AI: {ai_type.upper()} (depth {depth})")
    print(f"Test: {total_hands} hands, {total_contracts} contracts")
    print(f"File: {PLAY_BASELINE}")

    print(f"\n{BOLD}Breakdown:{NC}")

    # Display individual scores
    for metric_name, metric_label in [
        ('legality', 'Legality'),
        ('success_rate', 'Success Rate'),
        ('efficiency', 'Efficiency'),
        ('tactical', 'Tactical'),
        ('timing', 'Timing')
    ]:
        score = scores.get(metric_name, 0)

        # Status indicator
        if score >= 95:
            status = f"{GREEN}✅{NC}"
        elif score >= 80:
            status = f"{YELLOW}⚠️ {NC}"
        else:
            status = f"{RED}❌{NC}"

        print(f"  {status} {metric_label:18s} {score:6.1f}%")

    # Contract stats
    success_pct = (contracts_made / total_contracts * 100) if total_contracts > 0 else 0

    print(f"\n{BOLD}Performance:{NC}")
    print(f"  Contracts Made: {contracts_made}/{total_contracts} ({success_pct:.1f}%)")
    print(f"  Overtricks: {overtricks}")
    print(f"  Undertricks: {undertricks}")


def display_csv_format():
    """Display baseline data in CSV format."""
    print("\nTimestamp,System,Composite,Grade,Legality,Key_Metric,Status")

    bidding = load_baseline(BIDDING_BASELINE)
    if bidding:
        timestamp = bidding.get('timestamp', 'Unknown')
        scores_section = bidding.get('scores', {})
        scores = scores_section.get('scores', {})
        composite = scores.get('composite', 0)
        grade = 'A' if composite >= 95 else 'B' if composite >= 90 else 'C' if composite >= 80 else 'D' if composite >= 70 else 'F'
        print(f"{timestamp},"
              f"Bidding,"
              f"{composite:.1f},"
              f"{grade},"
              f"{scores.get('legality', 0):.1f},"
              f"{scores.get('appropriateness', 0):.1f},"
              f"{'READY' if composite >= 95 else 'NEAR_READY'}")

    play = load_baseline(PLAY_BASELINE)
    if play:
        timestamp = play.get('timestamp', 'Unknown')
        scores_section = play.get('scores', {})
        scores = scores_section.get('scores', {})
        composite = scores.get('composite', 0)
        grade = 'A' if composite >= 95 else 'B' if composite >= 90 else 'C' if composite >= 80 else 'D' if composite >= 70 else 'F'
        print(f"{timestamp},"
              f"Play,"
              f"{composite:.1f},"
              f"{grade},"
              f"{scores.get('legality', 0):.1f},"
              f"{scores.get('success_rate', 0):.1f},"
              f"{'READY' if composite >= 80 else 'NOT_READY'}")


def display_json_format():
    """Display baseline data in JSON format."""
    data = {
        "last_updated": datetime.now().isoformat(),
        "bidding": {},
        "play": {}
    }

    bidding = load_baseline(BIDDING_BASELINE)
    if bidding:
        scores_section = bidding.get('scores', {})
        scores = scores_section.get('scores', {})
        composite = scores.get('composite', 0)
        grade = 'A' if composite >= 95 else 'B' if composite >= 90 else 'C' if composite >= 80 else 'D' if composite >= 70 else 'F'
        data["bidding"] = {
            "composite": composite,
            "grade": grade,
            "timestamp": bidding.get('timestamp', 'Unknown'),
            "production_ready": composite >= 95,
            "legality": scores.get('legality', 0),
            "appropriateness": scores.get('appropriateness', 0),
            "conventions": scores.get('conventions', 0)
        }

    play = load_baseline(PLAY_BASELINE)
    if play:
        scores_section = play.get('scores', {})
        scores = scores_section.get('scores', {})
        composite = scores.get('composite', 0)
        grade = 'A' if composite >= 95 else 'B' if composite >= 90 else 'C' if composite >= 80 else 'D' if composite >= 70 else 'F'
        data["play"] = {
            "composite": composite,
            "grade": grade,
            "timestamp": play.get('timestamp', 'Unknown'),
            "production_ready": composite >= 80,
            "legality": scores.get('legality', 0),
            "success_rate": scores.get('success_rate', 0),
            "efficiency": scores.get('efficiency', 0)
        }

    print(json.dumps(data, indent=2))


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--csv':
            display_csv_format()
            return
        elif sys.argv[1] == '--json':
            display_json_format()
            return
        elif sys.argv[1] == '--help':
            print("Usage: python3 quick_baseline_check.py [--csv] [--json]")
            print("\nOptions:")
            print("  (none)   Display full status with colors")
            print("  --csv    Output in CSV format")
            print("  --json   Output in JSON format")
            print("  --help   Show this help")
            return

    # Default: display full status
    display_bidding_status()
    display_play_status()

    print("\n" + "=" * 80)
    print(f"\n{BOLD}For detailed documentation, see:{NC}")
    print("  - BASELINE_SCORES.md (quick reference)")
    print("  - quality_scores/README.md (full history)")
    print("  - ./check_baseline_status.sh (shell script)")
    print()


if __name__ == '__main__':
    main()
