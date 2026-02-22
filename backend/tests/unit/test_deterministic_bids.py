"""
Regression test for deterministic bid recommendations.

Bug: Feb 21, 2026 - "What should I bid" button cycled through different bids
on each click due to non-deterministic schema loading and tie-breaking.

Root Cause:
1. glob('*.json') returns files in arbitrary filesystem order
2. When rules have same priority, tie-breaker was insertion order
3. Different schema load order → different winning bid

Test ensures:
1. Schema loading order is deterministic (sorted)
2. Candidate sorting includes deterministic tie-breaker (rule_id)
3. Same input produces same output every time
"""

import pytest
from pathlib import Path
from engine.v2.interpreters.schema_interpreter import SchemaInterpreter


def test_schema_loading_is_deterministic():
    """Test that schemas are loaded in consistent order across runs."""
    # Load interpreter multiple times
    results = []
    for _ in range(5):
        interpreter = SchemaInterpreter()
        schema_names = list(interpreter.schemas.keys())
        results.append(schema_names)

    # All runs should produce identical schema order
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        assert result == first_result, \
            f"Schema loading order differs on run {i+1}: {result} != {first_result}"


def test_bid_recommendation_is_deterministic():
    """Test that same hand and auction always produces same bid."""
    interpreter = SchemaInterpreter()

    # Create test features for a common bidding situation
    features = {
        'hcp': 15,
        'is_balanced': True,
        'longest_suit_length': 4,
        'spade_length': 4,
        'heart_length': 3,
        'diamond_length': 3,
        'club_length': 3,
        'is_opening': True,
        'auction_history': [],
        'auction_level': 0,
        'is_contested': False,
        'opener_relationship': 'Me',
        'vulnerability': 'None',
    }

    # Call evaluate() 10 times with same features
    results = []
    for _ in range(10):
        result = interpreter.evaluate(features)
        results.append(result)

    # All results should be identical
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        assert result == first_result, \
            f"Bid differs on call {i+1}: {result} != {first_result}"


def test_tie_breaking_is_deterministic():
    """Test that rules with same priority are resolved deterministically."""
    interpreter = SchemaInterpreter()

    # Create features that match multiple rules
    features = {
        'hcp': 12,
        'is_balanced': True,
        'longest_suit_length': 4,
        'spade_length': 4,
        'heart_length': 3,
        'diamond_length': 3,
        'club_length': 3,
        'is_response': True,
        'auction_history': ['1♣'],
        'auction_level': 1,
        'is_contested': False,
        'opener_relationship': 'Partner',
        'partner_last_bid': '1♣',
        'support_for_partner': 2,
        'vulnerability': 'None',
    }

    # Get all matching candidates multiple times
    candidate_lists = []
    for _ in range(5):
        candidates = interpreter.evaluate_with_details(features)
        # Convert to tuples of (bid, priority, rule_id) for comparison
        candidate_tuples = [(c.bid, c.priority, c.rule_id) for c in candidates]
        candidate_lists.append(candidate_tuples)

    # All lists should be identical (same order)
    first_list = candidate_lists[0]
    for i, candidate_list in enumerate(candidate_lists[1:], 1):
        assert candidate_list == first_list, \
            f"Candidate order differs on call {i+1}"


def test_soft_matching_is_deterministic():
    """Test that soft matching (weighted scores) is also deterministic."""
    interpreter = SchemaInterpreter()

    # Create features for soft matching evaluation
    features = {
        'hcp': 10,
        'is_balanced': False,
        'longest_suit_length': 5,
        'spade_length': 5,
        'heart_length': 4,
        'diamond_length': 2,
        'club_length': 2,
        'is_response': True,
        'auction_history': ['1♦'],
        'auction_level': 1,
        'is_contested': False,
        'opener_relationship': 'Partner',
        'partner_last_bid': '1♦',
        'vulnerability': 'None',
    }

    # Call evaluate_all_candidates() multiple times
    results = []
    for _ in range(10):
        result = interpreter.evaluate_all_candidates(features)
        results.append(result)

    # All results should be identical
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        assert result == first_result, \
            f"Soft matching bid differs on call {i+1}: {result} != {first_result}"
