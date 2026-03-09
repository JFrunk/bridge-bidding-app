"""
Gap Analyzer for V2 Bidding Engine

Analyzes why rules didn't match and what gaps exist between
a hand's features and the rule requirements. Used for debugging
and UI feedback (e.g., "missing 1 HCP" or "need diamond stopper").

Extracted from SchemaInterpreter to keep that class focused on
rule evaluation and bid selection.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """
    Analyzes rule matching gaps for debugging and user feedback.

    Takes a SchemaInterpreter instance to access schemas and shared
    matching logic (_resolve_bid, _matches_trigger, _matches_pattern).
    """

    def __init__(self, interpreter):
        """
        Args:
            interpreter: SchemaInterpreter instance providing schema
                        access and pattern matching utilities.
        """
        self.interpreter = interpreter

    def get_rule_gap_analysis(
        self,
        features: Dict[str, Any],
        target_bid: str = None,
        max_rules: int = 10
    ) -> List[Dict]:
        """
        Analyze why rules didn't match and what gaps exist.

        Returns detailed information about:
        1. Which conditions passed vs failed
        2. For numeric conditions, how far off the actual value was
        3. What would need to change for the rule to match

        This enables visual debugging in the UI showing exactly why
        specific bids were rejected (e.g., "missing 1 HCP" or "need diamond stopper").

        Args:
            features: The extracted features for this hand/auction
            target_bid: If specified, only analyze rules for this bid
            max_rules: Maximum number of rules to return (sorted by priority)

        Returns:
            List of rule analysis dicts with gap information
        """
        analyses = []

        for category, schema in self.interpreter.schemas.items():
            for rule in schema.get('rules', []):
                bid = self.interpreter._resolve_bid(rule.get('bid', 'Pass'), features, rule)

                # Skip rules where bid resolution failed
                if bid is None:
                    continue

                # Filter by target bid if specified
                if target_bid and bid != target_bid:
                    continue

                analysis = self._analyze_rule_gaps(rule, features, category)
                analyses.append(analysis)

        # Sort by: matched rules first, then by how close (fewest gaps)
        analyses.sort(key=lambda a: (
            -1 if a['matched'] else 0,  # Matched rules first
            a['gap_count'],              # Then by fewest gaps
            -a['priority']               # Then by priority
        ))

        return analyses[:max_rules]

    def _analyze_rule_gaps(
        self,
        rule: Dict,
        features: Dict[str, Any],
        category: str
    ) -> Dict:
        """
        Analyze a single rule's conditions and identify specific gaps.

        Returns a detailed analysis including:
        - Which conditions passed/failed
        - For numeric constraints, the actual vs required values
        - A human-readable gap description
        """
        rule_id = rule.get('id', 'unknown')
        bid = self.interpreter._resolve_bid(rule.get('bid', 'Pass'), features, rule)
        priority = rule.get('priority', 0)
        description = rule.get('description', rule.get('explanation', ''))

        # Check trigger first
        trigger = rule.get('trigger')
        trigger_matched = True
        trigger_gap = None
        if trigger:
            trigger_matched = self.interpreter._matches_trigger(trigger, features)
            if not trigger_matched:
                trigger_gap = f"Auction pattern doesn't match: {trigger}"

        # Analyze conditions
        conditions = rule.get('conditions', {})
        constraints = rule.get('constraints', {})
        # constraints can be a list of dicts (e.g. [{"feature": "hcp", "min": 12}])
        # or a dict — merge dict constraints with conditions, analyze list separately
        if isinstance(constraints, list):
            condition_analysis = self._analyze_conditions(conditions, features)
            condition_analysis.extend(
                self._analyze_array_constraints_gaps(constraints, features)
            )
        else:
            all_conditions = {**conditions, **constraints}
            condition_analysis = self._analyze_conditions(all_conditions, features)

        # Calculate overall match
        all_passed = trigger_matched and all(
            c['passed'] for c in condition_analysis
        )
        gap_count = sum(1 for c in condition_analysis if not c['passed'])
        if not trigger_matched:
            gap_count += 1

        return {
            'rule_id': rule_id,
            'bid': bid,
            'category': category,
            'priority': priority,
            'description': description,
            'matched': all_passed,
            'gap_count': gap_count,
            'trigger': trigger,
            'trigger_matched': trigger_matched,
            'trigger_gap': trigger_gap,
            'conditions': condition_analysis,
            'forcing': rule.get('forcing', 'none'),
            'sets_forcing_level': rule.get('sets_forcing_level')
        }

    def _analyze_conditions(
        self,
        conditions: Dict,
        features: Dict[str, Any],
        prefix: str = ''
    ) -> List[Dict]:
        """
        Recursively analyze conditions and return detailed gap information.

        For each condition, returns:
        - key: The condition key (e.g., 'hcp', 'is_balanced')
        - required: What the condition requires
        - actual: The actual feature value
        - passed: Whether the condition was met
        - gap: Human-readable description of the gap (if failed)
        """
        results = []

        for key, expected in conditions.items():
            full_key = f"{prefix}{key}" if prefix else key

            # Handle boolean logic operators
            if key == 'OR':
                or_results = []
                for i, sub_cond in enumerate(expected):
                    sub_analysis = self._analyze_conditions(sub_cond, features, f"{full_key}[{i}].")
                    or_results.append(sub_analysis)
                # OR passes if any branch passes
                any_passed = any(
                    all(c['passed'] for c in branch) for branch in or_results
                )
                results.append({
                    'key': full_key,
                    'type': 'OR',
                    'required': 'any branch',
                    'actual': 'see branches',
                    'passed': any_passed,
                    'gap': None if any_passed else 'No OR branch matched',
                    'branches': or_results
                })
                continue

            if key == 'AND':
                and_results = []
                for i, sub_cond in enumerate(expected):
                    sub_analysis = self._analyze_conditions(sub_cond, features, f"{full_key}[{i}].")
                    and_results.extend(sub_analysis)
                results.extend(and_results)
                continue

            if key == 'NOT':
                not_analysis = self._analyze_conditions(expected, features, f"{full_key}.")
                # NOT passes if the inner condition fails
                inner_passed = all(c['passed'] for c in not_analysis)
                results.append({
                    'key': full_key,
                    'type': 'NOT',
                    'required': 'NOT satisfied',
                    'actual': 'condition matched' if inner_passed else 'condition not matched',
                    'passed': not inner_passed,
                    'gap': 'Condition should NOT match but does' if inner_passed else None,
                    'inner': not_analysis
                })
                continue

            # Handle special expert constraints
            if key == 'stoppers_required':
                stopped_count = sum(1 for suit in ['spades', 'hearts', 'diamonds', 'clubs']
                                   if features.get(f'{suit}_stopped', False))
                passed = stopped_count >= expected
                gap = None if passed else f"Need {expected} stoppers, have {stopped_count}"
                results.append({
                    'key': full_key,
                    'type': 'numeric',
                    'required': f">= {expected}",
                    'actual': stopped_count,
                    'passed': passed,
                    'gap': gap,
                    'shortfall': expected - stopped_count if not passed else 0
                })
                continue

            if key == 'stoppers_in':
                missing_stoppers = []
                for suit_ref in expected:
                    if suit_ref == 'opponent_suit':
                        opening_bid = features.get('opening_bid', '')
                        if opening_bid and len(opening_bid) >= 2:
                            suit_symbol = opening_bid[1] if opening_bid[0].isdigit() else None
                            suit_map = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
                            suit_name = suit_map.get(suit_symbol)
                            if suit_name and not features.get(f'{suit_name}_stopped', False):
                                missing_stoppers.append(suit_name)
                    else:
                        if not features.get(f'{suit_ref}_stopped', False):
                            missing_stoppers.append(suit_ref)

                passed = len(missing_stoppers) == 0
                gap = None if passed else f"Missing stopper in: {', '.join(missing_stoppers)}"
                results.append({
                    'key': full_key,
                    'type': 'stopper',
                    'required': expected,
                    'actual': f"Missing: {missing_stoppers}" if missing_stoppers else "All stopped",
                    'passed': passed,
                    'gap': gap,
                    'missing_stoppers': missing_stoppers
                })
                continue

            # Get actual value from features
            actual = features.get(key)

            # Handle dict conditions (comparisons)
            if isinstance(expected, dict):
                result = self._analyze_comparison(key, actual, expected, features)
                results.append(result)

            # Handle list membership (in: [...])
            elif isinstance(expected, list):
                matched = False
                for pattern in expected:
                    if isinstance(pattern, str) and isinstance(actual, str):
                        if self.interpreter._matches_pattern(pattern, actual):
                            matched = True
                            break
                    elif actual == pattern:
                        matched = True
                        break

                gap = None if matched else f"'{actual}' not in {expected}"
                results.append({
                    'key': full_key,
                    'type': 'set',
                    'required': f"in {expected}",
                    'actual': actual,
                    'passed': matched,
                    'gap': gap
                })

            # Handle direct equality
            else:
                if isinstance(expected, str) and isinstance(actual, str):
                    passed = self.interpreter._matches_pattern(expected, actual)
                else:
                    passed = actual == expected

                gap = None if passed else f"Expected {expected}, got {actual}"
                results.append({
                    'key': full_key,
                    'type': 'equality',
                    'required': expected,
                    'actual': actual,
                    'passed': passed,
                    'gap': gap
                })

        return results

    def _analyze_comparison(
        self,
        key: str,
        actual: Any,
        comparison: Dict,
        features: Dict[str, Any]
    ) -> Dict:
        """
        Analyze a numeric/string comparison and return detailed gap info.
        """
        if actual is None:
            return {
                'key': key,
                'type': 'comparison',
                'required': comparison,
                'actual': None,
                'passed': False,
                'gap': f"Feature '{key}' is not set"
            }

        failures = []
        details = {}

        for op, value in comparison.items():
            # Resolve reference values
            if isinstance(value, str) and value in features:
                resolved_value = features[value]
                details[f'{op}_reference'] = value
                value = resolved_value

            if op == 'min':
                try:
                    if actual < value:
                        # Only calculate numeric difference if both are numbers
                        if isinstance(actual, (int, float)) and isinstance(value, (int, float)):
                            failures.append(f"min {value} (have {actual}, need +{value - actual})")
                            details['min_shortfall'] = value - actual
                        else:
                            failures.append(f"min {value} (have {actual})")
                except TypeError:
                    # Can't compare these types (e.g., string quality levels)
                    failures.append(f"min {value} (have {actual})")
                details['min'] = value

            elif op == 'max':
                try:
                    if actual > value:
                        # Only calculate numeric difference if both are numbers
                        if isinstance(actual, (int, float)) and isinstance(value, (int, float)):
                            failures.append(f"max {value} (have {actual}, excess {actual - value})")
                            details['max_excess'] = actual - value
                        else:
                            failures.append(f"max {value} (have {actual})")
                except TypeError:
                    # Can't compare these types
                    failures.append(f"max {value} (have {actual})")
                details['max'] = value

            elif op == 'exact':
                if actual != value:
                    failures.append(f"exactly {value} (have {actual})")
                details['exact'] = value

            elif op == 'in':
                if actual not in value:
                    failures.append(f"in {value}")
                details['in'] = value

            elif op == 'not_in':
                if actual in value:
                    failures.append(f"not in {value}")
                details['not_in'] = value

        passed = len(failures) == 0
        gap = None if passed else f"{key}: need " + ", ".join(failures)

        return {
            'key': key,
            'type': 'comparison',
            'required': comparison,
            'actual': actual,
            'passed': passed,
            'gap': gap,
            **details
        }

    def _analyze_array_constraints_gaps(
        self,
        constraints: List[Dict],
        features: Dict[str, Any]
    ) -> List[Dict]:
        """
        Analyze array-format constraints and return gap information.

        Each constraint is a dict like:
        {"feature": "hcp", "min": 12, "max": 14, "constraint_type": "HARD"}
        """
        results = []
        for constraint in constraints:
            feature = constraint.get('feature', '')
            if not feature:
                continue

            actual = features.get(feature)
            constraint_type = constraint.get('constraint_type', 'HARD')

            # Build comparison dict from constraint fields
            comparison = {}
            if 'min' in constraint:
                comparison['min'] = constraint['min']
            if 'max' in constraint:
                comparison['max'] = constraint['max']
            if 'exact' in constraint:
                comparison['exact'] = constraint['exact']

            if comparison:
                result = self._analyze_comparison(feature, actual, comparison, features)
                result['constraint_type'] = constraint_type
                results.append(result)
            elif 'expected' in constraint:
                # Boolean/equality constraint: {"feature": "is_balanced", "expected": true}
                expected = constraint['expected']
                if isinstance(expected, str) and isinstance(actual, str):
                    passed = self.interpreter._matches_pattern(expected, actual)
                else:
                    passed = actual == expected
                gap = None if passed else f"Expected {expected}, got {actual}"
                results.append({
                    'key': feature,
                    'type': 'equality',
                    'required': expected,
                    'actual': actual,
                    'passed': passed,
                    'gap': gap,
                    'constraint_type': constraint_type
                })
            elif 'value' in constraint:
                expected = constraint['value']
                passed = actual == expected
                gap = None if passed else f"Expected {expected}, got {actual}"
                results.append({
                    'key': feature,
                    'type': 'equality',
                    'required': expected,
                    'actual': actual,
                    'passed': passed,
                    'gap': gap,
                    'constraint_type': constraint_type
                })

        return results
