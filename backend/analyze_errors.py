#!/usr/bin/env python3
"""
Error Analysis Script

Analyzes error logs to identify patterns and recurring issues in bidding/play functionality.

Usage:
    python3 analyze_errors.py                 # Show error summary
    python3 analyze_errors.py --recent 20     # Show 20 most recent errors
    python3 analyze_errors.py --patterns      # Show error patterns
    python3 analyze_errors.py --category bidding_logic  # Filter by category
"""

import json
import argparse
from pathlib import Path
from utils.error_logger import error_logger, get_recent_errors, detect_error_patterns, get_error_summary


def print_error_summary():
    """Print overall error summary statistics"""
    summary = get_error_summary()

    print("\n" + "="*80)
    print("ERROR SUMMARY")
    print("="*80)

    print(f"\nTotal Errors: {summary['total_errors']}")

    if summary['by_category']:
        print("\n--- Errors by Category ---")
        sorted_categories = sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories:
            print(f"  {category:20s}: {count:4d}")

    if summary['by_endpoint']:
        print("\n--- Errors by Endpoint ---")
        sorted_endpoints = sorted(summary['by_endpoint'].items(), key=lambda x: x[1], reverse=True)
        for endpoint, count in sorted_endpoints[:10]:  # Top 10
            print(f"  {endpoint:40s}: {count:4d}")

    print("\n" + "="*80)


def print_recent_errors(limit=10):
    """Print most recent errors with details"""
    errors = get_recent_errors(limit)

    print("\n" + "="*80)
    print(f"RECENT ERRORS (Last {limit})")
    print("="*80)

    for i, error in enumerate(errors, 1):
        print(f"\n[{i}] {error.get('timestamp', 'N/A')}")
        print(f"    Category: {error.get('category', 'unknown')}")
        print(f"    Type: {error.get('error_type', 'unknown')}")
        print(f"    Message: {error.get('error_message', 'N/A')}")
        print(f"    Endpoint: {error.get('endpoint', 'N/A')}")
        print(f"    User: {error.get('user_id', 'N/A')}")
        print(f"    Hash: {error.get('error_hash', 'N/A')}")

        # Show context if available
        context = error.get('context', {})
        if context:
            print(f"    Context:")
            for key, value in context.items():
                print(f"      - {key}: {value}")

    print("\n" + "="*80)


def print_error_patterns():
    """Print detected error patterns"""
    patterns = detect_error_patterns()

    print("\n" + "="*80)
    print("ERROR PATTERNS DETECTED")
    print("="*80)

    # High frequency errors
    if patterns['high_frequency_errors']:
        print("\n--- High Frequency Errors (>10 occurrences) ---")
        for error in patterns['high_frequency_errors']:
            print(f"\n  Hash: {error['hash']}")
            print(f"    Count: {error['count']}")
            print(f"    First seen: {error['first_seen']}")
            print(f"    Last seen: {error['last_seen']}")
    else:
        print("\n✅ No high frequency errors detected")

    # Critical endpoints
    if patterns['critical_endpoints']:
        print("\n--- Critical Endpoints (>5 errors) ---")
        for endpoint_data in patterns['critical_endpoints']:
            print(f"  {endpoint_data['endpoint']:40s}: {endpoint_data['error_count']} errors")
    else:
        print("\n✅ No critical endpoints detected")

    print("\n" + "="*80)


def print_errors_by_category(category):
    """Print all errors for a specific category"""
    errors = get_recent_errors(limit=1000)  # Get all errors
    filtered = [e for e in errors if e.get('category') == category]

    print("\n" + "="*80)
    print(f"ERRORS IN CATEGORY: {category}")
    print("="*80)

    if not filtered:
        print(f"\n✅ No errors found in category '{category}'")
        print("\n" + "="*80)
        return

    print(f"\nFound {len(filtered)} errors")

    for i, error in enumerate(filtered[:20], 1):  # Show first 20
        print(f"\n[{i}] {error.get('timestamp', 'N/A')}")
        print(f"    Type: {error.get('error_type', 'unknown')}")
        print(f"    Message: {error.get('error_message', 'N/A')}")
        print(f"    Endpoint: {error.get('endpoint', 'N/A')}")
        print(f"    Hash: {error.get('error_hash', 'N/A')}")

    if len(filtered) > 20:
        print(f"\n... and {len(filtered) - 20} more")

    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="Analyze bidding/play errors")
    parser.add_argument('--recent', type=int, help="Show N most recent errors")
    parser.add_argument('--patterns', action='store_true', help="Show error patterns")
    parser.add_argument('--category', type=str, help="Filter by category (bidding_logic, play_engine, etc.)")

    args = parser.parse_args()

    # Check if error logs exist
    log_dir = Path(__file__).parent / 'logs'
    if not log_dir.exists() or not list(log_dir.glob('*.json*')):
        print("\n✅ No errors logged yet - system is running clean!")
        print("\nError logs will appear in backend/logs/ when errors occur.")
        return

    if args.recent:
        print_recent_errors(args.recent)
    elif args.patterns:
        print_error_patterns()
    elif args.category:
        print_errors_by_category(args.category)
    else:
        # Default: show summary
        print_error_summary()

        # Also show patterns if any high-frequency errors exist
        patterns = detect_error_patterns()
        if patterns['high_frequency_errors'] or patterns['critical_endpoints']:
            print("\n⚠️  Issues detected! Run with --patterns for details\n")


if __name__ == '__main__':
    main()
