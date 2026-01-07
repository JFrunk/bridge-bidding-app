"""
V2 Schema-Based Bid Evaluator

Evaluates user bids using the V2 schema engine, providing unified explanation
logic for both AI bids and user feedback. This replaces the V1 heuristic-based
alternative generation with schema-driven candidate analysis.

Key advantages over V1:
1. Alternatives come from actual schema rules (not heuristics)
2. Same rules explain AI bids and evaluate user bids
3. Single source of truth for bidding logic
4. Transparent - can show exactly which rules matched
"""

from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from engine.hand import Hand
from engine.v2.interpreters.schema_interpreter import BidCandidate
from engine.learning.error_categorizer import get_error_categorizer, CategorizedError


class CorrectnessLevel(Enum):
    """Classification of bid correctness"""
    OPTIMAL = "optimal"           # Perfect bid
    ACCEPTABLE = "acceptable"     # Reasonable alternative
    SUBOPTIMAL = "suboptimal"     # Works but not best
    ERROR = "error"               # Incorrect


class ImpactLevel(Enum):
    """Assessment of mistake impact"""
    NONE = "none"                 # Style difference
    MINOR = "minor"               # Small inefficiency
    SIGNIFICANT = "significant"   # Could affect level/strain
    CRITICAL = "critical"         # Likely wrong contract


@dataclass
class V2BiddingFeedback:
    """
    Structured bidding feedback from V2 schema evaluation.

    Compatible with V1 BiddingFeedback but includes V2-specific data
    like matched rule IDs and candidate analysis.
    """
    # Context
    bid_number: int
    position: str
    user_bid: str

    # Evaluation
    correctness: CorrectnessLevel
    score: float  # 0-10 scale

    # Optimal and alternatives
    optimal_bid: str
    optimal_explanation: str
    optimal_rule_id: Optional[str]
    alternative_bids: List[str]

    # V2-specific: all candidates that matched
    matched_candidates: List[Dict]  # Simplified candidate info

    # Error details
    error_category: Optional[str]
    error_subcategory: Optional[str]
    impact: ImpactLevel
    helpful_hint: str

    # Learning
    key_concept: str
    difficulty: str
    forcing_status: str

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            'bid_number': self.bid_number,
            'position': self.position,
            'user_bid': self.user_bid,
            'correctness': self.correctness.value,
            'score': self.score,
            'optimal_bid': self.optimal_bid,
            'optimal_explanation': self.optimal_explanation,
            'optimal_rule_id': self.optimal_rule_id,
            'alternative_bids': self.alternative_bids,
            'matched_candidates': self.matched_candidates,
            'error_category': self.error_category,
            'error_subcategory': self.error_subcategory,
            'impact': self.impact.value,
            'helpful_hint': self.helpful_hint,
            'key_concept': self.key_concept,
            'difficulty': self.difficulty,
            'forcing_status': self.forcing_status
        }

    def to_user_message(self, verbosity: str = "normal") -> str:
        """Generate user-friendly message"""
        if self.correctness == CorrectnessLevel.OPTIMAL:
            msg = f"✓ Excellent! {self.user_bid} is appropriate here."
            if verbosity != "minimal":
                msg += f" {self.optimal_explanation}"
            return msg

        elif self.correctness == CorrectnessLevel.ACCEPTABLE:
            msg = f"✓ {self.user_bid} is acceptable."
            if self.optimal_explanation:
                msg += f" {self.optimal_explanation}"
            if self.optimal_bid and self.optimal_bid != self.user_bid:
                if verbosity == "minimal":
                    msg += f" (Optimal: {self.optimal_bid})"
                else:
                    msg += f"\n\nNote: {self.optimal_bid} is slightly more precise"
                    if self.helpful_hint:
                        msg += f" — {self.helpful_hint}"
                    else:
                        msg += "."
            return msg

        elif self.correctness == CorrectnessLevel.SUBOPTIMAL:
            msg = f"✗ {self.optimal_bid} would be better than {self.user_bid}."
            if verbosity != "minimal":
                msg += f"\n\n{self.helpful_hint}"
            return msg

        else:  # ERROR
            msg = f"✗ {self.user_bid} is not recommended here."
            msg += f"\n\nBetter bid: {self.optimal_bid}"
            if verbosity != "minimal":
                msg += f"\n\n{self.helpful_hint}"
            return msg


class V2BidEvaluator:
    """
    Evaluates user bids using V2 schema engine.

    This class provides the same evaluation capabilities as V1's
    BiddingFeedbackGenerator but uses V2's schema-driven approach
    for determining alternatives and correctness.

    Key difference from V1:
    - V1 uses heuristic rules to guess acceptable alternatives
    - V2 uses get_bid_candidates() to get ALL matching schema rules
    - Alternatives are bids that actually matched rules (transparent)
    """

    # Priority thresholds for determining acceptability
    OPTIMAL_THRESHOLD = 0.95  # Within 5% of top priority = optimal
    ACCEPTABLE_THRESHOLD = 0.70  # Within 30% of top priority = acceptable
    SUBOPTIMAL_THRESHOLD = 0.40  # Below 40% = error

    # Minimum priority for a candidate to be considered acceptable
    MIN_ACCEPTABLE_PRIORITY = 400

    def __init__(self, engine: 'BiddingEngineV2Schema'):
        """
        Initialize evaluator with a V2 schema engine.

        Args:
            engine: BiddingEngineV2Schema instance to use for evaluation
        """
        self.engine = engine
        self.error_categorizer = get_error_categorizer()

    def evaluate_bid(
        self,
        hand: Hand,
        user_bid: str,
        auction_history: List[str],
        my_position: str,
        vulnerability: str = 'None',
        dealer: str = 'North'
    ) -> V2BiddingFeedback:
        """
        Evaluate a user's bid against V2 schema rules.

        This method:
        1. Gets the optimal bid and all matching candidates from V2
        2. Checks if user's bid is among the candidates
        3. Determines correctness based on candidate priority
        4. Generates helpful feedback using the schema explanations

        Args:
            hand: User's Hand object
            user_bid: The bid the user made
            auction_history: List of previous bids
            my_position: User's position (North/East/South/West)
            vulnerability: Vulnerability string
            dealer: Dealer position

        Returns:
            V2BiddingFeedback object with evaluation results
        """
        # Get optimal bid and all candidates from V2 engine
        optimal_bid, optimal_explanation = self.engine.get_next_bid(
            hand, auction_history, my_position, vulnerability, 'detailed', dealer
        )

        candidates = self.engine.get_bid_candidates(
            hand, auction_history, my_position, vulnerability, dealer
        )

        # Get forcing state for context
        forcing_state = self.engine.get_forcing_state()
        forcing_status = forcing_state.get('forcing_level', 'NON_FORCING')

        # Determine correctness and score
        correctness, score = self._determine_correctness(
            user_bid, optimal_bid, candidates
        )

        # Get acceptable alternatives (top candidates excluding optimal)
        alternatives = self._get_acceptable_alternatives(
            candidates, optimal_bid, user_bid
        )

        # Find the rule that matched the user's bid (if any)
        user_candidate = self._find_user_candidate(user_bid, candidates)

        # Categorize error if not optimal/acceptable
        error = None
        if correctness in [CorrectnessLevel.SUBOPTIMAL, CorrectnessLevel.ERROR]:
            auction_context = {
                'history': auction_history,
                'vulnerability': vulnerability,
                'dealer': dealer,
                'current_player': my_position
            }
            error = self.error_categorizer.categorize(
                hand=hand,
                user_bid=user_bid,
                correct_bid=optimal_bid,
                convention_id=self._extract_convention_id(candidates),
                auction_context=auction_context
            )

        # Calculate impact
        impact = self._calculate_impact(user_bid, optimal_bid, error)

        # Generate helpful hint
        if error:
            helpful_hint = error.helpful_hint
        elif correctness == CorrectnessLevel.ACCEPTABLE:
            helpful_hint = self._generate_acceptable_hint(
                user_bid, optimal_bid, user_candidate, candidates
            )
        else:
            helpful_hint = ""

        # Extract learning concepts
        key_concept = self._extract_key_concept(candidates, optimal_bid)
        difficulty = self._assess_difficulty(auction_history, candidates)

        # Find optimal candidate for rule ID
        optimal_candidate = next(
            (c for c in candidates if c.bid == optimal_bid), None
        )

        # Build simplified candidate info for transparency
        matched_candidates = [
            {
                'bid': c.bid,
                'rule_id': c.rule_id,
                'priority': c.priority,
                'explanation': c.explanation
            }
            for c in candidates[:5]  # Top 5 for display
        ]

        return V2BiddingFeedback(
            bid_number=len(auction_history) + 1,
            position=my_position,
            user_bid=user_bid,
            correctness=correctness,
            score=score,
            optimal_bid=optimal_bid,
            optimal_explanation=optimal_explanation,
            optimal_rule_id=optimal_candidate.rule_id if optimal_candidate else None,
            alternative_bids=alternatives,
            matched_candidates=matched_candidates,
            error_category=error.category if error else None,
            error_subcategory=error.subcategory if error else None,
            impact=impact,
            helpful_hint=helpful_hint,
            key_concept=key_concept,
            difficulty=difficulty,
            forcing_status=forcing_status
        )

    def _determine_correctness(
        self,
        user_bid: str,
        optimal_bid: str,
        candidates: List[BidCandidate]
    ) -> Tuple[CorrectnessLevel, float]:
        """
        Determine correctness level and score based on candidate priorities.

        The key insight: if user's bid appears in candidates with decent
        priority, it's a valid alternative even if not optimal.

        Returns:
            (CorrectnessLevel, score)
        """
        # Exact match with optimal = OPTIMAL
        if user_bid == optimal_bid:
            return (CorrectnessLevel.OPTIMAL, 10.0)

        # No candidates = can't evaluate properly, default to error
        if not candidates:
            return (CorrectnessLevel.ERROR, 2.0)

        # Find user's bid in candidates
        user_candidate = self._find_user_candidate(user_bid, candidates)

        if user_candidate is None:
            # User's bid didn't match any rule = ERROR
            return (CorrectnessLevel.ERROR, 2.0)

        # User's bid matched a rule - determine acceptability by priority
        top_priority = candidates[0].priority
        user_priority = user_candidate.priority

        # Calculate relative priority
        if top_priority > 0:
            relative_priority = user_priority / top_priority
        else:
            relative_priority = 0

        # Also check absolute priority threshold
        if user_priority < self.MIN_ACCEPTABLE_PRIORITY:
            # Low absolute priority = suboptimal even if relatively close
            return (CorrectnessLevel.SUBOPTIMAL, 5.0)

        # Score based on relative priority
        if relative_priority >= self.OPTIMAL_THRESHOLD:
            # Very close to optimal - treat as optimal
            return (CorrectnessLevel.OPTIMAL, 9.5)
        elif relative_priority >= self.ACCEPTABLE_THRESHOLD:
            # Reasonable alternative
            score = 7.0 + (relative_priority - self.ACCEPTABLE_THRESHOLD) * 10
            return (CorrectnessLevel.ACCEPTABLE, min(score, 8.5))
        elif relative_priority >= self.SUBOPTIMAL_THRESHOLD:
            # Suboptimal but not error
            score = 4.0 + (relative_priority - self.SUBOPTIMAL_THRESHOLD) * 10
            return (CorrectnessLevel.SUBOPTIMAL, min(score, 6.5))
        else:
            # Low priority = error
            return (CorrectnessLevel.ERROR, 2.0 + relative_priority * 4)

    def _find_user_candidate(
        self,
        user_bid: str,
        candidates: List[BidCandidate]
    ) -> Optional[BidCandidate]:
        """Find the candidate matching the user's bid."""
        for candidate in candidates:
            if candidate.bid == user_bid:
                return candidate
        return None

    def _get_acceptable_alternatives(
        self,
        candidates: List[BidCandidate],
        optimal_bid: str,
        user_bid: str
    ) -> List[str]:
        """
        Get list of acceptable alternative bids from candidates.

        These are bids that matched schema rules with decent priority,
        excluding the optimal bid and user's bid.
        """
        alternatives = []

        if not candidates:
            return alternatives

        top_priority = candidates[0].priority
        threshold = top_priority * self.ACCEPTABLE_THRESHOLD

        for candidate in candidates:
            bid = candidate.bid

            # Skip optimal and user's bid
            if bid == optimal_bid or bid == user_bid:
                continue

            # Include if above threshold
            if candidate.priority >= threshold and candidate.priority >= self.MIN_ACCEPTABLE_PRIORITY:
                alternatives.append(bid)

            # Limit to top 3 alternatives
            if len(alternatives) >= 3:
                break

        return alternatives

    def _extract_convention_id(self, candidates: List[BidCandidate]) -> Optional[str]:
        """Extract convention ID from the winning candidate's rule."""
        if not candidates:
            return None

        rule_id = candidates[0].rule_id

        # Parse convention from rule_id (e.g., "stayman_4card_major" -> "stayman")
        convention_keywords = [
            'stayman', 'jacoby', 'blackwood', 'gerber',
            'michaels', 'unusual', 'negative_double', 'takeout',
            'preempt', 'weak_two', 'strong_2c', 'transfer'
        ]

        rule_lower = rule_id.lower()
        for keyword in convention_keywords:
            if keyword in rule_lower:
                return keyword

        return None

    def _calculate_impact(
        self,
        user_bid: str,
        optimal_bid: str,
        error: Optional[CategorizedError]
    ) -> ImpactLevel:
        """Determine impact of bidding error."""
        if error is None:
            return ImpactLevel.NONE

        # Parse bid levels
        user_level = self._parse_bid_level(user_bid)
        optimal_level = self._parse_bid_level(optimal_bid)

        # Critical errors
        if error.category in ['wrong_meaning', 'missed_fit', 'convention_meaning']:
            return ImpactLevel.CRITICAL

        # Slam-related errors are significant to critical
        if error.category == 'slam_bidding':
            if error.subcategory in ['overbid_slam', 'missed_slam']:
                return ImpactLevel.CRITICAL
            return ImpactLevel.SIGNIFICANT

        # Significant errors
        if error.category in ['wrong_level', 'strength_evaluation']:
            if user_level and optimal_level and abs(user_level - optimal_level) >= 2:
                return ImpactLevel.CRITICAL
            return ImpactLevel.SIGNIFICANT

        # Wrong strain
        if error.category == 'wrong_strain':
            if user_level == optimal_level:
                return ImpactLevel.SIGNIFICANT
            return ImpactLevel.CRITICAL

        return ImpactLevel.MINOR

    def _parse_bid_level(self, bid: str) -> Optional[int]:
        """Parse bid level from bid string."""
        if not bid or bid in ['Pass', 'X', 'XX']:
            return None
        try:
            return int(bid[0])
        except (ValueError, IndexError):
            return None

    def _generate_acceptable_hint(
        self,
        user_bid: str,
        optimal_bid: str,
        user_candidate: Optional[BidCandidate],
        candidates: List[BidCandidate]
    ) -> str:
        """
        Generate hint explaining why optimal is preferred over user's acceptable bid.

        Uses the schema explanations directly for transparency.
        """
        if not candidates:
            return f"{optimal_bid} is more standard in SAYC."

        optimal_candidate = next(
            (c for c in candidates if c.bid == optimal_bid), None
        )

        # Use the optimal bid's explanation
        if optimal_candidate and optimal_candidate.explanation:
            return f"{optimal_bid}: {optimal_candidate.explanation}"

        # Compare user's bid explanation if available
        if user_candidate and user_candidate.explanation:
            return (
                f"Your bid ({user_bid}) is valid, but {optimal_bid} is more "
                f"precise. {user_candidate.explanation}"
            )

        return f"{optimal_bid} is slightly more standard in SAYC."

    def _extract_key_concept(
        self,
        candidates: List[BidCandidate],
        optimal_bid: str
    ) -> str:
        """Extract the key learning concept from the evaluation."""
        if not candidates:
            return "Bidding judgment"

        # Find optimal candidate
        optimal_candidate = next(
            (c for c in candidates if c.bid == optimal_bid), None
        )

        if not optimal_candidate:
            return "Bidding judgment"

        rule_id = optimal_candidate.rule_id.lower()
        explanation = optimal_candidate.explanation.lower() if optimal_candidate.explanation else ""

        # Map rule patterns to concepts
        concept_patterns = {
            'stayman': 'Finding major suit fits',
            'jacoby': 'Transfers to major suits',
            'transfer': 'Transfers to major suits',
            'blackwood': 'Ace asking for slams',
            'gerber': 'Ace asking over NT',
            'opening_1nt': 'Balanced hand evaluation',
            'open_1nt': 'Balanced hand evaluation',
            'takeout': 'Competitive bidding',
            'negative_double': 'Showing unbid suits',
            'michaels': 'Two-suited overcalls',
            'unusual': 'Minor suit showing',
            'preempt': 'Preemptive bidding',
            'weak': 'Preemptive bidding',
            'strong_2c': 'Strong forcing openings',
            'slam': 'Slam bidding',
            'splinter': 'Slam try with shortage',
            'cuebid': 'Control showing',
        }

        for pattern, concept in concept_patterns.items():
            if pattern in rule_id or pattern in explanation:
                return concept

        # Check explanation for clues
        if 'balanced' in explanation:
            return 'Hand shape evaluation'
        elif 'hcp' in explanation or 'points' in explanation:
            return 'Point counting'
        elif 'support' in explanation:
            return 'Trump support'
        elif 'fit' in explanation:
            return 'Finding fits'
        elif 'game' in explanation:
            return 'Game bidding'
        elif 'slam' in explanation:
            return 'Slam bidding'

        return 'Bidding judgment'

    def _assess_difficulty(
        self,
        auction_history: List[str],
        candidates: List[BidCandidate]
    ) -> str:
        """Assess difficulty level of this decision."""
        bid_count = len(auction_history)

        # Late in auction = harder
        if bid_count > 6:
            return 'advanced'

        if not candidates:
            return 'intermediate'

        top_candidate = candidates[0]
        rule_id = top_candidate.rule_id.lower()

        # Easy conventions
        easy_patterns = ['open_1', 'opening_1', 'pass', 'raise']
        if any(p in rule_id for p in easy_patterns) and bid_count <= 2:
            return 'beginner'

        # Advanced conventions
        advanced_patterns = [
            'splinter', 'cuebid', 'fourth_suit', 'negative_double',
            'michaels', 'unusual', 'slam', 'grand'
        ]
        if any(p in rule_id for p in advanced_patterns):
            return 'advanced'

        # Intermediate by default
        return 'intermediate'


# Factory function for easy instantiation
def create_v2_evaluator(engine: 'BiddingEngineV2Schema') -> V2BidEvaluator:
    """Create a V2BidEvaluator with the given engine."""
    return V2BidEvaluator(engine)
