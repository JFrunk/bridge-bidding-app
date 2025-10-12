#!/usr/bin/env python3
"""
Architectural Compliance Report Generator

Analyzes the entire codebase for architectural health and compliance with
best practices documented in ARCHITECTURAL_DECISION_FRAMEWORK.md.

Usage:
    python3 .claude/scripts/architectural_compliance_report.py [--html]

Generates a comprehensive report covering:
- Anti-pattern detection (god classes, tight coupling, etc.)
- Dependency analysis (circular imports, excessive dependencies)
- Code metrics (file sizes, complexity estimates)
- ADR compliance (are decisions documented?)
- Architectural debt tracking

Returns:
    0 - All checks pass
    1 - Warnings detected
    2 - Critical issues detected
"""

import os
import sys
import ast
import re
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from datetime import datetime

class ArchitecturalComplianceChecker:
    def __init__(self, root_dir='.', verbose=False):
        self.root_dir = Path(root_dir)
        self.verbose = verbose
        self.issues = {
            'critical': [],
            'warning': [],
            'info': []
        }
        self.metrics = {}
        self.dependencies = defaultdict(set)

    def log(self, message):
        if self.verbose:
            print(f"[INFO] {message}")

    def add_issue(self, severity, category, message, file=None, line=None, recommendation=None):
        issue = {
            'severity': severity,
            'category': category,
            'message': message,
            'file': file,
            'line': line,
            'recommendation': recommendation
        }
        self.issues[severity].append(issue)

    def check_god_classes(self):
        """Detect god classes (files > 500 lines)"""
        self.log("Checking for god classes...")

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '.git' in str(py_file):
                continue

            try:
                lines = py_file.read_text(encoding='utf-8').splitlines()
                loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])

                if loc > 500:
                    self.add_issue(
                        'warning',
                        'god_class',
                        f'Large file: {loc} lines (> 500)',
                        file=str(py_file.relative_to(self.root_dir)),
                        recommendation='Consider breaking into smaller, focused modules'
                    )
                elif loc > 1000:
                    self.add_issue(
                        'critical',
                        'god_class',
                        f'Very large file: {loc} lines (> 1000)',
                        file=str(py_file.relative_to(self.root_dir)),
                        recommendation='This is a god class anti-pattern. Must be refactored.'
                    )
            except Exception as e:
                if self.verbose:
                    print(f"Error reading {py_file}: {e}")

    def check_global_state(self):
        """Detect global state variables"""
        self.log("Checking for global state...")

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '.git' in str(py_file) or 'test' in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.splitlines()

                # Look for module-level variables that look like state
                state_patterns = [
                    (r'^current_\w+\s*=', 'current_* variable'),
                    (r'^[A-Z_]+\s*=\s*(\{|\[|None)', 'CONSTANT-style mutable variable'),
                ]

                for i, line in enumerate(lines, 1):
                    if line.strip().startswith('#'):
                        continue

                    for pattern, description in state_patterns:
                        if re.search(pattern, line):
                            self.add_issue(
                                'warning',
                                'global_state',
                                f'Potential global state: {description}',
                                file=str(py_file.relative_to(self.root_dir)),
                                line=i,
                                recommendation='Consider session-based state management (see ARCHITECTURE_RISK_ANALYSIS.md Risk #1)'
                            )
            except Exception as e:
                if self.verbose:
                    print(f"Error reading {py_file}: {e}")

    def analyze_dependencies(self):
        """Analyze import dependencies"""
        self.log("Analyzing dependencies...")

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '.git' in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content)

                module_path = str(py_file.relative_to(self.root_dir)).replace('/', '.').replace('.py', '')

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.dependencies[module_path].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.dependencies[module_path].add(node.module)

            except Exception as e:
                if self.verbose:
                    print(f"Error analyzing {py_file}: {e}")

    def check_circular_dependencies(self):
        """Detect circular import dependencies"""
        self.log("Checking for circular dependencies...")

        def has_path(graph, start, end, visited=None):
            if visited is None:
                visited = set()
            if start == end:
                return True
            if start in visited:
                return False
            visited.add(start)
            for neighbor in graph.get(start, []):
                if has_path(graph, neighbor, end, visited):
                    return True
            return False

        for module_a in self.dependencies:
            for module_b in self.dependencies[module_a]:
                if module_b in self.dependencies and has_path(self.dependencies, module_b, module_a):
                    self.add_issue(
                        'critical',
                        'circular_dependency',
                        f'Circular dependency: {module_a} ↔ {module_b}',
                        recommendation='Refactor to use dependency injection or extract shared code to lower layer'
                    )

    def check_excessive_dependencies(self):
        """Check for modules with too many dependencies"""
        self.log("Checking for excessive dependencies...")

        for module, deps in self.dependencies.items():
            if len(deps) > 15:
                self.add_issue(
                    'warning',
                    'excessive_dependencies',
                    f'{module} has {len(deps)} dependencies (> 15)',
                    recommendation='High coupling. Consider reducing dependencies or splitting module.'
                )

    def check_adr_existence(self):
        """Check if ADRs exist and are being used"""
        self.log("Checking ADR usage...")

        adr_dir = self.root_dir / 'docs' / 'architecture' / 'decisions'

        if not adr_dir.exists():
            self.add_issue(
                'warning',
                'adr_missing',
                'No ADR directory found',
                recommendation='Create docs/architecture/decisions/ to document architectural decisions'
            )
            return

        adrs = list(adr_dir.glob('ADR-*.md'))
        if len(adrs) <= 1:  # Only ADR-0000 exists
            self.add_issue(
                'info',
                'adr_usage',
                f'Only {len(adrs)} ADR(s) found',
                recommendation='Create ADRs for significant architectural decisions'
            )

    def check_documentation_coverage(self):
        """Check if key architectural files are documented"""
        self.log("Checking documentation coverage...")

        key_files = [
            'server.py',
            'engine/bidding_engine.py',
            'engine/play_engine.py',
        ]

        for file_path in key_files:
            full_path = self.root_dir / 'backend' / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    # Check for module docstring
                    if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
                        self.add_issue(
                            'warning',
                            'missing_docstring',
                            f'No module docstring in {file_path}',
                            recommendation='Add module-level docstring explaining purpose and architecture'
                        )
                except Exception as e:
                    pass

    def check_test_organization(self):
        """Check if tests follow the organized structure"""
        self.log("Checking test organization...")

        test_root = self.root_dir / 'backend' / 'tests'
        if not test_root.exists():
            return

        expected_dirs = ['unit', 'integration', 'regression', 'features', 'scenarios']
        missing_dirs = []

        for dir_name in expected_dirs:
            if not (test_root / dir_name).exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            self.add_issue(
                'warning',
                'test_organization',
                f'Missing test directories: {", ".join(missing_dirs)}',
                recommendation='Create organized test structure (see backend/tests/README.md)'
            )

        # Check for tests in wrong location (backend/ root)
        backend_root = self.root_dir / 'backend'
        for test_file in backend_root.glob('test_*.py'):
            self.add_issue(
                'warning',
                'test_organization',
                f'Test file in wrong location: {test_file.name}',
                file=f'backend/{test_file.name}',
                recommendation='Move to backend/tests/{unit,integration,regression,features,scenarios}/'
            )

    def calculate_metrics(self):
        """Calculate overall project metrics"""
        self.log("Calculating metrics...")

        total_python_files = 0
        total_loc = 0
        total_test_files = 0

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '.git' in str(py_file):
                continue

            total_python_files += 1
            if 'test' in str(py_file):
                total_test_files += 1

            try:
                lines = py_file.read_text(encoding='utf-8').splitlines()
                loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
                total_loc += loc
            except:
                pass

        self.metrics = {
            'total_python_files': total_python_files,
            'total_loc': total_loc,
            'total_test_files': total_test_files,
            'test_to_code_ratio': total_test_files / max(total_python_files - total_test_files, 1),
            'avg_loc_per_file': total_loc / max(total_python_files, 1),
            'total_dependencies': len(self.dependencies),
            'total_issues': len(self.issues['critical']) + len(self.issues['warning']) + len(self.issues['info'])
        }

    def generate_report(self, format='text'):
        """Generate report in specified format"""
        if format == 'html':
            return self.generate_html_report()
        else:
            return self.generate_text_report()

    def generate_text_report(self):
        """Generate text report"""
        lines = []
        lines.append("=" * 80)
        lines.append("ARCHITECTURAL COMPLIANCE REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Python Files: {self.metrics.get('total_python_files', 0)}")
        lines.append(f"Total Lines of Code: {self.metrics.get('total_loc', 0):,}")
        lines.append(f"Average LOC per File: {self.metrics.get('avg_loc_per_file', 0):.1f}")
        lines.append(f"Test Files: {self.metrics.get('total_test_files', 0)}")
        lines.append(f"Test/Code Ratio: {self.metrics.get('test_to_code_ratio', 0):.2f}")
        lines.append("")
        lines.append(f"Critical Issues: {len(self.issues['critical'])}")
        lines.append(f"Warnings: {len(self.issues['warning'])}")
        lines.append(f"Info: {len(self.issues['info'])}")
        lines.append("")

        # Issues by severity
        for severity in ['critical', 'warning', 'info']:
            if self.issues[severity]:
                symbol = "🔴" if severity == 'critical' else "🟡" if severity == 'warning' else "🔵"
                lines.append(f"{symbol} {severity.upper()} ISSUES ({len(self.issues[severity])})")
                lines.append("-" * 80)

                for issue in self.issues[severity]:
                    lines.append(f"\n[{issue['category'].upper()}]")
                    if issue['file']:
                        location = issue['file']
                        if issue['line']:
                            location += f":{issue['line']}"
                        lines.append(f"  File: {location}")
                    lines.append(f"  Issue: {issue['message']}")
                    if issue['recommendation']:
                        lines.append(f"  Fix: {issue['recommendation']}")
                lines.append("")

        # Health Score
        total_issues = len(self.issues['critical']) + len(self.issues['warning'])
        if total_issues == 0:
            health_score = 100
            health_grade = "A+"
        elif total_issues < 5:
            health_score = 90
            health_grade = "A"
        elif total_issues < 10:
            health_score = 80
            health_grade = "B"
        elif total_issues < 20:
            health_score = 70
            health_grade = "C"
        else:
            health_score = 50
            health_grade = "D"

        lines.append("ARCHITECTURAL HEALTH SCORE")
        lines.append("-" * 80)
        lines.append(f"Score: {health_score}/100 (Grade: {health_grade})")
        lines.append("")

        if health_score < 80:
            lines.append("RECOMMENDATIONS:")
            lines.append("- Review and address critical issues first")
            lines.append("- Consult ARCHITECTURAL_DECISION_FRAMEWORK.md for guidance")
            lines.append("- Create ADRs for any architectural decisions")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def generate_html_report(self):
        """Generate HTML report"""
        # Simplified HTML report
        html = f"""
        <html>
        <head>
            <title>Architectural Compliance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .critical {{ color: red; }}
                .warning {{ color: orange; }}
                .info {{ color: blue; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Architectural Compliance Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <h2>Summary</h2>
            <table>
                <tr><td>Total Python Files</td><td>{self.metrics.get('total_python_files', 0)}</td></tr>
                <tr><td>Total Lines of Code</td><td>{self.metrics.get('total_loc', 0):,}</td></tr>
                <tr><td>Critical Issues</td><td class="critical">{len(self.issues['critical'])}</td></tr>
                <tr><td>Warnings</td><td class="warning">{len(self.issues['warning'])}</td></tr>
            </table>

            <h2>Issues</h2>
        """

        for severity in ['critical', 'warning']:
            if self.issues[severity]:
                html += f'<h3 class="{severity}">{severity.upper()} ({len(self.issues[severity])})</h3><ul>'
                for issue in self.issues[severity]:
                    location = issue['file'] or ''
                    if issue['line']:
                        location += f":{issue['line']}"
                    html += f"<li><strong>[{issue['category']}]</strong> {location}: {issue['message']}"
                    if issue['recommendation']:
                        html += f"<br><em>Recommendation: {issue['recommendation']}</em>"
                    html += "</li>"
                html += "</ul>"

        html += "</body></html>"
        return html

    def run(self):
        """Run all checks"""
        self.check_god_classes()
        self.check_global_state()
        self.analyze_dependencies()
        self.check_circular_dependencies()
        self.check_excessive_dependencies()
        self.check_adr_existence()
        self.check_documentation_coverage()
        self.check_test_organization()
        self.calculate_metrics()

        # Determine exit code
        if self.issues['critical']:
            return 2
        elif self.issues['warning']:
            return 1
        else:
            return 0

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate architectural compliance report')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    checker = ArchitecturalComplianceChecker(verbose=args.verbose)
    exit_code = checker.run()

    format = 'html' if args.html else 'text'
    report = checker.generate_report(format=format)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
