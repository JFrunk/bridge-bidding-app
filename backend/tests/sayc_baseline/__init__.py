"""
SAYC Baseline Test Suite

This package provides ground-truth validation for SAYC bidding logic.

Components:
- sayc_ground_truth.json: Test cases and rules from ACBL SAYC booklet
- sayc_logic_engine.py: Reference implementation for validation
- sayc_baseline_parser.py: Parser for saycbridge test format (to be added)

Usage:
    from tests.sayc_baseline import SAYCLogicEngine, SAYCTestRunner

    # Validate a single bid
    engine = SAYCLogicEngine()
    result = engine.classify_rebid('D', 'H', 2, 17)

    # Run all ground truth tests
    runner = SAYCTestRunner()
    results = runner.run_all_tests()
"""

from .sayc_logic_engine import (
    SAYCLogicEngine,
    SAYCTestRunner,
    BidClassification,
    ValidationResult
)

__all__ = [
    'SAYCLogicEngine',
    'SAYCTestRunner',
    'BidClassification',
    'ValidationResult'
]
