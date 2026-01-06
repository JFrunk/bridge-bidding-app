"""
Decay Curve Generator - Track trick potential throughout play.

The decay curve shows NS (user) maximum trick potential at each card played.
A flat curve means optimal play; drops indicate mistakes.

Physics:
- Serial Mutation: Cards are consumed in exact play order
- Normalization: All values from NS (user) perspective - NOT declarer
- Monotonicity: Potential can only decrease (or stay flat) with optimal play
- Defensive Leaks: Potential increases when NS defense makes mistakes

Implementation Notes:
- Uses DDS solve_board() for each state (52 calls per hand)
- Runs asynchronously to avoid blocking game flow
- Results stored in decay_curve column as JSON array
- Major errors extracted and stored in major_errors column
- Trick winners tracked for "locked-in tricks" visualization
"""

import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict

# Import seat utilities - single source of truth for position calculations
from utils.seats import SEATS, PARTNERS, NEXT_PLAYER, NS_SIDE, EW_SIDE, partner

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


# Position utilities - imported from utils.seats
# Using SEATS as POSITION_ORDER for backward compatibility
POSITION_ORDER = SEATS


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
    curve: List[int]                    # NS trick potential at each card
    major_errors: List[MajorError]      # Significant mistakes
    initial_potential: int              # Starting DD potential for NS
    final_potential: int                # Ending potential for NS
    total_tricks_lost: int              # Sum of NS errors
    defensive_gifts: int                # Tricks given by EW defense
    trick_winners: List[str]            # Winner of each trick ('N', 'E', 'S', 'W')
    ns_tricks_cumulative: List[int]     # Cumulative NS tricks at each card (0-52)
    dd_optimal_ns: int                  # DD optimal tricks for NS
    actual_tricks_ns: int               # Actual tricks NS took
    ns_is_declarer: bool                # Whether NS was declaring side
    required_tricks: int                # Required to make (declarer) or set (defense)
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
            'trick_winners': self.trick_winners,
            'ns_tricks_cumulative': self.ns_tricks_cumulative,
            'dd_optimal_ns': self.dd_optimal_ns,
            'actual_tricks_ns': self.actual_tricks_ns,
            'ns_is_declarer': self.ns_is_declarer,
            'required_tricks': self.required_tricks,
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

    Always normalizes to NS (user) perspective, not declarer.
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
        self.ns_is_declarer = declarer in NS_SIDE
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

    def is_ns_side(self, position: str) -> bool:
        """Check if position is on NS side (user's side)."""
        return position in NS_SIDE

    def is_declarer_side(self, position: str) -> bool:
        """Check if position is on declarer's side."""
        return position in self.declarer_side

    def normalize_tricks_to_ns(self, dds_result: int, leader: str) -> int:
        """
        Normalize DDS result to NS (user) perspective.

        Args:
            dds_result: Max tricks DDS says leader's side can take
            leader: Position currently on lead

        Returns:
            Max tricks NS can take from this position
        """
        tricks_remaining = self.get_tricks_remaining()

        if self.is_ns_side(leader):
            # DDS result is already from NS perspective
            return dds_result
        else:
            # DDS result is from EW's perspective
            # NS's potential = Total tricks - EW's potential
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

    The decay curve tracks NS (user) trick potential at each card played,
    normalized to always show NS perspective regardless of who declared.
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
        contract_level: int = 0,
        skip_interval: int = 1
    ) -> DecayCurveResult:
        """
        Generate decay curve for a hand.

        Args:
            hands: Initial hands as {position: [card_strings]}
            play_history: List of {'card': 'SA', 'position': 'W'}
            declarer: Declarer's position
            trump_suit: Trump suit ('S', 'H', 'D', 'C', 'NT')
            contract_level: Contract level (1-7) for calculating required tricks
            skip_interval: Query DDS every N cards (1=all, 4=every trick)

        Returns:
            DecayCurveResult with curve and detected errors, all from NS perspective
        """
        # Calculate NS-specific values
        ns_is_declarer = declarer in NS_SIDE
        tricks_needed = contract_level + 6 if contract_level > 0 else 7

        # Required tricks: For NS declarer, need to make contract
        # For NS defender, need to set (14 - tricks_needed)
        if ns_is_declarer:
            required_tricks = tricks_needed
        else:
            required_tricks = 14 - tricks_needed

        # Default empty result for error cases
        def empty_result(error_msg: Optional[str] = None, is_valid: bool = True) -> DecayCurveResult:
            return DecayCurveResult(
                curve=[],
                major_errors=[],
                initial_potential=0,
                final_potential=0,
                total_tricks_lost=0,
                defensive_gifts=0,
                trick_winners=[],
                ns_tricks_cumulative=[],
                dd_optimal_ns=0,
                actual_tricks_ns=0,
                ns_is_declarer=ns_is_declarer,
                required_tricks=required_tricks,
                is_valid=is_valid,
                error_message=error_msg
            )

        if not DDS_AVAILABLE:
            return empty_result("DDS not available on this platform", is_valid=False)

        if not play_history:
            return empty_result()

        try:
            reconstructor = StateReconstructor(hands, declarer)
            decay_points = []
            trump_denom = self._convert_trump(trump_suit)

            # Track trick winners and cumulative NS tricks
            trick_winners = []
            ns_tricks_cumulative = []
            current_trick_cards = []
            current_trick_leader = None
            ns_tricks_count = 0

            for i, play in enumerate(play_history):
                card = play['card']
                position = play['position']

                # Track the leader of each trick (first card)
                if i % 4 == 0:
                    current_trick_leader = position
                    current_trick_cards = []

                current_trick_cards.append({'card': card, 'position': position})

                # Optionally skip some positions for performance
                if i % skip_interval != 0:
                    # Interpolate or skip
                    if decay_points:
                        decay_points.append(decay_points[-1])
                    else:
                        decay_points.append(0)
                    reconstructor.play_card(card, position)
                    ns_tricks_cumulative.append(ns_tricks_count)
                    continue

                # Query DDS BEFORE removing the card
                try:
                    dds_result = self._query_dds(
                        reconstructor,
                        position,
                        trump_denom
                    )
                    self.stats['dds_calls'] += 1

                    # Normalize to NS perspective (not declarer)
                    normalized = reconstructor.normalize_tricks_to_ns(dds_result, position)
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

                # Determine trick winner when trick is complete
                if (i + 1) % 4 == 0 and len(current_trick_cards) == 4:
                    winner = self._determine_trick_winner(
                        current_trick_cards,
                        current_trick_leader,
                        trump_suit
                    )
                    trick_winners.append(winner)
                    if winner in NS_SIDE:
                        ns_tricks_count += 1

                ns_tricks_cumulative.append(ns_tricks_count)

            # Detect errors from the curve (now from NS perspective)
            major_errors = self._detect_errors_ns(
                decay_points,
                play_history
            )

            # Calculate summary stats
            initial = decay_points[0] if decay_points else 0
            final = decay_points[-1] if decay_points else 0
            total_lost = sum(e.loss for e in major_errors if e.error_type == 'ns_error')
            gifts = sum(e.loss for e in major_errors if e.error_type == 'ew_gift')

            self.stats['curves_generated'] += 1

            return DecayCurveResult(
                curve=decay_points,
                major_errors=major_errors,
                initial_potential=initial,
                final_potential=final,
                total_tricks_lost=total_lost,
                defensive_gifts=gifts,
                trick_winners=trick_winners,
                ns_tricks_cumulative=ns_tricks_cumulative,
                dd_optimal_ns=initial,  # DD optimal is the initial potential
                actual_tricks_ns=ns_tricks_count,
                ns_is_declarer=ns_is_declarer,
                required_tricks=required_tricks,
            )

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Decay curve generation failed: {e}")
            return empty_result(str(e), is_valid=False)

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

    def _detect_errors_ns(
        self,
        curve: List[int],
        play_history: List[Dict]
    ) -> List[MajorError]:
        """
        Detect major errors from the decay curve, from NS perspective.

        An error occurs when NS potential drops (NS made a mistake)
        or when NS potential increases (EW made a mistake).
        """
        errors = []

        for i in range(1, len(curve)):
            delta = curve[i] - curve[i-1]
            play = play_history[i]
            position = play['position']
            trick_number = (i // 4) + 1

            if delta < -self.ERROR_THRESHOLD:
                # NS potential dropped - NS made an error
                # (regardless of who played the card)
                errors.append(MajorError(
                    card_index=i,
                    trick_number=trick_number,
                    card=play['card'],
                    position=position,
                    loss=abs(delta),
                    error_type='ns_error',
                    potential_before=curve[i-1],
                    potential_after=curve[i],
                ))

            elif delta > 0:
                # NS potential increased - EW gave away tricks
                errors.append(MajorError(
                    card_index=i,
                    trick_number=trick_number,
                    card=play['card'],
                    position=position,
                    loss=delta,  # Actually a gain for NS
                    error_type='ew_gift',
                    potential_before=curve[i-1],
                    potential_after=curve[i],
                ))

        return errors

    def _determine_trick_winner(
        self,
        trick_cards: List[Dict],
        leader: str,
        trump_suit: str
    ) -> str:
        """
        Determine the winner of a trick.

        Args:
            trick_cards: List of {'card': 'SA', 'position': 'N'} for 4 cards
            leader: Position who led to the trick
            trump_suit: Trump suit ('S', 'H', 'D', 'C', 'NT')

        Returns:
            Position of the winner ('N', 'E', 'S', 'W')
        """
        if len(trick_cards) != 4:
            return leader  # Incomplete trick, return leader

        # Card ranking (A=14, K=13, Q=12, J=11, T=10, etc.)
        rank_values = {
            'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
            '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2
        }

        # Get led suit
        led_card = trick_cards[0]['card']
        led_suit = led_card[0] if len(led_card) >= 2 else None

        winner_idx = 0
        winner_value = 0
        is_trump = False

        for idx, play in enumerate(trick_cards):
            card = play['card']
            if len(card) < 2:
                continue

            suit = card[0]
            rank = card[1:]
            value = rank_values.get(rank, 0)

            # Check if this card is trump
            card_is_trump = (suit == trump_suit and trump_suit not in ['NT', 'N'])

            # Determine if this card wins
            if card_is_trump and not is_trump:
                # Trump beats non-trump
                winner_idx = idx
                winner_value = value
                is_trump = True
            elif card_is_trump and is_trump:
                # Higher trump wins
                if value > winner_value:
                    winner_idx = idx
                    winner_value = value
            elif not card_is_trump and not is_trump:
                # Must follow suit to win
                if suit == led_suit and value > winner_value:
                    winner_idx = idx
                    winner_value = value

        return trick_cards[winner_idx]['position']

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
