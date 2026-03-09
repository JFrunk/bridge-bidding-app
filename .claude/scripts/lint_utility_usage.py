#!/usr/bin/env python3
"""
Utility Usage Lint — detects inline code that should use shared utilities.

Scans Python and JavaScript files for banned patterns defined in
.claude/UTILITY_REGISTRY.md. Can check staged files only (pre-commit)
or the entire codebase (full scan).

Usage:
  python3 .claude/scripts/lint_utility_usage.py              # Scan staged files
  python3 .claude/scripts/lint_utility_usage.py --all        # Scan entire codebase
  python3 .claude/scripts/lint_utility_usage.py --fix-hint   # Show import suggestions

Exit codes:
  0 — No violations found
  1 — Violations found (blocks commit in pre-commit mode)
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ─── Files to always skip ───────────────────────────────────────────────

SKIP_FILES = {
    # The utilities themselves
    "backend/utils/seats.py",
    "frontend/src/utils/seats.js",
    "frontend/src/utils/suitColors.js",
    "frontend/src/shared/utils/cardUtils.js",
    "backend/utils/error_logger.py",
    "frontend/src/utils/sessionHelper.js",
    # This script
    ".claude/scripts/lint_utility_usage.py",
    # Registry doc
    ".claude/UTILITY_REGISTRY.md",
}

SKIP_DIRS = {
    "node_modules", "venv", "__pycache__", ".git", "build", "dist",
    "playwright-report", "test-results", ".claude/worktrees",
    "SAYC_External_Review", "tests", "__tests__",
}

SKIP_EXTENSIONS = {
    ".md", ".json", ".css", ".html", ".svg", ".png", ".jpg", ".ico",
    ".lock", ".map", ".txt", ".sh", ".yml", ".yaml", ".toml", ".cfg",
    ".ini", ".pem", ".env", ".db", ".pid",
}


# ─── Violation rules ────────────────────────────────────────────────────

@dataclass
class Rule:
    id: str
    pattern: re.Pattern
    message: str
    utility: str
    import_hint: str
    file_types: tuple  # (".py",) or (".js", ".jsx") or both
    # Optional: only flag if the file does NOT already import the utility
    skip_if_imports: Optional[str] = None
    # Some patterns need extra context to avoid false positives
    negative_lookbehind: Optional[str] = None


RULES: list[Rule] = []


def rule(id, pattern, message, utility, import_hint, file_types, **kwargs):
    """Register a lint rule."""
    RULES.append(Rule(
        id=id,
        pattern=re.compile(pattern),
        message=message,
        utility=utility,
        import_hint=import_hint,
        file_types=file_types,
        **kwargs,
    ))


# ── Seats (Python) ──────────────────────────────────────────────────────

rule(
    "SEATS-PY-001",
    r"['\"]N['\"]:\s*['\"]S['\"].*['\"]S['\"]:\s*['\"]N['\"]",
    "Inline partner map — use partner() from utils.seats",
    "backend/utils/seats.py",
    "from utils.seats import partner",
    (".py",),
)

rule(
    "SEATS-PY-002",
    r"\(\s*\w+\s*\+\s*[12]\s*\)\s*%\s*4",
    "Inline seat modulo arithmetic — use lho/partner/seat_from_index from utils.seats",
    "backend/utils/seats.py",
    "from utils.seats import lho, partner, seat_from_index",
    (".py",),
)

rule(
    "SEATS-PY-003",
    r"\(\s*\w+\s*\+\s*\w+\s*\)\s*%\s*4",
    "Inline seat rotation — use active_seat_bidding/active_seat_play from utils.seats",
    "backend/utils/seats.py",
    "from utils.seats import active_seat_bidding, active_seat_play, seat_from_index",
    (".py",),
)

rule(
    "SEATS-PY-004",
    r"\[\s*['\"]N['\"],\s*['\"]E['\"],\s*['\"]S['\"],\s*['\"]W['\"]\s*\]",
    "Inline seat array — use SEATS from utils.seats",
    "backend/utils/seats.py",
    "from utils.seats import SEATS",
    (".py",),
)

rule(
    "SEATS-PY-005",
    r"\[\s*['\"]North['\"],\s*['\"]East['\"],\s*['\"]South['\"],\s*['\"]West['\"]\s*\]",
    "Inline seat name array — use SEAT_NAMES from utils.seats",
    "backend/utils/seats.py",
    "from utils.seats import SEAT_NAMES",
    (".py",),
)

# ── Seats (JavaScript) ──────────────────────────────────────────────────

rule(
    "SEATS-JS-001",
    r"['\"]N['\"]:\s*['\"]S['\"].*['\"]S['\"]:\s*['\"]N['\"]",
    "Inline partner map — use partner() from utils/seats",
    "frontend/src/utils/seats.js",
    "import { partner } from '../utils/seats'",
    (".js", ".jsx"),
)

rule(
    "SEATS-JS-002",
    r"\(\s*\w+\s*\+\s*[12]\s*\)\s*%\s*4",
    "Inline seat modulo arithmetic — use seats utility functions",
    "frontend/src/utils/seats.js",
    "import { lho, partner, seatFromIndex } from '../utils/seats'",
    (".js", ".jsx"),
)

rule(
    "SEATS-JS-003",
    r"\(\s*\w+\s*\+\s*\w+\s*\)\s*%\s*4",
    "Inline seat rotation — use activeSeatBidding/activeSeatPlay from utils/seats",
    "frontend/src/utils/seats.js",
    "import { activeSeatBidding, activeSeatPlay, seatFromIndex } from '../utils/seats'",
    (".js", ".jsx"),
)

rule(
    "SEATS-JS-004",
    r"\[\s*['\"]N['\"],\s*['\"]E['\"],\s*['\"]S['\"],\s*['\"]W['\"]\s*\]",
    "Inline seat array — use SEATS from utils/seats",
    "frontend/src/utils/seats.js",
    "import { SEATS } from '../utils/seats'",
    (".js", ".jsx"),
)

# ── Suit symbols (JavaScript) ───────────────────────────────────────────

rule(
    "SUIT-JS-001",
    r"['\"]S['\"]:\s*['\"]♠['\"].*['\"]H['\"]:\s*['\"]♥['\"]",
    "Inline suit symbol map — use SUIT_MAP from utils/suitColors",
    "frontend/src/utils/suitColors.js",
    "import { SUIT_MAP } from '../utils/suitColors'",
    (".js", ".jsx"),
)

rule(
    "SUIT-JS-002",
    r"['\"]♠['\"]:\s*['\"]S['\"].*['\"]♥['\"]:\s*['\"]H['\"]",
    "Inline reverse suit map — use SYMBOL_TO_LETTER from utils/suitColors",
    "frontend/src/utils/suitColors.js",
    "import { SYMBOL_TO_LETTER } from '../utils/suitColors'",
    (".js", ".jsx"),
)

rule(
    "SUIT-JS-003",
    r"""===\s*['"]♥['"]\s*\|\|\s*\w+\s*===\s*['"]♦['"]""",
    "Inline red suit check — use isRedSuit() from utils/suitColors",
    "frontend/src/utils/suitColors.js",
    "import { isRedSuit } from '../utils/suitColors'",
    (".js", ".jsx"),
)

rule(
    "SUIT-JS-004",
    r"""\[['"]H['"],\s*['"]D['"],\s*['"]♥['"],\s*['"]♦['"]\]\.includes""",
    "Inline red suit array check — use isRedSuit() from utils/suitColors",
    "frontend/src/utils/suitColors.js",
    "import { isRedSuit } from '../utils/suitColors'",
    (".js", ".jsx"),
)

rule(
    "SUIT-JS-005",
    r"['\"]♠['\"]:\s*['\"]spades['\"]",
    "Inline suit names map — use SUIT_NAMES from utils/suitColors",
    "frontend/src/utils/suitColors.js",
    "import { SUIT_NAMES } from '../utils/suitColors'",
    (".js", ".jsx"),
)

# ── Card utilities (JavaScript) ─────────────────────────────────────────

rule(
    "CARD-JS-001",
    r"['\"]A['\"]:\s*14.*['\"]K['\"]:\s*13",
    "Inline rank ordering map — use RANK_ORDER from shared/utils/cardUtils",
    "frontend/src/shared/utils/cardUtils.js",
    "import { RANK_ORDER } from '../shared/utils/cardUtils'",
    (".js", ".jsx"),
)

rule(
    "CARD-JS-002",
    r"function\s+sortCards\s*\(",
    "Duplicate sortCards function — import from shared/utils/cardUtils",
    "frontend/src/shared/utils/cardUtils.js",
    "import { sortCards } from '../shared/utils/cardUtils'",
    (".js", ".jsx"),
    skip_if_imports="from.*cardUtils",
)

rule(
    "CARD-JS-003",
    r"function\s+groupCardsBySuit\s*\(|function\s+groupBySuit\s*\(",
    "Duplicate card grouping function — import from shared/utils/cardUtils",
    "frontend/src/shared/utils/cardUtils.js",
    "import { groupCardsBySuit } from '../shared/utils/cardUtils'",
    (".js", ".jsx"),
    skip_if_imports="from.*cardUtils",
)

# ── Error logging (Python) ──────────────────────────────────────────────

rule(
    "ERR-PY-001",
    r"traceback\.print_exc\(\)",
    "Raw traceback.print_exc() — use log_error() from utils.error_logger",
    "backend/utils/error_logger.py",
    "from utils.error_logger import log_error",
    (".py",),
)

rule(
    "ERR-PY-002",
    r"except\s+Exception\s+as\s+log_error\s*:",
    "Variable 'log_error' shadows the utility import — use a different name",
    "backend/utils/error_logger.py",
    "# Rename exception variable, e.g.: except Exception as exc:",
    (".py",),
)

# ── Session management (JavaScript) ─────────────────────────────────────

rule(
    "SESS-JS-001",
    r"localStorage\.getItem\(\s*['\"]bridge_session_id['\"]\s*\)",
    "Inline session ID retrieval — use getSessionId() from utils/sessionHelper",
    "frontend/src/utils/sessionHelper.js",
    "import { getSessionId } from '../utils/sessionHelper'",
    (".js", ".jsx"),
    skip_if_imports="from.*sessionHelper",
)

rule(
    "SESS-JS-002",
    r"['\"]X-Session-ID['\"]:\s*\w+",
    "Inline session header — use getSessionHeaders() from utils/sessionHelper",
    "frontend/src/utils/sessionHelper.js",
    "import { getSessionHeaders } from '../utils/sessionHelper'",
    (".js", ".jsx"),
    skip_if_imports="from.*sessionHelper",
)


# ─── Scanning logic ─────────────────────────────────────────────────────

@dataclass
class Violation:
    file: str
    line_num: int
    line_text: str
    rule: Rule


def should_skip_file(rel_path: str) -> bool:
    """Check if a file should be excluded from scanning."""
    if rel_path in SKIP_FILES:
        return True

    parts = Path(rel_path).parts
    for d in SKIP_DIRS:
        if d in parts:
            return True

    ext = Path(rel_path).suffix
    if ext in SKIP_EXTENSIONS:
        return True

    return False


def scan_file(filepath: Path, rel_path: str) -> list[Violation]:
    """Scan a single file for utility violations."""
    violations = []
    ext = filepath.suffix

    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return violations

    lines = content.split("\n")

    for rule in RULES:
        # Check file type match
        if ext not in rule.file_types:
            continue

        # Check if file already imports the utility (skip_if_imports)
        if rule.skip_if_imports and re.search(rule.skip_if_imports, content):
            continue

        for i, line in enumerate(lines, 1):
            # Skip comment-only lines
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            if rule.pattern.search(line):
                violations.append(Violation(
                    file=rel_path,
                    line_num=i,
                    line_text=stripped[:120],
                    rule=rule,
                ))

    return violations


def get_staged_files() -> list[str]:
    """Get list of staged files (for pre-commit mode)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        # Fallback: get all modified files
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


def get_all_files() -> list[str]:
    """Get all tracked Python and JS files."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


# ─── Output formatting ──────────────────────────────────────────────────

RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def format_violations(violations: list[Violation], show_hints: bool = False) -> str:
    """Format violations for terminal output."""
    if not violations:
        return f"{BOLD}✓ No utility violations found.{RESET}"

    # Group by file
    by_file: dict[str, list[Violation]] = {}
    for v in violations:
        by_file.setdefault(v.file, []).append(v)

    lines = []
    lines.append(f"\n{RED}{BOLD}✗ {len(violations)} utility violation(s) in {len(by_file)} file(s):{RESET}\n")

    for filepath, file_violations in sorted(by_file.items()):
        lines.append(f"  {BOLD}{filepath}{RESET}")
        for v in sorted(file_violations, key=lambda x: x.line_num):
            lines.append(f"    {YELLOW}L{v.line_num}{RESET}  [{v.rule.id}] {v.rule.message}")
            lines.append(f"         {DIM}{v.line_text}{RESET}")
            if show_hints:
                lines.append(f"         {CYAN}→ {v.rule.import_hint}{RESET}")
        lines.append("")

    lines.append(f"{DIM}See .claude/UTILITY_REGISTRY.md for the full list of shared utilities and banned patterns.{RESET}")
    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lint for inline utility duplication")
    parser.add_argument("--all", action="store_true", help="Scan entire codebase (not just staged files)")
    parser.add_argument("--fix-hint", action="store_true", help="Show import suggestions for each violation")
    parser.add_argument("--quiet", action="store_true", help="Only output if violations found")
    parser.add_argument("files", nargs="*", help="Specific files to scan (overrides --all and staged)")
    args = parser.parse_args()

    # Determine files to scan
    if args.files:
        files = args.files
    elif args.all:
        files = get_all_files()
    else:
        files = get_staged_files()

    # Filter and scan
    all_violations: list[Violation] = []
    scanned = 0

    for rel_path in files:
        if should_skip_file(rel_path):
            continue

        filepath = PROJECT_ROOT / rel_path
        if not filepath.is_file():
            continue

        ext = filepath.suffix
        if ext not in (".py", ".js", ".jsx", ".ts", ".tsx"):
            continue

        scanned += 1
        all_violations.extend(scan_file(filepath, rel_path))

    # Output
    if not args.quiet or all_violations:
        print(format_violations(all_violations, show_hints=args.fix_hint))

    if not args.quiet and not all_violations:
        print(f"{DIM}Scanned {scanned} file(s).{RESET}")

    sys.exit(1 if all_violations else 0)


if __name__ == "__main__":
    main()
