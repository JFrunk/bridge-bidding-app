#!/usr/bin/env python3
"""
Filesystem Health Check
Run before commits to catch file system issues early

Usage:
    python3 .claude/scripts/check_filesystem_health.py
    python3 .claude/scripts/check_filesystem_health.py --verbose
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal output
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_MD_TARGET = 12
ROOT_MD_MAX = 15
ROOT_ITEMS_TARGET = 25
ROOT_ITEMS_MAX = 30

def count_root_md_files() -> Tuple[int, List[str]]:
    """Count markdown files at root level."""
    root_files = list(PROJECT_ROOT.glob("*.md"))
    return len(root_files), [f.name for f in root_files]

def count_root_items() -> int:
    """Count total items in root directory (excluding hidden)."""
    items = [item for item in PROJECT_ROOT.iterdir() if not item.name.startswith('.')]
    return len(items)

def find_temp_files() -> List[str]:
    """Find temporary files that shouldn't be in repo."""
    temp_patterns = ['*.log', '*.patch', '*.tmp', '*.temp', '.DS_Store']
    temp_files = []

    for pattern in temp_patterns:
        files = list(PROJECT_ROOT.rglob(pattern))
        # Exclude node_modules and venv
        files = [f for f in files if 'node_modules' not in str(f) and 'venv' not in str(f)]
        temp_files.extend([str(f.relative_to(PROJECT_ROOT)) for f in files])

    return temp_files

def count_cache_files() -> Tuple[int, int]:
    """Count Python cache files."""
    pyc_files = list(PROJECT_ROOT.rglob("*.pyc"))
    pycache_dirs = list(PROJECT_ROOT.rglob("__pycache__"))

    # Exclude venv
    pyc_files = [f for f in pyc_files if 'venv' not in str(f)]
    pycache_dirs = [d for d in pycache_dirs if 'venv' not in str(d)]

    return len(pyc_files), len(pycache_dirs)

def find_large_files(threshold_mb: float = 1.0) -> List[Tuple[str, float]]:
    """Find large files in repo (excluding node_modules, venv)."""
    large_files = []
    threshold_bytes = threshold_mb * 1024 * 1024

    for file in PROJECT_ROOT.rglob("*"):
        if file.is_file():
            # Skip excluded directories
            if any(excluded in str(file) for excluded in ['node_modules', 'venv', '.git']):
                continue

            try:
                size = file.stat().st_size
                if size > threshold_bytes:
                    size_mb = size / (1024 * 1024)
                    large_files.append((str(file.relative_to(PROJECT_ROOT)), size_mb))
            except (OSError, PermissionError):
                pass

    return large_files

def check_for_orphaned_dirs() -> List[str]:
    """Check for known orphaned directories."""
    orphaned_dirs = ['Documents', 'src', 'misc', 'old_code', 'temp', 'tmp']
    found = []

    for dirname in orphaned_dirs:
        dir_path = PROJECT_ROOT / dirname
        if dir_path.exists() and dir_path.is_dir():
            found.append(dirname)

    return found

def check_git_status() -> Tuple[bool, List[str]]:
    """Check if cache files are being tracked by git."""
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--cached'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return False, []

        tracked_files = result.stdout.split('\n')
        bad_files = []

        for file in tracked_files:
            if any(pattern in file for pattern in ['__pycache__', '.pyc', '.DS_Store', 'venv/']):
                bad_files.append(file)

        return True, bad_files
    except Exception:
        return False, []

def check_completion_docs_at_root() -> List[str]:
    """Check for *_COMPLETE.md or *_IMPLEMENTATION.md files at root."""
    root_files = list(PROJECT_ROOT.glob("*.md"))
    completion_docs = [
        f.name for f in root_files
        if '_COMPLETE.md' in f.name or '_IMPLEMENTATION.md' in f.name
    ]
    return completion_docs

def print_header(text: str):
    """Print section header."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_issue(severity: str, message: str):
    """Print an issue with appropriate color."""
    if severity == "ERROR":
        print(f"  {RED}❌ ERROR: {message}{RESET}")
    elif severity == "WARNING":
        print(f"  {YELLOW}⚠️  WARNING: {message}{RESET}")
    elif severity == "INFO":
        print(f"  {BLUE}ℹ️  INFO: {message}{RESET}")

def print_success(message: str):
    """Print a success message."""
    print(f"  {GREEN}✅ {message}{RESET}")

def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    print_header("🔍 Filesystem Health Check")

    issues = []
    warnings = []
    info_messages = []

    # Check 1: Root directory markdown count
    md_count, md_files = count_root_md_files()
    if md_count > ROOT_MD_MAX:
        issues.append(f"{md_count} MD files at root (critical threshold: >{ROOT_MD_MAX})")
    elif md_count > ROOT_MD_TARGET:
        warnings.append(f"{md_count} MD files at root (target: <{ROOT_MD_TARGET})")
    else:
        print_success(f"Root directory: {md_count} MD files (target: <{ROOT_MD_TARGET})")

    if verbose and md_count > ROOT_MD_TARGET:
        print(f"\n    Root MD files:")
        for fname in sorted(md_files):
            print(f"      - {fname}")

    # Check 2: Root directory item count
    root_items = count_root_items()
    if root_items > ROOT_ITEMS_MAX:
        issues.append(f"{root_items} items at root (critical threshold: >{ROOT_ITEMS_MAX})")
    elif root_items > ROOT_ITEMS_TARGET:
        warnings.append(f"{root_items} items at root (target: <{ROOT_ITEMS_TARGET})")
    else:
        print_success(f"Root items: {root_items} (target: <{ROOT_ITEMS_TARGET})")

    # Check 3: Temporary files
    temp_files = find_temp_files()
    if temp_files:
        warnings.append(f"{len(temp_files)} temporary file(s) found")
        if verbose:
            print(f"\n    Temporary files:")
            for fname in temp_files[:10]:  # Limit to first 10
                print(f"      - {fname}")
            if len(temp_files) > 10:
                print(f"      ... and {len(temp_files) - 10} more")
    else:
        print_success("No temporary files found")

    # Check 4: Python cache
    pyc_count, pycache_count = count_cache_files()
    total_cache = pyc_count + pycache_count
    if total_cache > 0:
        warnings.append(f"{pyc_count} .pyc files, {pycache_count} __pycache__ directories")
        info_messages.append("Run: git rm -r --cached `find . -name '__pycache__'`")
    else:
        print_success("No Python cache files found")

    # Check 5: Large files
    large_files = find_large_files(threshold_mb=1.0)
    if large_files:
        warnings.append(f"{len(large_files)} large file(s) >1MB in repo")
        if verbose:
            print(f"\n    Large files:")
            for fname, size_mb in large_files[:5]:
                print(f"      - {fname} ({size_mb:.2f} MB)")
            if len(large_files) > 5:
                print(f"      ... and {len(large_files) - 5} more")
    else:
        print_success("No large files found")

    # Check 6: Orphaned directories
    orphaned = check_for_orphaned_dirs()
    if orphaned:
        warnings.append(f"Orphaned directories: {', '.join(orphaned)}")
        info_messages.append("Consider organizing or removing orphaned directories")
    else:
        print_success("No orphaned directories found")

    # Check 7: Git tracked cache files
    git_ok, bad_git_files = check_git_status()
    if git_ok and bad_git_files:
        issues.append(f"{len(bad_git_files)} cache/temp files tracked by git")
        if verbose:
            print(f"\n    Files tracked by git that shouldn't be:")
            for fname in bad_git_files[:10]:
                print(f"      - {fname}")
            if len(bad_git_files) > 10:
                print(f"      ... and {len(bad_git_files) - 10} more")
        info_messages.append("Run: git rm -r --cached <file>")
    elif git_ok:
        print_success("No cache files tracked by git")

    # Check 8: Completion docs at root
    completion_docs = check_completion_docs_at_root()
    if completion_docs:
        warnings.append(f"{len(completion_docs)} completion doc(s) at root")
        if verbose:
            print(f"\n    Completion docs at root:")
            for fname in completion_docs:
                print(f"      - {fname}")
        info_messages.append("Move to docs/project-status/YYYY-MM-DD_*.md")

    # Print summary
    print_header("📊 Summary")

    if issues:
        print(f"\n{RED}🚨 CRITICAL ISSUES:{RESET}")
        for issue in issues:
            print_issue("ERROR", issue)

    if warnings:
        print(f"\n{YELLOW}⚠️  WARNINGS:{RESET}")
        for warning in warnings:
            print_issue("WARNING", warning)

    if info_messages:
        print(f"\n{BLUE}💡 RECOMMENDATIONS:{RESET}")
        for msg in info_messages:
            print_issue("INFO", msg)

    # Final result
    print()
    if issues:
        print(f"{RED}❌ Filesystem health check FAILED{RESET}")
        print(f"\n{BLUE}📖 See: .claude/FILESYSTEM_GUIDELINES.md for guidance{RESET}")
        return 1
    elif warnings:
        print(f"{YELLOW}⚠️  Filesystem health check passed with warnings{RESET}")
        print(f"\n{BLUE}📖 See: .claude/FILESYSTEM_GUIDELINES.md for guidance{RESET}")
        return 0
    else:
        print(f"{GREEN}✅ Filesystem health check passed!{RESET}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
