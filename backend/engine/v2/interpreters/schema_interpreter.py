"""
Schema Interpreter for V2 Bidding Engine

Reads JSON schema files and evaluates rules against hand features
to determine appropriate bids.

Includes Forcing Level state tracking for proper handling of:
- Non-forcing bids
- One-round forcing bids (new suit responses in SAYC)
- Game forcing sequences (2/1, jump shifts, 4th suit forcing)
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ForcingLevel(Enum):
    """Forcing level states for auction tracking."""
    NON_FORCING = "NON_FORCING"
    FORCING_1_ROUND = "FORCING_1_ROUND"
    GAME_FORCE = "GAME_FORCE"


@dataclass
class AuctionState:
    """Tracks the current state of the auction for forcing logic."""
    forcing_level: ForcingLevel = ForcingLevel.NON_FORCING
    is_game_forced: bool = False
    forcing_source: Optional[str] = None  # Rule ID that established forcing
    bids_since_forcing: int = 0  # Track rounds since forcing was set

    def reset(self):
        """Reset state for a new deal."""
        self.forcing_level = ForcingLevel.NON_FORCING
        self.is_game_forced = False
        self.forcing_source = None
        self.bids_since_forcing = 0


@dataclass
class BidCandidate:
    """A potential bid with its rule and score."""
    bid: str
    rule_id: str
    priority: int
    explanation: str
    forcing: str
    conditions_met: Dict[str, bool]
    sets_forcing_level: Optional[str] = None  # The forcing level this bid establishes


@dataclass
class BidValidationResult:
    """Result of validating a bid against forcing constraints."""
    is_valid: bool
    reason: Optional[str] = None
    violation_type: Optional[str] = None  # "GAME_FORCE_VIOLATION", "ONE_ROUND_VIOLATION"


class SchemaInterpreter:
    """
    Interprets JSON bidding schemas and evaluates rules against features.

    The interpreter:
    1. Loads schema files
    2. Evaluates each rule's conditions against features
    3. Returns matching bids sorted by priority
    4. Tracks forcing level state across the auction

    Forcing Level State Machine:
    - NON_FORCING: Any bid including Pass is valid
    - FORCING_1_ROUND: Partner cannot pass on their next turn
    - GAME_FORCE: Neither partner can pass until game is reached (sticky)
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

        # Forcing level state tracking
        self.auction_state = AuctionState()

        self._load_schemas()

    def reset_state(self):
        """Reset auction state for a new deal."""
        self.auction_state.reset()

    def get_forcing_state(self) -> Dict[str, Any]:
        """Get current forcing state for debugging/display."""
        return {
            'forcing_level': self.auction_state.forcing_level.value,
            'is_game_forced': self.auction_state.is_game_forced,
            'forcing_source': self.auction_state.forcing_source,
            'bids_since_forcing': self.auction_state.bids_since_forcing
        }

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

    def _update_forcing_state(self, new_level: Optional[str], rule_id: str):
        """
        Update the forcing state based on a matched rule's metadata.

        State transitions:
        - GAME_FORCE is "sticky" - once set, cannot be unset until game reached
        - FORCING_1_ROUND expires after partner bids (tracked via bids_since_forcing)
        - NON_FORCING is the default state

        Args:
            new_level: The sets_forcing_level value from the matched rule
            rule_id: ID of the rule that matched (for tracking source)
        """
        # Game force is permanent (sticky)
        if self.auction_state.is_game_forced:
            return

        if new_level == "GAME_FORCE":
            self.auction_state.forcing_level = ForcingLevel.GAME_FORCE
            self.auction_state.is_game_forced = True
            self.auction_state.forcing_source = rule_id
            self.auction_state.bids_since_forcing = 0

        elif new_level == "FORCING_1_ROUND":
            self.auction_state.forcing_level = ForcingLevel.FORCING_1_ROUND
            self.auction_state.forcing_source = rule_id
            self.auction_state.bids_since_forcing = 0

        elif new_level == "NON_FORCING" or new_level is None:
            # Check if we should expire a 1-round forcing
            if self.auction_state.forcing_level == ForcingLevel.FORCING_1_ROUND:
                self.auction_state.bids_since_forcing += 1
                # After partner bids (2 bids in partnership), 1-round forcing expires
                if self.auction_state.bids_since_forcing >= 2:
                    self.auction_state.forcing_level = ForcingLevel.NON_FORCING
                    self.auction_state.forcing_source = None

    def validate_bid_against_forcing(self, bid: str) -> BidValidationResult:
        """
        Validate a bid against the current forcing state.

        This is the "falsification" logic that prevents illegal passes
        during forcing sequences.

        Args:
            bid: The bid to validate

        Returns:
            BidValidationResult indicating if the bid is legal
        """
        if bid != "Pass":
            return BidValidationResult(is_valid=True)

        # Check Game Force violation
        if self.auction_state.is_game_forced:
            return BidValidationResult(
                is_valid=False,
                reason="Cannot Pass: Auction is Game Forced. Partnership must reach game.",
                violation_type="GAME_FORCE_VIOLATION"
            )

        # Check 1-round forcing violation
        if self.auction_state.forcing_level == ForcingLevel.FORCING_1_ROUND:
            return BidValidationResult(
                is_valid=False,
                reason="Cannot Pass: Partner's bid is forcing for one round.",
                violation_type="ONE_ROUND_VIOLATION"
            )

        return BidValidationResult(is_valid=True)

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
                    conditions_met={},  # Could populate for debugging
                    sets_forcing_level=rule.get('sets_forcing_level')  # Track forcing level
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
        - Special expert constraints:
          - stoppers_required: minimum number of stopped suits
          - stoppers_in: specific suits that must be stopped
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

            # Handle special expert constraints
            if key == 'stoppers_required':
                # Count stopped suits from individual stopper features
                stopped_count = sum(1 for suit in ['spades', 'hearts', 'diamonds', 'clubs']
                                   if features.get(f'{suit}_stopped', False))
                if stopped_count < expected:
                    return False
                continue

            if key == 'stoppers_in':
                # Check that specific suits are stopped
                # expected is a list like ["spades", "hearts"] or ["opponent_suit"]
                if isinstance(expected, list):
                    for suit_ref in expected:
                        # Handle dynamic reference to opponent's suit
                        if suit_ref == 'opponent_suit':
                            opening_bid = features.get('opening_bid', '')
                            if opening_bid and len(opening_bid) >= 2:
                                suit_symbol = opening_bid[1] if opening_bid[0].isdigit() else None
                                suit_map = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
                                suit_name = suit_map.get(suit_symbol)
                                if suit_name and not features.get(f'{suit_name}_stopped', False):
                                    return False
                        else:
                            # Direct suit name
                            if not features.get(f'{suit_ref}_stopped', False):
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
