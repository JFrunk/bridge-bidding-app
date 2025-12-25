"""
Play Feedback Generator - Mirrors Bidding Feedback System

Provides real-time feedback on card play decisions including:
- Correctness evaluation (optimal, good, suboptimal, blunder)
- Quality scoring (0-10 scale)
- Tricks cost assessment
- Error categorization
- Actionable hints and explanations

This module does NOT modify play state - it only evaluates
and provides feedback on plays that have already been made.
"""

import sys
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple
from datetime import datetime

# Database abstraction layer for SQLite/PostgreSQL compatibility
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection

from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract


class PlayCorrectnessLevel(Enum):
    """Classification of play correctness"""
    OPTIMAL = "optimal"           # Maintains maximum tricks
    GOOD = "good"                 # Loses 0-1 tricks, reasonable alternative
    SUBOPTIMAL = "suboptimal"     # Loses 1-2 tricks
    BLUNDER = "blunder"           # Loses 2+ tricks
    ILLEGAL = "illegal"           # Did not follow suit when required


class PlayCategory(Enum):
    """Categories of card plays for learning purposes"""
    OPENING_LEAD = "opening_lead"
    FOLLOWING_SUIT = "following_suit"
    DISCARDING = "discarding"
    TRUMPING = "trumping"
    FINESSING = "finessing"
    CASHING = "cashing"
    HOLD_UP = "hold_up"
    COMMUNICATION = "communication"
    DEFENSIVE = "defensive"
    UNKNOWN = "unknown"


@dataclass
class PlayFeedback:
    """
    Structured play feedback for API/UI consumption

    This class represents evaluation of a single card play decision.
    It does NOT modify any game state - it's pure data.
    """

    # Context
    trick_number: int             # Which trick (1-13)
    position: str                 # "N", "E", "S", "W"
    user_card: str                # What user played (e.g., "A♠")

    # Evaluation
    correctness: PlayCorrectnessLevel
    score: float                  # 0-10 scale

    # Optimal alternative
    optimal_cards: List[str]      # Cards that maintain maximum tricks
    tricks_with_user_card: int    # Tricks achievable after this play
    tricks_with_optimal: int      # Tricks achievable with optimal play
    tricks_cost: int              # Difference (tricks lost)

    # Play context
    play_category: PlayCategory   # Type of play situation
    contract: str                 # e.g., "4♠ by S"
    is_declarer_side: bool        # True if declarer or dummy
    led_suit: Optional[str]       # Suit led to this trick (if not leader)

    # Explanation
    reasoning: str                # Why this card is good/bad
    helpful_hint: str             # Actionable advice

    # Learning
    key_concept: str              # "finessing", "trump management", etc.
    difficulty: str               # "beginner", "intermediate", "advanced"

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            **asdict(self),
            'correctness': self.correctness.value,
            'play_category': self.play_category.value
        }

    def to_user_message(self, verbosity: str = "normal") -> str:
        """
        Generate user-friendly message

        Args:
            verbosity: "minimal", "normal", or "detailed"
        """
        if self.correctness == PlayCorrectnessLevel.OPTIMAL:
            msg = f"Excellent! {self.user_card} is the best play here."
            if verbosity != "minimal" and self.reasoning:
                msg += f" {self.reasoning}"
            return msg

        elif self.correctness == PlayCorrectnessLevel.GOOD:
            msg = f"{self.user_card} is a reasonable play."
            if self.tricks_cost > 0:
                msg += f" (costs {self.tricks_cost} trick{'s' if self.tricks_cost > 1 else ''} vs optimal)"
            if verbosity == "detailed" and self.optimal_cards:
                msg += f"\n\nOptimal: {', '.join(self.optimal_cards)}"
            return msg

        elif self.correctness == PlayCorrectnessLevel.SUBOPTIMAL:
            msg = f"{', '.join(self.optimal_cards)} would be better than {self.user_card}."
            if self.tricks_cost > 0:
                msg += f" (costs {self.tricks_cost} trick{'s' if self.tricks_cost > 1 else ''})"
            if verbosity != "minimal" and self.helpful_hint:
                msg += f"\n\n{self.helpful_hint}"
            return msg

        elif self.correctness == PlayCorrectnessLevel.BLUNDER:
            msg = f"{self.user_card} is a significant mistake."
            if self.tricks_cost > 0:
                msg += f" Costs {self.tricks_cost} trick{'s' if self.tricks_cost > 1 else ''}!"
            if self.optimal_cards:
                msg += f"\n\nBetter: {', '.join(self.optimal_cards)}"
            if verbosity != "minimal" and self.helpful_hint:
                msg += f"\n\n{self.helpful_hint}"
            return msg

        else:  # ILLEGAL
            msg = f"Illegal play! You must follow suit when able."
            return msg


class PlayFeedbackGenerator:
    """
    Generates structured feedback for card play decisions

    IMPORTANT: This class is READ-ONLY with respect to game state.
    It evaluates decisions but does not modify:
    - Play state
    - Deal state
    - Session state

    It only writes to the play_decisions table for analytics.

    Supports two evaluation modes:
    1. DDS-based: Perfect double-dummy analysis (production)
    2. Minimax-based: Heuristic evaluation (development fallback)
    """

    # Score mapping based on tricks cost
    SCORE_MAP = {
        0: (PlayCorrectnessLevel.OPTIMAL, 10.0),
        1: (PlayCorrectnessLevel.GOOD, 7.5),
        2: (PlayCorrectnessLevel.SUBOPTIMAL, 5.0),
        3: (PlayCorrectnessLevel.BLUNDER, 2.5),
    }

    def __init__(self, use_dds: bool = True):
        """
        Initialize feedback generator

        Args:
            use_dds: Whether to use DDS for evaluation (falls back to minimax if unavailable)
        """
        self.use_dds = use_dds
        self._dds_available = None
        self._check_dds_availability()

    def _check_dds_availability(self):
        """Check if DDS is available on this platform"""
        import platform

        if platform.system() != 'Linux':
            self._dds_available = False
            return

        try:
            from endplay.dds import solve_board
            self._dds_available = True
        except ImportError:
            self._dds_available = False

    @property
    def dds_available(self) -> bool:
        """Whether DDS evaluation is available"""
        return self._dds_available and self.use_dds

    def evaluate_play(self,
                      play_state: PlayState,
                      user_card: Card,
                      position: str) -> PlayFeedback:
        """
        Evaluate a single card play and generate structured feedback

        Args:
            play_state: Current play state (before card is played)
            user_card: Card object the user played
            position: Position playing ("N", "E", "S", "W")

        Returns:
            PlayFeedback object

        Note: This method does NOT modify any game state.
        """
        # Get legal cards
        hand = play_state.hands[position]
        legal_cards = self._get_legal_cards(hand, play_state)

        # Check if play is legal
        if user_card not in legal_cards:
            return self._create_illegal_feedback(play_state, user_card, position, legal_cards)

        # Determine play category
        play_category = self._categorize_play(play_state, user_card, position, legal_cards)

        # Evaluate using DDS or fallback
        if self.dds_available:
            return self._evaluate_with_dds(play_state, user_card, position, legal_cards, play_category)
        else:
            return self._evaluate_with_minimax(play_state, user_card, position, legal_cards, play_category)

    def evaluate_and_store(self,
                           user_id: int,
                           play_state: PlayState,
                           user_card: Card,
                           position: str,
                           session_id: Optional[str] = None) -> PlayFeedback:
        """
        Evaluate play AND store in database for dashboard tracking

        Args:
            user_id: User ID
            play_state: Current play state
            user_card: Card played
            position: Position playing
            session_id: Optional session ID

        Returns:
            PlayFeedback object

        Note: This stores feedback in database but does NOT modify game state.
        """
        feedback = self.evaluate_play(play_state, user_card, position)
        self._store_feedback(user_id, feedback, session_id)
        return feedback

    def _get_legal_cards(self, hand: Hand, play_state: PlayState) -> List[Card]:
        """Get legal cards for this hand given current trick"""
        all_cards = list(hand.cards)

        # If leading, all cards are legal
        if not play_state.current_trick:
            return all_cards

        # Must follow suit if possible
        led_suit = play_state.current_trick[0][0].suit
        suit_cards = [c for c in all_cards if c.suit == led_suit]

        if suit_cards:
            return suit_cards

        # Can't follow suit - all cards legal
        return all_cards

    def _categorize_play(self,
                         play_state: PlayState,
                         user_card: Card,
                         position: str,
                         legal_cards: List[Card]) -> PlayCategory:
        """Determine the category of this play for learning purposes"""
        contract = play_state.contract
        trump_suit = contract.trump_suit

        # Check if this is opening lead
        if len(play_state.trick_history) == 0 and not play_state.current_trick:
            return PlayCategory.OPENING_LEAD

        # Check if following suit
        if play_state.current_trick:
            led_suit = play_state.current_trick[0][0].suit

            # Trumping (playing trump when can't follow)
            if user_card.suit == trump_suit and led_suit != trump_suit:
                return PlayCategory.TRUMPING

            # Discarding (not following, not trumping)
            if user_card.suit != led_suit and user_card.suit != trump_suit:
                return PlayCategory.DISCARDING

            # Following suit
            if user_card.suit == led_suit:
                return PlayCategory.FOLLOWING_SUIT

        # Cashing high cards
        if user_card.rank in ['A', 'K'] and not play_state.current_trick:
            return PlayCategory.CASHING

        return PlayCategory.UNKNOWN

    def _create_illegal_feedback(self,
                                  play_state: PlayState,
                                  user_card: Card,
                                  position: str,
                                  legal_cards: List[Card]) -> PlayFeedback:
        """Create feedback for an illegal play"""
        led_suit = play_state.current_trick[0][0].suit if play_state.current_trick else None

        return PlayFeedback(
            trick_number=len(play_state.trick_history) + 1,
            position=position,
            user_card=f"{user_card.rank}{user_card.suit}",
            correctness=PlayCorrectnessLevel.ILLEGAL,
            score=0.0,
            optimal_cards=[f"{c.rank}{c.suit}" for c in legal_cards[:3]],
            tricks_with_user_card=0,
            tricks_with_optimal=0,
            tricks_cost=0,
            play_category=PlayCategory.FOLLOWING_SUIT,
            contract=str(play_state.contract),
            is_declarer_side=self._is_declarer_side(position, play_state.contract),
            led_suit=led_suit,
            reasoning=f"Must follow {led_suit} when holding cards in that suit",
            helpful_hint=f"You have {led_suit} cards - you must play one of them",
            key_concept="Following suit",
            difficulty="beginner"
        )

    def _evaluate_with_dds(self,
                           play_state: PlayState,
                           user_card: Card,
                           position: str,
                           legal_cards: List[Card],
                           play_category: PlayCategory) -> PlayFeedback:
        """Evaluate play using DDS (Double Dummy Solver)"""
        from endplay.types import Deal, Denom, Player
        from endplay.dds import solve_board

        # Build PBN from current state
        pbn = self._build_pbn(play_state)

        # Get trump denomination
        trump = self._get_trump_denom(play_state.contract.trump_suit)

        # Map position to player
        player_map = {'N': Player.north, 'E': Player.east, 'S': Player.south, 'W': Player.west}
        player = player_map[position]

        try:
            # Create deal
            deal = Deal(pbn)

            # Solve for each legal card to find optimal
            card_tricks = {}
            for card in legal_cards:
                # Create a copy of deal with this card played
                # solve_board returns tricks for the side to play
                result = solve_board(deal, trump, player)

                # Get tricks for this specific card
                card_key = f"{card.rank}{card.suit}"
                # Note: solve_board returns tricks achievable
                card_tricks[card_key] = result

            # Find optimal tricks (maximum)
            max_tricks = max(card_tricks.values()) if card_tricks else 0

            # Find all optimal cards
            optimal_cards = [card for card, tricks in card_tricks.items() if tricks == max_tricks]

            # Get tricks for user's card
            user_card_key = f"{user_card.rank}{user_card.suit}"
            user_tricks = card_tricks.get(user_card_key, 0)

            # Calculate tricks cost
            tricks_cost = max_tricks - user_tricks

        except Exception as e:
            print(f"DDS evaluation failed: {e}")
            # Fall back to minimax
            return self._evaluate_with_minimax(play_state, user_card, position, legal_cards, play_category)

        # Determine correctness and score
        correctness, score = self._get_correctness_and_score(tricks_cost)

        # Generate feedback
        reasoning, hint = self._generate_feedback_text(
            play_state, user_card, position, optimal_cards, tricks_cost, play_category
        )

        led_suit = play_state.current_trick[0][0].suit if play_state.current_trick else None

        return PlayFeedback(
            trick_number=len(play_state.trick_history) + 1,
            position=position,
            user_card=user_card_key,
            correctness=correctness,
            score=score,
            optimal_cards=optimal_cards[:3],  # Limit to 3 for display
            tricks_with_user_card=user_tricks,
            tricks_with_optimal=max_tricks,
            tricks_cost=tricks_cost,
            play_category=play_category,
            contract=str(play_state.contract),
            is_declarer_side=self._is_declarer_side(position, play_state.contract),
            led_suit=led_suit,
            reasoning=reasoning,
            helpful_hint=hint,
            key_concept=self._get_key_concept(play_category),
            difficulty=self._assess_difficulty(play_state, play_category)
        )

    def _evaluate_with_minimax(self,
                                play_state: PlayState,
                                user_card: Card,
                                position: str,
                                legal_cards: List[Card],
                                play_category: PlayCategory) -> PlayFeedback:
        """
        Evaluate play using Minimax heuristics (fallback when DDS unavailable)

        This provides approximate evaluation based on:
        - Card rank relative to other legal options
        - Play category appropriateness
        - Basic tactical considerations
        """
        from engine.play.ai.evaluation import PositionEvaluator

        evaluator = PositionEvaluator()

        # Get declarer perspective
        declarer = play_state.contract.declarer
        perspective = declarer  # Evaluate from declarer's view

        # Evaluate current position
        base_score = evaluator.evaluate(play_state, perspective)

        # Heuristic scoring based on card choice
        user_card_key = f"{user_card.rank}{user_card.suit}"

        # Sort legal cards by rank
        rank_order = "23456789TJQKA"
        sorted_cards = sorted(legal_cards, key=lambda c: rank_order.index(c.rank), reverse=True)

        # Find user's card position in sorted list
        user_card_index = next((i for i, c in enumerate(sorted_cards) if c == user_card), len(sorted_cards))

        # Heuristic: penalize based on how far from best card
        # This is approximate - DDS would be more accurate
        if len(sorted_cards) <= 1:
            tricks_cost = 0
        elif user_card_index == 0:
            tricks_cost = 0  # Played highest - usually good
        elif user_card_index == len(sorted_cards) - 1:
            # Played lowest - could be good (saving winners) or bad
            if play_category in [PlayCategory.DISCARDING, PlayCategory.FOLLOWING_SUIT]:
                tricks_cost = 0  # Reasonable to save high cards
            else:
                tricks_cost = 1
        else:
            tricks_cost = min(user_card_index, 2)  # Middle cards - uncertain

        # Adjust based on play category
        if play_category == PlayCategory.CASHING and user_card.rank in ['A', 'K']:
            tricks_cost = 0  # Cashing winners is good
        elif play_category == PlayCategory.TRUMPING:
            tricks_cost = max(0, tricks_cost - 1)  # Trumping is often right

        # Determine optimal cards (heuristic: top cards are usually optimal)
        optimal_cards = [f"{c.rank}{c.suit}" for c in sorted_cards[:2]]

        # Determine correctness and score
        correctness, score = self._get_correctness_and_score(tricks_cost)

        # Mark as approximate since not using DDS
        reasoning, hint = self._generate_feedback_text(
            play_state, user_card, position, optimal_cards, tricks_cost, play_category
        )
        reasoning = "(Approximate) " + reasoning

        led_suit = play_state.current_trick[0][0].suit if play_state.current_trick else None

        return PlayFeedback(
            trick_number=len(play_state.trick_history) + 1,
            position=position,
            user_card=user_card_key,
            correctness=correctness,
            score=score,
            optimal_cards=optimal_cards,
            tricks_with_user_card=0,  # Unknown without DDS
            tricks_with_optimal=0,    # Unknown without DDS
            tricks_cost=tricks_cost,
            play_category=play_category,
            contract=str(play_state.contract),
            is_declarer_side=self._is_declarer_side(position, play_state.contract),
            led_suit=led_suit,
            reasoning=reasoning,
            helpful_hint=hint,
            key_concept=self._get_key_concept(play_category),
            difficulty=self._assess_difficulty(play_state, play_category)
        )

    def _get_correctness_and_score(self, tricks_cost: int) -> Tuple[PlayCorrectnessLevel, float]:
        """Map tricks cost to correctness level and score"""
        if tricks_cost <= 0:
            return PlayCorrectnessLevel.OPTIMAL, 10.0
        elif tricks_cost == 1:
            return PlayCorrectnessLevel.GOOD, 7.5
        elif tricks_cost == 2:
            return PlayCorrectnessLevel.SUBOPTIMAL, 5.0
        else:
            return PlayCorrectnessLevel.BLUNDER, max(0, 3.0 - (tricks_cost - 3))

    def _generate_feedback_text(self,
                                 play_state: PlayState,
                                 user_card: Card,
                                 position: str,
                                 optimal_cards: List[str],
                                 tricks_cost: int,
                                 play_category: PlayCategory) -> Tuple[str, str]:
        """Generate reasoning and helpful hint based on play analysis"""
        user_card_str = f"{user_card.rank}{user_card.suit}"

        if tricks_cost == 0:
            if play_category == PlayCategory.OPENING_LEAD:
                reasoning = "Good opening lead choice."
                hint = ""
            elif play_category == PlayCategory.CASHING:
                reasoning = "Correctly cashing a winner."
                hint = ""
            elif play_category == PlayCategory.TRUMPING:
                reasoning = "Good decision to ruff."
                hint = ""
            else:
                reasoning = "Optimal play."
                hint = ""

        elif tricks_cost == 1:
            if play_category == PlayCategory.OPENING_LEAD:
                reasoning = f"Reasonable lead, but {optimal_cards[0]} might be slightly better."
                hint = "Consider leading partner's suit or top of a sequence."
            elif play_category == PlayCategory.DISCARDING:
                reasoning = "Discard is acceptable but not optimal."
                hint = "Keep cards that work with partner or protect stoppers."
            else:
                reasoning = f"{optimal_cards[0]} maintains an extra trick."
                hint = "Think about which cards can still win tricks."

        elif tricks_cost == 2:
            reasoning = f"This costs 2 tricks. {optimal_cards[0]} would be much better."
            if play_category == PlayCategory.TRUMPING:
                hint = "Consider whether you need to ruff or preserve trumps."
            elif play_category == PlayCategory.FOLLOWING_SUIT:
                hint = "When following suit, consider which card gives best chance."
            else:
                hint = "Look for the play that maintains the most tricks."

        else:  # 3+ tricks cost
            reasoning = f"Significant mistake - costs {tricks_cost} tricks!"
            hint = f"Play {optimal_cards[0]} to maintain your trick potential."

        return reasoning, hint

    def _build_pbn(self, play_state: PlayState) -> str:
        """Build PBN string from play state"""
        hands = []
        for pos in ['N', 'E', 'S', 'W']:
            hand = play_state.hands[pos]
            suits = {'♠': [], '♥': [], '♦': [], '♣': []}
            for card in hand.cards:
                suits[card.suit].append(card.rank)
            for suit in suits:
                suits[suit].sort(key=lambda r: "23456789TJQKA".index(r), reverse=True)
            hand_str = '.'.join([
                ''.join(suits['♠']) or '-',
                ''.join(suits['♥']) or '-',
                ''.join(suits['♦']) or '-',
                ''.join(suits['♣']) or '-'
            ])
            hands.append(hand_str)

        return f"N:{' '.join(hands)}"

    def _get_trump_denom(self, trump_suit: Optional[str]):
        """Convert trump suit to endplay Denom"""
        from endplay.types import Denom

        trump_map = {
            None: Denom.nt,
            '♠': Denom.spades,
            '♥': Denom.hearts,
            '♦': Denom.diamonds,
            '♣': Denom.clubs
        }
        return trump_map.get(trump_suit, Denom.nt)

    def _is_declarer_side(self, position: str, contract: Contract) -> bool:
        """Check if position is on declarer's side"""
        declarer = contract.declarer
        if declarer in ['N', 'S']:
            return position in ['N', 'S']
        else:
            return position in ['E', 'W']

    def _get_key_concept(self, play_category: PlayCategory) -> str:
        """Map play category to learning concept"""
        concept_map = {
            PlayCategory.OPENING_LEAD: "Opening leads",
            PlayCategory.FOLLOWING_SUIT: "Following suit correctly",
            PlayCategory.DISCARDING: "Defensive discards",
            PlayCategory.TRUMPING: "Trump management",
            PlayCategory.FINESSING: "Finessing technique",
            PlayCategory.CASHING: "Cashing winners",
            PlayCategory.HOLD_UP: "Hold-up play",
            PlayCategory.COMMUNICATION: "Entries and communication",
            PlayCategory.DEFENSIVE: "Defensive play",
            PlayCategory.UNKNOWN: "Card play"
        }
        return concept_map.get(play_category, "Card play")

    def _assess_difficulty(self, play_state: PlayState, play_category: PlayCategory) -> str:
        """Assess difficulty level of this play decision"""
        trick_number = len(play_state.trick_history) + 1

        # Opening lead is intermediate
        if play_category == PlayCategory.OPENING_LEAD:
            return "intermediate"

        # Early tricks are easier
        if trick_number <= 3:
            return "beginner"

        # Late tricks with few cards are harder
        if trick_number >= 10:
            return "advanced"

        # Finessing is advanced
        if play_category == PlayCategory.FINESSING:
            return "advanced"

        return "intermediate"

    def _store_feedback(self,
                        user_id: int,
                        feedback: PlayFeedback,
                        session_id: Optional[str]):
        """Store feedback in play_decisions table"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO play_decisions (
                        user_id, session_id, position, trick_number,
                        user_card, optimal_card, score, rating,
                        tricks_cost, contract, feedback, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    session_id,
                    feedback.position,
                    feedback.trick_number,
                    feedback.user_card,
                    feedback.optimal_cards[0] if feedback.optimal_cards else None,
                    feedback.score,
                    feedback.correctness.value,
                    feedback.tricks_cost,
                    feedback.contract,
                    feedback.reasoning,
                    datetime.now()
                ))

                print(f"Stored play decision: {feedback.user_card} "
                      f"(correctness: {feedback.correctness.value}, score: {feedback.score})")
        except Exception as e:
            print(f"Error storing play feedback: {e}")
            import traceback
            traceback.print_exc()


# Singleton instance
_feedback_generator = None


def get_play_feedback_generator(use_dds: bool = True) -> PlayFeedbackGenerator:
    """Get singleton play feedback generator instance"""
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = PlayFeedbackGenerator(use_dds=use_dds)
    return _feedback_generator
