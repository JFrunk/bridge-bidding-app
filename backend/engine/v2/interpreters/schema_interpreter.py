"""
Schema Interpreter for V2 Bidding Engine

Reads JSON schema files and evaluates rules against hand features
to determine appropriate bids.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class BidCandidate:
    """A potential bid with its rule and score."""
    bid: str
    rule_id: str
    priority: int
    explanation: str
    forcing: str
    conditions_met: Dict[str, bool]


class SchemaInterpreter:
    """
    Interprets JSON bidding schemas and evaluates rules against features.

    The interpreter:
    1. Loads schema files
    2. Evaluates each rule's conditions against features
    3. Returns matching bids sorted by priority
    """

    def __init__(self, schema_dir: str = None):
        """
        Initialize interpreter with schema directory.

        Args:
            schema_dir: Path to directory containing JSON schema files.
                       Defaults to engine/v2/schemas/
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent.parent / 'schemas'
        self.schema_dir = Path(schema_dir)
        self.schemas: Dict[str, Dict] = {}
        self._load_schemas()

    def _load_schemas(self):
        """Load all JSON schema files from the schema directory."""
        for schema_file in self.schema_dir.glob('*.json'):
            try:
                with open(schema_file, 'r') as f:
                    schema = json.load(f)
                    category = schema.get('category', schema_file.stem)
                    self.schemas[category] = schema
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load schema {schema_file}: {e}")

    def evaluate(self, features: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """
        Evaluate all schemas against features and return best bid.

        Args:
            features: Flat feature dictionary from enhanced_extractor

        Returns:
            Tuple of (bid, explanation) or None if no rule matches
        """
        candidates = []

        # Evaluate all schemas
        for category, schema in self.schemas.items():
            category_candidates = self._evaluate_schema(schema, features)
            candidates.extend(category_candidates)

        if not candidates:
            return None

        # Sort by priority (highest first)
        candidates.sort(key=lambda c: c.priority, reverse=True)

        # Return best match
        best = candidates[0]
        return (best.bid, best.explanation)

    def evaluate_with_details(self, features: Dict[str, Any]) -> List[BidCandidate]:
        """
        Evaluate all schemas and return all matching candidates with details.

        Useful for debugging and understanding why certain bids are chosen.

        Args:
            features: Flat feature dictionary

        Returns:
            List of BidCandidate objects sorted by priority
        """
        candidates = []

        for category, schema in self.schemas.items():
            category_candidates = self._evaluate_schema(schema, features)
            candidates.extend(category_candidates)

        candidates.sort(key=lambda c: c.priority, reverse=True)
        return candidates

    def _evaluate_schema(self, schema: Dict, features: Dict[str, Any]) -> List[BidCandidate]:
        """Evaluate all rules in a schema against features."""
        candidates = []

        for rule in schema.get('rules', []):
            if self._evaluate_rule(rule, features):
                bid = self._resolve_bid(rule.get('bid', 'Pass'), features)
                explanation = self._format_explanation(rule.get('explanation', ''), features)

                candidate = BidCandidate(
                    bid=bid,
                    rule_id=rule.get('id', 'unknown'),
                    priority=rule.get('priority', 0),
                    explanation=explanation,
                    forcing=rule.get('forcing', 'none'),
                    conditions_met={}  # Could populate for debugging
                )
                candidates.append(candidate)

        return candidates

    def _evaluate_rule(self, rule: Dict, features: Dict[str, Any]) -> bool:
        """
        Evaluate a single rule's conditions against features.

        Args:
            rule: Rule dictionary from schema
            features: Feature dictionary

        Returns:
            True if all conditions are met
        """
        conditions = rule.get('conditions', {})
        return self._evaluate_conditions(conditions, features)

    def _evaluate_conditions(self, conditions: Dict, features: Dict[str, Any]) -> bool:
        """
        Recursively evaluate conditions dictionary.

        Supports:
        - Simple key: value matching
        - Numeric comparisons: {"min": x, "max": y, "exact": z}
        - Boolean logic: OR, AND, NOT
        - Set membership: {"in": [...]}
        """
        for key, expected in conditions.items():
            # Handle OR conditions
            if key == 'OR':
                if not isinstance(expected, list):
                    return False
                if not any(self._evaluate_conditions(cond, features) for cond in expected):
                    return False
                continue

            # Handle AND conditions (implicit in normal conditions)
            if key == 'AND':
                if not isinstance(expected, list):
                    return False
                if not all(self._evaluate_conditions(cond, features) for cond in expected):
                    return False
                continue

            # Handle NOT conditions
            if key == 'NOT':
                if self._evaluate_conditions(expected, features):
                    return False
                continue

            # Get actual value from features
            actual = features.get(key)

            # Handle dict conditions (comparisons)
            if isinstance(expected, dict):
                if not self._evaluate_comparison(actual, expected, features):
                    return False

            # Handle list membership
            elif isinstance(expected, list):
                if actual not in expected:
                    return False

            # Handle direct equality
            else:
                if actual != expected:
                    return False

        return True

    def _evaluate_comparison(self, actual: Any, comparison: Dict, features: Dict[str, Any]) -> bool:
        """
        Evaluate numeric/string comparison conditions.

        Supports:
        - min: actual >= value
        - max: actual <= value
        - exact: actual == value
        - in: actual in list
        - not_in: actual not in list
        - Reference values: "spades_length" means use features['spades_length']
        """
        if actual is None:
            return False

        for op, value in comparison.items():
            # Resolve reference values (e.g., "spades_length" -> features['spades_length'])
            if isinstance(value, str) and value in features:
                value = features[value]

            if op == 'min':
                if actual < value:
                    return False

            elif op == 'max':
                if actual > value:
                    return False

            elif op == 'exact':
                if actual != value:
                    return False

            elif op == 'in':
                if actual not in value:
                    return False

            elif op == 'not_in':
                if actual in value:
                    return False

        return True

    def _resolve_bid(self, bid_template: str, features: Dict[str, Any]) -> str:
        """
        Resolve bid template with feature values.

        Examples:
        - "1{longest_suit}" -> "1♠"
        - "2{partner_suit}" -> "2♥"
        """
        # Handle dynamic bid templates
        pattern = r'\{(\w+)\}'

        def replace_var(match):
            var_name = match.group(1)

            # Special case: partner_suit
            if var_name == 'partner_suit':
                partner_bid = features.get('partner_last_bid', '')
                if partner_bid and len(partner_bid) >= 2:
                    return partner_bid[1:]
                return ''

            # Special case: opponent_suit
            if var_name == 'opponent_suit':
                opening_bid = features.get('opening_bid', '')
                if opening_bid and len(opening_bid) >= 2:
                    return opening_bid[1:]
                return ''

            # Get from features
            value = features.get(var_name, '')
            return str(value) if value else ''

        resolved = re.sub(pattern, replace_var, bid_template)
        return resolved

    def _format_explanation(self, template: str, features: Dict[str, Any]) -> str:
        """
        Format explanation string with feature values.

        Examples:
        - "Opening with {hcp} HCP" -> "Opening with 15 HCP"
        """
        pattern = r'\{(\w+)\}'

        def replace_var(match):
            var_name = match.group(1)
            value = features.get(var_name)
            if value is not None:
                return str(value)
            return match.group(0)  # Keep original if not found

        return re.sub(pattern, replace_var, template)

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """Find a rule by its ID across all schemas."""
        for schema in self.schemas.values():
            for rule in schema.get('rules', []):
                if rule.get('id') == rule_id:
                    return rule
        return None

    def list_rules(self, category: str = None) -> List[Dict]:
        """List all rules, optionally filtered by category."""
        rules = []
        for cat, schema in self.schemas.items():
            if category and cat != category:
                continue
            for rule in schema.get('rules', []):
                rules.append({
                    'category': cat,
                    **rule
                })
        return sorted(rules, key=lambda r: r.get('priority', 0), reverse=True)
