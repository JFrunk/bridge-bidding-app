#!/usr/bin/env python3
"""
CSS Responsive Design Checker

Scans CSS files for common responsive design issues that cause
overflow problems on narrow screens (360px and below).

Run: python3 .claude/scripts/check_responsive_css.py [--verbose]
"""

import os
import re
import sys
import argparse
from pathlib import Path

# Patterns that often cause mobile overflow issues
PROBLEMATIC_PATTERNS = [
    {
        "name": "Fixed min-width over 300px",
        "pattern": r"^\s*min-width:\s*(\d{3,})px",
        "check": lambda m: int(m.group(1)) > 300,
        "suggestion": "Use min-width: min({value}px, 100%) instead",
        "severity": "error",
        "skip_in_media_query": True
    },
    {
        "name": "Fixed max-width over viewport",
        "pattern": r"max-width:\s*(\d{4,})px",
        "check": lambda m: int(m.group(1)) > 1200,
        "suggestion": "Consider using max-width: min({value}px, 100vw - 20px)",
        "severity": "warning"
    },
    {
        "name": "Fixed translateX animation",
        "pattern": r"translateX\(\s*(\d{3,})px\s*\)",
        "check": lambda m: int(m.group(1)) > 100,
        "suggestion": "Use translateX(100%) for responsive animations",
        "severity": "warning"
    },
    {
        "name": "Grid minmax without responsive fallback",
        "pattern": r"minmax\(\s*(\d{3,})px",
        "check": lambda m: int(m.group(1)) > 280 and "min(" not in m.group(0),
        "suggestion": "Use minmax(min({value}px, 100%), 1fr) for responsive grids",
        "severity": "error"
    },
    {
        "name": "Fixed width over 350px",
        "pattern": r"(?<!max-|min-)width:\s*(\d{3,})px",
        "check": lambda m: int(m.group(1)) > 350,
        "suggestion": "Consider using width: min({value}px, 100%) or max-width instead",
        "severity": "warning"
    }
]

# Files/patterns to skip
SKIP_PATTERNS = [
    "node_modules",
    ".min.css",
    "vendor",
    "build",
    "dist"
]

def should_skip(filepath: str) -> bool:
    """Check if file should be skipped."""
    return any(pattern in filepath for pattern in SKIP_PATTERNS)

def check_for_360_breakpoint(content: str) -> bool:
    """Check if file has a 360px breakpoint when it has grid/flex layouts."""
    has_grid_or_flex = re.search(r"(display:\s*(grid|flex)|grid-template-columns)", content)
    has_mobile_breakpoint = re.search(r"@media.*max-width:\s*(480|600|768)px", content)
    has_360_breakpoint = re.search(r"@media.*max-width:\s*360px", content)
    return has_grid_or_flex and has_mobile_breakpoint and not has_360_breakpoint

def scan_file(filepath: str, verbose: bool = False) -> list:
    """Scan a single CSS file for responsive issues."""
    issues = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [{"file": filepath, "line": 0, "issue": f"Could not read file: {e}", "severity": "error"}]

    for pattern_info in PROBLEMATIC_PATTERNS:
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('/*') or line.strip().startswith('//'):
                continue
            if 'min(' in line and pattern_info["name"] != "Grid minmax without responsive fallback":
                continue
            if pattern_info.get("skip_in_media_query") and '@media' in line:
                continue

            matches = re.finditer(pattern_info["pattern"], line)
            for match in matches:
                if pattern_info["check"](match):
                    value = match.group(1)
                    issues.append({
                        "file": filepath,
                        "line": i,
                        "issue": pattern_info["name"],
                        "found": match.group(0),
                        "suggestion": pattern_info["suggestion"].format(value=value),
                        "severity": pattern_info["severity"]
                    })

    if check_for_360_breakpoint(content):
        issues.append({
            "file": filepath,
            "line": 0,
            "issue": "Missing 360px breakpoint",
            "found": "Has 480px/600px breakpoint but no 360px",
            "suggestion": "Add @media (max-width: 360px) breakpoint for extra small phones",
            "severity": "warning"
        })

    return issues

def scan_directory(directory: str, verbose: bool = False) -> list:
    """Scan directory for CSS files and check each one."""
    all_issues = []
    css_files = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(root, d))]
        for file in files:
            if file.endswith('.css') and not should_skip(file):
                css_files.append(os.path.join(root, file))

    if verbose:
        print(f"Scanning {len(css_files)} CSS files...")

    for filepath in css_files:
        issues = scan_file(filepath, verbose)
        all_issues.extend(issues)

    return all_issues

def print_results(issues: list, verbose: bool = False) -> int:
    """Print results and return exit code."""
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    if not issues:
        print("\033[92m✅ No responsive design issues found!\033[0m")
        return 0

    print("\n\033[94m" + "=" * 60 + "\033[0m")
    print("\033[94mCSS Responsive Design Check Results\033[0m")
    print("\033[94m" + "=" * 60 + "\033[0m\n")

    by_file = {}
    for issue in issues:
        filepath = issue["file"]
        if filepath not in by_file:
            by_file[filepath] = []
        by_file[filepath].append(issue)

    for filepath, file_issues in by_file.items():
        rel_path = os.path.relpath(filepath)
        print(f"\n\033[1m{rel_path}\033[0m")

        for issue in file_issues:
            severity_color = "\033[91m" if issue["severity"] == "error" else "\033[93m"
            severity_icon = "❌" if issue["severity"] == "error" else "⚠️"
            line_info = f"Line {issue['line']}: " if issue["line"] > 0 else ""
            print(f"  {severity_icon} {severity_color}{line_info}{issue['issue']}\033[0m")
            if "found" in issue:
                print(f"     Found: {issue['found']}")
            print(f"     Fix: {issue['suggestion']}")

    print("\n" + "=" * 60)
    print(f"\033[91mErrors: {len(errors)}\033[0m")
    print(f"\033[93mWarnings: {len(warnings)}\033[0m")

    if errors:
        print("\n\033[91m❌ Responsive design check FAILED!\033[0m")
        print("Fix errors before committing CSS changes.")
        return 1
    elif warnings:
        print("\n\033[93m⚠️ Responsive design check passed with warnings.\033[0m")
        return 0

    return 0

def main():
    parser = argparse.ArgumentParser(description="Check CSS for responsive design issues")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--path", "-p", default="frontend/src", help="Path to scan")
    parser.add_argument("--file", "-f", help="Check a single file")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    os.chdir(project_root)

    if args.file:
        issues = scan_file(args.file, args.verbose)
    else:
        issues = scan_directory(args.path, args.verbose)

    return print_results(issues, args.verbose)

if __name__ == "__main__":
    sys.exit(main())
