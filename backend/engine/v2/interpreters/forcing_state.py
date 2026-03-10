"""
Forcing State Machine for V2 Bidding Engine

Tracks forcing level state across an auction:
- NON_FORCING: Any bid including Pass is valid
- FORCING_1_ROUND: Partner cannot pass on their next turn
- GAME_FORCE: Neither partner can pass until game is reached (sticky)

Extracted from SchemaInterpreter to keep that class focused on
rule evaluation and bid selection.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ForcingLevel(Enum):
    """Forcing level states for auction tracking."""
    NON_FORCING = "NON_FORCING"
    FORCING_1_ROUND = "FORCING_1_ROUND"
    GAME_FORCE = "GAME_FORCE"


@dataclass
class AuctionState:
    """Tracks the current state of the auction for forcing logic."""
    forcing_level: ForcingLevel = ForcingLevel.NON_FORCING
    is_game_forced: bool = False
    forcing_source: Optional[str] = None  # Rule ID that established forcing
    bids_since_forcing: int = 0  # Track rounds since forcing was set

    def reset(self):
        """Reset state for a new deal."""
        self.forcing_level = ForcingLevel.NON_FORCING
        self.is_game_forced = False
        self.forcing_source = None
        self.bids_since_forcing = 0


@dataclass
class BidValidationResult:
    """Result of validating a bid against forcing constraints."""
    is_valid: bool
    reason: Optional[str] = None
    violation_type: Optional[str] = None  # "GAME_FORCE_VIOLATION", "ONE_ROUND_VIOLATION"


class ForcingStateMachine:
    """
    Manages forcing level state across an auction.

    State transitions:
    - GAME_FORCE is "sticky" — once set, cannot be unset until game reached
    - FORCING_1_ROUND expires after partner bids (tracked via bids_since_forcing)
    - NON_FORCING is the default state
    """

    def __init__(self):
        self.state = AuctionState()

    def reset(self):
        """Reset state for a new deal."""
        self.state.reset()

    def get_state(self) -> Dict[str, Any]:
        """Get current forcing state for debugging/display."""
        return {
            'forcing_level': self.state.forcing_level.value,
            'is_game_forced': self.state.is_game_forced,
            'forcing_source': self.state.forcing_source,
            'bids_since_forcing': self.state.bids_since_forcing
        }

    def update(self, new_level: Optional[str], rule_id: str):
        """
        Update the forcing state based on a matched rule's metadata.

        Args:
            new_level: The sets_forcing_level value from the matched rule
            rule_id: ID of the rule that matched (for tracking source)
        """
        # Game force is permanent (sticky)
        if self.state.is_game_forced:
            return

        if new_level == "GAME_FORCE":
            self.state.forcing_level = ForcingLevel.GAME_FORCE
            self.state.is_game_forced = True
            self.state.forcing_source = rule_id
            self.state.bids_since_forcing = 0

        elif new_level == "FORCING_1_ROUND":
            self.state.forcing_level = ForcingLevel.FORCING_1_ROUND
            self.state.forcing_source = rule_id
            self.state.bids_since_forcing = 0

        elif new_level == "NON_FORCING" or new_level is None:
            # Check if we should expire a 1-round forcing
            if self.state.forcing_level == ForcingLevel.FORCING_1_ROUND:
                self.state.bids_since_forcing += 1
                # After partner bids (2 bids in partnership), 1-round forcing expires
                if self.state.bids_since_forcing >= 2:
                    self.state.forcing_level = ForcingLevel.NON_FORCING
                    self.state.forcing_source = None

    def validate_bid(self, bid: str, last_contract_level: int = 0,
                     last_contract_suit: str = '') -> BidValidationResult:
        """
        Validate a bid against the current forcing state.

        This is the "falsification" logic that prevents illegal passes
        during forcing sequences.

        Args:
            bid: The bid to validate
            last_contract_level: Current highest bid level in auction (0-7)
            last_contract_suit: Suit of the last contract bid (for game-level check)

        Returns:
            BidValidationResult indicating if the bid is legal
        """
        if bid != "Pass":
            return BidValidationResult(is_valid=True)

        # Check if game level has been reached — GF is satisfied
        # Game = 3NT, 4♥, 4♠, 5♣, 5♦, or any level 6+
        game_reached = (
            last_contract_level >= 6 or
            last_contract_level >= 5 or  # 5-level of any suit is game for minors
            (last_contract_level == 4 and last_contract_suit in ('♥', '♠', 'NT')) or
            (last_contract_level == 3 and last_contract_suit == 'NT')
        )
        if game_reached:
            # Game force is satisfied — pass is legal
            return BidValidationResult(is_valid=True)

        # Check Game Force violation
        if self.state.is_game_forced:
            return BidValidationResult(
                is_valid=False,
                reason="Cannot Pass: Auction is Game Forced. Partnership must reach game.",
                violation_type="GAME_FORCE_VIOLATION"
            )

        # Check 1-round forcing violation
        if self.state.forcing_level == ForcingLevel.FORCING_1_ROUND:
            return BidValidationResult(
                is_valid=False,
                reason="Cannot Pass: Partner's bid is forcing for one round.",
                violation_type="ONE_ROUND_VIOLATION"
            )

        return BidValidationResult(is_valid=True)
