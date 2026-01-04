"""
Decay Curve Generator - Track trick potential throughout play.

The decay curve shows declarer's maximum trick potential at each card played.
A flat curve means optimal play; drops indicate mistakes.

Physics:
- Serial Mutation: Cards are consumed in exact play order
- Normalization: All values from Declarer's perspective
- Monotonicity: Potential can only decrease (or stay flat) with optimal play
- Defensive Leaks: Potential increases when defense makes mistakes

Implementation Notes:
- Uses DDS solve_board() for each state (52 calls per hand)
- Runs asynchronously to avoid blocking game flow
- Results stored in decay_curve column as JSON array
- Major errors extracted and stored in major_errors column
"""

import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Try to import DDS
try:
    from endplay.types import Deal, Player as EndplayPlayer, Denom, Card as EndplayCard
    from endplay.dds import solve_board
    DDS_AVAILABLE = True
except ImportError:
    DDS_AVAILABLE = False
    Deal = None
    EndplayPlayer = None
    Denom = None
    EndplayCard = None
    solve_board = None


# Position utilities
POSITION_ORDER = ['N', 'E', 'S', 'W']
PARTNERS = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
NEXT_PLAYER = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}


@dataclass
class MajorError:
    """A significant mistake during play."""
    card_index: int      # Index in play history (0-51)
    trick_number: int    # Which trick (1-13)
    card: str            # Card played (e.g., 'SQ')
    position: str        # Who played it
    loss: int            # Tricks lost (always positive)
    error_type: str      # 'declarer_error' or 'defensive_gift'
    potential_before: int
    potential_after: int
    optimal_card: Optional[str] = None
    reasoning: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DecayCurveResult:
    """Complete decay curve analysis result."""
    curve: List[int]                    # Trick potential at each card
    major_errors: List[MajorError]      # Significant mistakes
    initial_potential: int              # Starting DD potential
    final_potential: int                # Ending potential
    total_tricks_lost: int              # Sum of declarer errors
    defensive_gifts: int                # Tricks given by defense
    is_valid: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'curve': self.curve,
            'major_errors': [e.to_dict() for e in self.major_errors],
            'initial_potential': self.initial_potential,
            'final_potential': self.final_potential,
            'total_tricks_lost': self.total_tricks_lost,
            'defensive_gifts': self.defensive_gifts,
            'is_valid': self.is_valid,
            'error_message': self.error_message,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class StateReconstructor:
    """
    Reconstructs game state by consuming cards from play history.

    This is the "physics engine" for decay curves - it must perfectly
    track the 52-card state transitions.
    """

    def __init__(self, hands: Dict[str, List[str]], declarer: str):
        """
        Initialize with starting hands and declarer position.

        Args:
            hands: Dict mapping position to list of card strings
                   e.g., {'N': ['SA', 'SK', ...], 'E': [...], ...}
            declarer: Position of declarer ('N', 'E', 'S', 'W')
        """
        # Deep copy hands
        self.current_hands = {pos: list(cards) for pos, cards in hands.items()}
        self.declarer = declarer
        self.declarer_side = {declarer, PARTNERS[declarer]}
        self.cards_played = 0

    def get_total_cards_remaining(self) -> int:
        """Get total cards remaining across all hands."""
        return sum(len(h) for h in self.current_hands.values())

    def get_tricks_remaining(self) -> int:
        """Get number of complete tricks remaining."""
        return self.get_total_cards_remaining() // 4

    def play_card(self, card_str: str, position: str) -> bool:
        """
        Remove a card from a hand.

        Args:
            card_str: Card string like 'SA' (Ace of Spades)
            position: Position playing the card

        Returns:
            True if card was found and removed, False otherwise
        """
        hand = self.current_hands.get(position, [])
        if card_str in hand:
            hand.remove(card_str)
            self.cards_played += 1
            return True
        return False

    def is_declarer_side(self, position: str) -> bool:
        """Check if position is on declarer's side."""
        return position in self.declarer_side

    def normalize_tricks(self, dds_result: int, leader: str) -> int:
        """
        Normalize DDS result to declarer's perspective.

        Args:
            dds_result: Max tricks DDS says leader's side can take
            leader: Position currently on lead

        Returns:
            Max tricks declarer's side can take
        """
        tricks_remaining = self.get_tricks_remaining()

        if self.is_declarer_side(leader):
            # DDS result is already from declarer's perspective
            return dds_result
        else:
            # DDS result is from defense's perspective
            # Declarer's potential = Total tricks - Defense's potential
            return tricks_remaining - dds_result

    def get_pbn_string(self) -> str:
        """
        Build PBN deal string from current hands.

        Format: "N:AKQJ.T98.765.432 EJT9.AKQ.J98.765 ..."
        """
        parts = []
        for pos in POSITION_ORDER:
            hand = self.current_hands.get(pos, [])
            # Group cards by suit
            suits = {'S': [], 'H': [], 'D': [], 'C': []}
            for card in hand:
                if len(card) >= 2:
                    suit = card[0]
                    rank = card[1:]
                    if suit in suits:
                        suits[suit].append(rank)

            # Build suit string
            suit_strs = []
            for suit in ['S', 'H', 'D', 'C']:
                suit_strs.append(''.join(suits[suit]))

            parts.append('.'.join(suit_strs))

        return f"N:{' '.join(parts)}"


class DecayCurveGenerator:
    """
    Generates decay curves from play history using DDS.

    The decay curve tracks declarer's trick potential at each card played,
    normalized to always show declarer's perspective.
    """

    # Minimum trick loss to flag as major error
    ERROR_THRESHOLD = 1

    def __init__(self):
        """Initialize the generator."""
        self.stats = {
            'curves_generated': 0,
            'dds_calls': 0,
            'errors': 0,
        }

    @property
    def is_available(self) -> bool:
        """Check if DDS is available."""
        return DDS_AVAILABLE

    def generate(
        self,
        hands: Dict[str, List[str]],
        play_history: List[Dict],
        declarer: str,
        trump_suit: str,
        skip_interval: int = 1
    ) -> DecayCurveResult:
        """
        Generate decay curve for a hand.

        Args:
            hands: Initial hands as {position: [card_strings]}
            play_history: List of {'card': 'SA', 'position': 'W'}
            declarer: Declarer's position
            trump_suit: Trump suit ('S', 'H', 'D', 'C', 'NT')
            skip_interval: Query DDS every N cards (1=all, 4=every trick)

        Returns:
            DecayCurveResult with curve and detected errors
        """
        if not DDS_AVAILABLE:
            return DecayCurveResult(
                curve=[],
                major_errors=[],
                initial_potential=0,
                final_potential=0,
                total_tricks_lost=0,
                defensive_gifts=0,
                is_valid=False,
                error_message="DDS not available on this platform"
            )

        if not play_history:
            return DecayCurveResult(
                curve=[],
                major_errors=[],
                initial_potential=0,
                final_potential=0,
                total_tricks_lost=0,
                defensive_gifts=0,
            )

        try:
            reconstructor = StateReconstructor(hands, declarer)
            decay_points = []
            trump_denom = self._convert_trump(trump_suit)

            for i, play in enumerate(play_history):
                card = play['card']
                position = play['position']

                # Optionally skip some positions for performance
                if i % skip_interval != 0:
                    # Interpolate or skip
                    if decay_points:
                        decay_points.append(decay_points[-1])
                    else:
                        decay_points.append(0)
                    reconstructor.play_card(card, position)
                    continue

                # Query DDS BEFORE removing the card
                try:
                    dds_result = self._query_dds(
                        reconstructor,
                        position,
                        trump_denom
                    )
                    self.stats['dds_calls'] += 1

                    # Normalize to declarer's perspective
                    normalized = reconstructor.normalize_tricks(dds_result, position)
                    decay_points.append(normalized)
                except Exception as e:
                    logger.warning(f"DDS query failed at card {i}: {e}")
                    # Use last known value
                    if decay_points:
                        decay_points.append(decay_points[-1])
                    else:
                        decay_points.append(0)

                # Mutate state: remove the played card
                success = reconstructor.play_card(card, position)
                if not success:
                    logger.warning(f"Card {card} not found in {position}'s hand at play {i}")

            # Detect errors from the curve
            major_errors = self._detect_errors(
                decay_points,
                play_history,
                declarer
            )

            # Calculate summary stats
            initial = decay_points[0] if decay_points else 0
            final = decay_points[-1] if decay_points else 0
            total_lost = sum(e.loss for e in major_errors if e.error_type == 'declarer_error')
            gifts = sum(e.loss for e in major_errors if e.error_type == 'defensive_gift')

            self.stats['curves_generated'] += 1

            return DecayCurveResult(
                curve=decay_points,
                major_errors=major_errors,
                initial_potential=initial,
                final_potential=final,
                total_tricks_lost=total_lost,
                defensive_gifts=gifts,
            )

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Decay curve generation failed: {e}")
            return DecayCurveResult(
                curve=[],
                major_errors=[],
                initial_potential=0,
                final_potential=0,
                total_tricks_lost=0,
                defensive_gifts=0,
                is_valid=False,
                error_message=str(e)
            )

    def _query_dds(
        self,
        reconstructor: StateReconstructor,
        leader: str,
        trump_denom: Any
    ) -> int:
        """
        Query DDS for max tricks from current position.

        Args:
            reconstructor: Current state
            leader: Position on lead
            trump_denom: Trump denomination for endplay

        Returns:
            Max tricks the leader's side can take
        """
        # Build PBN and create Deal
        pbn = reconstructor.get_pbn_string()
        deal = Deal(pbn)
        deal.trump = trump_denom
        deal.first = self._convert_position(leader)

        # solve_board returns optimal plays with trick counts
        solved = solve_board(deal)

        # Get the max tricks from the solution
        if solved:
            # Each item is (card, tricks) - tricks is for the side on lead
            max_tricks = max(tricks for card, tricks in solved)
            return max_tricks

        return 0

    def _detect_errors(
        self,
        curve: List[int],
        play_history: List[Dict],
        declarer: str
    ) -> List[MajorError]:
        """
        Detect major errors from the decay curve.

        An error occurs when potential drops significantly.
        """
        declarer_side = {declarer, PARTNERS[declarer]}
        errors = []

        for i in range(1, len(curve)):
            delta = curve[i] - curve[i-1]
            play = play_history[i]
            position = play['position']
            trick_number = (i // 4) + 1

            if delta < -self.ERROR_THRESHOLD:
                # Potential dropped - determine whose error
                if position in declarer_side:
                    error_type = 'declarer_error'
                else:
                    # Defense was on lead but declarer lost tricks?
                    # This is unusual - might be a defensive gift that
                    # the declarer failed to capitalize on
                    error_type = 'declarer_error'

                errors.append(MajorError(
                    card_index=i,
                    trick_number=trick_number,
                    card=play['card'],
                    position=position,
                    loss=abs(delta),
                    error_type=error_type,
                    potential_before=curve[i-1],
                    potential_after=curve[i],
                ))

            elif delta > 0:
                # Potential increased - defense leaked
                if position not in declarer_side:
                    errors.append(MajorError(
                        card_index=i,
                        trick_number=trick_number,
                        card=play['card'],
                        position=position,
                        loss=delta,  # Actually a gain for declarer
                        error_type='defensive_gift',
                        potential_before=curve[i-1],
                        potential_after=curve[i],
                    ))

        return errors

    def _convert_trump(self, trump_suit: str) -> Any:
        """Convert trump suit string to endplay Denom."""
        if not DDS_AVAILABLE:
            return None

        mapping = {
            'S': Denom.spades,
            'H': Denom.hearts,
            'D': Denom.diamonds,
            'C': Denom.clubs,
            'NT': Denom.nt,
            'N': Denom.nt,
        }
        return mapping.get(trump_suit.upper(), Denom.nt)

    def _convert_position(self, position: str) -> Any:
        """Convert position string to endplay Player."""
        if not DDS_AVAILABLE:
            return None

        mapping = {
            'N': EndplayPlayer.north,
            'E': EndplayPlayer.east,
            'S': EndplayPlayer.south,
            'W': EndplayPlayer.west,
        }
        return mapping.get(position.upper())


# Singleton instance
_decay_generator: Optional[DecayCurveGenerator] = None


def get_decay_generator() -> DecayCurveGenerator:
    """Get singleton decay curve generator."""
    global _decay_generator
    if _decay_generator is None:
        _decay_generator = DecayCurveGenerator()
    return _decay_generator
