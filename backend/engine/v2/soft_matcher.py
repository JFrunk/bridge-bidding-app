"""
Soft Matcher for V2 Bidding Engine

Implements fuzzy logic matching between bidding rules and hand features.
Instead of binary match/no-match, calculates a Match Quality Score (0.0-1.0)
that enables "Best-Match-Wins" selection over "First-Match-Wins".

Supports two constraint formats:
1. Legacy: conditions/constraints dicts with implicit penalty logic
2. New: constraints array with explicit constraint_type (HARD/SOFT) and penalty_per_unit

Architecture Reference: docs/architecture/BRIDGE_ARCH_SPEC.md
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of soft matching a rule against hand features."""
    score: float  # 0.0 to 1.0
    penalties: Dict[str, float]  # Breakdown of applied penalties
    hard_fail_reason: Optional[str] = None  # If score is 0.0, why


class SoftMatcher:
    """
    Fuzzy logic engine for matching bidding rules to hand features.

    Instead of binary pass/fail, calculates how well a hand "fits" a rule:
    - 1.0 = Perfect match
    - 0.9 = Minor deviation (1 HCP off)
    - 0.75 = Moderate deviation (2 HCP off)
    - 0.0 = Hard fail (structural violation like wrong shape)

    This enables the bidding engine to select the BEST matching rule
    rather than the first rule that happens to match.

    Constraint Types:
    - HARD: Must pass exactly, otherwise score = 0.0
    - SOFT: Can deviate with penalty = penalty_per_unit * distance
    """

    # Legacy penalty thresholds (used when constraint_type not specified)
    HCP_SOFT_PENALTY_PER_POINT = 0.10  # 10% per HCP difference
    HCP_HARD_FAIL_THRESHOLD = 3  # More than 3 HCP off = hard fail
    SEMI_BALANCED_PENALTY = 0.20  # 20% penalty for semi-balanced when balanced required

    def calculate(self, rule: Dict[str, Any], features: Dict[str, Any]) -> MatchResult:
        """
        Calculate match quality between a rule and hand features.

        Supports two formats:
        1. New format: constraints as list of {feature, min/max/expected, constraint_type, penalty_per_unit}
        2. Legacy format: conditions/constraints as dicts

        Args:
            rule: Rule dictionary from schema
            features: Hand features dictionary from enhanced_extractor

        Returns:
            MatchResult with score (0.0-1.0), penalty breakdown, and fail reason
        """
        # Check for new-format constraints array
        constraints_array = rule.get('constraints')
        if isinstance(constraints_array, list):
            return self._evaluate_new_format(constraints_array, features, rule)

        # Fall back to legacy format
        return self._evaluate_legacy_format(rule, features)

    def _evaluate_new_format(self, constraints: List[Dict], features: Dict[str, Any], rule: Dict) -> MatchResult:
        """
        Evaluate constraints using MULTIPLICATIVE quality scoring.

        Per BRIDGE_ARCH_SPEC.md:
        - Each constraint returns a score (1.0 = pass, 0.0 = HARD fail, or soft penalty)
        - Final quality = PRODUCT of all constraint scores
        - If any HARD constraint fails, total = 0.0

        New format example:
        {
          "constraints": [
            {"feature": "hcp", "min": 15, "max": 17, "constraint_type": "SOFT", "penalty_per_unit": 0.10},
            {"feature": "is_balanced", "expected": true, "constraint_type": "HARD"}
          ]
        }
        """
        quality = 1.0  # Start with perfect match
        constraint_scores = {}

        for constraint in constraints:
            feature_name = constraint.get('feature')
            actual = features.get(feature_name)

            # Evaluate this constraint and get its individual score
            constraint_score, fail_reason = self.evaluate_constraint(constraint, actual)
            constraint_scores[feature_name] = constraint_score

            # HARD fail = immediate 0.0
            if constraint_score == 0.0:
                constraint_type = constraint.get('constraint_type', 'HARD').upper()
                if constraint_type == 'HARD':
                    return MatchResult(
                        score=0.0,
                        penalties={feature_name: 1.0},
                        hard_fail_reason=fail_reason
                    )

            # MULTIPLICATIVE: quality *= constraint_score
            quality *= constraint_score

        # Check trigger pattern if present (always HARD)
        trigger = rule.get('trigger')
        if trigger:
            trigger_result = self._check_trigger(trigger, features)
            if trigger_result[0] == 0.0:
                return MatchResult(
                    score=0.0,
                    penalties={'trigger': 1.0},
                    hard_fail_reason=trigger_result[1]
                )

        # Convert constraint_scores to penalties for debugging (penalty = 1.0 - score)
        penalties = {k: 1.0 - v for k, v in constraint_scores.items() if v < 1.0}

        # Ensure quality stays in valid range
        quality = max(0.0, min(1.0, quality))

        return MatchResult(score=quality, penalties=penalties)

    # Asymmetric penalty multipliers for specific features
    OVERSHOOT_PENALTY_MULTIPLIER = 2.0  # Double penalty for exceeding max (e.g., 18+ HCP for 1NT)

    def evaluate_constraint(self, constraint: Dict, actual: Any) -> Tuple[float, Optional[str]]:
        """
        Evaluate a single constraint and return its score.

        Per spec:
        - HARD: return 1.0 if match, 0.0 if not
        - SOFT: return 1.0 - (distance * penalty_per_unit), clamped to [0, 1]

        HCP Asymmetric Penalty (calibration):
        - Undershoot (below min): Normal penalty (gentle slope - allow upgrades)
        - Overshoot (above max): 2x penalty (steep cliff - force strong opening sequence)

        Rationale: Opening 1NT with 18+ HCP traps the hand in a narrow range.
        We prefer opening 1-Suit and rebidding strong for better accuracy.

        Args:
            constraint: Constraint dict with feature, min/max/expected, constraint_type, penalty_per_unit
            actual: Actual value from features

        Returns:
            Tuple of (score: float 0.0-1.0, fail_reason: Optional[str])
        """
        feature_name = constraint.get('feature')
        constraint_type = constraint.get('constraint_type', 'HARD').upper()
        penalty_per_unit = constraint.get('penalty_per_unit', 0.10)

        # Calculate if constraint passes and distance from target
        passed, distance, fail_reason = self._evaluate_single_constraint(constraint, actual)

        if passed:
            return (1.0, None)

        if constraint_type == 'HARD':
            return (0.0, fail_reason)

        # SOFT: Apply asymmetric penalty for HCP (overshoot penalized more heavily)
        effective_penalty = penalty_per_unit

        if feature_name == 'hcp':
            max_val = constraint.get('max')
            if max_val is not None and actual is not None and actual > max_val:
                # Overshoot: Apply double penalty to discourage strong hands in narrow ranges
                effective_penalty = penalty_per_unit * self.OVERSHOOT_PENALTY_MULTIPLIER

        # SOFT: score = 1.0 - (distance * effective_penalty)
        score = 1.0 - (distance * effective_penalty)
        score = max(0.0, score)  # Clamp to minimum 0.0
        return (score, fail_reason)

    def _evaluate_single_constraint(self, constraint: Dict, actual: Any) -> Tuple[bool, float, Optional[str]]:
        """
        Evaluate a single constraint and return (passed, distance, fail_reason).

        Args:
            constraint: Constraint dict with feature, min/max/expected, etc.
            actual: Actual value from features

        Returns:
            Tuple of (passed: bool, distance: float, fail_reason: Optional[str])
        """
        feature_name = constraint.get('feature')

        # Handle boolean expected value
        if 'expected' in constraint:
            expected = constraint['expected']
            if actual == expected:
                return (True, 0, None)
            else:
                return (False, 1, f"{feature_name}: expected {expected}, got {actual}")

        # Handle min/max range
        min_val = constraint.get('min')
        max_val = constraint.get('max')

        if actual is None:
            return (False, 1, f"{feature_name}: value not set")

        distance = 0
        fail_reason = None

        if min_val is not None and actual < min_val:
            distance = min_val - actual
            fail_reason = f"{feature_name}: {actual} below min {min_val}"
        elif max_val is not None and actual > max_val:
            distance = actual - max_val
            fail_reason = f"{feature_name}: {actual} above max {max_val}"

        passed = (distance == 0)
        return (passed, distance, fail_reason)

    def _evaluate_legacy_format(self, rule: Dict[str, Any], features: Dict[str, Any]) -> MatchResult:
        """
        Evaluate using the legacy conditions/constraints dict format.

        This preserves backward compatibility with existing schema files.
        """
        score = 1.0
        penalties = {}

        conditions = rule.get('conditions', {})
        constraints_dict = rule.get('constraints', {}) if isinstance(rule.get('constraints'), dict) else {}
        all_conditions = {**conditions, **constraints_dict}

        # 1. HCP Check (Soft penalty with hard fail threshold)
        hcp_result = self._check_hcp(all_conditions, features)
        if hcp_result[0] == 0.0:
            return MatchResult(
                score=0.0,
                penalties={'hcp': 1.0},
                hard_fail_reason=hcp_result[1]
            )
        if hcp_result[0] < 1.0:
            penalty = 1.0 - hcp_result[0]
            penalties['hcp'] = penalty
            score -= penalty

        # 2. Shape Check (Hard fail for insufficient suit length)
        shape_result = self._check_shape(all_conditions, features)
        if shape_result[0] == 0.0:
            return MatchResult(
                score=0.0,
                penalties={'shape': 1.0},
                hard_fail_reason=shape_result[1]
            )
        if shape_result[0] < 1.0:
            penalty = 1.0 - shape_result[0]
            penalties['shape'] = penalty
            score -= penalty

        # 3. Balance Check (Soft for semi-balanced, hard for unbalanced)
        balance_result = self._check_balance(all_conditions, features)
        if balance_result[0] == 0.0:
            return MatchResult(
                score=0.0,
                penalties={'balance': 1.0},
                hard_fail_reason=balance_result[1]
            )
        if balance_result[0] < 1.0:
            penalty = 1.0 - balance_result[0]
            penalties['balance'] = penalty
            score -= penalty

        # 4. Boolean conditions (hard fail)
        bool_result = self._check_boolean_conditions(all_conditions, features)
        if bool_result[0] == 0.0:
            return MatchResult(
                score=0.0,
                penalties={'boolean': 1.0},
                hard_fail_reason=bool_result[1]
            )

        # 5. Trigger pattern check (hard fail)
        trigger = rule.get('trigger')
        if trigger:
            trigger_result = self._check_trigger(trigger, features)
            if trigger_result[0] == 0.0:
                return MatchResult(
                    score=0.0,
                    penalties={'trigger': 1.0},
                    hard_fail_reason=trigger_result[1]
                )

        # 6. Other conditions (hard fail) - catches partner_last_bid, etc.
        other_result = self._check_other_conditions(all_conditions, features)
        if other_result[0] == 0.0:
            return MatchResult(
                score=0.0,
                penalties={'other': 1.0},
                hard_fail_reason=other_result[1]
            )

        # Ensure score stays in valid range
        score = max(0.0, min(1.0, score))

        return MatchResult(score=score, penalties=penalties)

    def _check_hcp(self, conditions: Dict, features: Dict) -> Tuple[float, Optional[str]]:
        """
        Check HCP conditions with soft penalties.

        Returns:
            Tuple of (score 0.0-1.0, failure reason if hard fail)
        """
        hcp_condition = conditions.get('hcp')
        if not hcp_condition:
            return (1.0, None)  # No HCP requirement

        actual_hcp = features.get('hcp', 0)

        # Handle different condition formats
        if isinstance(hcp_condition, dict):
            min_hcp = hcp_condition.get('min', 0)
            max_hcp = hcp_condition.get('max', 40)
        elif isinstance(hcp_condition, (int, float)):
            min_hcp = max_hcp = hcp_condition
        else:
            return (1.0, None)

        # Calculate penalty
        penalty = self._calculate_hcp_penalty(min_hcp, max_hcp, actual_hcp)

        if penalty >= 1.0:
            return (0.0, f"HCP {actual_hcp} too far from required {min_hcp}-{max_hcp}")

        return (1.0 - penalty, None)

    def _calculate_hcp_penalty(self, target_min: int, target_max: int, actual: int) -> float:
        """
        Calculate HCP penalty using decay function from spec.

        Penalty schedule:
        - In range: 0.0
        - 1 point off: 0.10 (10%)
        - 2 points off: 0.25 (25%)
        - 3+ points off: 1.0 (hard fail)
        """
        if target_min <= actual <= target_max:
            return 0.0

        # Calculate distance to nearest boundary
        if actual < target_min:
            dist = target_min - actual
        else:
            dist = actual - target_max

        # Decay function per spec
        if dist == 1:
            return 0.10
        if dist == 2:
            return 0.25
        return 1.0  # Hard fail for 3+ points difference

    def _check_shape(self, conditions: Dict, features: Dict) -> Tuple[float, Optional[str]]:
        """
        Check suit length requirements (hard fail for insufficient length).

        Returns:
            Tuple of (score 0.0-1.0, failure reason if hard fail)
        """
        suit_map = {
            'spades_length': 'spades',
            'hearts_length': 'hearts',
            'diamonds_length': 'diamonds',
            'clubs_length': 'clubs'
        }

        for length_key, suit_name in suit_map.items():
            length_condition = conditions.get(length_key)
            if not length_condition:
                continue

            actual_length = features.get(length_key, 0)

            if isinstance(length_condition, dict):
                min_len = length_condition.get('min', 0)
                max_len = length_condition.get('max', 13)

                # Hard fail for insufficient length (structural violation)
                if actual_length < min_len:
                    return (0.0, f"{suit_name}: have {actual_length}, need {min_len}+")

                # Hard fail for too many cards (e.g., Stayman with 5+ major)
                if actual_length > max_len:
                    return (0.0, f"{suit_name}: have {actual_length}, max {max_len}")

            elif isinstance(length_condition, (int, float)):
                if actual_length < length_condition:
                    return (0.0, f"{suit_name}: have {actual_length}, need {length_condition}+")

        return (1.0, None)

    def _check_balance(self, conditions: Dict, features: Dict) -> Tuple[float, Optional[str]]:
        """
        Check balanced hand requirements.

        - Balanced required + balanced hand = 1.0
        - Balanced required + semi-balanced = 0.8 (soft penalty)
        - Balanced required + unbalanced = 0.0 (hard fail)

        Returns:
            Tuple of (score 0.0-1.0, failure reason if hard fail)
        """
        requires_balanced = conditions.get('is_balanced')
        if not requires_balanced:
            return (1.0, None)  # No balance requirement

        is_balanced = features.get('is_balanced', False)
        is_semi_balanced = features.get('is_semi_balanced', False)

        if is_balanced:
            return (1.0, None)

        if is_semi_balanced:
            # Soft penalty for semi-balanced (e.g., 5-3-3-2)
            return (1.0 - self.SEMI_BALANCED_PENALTY, None)

        # Unbalanced hand with balanced requirement = hard fail
        return (0.0, "Unbalanced hand, balanced required")

    def _check_boolean_conditions(self, conditions: Dict, features: Dict) -> Tuple[float, Optional[str]]:
        """
        Check boolean conditions (hard fail only).

        Returns:
            Tuple of (1.0 if all pass, 0.0 with reason if any fail)
        """
        boolean_keys = [
            'is_opening', 'is_response', 'is_contested', 'is_overcall',
            'has_5_card_major', 'is_two_over_one', 'is_game_forced',
            'partner_opened', 'opponent_opened'
        ]

        for key in boolean_keys:
            if key not in conditions:
                continue

            required = conditions[key]
            actual = features.get(key, False)

            if required != actual:
                return (0.0, f"{key}: expected {required}, got {actual}")

        return (1.0, None)

    def _check_trigger(self, trigger: str, features: Dict) -> Tuple[float, Optional[str]]:
        """
        Check auction trigger pattern (hard fail only).

        Trigger patterns like "1NT - ?" must match exactly.

        Returns:
            Tuple of (1.0 if matches, 0.0 with reason if not)
        """
        import re

        auction_history = features.get('_auction_history', features.get('auction_history', []))

        # Parse trigger pattern
        trigger_parts = [p.strip() for p in trigger.split(' - ')]

        if not trigger_parts or trigger_parts[-1] != '?':
            return (0.0, f"Invalid trigger format: {trigger}")

        bid_patterns = trigger_parts[:-1]

        if len(auction_history) != len(bid_patterns):
            return (0.0, f"Auction length mismatch: have {len(auction_history)}, need {len(bid_patterns)}")

        # Match each bid against pattern
        for i, pattern in enumerate(bid_patterns):
            actual_bid = auction_history[i]
            if not self._matches_pattern(pattern, actual_bid):
                return (0.0, f"Auction mismatch at position {i}: {actual_bid} vs {pattern}")

        return (1.0, None)

    def _matches_pattern(self, pattern: str, value: str) -> bool:
        """Check if a bid matches a pattern (with regex support)."""
        import re

        if pattern == value:
            return True

        # Normalize to ASCII for comparison
        def normalize(s: str) -> str:
            return s.replace('♣', 'C').replace('♦', 'D').replace('♥', 'H').replace('♠', 'S').replace('NT', 'N')

        pattern_norm = normalize(pattern)
        value_norm = normalize(value)

        if pattern_norm == value_norm:
            return True

        # Try regex match
        try:
            if re.match(f"^{pattern_norm}$", value_norm):
                return True
        except re.error:
            pass

        return False

    def _check_other_conditions(self, conditions: Dict, features: Dict) -> Tuple[float, Optional[str]]:
        """
        Check all remaining conditions not handled by specialized checks.

        This catches conditions like:
        - partner_last_bid (string with 'in' list)
        - is_responder_rebid, is_opener_rebid (booleans)
        - Any other conditions not explicitly handled

        Returns:
            Tuple of (1.0 if all pass, 0.0 with reason if any fail)
        """
        # Keys already handled by specialized checks
        handled_keys = {
            'hcp', 'is_balanced',
            'spades_length', 'hearts_length', 'diamonds_length', 'clubs_length',
            'is_opening', 'is_response', 'is_contested', 'is_overcall',
            'has_5_card_major', 'is_two_over_one', 'is_game_forced',
            'partner_opened', 'opponent_opened',
            'OR', 'AND', 'NOT',  # Boolean operators handled elsewhere
            'stoppers_required', 'stoppers_in'  # Stopper conditions
        }

        for key, expected in conditions.items():
            if key in handled_keys:
                continue

            actual = features.get(key)

            # Handle dict conditions (e.g., partner_last_bid: {in: [...]} )
            if isinstance(expected, dict):
                if 'in' in expected:
                    # Check if actual is in the allowed list
                    allowed = expected['in']
                    matched = False
                    if actual is not None:
                        for pattern in allowed:
                            if self._matches_pattern(str(pattern), str(actual)):
                                matched = True
                                break
                    if not matched:
                        return (0.0, f"{key}: '{actual}' not in allowed list")
                elif 'not_in' in expected:
                    # Check if actual is NOT in the forbidden list
                    forbidden = expected['not_in']
                    if actual is not None:
                        for pattern in forbidden:
                            if self._matches_pattern(str(pattern), str(actual)):
                                return (0.0, f"{key}: '{actual}' in forbidden list")
                elif 'exact' in expected:
                    # Check for exact value match (HARD constraint)
                    exact_val = expected['exact']
                    if actual is None:
                        return (0.0, f"{key}: value not set, expected exactly {exact_val}")
                    try:
                        if actual != exact_val:
                            return (0.0, f"{key}: expected exactly {exact_val}, got {actual}")
                    except TypeError:
                        pass  # Can't compare, skip
                elif 'min' in expected or 'max' in expected:
                    # Numeric comparison
                    if actual is None:
                        return (0.0, f"{key}: value not set, expected range")
                    min_val = expected.get('min', float('-inf'))
                    max_val = expected.get('max', float('inf'))
                    try:
                        if actual < min_val or actual > max_val:
                            return (0.0, f"{key}: {actual} not in range [{min_val}, {max_val}]")
                    except TypeError:
                        pass  # Can't compare, skip

            # Handle boolean conditions
            elif isinstance(expected, bool):
                if actual != expected:
                    return (0.0, f"{key}: expected {expected}, got {actual}")

            # Handle string equality
            elif isinstance(expected, str):
                if not self._matches_pattern(expected, str(actual) if actual else ''):
                    return (0.0, f"{key}: expected '{expected}', got '{actual}'")

            # Handle list (in-list check)
            elif isinstance(expected, list):
                matched = False
                if actual is not None:
                    for pattern in expected:
                        if self._matches_pattern(str(pattern), str(actual)):
                            matched = True
                            break
                if not matched:
                    return (0.0, f"{key}: '{actual}' not in {expected}")

        return (1.0, None)

    def get_match_quality(self, rule: Dict[str, Any], features: Dict[str, Any]) -> float:
        """
        Convenience method returning just the score.

        Args:
            rule: Rule dictionary from schema
            features: Hand features dictionary

        Returns:
            Match quality score (0.0-1.0)
        """
        result = self.calculate(rule, features)
        return result.score

    def calculate_match_quality(self, rule: Dict[str, Any], hand_features: Dict[str, Any]) -> float:
        """
        Calculate match quality between a rule and hand features.

        Per BRIDGE_ARCH_SPEC.md:
        - Returns the PRODUCT (multiplication) of all constraint scores
        - If any HARD constraint is 0.0, the total must be 0.0
        - SOFT constraints return 1.0 - (distance * penalty_per_unit)

        Args:
            rule: Rule dictionary from schema
            hand_features: Hand features dictionary

        Returns:
            Match quality score (0.0-1.0)
        """
        return self.get_match_quality(rule, hand_features)
