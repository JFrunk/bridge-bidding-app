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

import json
import sys
import sqlite3
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple
from datetime import datetime

# Database abstraction layer for SQLite/PostgreSQL compatibility
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection

from engine.hand import Hand
from engine.ai.bid_explanation import BidExplanation
from engine.learning.error_categorizer import get_error_categorizer

# Import bidding modules for generating acceptable alternatives
from engine.overcalls import OvercallModule
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention
from engine.ai.conventions.michaels_cuebid import MichaelsCuebidConvention
from engine.ai.conventions.unusual_2nt import Unusual2NTConvention
from engine.ai.conventions.negative_doubles import NegativeDoubleConvention
from engine.opening_bids import OpeningBidsModule
from engine.ai.conventions.preempts import PreemptConvention
from engine.responses import ResponseModule
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.blackwood import BlackwoodConvention


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
    Generates structured feedback for bidding decisions

    IMPORTANT: This class is READ-ONLY with respect to game state.
    It evaluates decisions but does not modify:
    - Auction history
    - Deal state
    - Session state
    - Bidding sequences

    It only writes to the bidding_decisions table for analytics.
    """

    def __init__(self, db_path: str = 'backend/bridge.db'):
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
                    auction_context=auction_context  # Pass full context dict, not just history
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
            helpful_hint = self._generate_acceptable_hint(user_bid, optimal_bid, hand, auction_context)
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
                          hand_analysis_id: Optional[int] = None,
                          hand_number: Optional[int] = None) -> BiddingFeedback:
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
            hand_number: Optional hand number within session (1-indexed)

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
        self._store_feedback(user_id, feedback, auction_context, session_id, hand_analysis_id, hand_number)

        return feedback

    def _store_feedback(self,
                       user_id: int,
                       feedback: BiddingFeedback,
                       auction_context: Dict,
                       session_id: Optional[str],
                       hand_analysis_id: Optional[int],
                       hand_number: Optional[int] = None):
        """Store feedback in bidding_decisions table"""
        # Use custom db_path if provided (for testing), otherwise use global connection
        if self.db_path and self.db_path != 'backend/bridge.db':
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
        else:
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
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
                feedback.reasoning
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

        This method runs multiple bidding modules to find valid alternative bids.
        A bid is acceptable if:
        1. A recognized bidding module would recommend it
        2. It's legal given the auction
        3. It's reasonably close in meaning/strength to the optimal bid

        Examples:
        - Optimal: 1NT overcall, Acceptable: X (takeout double) - both show ~15+ HCP
        - Optimal: 4♥, Acceptable: 3♥ (borderline game values)
        - Optimal: 1♠, Acceptable: 1♥ (both show 5-card major opening)
        """
        alternatives = []

        # Build features dict for module evaluation
        features = self._build_features_for_alternatives(hand, auction_context)
        if not features:
            return []

        # Get relevant modules based on auction state
        modules_to_check = self._get_relevant_modules(auction_context, features)

        # Run each module and collect valid alternative bids
        for module in modules_to_check:
            try:
                result = module.evaluate(hand, features)
                if result:
                    bid = result[0]
                    # Skip if same as optimal or already in alternatives
                    if bid == optimal_bid or bid in alternatives:
                        continue
                    # Check if it's a reasonable alternative
                    if self._is_reasonable_alternative(bid, optimal_bid, hand, auction_context):
                        alternatives.append(bid)
            except Exception as e:
                # Don't fail feedback generation if a module errors
                print(f"Warning: Module {type(module).__name__} failed: {e}")
                continue

        return alternatives

    def _build_features_for_alternatives(self, hand: Hand, auction_context: Dict) -> Optional[Dict]:
        """Build the features dict needed for module evaluation"""
        try:
            from engine.ai.feature_extractor import extract_features

            history = auction_context.get('history', [])
            current_player = auction_context.get('current_player', 'South')
            vulnerability = auction_context.get('vulnerability', 'None')
            dealer = auction_context.get('dealer', 'North')

            return extract_features(hand, history, current_player, vulnerability, dealer)
        except Exception as e:
            print(f"Warning: Could not build features for alternatives: {e}")
            return None

    def _get_relevant_modules(self, auction_context: Dict, features: Dict) -> List:
        """
        Determine which bidding modules are relevant for this auction state.

        We check modules that might produce valid alternative bids based on:
        - Opening vs competitive situation
        - Partnership vs opponent auction
        - What conventions might apply
        """
        modules = []
        auction = features.get('auction_features', {})

        # Competitive situation (opponent opened)
        if auction.get('opener_relationship') == 'Opponent':
            # All competitive bidding options
            modules.extend([
                OvercallModule(),
                TakeoutDoubleConvention(),
                MichaelsCuebidConvention(),
                Unusual2NTConvention(),
            ])

        # Partner opened - response options
        elif auction.get('opener_relationship') == 'Partner':
            modules.append(ResponseModule())
            # Check for conventions over NT
            opening_bid = auction.get('opening_bid', '')
            if opening_bid in ['1NT', '2NT']:
                modules.extend([
                    StaymanConvention(),
                    JacobyConvention(),
                ])
            # Slam conventions
            modules.append(BlackwoodConvention())
            # Negative doubles if opponent interfered
            modules.append(NegativeDoubleConvention())

        # Opening situation
        elif not auction.get('opener'):
            modules.extend([
                OpeningBidsModule(),
                PreemptConvention(),
            ])

        return modules

    def _is_reasonable_alternative(self, bid: str, optimal_bid: str,
                                   hand: Hand, auction_context: Dict) -> bool:
        """
        Check if a bid is a reasonable alternative to the optimal bid.

        Criteria:
        1. Same general category (competitive action, game try, slam try, etc.)
        2. Not wildly different in level (within 1 level usually)
        3. Both legal
        4. Makes bridge sense (e.g., 1NT and X are both valid over opponent's 1♦)
        """
        # Parse bid information for use throughout
        bid_suit = self._extract_suit(bid)
        optimal_suit = self._extract_suit(optimal_bid)
        bid_level = self._parse_bid_level(bid)
        optimal_level = self._parse_bid_level(optimal_bid)

        # Special case: Pass is only acceptable if optimal is also conservative
        if bid == 'Pass':
            # Pass is acceptable alternative to weak bids or when borderline
            if optimal_level and optimal_level >= 3:
                return False  # Don't accept Pass as alternative to game+ bids
            # Pass could be acceptable for borderline hands
            if hand.hcp < 12:
                return True
            return False

        # SLAM BIDDING ALTERNATIVES
        # Handle game vs slam decisions - these are often judgment calls
        if optimal_level and optimal_level >= 6:
            # Optimal is slam - check if user's bid is acceptable alternative

            # Game bid in same suit is acceptable (conservative slam decision)
            if bid_level and bid_level in [4, 5] and bid_suit == optimal_suit:
                # With 30-32 HCP, game is a reasonable alternative to slam
                if hand.hcp < 18:  # Not a powerhouse hand
                    return True

            # Blackwood (4NT) is acceptable alternative to direct slam bid
            # User might want to check aces before committing
            if bid == '4NT':
                return True

            # Different slam level is acceptable (6 vs 7, or small vs grand)
            if bid_level and bid_level >= 6:
                return True

        # If optimal is Blackwood (4NT), direct game or slam in a suit is acceptable
        if optimal_bid == '4NT':
            # Direct game or slam in a major is acceptable
            if bid_level and bid_level >= 4 and bid_suit in ['♥', '♠', 'NT']:
                return True

        # Game vs slam try decisions
        if optimal_level and optimal_level in [4, 5]:
            # If optimal is game and user bids slam, check if reasonable
            if bid_level and bid_level == 6 and bid_suit == optimal_suit:
                # Slam try is acceptable if hand has slam-ish values
                if hand.hcp >= 15:
                    return True

        # Double (X) and NT overcalls are reasonable alternatives to each other
        # when both show similar strength in competitive situations
        competitive_equivalents = {
            ('X', '1NT'), ('1NT', 'X'),
            ('X', '2NT'), ('2NT', 'X'),
        }
        if (bid, optimal_bid) in competitive_equivalents or (optimal_bid, bid) in competitive_equivalents:
            return True

        # Same suit at different levels (game try vs invitation)
        if bid_suit and optimal_suit and bid_suit == optimal_suit:
            # Same suit, within 1 level = acceptable
            if bid_level and optimal_level and abs(bid_level - optimal_level) <= 1:
                return True

        # Different suits at same level in opening/response situations
        # (e.g., 1♥ vs 1♠ as opening bids)
        if bid_level and optimal_level and bid_level == optimal_level == 1:
            if bid_suit and optimal_suit:
                # Both are 1-level suit bids - reasonable alternatives
                return True

        # NT vs suit at same/similar level
        if bid_level and optimal_level and abs(bid_level - optimal_level) <= 1:
            if (bid_suit == 'NT' or optimal_suit == 'NT'):
                return True

        # Two-suited bids are alternatives to each other
        two_suited_bids = {'X', 'michaels', 'unusual_2nt'}
        # Michaels cuebid is 2 of opponent's suit, Unusual 2NT is 2NT
        # These are alternatives to each other and to takeout double

        return False

    def _extract_suit(self, bid: str) -> Optional[str]:
        """Extract suit from bid string"""
        if not bid or bid in ['Pass', 'X', 'XX']:
            return None
        if 'NT' in bid:
            return 'NT'
        for suit in ['♠', '♥', '♦', '♣', 'S', 'H', 'D', 'C']:
            if suit in bid:
                return suit
        # Try extracting after level number
        if len(bid) >= 2:
            return bid[1:]
        return None

    def _get_alternatives(self,
                         hand: Hand,
                         auction_context: Dict) -> List[str]:
        """Get alternative bids worth considering (for display purposes)"""
        # This is used for the alternative_bids field in feedback
        # We can reuse the acceptable alternatives logic here
        return []

    def _generate_acceptable_hint(self, user_bid: str, optimal_bid: str,
                                  hand: Hand, auction_context: Dict) -> str:
        """
        Generate a helpful hint explaining why the optimal bid is preferred
        over the acceptable alternative the user chose.
        """
        user_suit = self._extract_suit(user_bid)
        optimal_suit = self._extract_suit(optimal_bid)
        user_level = self._parse_bid_level(user_bid)
        optimal_level = self._parse_bid_level(optimal_bid)

        # SLAM BIDDING HINTS
        # User bid game, optimal was slam
        if optimal_level and optimal_level >= 6 and user_level and user_level in [4, 5]:
            return (f"with {hand.hcp} HCP and partnership values around 33+ points, "
                    f"slam is likely makeable. Consider using Blackwood (4NT) to check for aces.")

        # User bid slam, optimal was Blackwood
        if optimal_bid == '4NT' and user_level and user_level >= 6:
            return (f"Blackwood (4NT) first lets you check for aces before committing to slam. "
                    f"This avoids bidding slam missing two aces.")

        # User bid Blackwood, optimal was direct slam
        if user_bid == '4NT' and optimal_level and optimal_level >= 6:
            return (f"with a strong hand and likely sufficient aces, "
                    f"direct slam bidding is more efficient here.")

        # User bid small slam, optimal was grand
        if user_level == 6 and optimal_level == 7:
            return (f"with {hand.hcp} HCP and all aces accounted for, "
                    f"consider the grand slam when you have the values.")

        # User bid grand slam, optimal was small slam
        if user_level == 7 and optimal_level == 6:
            return "be cautious about grand slams - missing even one ace is fatal."

        # 1NT vs X (takeout double) - most common case
        if (user_bid == 'X' and 'NT' in optimal_bid) or (optimal_bid == 'X' and 'NT' in user_bid):
            if 'NT' in optimal_bid:
                # User doubled, optimal was NT
                return f"it shows {hand.hcp} HCP balanced with a stopper, giving partner a clearer picture of your hand."
            else:
                # User bid NT, optimal was double
                return "a takeout double better describes your shape and gets all suits into play."

        # Same suit, different levels (e.g., 3♥ vs 4♥)
        if user_suit == optimal_suit and user_level and optimal_level:
            if optimal_level > user_level:
                return f"with {hand.hcp} HCP and {hand.total_points} total points, you have enough for the higher level."
            else:
                return f"the lower level is more cautious and leaves room to explore."

        # Different suits at same level
        if user_level == optimal_level and user_suit and optimal_suit and user_suit != optimal_suit:
            if optimal_suit == 'NT':
                return f"with balanced shape, NT better describes your hand type."
            else:
                return f"showing {optimal_suit} first follows standard bidding priorities."

        # Opening bid alternatives
        if user_level == 1 and optimal_level == 1:
            return "this follows standard opening bid priorities in SAYC."

        # Default hint
        return f"{optimal_bid} is slightly more standard in SAYC."

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

def get_feedback_generator(db_path: str = 'backend/bridge.db') -> BiddingFeedbackGenerator:
    """Get singleton feedback generator instance"""
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = BiddingFeedbackGenerator(db_path)
    return _feedback_generator
