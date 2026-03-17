#!/usr/bin/env python3
"""
Commit Readiness Check — runs as a CC Stop hook.

After each CC response, checks whether uncommitted changes have accumulated
and reminds CC to offer a commit if a logical unit of work appears complete.

Exit codes:
  0 — No action needed (clean, or too few changes to bother)
  0 with stdout — Suggestion for CC to consider committing

This hook never blocks — it only advises.
"""

import subprocess
import sys
import os
from pathlib import Path

# Thresholds
MIN_CHANGED_FILES = 2       # Don't nag for a single file edit
MIN_CHANGED_LINES = 10      # Don't nag for trivial changes
MAX_UNCOMMITTED_FILES = 8   # Strongly suggest commit above this

def get_uncommitted_stats():
    """Get count of uncommitted changed files and lines."""
    try:
        # Tracked files with modifications (staged + unstaged)
        status = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, check=True,
            cwd='/Users/simonroy/Desktop/Bridge-Bidding-Program'
        )

        lines = [l for l in status.stdout.strip().split('\n') if l.strip()]

        # Filter to meaningful changes (not untracked ?? files)
        modified = [l for l in lines if not l.startswith('??')]
        untracked_new = [l for l in lines if l.startswith('??')]

        if not modified:
            return 0, 0, []

        # Count changed lines in tracked files
        diff = subprocess.run(
            ['git', 'diff', '--stat', '--cached'],
            capture_output=True, text=True,
            cwd='/Users/simonroy/Desktop/Bridge-Bidding-Program'
        )
        diff_unstaged = subprocess.run(
            ['git', 'diff', '--stat'],
            capture_output=True, text=True,
            cwd='/Users/simonroy/Desktop/Bridge-Bidding-Program'
        )

        # Rough line count from stat output
        total_lines = 0
        for output in [diff.stdout, diff_unstaged.stdout]:
            for line in output.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        num_part = parts[1].strip().split()[0]
                        try:
                            total_lines += int(num_part)
                        except (ValueError, IndexError):
                            pass

        # Get file names for context
        file_names = []
        for l in modified:
            # Status format: "XY filename" or "XY orig -> new"
            parts = l.strip().split(maxsplit=1)
            if len(parts) >= 2:
                file_names.append(parts[1])

        return len(modified), total_lines, file_names

    except (subprocess.CalledProcessError, FileNotFoundError):
        return 0, 0, []


def main():
    file_count, line_count, file_names = get_uncommitted_stats()

    # Nothing to do
    if file_count < MIN_CHANGED_FILES and line_count < MIN_CHANGED_LINES:
        sys.exit(0)

    # Build suggestion message
    if file_count >= MAX_UNCOMMITTED_FILES:
        urgency = "RECOMMEND"
        msg = (
            f"[commit-check] {file_count} files with uncommitted changes "
            f"(~{line_count} lines). This is getting large — suggest running "
            f"/smart-commit to bundle these into a commit before continuing."
        )
    else:
        urgency = "NOTE"
        msg = (
            f"[commit-check] {file_count} modified files with ~{line_count} "
            f"changed lines since last commit. Consider whether the current "
            f"changes form a logical commit before starting new work."
        )

    # Output to stdout — CC sees this as hook feedback
    print(msg)
    sys.exit(0)


if __name__ == '__main__':
    main()
