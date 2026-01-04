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
    is_limit_bid: bool = False  # Whether this bid shows a narrow range (pass or accept)


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
                    sets_forcing_level=rule.get('sets_forcing_level'),  # Track forcing level
                    is_limit_bid=rule.get('is_limit_bid', False)  # Track limit bids
                )
                candidates.append(candidate)

        return candidates

    def _evaluate_rule(self, rule: Dict, features: Dict[str, Any]) -> bool:
        """
        Evaluate a single rule's conditions and trigger against features.

        Supports two matching modes:
        1. Condition-based: Traditional conditions dictionary
        2. Trigger-based: Auction pattern matching like "1[CDHS] - ?" or "1C - Pass - 1H - ?"

        Args:
            rule: Rule dictionary from schema
            features: Feature dictionary

        Returns:
            True if all conditions are met (and trigger matches if present)
        """
        # Check trigger pattern first if present
        trigger = rule.get('trigger')
        if trigger:
            if not self._matches_trigger(trigger, features):
                return False

        # Then check conditions
        conditions = rule.get('conditions', {})
        if conditions:
            if not self._evaluate_conditions(conditions, features):
                return False

        # If we have constraints (alternative to conditions), check those too
        constraints = rule.get('constraints', {})
        if constraints:
            if not self._evaluate_conditions(constraints, features):
                return False

        return True

    def _matches_trigger(self, trigger: str, features: Dict[str, Any]) -> bool:
        """
        Match an auction trigger pattern against the current auction history.

        Trigger format examples:
        - "1[CDHS] - ?" matches any 1-level opening, we're next to bid
        - "1C - Pass - 1H - ?" matches specific sequence
        - "1[CD] - 1[HS] - ?" matches minor opening, major overcall, we're next

        The "?" represents "our turn to bid" (the position we're evaluating for).
        "-" separates bids in the auction.

        Args:
            trigger: The trigger pattern string
            features: Feature dictionary containing auction_history

        Returns:
            True if the current auction matches the trigger pattern
        """
        # Get auction history from features (stored with underscore prefix)
        auction_history = features.get('_auction_history', features.get('auction_history', []))
        if not auction_history and not trigger:
            return True

        # Parse trigger pattern - split by " - " to get bid patterns
        trigger_parts = [p.strip() for p in trigger.split(' - ')]

        # The last part should be "?" representing our turn
        if not trigger_parts or trigger_parts[-1] != '?':
            return False

        # Remove the "?" - we only match the preceding bids
        bid_patterns = trigger_parts[:-1]

        # Check if auction history length matches (we need exactly as many bids as patterns)
        if len(auction_history) != len(bid_patterns):
            return False

        # Match each bid in history against corresponding pattern
        for i, pattern in enumerate(bid_patterns):
            actual_bid = auction_history[i]
            if not self._matches_pattern(pattern, actual_bid):
                return False

        return True

    def _matches_pattern(self, pattern: str, value: str) -> bool:
        """
        Check if a value matches a pattern using exact match first, then regex.

        This enables flexible matching for bid patterns like:
        - "1[HS]" matches "1♥" or "1♠"
        - "1[CDHS]" matches any 1-level suit bid
        - "[12][HS]" matches 1♥, 1♠, 2♥, or 2♠

        The pattern uses a bridge-friendly regex syntax where:
        - C = ♣ (clubs)
        - D = ♦ (diamonds)
        - H = ♥ (hearts)
        - S = ♠ (spades)
        - N = NT (notrump)

        Args:
            pattern: The pattern to match (can be exact string or regex)
            value: The actual value to match against

        Returns:
            True if the value matches the pattern
        """
        if pattern is None or value is None:
            return pattern == value

        # 1. Try exact match first (fastest path)
        if pattern == value:
            return True

        # 2. Convert value's suit symbols to letters for regex matching
        # This allows patterns like "1[HS]" to match "1♥" or "1♠"
        value_normalized = value.replace('♣', 'C').replace('♦', 'D').replace('♥', 'H').replace('♠', 'S').replace('NT', 'N')

        # 3. Try regex match (flexible path)
        try:
            # Anchor the pattern to match the entire string
            regex_pattern = f"^{pattern}$"
            if re.match(regex_pattern, value_normalized):
                return True
        except re.error:
            # Invalid regex, fall through to return False
            pass

        return False

    def _evaluate_conditions(self, conditions: Dict, features: Dict[str, Any]) -> bool:
        """
        Recursively evaluate conditions dictionary.

        Supports:
        - Simple key: value matching (with regex support for string values)
        - Numeric comparisons: {"min": x, "max": y, "exact": z}
        - Boolean logic: OR, AND, NOT
        - Set membership: {"in": [...]}
        - Regex patterns: "1[HS]" matches "1♥" or "1♠"
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

            # Handle list membership (with regex support for each item)
            elif isinstance(expected, list):
                # Check if actual matches any pattern in the list
                matched = False
                for pattern in expected:
                    if isinstance(pattern, str) and isinstance(actual, str):
                        if self._matches_pattern(pattern, actual):
                            matched = True
                            break
                    elif actual == pattern:
                        matched = True
                        break
                if not matched:
                    return False

            # Handle direct equality (with regex support for string patterns)
            else:
                if isinstance(expected, str) and isinstance(actual, str):
                    if not self._matches_pattern(expected, actual):
                        return False
                elif actual != expected:
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

        # Ordinal mappings for quality comparisons
        quality_order = {'poor': 0, 'fair': 1, 'good': 2, 'excellent': 3}

        for op, value in comparison.items():
            # Resolve reference values (e.g., "spades_length" -> features['spades_length'])
            if isinstance(value, str) and value in features:
                value = features[value]

            if op == 'min':
                # Handle quality ordinal comparisons
                if isinstance(value, str) and value in quality_order:
                    actual_ord = quality_order.get(actual, -1)
                    value_ord = quality_order.get(value, 0)
                    if actual_ord < value_ord:
                        return False
                elif actual < value:
                    return False

            elif op == 'max':
                # Handle quality ordinal comparisons
                if isinstance(value, str) and value in quality_order:
                    actual_ord = quality_order.get(actual, 99)
                    value_ord = quality_order.get(value, 0)
                    if actual_ord > value_ord:
                        return False
                elif actual > value:
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
        - "2{lower_suit}" -> "2♣" (my second suit, below barrier)
        - "2{higher_suit}" -> "2♥" (my second suit, reverse)
        - "2{first_suit}" -> "2♦" (rebid my first suit)
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

            # Special case: partner_first_suit
            if var_name == 'partner_first_suit':
                return features.get('partner_first_suit', '')

            # Special case: opponent_suit
            if var_name == 'opponent_suit':
                opening_bid = features.get('opening_bid', '')
                if opening_bid and len(opening_bid) >= 2:
                    return opening_bid[1:]
                return ''

            # Special case: lower_suit - my second suit when it's lower ranked
            if var_name == 'lower_suit':
                if features.get('second_suit_lower'):
                    return features.get('second_suit', '')
                return ''

            # Special case: higher_suit - my second suit when it's higher ranked (reverse)
            if var_name == 'higher_suit':
                if features.get('second_suit_higher'):
                    return features.get('second_suit', '')
                return ''

            # Special case: first_suit - my first bid suit (for rebidding own suit)
            if var_name == 'first_suit':
                return features.get('my_suit', '')

            # Special case: my_suit - same as first_suit
            if var_name == 'my_suit':
                return features.get('my_suit', '')

            # Special case: suit - general suit placeholder
            # For overcalls: use best_suit (best overcallable suit)
            # Otherwise: try second_suit or longest_suit
            if var_name == 'suit':
                if features.get('is_overcall') or features.get('is_competitive_later'):
                    return features.get('best_suit') or features.get('longest_suit', '')
                return features.get('second_suit') or features.get('longest_suit', '')

            # Special case: new_suit or new_lower_suit - for responder's new suit
            if var_name in ['new_suit', 'new_lower_suit']:
                if features.get('second_suit_lower'):
                    return features.get('second_suit', '')
                return features.get('second_suit', '')

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

        for category, schema in self.schemas.items():
            for rule in schema.get('rules', []):
                bid = self._resolve_bid(rule.get('bid', 'Pass'), features)

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
        bid = self._resolve_bid(rule.get('bid', 'Pass'), features)
        priority = rule.get('priority', 0)
        description = rule.get('description', rule.get('explanation', ''))

        # Check trigger first
        trigger = rule.get('trigger')
        trigger_matched = True
        trigger_gap = None
        if trigger:
            trigger_matched = self._matches_trigger(trigger, features)
            if not trigger_matched:
                trigger_gap = f"Auction pattern doesn't match: {trigger}"

        # Analyze conditions
        conditions = rule.get('conditions', {})
        constraints = rule.get('constraints', {})
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
                        if self._matches_pattern(pattern, actual):
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
                    passed = self._matches_pattern(expected, actual)
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
                if actual < value:
                    failures.append(f"min {value} (have {actual}, need +{value - actual})")
                    details['min_shortfall'] = value - actual
                details['min'] = value

            elif op == 'max':
                if actual > value:
                    failures.append(f"max {value} (have {actual}, excess {actual - value})")
                    details['max_excess'] = actual - value
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
