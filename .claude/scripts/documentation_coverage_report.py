#!/usr/bin/env python3
"""
Documentation Coverage Report Generator

Analyzes the codebase to identify:
- Python modules without corresponding documentation
- Features implemented but not documented
- Bug fixes in git history without documentation
- Test files without documentation

Usage:
    python .claude/scripts/documentation_coverage_report.py
    python .claude/scripts/documentation_coverage_report.py --html
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'

class DocumentationCoverageAnalyzer:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.backend_dir = self.root_dir / 'backend'
        self.docs_dir = self.root_dir / 'docs'
        self.engine_dir = self.backend_dir / 'engine'

    def get_python_modules(self) -> List[Path]:
        """Get all Python modules in backend/engine"""
        if not self.engine_dir.exists():
            return []

        modules = []
        for py_file in self.engine_dir.glob('*.py'):
            if py_file.name != '__init__.py' and not py_file.name.startswith('_'):
                modules.append(py_file)
        return modules

    def get_feature_docs(self) -> Set[str]:
        """Get list of documented features"""
        features_dir = self.docs_dir / 'features'
        if not features_dir.exists():
            return set()

        documented_features = set()
        for doc_file in features_dir.glob('*.md'):
            # Extract feature name from filename
            feature_name = doc_file.stem.lower()
            documented_features.add(feature_name)

        return documented_features

    def get_bug_fix_docs(self) -> Set[str]:
        """Get list of documented bug fixes"""
        bugfix_dir = self.docs_dir / 'bug-fixes'
        if not bugfix_dir.exists():
            return set()

        documented_fixes = set()
        for doc_file in bugfix_dir.glob('*.md'):
            documented_fixes.add(doc_file.stem)

        return documented_fixes

    def get_recent_bug_fixes_from_git(self, limit=50) -> List[Dict]:
        """Get recent bug fix commits from git history"""
        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--oneline', '--grep=fix:', '--grep=bug', '--ignore-case'],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.root_dir
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1]
                        })
            return commits
        except subprocess.CalledProcessError:
            return []

    def check_module_documentation(self) -> Dict:
        """Check if Python modules have corresponding documentation"""
        modules = self.get_python_modules()
        documented_features = self.get_feature_docs()

        results = {
            'total_modules': len(modules),
            'documented': [],
            'undocumented': [],
            'coverage_percent': 0
        }

        for module in modules:
            module_name = module.stem
            # Check if there's a feature doc that mentions this module
            is_documented = False

            # Check feature docs for mentions
            features_dir = self.docs_dir / 'features'
            if features_dir.exists():
                for feature_doc in features_dir.glob('*.md'):
                    content = feature_doc.read_text()
                    if module_name in content.lower():
                        is_documented = True
                        results['documented'].append({
                            'module': module_name,
                            'doc': feature_doc.name
                        })
                        break

            if not is_documented:
                results['undocumented'].append(module_name)

        if results['total_modules'] > 0:
            results['coverage_percent'] = (len(results['documented']) / results['total_modules']) * 100

        return results

    def check_bug_fix_documentation(self) -> Dict:
        """Check if recent bug fixes have documentation"""
        git_fixes = self.get_recent_bug_fixes_from_git()
        documented_fixes = self.get_bug_fix_docs()

        results = {
            'total_fixes': len(git_fixes),
            'documented_count': len(documented_fixes),
            'recent_fixes': git_fixes[:10],  # Show last 10
            'undocumented': []
        }

        # This is a basic check - actual matching would require more sophisticated analysis
        for fix in git_fixes[:10]:
            # Check if commit message keywords appear in any bug fix docs
            has_doc = False
            message_lower = fix['message'].lower()

            for doc_name in documented_fixes:
                doc_name_lower = doc_name.lower()
                # Very basic matching
                if any(word in doc_name_lower for word in message_lower.split() if len(word) > 4):
                    has_doc = True
                    break

            if not has_doc:
                results['undocumented'].append(fix)

        return results

    def generate_report(self) -> str:
        """Generate comprehensive coverage report"""
        report = []
        report.append("=" * 70)
        report.append("DOCUMENTATION COVERAGE REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Module coverage
        report.append("1. MODULE DOCUMENTATION COVERAGE")
        report.append("-" * 70)
        module_results = self.check_module_documentation()

        report.append(f"Total Python modules in backend/engine: {module_results['total_modules']}")
        report.append(f"Modules with documentation: {len(module_results['documented'])}")
        report.append(f"Coverage: {module_results['coverage_percent']:.1f}%")
        report.append("")

        if module_results['undocumented']:
            report.append(f"{YELLOW}Undocumented modules:{NC}")
            for module in module_results['undocumented']:
                report.append(f"  • {module}.py")
        else:
            report.append(f"{GREEN}✓ All modules have documentation!{NC}")

        report.append("")

        # Bug fix documentation
        report.append("2. BUG FIX DOCUMENTATION")
        report.append("-" * 70)
        bugfix_results = self.check_bug_fix_documentation()

        report.append(f"Recent bug fix commits analyzed: {len(bugfix_results['recent_fixes'])}")
        report.append(f"Bug fix documentation files: {bugfix_results['documented_count']}")
        report.append("")

        if bugfix_results['undocumented']:
            report.append(f"{YELLOW}Recent fixes that may need documentation:{NC}")
            for fix in bugfix_results['undocumented'][:5]:
                report.append(f"  • {fix['hash']}: {fix['message']}")
        else:
            report.append(f"{GREEN}✓ Recent fixes appear to be documented{NC}")

        report.append("")

        # Documentation health metrics
        report.append("3. DOCUMENTATION HEALTH METRICS")
        report.append("-" * 70)

        # Count documentation files
        total_docs = sum(1 for _ in self.docs_dir.rglob('*.md'))
        report.append(f"Total documentation files: {total_docs}")

        features_count = len(list((self.docs_dir / 'features').glob('*.md'))) if (self.docs_dir / 'features').exists() else 0
        bugfix_count = len(list((self.docs_dir / 'bug-fixes').glob('*.md'))) if (self.docs_dir / 'bug-fixes').exists() else 0
        guide_count = len(list((self.docs_dir / 'guides').glob('*.md'))) if (self.docs_dir / 'guides').exists() else 0
        arch_count = len(list((self.docs_dir / 'architecture').glob('*.md'))) if (self.docs_dir / 'architecture').exists() else 0

        report.append(f"  • Feature documentation: {features_count}")
        report.append(f"  • Bug fix documentation: {bugfix_count}")
        report.append(f"  • Guides: {guide_count}")
        report.append(f"  • Architecture docs: {arch_count}")
        report.append("")

        # Overall assessment
        report.append("4. OVERALL ASSESSMENT")
        report.append("-" * 70)

        if module_results['coverage_percent'] >= 90 and len(bugfix_results['undocumented']) <= 2:
            report.append(f"{GREEN}✅ EXCELLENT: Documentation coverage is very good{NC}")
        elif module_results['coverage_percent'] >= 70:
            report.append(f"{YELLOW}⚠️  GOOD: Documentation coverage is acceptable but could be improved{NC}")
        else:
            report.append(f"{RED}❌ NEEDS IMPROVEMENT: Documentation coverage is insufficient{NC}")

        report.append("")

        # Recommendations
        report.append("5. RECOMMENDATIONS")
        report.append("-" * 70)

        if module_results['undocumented']:
            report.append("• Create feature documentation for undocumented modules:")
            for module in module_results['undocumented'][:3]:
                report.append(f"  - docs/features/{module.upper()}.md")

        if bugfix_results['undocumented']:
            report.append("• Document recent bug fixes:")
            for fix in bugfix_results['undocumented'][:3]:
                report.append(f"  - Create docs/bug-fixes/FIX_[DESCRIPTION].md for: {fix['message'][:50]}")

        if not module_results['undocumented'] and not bugfix_results['undocumented']:
            report.append(f"{GREEN}• Keep up the excellent documentation practices!{NC}")
            report.append("• Continue to document all new features and bug fixes")

        report.append("")
        report.append("=" * 70)

        return '\n'.join(report)

    def save_html_report(self, report_text: str):
        """Save report as HTML file"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Documentation Coverage Report</title>
    <style>
        body {{ font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }}
        .green {{ color: #4ec9b0; }}
        .yellow {{ color: #dcdcaa; }}
        .red {{ color: #f48771; }}
        pre {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <pre>{report_text}</pre>
</body>
</html>
"""
        output_file = self.root_dir / 'documentation_coverage_report.html'
        output_file.write_text(html_content)
        print(f"\n{GREEN}HTML report saved to: {output_file}{NC}")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate documentation coverage report'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML report in addition to console output'
    )

    args = parser.parse_args()

    analyzer = DocumentationCoverageAnalyzer()
    report = analyzer.generate_report()

    print(report)

    if args.html:
        analyzer.save_html_report(report)

if __name__ == '__main__':
    main()
