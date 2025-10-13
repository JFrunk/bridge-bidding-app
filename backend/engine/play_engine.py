"""
PlayEngine - Core card play logic for bridge

Handles:
- Legal play validation (follow suit rules)
- Trick winner determination
- Scoring
- Game state management

This is the stable foundation that won't change when AI improves.
"""

from engine.hand import Hand, Card
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class GamePhase(Enum):
    """
    Explicit game phase enumeration for state machine.

    Flow: SETUP → DEALING → BIDDING → PLAY_STARTING → PLAY_IN_PROGRESS →
          PLAY_COMPLETE → SCORING → ROUND_COMPLETE
    """
    SETUP = "setup"                      # Initial state, no deal yet
    DEALING = "dealing"                  # Cards being dealt
    BIDDING = "bidding"                  # Auction in progress
    BIDDING_COMPLETE = "bidding_complete"  # Auction ended, contract determined
    PLAY_STARTING = "play_starting"      # Opening lead about to be made
    PLAY_IN_PROGRESS = "play_in_progress"  # Cards being played
    PLAY_COMPLETE = "play_complete"      # All 13 tricks played
    SCORING = "scoring"                  # Calculating final score
    ROUND_COMPLETE = "round_complete"    # Hand complete, ready for next

    def __str__(self):
        return self.value

    @property
    def is_play_phase(self) -> bool:
        """Check if currently in play phase (any play state)"""
        return self in [GamePhase.PLAY_STARTING, GamePhase.PLAY_IN_PROGRESS, GamePhase.PLAY_COMPLETE]

    @property
    def is_bidding_phase(self) -> bool:
        """Check if currently in bidding phase"""
        return self in [GamePhase.BIDDING, GamePhase.BIDDING_COMPLETE]

    @property
    def allows_card_play(self) -> bool:
        """Check if card play is allowed in this phase"""
        return self in [GamePhase.PLAY_STARTING, GamePhase.PLAY_IN_PROGRESS]

    @property
    def allows_bidding(self) -> bool:
        """Check if bidding is allowed in this phase"""
        return self == GamePhase.BIDDING

@dataclass
class Contract:
    """Represents the final contract from bidding"""
    level: int  # 1-7
    strain: str  # ♣, ♦, ♥, ♠, or NT
    declarer: str  # N, E, S, W
    doubled: int = 0  # 0=undoubled, 1=doubled, 2=redoubled

    def __str__(self):
        double_str = "" if self.doubled == 0 else "X" if self.doubled == 1 else "XX"
        return f"{self.level}{self.strain}{double_str} by {self.declarer}"

    @property
    def trump_suit(self) -> Optional[str]:
        """Return trump suit, or None for NT"""
        return None if self.strain == 'NT' else self.strain

    @property
    def tricks_needed(self) -> int:
        """Tricks needed to make contract (book + level)"""
        return 6 + self.level


@dataclass
class Trick:
    """Represents one complete trick (4 cards)"""
    cards: List[Tuple[Card, str]]  # (card, player) pairs
    leader: str  # Who led
    winner: str  # Who won

    @property
    def led_suit(self) -> str:
        """The suit that was led"""
        return self.cards[0][0].suit


@dataclass
class PlayState:
    """Complete state of card play"""
    contract: Contract
    hands: Dict[str, Hand]  # Current cards in each hand
    current_trick: List[Tuple[Card, str]]  # Cards played in current trick
    tricks_won: Dict[str, int]  # Tricks won by each player
    trick_history: List[Trick] = field(default_factory=list)
    next_to_play: str = 'N'
    dummy_revealed: bool = False
    current_trick_leader: Optional[str] = None  # Who led the current trick
    phase: GamePhase = GamePhase.PLAY_STARTING  # Current game phase

    @property
    def dummy(self) -> str:
        """Return dummy position (partner of declarer)"""
        declarer = self.contract.declarer
        return {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}[declarer]

    @property
    def tricks_taken_ns(self) -> int:
        """Total tricks taken by NS partnership"""
        return self.tricks_won.get('N', 0) + self.tricks_won.get('S', 0)

    @property
    def tricks_taken_ew(self) -> int:
        """Total tricks taken by EW partnership"""
        return self.tricks_won.get('E', 0) + self.tricks_won.get('W', 0)

    @property
    def is_complete(self) -> bool:
        """Check if all 13 tricks have been played"""
        total_tricks = self.tricks_taken_ns + self.tricks_taken_ew
        return total_tricks == 13

    def transition_to(self, new_phase: GamePhase) -> None:
        """
        Transition to a new game phase with validation.

        Raises ValueError if transition is invalid.
        """
        valid_transitions = {
            GamePhase.SETUP: [GamePhase.DEALING],
            GamePhase.DEALING: [GamePhase.BIDDING],
            GamePhase.BIDDING: [GamePhase.BIDDING_COMPLETE],
            GamePhase.BIDDING_COMPLETE: [GamePhase.PLAY_STARTING],
            GamePhase.PLAY_STARTING: [GamePhase.PLAY_IN_PROGRESS],
            GamePhase.PLAY_IN_PROGRESS: [GamePhase.PLAY_IN_PROGRESS, GamePhase.PLAY_COMPLETE],
            GamePhase.PLAY_COMPLETE: [GamePhase.SCORING],
            GamePhase.SCORING: [GamePhase.ROUND_COMPLETE],
            GamePhase.ROUND_COMPLETE: [GamePhase.SETUP, GamePhase.DEALING],
        }

        if new_phase not in valid_transitions.get(self.phase, []):
            raise ValueError(
                f"Invalid phase transition: {self.phase} → {new_phase}. "
                f"Valid transitions from {self.phase}: {valid_transitions.get(self.phase, [])}"
            )

        self.phase = new_phase

    def can_play_card(self) -> bool:
        """Check if card play is allowed in current phase"""
        return self.phase.allows_card_play

    def update_phase_after_card(self) -> None:
        """
        Auto-update phase based on game state after a card is played.

        Call this after each card play to keep phase in sync.
        """
        if self.phase == GamePhase.PLAY_STARTING and len(self.current_trick) > 0:
            # First card played, transition to in progress
            self.phase = GamePhase.PLAY_IN_PROGRESS

        elif self.phase == GamePhase.PLAY_IN_PROGRESS and self.is_complete:
            # All tricks complete
            self.phase = GamePhase.PLAY_COMPLETE


class PlayEngine:
    """Core engine for card play - stable foundation"""

    # Position order (clockwise from North)
    POSITIONS = ['N', 'E', 'S', 'W']

    # Rank values for comparison
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    @staticmethod
    def create_play_session(contract: Contract, hands: Dict[str, Hand],
                           vulnerability: Optional[Dict[str, bool]] = None) -> PlayState:
        """
        Factory method for creating standalone play session

        This enables testing and standalone play without going through bidding phase.

        Args:
            contract: The contract to play
            hands: Dictionary mapping position ('N', 'E', 'S', 'W') to Hand objects
            vulnerability: Optional vulnerability dict {'ns': bool, 'ew': bool}

        Returns:
            PlayState ready to begin play

        Example:
            contract = Contract(level=3, strain='NT', declarer='S')
            hands = {'N': hand_n, 'E': hand_e, 'S': hand_s, 'W': hand_w}
            play_state = PlayEngine.create_play_session(contract, hands)
        """
        if vulnerability is None:
            vulnerability = {'ns': False, 'ew': False}

        # Opening leader is LHO of declarer
        opening_leader = PlayEngine.next_player(contract.declarer)

        return PlayState(
            contract=contract,
            hands=hands,
            current_trick=[],
            tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
            trick_history=[],
            next_to_play=opening_leader,
            dummy_revealed=False
        )

    @staticmethod
    def determine_contract(auction: List[str], dealer_index: int = 0) -> Optional[Contract]:
        """
        Determine final contract from auction

        Returns None if all Pass (no contract)
        """
        # Find last non-Pass bid
        last_bid = None
        last_bid_index = -1

        for i, bid in enumerate(auction):
            if bid not in ['Pass', 'X', 'XX']:
                last_bid = bid
                last_bid_index = i

        if not last_bid:
            return None  # All passed

        # Check if auction is complete (3 passes after last bid)
        passes_after = sum(1 for b in auction[last_bid_index + 1:] if b == 'Pass')
        if passes_after < 3:
            return None  # Bidding not complete

        # Extract contract details
        level = int(last_bid[0])
        strain = last_bid[1:]

        # Find declarer (first player on winning side to bid this strain)
        declarer = PlayEngine._find_declarer(auction, last_bid, dealer_index)

        # Count doubles/redoubles
        doubled = PlayEngine._count_doubles(auction, last_bid_index)

        return Contract(level=level, strain=strain, declarer=declarer, doubled=doubled)

    @staticmethod
    def _find_declarer(auction: List[str], final_bid: str, dealer_index: int) -> str:
        """Find who declared the final contract (first to bid strain)"""
        strain = final_bid[1:]
        positions = PlayEngine.POSITIONS

        for i, bid in enumerate(auction):
            if bid.endswith(strain) and bid not in ['Pass', 'X', 'XX']:
                position = positions[(dealer_index + i) % 4]
                # Check if this is the winning partnership
                final_bidder_pos = positions[(dealer_index + len(auction) - 4) % 4]
                if PlayEngine._same_partnership(position, final_bidder_pos):
                    return position

        # Fallback: final bidder
        return positions[(dealer_index + len(auction) - 4) % 4]

    @staticmethod
    def _same_partnership(pos1: str, pos2: str) -> bool:
        """Check if two positions are on same partnership"""
        return (pos1 in ['N', 'S'] and pos2 in ['N', 'S']) or \
               (pos1 in ['E', 'W'] and pos2 in ['E', 'W'])

    @staticmethod
    def _count_doubles(auction: List[str], last_bid_index: int) -> int:
        """Count doubles/redoubles after last bid"""
        doubled = 0
        for bid in auction[last_bid_index + 1:]:
            if bid == 'X':
                doubled = 1
            elif bid == 'XX':
                doubled = 2
        return doubled

    @staticmethod
    def is_legal_play(card: Card, hand: Hand, current_trick: List[Tuple[Card, str]],
                      trump_suit: Optional[str] = None) -> bool:
        """
        Check if card play is legal according to bridge rules

        Rules:
        1. Must follow suit if able
        2. If void in led suit, any card is legal
        """
        if card not in hand.cards:
            return False

        if not current_trick:
            # Leading - any card is legal
            return True

        led_suit = current_trick[0][0].suit

        # Check if we have cards in led suit
        cards_in_led_suit = [c for c in hand.cards if c.suit == led_suit]

        if cards_in_led_suit:
            # Must follow suit
            return card.suit == led_suit

        # Void in led suit - any card is legal
        return True

    @staticmethod
    def determine_trick_winner(trick: List[Tuple[Card, str]], trump_suit: Optional[str]) -> str:
        """
        Determine which player won the trick

        Rules:
        1. Highest trump wins
        2. If no trumps, highest card in led suit wins
        """
        if len(trick) != 4:
            raise ValueError("Trick must have exactly 4 cards")

        led_suit = trick[0][0].suit

        # Find all trump cards
        if trump_suit:
            trump_cards = [(card, player) for card, player in trick if card.suit == trump_suit]
            if trump_cards:
                # Highest trump wins
                winner_card, winner = max(trump_cards,
                                         key=lambda x: PlayEngine.RANK_VALUES[x[0].rank])
                return winner

        # No trumps played - highest card in led suit wins
        led_suit_cards = [(card, player) for card, player in trick if card.suit == led_suit]
        winner_card, winner = max(led_suit_cards,
                                  key=lambda x: PlayEngine.RANK_VALUES[x[0].rank])
        return winner

    @staticmethod
    def next_player(current: str) -> str:
        """Get next player clockwise"""
        positions = PlayEngine.POSITIONS
        idx = positions.index(current)
        return positions[(idx + 1) % 4]

    @staticmethod
    def partner(position: str) -> str:
        """Get partner of given position"""
        positions = PlayEngine.POSITIONS
        idx = positions.index(position)
        return positions[(idx + 2) % 4]

    @staticmethod
    def calculate_score(contract: Contract, tricks_taken: int,
                       vulnerability: Dict[str, bool], hands: Optional[Dict[str, Hand]] = None) -> Dict:
        """
        Calculate score for a completed contract (SAYC scoring)

        Returns dict with:
        - score: int (positive for declarer, negative for defenders)
        - made: bool
        - overtricks/undertricks: int
        - honors_bonus: int (if hands provided)
        """
        tricks_needed = contract.tricks_needed
        declarer_side = 'ns' if contract.declarer in ['N', 'S'] else 'ew'
        is_vulnerable = vulnerability.get(declarer_side, False)

        if tricks_taken >= tricks_needed:
            # Contract made
            result = PlayEngine._score_made_contract(contract, tricks_taken, is_vulnerable)
        else:
            # Contract defeated
            result = PlayEngine._score_down_contract(contract, tricks_taken, is_vulnerable)

        # Add honors bonus if hands are provided
        if hands:
            honors_bonus = PlayEngine.calculate_honors(contract, hands)
            if honors_bonus > 0:
                result['score'] += honors_bonus
                result['breakdown']['honors_bonus'] = honors_bonus

        return result

    @staticmethod
    def calculate_honors(contract: Contract, hands: Dict[str, Hand]) -> int:
        """
        Calculate honors bonus (rubber bridge rule, also used in some duplicate)

        Honors Rules:
        - Trump contracts:
          * 4 of 5 trump honors (A, K, Q, J, 10) in one hand = 100
          * All 5 trump honors in one hand = 150
        - Notrump contracts:
          * All 4 aces in one hand = 150

        Returns:
            int: Honors bonus (0 if no honors, 100 or 150 if honors held)
        """
        if contract.strain == 'NT':
            # Check for all 4 aces in one hand
            for position, hand in hands.items():
                aces_count = sum(1 for card in hand.cards if card.rank == 'A')
                if aces_count == 4:
                    return 150
            return 0
        else:
            # Trump contract - check for trump honors
            trump_suit = contract.trump_suit
            honor_ranks = {'A', 'K', 'Q', 'J', 'T'}  # T = 10

            # Check each hand for trump honors
            for position, hand in hands.items():
                trump_honors = [card for card in hand.cards
                               if card.suit == trump_suit and card.rank in honor_ranks]

                honor_count = len(trump_honors)

                if honor_count == 5:
                    return 150  # All 5 honors
                elif honor_count == 4:
                    return 100  # 4 of 5 honors

            return 0  # No honors bonus

    @staticmethod
    def _score_made_contract(contract: Contract, tricks_taken: int, vulnerable: bool) -> Dict:
        """Calculate score for made contract"""
        tricks_needed = contract.tricks_needed
        overtricks = tricks_taken - tricks_needed

        # Base trick score
        if contract.strain in ['♣', '♦']:
            per_trick = 20
        else:  # ♥, ♠, NT
            per_trick = 30

        trick_score = contract.level * per_trick
        if contract.strain == 'NT':
            trick_score += 10  # First NT trick is 40

        # Apply doubling
        if contract.doubled >= 1:
            trick_score *= 2
        if contract.doubled == 2:
            trick_score *= 2

        # Game bonus
        game_bonus = 0
        if trick_score >= 100:
            game_bonus = 500 if vulnerable else 300
        else:
            game_bonus = 50  # Part-score bonus

        # Slam bonuses
        slam_bonus = 0
        if contract.level == 6:
            slam_bonus = 750 if vulnerable else 500
        elif contract.level == 7:
            slam_bonus = 1500 if vulnerable else 1000

        # Overtricks
        overtrick_score = 0
        if contract.doubled == 0:
            overtrick_score = overtricks * per_trick
        elif contract.doubled == 1:
            overtrick_score = overtricks * (200 if vulnerable else 100)
        else:  # redoubled
            overtrick_score = overtricks * (400 if vulnerable else 200)

        # Double/redouble bonus
        double_bonus = 50 * contract.doubled if contract.doubled > 0 else 0

        total = trick_score + game_bonus + slam_bonus + overtrick_score + double_bonus

        return {
            'score': total,
            'made': True,
            'overtricks': overtricks,
            'breakdown': {
                'trick_score': trick_score,
                'game_bonus': game_bonus,
                'slam_bonus': slam_bonus,
                'overtrick_score': overtrick_score,
                'double_bonus': double_bonus
            }
        }

    @staticmethod
    def _score_down_contract(contract: Contract, tricks_taken: int, vulnerable: bool) -> Dict:
        """Calculate penalty for defeated contract"""
        tricks_needed = contract.tricks_needed
        undertricks = tricks_needed - tricks_taken

        if contract.doubled == 0:
            # Undoubled
            penalty_per_trick = 100 if vulnerable else 50
            penalty = undertricks * penalty_per_trick
        else:
            # Doubled or redoubled
            multiplier = 2 if contract.doubled == 2 else 1

            if vulnerable:
                # First undertrick: 200, rest: 300
                penalty = 200 * multiplier
                if undertricks > 1:
                    penalty += (undertricks - 1) * 300 * multiplier
            else:
                # First: 100, second/third: 200, rest: 300
                penalty = 100 * multiplier
                if undertricks > 1:
                    penalty += min(2, undertricks - 1) * 200 * multiplier
                if undertricks > 3:
                    penalty += (undertricks - 3) * 300 * multiplier

        return {
            'score': -penalty,
            'made': False,
            'undertricks': undertricks,
            'breakdown': {
                'penalty': penalty
            }
        }
