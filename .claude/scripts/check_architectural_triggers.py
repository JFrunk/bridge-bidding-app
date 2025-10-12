#!/usr/bin/env python3
"""
Architectural Trigger Detection Script

Analyzes git staged changes to detect architectural triggers that require
review via the Architecture Decision Records (ADR) process.

Usage:
    python3 .claude/scripts/check_architectural_triggers.py [--verbose]

Returns:
    0 - No triggers detected
    1 - Low/medium risk triggers detected (warning)
    2 - High risk triggers detected (requires review)
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

class ArchitecturalTriggerDetector:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.warnings = []
        self.errors = []
        self.triggers_detected = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': []
        }

    def log_info(self, message):
        if self.verbose:
            print(f"[INFO] {message}")

    def log_warning(self, message):
        self.warnings.append(message)
        print(f"[WARNING] {message}")

    def log_error(self, message):
        self.errors.append(message)
        print(f"[ERROR] {message}")

    def get_staged_files(self) -> Tuple[List[str], List[str]]:
        """Get list of staged files (added, modified, deleted)"""
        try:
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-status'],
                capture_output=True,
                text=True,
                check=True
            )

            added_modified = []
            deleted = []

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                status, *files = line.split('\t')
                filepath = files[-1]  # Handle renames

                if status in ['A', 'M', 'C']:  # Added, Modified, Copied
                    added_modified.append(filepath)
                elif status == 'D':  # Deleted
                    deleted.append(filepath)

            return added_modified, deleted

        except subprocess.CalledProcessError:
            # Not a git repo or no staged changes
            return [], []

    def check_new_directories(self, files: List[str]):
        """Detect new directories being created"""
        dirs = set()
        for filepath in files:
            dir_path = os.path.dirname(filepath)
            if dir_path and not os.path.exists(dir_path):
                dirs.add(dir_path)

        if dirs:
            self.triggers_detected['high_risk'].append({
                'type': 'new_directories',
                'severity': 'HIGH',
                'message': f'Creating new directories: {", ".join(sorted(dirs))}',
                'recommendation': 'Review project structure. Is this the right place? Does it follow existing patterns?'
            })

    def check_dependency_changes(self, files: List[str]):
        """Detect changes to dependency files"""
        dependency_files = {
            'requirements.txt': 'Python',
            'package.json': 'JavaScript/Node',
            'Pipfile': 'Python (Pipenv)',
            'pyproject.toml': 'Python',
            'setup.py': 'Python'
        }

        for filepath in files:
            basename = os.path.basename(filepath)
            if basename in dependency_files:
                self.triggers_detected['high_risk'].append({
                    'type': 'dependency_changes',
                    'severity': 'HIGH',
                    'file': filepath,
                    'message': f'Modifying {dependency_files[basename]} dependencies',
                    'recommendation': 'Review new dependencies. Are they necessary? What are the security implications?'
                })

    def check_data_structure_changes(self, files: List[str]):
        """Detect changes to core data structures"""
        data_structure_patterns = [
            (r'engine/(hand|card|deal|contract)\.py', 'Core data structures'),
            (r'engine/play_engine\.py', 'Play engine state'),
            (r'engine/bidding_engine\.py', 'Bidding engine state'),
        ]

        for filepath in files:
            for pattern, description in data_structure_patterns:
                if re.search(pattern, filepath):
                    self.triggers_detected['high_risk'].append({
                        'type': 'data_structure_changes',
                        'severity': 'HIGH',
                        'file': filepath,
                        'message': f'Modifying {description} ({filepath})',
                        'recommendation': 'These are used across many modules. Ensure backward compatibility or plan migration.'
                    })

    def check_api_changes(self, files: List[str]):
        """Detect API endpoint modifications"""
        api_patterns = [
            'server.py',
            'api/',
            'routes.py',
            'endpoints.py'
        ]

        for filepath in files:
            for pattern in api_patterns:
                if pattern in filepath:
                    self.triggers_detected['high_risk'].append({
                        'type': 'api_changes',
                        'severity': 'HIGH',
                        'file': filepath,
                        'message': f'Modifying API endpoints ({filepath})',
                        'recommendation': 'Consider backward compatibility. Update API documentation. Verify frontend integration.'
                    })
                    break

    def check_config_changes(self, files: List[str]):
        """Detect configuration changes"""
        config_patterns = [
            '.env',
            'config.py',
            'settings.py',
            'pytest.ini',
            '.github/workflows/',
            'Dockerfile'
        ]

        for filepath in files:
            for pattern in config_patterns:
                if pattern in filepath:
                    severity = 'HIGH' if 'github/workflows' in pattern or 'Dockerfile' in pattern else 'MEDIUM'
                    self.triggers_detected[severity.lower() + '_risk'].append({
                        'type': 'config_changes',
                        'severity': severity,
                        'file': filepath,
                        'message': f'Modifying configuration ({filepath})',
                        'recommendation': 'Test in dev environment first. Document changes. Consider environment-specific impacts.'
                    })

    def check_large_files(self, files: List[str]):
        """Detect creation of large files that might indicate god classes"""
        for filepath in files:
            if os.path.exists(filepath):
                lines = 0
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                except:
                    continue

                if lines > 500:
                    self.triggers_detected['medium_risk'].append({
                        'type': 'large_file',
                        'severity': 'MEDIUM',
                        'file': filepath,
                        'lines': lines,
                        'message': f'Creating/modifying large file ({filepath}): {lines} lines',
                        'recommendation': 'Consider breaking into smaller, focused modules. Review Single Responsibility Principle.'
                    })

    def check_shared_utility_changes(self, files: List[str]):
        """Detect changes to shared utilities"""
        utility_patterns = [
            'utils/',
            'helpers/',
            'shared/',
            'common/',
            'core/'
        ]

        for filepath in files:
            for pattern in utility_patterns:
                if pattern in filepath:
                    self.triggers_detected['medium_risk'].append({
                        'type': 'shared_utility_changes',
                        'severity': 'MEDIUM',
                        'file': filepath,
                        'message': f'Modifying shared utility ({filepath})',
                        'recommendation': 'These are used by multiple modules. Ensure changes are backward compatible. Update all callers.'
                    })
                    break

    def check_state_management_patterns(self, files: List[str]):
        """Detect introduction of new state management"""
        for filepath in files:
            if not os.path.exists(filepath):
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for global state indicators
                global_indicators = [
                    r'^\s*global\s+\w+',
                    r'^[A-Z_]+\s*=',  # Module-level constants (might be state)
                ]

                for pattern in global_indicators:
                    if re.search(pattern, content, re.MULTILINE):
                        self.triggers_detected['medium_risk'].append({
                            'type': 'state_management',
                            'severity': 'MEDIUM',
                            'file': filepath,
                            'message': f'Potential global state in {filepath}',
                            'recommendation': 'Review ARCHITECTURE_RISK_ANALYSIS.md Risk #1. Consider session-based state.'
                        })
                        break
            except:
                continue

    def check_test_infrastructure_changes(self, files: List[str]):
        """Detect changes to test infrastructure"""
        test_infra_patterns = [
            'pytest.ini',
            'conftest.py',
            'tests/fixtures/',
            'tests/helpers/',
            'test_*.sh'
        ]

        for filepath in files:
            for pattern in test_infra_patterns:
                if pattern in filepath:
                    self.triggers_detected['medium_risk'].append({
                        'type': 'test_infrastructure',
                        'severity': 'MEDIUM',
                        'file': filepath,
                        'message': f'Modifying test infrastructure ({filepath})',
                        'recommendation': 'Ensure all tests still pass. Update test documentation if needed.'
                    })
                    break

    def analyze(self) -> int:
        """Run all checks and return exit code"""
        self.log_info("Checking for architectural triggers...")

        staged_files, deleted_files = self.get_staged_files()

        if not staged_files and not deleted_files:
            self.log_info("No staged changes detected.")
            return 0

        self.log_info(f"Analyzing {len(staged_files)} staged files...")

        # Run all checks
        self.check_new_directories(staged_files)
        self.check_dependency_changes(staged_files)
        self.check_data_structure_changes(staged_files)
        self.check_api_changes(staged_files)
        self.check_config_changes(staged_files)
        self.check_large_files(staged_files)
        self.check_shared_utility_changes(staged_files)
        self.check_state_management_patterns(staged_files)
        self.check_test_infrastructure_changes(staged_files)

        # Report findings
        return self.report()

    def report(self) -> int:
        """Generate report and return appropriate exit code"""
        total_triggers = (
            len(self.triggers_detected['high_risk']) +
            len(self.triggers_detected['medium_risk']) +
            len(self.triggers_detected['low_risk'])
        )

        if total_triggers == 0:
            print("\n✅ No architectural triggers detected.")
            return 0

        print("\n" + "="*70)
        print("🏗️  ARCHITECTURAL TRIGGERS DETECTED")
        print("="*70)

        # High risk triggers
        if self.triggers_detected['high_risk']:
            print(f"\n🔴 HIGH RISK TRIGGERS ({len(self.triggers_detected['high_risk'])})")
            print("   ⚠️  ARCHITECTURAL REVIEW REQUIRED")
            print()
            for trigger in self.triggers_detected['high_risk']:
                print(f"   • {trigger['message']}")
                print(f"     → {trigger['recommendation']}")
                print()

        # Medium risk triggers
        if self.triggers_detected['medium_risk']:
            print(f"\n🟡 MEDIUM RISK TRIGGERS ({len(self.triggers_detected['medium_risk'])})")
            print("   ⚠️  REVIEW STRONGLY RECOMMENDED")
            print()
            for trigger in self.triggers_detected['medium_risk']:
                print(f"   • {trigger['message']}")
                print(f"     → {trigger['recommendation']}")
                print()

        # Low risk triggers
        if self.triggers_detected['low_risk']:
            print(f"\n🟢 LOW RISK TRIGGERS ({len(self.triggers_detected['low_risk'])})")
            print()
            for trigger in self.triggers_detected['low_risk']:
                print(f"   • {trigger['message']}")
                print()

        print("="*70)
        print("\n📋 NEXT STEPS:")
        print()

        if self.triggers_detected['high_risk']:
            print("   1. PAUSE implementation")
            print("   2. Review: .claude/ARCHITECTURAL_DECISION_FRAMEWORK.md")
            print("   3. Complete 30-minute architectural review checklist")
            print("   4. Create ADR in docs/architecture/decisions/")
            print("   5. Get user approval for high-risk changes")
            print()
            return 2  # High risk
        elif self.triggers_detected['medium_risk']:
            print("   1. Review: .claude/ARCHITECTURAL_DECISION_FRAMEWORK.md")
            print("   2. Consider creating an ADR if decision is significant")
            print("   3. Proceed with caution")
            print()
            return 1  # Medium risk
        else:
            print("   1. Proceed with implementation")
            print("   2. Follow standard development checklist")
            print()
            return 0  # Low risk

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Detect architectural triggers in staged git changes'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    detector = ArchitecturalTriggerDetector(verbose=args.verbose)
    exit_code = detector.analyze()

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
