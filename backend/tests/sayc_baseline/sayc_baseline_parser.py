"""
SAYCBridge Baseline Parser

Parses the z3b_baseline.txt file from the saycbridge project into
a structured format for testing our bidding engine.

Format of z3b_baseline.txt:
    test_[category_name]:
    FAIL: [actual] (expected [expected]) for [hand] (hcp: X lp: Y sp: Z), history: [history]
    Pass X of Y hands

Hand notation: Spades.Hearts.Diamonds.Clubs (e.g., "K92.QJT7.KQ4.AJ7")
History notation: Space-separated bids (e.g., "1D P 1S P" or "1H P P")
"""

import re
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path


@dataclass
class BaselineTestCase:
    """A single test case from the baseline."""
    test_id: str
    category: str
    hand: str  # Dot-separated: S.H.D.C
    history: List[str]  # Bidding history before this bid
    expected_bid: str  # The correct SAYC bid
    actual_bid: Optional[str]  # What saycbridge produced (for failed tests)
    hcp: int
    lp: int  # Length points
    sp: int  # Support points
    passed: bool
    is_subtest: bool = False
    subtest_of: Optional[str] = None


@dataclass
class CategorySummary:
    """Summary of test results for a category."""
    category: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    test_cases: List[BaselineTestCase]


class SAYCBaselineParser:
    """
    Parser for saycbridge z3b_baseline.txt format.

    Converts to structured test cases that can be used to validate
    our bidding engine against the SAYC ground truth.
    """

    # Bid notation mapping from saycbridge to our format
    BID_MAP = {
        'P': 'Pass',
        'X': 'X',
        'XX': 'XX',
        'N': 'NT',
        '1N': '1NT', '2N': '2NT', '3N': '3NT', '4N': '4NT', '5N': '5NT', '6N': '6NT', '7N': '7NT',
        'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠',
    }

    # Regex patterns
    CATEGORY_PATTERN = re.compile(r'^test_(\w+):$')
    FAIL_PATTERN = re.compile(
        r'FAIL: (\S+) \(expected (\S+)\) for ([^\s]+) '
        r'\(hcp: (\d+) lp: (\d+) sp: (\d+)\), history: (.*)$'
    )
    SUBTEST_PATTERN = re.compile(r'\(subtest of ([^)]+)\)')
    SUMMARY_PATTERN = re.compile(r'Pass (\d+) of (\d+) hands')
    WARNING_PATTERN = re.compile(r'^WARNING:')

    def __init__(self):
        self.categories: Dict[str, CategorySummary] = {}
        self.all_test_cases: List[BaselineTestCase] = []
        self.total_passed = 0
        self.total_tests = 0

    def parse_file(self, filepath: str) -> Dict[str, CategorySummary]:
        """
        Parse the baseline file and return categorized test cases.

        Args:
            filepath: Path to z3b_baseline.txt

        Returns:
            Dict mapping category name to CategorySummary
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Baseline file not found: {filepath}")

        with open(path, 'r') as f:
            lines = f.readlines()

        current_category = None
        category_cases = []
        test_counter = 0

        for line in lines:
            line = line.strip()

            # Skip empty lines and warnings
            if not line or self.WARNING_PATTERN.match(line):
                continue

            # Check for category header
            cat_match = self.CATEGORY_PATTERN.match(line)
            if cat_match:
                # Save previous category
                if current_category and category_cases:
                    self._save_category(current_category, category_cases)

                current_category = cat_match.group(1)
                category_cases = []
                continue

            # Check for FAIL line
            fail_match = self.FAIL_PATTERN.match(line)
            if fail_match:
                actual, expected, hand, hcp, lp, sp, history_str = fail_match.groups()

                # Check for subtest
                is_subtest = False
                subtest_of = None
                subtest_match = self.SUBTEST_PATTERN.search(line)
                if subtest_match:
                    is_subtest = True
                    subtest_of = subtest_match.group(1)

                test_counter += 1
                test_case = BaselineTestCase(
                    test_id=f"{current_category}_{test_counter:04d}",
                    category=current_category,
                    hand=hand,
                    history=self._parse_history(history_str),
                    expected_bid=self._convert_bid(expected),
                    actual_bid=self._convert_bid(actual) if actual != 'None' else None,
                    hcp=int(hcp),
                    lp=int(lp),
                    sp=int(sp),
                    passed=False,
                    is_subtest=is_subtest,
                    subtest_of=subtest_of
                )
                category_cases.append(test_case)
                self.all_test_cases.append(test_case)
                continue

            # Check for summary line
            summary_match = self.SUMMARY_PATTERN.match(line)
            if summary_match:
                passed, total = int(summary_match.group(1)), int(summary_match.group(2))
                # Add implicit passed tests
                failed_count = len(category_cases)
                passed_count = passed

                # Update totals
                self.total_passed += passed
                self.total_tests += total
                continue

        # Save last category
        if current_category and category_cases:
            self._save_category(current_category, category_cases)

        return self.categories

    def _save_category(self, name: str, cases: List[BaselineTestCase]):
        """Save a category's test cases."""
        failed = len(cases)
        # We'll estimate total from the summary line later
        self.categories[name] = CategorySummary(
            category=name,
            total=0,  # Will be updated
            passed=0,
            failed=failed,
            pass_rate=0.0,
            test_cases=cases
        )

    def _parse_history(self, history_str: str) -> List[str]:
        """
        Parse history string to list of bids.

        Args:
            history_str: Space-separated bids like "1D P 1S P"

        Returns:
            List of converted bids like ["1♦", "Pass", "1♠", "Pass"]
        """
        if not history_str or history_str.strip() == '':
            return []

        bids = history_str.strip().split()
        return [self._convert_bid(bid) for bid in bids]

    def _convert_bid(self, bid: str) -> str:
        """
        Convert saycbridge bid notation to our format.

        Examples:
            "1D" -> "1♦"
            "P" -> "Pass"
            "2N" -> "2NT"
            "X" -> "X"
        """
        if not bid or bid == 'None':
            return None

        # Direct mapping
        if bid in self.BID_MAP:
            return self.BID_MAP[bid]

        # Level + strain bids (1D, 2H, 3S, etc.)
        if len(bid) >= 2 and bid[0].isdigit():
            level = bid[0]
            strain = bid[1:]

            if strain == 'N':
                return f"{level}NT"
            elif strain in self.BID_MAP:
                return f"{level}{self.BID_MAP[strain]}"
            else:
                # Unknown strain, return as-is
                return bid

        return bid

    def convert_hand_to_dict(self, hand_str: str) -> Dict[str, str]:
        """
        Convert dot-notation hand to dict format.

        Args:
            hand_str: "K92.QJT7.KQ4.AJ7" (S.H.D.C)

        Returns:
            {'S': 'K92', 'H': 'QJT7', 'D': 'KQ4', 'C': 'AJ7'}
        """
        parts = hand_str.split('.')
        if len(parts) != 4:
            return {}
        return {
            'S': parts[0],
            'H': parts[1],
            'D': parts[2],
            'C': parts[3]
        }

    def get_failed_tests(self) -> List[BaselineTestCase]:
        """Get all failed test cases (excluding subtests)."""
        return [tc for tc in self.all_test_cases if not tc.is_subtest]

    def get_tests_by_category(self, category: str) -> List[BaselineTestCase]:
        """Get test cases for a specific category."""
        return [tc for tc in self.all_test_cases if tc.category == category]

    def export_to_json(self, filepath: str):
        """Export parsed test cases to JSON format."""
        data = {
            'metadata': {
                'source': 'saycbridge z3b_baseline.txt',
                'total_tests': self.total_tests,
                'total_passed': self.total_passed,
                'pass_rate': self.total_passed / self.total_tests if self.total_tests > 0 else 0
            },
            'categories': {
                name: {
                    'total': cat.total,
                    'passed': cat.passed,
                    'failed': cat.failed,
                    'pass_rate': cat.pass_rate,
                    'test_cases': [asdict(tc) for tc in cat.test_cases]
                }
                for name, cat in self.categories.items()
            },
            'all_failed_tests': [asdict(tc) for tc in self.get_failed_tests()]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Exported {len(self.all_test_cases)} test cases to {filepath}")

    def print_summary(self):
        """Print summary of parsed baseline."""
        print("=" * 60)
        print("SAYCBRIDGE BASELINE SUMMARY")
        print("=" * 60)
        print(f"Total tests: {self.total_tests}")
        print(f"Total passed: {self.total_passed}")
        print(f"Pass rate: {self.total_passed/self.total_tests*100:.1f}%" if self.total_tests > 0 else "N/A")
        print()
        print("Categories with failures:")
        print("-" * 60)
        for name, cat in sorted(self.categories.items(), key=lambda x: -len(x[1].test_cases)):
            if cat.test_cases:
                print(f"  {name}: {len(cat.test_cases)} failed tests")
        print()


def parse_baseline() -> Tuple[SAYCBaselineParser, List[BaselineTestCase]]:
    """
    Convenience function to parse the baseline file.

    Returns:
        Tuple of (parser, failed_test_cases)
    """
    parser = SAYCBaselineParser()
    baseline_path = Path(__file__).parent / "z3b_baseline.txt"

    if baseline_path.exists():
        parser.parse_file(str(baseline_path))
        return parser, parser.get_failed_tests()
    else:
        print(f"Warning: Baseline file not found at {baseline_path}")
        return parser, []


# ==================== Main ====================

if __name__ == "__main__":
    parser = SAYCBaselineParser()
    baseline_path = Path(__file__).parent / "z3b_baseline.txt"

    if baseline_path.exists():
        parser.parse_file(str(baseline_path))
        parser.print_summary()

        # Export to JSON
        json_path = Path(__file__).parent / "baseline_parsed.json"
        parser.export_to_json(str(json_path))

        # Show sample test cases
        print("\nSample failed test cases:")
        print("-" * 60)
        for i, tc in enumerate(parser.get_failed_tests()[:5]):
            print(f"\n{i+1}. {tc.test_id}")
            print(f"   Category: {tc.category}")
            print(f"   Hand: {tc.hand} ({tc.hcp} HCP)")
            print(f"   History: {' -> '.join(tc.history) if tc.history else 'Opening'}")
            print(f"   Expected: {tc.expected_bid}")
            print(f"   saycbridge got: {tc.actual_bid}")
    else:
        print(f"Baseline file not found: {baseline_path}")
        print("Download from: https://github.com/eseidel/saycbridge/blob/master/src/z3b_baseline.txt")
