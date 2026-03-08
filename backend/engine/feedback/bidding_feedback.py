"""
Bidding Feedback — Data Models and Database Storage

Provides:
- BiddingFeedback dataclass (structured feedback for API/UI)
- CorrectnessLevel / ImpactLevel enums
- BiddingFeedbackGenerator (database storage for analytics)

Bid evaluation logic lives in V2BidEvaluator (engine/v2/feedback/bid_evaluator.py).
This module handles the storage layer and shared data types.
"""

import json
import sys
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict

# Database abstraction layer (PostgreSQL in production)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection


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

    # Structured learning feedback (Phase: Learning Enhancement)
    learning_feedback: Optional[Dict] = None  # LearningFeedback.to_dict()

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
            msg = f"✓ Excellent! {self.user_bid} is appropriate here."
            if verbosity != "minimal":
                msg += f" {self.reasoning}"
            return msg

        elif self.correctness == CorrectnessLevel.ACCEPTABLE:
            msg = f"✓ {self.user_bid} is acceptable."
            if self.reasoning:
                msg += f" {self.reasoning}"
            # Always show the optimal alternative for learning purposes
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


class BiddingFeedbackGenerator:
    """
    Database storage layer for bidding feedback.

    Bid evaluation is handled by V2BidEvaluator (engine/v2/feedback/bid_evaluator.py).
    This class stores the evaluated feedback in the bidding_decisions table for analytics.
    """

    def _store_feedback(self,
                       user_id: int,
                       feedback: BiddingFeedback,
                       auction_context: Dict,
                       session_id: Optional[str],
                       hand_analysis_id: Optional[int],
                       hand_number: Optional[int] = None,
                       deal_data: Optional[Dict] = None):
        """Store feedback in bidding_decisions table"""
        # Always use get_connection() for consistency with analytics queries.
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO bidding_decisions (
                    hand_analysis_id, user_id, session_id, hand_number,
                    bid_number, position, dealer, vulnerability,
                    user_bid, optimal_bid, auction_before,
                    correctness, score, impact,
                    error_category, error_subcategory,
                    key_concept, difficulty,
                    helpful_hint, reasoning,
                    deal_data,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                hand_analysis_id,
                user_id,
                session_id,
                hand_number,
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
                feedback.reasoning,
                json.dumps(deal_data) if deal_data else None
            ))

            conn.commit()
            print(f"✅ Stored bidding decision: {feedback.user_bid} (correctness: {feedback.correctness.value}, score: {feedback.score})")
        except Exception as e:
            print(f"❌ Error storing bidding feedback: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            raise  # Re-raise so the API endpoint can catch it
        finally:
            conn.close()



# Singleton instance
_feedback_generator = None

def get_feedback_generator() -> BiddingFeedbackGenerator:
    """Get singleton feedback generator instance"""
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = BiddingFeedbackGenerator()
    return _feedback_generator
