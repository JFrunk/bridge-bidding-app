#!/usr/bin/env python3
"""
Generate V2 Schema Coverage Report

Creates a markdown report showing V2 schema coverage and areas for improvement.

Usage:
    python3 generate_coverage_report.py results_v2.json
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


def load_results(filepath: str) -> dict:
    """Load results from JSON file."""
    with open(filepath) as f:
        return json.load(f)


def generate_report(results: dict) -> str:
    """Generate markdown coverage report."""
    summary = results.get('summary', {})
    category_stats = results.get('category_stats', {})

    timestamp = results.get('timestamp', datetime.now().isoformat())

    # Calculate metrics
    total = summary.get('total', 0)
    passed = summary.get('matched_expected', 0)
    schema_hits = summary.get('schema_hits', 0)
    v1_fallbacks = summary.get('v1_fallbacks', 0)
    compliance_rate = summary.get('compliance_rate', 0)

    schema_coverage = schema_hits / max(1, total)

    # Grade
    if compliance_rate >= 0.8:
        grade = "A"
        grade_emoji = "🏆"
    elif compliance_rate >= 0.6:
        grade = "B"
        grade_emoji = "✅"
    elif compliance_rate >= 0.4:
        grade = "C"
        grade_emoji = "⚠️"
    elif compliance_rate >= 0.2:
        grade = "D"
        grade_emoji = "📈"
    else:
        grade = "F"
        grade_emoji = "🚧"

    report = f"""# V2 Schema Engine Coverage Report

**Generated:** {timestamp}
**Grade:** {grade_emoji} {grade} ({compliance_rate*100:.1f}%)

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {total} |
| Passed | {passed} ({compliance_rate*100:.1f}%) |
| Schema Hits | {schema_hits} ({schema_coverage*100:.1f}%) |
| V1 Fallbacks | {v1_fallbacks} |

## Schema Coverage Progress

```
Compliance:  {'█' * int(compliance_rate * 20)}{'░' * (20 - int(compliance_rate * 20))} {compliance_rate*100:.1f}%
Schema:      {'█' * int(schema_coverage * 20)}{'░' * (20 - int(schema_coverage * 20))} {schema_coverage*100:.1f}%
```

## Category Breakdown

"""

    # Sort categories by improvement priority (low pass rate + high volume)
    sorted_cats = sorted(
        category_stats.items(),
        key=lambda x: (x[1]['matched_expected'] / max(1, x[1]['total']), -x[1]['total'])
    )

    report += "| Category | Pass Rate | Schema Coverage | Tests |\n"
    report += "|----------|-----------|-----------------|-------|\n"

    for cat, stats in sorted_cats:
        total_cat = stats['total']
        passed_cat = stats['matched_expected']
        schema_cat = stats.get('schema_hits', 0)

        pass_rate = passed_cat / max(1, total_cat)
        schema_rate = schema_cat / max(1, total_cat)

        status = "✅" if pass_rate >= 0.8 else "⚠️" if pass_rate >= 0.5 else "❌"

        report += f"| {status} {cat} | {pass_rate*100:.0f}% | {schema_rate*100:.0f}% | {total_cat} |\n"

    # Priority improvements
    report += "\n## Priority Improvements\n\n"

    low_coverage_cats = [
        (cat, stats) for cat, stats in category_stats.items()
        if stats['matched_expected'] / max(1, stats['total']) < 0.5
    ]

    if low_coverage_cats:
        report += "Categories below 50% compliance:\n\n"
        for cat, stats in sorted(low_coverage_cats, key=lambda x: -x[1]['total']):
            total_cat = stats['total']
            passed_cat = stats['matched_expected']
            schema_cat = stats.get('schema_hits', 0)
            pass_rate = passed_cat / max(1, total_cat)
            schema_rate = schema_cat / max(1, total_cat)

            report += f"- **{cat}**: {pass_rate*100:.0f}% pass rate, {schema_rate*100:.0f}% schema coverage ({total_cat} tests)\n"

    else:
        report += "🎉 All categories above 50% compliance!\n"

    # Next steps
    report += "\n## Next Steps\n\n"
    report += """1. Focus on categories with lowest pass rates and highest test counts
2. Analyze failure patterns within each category
3. Add targeted rules to `sayc_*.json` schema files
4. Run category-specific tests to validate improvements
"""

    return report


def main():
    parser = argparse.ArgumentParser(description='Generate V2 schema coverage report')
    parser.add_argument('results_file', type=str, help='Path to results JSON')
    parser.add_argument('--output', type=str, default='coverage_report.md',
                        help='Output markdown file')

    args = parser.parse_args()

    # Load results
    results = load_results(args.results_file)

    # Generate report
    report = generate_report(results)

    # Write report
    with open(args.output, 'w') as f:
        f.write(report)

    print(f"Coverage report written to: {args.output}")
    print("\n" + "=" * 50)
    print(report)

    return 0


if __name__ == '__main__':
    sys.exit(main())
