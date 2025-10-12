#!/usr/bin/env python3
"""
Documentation Compliance Checker

Automated script to verify that documentation practices are being followed.
Run this after completing any feature or bug fix to ensure documentation compliance.

Usage:
    python .claude/scripts/check_documentation_compliance.py
    python .claude/scripts/check_documentation_compliance.py --verbose
    python .claude/scripts/check_documentation_compliance.py --fix-dates
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict
import subprocess

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class DocumentationChecker:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.successes = []
        self.root_dir = Path(__file__).parent.parent.parent

    def log_error(self, message: str):
        """Log an error message"""
        self.errors.append(message)
        print(f"{RED}❌ ERROR: {message}{NC}")

    def log_warning(self, message: str):
        """Log a warning message"""
        self.warnings.append(message)
        print(f"{YELLOW}⚠️  WARNING: {message}{NC}")

    def log_success(self, message: str):
        """Log a success message"""
        self.successes.append(message)
        if self.verbose:
            print(f"{GREEN}✓ {message}{NC}")

    def log_info(self, message: str):
        """Log an info message"""
        if self.verbose:
            print(f"{BLUE}ℹ {message}{NC}")

    def get_staged_files(self) -> Tuple[List[str], List[str]]:
        """Get staged code and documentation files"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                capture_output=True,
                text=True,
                check=True
            )
            staged_files = result.stdout.strip().split('\n') if result.stdout else []

            code_files = [f for f in staged_files if self._is_code_file(f)]
            doc_files = [f for f in staged_files if self._is_doc_file(f)]

            return code_files, doc_files
        except subprocess.CalledProcessError:
            self.log_warning("Not in a git repository or git not available")
            return [], []

    def _is_code_file(self, filepath: str) -> bool:
        """Check if file is a code file"""
        code_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx']
        return (any(filepath.endswith(ext) for ext in code_extensions) and
                '__pycache__' not in filepath and
                'node_modules' not in filepath)

    def _is_doc_file(self, filepath: str) -> bool:
        """Check if file is a documentation file"""
        return filepath.endswith('.md') or 'docs/' in filepath

    def check_code_without_docs(self) -> bool:
        """Check if code changes exist without documentation changes"""
        code_files, doc_files = self.get_staged_files()

        if code_files and not doc_files:
            self.log_error(
                f"Found {len(code_files)} staged code file(s) but NO documentation files.\n"
                f"       Code files: {', '.join(code_files)}\n"
                f"       You MUST update relevant documentation before committing."
            )
            return False
        elif code_files and doc_files:
            self.log_success(
                f"Found {len(code_files)} code file(s) and {len(doc_files)} documentation file(s) staged"
            )
            return True
        elif doc_files:
            self.log_success(f"Found {len(doc_files)} documentation file(s) staged")
            return True
        else:
            self.log_info("No staged files found")
            return True

    def check_documentation_dates(self) -> bool:
        """Check if documentation has current 'Last Updated' dates"""
        today = datetime.now().strftime("%Y-%m-%d")
        issues_found = False

        _, doc_files = self.get_staged_files()

        for doc_file in doc_files:
            filepath = self.root_dir / doc_file
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text()

                # Check for Last Updated pattern
                last_updated_pattern = r'\*\*Last Updated\*\*:\s*(\d{4}-\d{2}-\d{2})'
                matches = re.findall(last_updated_pattern, content)

                if matches:
                    for date in matches:
                        if date != today:
                            self.log_warning(
                                f"{doc_file}: Last Updated date is {date}, should be {today}"
                            )
                            issues_found = True
                        else:
                            self.log_success(f"{doc_file}: Last Updated date is current")
                else:
                    # Check if this type of doc should have a date
                    if self._should_have_date(doc_file):
                        self.log_warning(
                            f"{doc_file}: Missing 'Last Updated' date"
                        )
                        issues_found = True
            except Exception as e:
                self.log_warning(f"Could not read {doc_file}: {e}")

        return not issues_found

    def _should_have_date(self, filepath: str) -> bool:
        """Check if this type of doc should have a Last Updated date"""
        # Skip certain files that don't need dates
        skip_patterns = ['README.md', 'CONTRIBUTING.md', 'LICENSE']
        filename = os.path.basename(filepath)
        return not any(pattern in filename for pattern in skip_patterns)

    def check_broken_links(self) -> bool:
        """Check for broken internal links in documentation"""
        issues_found = False
        _, doc_files = self.get_staged_files()

        for doc_file in doc_files:
            filepath = self.root_dir / doc_file
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text()

                # Find markdown links
                link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                links = re.findall(link_pattern, content)

                for link_text, link_url in links:
                    # Skip external links
                    if link_url.startswith('http://') or link_url.startswith('https://'):
                        continue

                    # Skip anchors only
                    if link_url.startswith('#'):
                        continue

                    # Remove anchor from link
                    link_path = link_url.split('#')[0]
                    if not link_path:
                        continue

                    # Resolve relative path
                    doc_dir = filepath.parent
                    target_path = (doc_dir / link_path).resolve()

                    if not target_path.exists():
                        self.log_error(
                            f"{doc_file}: Broken link to '{link_url}'"
                        )
                        issues_found = True
                    else:
                        self.log_success(f"{doc_file}: Link to '{link_url}' is valid")
            except Exception as e:
                self.log_warning(f"Could not check links in {doc_file}: {e}")

        return not issues_found

    def check_todo_fixme_markers(self) -> bool:
        """Check for unresolved TODO/FIXME markers in staged documentation"""
        issues_found = False
        _, doc_files = self.get_staged_files()

        for doc_file in doc_files:
            filepath = self.root_dir / doc_file
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text()
                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    if 'TODO' in line or 'FIXME' in line:
                        # Skip if it's in a code block or example
                        if not line.strip().startswith('```'):
                            self.log_warning(
                                f"{doc_file}:{line_num}: Contains TODO/FIXME marker"
                            )
                            issues_found = True
            except Exception as e:
                self.log_warning(f"Could not check {doc_file}: {e}")

        return not issues_found

    def check_required_documentation_files(self) -> bool:
        """Check if required documentation files exist"""
        required_files = [
            '.claude/DOCUMENTATION_PRACTICES.md',
            '.claude/PROJECT_CONTEXT.md',
            'docs/DOCUMENTATION_CHECKLIST.md',
            'CONTRIBUTING.md',
            'README.md',
            'docs/README.md',
            'docs/project-overview/DOCUMENTATION_INDEX.md'
        ]

        all_exist = True
        for req_file in required_files:
            filepath = self.root_dir / req_file
            if not filepath.exists():
                self.log_error(f"Required documentation file missing: {req_file}")
                all_exist = False
            else:
                self.log_success(f"Required file exists: {req_file}")

        return all_exist

    def check_feature_documentation(self) -> bool:
        """Check if features have corresponding documentation"""
        # Get list of Python files in engine/
        engine_dir = self.root_dir / 'backend' / 'engine'
        if not engine_dir.exists():
            return True

        features_dir = self.root_dir / 'docs' / 'features'
        if not features_dir.exists():
            self.log_warning("docs/features/ directory does not exist")
            return False

        # This is a basic check - can be expanded
        self.log_info("Feature documentation check passed (basic)")
        return True

    def check_bug_fix_documentation(self) -> bool:
        """Check if recent commits have bug fix documentation"""
        try:
            # Get recent commit messages
            result = subprocess.run(
                ['git', 'log', '--oneline', '-5'],
                capture_output=True,
                text=True,
                check=True
            )

            commits = result.stdout.strip().split('\n')
            bug_fixes_dir = self.root_dir / 'docs' / 'bug-fixes'

            for commit in commits:
                if 'fix:' in commit.lower() or 'bug' in commit.lower():
                    # Check if there's recent bug fix documentation
                    if bug_fixes_dir.exists():
                        self.log_success("Bug fix documentation directory exists")
                    else:
                        self.log_warning(
                            "Recent bug fix commits found but docs/bug-fixes/ doesn't exist"
                        )
                        return False

            return True
        except subprocess.CalledProcessError:
            return True

    def generate_report(self) -> Dict:
        """Generate a summary report"""
        return {
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'successes': len(self.successes),
            'error_messages': self.errors,
            'warning_messages': self.warnings
        }

    def run_all_checks(self) -> bool:
        """Run all documentation compliance checks"""
        print(f"{BLUE}{'='*60}{NC}")
        print(f"{BLUE}Documentation Compliance Checker{NC}")
        print(f"{BLUE}{'='*60}{NC}\n")

        checks = [
            ("Required documentation files", self.check_required_documentation_files),
            ("Code without documentation", self.check_code_without_docs),
            ("Documentation dates", self.check_documentation_dates),
            ("Broken links", self.check_broken_links),
            ("TODO/FIXME markers", self.check_todo_fixme_markers),
            ("Feature documentation", self.check_feature_documentation),
            ("Bug fix documentation", self.check_bug_fix_documentation),
        ]

        all_passed = True
        for check_name, check_func in checks:
            print(f"\n{BLUE}Checking: {check_name}{NC}")
            try:
                result = check_func()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_error(f"Exception during {check_name}: {e}")
                all_passed = False

        # Generate report
        print(f"\n{BLUE}{'='*60}{NC}")
        print(f"{BLUE}Summary{NC}")
        print(f"{BLUE}{'='*60}{NC}")

        report = self.generate_report()

        if report['errors'] > 0:
            print(f"{RED}Errors: {report['errors']}{NC}")
        else:
            print(f"{GREEN}Errors: 0{NC}")

        if report['warnings'] > 0:
            print(f"{YELLOW}Warnings: {report['warnings']}{NC}")
        else:
            print(f"{GREEN}Warnings: 0{NC}")

        print(f"{GREEN}Successes: {report['successes']}{NC}")

        if all_passed and report['errors'] == 0:
            print(f"\n{GREEN}✅ All documentation compliance checks PASSED!{NC}")
            return True
        elif report['errors'] == 0:
            print(f"\n{YELLOW}⚠️  All checks passed but with warnings{NC}")
            return True
        else:
            print(f"\n{RED}❌ Documentation compliance checks FAILED{NC}")
            print(f"\n{YELLOW}Please address the errors above before committing.{NC}")
            return False

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Check documentation compliance for the project'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--fix-dates',
        action='store_true',
        help='Automatically update Last Updated dates (not implemented yet)'
    )

    args = parser.parse_args()

    checker = DocumentationChecker(verbose=args.verbose)
    success = checker.run_all_checks()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
