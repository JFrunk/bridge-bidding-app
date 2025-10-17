"""
Bidding Feedback Generator - Phase 1 Implementation

Provides real-time feedback on bidding decisions including:
- Correctness evaluation (optimal, acceptable, suboptimal, error)
- Quality scoring (0-10 scale)
- Impact assessment (none, minor, significant, critical)
- Error categorization
- Actionable hints and explanations

This module does NOT modify bidding state or sequences - it only evaluates
and provides feedback on decisions that have already been made.
"""

import sqlite3
import json
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from engine.hand import Hand
from engine.ai.bid_explanation import BidExplanation
from engine.learning.error_categorizer import get_error_categorizer


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
class BiddingFeedback:
    """
    Structured bidding feedback for API/UI consumption

    This class represents evaluation of a single bidding decision.
    It does NOT modify any game state - it's pure data.
    """

    # Context
    bid_number: int               # Position in auction (1-based)
    position: str                 # "North", "East", "South", "West"
    user_bid: str                 # What user bid (e.g., "2♥")

    # Evaluation
    correctness: CorrectnessLevel
    score: float                  # 0-10 scale

    # Optimal alternative (if not optimal)
    optimal_bid: str
    alternative_bids: List[str]   # Other acceptable bids

    # Explanation
    reasoning: str                # Why this bid? (from BidExplanation)
    explanation_level: str        # "simple", "detailed", "expert"
    rule_reference: Optional[str] # SAYC rule ID

    # Error details (if applicable)
    error_category: Optional[str]     # From ErrorCategorizer
    error_subcategory: Optional[str]  # More specific
    impact: ImpactLevel              # How bad is this mistake?
    helpful_hint: str                # Actionable advice

    # Learning
    key_concept: str              # "HCP counting", "finding fits", etc.
    difficulty: str               # "beginner", "intermediate", "advanced"

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            **asdict(self),
            'correctness': self.correctness.value,
            'impact': self.impact.value
        }

    def to_user_message(self, verbosity: str = "normal") -> str:
        """
        Generate user-friendly message

        Args:
            verbosity: "minimal", "normal", or "detailed"
        """
        if self.correctness == CorrectnessLevel.OPTIMAL:
            msg = f"✓ Excellent! {self.user_bid} is perfect here."
            if verbosity != "minimal":
                msg += f" {self.reasoning}"
            return msg

        elif self.correctness == CorrectnessLevel.ACCEPTABLE:
            msg = f"✓ {self.user_bid} is acceptable. {self.reasoning}"
            if verbosity == "detailed":
                msg += f"\n\nNote: {self.optimal_bid} is slightly more precise."
            return msg

        elif self.correctness == CorrectnessLevel.SUBOPTIMAL:
            msg = f"⚠️ {self.optimal_bid} would be better than {self.user_bid}."
            if verbosity != "minimal":
                msg += f"\n\n{self.helpful_hint}"
            return msg

        else:  # ERROR
            msg = f"❌ {self.user_bid} is not recommended here."
            msg += f"\n\nBetter bid: {self.optimal_bid}"
            if verbosity != "minimal":
                msg += f"\n\n{self.helpful_hint}"
            return msg


class BiddingFeedbackGenerator:
    """
    Generates structured feedback for bidding decisions

    IMPORTANT: This class is READ-ONLY with respect to game state.
    It evaluates decisions but does not modify:
    - Auction history
    - Deal state
    - Session state
    - Bidding sequences

    It only writes to the bidding_decisions table for analytics.
    """

    def __init__(self, db_path: str = 'bridge.db'):
        self.db_path = db_path
        self.error_categorizer = get_error_categorizer()

    def evaluate_bid(self,
                     hand: Hand,
                     user_bid: str,
                     auction_context: Dict,
                     optimal_bid: str,
                     optimal_explanation: BidExplanation) -> BiddingFeedback:
        """
        Evaluate a single bid and generate structured feedback

        Args:
            hand: Hand object
            user_bid: str - What user bid
            auction_context: dict - Current auction state
            optimal_bid: str - AI's recommended bid
            optimal_explanation: BidExplanation object

        Returns:
            BiddingFeedback object

        Note: This method does NOT modify any game state.
        """
        # Determine correctness level
        if user_bid == optimal_bid:
            correctness = CorrectnessLevel.OPTIMAL
            score = 10.0
            error = None

        else:
            # Check if bid is acceptable alternative
            acceptable_bids = self._get_acceptable_alternatives(
                hand, auction_context, optimal_bid
            )

            if user_bid in acceptable_bids:
                correctness = CorrectnessLevel.ACCEPTABLE
                score = 7.5
                error = None

            else:
                # Categorize error
                error = self.error_categorizer.categorize(
                    hand=hand,
                    user_bid=user_bid,
                    correct_bid=optimal_bid,
                    convention_id=auction_context.get('convention_id'),
                    auction_context=auction_context.get('history', [])
                )

                # Determine severity
                if error.category in ['wrong_meaning', 'missed_fit', 'convention_meaning']:
                    correctness = CorrectnessLevel.ERROR
                    score = 2.0
                elif error.category in ['wrong_level', 'strength_evaluation']:
                    correctness = CorrectnessLevel.SUBOPTIMAL
                    score = 5.0
                else:
                    correctness = CorrectnessLevel.SUBOPTIMAL
                    score = 6.0

        # Calculate impact
        impact = self._calculate_impact(user_bid, optimal_bid, error)

        # Generate helpful hint
        if error:
            helpful_hint = error.helpful_hint
        elif correctness == CorrectnessLevel.ACCEPTABLE:
            helpful_hint = f"{optimal_bid} is slightly more standard in SAYC."
        else:
            helpful_hint = ""

        # Build feedback object
        feedback = BiddingFeedback(
            bid_number=len(auction_context.get('history', [])) + 1,
            position=auction_context.get('current_player', 'South'),
            user_bid=user_bid,
            correctness=correctness,
            score=score,
            optimal_bid=optimal_bid,
            alternative_bids=self._get_alternatives(hand, auction_context),
            reasoning=optimal_explanation.primary_reason if optimal_explanation else "",
            explanation_level="detailed",
            rule_reference=optimal_explanation.sayc_rule_id if optimal_explanation else None,
            error_category=error.category if error else None,
            error_subcategory=error.subcategory if error else None,
            impact=impact,
            helpful_hint=helpful_hint,
            key_concept=self._extract_key_concept(optimal_explanation),
            difficulty=self._assess_difficulty(optimal_explanation, auction_context)
        )

        return feedback

    def evaluate_and_store(self,
                          user_id: int,
                          hand: Hand,
                          user_bid: str,
                          auction_context: Dict,
                          optimal_bid: str,
                          optimal_explanation: BidExplanation,
                          session_id: Optional[str] = None,
                          hand_analysis_id: Optional[int] = None) -> BiddingFeedback:
        """
        Evaluate bid AND store in database for dashboard tracking

        Args:
            user_id: User ID
            hand: Hand object
            user_bid: What user bid
            auction_context: Auction context dict
            optimal_bid: AI recommended bid
            optimal_explanation: BidExplanation object
            session_id: Optional session ID
            hand_analysis_id: Optional hand analysis ID (for Phase 3)

        Returns:
            BiddingFeedback object

        Note: This stores feedback in database but does NOT modify game state.
        """
        # Generate feedback
        feedback = self.evaluate_bid(
            hand, user_bid, auction_context,
            optimal_bid, optimal_explanation
        )

        # Store in database
        self._store_feedback(user_id, feedback, auction_context, session_id, hand_analysis_id)

        return feedback

    def _store_feedback(self,
                       user_id: int,
                       feedback: BiddingFeedback,
                       auction_context: Dict,
                       session_id: Optional[str],
                       hand_analysis_id: Optional[int]):
        """Store feedback in bidding_decisions table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO bidding_decisions (
                    hand_analysis_id, user_id, session_id,
                    bid_number, position, dealer, vulnerability,
                    user_bid, optimal_bid, auction_before,
                    correctness, score, impact,
                    error_category, error_subcategory,
                    key_concept, difficulty,
                    helpful_hint, reasoning,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                hand_analysis_id,
                user_id,
                session_id,
                feedback.bid_number,
                feedback.position,
                auction_context.get('dealer'),
                auction_context.get('vulnerability'),
                feedback.user_bid,
                feedback.optimal_bid,
                json.dumps(auction_context.get('history', [])),
                feedback.correctness.value,
                feedback.score,
                feedback.impact.value,
                feedback.error_category,
                feedback.error_subcategory,
                feedback.key_concept,
                feedback.difficulty,
                feedback.helpful_hint,
                feedback.reasoning
            ))

            conn.commit()
        except Exception as e:
            print(f"Error storing bidding feedback: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _calculate_impact(self,
                         user_bid: str,
                         optimal_bid: str,
                         error) -> ImpactLevel:
        """Determine impact of bidding error"""
        if error is None:
            return ImpactLevel.NONE

        # Parse bid levels
        user_level = self._parse_bid_level(user_bid)
        optimal_level = self._parse_bid_level(optimal_bid)

        # Critical errors
        if error.category in ['wrong_meaning', 'missed_fit', 'convention_meaning']:
            return ImpactLevel.CRITICAL

        # Significant errors
        if error.category in ['wrong_level', 'strength_evaluation']:
            # Large level difference is critical
            if user_level and optimal_level and abs(user_level - optimal_level) >= 2:
                return ImpactLevel.CRITICAL
            return ImpactLevel.SIGNIFICANT

        # Wrong strain but same level
        if error.category == 'wrong_strain':
            if user_level == optimal_level:
                return ImpactLevel.SIGNIFICANT
            else:
                return ImpactLevel.CRITICAL

        return ImpactLevel.MINOR

    def _parse_bid_level(self, bid: str) -> Optional[int]:
        """Parse bid level from bid string"""
        if not bid or bid in ['Pass', 'Double', 'Redouble']:
            return None
        try:
            return int(bid[0])
        except (ValueError, IndexError):
            return None

    def _get_acceptable_alternatives(self,
                                    hand: Hand,
                                    auction_context: Dict,
                                    optimal_bid: str) -> List[str]:
        """
        Get list of bids that are acceptable (not perfect, but reasonable)

        Examples:
        - Optimal: 1NT, Acceptable: 1♣ (with 3-3-3-4 15 HCP)
        - Optimal: 4♥, Acceptable: 3♥ (borderline game values)

        For now, returns empty list. Can be enhanced later with
        bidding engine integration.
        """
        # Future enhancement: Use bidding engine to generate alternatives
        return []

    def _get_alternatives(self,
                         hand: Hand,
                         auction_context: Dict) -> List[str]:
        """Get alternative bids worth considering"""
        # Future enhancement
        return []

    def _extract_key_concept(self, explanation: Optional[BidExplanation]) -> str:
        """Extract the key learning concept from explanation"""
        if not explanation:
            return "Bidding judgment"

        # Map convention/rule to concept
        concept_map = {
            'stayman': 'Finding major suit fits',
            'jacoby_transfer': 'Transfers to major suits',
            'blackwood': 'Ace asking for slams',
            'opening_1nt': 'Balanced hand evaluation',
            'takeout_double': 'Competitive bidding',
            'negative_double': 'Showing unbid suits',
            'michaels_cuebid': 'Two-suited overcalls',
            'unusual_2nt': 'Minor suit showing',
            'weak_two': 'Preemptive bidding',
            'strong_2c': 'Strong forcing openings'
        }

        if explanation.convention_reference:
            return concept_map.get(
                explanation.convention_reference,
                explanation.convention_reference.replace('_', ' ').title()
            )

        # Default based on primary reason
        reason_lower = explanation.primary_reason.lower() if explanation.primary_reason else ""

        if 'balanced' in reason_lower:
            return 'Hand shape evaluation'
        elif 'hcp' in reason_lower or 'points' in reason_lower:
            return 'Point counting'
        elif 'support' in reason_lower:
            return 'Trump support'
        elif 'fit' in reason_lower:
            return 'Finding fits'
        elif 'game' in reason_lower:
            return 'Game bidding'
        elif 'slam' in reason_lower:
            return 'Slam bidding'
        else:
            return 'Bidding judgment'

    def _assess_difficulty(self,
                          explanation: Optional[BidExplanation],
                          auction_context: Dict) -> str:
        """Assess difficulty level of this decision"""
        if not explanation:
            return 'intermediate'

        # Count bid number (later in auction = harder)
        bid_count = len(auction_context.get('history', []))

        # Advanced: Multiple rule checks or complex logic
        if hasattr(explanation, 'rule_checks') and len(explanation.rule_checks) > 5:
            return 'advanced'

        # Advanced: Late in auction (rebids, etc.)
        if bid_count > 4:
            return 'advanced'

        # Intermediate: Convention application
        if explanation.convention_reference:
            # Some conventions are easier
            easy_conventions = ['opening_1nt', 'stayman', 'jacoby_transfer']
            if explanation.convention_reference in easy_conventions:
                return 'intermediate'
            return 'advanced'

        # Beginner: Basic opening bids, simple responses
        if bid_count <= 2:
            return 'beginner'

        return 'intermediate'


# Singleton instance
_feedback_generator = None

def get_feedback_generator(db_path: str = 'bridge.db') -> BiddingFeedbackGenerator:
    """Get singleton feedback generator instance"""
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = BiddingFeedbackGenerator(db_path)
    return _feedback_generator
