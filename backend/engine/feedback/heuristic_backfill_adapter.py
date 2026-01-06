"""
Heuristic Backfill Adapter - Physics-Based Play Violation Analysis

This adapter enriches PlayFeedback objects with explicit physics-based violation
analysis that maps to the frontend HeuristicScorecard component's four principles:

1. CONSERVATION - Don't waste high honors (Ace-on-King prevention)
2. FLUIDITY - Keep suits unblocked for partner runs
3. SIGNALING - Honest card choices following conventions (Lowest of Equals, etc.)
4. RESOURCES - Maintain HCP floors and entry preservation

Architecture:
- Takes a PlayFeedback object as input
- Analyzes the play for physics violations
- Returns enriched PlayFeedback with physics_violation field

The physics_violation field contains:
- principle: "conservation" | "fluidity" | "signaling" | "resources"
- violation_type: Specific violation name (e.g., "ace_on_king")
- explanation: Human-readable explanation
- corrective_action: What should have been played

Usage:
    from engine.feedback.heuristic_backfill_adapter import HeuristicBackfillAdapter

    adapter = HeuristicBackfillAdapter()
    enriched_feedback = adapter.enrich(feedback, play_state, user_card, optimal_cards)
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Import types from play_feedback
from engine.hand import Card, Hand
from engine.play_engine import PlayState


class PhysicsPrinciple(Enum):
    """The four physics principles of bridge card play"""
    CONSERVATION = "conservation"  # Don't waste high honors
    FLUIDITY = "fluidity"          # Keep suits unblocked
    SIGNALING = "signaling"        # Partner communication
    RESOURCES = "resources"        # Force out opponent cards


@dataclass
class PhysicsViolation:
    """
    Represents a physics principle violation in card play.

    This is the structured data that the frontend HeuristicScorecard
    component consumes to display educational diagnostics.
    """
    principle: str              # "conservation" | "fluidity" | "signaling" | "resources"
    violation_type: str         # Specific violation name (e.g., "ace_on_king")
    explanation: str            # Human-readable explanation
    corrective_action: str      # What should have been played
    severity: str = "minor"     # "minor" | "moderate" | "major"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "principle": self.principle,
            "violation_type": self.violation_type,
            "explanation": self.explanation,
            "corrective_action": self.corrective_action,
            "severity": self.severity
        }


class HeuristicBackfillAdapter:
    """
    Enriches PlayFeedback with physics-based violation analysis.

    This adapter analyzes card plays against the four physics principles
    and generates structured violation data for educational feedback.

    Detection Categories:

    CONSERVATION Violations:
    - ace_on_king: Honor spent on trick already won by partnership
    - wasted_winner: Overtook partner's winning card
    - premature_honor: Played honor when lower card would suffice

    FLUIDITY Violations:
    - blocked_suit: High card should have been played to clear path
    - entry_destruction: Removed entry prematurely
    - stranded_winners: Created unreachable winners

    SIGNALING Violations:
    - lowest_of_equals: Violated Lowest of Equals convention
    - top_of_sequence: Failed to lead top of sequence
    - attitude_error: Sent wrong attitude signal
    - count_error: Sent wrong count signal

    RESOURCES Violations:
    - overtake_partner: Wasted winner by overtaking partner
    - promotion_missed: Failed to force out enemy honor
    - hcp_waste: Unnecessary HCP expenditure
    """

    # Rank values for comparison (2=2, ..., A=14)
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    # Honor ranks (J, Q, K, A)
    HONOR_RANKS = {'J', 'Q', 'K', 'A', '11', '12', '13', '14'}

    def __init__(self):
        """Initialize the adapter"""
        pass

    def enrich(self,
               feedback: Any,  # PlayFeedback object
               play_state: Optional[PlayState],
               user_card: Card,
               optimal_cards: List[Card],
               position: str = 'S') -> Any:
        """
        Enrich a PlayFeedback object with physics violation analysis.

        Args:
            feedback: The PlayFeedback object to enrich
            play_state: Current play state (for context analysis)
            user_card: The card the user played
            optimal_cards: List of optimal cards from DDS/Minimax
            position: Position making the play ('N', 'E', 'S', 'W')

        Returns:
            The same PlayFeedback object with physics_violation added
        """
        # Check if user played optimally (in equivalence set)
        user_in_optimal = any(
            user_card.rank == opt.rank and user_card.suit == opt.suit
            for opt in optimal_cards
        )

        # If user played optimally, no violation to detect
        if user_in_optimal and len(optimal_cards) <= 1:
            feedback.physics_violation = None
            return feedback

        # Detect physics violations
        violation = self._detect_violation(
            play_state=play_state,
            user_card=user_card,
            optimal_cards=optimal_cards,
            position=position,
            signal_heuristic=getattr(feedback, 'signal_heuristic', None),
            signal_context=getattr(feedback, 'signal_context', None),
            is_signal_optimal=getattr(feedback, 'is_signal_optimal', True)
        )

        # Attach violation to feedback
        feedback.physics_violation = violation.to_dict() if violation else None

        return feedback

    def _detect_violation(self,
                          play_state: Optional[PlayState],
                          user_card: Card,
                          optimal_cards: List[Card],
                          position: str,
                          signal_heuristic: Optional[str],
                          signal_context: Optional[str],
                          is_signal_optimal: bool) -> Optional[PhysicsViolation]:
        """
        Detect the primary physics violation in this play.

        Returns the most significant violation, or None if no violation detected.
        """
        # Priority order: Conservation > Fluidity > Signaling > Resources

        # 1. Check CONSERVATION violations (highest priority)
        conservation_violation = self._check_conservation_violation(
            play_state, user_card, optimal_cards, position
        )
        if conservation_violation:
            return conservation_violation

        # 2. Check FLUIDITY violations
        fluidity_violation = self._check_fluidity_violation(
            play_state, user_card, optimal_cards, position
        )
        if fluidity_violation:
            return fluidity_violation

        # 3. Check SIGNALING violations
        if not is_signal_optimal and signal_heuristic:
            signaling_violation = self._check_signaling_violation(
                user_card, optimal_cards, signal_heuristic, signal_context
            )
            if signaling_violation:
                return signaling_violation

        # 4. Check RESOURCES violations
        resources_violation = self._check_resources_violation(
            play_state, user_card, optimal_cards, position
        )
        if resources_violation:
            return resources_violation

        return None

    def _check_conservation_violation(self,
                                       play_state: Optional[PlayState],
                                       user_card: Card,
                                       optimal_cards: List[Card],
                                       position: str) -> Optional[PhysicsViolation]:
        """
        Check for CONSERVATION principle violations.

        Conservation violations occur when high honors are wasted:
        - Ace-on-King: Playing ace when partner's king already wins
        - Wasted Winner: Overtaking partner's winning card
        - Premature Honor: Playing honor when lower card suffices
        """
        if not play_state or not play_state.current_trick:
            return None

        user_rank_val = self._rank_value(user_card.rank)
        opt_rank_val = self._rank_value(optimal_cards[0].rank) if optimal_cards else 0

        # Get current trick context
        current_trick = play_state.current_trick
        contract = play_state.contract

        if not current_trick:
            return None

        led_suit = current_trick[0][0].suit
        trump_suit = contract.trump_suit if contract else None

        # Find current winner
        current_winner_card, current_winner_pos = self._get_trick_winner(
            current_trick, led_suit, trump_suit
        )

        if not current_winner_card:
            return None

        # Determine partnerships
        declarer = contract.declarer if contract else None
        dummy = self._get_partner_position(declarer) if declarer else None
        is_declarer_side = position in [declarer, dummy] if declarer else False

        # Check if partner is winning
        partner_pos = self._get_partner_position(position)
        partner_is_winning = current_winner_pos == partner_pos

        # ACE-ON-KING: User played high when partner already winning
        if partner_is_winning:
            partner_winner_val = self._rank_value(current_winner_card.rank)

            # User played higher honor than partner's winner
            if (user_rank_val > partner_winner_val and
                self._is_honor(user_card.rank) and
                user_card.suit == led_suit):

                # Optimal play should be lower
                if opt_rank_val < user_rank_val:
                    return PhysicsViolation(
                        principle="conservation",
                        violation_type="ace_on_king",
                        explanation=(
                            f"Partner's {current_winner_card.rank}{current_winner_card.suit} "
                            f"was already winning. Playing {user_card.rank}{user_card.suit} "
                            f"wastes a winner on a trick already won."
                        ),
                        corrective_action=(
                            f"Play {optimal_cards[0].rank}{optimal_cards[0].suit} "
                            f"to conserve your {user_card.rank} for a future trick."
                        ),
                        severity="major" if user_rank_val >= 14 else "moderate"
                    )

        # WASTED WINNER: Overtook partner's winning card unnecessarily
        if partner_is_winning and user_rank_val > self._rank_value(current_winner_card.rank):
            if user_card.suit == led_suit and self._is_honor(user_card.rank):
                return PhysicsViolation(
                    principle="conservation",
                    violation_type="wasted_winner",
                    explanation=(
                        f"You overtook partner's {current_winner_card.rank}{current_winner_card.suit} "
                        f"with {user_card.rank}{user_card.suit}. Both are winners but only one "
                        f"was needed for this trick."
                    ),
                    corrective_action=(
                        f"Play {optimal_cards[0].rank}{optimal_cards[0].suit} and save "
                        f"your {user_card.rank} to win a different trick."
                    ),
                    severity="moderate"
                )

        # PREMATURE HONOR: Played honor when lower card would work
        if (self._is_honor(user_card.rank) and
            optimal_cards and
            not self._is_honor(optimal_cards[0].rank)):

            # Check if user's honor was unnecessary
            if user_card.suit == led_suit and opt_rank_val < user_rank_val:
                return PhysicsViolation(
                    principle="conservation",
                    violation_type="premature_honor",
                    explanation=(
                        f"Playing {user_card.rank}{user_card.suit} expends a valuable honor. "
                        f"A lower card would achieve the same result."
                    ),
                    corrective_action=(
                        f"Play {optimal_cards[0].rank}{optimal_cards[0].suit} to preserve "
                        f"your {user_card.rank} for when it's truly needed."
                    ),
                    severity="minor"
                )

        return None

    def _check_fluidity_violation(self,
                                   play_state: Optional[PlayState],
                                   user_card: Card,
                                   optimal_cards: List[Card],
                                   position: str) -> Optional[PhysicsViolation]:
        """
        Check for FLUIDITY principle violations.

        Fluidity violations occur when suits become blocked:
        - Blocked Suit: High card retained blocks partner's run
        - Entry Destruction: Prematurely removed an entry
        """
        if not play_state:
            return None

        hand = play_state.hands.get(position)
        if not hand:
            return None

        contract = play_state.contract
        trump_suit = contract.trump_suit if contract else None

        # Get cards in the same suit as user's play
        suit_cards = [c for c in hand.cards if c.suit == user_card.suit]
        opt_card = optimal_cards[0] if optimal_cards else None

        if not opt_card or opt_card.suit != user_card.suit:
            return None

        user_rank_val = self._rank_value(user_card.rank)
        opt_rank_val = self._rank_value(opt_card.rank)

        # BLOCKED SUIT: Should have played high to unblock
        # Detected when optimal is higher but user played lower
        if opt_rank_val > user_rank_val and len(suit_cards) <= 2:
            # Short holding where high card should have been played
            # This is the "unblock" situation
            if self._is_honor(opt_card.rank):
                return PhysicsViolation(
                    principle="fluidity",
                    violation_type="blocked_suit",
                    explanation=(
                        f"With only {len(suit_cards)} card(s) in {user_card.suit}, "
                        f"keeping {opt_card.rank}{opt_card.suit} blocks the suit. "
                        f"Partner cannot continue the suit after you win."
                    ),
                    corrective_action=(
                        f"Unblock by playing {opt_card.rank}{opt_card.suit} now, "
                        f"letting partner's lower cards maintain control."
                    ),
                    severity="moderate"
                )

        # STRANDED WINNERS: Created unreachable winners
        # Detected when user played a card that might strand winners
        if len(suit_cards) >= 3 and self._is_honor(user_card.rank):
            # Check if playing this honor might strand others
            remaining_honors = [c for c in suit_cards
                               if c.suit == user_card.suit
                               and self._is_honor(c.rank)
                               and not (c.rank == user_card.rank and c.suit == user_card.suit)]

            if remaining_honors and opt_rank_val < user_rank_val:
                return PhysicsViolation(
                    principle="fluidity",
                    violation_type="stranded_winners",
                    explanation=(
                        f"Playing {user_card.rank}{user_card.suit} may strand your other "
                        f"honor(s) in the suit without entries to cash them."
                    ),
                    corrective_action=(
                        f"Play {opt_card.rank}{opt_card.suit} to maintain flexibility "
                        f"and preserve entries to your winners."
                    ),
                    severity="minor"
                )

        return None

    def _check_signaling_violation(self,
                                    user_card: Card,
                                    optimal_cards: List[Card],
                                    signal_heuristic: str,
                                    signal_context: Optional[str]) -> Optional[PhysicsViolation]:
        """
        Check for SIGNALING principle violations.

        Signaling violations occur when card selection sends wrong message:
        - Lowest of Equals: Failed to play lowest from touching cards
        - Top of Sequence: Failed to lead top from sequence
        - Attitude Error: Sent wrong encourage/discourage signal
        - Count Error: Sent wrong count signal
        """
        if not signal_heuristic:
            return None

        opt_card = optimal_cards[0] if optimal_cards else None
        if not opt_card:
            return None

        heuristic_upper = signal_heuristic.upper()
        user_rank_val = self._rank_value(user_card.rank)
        opt_rank_val = self._rank_value(opt_card.rank)

        # LOWEST OF EQUALS (MIN_OF_EQUALS): Should have played lower
        if heuristic_upper in ['MIN_OF_EQUALS', 'DECLARER_CONSERVE', 'DEFENSIVE_DEFER']:
            if user_rank_val > opt_rank_val:
                return PhysicsViolation(
                    principle="signaling",
                    violation_type="lowest_of_equals",
                    explanation=(
                        f"When multiple cards are equivalent, convention says play lowest. "
                        f"Playing {user_card.rank}{user_card.suit} instead of "
                        f"{opt_card.rank}{opt_card.suit} violates 'Lowest of Equals'."
                    ),
                    corrective_action=(
                        f"Play {opt_card.rank}{opt_card.suit} to follow standard conventions "
                        f"and preserve {user_card.rank} for later."
                    ),
                    severity="minor"
                )

        # TOP OF SEQUENCE: Should have played higher
        if heuristic_upper == 'TOP_OF_SEQUENCE':
            if user_rank_val < opt_rank_val:
                return PhysicsViolation(
                    principle="signaling",
                    violation_type="top_of_sequence",
                    explanation=(
                        f"When leading from a sequence like KQJ, lead the top card. "
                        f"Leading {user_card.rank}{user_card.suit} instead of "
                        f"{opt_card.rank}{opt_card.suit} misleads partner about your holding."
                    ),
                    corrective_action=(
                        f"Lead {opt_card.rank}{opt_card.suit} to promise the touching "
                        f"honors below it."
                    ),
                    severity="minor"
                )

        # BOTTOM OF SEQUENCE: Should have played lower when following
        if heuristic_upper == 'BOTTOM_OF_SEQUENCE':
            if user_rank_val > opt_rank_val:
                return PhysicsViolation(
                    principle="signaling",
                    violation_type="bottom_of_sequence",
                    explanation=(
                        f"When following from a sequence, play the bottom. "
                        f"Playing {user_card.rank}{user_card.suit} instead of "
                        f"{opt_card.rank}{opt_card.suit} fails to signal your higher cards."
                    ),
                    corrective_action=(
                        f"Play {opt_card.rank}{opt_card.suit} to signal possession of "
                        f"higher touching honors."
                    ),
                    severity="minor"
                )

        # ATTITUDE SIGNAL: Wrong encourage/discourage
        if heuristic_upper == 'ATTITUDE_SIGNAL':
            return PhysicsViolation(
                principle="signaling",
                violation_type="attitude_error",
                explanation=(
                    f"Attitude signals use high cards to encourage, low to discourage. "
                    f"Your {user_card.rank}{user_card.suit} sends a different message "
                    f"than {opt_card.rank}{opt_card.suit}."
                ),
                corrective_action=(
                    f"Play {opt_card.rank}{opt_card.suit} to send the correct attitude "
                    f"signal to partner."
                ),
                severity="minor"
            )

        # COUNT SIGNAL: Wrong count message
        if heuristic_upper == 'COUNT_SIGNAL':
            return PhysicsViolation(
                principle="signaling",
                violation_type="count_error",
                explanation=(
                    f"Count signals show suit length: high-low = even, low-high = odd. "
                    f"Playing {user_card.rank}{user_card.suit} sends wrong count information."
                ),
                corrective_action=(
                    f"Play {opt_card.rank}{opt_card.suit} to accurately show your count."
                ),
                severity="minor"
            )

        return None

    def _check_resources_violation(self,
                                    play_state: Optional[PlayState],
                                    user_card: Card,
                                    optimal_cards: List[Card],
                                    position: str) -> Optional[PhysicsViolation]:
        """
        Check for RESOURCES principle violations.

        Resources violations occur when HCP is wasted or opponents not pressured:
        - Overtake Partner: Wasted winner by overtaking
        - Promotion Missed: Failed to force out enemy honor
        """
        if not play_state or not play_state.current_trick:
            return None

        opt_card = optimal_cards[0] if optimal_cards else None
        if not opt_card:
            return None

        user_rank_val = self._rank_value(user_card.rank)
        opt_rank_val = self._rank_value(opt_card.rank)

        # PROMOTION MISSED: Should have played high to force out enemy honors
        # Detected when optimal is higher (forcing play) but user played low
        if opt_rank_val > user_rank_val and self._is_honor(opt_card.rank):
            current_trick = play_state.current_trick
            led_suit = current_trick[0][0].suit if current_trick else None

            # Check if this is a third-hand situation where we should force
            if len(current_trick) == 2 and user_card.suit == led_suit:
                return PhysicsViolation(
                    principle="resources",
                    violation_type="promotion_missed",
                    explanation=(
                        f"Playing {opt_card.rank}{opt_card.suit} third hand would force "
                        f"declarer to use a high card or lose the trick."
                    ),
                    corrective_action=(
                        f"Play {opt_card.rank}{opt_card.suit} to pressure declarer's "
                        f"high cards and promote your lower honors."
                    ),
                    severity="minor"
                )

        return None

    # ========== Helper Methods ==========

    def _rank_value(self, rank: str) -> int:
        """Get numeric value of rank"""
        return self.RANK_VALUES.get(rank, 0)

    def _is_honor(self, rank: str) -> bool:
        """Check if rank is an honor (J, Q, K, A)"""
        return rank in {'J', 'Q', 'K', 'A'}

    def _get_partner_position(self, position: str) -> str:
        """Get partner's position (opposite)"""
        opposite = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
        return opposite.get(position, 'N')

    def _get_trick_winner(self,
                          current_trick: List,
                          led_suit: str,
                          trump_suit: Optional[str]) -> tuple:
        """
        Determine current trick winner considering trump.

        Returns (winning_card, winning_position) or (None, None) if empty.
        """
        if not current_trick:
            return None, None

        winner_card = None
        winner_pos = None
        winner_rank = -1

        for card, pos in current_trick:
            card_rank = self._rank_value(card.rank)

            # Trump beats non-trump
            if trump_suit and card.suit == trump_suit:
                if winner_card is None or winner_card.suit != trump_suit:
                    winner_card = card
                    winner_pos = pos
                    winner_rank = card_rank
                elif card_rank > winner_rank:
                    winner_card = card
                    winner_pos = pos
                    winner_rank = card_rank
            elif card.suit == led_suit:
                if winner_card is None or (winner_card.suit != trump_suit and card_rank > winner_rank):
                    winner_card = card
                    winner_pos = pos
                    winner_rank = card_rank

        return winner_card, winner_pos


# Singleton instance
_adapter_instance = None


def get_heuristic_backfill_adapter() -> HeuristicBackfillAdapter:
    """
    Get singleton adapter instance.

    Returns:
        HeuristicBackfillAdapter instance
    """
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = HeuristicBackfillAdapter()
    return _adapter_instance


# Self-test
if __name__ == '__main__':
    print("Heuristic Backfill Adapter - Self Test")
    print("=" * 50)

    adapter = get_heuristic_backfill_adapter()
    print("Adapter initialized successfully!")

    # Test violation creation
    violation = PhysicsViolation(
        principle="conservation",
        violation_type="ace_on_king",
        explanation="Test explanation",
        corrective_action="Test corrective action",
        severity="major"
    )
    print(f"\nTest violation: {violation.to_dict()}")

    print("\nAll self-tests passed!")
