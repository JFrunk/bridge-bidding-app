"""
Bridge Rules Engine - Encodes Official Bridge Laws

This module implements the core rules of contract bridge regarding:
1. Hand visibility (who can see which hands)
2. Play control (who controls which positions)
3. Turn determination (whose turn is it to play)

References:
- Laws of Duplicate Bridge (2017)
- Law 41: Dummy's Rights and Limitations
- Law 45: Card Play Procedure

Design Principles:
- Declarative: Rules are encoded as pure functions
- Testable: All edge cases have explicit test coverage
- Single Source of Truth: Both frontend and backend use this engine
- Self-Documenting: Code reads like the rulebook
"""

from typing import Set, Optional
from dataclasses import dataclass
from enum import Enum


class Position(Enum):
    """Bridge table positions (compass directions)"""
    NORTH = 'N'
    EAST = 'E'
    SOUTH = 'S'
    WEST = 'W'

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, s: str) -> 'Position':
        """Convert string to Position enum"""
        mapping = {
            'N': cls.NORTH, 'North': cls.NORTH,
            'E': cls.EAST, 'East': cls.EAST,
            'S': cls.SOUTH, 'South': cls.SOUTH,
            'W': cls.WEST, 'West': cls.WEST
        }
        return mapping.get(s, cls.SOUTH)  # Default to South


class PlayerRole(Enum):
    """Player's role in the current deal"""
    DECLARER = 'declarer'
    DUMMY = 'dummy'
    DEFENDER = 'defender'


@dataclass
class GameState:
    """
    Represents the current state of a bridge game

    Attributes:
        declarer: Position of declarer (e.g., 'N', 'S', 'E', 'W')
        dummy: Position of dummy (partner of declarer)
        user_position: Position of human player (default 'S')
        next_to_play: Position that should play next card
        dummy_revealed: Whether dummy has been revealed (after opening lead)
        opening_lead_made: Whether the opening lead has been played
    """
    declarer: str
    dummy: str
    user_position: str = 'S'
    next_to_play: Optional[str] = None
    dummy_revealed: bool = False
    opening_lead_made: bool = False


class BridgeRulesEngine:
    """
    Encodes the official laws of bridge regarding visibility and control.

    Key Bridge Rules Implemented:

    1. DECLARER CONTROL (Law 45):
       - Declarer controls BOTH their own hand AND dummy's hand
       - Declarer makes all decisions for dummy
       - Dummy makes NO decisions (passive role)

    2. DEFENDER CONTROL:
       - Each defender controls ONLY their own hand
       - Defenders cannot see or control partner's hand

    3. HAND VISIBILITY (Law 41):
       - Before opening lead: Only player's own hand visible
       - After opening lead: Dummy is revealed to ALL players
       - Declarer sees: Own hand + Dummy (2 hands)
       - Defenders see: Own hand + Dummy (2 hands)
       - Dummy player sees: Own hand + Declarer's hand (2 hands) [if human is dummy]

    4. TURN SEQUENCING:
       - Opening lead: Left-hand opponent (LHO) of declarer leads first
       - After opening lead: Play proceeds clockwise
       - Winner of trick leads to next trick
    """

    @staticmethod
    def get_dummy_position(declarer: str) -> str:
        """
        Get dummy position (partner of declarer).

        In bridge, partners sit opposite each other:
        - North ↔ South
        - East ↔ West

        Args:
            declarer: Position of declarer ('N', 'E', 'S', 'W')

        Returns:
            Position of dummy (partner of declarer)
        """
        partnerships = {
            'N': 'S', 'S': 'N',  # North-South partnership
            'E': 'W', 'W': 'E'   # East-West partnership
        }
        return partnerships.get(declarer, 'N')

    @staticmethod
    def get_player_role(position: str, declarer: str, dummy: str) -> PlayerRole:
        """
        Determine the role of a position in the current deal.

        Args:
            position: Position to check ('N', 'E', 'S', 'W')
            declarer: Position of declarer
            dummy: Position of dummy

        Returns:
            PlayerRole enum (DECLARER, DUMMY, or DEFENDER)
        """
        if position == declarer:
            return PlayerRole.DECLARER
        elif position == dummy:
            return PlayerRole.DUMMY
        else:
            return PlayerRole.DEFENDER

    @staticmethod
    def get_visible_hands(state: GameState) -> Set[str]:
        """
        Determine which hands should be visible to the user (SINGLE-PLAYER MODE).

        Single-Player Visibility Rules:
        1. User ALWAYS sees South (their hand)
        2. After opening lead, dummy is revealed
        3. If NS is declaring (N or S is declarer), user sees BOTH N and S after opening lead
        4. If EW is declaring (E or W is declarer), user sees S and dummy (E or W)

        Args:
            state: Current game state

        Returns:
            Set of positions whose hands should be visible (e.g., {'S', 'N'})
        """
        declarer = state.declarer
        dummy = state.dummy
        visible = {'S'}  # Always see South

        # After opening lead, reveal hands based on who is declaring
        if state.opening_lead_made or state.dummy_revealed:
            visible.add(dummy)  # Standard bridge: dummy always revealed

            # SINGLE-PLAYER MODE: If NS is declaring, user sees BOTH partnership hands
            # This reveals the declarer's hand (N or S) in addition to user's own hand
            if declarer in ['N', 'S']:
                visible.add('N')
                visible.add('S')

        return visible

    @staticmethod
    def get_controllable_positions(state: GameState) -> Set[str]:
        """
        Determine which positions the user can play cards from (SINGLE-PLAYER MODE).

        Single-Player Control Rules (DIGITAL BRIDGE - NOT 4-PLAYER RULES):
        1. User controls South ALWAYS
        2. User controls North ONLY when NS is declaring (N or S is declarer)
        3. Before opening lead, only the opening leader can act
        4. IMPORTANT: In single-player mode, user controls BOTH declarer AND dummy
           when NS is declaring (unlike 4-player bridge where dummy is passive)

        Args:
            state: Current game state

        Returns:
            Set of positions user can play from (e.g., {'S', 'N'})
        """
        declarer = state.declarer

        # NS is declaring side (North or South is declarer)
        if declarer in ['N', 'S']:
            # Before opening lead, only opening leader can act
            if not state.opening_lead_made:
                opening_leader = BridgeRulesEngine.get_opening_leader(declarer)
                # If opening leader is NS, user can make the lead
                if opening_leader in ['N', 'S']:
                    return {opening_leader}
                else:
                    # Wait for AI (E or W) to make opening lead
                    return set()
            else:
                # After opening lead, user controls both N and S (if user is declarer)
                return {'N', 'S'}

        # EW is declaring side (East or West is declarer)
        else:
            # User controls only South (defense)
            # Note: User can make opening lead if South is opening leader
            return {'S'}

    @staticmethod
    def is_user_turn(state: GameState) -> bool:
        """
        Determine if it's the user's turn to play a card.

        User's turn when:
        1. next_to_play is a position the user controls

        Args:
            state: Current game state

        Returns:
            True if user should play, False if AI should play
        """
        if not state.next_to_play:
            return False

        controllable = BridgeRulesEngine.get_controllable_positions(state)
        return state.next_to_play in controllable

    @staticmethod
    def should_ai_play(state: GameState) -> bool:
        """
        Determine if AI should play the next card.

        AI plays when it's NOT the user's turn.

        Args:
            state: Current game state

        Returns:
            True if AI should play, False if user should play
        """
        return not BridgeRulesEngine.is_user_turn(state)

    @staticmethod
    def can_user_play_from_position(state: GameState, position: str) -> bool:
        """
        Check if user can play a card from a specific position.

        Args:
            state: Current game state
            position: Position to check ('N', 'E', 'S', 'W')

        Returns:
            True if user can play from this position
        """
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        return position in controllable

    @staticmethod
    def get_next_player(current_player: str) -> str:
        """
        Get the next player in clockwise order.

        Clockwise order: N → E → S → W → N

        Args:
            current_player: Current position ('N', 'E', 'S', 'W')

        Returns:
            Next position in clockwise order
        """
        order = ['N', 'E', 'S', 'W']
        try:
            current_idx = order.index(current_player)
            next_idx = (current_idx + 1) % 4
            return order[next_idx]
        except ValueError:
            return 'N'  # Default to North if invalid position

    @staticmethod
    def get_opening_leader(declarer: str) -> str:
        """
        Determine who makes the opening lead.

        Bridge Rule: Left-hand opponent (LHO) of declarer leads first.
        LHO is the player to declarer's left (next clockwise).

        Args:
            declarer: Position of declarer ('N', 'E', 'S', 'W')

        Returns:
            Position of opening leader
        """
        return BridgeRulesEngine.get_next_player(declarer)

    @staticmethod
    def validate_play_request(state: GameState, position: str) -> tuple[bool, Optional[str]]:
        """
        Validate whether a play request is legal according to bridge rules.

        Args:
            state: Current game state
            position: Position attempting to play

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error message") if invalid
        """
        # Check if it's this position's turn
        if state.next_to_play != position:
            return False, f"Not {position}'s turn to play (next: {state.next_to_play})"

        # Check if user controls this position
        user_role = BridgeRulesEngine.get_player_role(
            state.user_position, state.declarer, state.dummy
        )
        controllable = BridgeRulesEngine.get_controllable_positions(state)

        # If AI is requesting to play
        if position not in controllable:
            # This is valid - AI should play for positions user doesn't control
            return True, None

        # If user is requesting to play from a position they don't control
        if position in controllable and not BridgeRulesEngine.is_user_turn(state):
            return False, f"User cannot play from {position} - not user's turn"

        return True, None

    @staticmethod
    def get_ui_display_info(state: GameState) -> dict:
        """
        Get all information needed for UI display.

        This provides a comprehensive view of what should be shown to the user.

        Args:
            state: Current game state

        Returns:
            Dictionary with UI display information
        """
        user_role = BridgeRulesEngine.get_player_role(
            state.user_position, state.declarer, state.dummy
        )

        return {
            'visible_hands': list(BridgeRulesEngine.get_visible_hands(state)),
            'controllable_positions': list(BridgeRulesEngine.get_controllable_positions(state)),
            'is_user_turn': BridgeRulesEngine.is_user_turn(state),
            'user_role': user_role.value,
            'next_to_play': state.next_to_play,
            'declarer': state.declarer,
            'dummy': state.dummy,
            'user_position': state.user_position,
            'dummy_revealed': state.dummy_revealed,
            'display_message': BridgeRulesEngine._get_turn_message(state)
        }

    @staticmethod
    def _get_turn_message(state: GameState) -> str:
        """
        Generate a user-friendly message about whose turn it is.

        Args:
            state: Current game state

        Returns:
            Human-readable turn message
        """
        if not state.next_to_play:
            return "Waiting for game to start..."

        controllable = BridgeRulesEngine.get_controllable_positions(state)

        if state.next_to_play in controllable:
            if state.next_to_play == state.dummy:
                return f"Your turn to play from dummy's hand ({state.dummy})!"
            elif state.next_to_play == state.declarer:
                return f"Your turn to play from your hand ({state.declarer})!"
            else:
                return "Your turn to play!"
        else:
            return f"Waiting for {state.next_to_play} to play..."

    # ──────────────────────────────────────────────────────────────────
    # BIDDING PHASE - Turn Determination
    # ──────────────────────────────────────────────────────────────────

    POSITION_ORDER = ['North', 'East', 'South', 'West']
    SHORT_TO_FULL = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
    FULL_TO_SHORT = {'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W'}

    @staticmethod
    def get_current_bidder(dealer: str, auction_length: int) -> str:
        """
        Calculate whose turn it is to bid based on dealer and number of
        bids already made.

        Bidding proceeds clockwise from the dealer:
          dealer bids first (auction_length=0),
          then LHO, partner, RHO, back to dealer, etc.

        Args:
            dealer: Full position name ('North', 'East', 'South', 'West')
                    or short form ('N', 'E', 'S', 'W')
            auction_length: Number of bids already placed in the auction

        Returns:
            Full position name of the player who should bid next
        """
        # Normalise to full name
        full_dealer = BridgeRulesEngine.SHORT_TO_FULL.get(dealer, dealer)
        order = BridgeRulesEngine.POSITION_ORDER
        try:
            dealer_idx = order.index(full_dealer)
        except ValueError:
            dealer_idx = 0  # Fallback to North
        return order[(dealer_idx + auction_length) % 4]

    @staticmethod
    def is_user_bid_turn(dealer: str, auction_length: int,
                         user_position: str = 'South') -> bool:
        """
        Determine whether it is the human player's turn to bid.

        Args:
            dealer: Dealer position (full or short name)
            auction_length: Number of bids already in the auction
            user_position: Human player's seat (default 'South')

        Returns:
            True if it is the human player's turn
        """
        current = BridgeRulesEngine.get_current_bidder(dealer, auction_length)
        full_user = BridgeRulesEngine.SHORT_TO_FULL.get(user_position,
                                                         user_position)
        return current == full_user

    @staticmethod
    def validate_bidder(dealer: str, auction_length: int,
                        claimed_player: str) -> tuple:
        """
        Validate that the claimed bidder matches the expected position.

        Args:
            dealer: Dealer position
            auction_length: Current auction length
            claimed_player: Position claiming to bid

        Returns:
            (is_valid, expected_player)  – is_valid is True when
            claimed_player matches the expected bidder.
        """
        expected = BridgeRulesEngine.get_current_bidder(dealer,
                                                         auction_length)
        full_claimed = BridgeRulesEngine.SHORT_TO_FULL.get(claimed_player,
                                                            claimed_player)
        return (full_claimed == expected, expected)
