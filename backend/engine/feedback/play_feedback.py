"""
Play Feedback Generator - DDS-Based Card Play Evaluation

Provides real-time feedback on card play decisions using DDS (Double Dummy Solver)
for optimal play analysis. This is the play equivalent of bidding_feedback.py.

Features:
- DDS-based optimal play evaluation (<1ms per solve)
- Scoring (0-10 scale) with correctness ratings
- Trick cost calculation (how many tricks lost vs optimal)
- Play categorization (opening lead, following suit, discarding, trumping)
- Educational feedback with learning concepts
- Database storage for dashboard analytics

Performance: <1ms per solve on Linux (production)
Fallback: Minimax heuristics on macOS (development)

This module does NOT modify play state - it only evaluates and provides feedback.
"""

import sys
import platform
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple
from datetime import datetime

# Database abstraction layer
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection

from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract

# Import DDS if available (Linux production)
# Falls back to Minimax on macOS (development)
try:
    from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE
except ImportError:
    DDS_AVAILABLE = False
    DDSPlayAI = None

# Always have Minimax available as fallback
from engine.play.ai.minimax_ai import MinimaxPlayAI

# Import tactical signal overlay for user play signal evaluation
try:
    from engine.play.ai.play_signal_overlay import TacticalPlayFilter, SignalResult
    SIGNAL_OVERLAY_AVAILABLE = True
except ImportError:
    SIGNAL_OVERLAY_AVAILABLE = False
    TacticalPlayFilter = None
    SignalResult = None

# Import heuristic backfill adapter for physics violation analysis
try:
    from engine.feedback.heuristic_backfill_adapter import get_heuristic_backfill_adapter
    HEURISTIC_ADAPTER_AVAILABLE = True
except ImportError:
    HEURISTIC_ADAPTER_AVAILABLE = False
    get_heuristic_backfill_adapter = None


class PlayCorrectnessLevel(Enum):
    """Classification of play correctness"""
    OPTIMAL = "optimal"         # Perfect play - achieves maximum tricks
    GOOD = "good"               # Close to optimal (0-1 trick cost)
    SUBOPTIMAL = "suboptimal"   # Costs tricks but not terrible
    BLUNDER = "blunder"         # Significant trick loss
    ILLEGAL = "illegal"         # Not a legal play


class PlayCategory(Enum):
    """Type of play situation"""
    OPENING_LEAD = "opening_lead"       # First card of hand
    FOLLOWING_SUIT = "following_suit"   # Must follow suit
    DISCARDING = "discarding"           # Void in led suit, no trump
    TRUMPING = "trumping"               # Void in led suit, can ruff
    OVERRUFFING = "overruffing"         # Ruff over opponent's ruff
    SLUFFING = "sluffing"               # Discard when could trump
    FINESSING = "finessing"             # Finesse play
    CASHING = "cashing"                 # Cashing winners
    HOLD_UP = "hold_up"                 # Hold-up play in NT
    DUCKING = "ducking"                 # Ducking to maintain entries


@dataclass
class PlayFeedback:
    """
    Structured play feedback for API/UI consumption.

    This class represents evaluation of a single card play decision.
    It does NOT modify any game state - it's pure data.
    """

    # Context
    trick_number: int           # Which trick (1-13)
    position: str               # 'N', 'E', 'S', 'W'
    user_card: str              # What user played (e.g., "A♠")
    contract: str               # Contract string (e.g., "4♠")
    is_declarer_side: bool      # True if declarer/dummy, False if defender
    led_suit: Optional[str]     # Suit that was led (None if opening lead)

    # Evaluation
    correctness: PlayCorrectnessLevel
    score: float                # 0-10 scale

    # Optimal analysis
    optimal_cards: List[str]    # Cards that achieve maximum tricks
    tricks_cost: int            # Tricks lost vs optimal (0 = optimal, -1 = unknown/heuristic)
    tricks_with_user_card: int  # Tricks achievable with user's play (-1 = unknown)
    tricks_with_optimal: int    # Tricks achievable with best play (-1 = unknown)

    # Explanation
    reasoning: str              # Why this play? What went wrong?
    play_category: PlayCategory # Type of play situation
    helpful_hint: str           # Actionable advice

    # Learning
    key_concept: str            # Bridge concept being tested
    difficulty: str             # beginner, intermediate, advanced, expert

    # Analysis source (added to distinguish DDS vs heuristic evaluation)
    analysis_source: str = "dds"  # "dds" = exact, "heuristic" = Minimax estimation

    # Signal analysis (NEW - for tactical play overlay)
    signal_reason: Optional[str] = None       # Why this card was chosen from equivalence set
    signal_heuristic: Optional[str] = None    # Heuristic applied (e.g., "MIN_OF_EQUALS")
    signal_context: Optional[str] = None      # Context type (e.g., "SECOND_HAND_FOLLOW")
    is_signal_optimal: bool = True            # True if follows standard conventions

    # Physics violation analysis (for HeuristicScorecard component)
    physics_violation: Optional[Dict] = None  # Structured physics principle violation data

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            **asdict(self),
            'correctness': self.correctness.value,
            'play_category': self.play_category.value
        }

    def to_user_message(self, verbosity: str = "normal") -> str:
        """
        Generate user-friendly message.

        Args:
            verbosity: "minimal", "normal", or "detailed"
        """
        # Flag for heuristic analysis (tricks_cost = -1 means unknown)
        is_heuristic = self.analysis_source == "heuristic" or self.tricks_cost < 0

        if self.correctness == PlayCorrectnessLevel.OPTIMAL:
            msg = f"Excellent! {self.user_card} is great here."
            if verbosity != "minimal" and self.reasoning:
                msg += f" {self.reasoning}"
            return msg

        elif self.correctness == PlayCorrectnessLevel.GOOD:
            msg = f"{self.user_card} is a reasonable play."
            if not is_heuristic and self.tricks_cost == 1:
                msg += f" (Optimal: {', '.join(self.optimal_cards[:2])} - costs 1 trick)"
            elif self.optimal_cards:
                msg += f" (Optimal: {', '.join(self.optimal_cards[:2])})"
            if verbosity != "minimal" and self.helpful_hint:
                msg += f"\n\nTip: {self.helpful_hint}"
            return msg

        elif self.correctness == PlayCorrectnessLevel.SUBOPTIMAL:
            optimal_str = ', '.join(self.optimal_cards[:2])
            msg = f"{optimal_str} would be better than {self.user_card}."
            if not is_heuristic and self.tricks_cost > 0:
                msg += f" (Costs {self.tricks_cost} trick{'s' if self.tricks_cost > 1 else ''})"
            if verbosity != "minimal" and self.helpful_hint:
                msg += f"\n\n{self.helpful_hint}"
            return msg

        elif self.correctness == PlayCorrectnessLevel.BLUNDER:
            optimal_str = ', '.join(self.optimal_cards[:2])
            if not is_heuristic and self.tricks_cost > 0:
                msg = f"Mistake: {self.user_card} costs {self.tricks_cost} tricks!"
            else:
                msg = f"Mistake: {self.user_card} is not the best play here."
            msg += f"\n\nBetter play: {optimal_str}"
            if verbosity != "minimal" and self.helpful_hint:
                msg += f"\n\n{self.helpful_hint}"
            return msg

        else:  # ILLEGAL
            msg = f"Illegal play: {self.user_card}."
            if self.helpful_hint:
                msg += f" {self.helpful_hint}"
            return msg


class PlayFeedbackGenerator:
    """
    Generates structured feedback for card play decisions using DDS.

    IMPORTANT: This class is READ-ONLY with respect to game state.
    It evaluates decisions but does not modify:
    - Play state
    - Trick history
    - Hands

    It only writes to the play_decisions table for analytics.

    Performance:
    - DDS: <1ms per solve (Linux production)
    - Minimax: ~50-200ms per solve (macOS development fallback)
    """

    def __init__(self, use_dds: bool = True):
        """
        Initialize the feedback generator.

        Args:
            use_dds: If True, use DDS when available. If False, always use Minimax.
        """
        # DDS only works reliably on Linux
        self.platform_allows_dds = platform.system() == 'Linux'
        self.dds_available = DDS_AVAILABLE and self.platform_allows_dds and use_dds

        if self.dds_available:
            try:
                self._dds_ai = DDSPlayAI()
                print("PlayFeedbackGenerator: Using DDS for optimal play analysis")
            except Exception as e:
                print(f"PlayFeedbackGenerator: DDS init failed ({e}), using Minimax")
                self.dds_available = False
                self._dds_ai = None
        else:
            self._dds_ai = None

        # Always have Minimax as fallback
        self._minimax_ai = MinimaxPlayAI(max_depth=3)

        # Initialize tactical signal filter for user play signal evaluation
        self._tactical_filter = None
        if SIGNAL_OVERLAY_AVAILABLE:
            try:
                self._tactical_filter = TacticalPlayFilter()
            except Exception as e:
                print(f"PlayFeedbackGenerator: TacticalPlayFilter init failed ({e})")

        # Initialize heuristic backfill adapter for physics violation analysis
        self._heuristic_adapter = None
        if HEURISTIC_ADAPTER_AVAILABLE:
            try:
                self._heuristic_adapter = get_heuristic_backfill_adapter()
            except Exception as e:
                print(f"PlayFeedbackGenerator: HeuristicBackfillAdapter init failed ({e})")

    def _evaluate_signal(self,
                         play_state: PlayState,
                         user_card: Card,
                         position: str,
                         optimal_cards: List[Card]) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
        """
        Evaluate if user's play follows standard bridge signaling conventions.

        When multiple cards have the same DDS value (equivalence set), there's
        still a "correct" card to play based on signaling conventions:
        - 2nd hand low
        - 3rd hand high (or bottom of sequence)
        - Attitude signals when discarding
        - Count signals

        Args:
            play_state: Current play state
            user_card: Card user played
            position: Position making the play
            optimal_cards: Cards with optimal DDS value (equivalence set)

        Returns:
            Tuple of (signal_reason, signal_heuristic, signal_context, is_signal_optimal)
        """
        if self._tactical_filter is None:
            return (None, None, None, True)

        # Only evaluate signals when user card is in the equivalence set
        # (i.e., user didn't lose tricks but may have violated conventions)
        user_in_equiv_set = any(
            user_card.rank == c.rank and user_card.suit == c.suit
            for c in optimal_cards
        )

        if not user_in_equiv_set or len(optimal_cards) <= 1:
            # User either lost tricks (different issue) or only one optimal card
            return (None, None, None, True)

        # Get the tactically optimal card from the equivalence set
        try:
            hand = play_state.hands[position]
            trump_suit = play_state.contract.trump_suit if play_state.contract else None

            signal_result = self._tactical_filter.select_tactical_card(
                equivalence_set=optimal_cards,
                game_state=play_state,
                position=position,
                hand=hand,
                trump_suit=trump_suit
            )

            # Check if user played the signal-optimal card
            user_matches_signal = (
                user_card.rank == signal_result.card.rank and
                user_card.suit == signal_result.card.suit
            )

            return (
                signal_result.reason,
                signal_result.heuristic.value if signal_result.heuristic else None,
                signal_result.context.value if signal_result.context else None,
                user_matches_signal
            )

        except Exception as e:
            # Signal evaluation failed - don't crash, just skip signal feedback
            return (None, None, None, True)

    def evaluate_play(self,
                      play_state: PlayState,
                      user_card: Card,
                      position: str) -> PlayFeedback:
        """
        Evaluate a single card play and generate structured feedback.

        Args:
            play_state: Current play state (before the card is played)
            user_card: The card the user chose to play
            position: Position making the play ('N', 'E', 'S', 'W')

        Returns:
            PlayFeedback object with evaluation

        Note: This method does NOT modify any game state.
        """
        # Get legal cards for this position
        hand = play_state.hands[position]
        legal_cards = self._get_legal_cards(hand, play_state)

        # Check if play is legal
        user_card_str = f"{user_card.rank}{user_card.suit}"
        is_legal = any(c.rank == user_card.rank and c.suit == user_card.suit
                       for c in legal_cards)

        if not is_legal:
            return self._create_illegal_feedback(user_card, position, play_state)

        # Determine play category
        play_category = self._categorize_play(play_state, position, user_card)

        # Get optimal plays using DDS or Minimax
        optimal_cards, user_tricks, optimal_tricks, analysis_source = self._analyze_plays(
            play_state, position, user_card, legal_cards
        )

        # Calculate trick cost (may be -1 if using heuristics and not optimal)
        if user_tricks >= 0 and optimal_tricks >= 0:
            tricks_cost = optimal_tricks - user_tricks
        else:
            # Heuristic mode - we don't know exact trick cost
            # Check if user played optimal card
            user_is_optimal = any(
                user_card.rank == c.rank and user_card.suit == c.suit
                for c in optimal_cards
            )
            tricks_cost = 0 if user_is_optimal else -1  # -1 = unknown

        # Determine correctness level
        correctness = self._determine_correctness(tricks_cost, user_card, optimal_cards)

        # Calculate score (0-10)
        score = self._calculate_score(correctness, tricks_cost)

        # Generate reasoning and hints
        reasoning = self._generate_reasoning(
            play_category, correctness, user_card, optimal_cards,
            tricks_cost, play_state, position
        )
        helpful_hint = self._generate_hint(
            play_category, correctness, user_card, optimal_cards,
            play_state, position
        )

        # Determine learning concept and difficulty
        key_concept = self._extract_key_concept(play_category, play_state)
        difficulty = self._assess_difficulty(play_category, play_state)

        # Determine led suit
        led_suit = None
        if play_state.current_trick:
            led_suit = play_state.current_trick[0][0].suit

        # Evaluate signal conventions (only when user is in equivalence set)
        signal_reason, signal_heuristic, signal_context, is_signal_optimal = self._evaluate_signal(
            play_state, user_card, position, optimal_cards
        )

        # CONSISTENCY CHECK: Avoid contradictory feedback
        # If correctness is OPTIMAL but is_signal_optimal is False, we need to check for contradictions.
        # The reasoning text might say the play was correct (e.g., "conserving honors") while
        # is_signal_optimal=False suggests it wasn't. This confuses users.
        #
        # Resolution: If reasoning indicates the play was actually correct/good, align is_signal_optimal.
        if correctness == PlayCorrectnessLevel.OPTIMAL and not is_signal_optimal and reasoning:
            # Check if reasoning says the play was correct
            reasoning_lower = reasoning.lower()
            correct_indicators = ["correct", "conserving", "optimal", "good", "right", "best"]
            if any(indicator in reasoning_lower for indicator in correct_indicators):
                # Reasoning says correct but signal says not optimal - contradiction!
                # Suppress the signal deviation to avoid confusing feedback
                is_signal_optimal = True

        # Build feedback object
        feedback = PlayFeedback(
            trick_number=len(play_state.trick_history) + 1,
            position=position,
            user_card=user_card_str,
            contract=str(play_state.contract) if play_state.contract else "",
            is_declarer_side=self._is_declarer_side(position, play_state.contract),
            led_suit=led_suit,
            correctness=correctness,
            score=score,
            optimal_cards=[f"{c.rank}{c.suit}" for c in optimal_cards],
            tricks_cost=tricks_cost,
            tricks_with_user_card=user_tricks,
            tricks_with_optimal=optimal_tricks,
            reasoning=reasoning,
            play_category=play_category,
            helpful_hint=helpful_hint,
            key_concept=key_concept,
            difficulty=difficulty,
            analysis_source=analysis_source,
            signal_reason=signal_reason,
            signal_heuristic=signal_heuristic,
            signal_context=signal_context,
            is_signal_optimal=is_signal_optimal
        )

        # Enrich with physics violation analysis
        if self._heuristic_adapter:
            try:
                feedback = self._heuristic_adapter.enrich(
                    feedback=feedback,
                    play_state=play_state,
                    user_card=user_card,
                    optimal_cards=optimal_cards,
                    position=position
                )
            except Exception as e:
                # Don't fail the whole feedback if physics analysis fails
                print(f"Physics violation analysis failed: {e}")
                feedback.physics_violation = None

        return feedback

    def evaluate_and_store(self,
                           user_id: int,
                           play_state: PlayState,
                           user_card: Card,
                           position: str,
                           session_id: Optional[str] = None,
                           hand_number: Optional[int] = None) -> PlayFeedback:
        """
        Evaluate play AND store in database for dashboard tracking.

        Args:
            user_id: User ID
            play_state: Current play state
            user_card: Card user played
            position: Position making play
            session_id: Optional session ID
            hand_number: Optional hand number within session (1-indexed)

        Returns:
            PlayFeedback object

        Note: This stores feedback in database but does NOT modify game state.
        """
        # Generate feedback
        feedback = self.evaluate_play(play_state, user_card, position)

        # Store in database
        self._store_feedback(user_id, feedback, session_id, hand_number)

        return feedback

    def _get_legal_cards(self, hand: Hand, play_state: PlayState) -> List[Card]:
        """Get all legal cards from hand"""
        if not play_state.current_trick:
            return list(hand.cards)

        led_suit = play_state.current_trick[0][0].suit
        cards_in_suit = [c for c in hand.cards if c.suit == led_suit]

        if cards_in_suit:
            return cards_in_suit

        # Void - any card is legal
        return list(hand.cards)

    def _categorize_play(self, state: PlayState, position: str, card: Card) -> PlayCategory:
        """Determine what type of play situation this is"""
        # Opening lead - only the very first card of the hand
        if not state.trick_history and not state.current_trick:
            return PlayCategory.OPENING_LEAD

        # Leading to a subsequent trick (not opening lead)
        if not state.current_trick:
            # This is a lead, but not the opening lead
            # Categorize based on what card is being led
            trump_suit = state.contract.trump_suit if state.contract else None
            if card.suit == trump_suit:
                return PlayCategory.TRUMPING  # Leading trump
            # Could add more specific lead categories later
            # For now, categorize as following suit (general play)
            return PlayCategory.FOLLOWING_SUIT

        # Following suit
        led_suit = state.current_trick[0][0].suit
        hand = state.hands[position]
        has_led_suit = any(c.suit == led_suit for c in hand.cards)

        if card.suit == led_suit:
            return PlayCategory.FOLLOWING_SUIT

        # Void in led suit
        trump_suit = state.contract.trump_suit if state.contract else None

        if card.suit == trump_suit:
            # Check if overruffing
            existing_trumps = [c for c, _ in state.current_trick if c.suit == trump_suit]
            if existing_trumps:
                return PlayCategory.OVERRUFFING
            return PlayCategory.TRUMPING
        else:
            # Discarding - check if could have trumped
            if trump_suit and any(c.suit == trump_suit for c in hand.cards):
                return PlayCategory.SLUFFING
            return PlayCategory.DISCARDING

    def _analyze_plays(self, state: PlayState, position: str,
                       user_card: Card, legal_cards: List[Card]
                       ) -> Tuple[List[Card], int, int, str]:
        """
        Analyze all legal plays using DDS or Minimax.

        Returns:
            (optimal_cards, user_tricks, optimal_tricks, analysis_source)
            - analysis_source: "dds" for exact analysis, "heuristic" for Minimax
        """
        if self.dds_available and self._dds_ai:
            return self._analyze_with_dds(state, position, user_card, legal_cards)
        else:
            return self._analyze_with_minimax(state, position, user_card, legal_cards)

    def _analyze_with_dds(self, state: PlayState, position: str,
                          user_card: Card, legal_cards: List[Card]
                          ) -> Tuple[List[Card], int, int, str]:
        """
        Use DDS solve_board to find optimal plays.

        solve_board returns (card, tricks) pairs showing how many tricks
        can be made with each legal play. We find which cards achieve
        the maximum and compare to user's choice.

        IMPORTANT: When reconstructing a deal with cards already played to the
        current trick, we must set deal.first to the LEADER of the trick (not
        the current player), then play the cards in order. This ensures endplay
        correctly tracks the trick state and who is to play next.

        Returns:
            (optimal_cards, user_tricks, optimal_tricks, analysis_source)
            - analysis_source is "dds" for exact DDS analysis
        """
        try:
            from endplay.types import Deal, Player as EndplayPlayer, Denom
            from endplay.dds import solve_board

            # Convert state to endplay format
            # IMPORTANT: Use include_current_trick=True to add cards back to hands
            # before calling deal.play(). This prevents "card not in hand" errors.
            pbn = self._dds_ai._get_pbn_string(state, include_current_trick=True)
            deal = Deal(pbn)
            deal.trump = self._dds_ai._convert_trump(state.contract.trump_suit)

            # Set up the current trick state correctly
            if state.current_trick:
                # Set deal.first to the LEADER of the trick (first player who played)
                # This is critical - endplay needs to know who led to reconstruct the trick
                leader = state.current_trick[0][1]  # (card, position) - get position
                deal.first = self._dds_ai._convert_position(leader)

                # Play the cards already in the trick
                # After this, endplay will know the current player is `position`
                for played_card, played_pos in state.current_trick:
                    endplay_card = self._dds_ai._convert_card_to_endplay(played_card)
                    deal.play(endplay_card)
            else:
                # No cards in current trick - position is leading
                deal.first = self._dds_ai._convert_position(position)

            # Solve to get optimal plays
            solved = solve_board(deal)

            # Build mapping of card -> tricks
            card_tricks = {}
            max_tricks = -1

            for endplay_card, tricks in solved:
                our_card = self._dds_ai._convert_endplay_card_to_ours(endplay_card, legal_cards)
                if our_card:
                    card_tricks[f"{our_card.rank}{our_card.suit}"] = tricks
                    if tricks > max_tricks:
                        max_tricks = tricks

            # Find optimal cards (all that achieve max tricks)
            optimal_cards = [c for c in legal_cards
                             if card_tricks.get(f"{c.rank}{c.suit}", -1) == max_tricks]

            # Get tricks for user's card
            user_key = f"{user_card.rank}{user_card.suit}"
            user_tricks = card_tricks.get(user_key, 0)

            return optimal_cards, user_tricks, max_tricks, "dds"

        except Exception as e:
            print(f"DDS analysis failed: {e}, falling back to Minimax")
            return self._analyze_with_minimax(state, position, user_card, legal_cards)

    def _analyze_with_minimax(self, state: PlayState, position: str,
                               user_card: Card, legal_cards: List[Card]
                               ) -> Tuple[List[Card], int, int, str]:
        """
        Use Minimax to estimate optimal plays.

        Less accurate than DDS but works on all platforms.
        Returns relative scoring rather than exact trick counts.

        Returns:
            (optimal_cards, user_tricks, optimal_tricks, analysis_source)
            - When using heuristics, tricks values are set to -1 (unknown)
            - analysis_source is "heuristic" to indicate inexact evaluation
        """
        # Get Minimax's choice
        try:
            optimal_card = self._minimax_ai.choose_card(state, position)
        except Exception as e:
            print(f"Minimax failed: {e}")
            optimal_card = legal_cards[0] if legal_cards else user_card

        # For Minimax, we can only determine if user's choice matches optimal
        # We CANNOT determine exact trick counts, so we use -1 to indicate unknown

        # If user played the same as Minimax, it's optimal
        if user_card.rank == optimal_card.rank and user_card.suit == optimal_card.suit:
            # Optimal play - tricks_cost will be 0
            return [optimal_card], 0, 0, "heuristic"

        # Non-optimal play - we don't know exact trick cost
        # Use -1 to indicate "unknown" rather than making up fake values
        return [optimal_card], -1, -1, "heuristic"

    def _determine_correctness(self, tricks_cost: int, user_card: Card,
                               optimal_cards: List[Card]) -> PlayCorrectnessLevel:
        """Determine correctness level based on trick cost"""
        # Check if user played an optimal card
        for opt_card in optimal_cards:
            if user_card.rank == opt_card.rank and user_card.suit == opt_card.suit:
                return PlayCorrectnessLevel.OPTIMAL

        if tricks_cost == 0:
            return PlayCorrectnessLevel.OPTIMAL
        elif tricks_cost == -1:
            # Heuristic mode - we know it's not optimal but don't know how bad
            # Default to SUBOPTIMAL (non-judgmental - we don't claim specific trick loss)
            return PlayCorrectnessLevel.SUBOPTIMAL
        elif tricks_cost == 1:
            return PlayCorrectnessLevel.GOOD
        elif tricks_cost == 2:
            return PlayCorrectnessLevel.SUBOPTIMAL
        else:  # 3+ tricks cost
            return PlayCorrectnessLevel.BLUNDER

    def _calculate_score(self, correctness: PlayCorrectnessLevel, tricks_cost: int) -> float:
        """Calculate score on 0-10 scale"""
        if correctness == PlayCorrectnessLevel.OPTIMAL:
            return 10.0
        elif correctness == PlayCorrectnessLevel.GOOD:
            return 8.0  # 1 trick cost
        elif correctness == PlayCorrectnessLevel.SUBOPTIMAL:
            # Heuristic mode (tricks_cost = -1): give neutral score
            if tricks_cost < 0:
                return 6.0  # Unknown cost - give benefit of doubt
            return 5.0 - max(0, tricks_cost - 2)  # 2-3 tricks cost
        elif correctness == PlayCorrectnessLevel.BLUNDER:
            if tricks_cost < 0:
                return 3.0  # Unknown cost blunder
            return max(0.0, 3.0 - tricks_cost)  # 4+ tricks cost
        else:  # ILLEGAL
            return 0.0

    def _generate_reasoning(self, category: PlayCategory, correctness: PlayCorrectnessLevel,
                            user_card: Card, optimal_cards: List[Card],
                            tricks_cost: int, state: PlayState, position: str) -> str:
        """Generate explanation of why this play was good/bad"""
        user_str = f"{user_card.rank}{user_card.suit}"
        optimal_str = ', '.join([f"{c.rank}{c.suit}" for c in optimal_cards[:2]]) if optimal_cards else ""

        if correctness == PlayCorrectnessLevel.OPTIMAL:
            return self._explain_optimal_play(user_str, category, state, position)

        # For non-optimal plays, explain WHY the optimal is better
        # Only add context_reason if we have something meaningful to say
        context_reason = self._explain_why_better(
            user_card, optimal_cards, category, state, position, tricks_cost
        )
        suffix = f" {context_reason}" if context_reason else ""

        if correctness == PlayCorrectnessLevel.GOOD:
            return f"{user_str} works, but {optimal_str} is slightly better.{suffix}"
        elif correctness == PlayCorrectnessLevel.SUBOPTIMAL:
            if tricks_cost > 0:
                return f"{optimal_str} saves {tricks_cost} trick{'s' if tricks_cost > 1 else ''}.{suffix}"
            else:
                return f"{optimal_str} is likely better.{suffix}"
        else:  # BLUNDER
            if tricks_cost > 0:
                return f"Critical mistake costing {tricks_cost} tricks. {optimal_str} is better.{suffix}"
            else:
                return f"This play is likely costly. {optimal_str} is better.{suffix}"

    def _explain_optimal_play(self, user_str: str, category: PlayCategory,
                               state: PlayState, position: str) -> str:
        """Generate explanation for an optimal play"""
        if category == PlayCategory.OPENING_LEAD:
            return f"{user_str} is the best opening lead."
        elif category == PlayCategory.FOLLOWING_SUIT:
            trick_pos = len(state.current_trick) if state and state.current_trick else 0
            if trick_pos == 1:
                # Check what card was played to provide accurate feedback
                user_rank_val = self._rank_value(user_str[0]) if user_str else 0
                led_card = state.current_trick[0][0] if state.current_trick else None
                led_rank_val = self._rank_value(led_card.rank) if led_card else 0

                # Honor cards are J (11), Q (12), K (13), A (14)
                is_honor = user_rank_val >= 11

                # Check if covering an opponent's honor (e.g., Ace over King)
                is_covering = is_honor and led_rank_val >= 11 and user_rank_val > led_rank_val

                if is_covering:
                    return f"Playing {user_str} to cover the opponent's honor is correct."
                elif is_honor:
                    # User played a high card in second seat - might be correct for other reasons
                    return f"Playing {user_str} is the correct play here."
                else:
                    # User played a low card - "second hand low" applies
                    return f"Playing {user_str} second hand low is correct."
            elif trick_pos == 2:
                # Check context before saying "third hand high"
                led_card = state.current_trick[0][0] if state.current_trick else None
                second_card = state.current_trick[1][0] if len(state.current_trick) >= 2 else None

                # Check if trick is already lost to second hand
                if led_card and second_card and second_card.suit == led_card.suit:
                    user_rank_val = self._rank_value(user_str[0]) if user_str else 0
                    second_val = self._rank_value(second_card.rank)
                    if second_val > user_rank_val:
                        # User played low because trick was already lost
                        return f"Playing {user_str} is correct - conserving honors when the trick is lost."

                return f"Playing {user_str} third hand is correct."
            else:
                return f"Playing {user_str} is correct."
        elif category == PlayCategory.TRUMPING:
            return f"Ruffing with {user_str} wins this trick optimally."
        elif category == PlayCategory.DISCARDING:
            return f"{user_str} is the right discard - it preserves your winners."
        else:
            return f"{user_str} is the correct play."

    def _analyze_trick_context(self, state: PlayState) -> dict:
        """
        Analyze the current trick to determine context for feedback.

        Returns dict with:
            - trick_pos: 0=lead, 1=second, 2=third, 3=fourth
            - led_card: Card that was led (or None)
            - led_suit: Suit that was led (or None)
            - current_winner_value: Highest card value currently winning
            - current_winner_pos: Position of current winner
            - can_beat_current: Whether optimal card can beat current winner
            - trick_already_lost: Whether opponent has unbeatable card
        """
        context = {
            'trick_pos': 0,
            'led_card': None,
            'led_suit': None,
            'current_winner_value': 0,
            'current_winner_pos': None,
            'second_hand_card': None,
        }

        if not state.current_trick:
            return context

        context['trick_pos'] = len(state.current_trick)
        context['led_card'] = state.current_trick[0][0]
        context['led_suit'] = context['led_card'].suit

        # Find current winner (highest card in led suit)
        for played_card, played_pos in state.current_trick:
            if played_card.suit == context['led_suit']:
                card_value = self._rank_value(played_card.rank)
                if card_value > context['current_winner_value']:
                    context['current_winner_value'] = card_value
                    context['current_winner_pos'] = played_pos

        # Track second hand's card for third hand analysis
        if len(state.current_trick) >= 2:
            context['second_hand_card'] = state.current_trick[1][0]

        return context

    def _explain_why_better(self, user_card: Card, optimal_cards: List[Card],
                            category: PlayCategory, state: PlayState,
                            position: str, tricks_cost: int) -> str:
        """
        Generate contextual explanation of WHY the optimal play is better.

        Uses trick context to provide accurate, situation-specific feedback
        rather than generic bridge principles that may not apply.
        """
        if not optimal_cards or not state:
            return ""

        opt_card = optimal_cards[0]
        user_rank = user_card.rank
        opt_rank = opt_card.rank
        user_suit = user_card.suit
        opt_suit = opt_card.suit

        opt_value = self._rank_value(opt_rank)
        user_value = self._rank_value(user_rank)

        # Get hand and trump info for deeper analysis
        hand = state.hands.get(position)
        trump_suit = state.contract.trump_suit if state.contract else None

        # Get trick context
        ctx = self._analyze_trick_context(state)
        trick_pos = ctx['trick_pos']

        # === OPENING LEAD ===
        if category == PlayCategory.OPENING_LEAD:
            # Check for split honors (AQ, KJ) - wait for them to lead to you
            if hand and self._has_tenace(hand, user_suit) and not self._has_tenace(hand, opt_suit):
                return "Don't lead away from split honors (like AQ) - wait for them to lead to you"

            # Don't lead trump
            if user_suit == trump_suit and opt_suit != trump_suit:
                return "Don't lead trump - it does declarer's work for them"

            if opt_suit != user_suit:
                return f"Leading {opt_suit} is safer"
            if opt_rank in ['4', '5', '6', '7']:
                return "4th best helps partner count the suit and sets up your long cards"
            if opt_rank in ['K', 'Q', 'J', 'T']:
                return "Top of sequence forces out higher honors to make your lower cards winners"
            if opt_rank == 'A':
                return "Lead the Ace to see dummy and keep control"

            # Top of nothing - signal no honors
            if hand:
                suit_cards = [c for c in hand.cards if c.suit == opt_suit]
                has_honors = any(c.rank in ['A', 'K', 'Q', 'J'] for c in suit_cards)
                if not has_honors and opt_value == max(self._rank_value(c.rank) for c in suit_cards):
                    return "Lead high from a weak suit to tell partner you have no honors"
            return ""

        # === MID-HAND LEAD (leading but not opening) ===
        if trick_pos == 0 and category != PlayCategory.OPENING_LEAD:
            # Cash winners
            if opt_rank == 'A':
                return "Cash your Ace while you have the lead"
            if opt_rank in ['K', 'Q', 'J', 'T'] and hand:
                if self._is_top_of_sequence(opt_card, hand, opt_suit):
                    return "Lead top of sequence to force out higher honors"
            # Avoid split honors
            if hand and self._has_tenace(hand, user_suit) and not self._has_tenace(hand, opt_suit):
                return f"Don't lead from {user_suit} - wait for them to lead to you"
            return ""

        # === SECOND HAND (trick_pos == 1) ===
        if trick_pos == 1 and category == PlayCategory.FOLLOWING_SUIT:
            if user_rank in ['A', 'K', 'Q', 'J', 'T'] and opt_rank not in ['A', 'K', 'Q', 'J', 'T']:
                return "Second hand low - don't waste an honor that declarer can easily capture"
            if opt_value < ctx['current_winner_value']:
                return "Play low to let partner win in third seat"
            return ""

        # === THIRD HAND (trick_pos == 2) ===
        if trick_pos == 2 and category == PlayCategory.FOLLOWING_SUIT:
            second_card = ctx['second_hand_card']
            led_card = ctx['led_card']

            # Check if trick is already lost to second hand
            trick_lost = False
            if second_card and led_card and second_card.suit == led_card.suit:
                second_value = self._rank_value(second_card.rank)
                if second_value >= opt_value:
                    trick_lost = True

            if trick_lost:
                if opt_value < user_value:
                    return "Don't waste an honor on a trick you cannot win"
                return ""

            # Trick is still winnable
            if user_rank in ['2', '3', '4', '5', '6'] and opt_rank in ['A', 'K', 'Q', 'J', 'T']:
                return "Play high third hand - force declarer to spend a high card or win the trick"
            if opt_value > user_value:
                return "Play higher to win or force out declarer's honors"

            # Unblock situation - let partner keep the lead
            if led_card and led_card.rank in ['K', 'Q', 'J'] and opt_rank not in ['A', 'K', 'Q', 'J']:
                return "Play low - let partner hold the lead"
            return ""

        # === FOURTH HAND (trick_pos == 3) ===
        if trick_pos == 3 and category == PlayCategory.FOLLOWING_SUIT:
            can_win = opt_value > ctx['current_winner_value']

            if can_win:
                if opt_value < user_value:
                    return "Win with your cheapest card"
                return ""
            else:
                if opt_value < user_value:
                    return "Play low - you can't win this trick"
                return ""

        # === TRUMPING ===
        if category == PlayCategory.TRUMPING:
            if opt_value < user_value:
                return "Trump with a small card - save your high trumps for later"
            if opt_value > user_value:
                return "Trump high enough to beat any overruff"
            return ""

        # === DISCARDING ===
        if category == PlayCategory.DISCARDING:
            if hand:
                user_suit_cards = [c for c in hand.cards if c.suit == user_suit]
                opt_suit_cards = [c for c in hand.cards if c.suit == opt_suit]

                # Don't discard lone high cards (stoppers)
                if len(user_suit_cards) == 1 and user_value >= 13:  # K or A
                    return f"Keep the high card that protects your {user_suit}"

                # Don't discard trump
                if user_suit == trump_suit and opt_suit != trump_suit:
                    return "Keep your trumps"

                # Discard from length
                if len(opt_suit_cards) > len(user_suit_cards):
                    return f"Discard from {opt_suit} where you can spare the small cards"

            if opt_suit != user_suit:
                return f"Discard from {opt_suit} to protect your {user_suit}"
            if opt_value < user_value:
                return "Discard your lowest card"
            return ""

        return ""

    def _has_tenace(self, hand, suit: str) -> bool:
        """Check if hand has a tenace (AQ, KJ, etc.) in the given suit."""
        suit_cards = [c for c in hand.cards if c.suit == suit]
        ranks = set(c.rank for c in suit_cards)

        # Common tenaces: AQ, KJ, AJ, QT
        tenaces = [{'A', 'Q'}, {'K', 'J'}, {'A', 'J'}, {'Q', 'T'}]
        for tenace in tenaces:
            if tenace.issubset(ranks):
                # Check that the middle card is missing
                if tenace == {'A', 'Q'} and 'K' not in ranks:
                    return True
                if tenace == {'K', 'J'} and 'Q' not in ranks:
                    return True
                if tenace == {'A', 'J'} and 'K' not in ranks and 'Q' not in ranks:
                    return True
                if tenace == {'Q', 'T'} and 'K' not in ranks and 'J' not in ranks:
                    return True
        return False

    def _is_top_of_sequence(self, card: Card, hand, suit: str) -> bool:
        """Check if card is top of a sequence (KQJ, QJT, etc.)."""
        suit_cards = [c for c in hand.cards if c.suit == suit]
        if len(suit_cards) < 2:
            return False

        ranks = sorted([self._rank_value(c.rank) for c in suit_cards], reverse=True)
        card_value = self._rank_value(card.rank)

        # Must be highest
        if card_value != ranks[0]:
            return False

        # Check for at least 2 consecutive cards
        if len(ranks) >= 2 and ranks[0] - ranks[1] == 1:
            return True
        return False

    def _rank_value(self, rank: str) -> int:
        """Convert rank to numeric value for comparison"""
        rank_order = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                      '9': 9, 'T': 10, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return rank_order.get(rank, 0)

    def _generate_hint(self, category: PlayCategory, correctness: PlayCorrectnessLevel,
                       user_card: Card, optimal_cards: List[Card],
                       state: PlayState, position: str) -> str:
        """Generate actionable advice for improvement based on trick context."""
        if correctness == PlayCorrectnessLevel.OPTIMAL:
            return ""  # No hint needed for optimal play

        # Get context for smarter hints
        ctx = self._analyze_trick_context(state)
        opt_value = self._rank_value(optimal_cards[0].rank) if optimal_cards else 0

        # === OPENING LEAD ===
        if category == PlayCategory.OPENING_LEAD:
            return "Lead from length (4th best) or top of a sequence."

        # === FOLLOWING SUIT ===
        if category == PlayCategory.FOLLOWING_SUIT:
            trick_pos = ctx['trick_pos']

            if trick_pos == 1:  # Second hand
                return "Second hand low - save honors unless you can win cheaply."

            if trick_pos == 2:  # Third hand
                # Check if trick is lost
                second_card = ctx['second_hand_card']
                led_card = ctx['led_card']
                if second_card and led_card and second_card.suit == led_card.suit:
                    second_value = self._rank_value(second_card.rank)
                    if second_value >= opt_value:
                        return "When you can't beat the current winner, save your honors."
                return "Third hand high - win the trick or force out honors."

            if trick_pos == 3:  # Fourth hand
                can_win = opt_value > ctx['current_winner_value']
                if can_win:
                    return "Win with your cheapest winner."
                return "Play low when you can't win."

        # === TRUMPING ===
        if category == PlayCategory.TRUMPING:
            return "Ruff with your lowest trump that wins."

        # === DISCARDING ===
        if category == PlayCategory.DISCARDING:
            return "Discard from weak suits to protect your winners."

        # === SLUFFING ===
        if category == PlayCategory.SLUFFING:
            return "Consider whether ruffing or discarding gains more tricks."

        return ""

    def _extract_key_concept(self, category: PlayCategory, state: PlayState = None) -> str:
        """Determine what bridge concept this play tests"""
        concept_map = {
            PlayCategory.OPENING_LEAD: "Opening leads",
            PlayCategory.FOLLOWING_SUIT: "Card play in suit",
            PlayCategory.TRUMPING: "Trump management",
            PlayCategory.OVERRUFFING: "Trump management",
            PlayCategory.DISCARDING: "Discard signals",
            PlayCategory.SLUFFING: "Sluff vs ruff decision",
            PlayCategory.FINESSING: "Finessing techniques",
            PlayCategory.CASHING: "Cashing winners",
            PlayCategory.HOLD_UP: "Hold-up plays",
            PlayCategory.DUCKING: "Ducking technique"
        }
        return concept_map.get(category, "Card play")

    def _get_key_concept(self, category: PlayCategory) -> str:
        """Alias for tests - get key concept for a category"""
        return self._extract_key_concept(category)

    def _get_correctness_and_score(self, tricks_cost: int) -> Tuple[PlayCorrectnessLevel, float]:
        """
        Get correctness level and score from tricks cost.

        This is the main scoring function used by tests.

        Args:
            tricks_cost: Number of tricks lost compared to optimal play

        Returns:
            Tuple of (PlayCorrectnessLevel, score)
        """
        if tricks_cost == 0:
            return PlayCorrectnessLevel.OPTIMAL, 10.0
        elif tricks_cost == 1:
            return PlayCorrectnessLevel.GOOD, 7.5
        elif tricks_cost == 2:
            return PlayCorrectnessLevel.SUBOPTIMAL, 5.0
        else:  # 3+ tricks cost
            # Score decreases by 1 for each additional trick lost
            score = max(0.0, 3.0 - (tricks_cost - 3))
            return PlayCorrectnessLevel.BLUNDER, score

    def _generate_feedback_text(self, play_state, user_card: Card, position: str,
                                optimal_cards: List[str], tricks_cost: int,
                                play_category: PlayCategory) -> Tuple[str, str]:
        """
        Generate reasoning and hint text for feedback.

        Args:
            play_state: Current play state (can be None for tests)
            user_card: Card user played
            position: Position making play
            optimal_cards: List of optimal card strings
            tricks_cost: Tricks lost compared to optimal
            play_category: Type of play

        Returns:
            Tuple of (reasoning, helpful_hint)
        """
        user_str = f"{user_card.rank}{user_card.suit}"

        if tricks_cost == 0:
            reasoning = f"Playing {user_str} is correct. Good card play."
            hint = ""
        elif tricks_cost == 1:
            optimal_str = ', '.join(optimal_cards[:2]) if optimal_cards else "unknown"
            reasoning = f"{user_str} is reasonable, but {optimal_str} is slightly better."
            hint = "Consider the optimal alternatives for future hands."
        elif tricks_cost == 2:
            optimal_str = ', '.join(optimal_cards[:2]) if optimal_cards else "unknown"
            reasoning = f"{optimal_str} would save {tricks_cost} tricks."
            hint = self._get_category_hint(play_category)
        else:  # Blunder
            optimal_str = ', '.join(optimal_cards[:2]) if optimal_cards else "unknown"
            reasoning = f"This mistake cost {tricks_cost} tricks. {optimal_str} was better."
            hint = self._get_category_hint(play_category)

        return reasoning, hint

    def _get_category_hint(self, category: PlayCategory) -> str:
        """Get a hint based on play category"""
        hints = {
            PlayCategory.OPENING_LEAD: "Consider leading from length (4th best) or top of sequence.",
            PlayCategory.FOLLOWING_SUIT: "Review second hand low, third hand high principles.",
            PlayCategory.TRUMPING: "Ruff with lowest trump that wins.",
            PlayCategory.OVERRUFFING: "Consider whether overruffing is worthwhile.",
            PlayCategory.DISCARDING: "Discard from your longest weak suit.",
            PlayCategory.SLUFFING: "Weigh the pros and cons of ruffing vs discarding.",
            PlayCategory.FINESSING: "A finesse has a 50% chance of success.",
            PlayCategory.CASHING: "Cash winners in the right order to avoid blocking.",
            PlayCategory.HOLD_UP: "Hold up to cut defender communications.",
            PlayCategory.DUCKING: "Ducking can preserve entries."
        }
        return hints.get(category, "Count your winners and plan the play.")

    def _assess_difficulty(self, category: PlayCategory, state: PlayState) -> str:
        """Assess difficulty level of this decision"""
        trick_num = len(state.trick_history) + 1

        # Late tricks are harder (more counting required)
        if trick_num >= 10:
            return "expert"
        elif trick_num >= 7:
            return "advanced"
        elif category in [PlayCategory.OVERRUFFING, PlayCategory.SLUFFING]:
            return "advanced"
        elif category == PlayCategory.OPENING_LEAD:
            return "intermediate"
        else:
            return "beginner"

    def _is_declarer_side(self, position: str, contract: Optional[Contract]) -> bool:
        """Check if position is on declarer's side"""
        if not contract:
            return False

        declarer = contract.declarer
        partnerships = {
            'N': ['N', 'S'],
            'S': ['N', 'S'],
            'E': ['E', 'W'],
            'W': ['E', 'W']
        }
        return position in partnerships.get(declarer, [])

    def _create_illegal_feedback(self, user_card: Card, position: str,
                                  state: PlayState) -> PlayFeedback:
        """Create feedback for an illegal play"""
        user_str = f"{user_card.rank}{user_card.suit}"
        led_suit = state.current_trick[0][0].suit if state.current_trick else None

        hint = ""
        if led_suit:
            hint = f"You must follow suit ({led_suit}) if possible."

        return PlayFeedback(
            trick_number=len(state.trick_history) + 1,
            position=position,
            user_card=user_str,
            contract=str(state.contract) if state.contract else "",
            is_declarer_side=self._is_declarer_side(position, state.contract),
            led_suit=led_suit,
            correctness=PlayCorrectnessLevel.ILLEGAL,
            score=0.0,
            optimal_cards=[],
            tricks_cost=0,
            tricks_with_user_card=0,
            tricks_with_optimal=0,
            reasoning=f"{user_str} is not a legal play.",
            play_category=PlayCategory.FOLLOWING_SUIT,
            helpful_hint=hint,
            key_concept="Following suit rules",
            difficulty="beginner"
        )

    def _store_feedback(self, user_id: int, feedback: PlayFeedback,
                        session_id: Optional[str], hand_number: Optional[int] = None):
        """Store feedback in play_decisions table"""
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO play_decisions (
                    user_id, session_id, hand_number, position, trick_number,
                    user_card, optimal_card, score, rating,
                    tricks_cost, tricks_with_user_card, tricks_with_optimal,
                    contract, is_declarer_side, play_category,
                    key_concept, difficulty, feedback, helpful_hint,
                    analysis_source, signal_reason, signal_heuristic,
                    signal_context, is_signal_optimal, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                session_id,
                hand_number,
                feedback.position,
                feedback.trick_number,
                feedback.user_card,
                feedback.optimal_cards[0] if feedback.optimal_cards else None,
                feedback.score,
                feedback.correctness.value,
                feedback.tricks_cost,
                feedback.tricks_with_user_card,
                feedback.tricks_with_optimal,
                feedback.contract,
                1 if feedback.is_declarer_side else 0,
                feedback.play_category.value,
                feedback.key_concept,
                feedback.difficulty,
                feedback.reasoning,
                feedback.helpful_hint,
                feedback.analysis_source,
                feedback.signal_reason,
                feedback.signal_heuristic,
                feedback.signal_context,
                1 if feedback.is_signal_optimal else 0
            ))

            conn.commit()
        except Exception as e:
            print(f"Error storing play feedback: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
        finally:
            conn.close()


# Singleton instance
_feedback_generator = None


def get_play_feedback_generator(use_dds: bool = True) -> PlayFeedbackGenerator:
    """
    Get singleton feedback generator instance.

    Args:
        use_dds: If True, use DDS when available (Linux production).
                 If False, always use Minimax fallback.

    Returns:
        PlayFeedbackGenerator instance
    """
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = PlayFeedbackGenerator(use_dds=use_dds)
    return _feedback_generator


# Self-test
if __name__ == '__main__':
    print("Play Feedback Generator - Self Test")
    print("=" * 50)

    # Create generator
    generator = get_play_feedback_generator(use_dds=True)
    print(f"DDS available: {generator.dds_available}")
    print(f"Platform: {platform.system()}")

    print("\nPlay Feedback Generator initialized successfully!")
