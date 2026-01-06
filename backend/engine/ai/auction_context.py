"""
Auction Context - Expert-Level Partnership Range Tracking

This module implements the mental model expert bridge players use to track
partnership strength throughout an auction. It combines:

1. EXPLICIT information - what each bid directly shows
2. IMPLICIT information - what each bid denies (negative inferences)

Expert thought process example:
- Partner opened 1♠ → Shows 13-21 HCP, 5+ spades
- Partner DIDN'T open 1NT → Denies 15-17 balanced
- Partner DIDN'T open 2♣ → Denies 22+ HCP
- Partner rebid 2♠ → Shows minimum (13-16), 6+ spades
- Partner DIDN'T jump to 3♠ → Denies 16-18 with 6+ spades

Combined inference: Partner has 13-16 HCP, 6+ spades, unbalanced.

Part of ADR-0002: Bidding System Robustness Improvements
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

# Seat utilities - for partner calculation (uses modulo-4 clock system)
from utils.seats import SEATS

# Modulo-4 offsets for relative positions (see utils/seats.py)
PARTNER_OFFSET = 2

logger = logging.getLogger(__name__)


@dataclass
class PartnershipRanges:
    """
    Tracks HCP and shape ranges for both partners.

    Ranges are continuously narrowed as the auction progresses,
    using both explicit (what was bid) and implicit (what wasn't bid) information.
    """
    # HCP ranges (min, max)
    opener_hcp: Tuple[int, int] = (0, 40)
    responder_hcp: Tuple[int, int] = (0, 40)

    # Shape information: suit -> (min_length, max_length)
    opener_suits: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        '♠': (0, 13), '♥': (0, 13), '♦': (0, 13), '♣': (0, 13)
    })
    responder_suits: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        '♠': (0, 13), '♥': (0, 13), '♦': (0, 13), '♣': (0, 13)
    })

    # Limiting flags - once limited, player has shown their maximum
    opener_limited: bool = False
    responder_limited: bool = False

    # Agreed trump suit (if any)
    agreed_suit: Optional[str] = None

    # Forcing status
    game_forcing: bool = False
    one_round_force: bool = False
    invitational: bool = False

    def narrow_hcp(self, role: str, new_min: int = None, new_max: int = None):
        """Narrow HCP range for opener or responder."""
        if role == 'opener':
            current_min, current_max = self.opener_hcp
            self.opener_hcp = (
                max(current_min, new_min) if new_min is not None else current_min,
                min(current_max, new_max) if new_max is not None else current_max
            )
        else:
            current_min, current_max = self.responder_hcp
            self.responder_hcp = (
                max(current_min, new_min) if new_min is not None else current_min,
                min(current_max, new_max) if new_max is not None else current_max
            )

    def narrow_suit(self, role: str, suit: str, new_min: int = None, new_max: int = None):
        """Narrow suit length range for opener or responder."""
        suits = self.opener_suits if role == 'opener' else self.responder_suits
        current_min, current_max = suits[suit]
        suits[suit] = (
            max(current_min, new_min) if new_min is not None else current_min,
            min(current_max, new_max) if new_max is not None else current_max
        )

    @property
    def combined_minimum(self) -> int:
        """Conservative combined HCP estimate (both minimums)."""
        return self.opener_hcp[0] + self.responder_hcp[0]

    @property
    def combined_maximum(self) -> int:
        """Optimistic combined HCP estimate (both maximums)."""
        return self.opener_hcp[1] + self.responder_hcp[1]

    @property
    def combined_midpoint(self) -> int:
        """Expected combined HCP (average of ranges)."""
        opener_mid = (self.opener_hcp[0] + self.opener_hcp[1]) / 2
        responder_mid = (self.responder_hcp[0] + self.responder_hcp[1]) / 2
        return int(opener_mid + responder_mid)

    def likely_has_game(self) -> bool:
        """True if partnership likely has game values (25+ combined)."""
        # Use midpoint for "likely" assessment
        return self.combined_midpoint >= 25

    def definitely_has_game(self) -> bool:
        """True if partnership definitely has game values."""
        return self.combined_minimum >= 25

    def might_have_slam(self) -> bool:
        """True if partnership might have slam values (33+ combined)."""
        return self.combined_maximum >= 33


@dataclass
class AuctionContext:
    """
    Complete auction context tracking both explicit and implicit information.

    This is the "mental model" that expert players maintain throughout the auction.
    """
    ranges: PartnershipRanges = field(default_factory=PartnershipRanges)

    # Track who has bid what
    opener_bids: List[str] = field(default_factory=list)
    responder_bids: List[str] = field(default_factory=list)

    # Track the opening bid specially
    opening_bid: Optional[str] = None
    opener_position: Optional[str] = None

    # Auction state
    is_competitive: bool = False
    passed_out: bool = False

    @property
    def has_fit(self) -> bool:
        """True if partnership has agreed on a trump suit."""
        return self.ranges.agreed_suit is not None

    def __repr__(self):
        return (
            f"AuctionContext(\n"
            f"  opener_hcp={self.ranges.opener_hcp}, "
            f"responder_hcp={self.ranges.responder_hcp}\n"
            f"  combined={self.ranges.combined_minimum}-{self.ranges.combined_maximum}, "
            f"midpoint={self.ranges.combined_midpoint}\n"
            f"  game_forcing={self.ranges.game_forcing}, "
            f"agreed_suit={self.ranges.agreed_suit}\n"
            f")"
        )


class AuctionAnalyzer:
    """
    Analyzes auction to build AuctionContext with both explicit and implicit inferences.

    This replicates how expert bridge players process an auction:
    1. What does each bid SHOW? (explicit)
    2. What does each bid DENY? (implicit/negative inference)
    """

    # ==========================================================================
    # EXPLICIT BID MEANINGS - What each bid directly shows
    # ==========================================================================

    OPENING_BID_MEANINGS = {
        # 1-level suit openings: 13-21 HCP (could be more with distribution)
        '1♣': {'hcp': (13, 21), 'suit': ('♣', 3, 13), 'balanced_ok': True},
        '1♦': {'hcp': (13, 21), 'suit': ('♦', 4, 13), 'balanced_ok': True},
        '1♥': {'hcp': (13, 21), 'suit': ('♥', 5, 13), 'balanced_ok': False},
        '1♠': {'hcp': (13, 21), 'suit': ('♠', 5, 13), 'balanced_ok': False},

        # 1NT: 15-17 balanced
        '1NT': {'hcp': (15, 17), 'balanced': True},

        # 2♣: 22+ or 9+ tricks (we'll use 22+)
        '2♣': {'hcp': (22, 40), 'artificial': True},

        # Weak twos: 6-10 HCP, 6-card suit
        '2♦': {'hcp': (6, 10), 'suit': ('♦', 6, 6), 'preemptive': True},
        '2♥': {'hcp': (6, 10), 'suit': ('♥', 6, 6), 'preemptive': True},
        '2♠': {'hcp': (6, 10), 'suit': ('♠', 6, 6), 'preemptive': True},

        # 2NT: 20-21 balanced
        '2NT': {'hcp': (20, 21), 'balanced': True},

        # 3-level preempts: 6-10 HCP, 7-card suit
        '3♣': {'hcp': (6, 10), 'suit': ('♣', 7, 7), 'preemptive': True},
        '3♦': {'hcp': (6, 10), 'suit': ('♦', 7, 7), 'preemptive': True},
        '3♥': {'hcp': (6, 10), 'suit': ('♥', 7, 7), 'preemptive': True},
        '3♠': {'hcp': (6, 10), 'suit': ('♠', 7, 7), 'preemptive': True},

        # 3NT: Gambling (solid 7+ minor) or 25-27 balanced
        '3NT': {'hcp': (25, 27), 'balanced': True},

        # 4-level preempts: 6-10 HCP, 8-card suit
        '4♣': {'hcp': (6, 10), 'suit': ('♣', 8, 8), 'preemptive': True},
        '4♦': {'hcp': (6, 10), 'suit': ('♦', 8, 8), 'preemptive': True},
        '4♥': {'hcp': (6, 10), 'suit': ('♥', 8, 8), 'preemptive': True},
        '4♠': {'hcp': (6, 10), 'suit': ('♠', 8, 8), 'preemptive': True},
    }

    # Response meanings vary by opening bid
    RESPONSE_MEANINGS = {
        # Responses to 1-level suit openings
        '1_level_new_suit': {'hcp': (6, 40), 'suit_min': 4},  # Forcing
        '1NT_response': {'hcp': (6, 10), 'denies_4_card_major': True},
        'simple_raise': {'hcp': (6, 10), 'support': 3},  # e.g., 1♠-2♠
        'jump_raise': {'hcp': (10, 12), 'support': 4},   # e.g., 1♠-3♠ (invitational)
        'game_raise': {'hcp': (13, 16), 'support': 4},   # e.g., 1♠-4♠
        '2_level_new_suit': {'hcp': (10, 40), 'suit_min': 5},  # Game forcing
        '2NT_response': {'hcp': (11, 12), 'balanced': True},  # Invitational
        '3NT_response': {'hcp': (13, 15), 'balanced': True},  # Game values

        # Responses to 1NT
        'stayman_2c': {'hcp': (8, 40), 'artificial': True},  # 4-card major inquiry
        'jacoby_2d': {'hcp': (0, 40), 'suit': ('♥', 5, 13)},  # Transfer to hearts
        'jacoby_2h': {'hcp': (0, 40), 'suit': ('♠', 5, 13)},  # Transfer to spades
        '2NT_over_1NT': {'hcp': (8, 9), 'invitational': True},
        '3NT_over_1NT': {'hcp': (10, 15)},
        '4NT_over_1NT': {'hcp': (16, 17), 'quantitative': True},
    }

    # Rebid meanings (opener's second bid)
    REBID_MEANINGS = {
        'minimum_rebid_suit': {'hcp': (13, 16), 'limited': True},  # Simple rebid
        'minimum_rebid_1nt': {'hcp': (12, 14), 'limited': True, 'balanced': True},
        'jump_rebid_suit': {'hcp': (16, 18)},  # Jump rebid own suit
        'reverse': {'hcp': (17, 40)},  # Higher-ranking new suit at 2-level
        'jump_shift_rebid': {'hcp': (19, 21)},  # Jump in new suit
        '2NT_rebid': {'hcp': (18, 19), 'balanced': True},
        '3NT_rebid': {'hcp': (18, 19), 'balanced': True},  # After 2-level response
    }

    # ==========================================================================
    # IMPLICIT/NEGATIVE INFERENCES - What each bid denies
    # ==========================================================================

    OPENING_DENIALS = {
        # 1-level suit opening denies:
        '1♣': {'denies_hcp_above': 21, 'denies_balanced_15_17': True},
        '1♦': {'denies_hcp_above': 21, 'denies_balanced_15_17': True},
        '1♥': {'denies_hcp_above': 21, 'denies_balanced_15_17': True, 'denies_longer_spades': True},
        '1♠': {'denies_hcp_above': 21, 'denies_balanced_15_17': True},

        # 1NT denies:
        '1NT': {'denies_hcp_above': 17, 'denies_hcp_below': 15, 'denies_5_card_major': True},

        # 2♣ denies:
        '2♣': {'denies_hcp_below': 22},

        # Weak twos deny:
        '2♦': {'denies_hcp_above': 10, 'denies_hcp_below': 6, 'denies_4_card_major': True},
        '2♥': {'denies_hcp_above': 10, 'denies_hcp_below': 6},
        '2♠': {'denies_hcp_above': 10, 'denies_hcp_below': 6},

        # 2NT denies:
        '2NT': {'denies_hcp_above': 21, 'denies_hcp_below': 20},
    }

    RESPONSE_DENIALS = {
        # Simple raise denies game values
        'simple_raise': {'denies_hcp_above': 10},

        # Jump raise denies game values (invitational only)
        'jump_raise': {'denies_hcp_above': 12, 'denies_hcp_below': 10},

        # 1NT response denies 4-card major (usually) and game values
        '1NT_response': {'denies_hcp_above': 10, 'denies_4_card_major_usually': True},

        # 2-level new suit doesn't deny much (game forcing)
        '2_level_new_suit': {'denies_hcp_below': 10},

        # 2NT response is invitational - denies game forcing values
        '2NT_response': {'denies_hcp_above': 12, 'denies_hcp_below': 11},

        # Pass denies opening strength response
        'pass_response': {'denies_hcp_above': 5},
    }

    REBID_DENIALS = {
        # Minimum rebid denies extras
        'minimum_rebid': {'denies_hcp_above': 16},

        # 1NT rebid denies extras and unbalanced shape
        '1NT_rebid': {'denies_hcp_above': 14, 'denies_hcp_below': 12},

        # Jump rebid shows extras, denies maximum
        'jump_rebid': {'denies_hcp_above': 18, 'denies_hcp_below': 16},

        # Reverse shows 17+, denies minimum
        'reverse': {'denies_hcp_below': 17},

        # Pass after response denies ability to continue (extreme minimum)
        'pass_rebid': {'denies_hcp_above': 14},
    }

    def analyze_auction(self, auction_history: List[str], positions: List[str],
                        my_index: int) -> AuctionContext:
        """
        Analyze complete auction and return AuctionContext with ranges.

        Args:
            auction_history: List of bids ['1♠', 'Pass', '2♠', 'Pass', ...]
            positions: ['North', 'East', 'South', 'West']
            my_index: Index of current player (0-3)

        Returns:
            AuctionContext with narrowed ranges based on all bids
        """
        context = AuctionContext()

        # Find opener
        opener_index = None
        for i, bid in enumerate(auction_history):
            if bid not in ['Pass', 'X', 'XX']:
                opener_index = i % 4
                context.opening_bid = bid
                context.opener_position = positions[opener_index]
                break

        if opener_index is None:
            context.passed_out = True
            return context

        # Determine responder (opener's partner)
        responder_index = (opener_index + PARTNER_OFFSET) % 4

        # Process each bid
        for i, bid in enumerate(auction_history):
            if bid in ['Pass', 'X', 'XX']:
                # Handle Pass specially
                if bid == 'Pass':
                    self._process_pass(context, i, opener_index, responder_index, auction_history)
                continue

            bidder_index = i % 4

            # Is this the opener or responder (or opponent)?
            if bidder_index == opener_index:
                context.opener_bids.append(bid)
                self._process_opener_bid(context, bid, len(context.opener_bids), auction_history[:i])
            elif bidder_index == responder_index:
                context.responder_bids.append(bid)
                self._process_responder_bid(context, bid, len(context.responder_bids), auction_history[:i])
            else:
                # Opponent bid - mark as competitive
                context.is_competitive = True

        logger.debug(f"Auction analysis complete: {context}")
        return context

    def _process_opener_bid(self, context: AuctionContext, bid: str, bid_number: int,
                           prior_auction: List[str]):
        """Process opener's bid and update ranges."""
        ranges = context.ranges

        if bid_number == 1:
            # Opening bid
            self._apply_opening_bid(context, bid)
        else:
            # Rebid
            self._apply_opener_rebid(context, bid, prior_auction)

    def _process_responder_bid(self, context: AuctionContext, bid: str, bid_number: int,
                               prior_auction: List[str]):
        """Process responder's bid and update ranges."""
        ranges = context.ranges

        if bid_number == 1:
            # First response
            self._apply_response(context, bid, prior_auction)
        else:
            # Responder's rebid
            self._apply_responder_rebid(context, bid, prior_auction)

    def _process_pass(self, context: AuctionContext, auction_index: int,
                     opener_index: int, responder_index: int, auction_history: List[str]):
        """Process a Pass bid - important for negative inferences."""
        bidder_index = auction_index % 4
        ranges = context.ranges

        # Pass by responder after partner opened = weak hand
        if bidder_index == responder_index and len(context.opener_bids) >= 1:
            if len(context.responder_bids) == 0:
                # First response was Pass - very weak
                ranges.narrow_hcp('responder', new_max=5)
                ranges.responder_limited = True

        # Pass by opener after response = minimum, nothing more to say
        if bidder_index == opener_index and len(context.responder_bids) >= 1:
            if len(context.opener_bids) >= 1 and not ranges.opener_limited:
                # Opener passed after response - minimum hand
                ranges.narrow_hcp('opener', new_max=15)
                ranges.opener_limited = True

    def _apply_opening_bid(self, context: AuctionContext, bid: str):
        """Apply opening bid meanings and denials."""
        ranges = context.ranges

        meaning = self.OPENING_BID_MEANINGS.get(bid, {})
        denial = self.OPENING_DENIALS.get(bid, {})

        # Apply explicit HCP range
        if 'hcp' in meaning:
            ranges.narrow_hcp('opener', new_min=meaning['hcp'][0], new_max=meaning['hcp'][1])

        # Apply suit length
        if 'suit' in meaning:
            suit, min_len, max_len = meaning['suit']
            ranges.narrow_suit('opener', suit, new_min=min_len, new_max=max_len)

        # Apply denials (implicit)
        if 'denies_hcp_above' in denial:
            ranges.narrow_hcp('opener', new_max=denial['denies_hcp_above'])
        if 'denies_hcp_below' in denial:
            ranges.narrow_hcp('opener', new_min=denial['denies_hcp_below'])

        # Preemptive openings are limited
        if meaning.get('preemptive'):
            ranges.opener_limited = True

    def _apply_response(self, context: AuctionContext, bid: str, prior_auction: List[str]):
        """Apply response meanings based on opening bid."""
        ranges = context.ranges
        opening = context.opening_bid

        # Determine response type
        response_type = self._classify_response(bid, opening)

        if response_type == 'simple_raise':
            ranges.narrow_hcp('responder', new_min=6, new_max=10)
            ranges.responder_limited = True
            # Find the suit being raised
            if opening and len(opening) >= 2:
                suit = opening[1] if opening[1] in '♠♥♦♣' else opening[1:]
                if suit in '♠♥♦♣':
                    ranges.narrow_suit('responder', suit, new_min=3)
                    ranges.agreed_suit = suit

        elif response_type == 'jump_raise':
            ranges.narrow_hcp('responder', new_min=10, new_max=12)
            ranges.invitational = True
            if opening and len(opening) >= 2:
                suit = opening[1] if opening[1] in '♠♥♦♣' else opening[1:]
                if suit in '♠♥♦♣':
                    ranges.narrow_suit('responder', suit, new_min=4)
                    ranges.agreed_suit = suit

        elif response_type == 'game_raise':
            ranges.narrow_hcp('responder', new_min=13, new_max=16)
            ranges.game_forcing = True
            if opening and len(opening) >= 2:
                suit = opening[1] if opening[1] in '♠♥♦♣' else opening[1:]
                if suit in '♠♥♦♣':
                    ranges.agreed_suit = suit

        elif response_type == '1NT_response':
            ranges.narrow_hcp('responder', new_min=6, new_max=10)
            ranges.responder_limited = True

        elif response_type == '1_level_new_suit':
            ranges.narrow_hcp('responder', new_min=6)
            ranges.one_round_force = True
            # Show suit length
            suit = bid[1] if len(bid) >= 2 and bid[1] in '♠♥♦♣' else None
            if suit:
                ranges.narrow_suit('responder', suit, new_min=4)

        elif response_type == '2_level_new_suit':
            ranges.narrow_hcp('responder', new_min=10)
            ranges.game_forcing = True
            suit = bid[1] if len(bid) >= 2 and bid[1] in '♠♥♦♣' else None
            if suit:
                ranges.narrow_suit('responder', suit, new_min=5)

        elif response_type == '2NT_response':
            ranges.narrow_hcp('responder', new_min=11, new_max=12)
            ranges.invitational = True

        elif response_type == '3NT_response':
            ranges.narrow_hcp('responder', new_min=13, new_max=15)
            ranges.responder_limited = True

        # STAYMAN and JACOBY TRANSFERS over 1NT
        elif response_type == 'stayman_2c':
            # Stayman: 8+ HCP with a 4-card major, asking for majors
            # Can be invitational (8-9) or game-forcing (10+)
            # We use a wide range since exact values depend on followup
            ranges.narrow_hcp('responder', new_min=8)
            ranges.one_round_force = True
            # Don't set game_forcing yet - depends on the continuation

        elif response_type == 'jacoby_2d':
            # Transfer to hearts: can be very weak (0 HCP) with 5+ hearts
            # or strong with 5+ hearts
            ranges.narrow_suit('responder', '♥', new_min=5)
            ranges.one_round_force = True

        elif response_type == 'jacoby_2h':
            # Transfer to spades: can be very weak (0 HCP) with 5+ spades
            # or strong with 5+ spades
            ranges.narrow_suit('responder', '♠', new_min=5)
            ranges.one_round_force = True

    def _apply_opener_rebid(self, context: AuctionContext, bid: str, prior_auction: List[str]):
        """Apply opener's rebid meanings."""
        ranges = context.ranges

        rebid_type = self._classify_rebid(bid, context.opening_bid, prior_auction)

        if rebid_type == 'stayman_response':
            # Stayman response (2♦/2♥/2♠) doesn't change opener's HCP range
            # Just shows whether they have a 4-card major
            # HCP stays at 15-17 for 1NT opener
            if bid == '2♦':
                # No 4-card major
                ranges.narrow_suit('opener', '♥', new_max=3)
                ranges.narrow_suit('opener', '♠', new_max=3)
            elif bid == '2♥':
                # Has 4+ hearts
                ranges.narrow_suit('opener', '♥', new_min=4)
            elif bid == '2♠':
                # Has 4+ spades (and not 4 hearts, or chose spades)
                ranges.narrow_suit('opener', '♠', new_min=4)
            return  # Don't apply other rebid logic

        elif rebid_type == 'transfer_completion':
            # Transfer completion is mandatory - doesn't show extra values
            # HCP stays unchanged
            return  # Don't apply other rebid logic

        elif rebid_type == 'minimum_rebid':
            ranges.narrow_hcp('opener', new_max=16)
            ranges.opener_limited = True

        elif rebid_type == '1NT_rebid':
            ranges.narrow_hcp('opener', new_min=12, new_max=14)
            ranges.opener_limited = True

        elif rebid_type == '2NT_rebid':
            ranges.narrow_hcp('opener', new_min=18, new_max=19)

        elif rebid_type == 'jump_rebid':
            ranges.narrow_hcp('opener', new_min=16, new_max=18)

        elif rebid_type == 'reverse':
            ranges.narrow_hcp('opener', new_min=17)
            ranges.one_round_force = True

        elif rebid_type == 'game_bid':
            # Opener jumped to game - shows extras
            ranges.narrow_hcp('opener', new_min=16)

    def _apply_responder_rebid(self, context: AuctionContext, bid: str, prior_auction: List[str]):
        """Apply responder's rebid meanings."""
        ranges = context.ranges

        # If responder bids again after being limited, they're showing extras
        # or correcting
        if ranges.responder_limited:
            return  # Already limited, can't show more

        # Check if this is a Stayman continuation
        is_stayman_continuation = '2♣' in context.responder_bids and context.opening_bid in ['1NT', '2NT']

        if is_stayman_continuation:
            # After Stayman, responder's rebid reveals their hand type
            try:
                bid_level = int(bid[0])
                bid_suit = bid[1:] if len(bid) > 1 else ''
            except (ValueError, IndexError):
                return

            # Get opener's response to Stayman (what did they bid?)
            opener_stayman_response = None
            for ob in context.opener_bids:
                if ob in ['2♦', '2♥', '2♠']:
                    opener_stayman_response = ob
                    break

            if opener_stayman_response:
                opener_suit = opener_stayman_response[1:] if len(opener_stayman_response) > 1 else ''

                # 3-level raise of opener's major = limit raise (8-9 HCP, 4-card support)
                if bid_level == 3 and bid_suit == opener_suit and bid_suit in ['♥', '♠']:
                    ranges.narrow_hcp('responder', new_min=8, new_max=9)
                    ranges.invitational = True
                    ranges.responder_limited = True
                    ranges.agreed_suit = bid_suit
                    return

                # 4-level bid of opener's major = game values (10+ HCP, 4-card support)
                if bid_level == 4 and bid_suit == opener_suit and bid_suit in ['♥', '♠']:
                    ranges.narrow_hcp('responder', new_min=10, new_max=15)
                    ranges.agreed_suit = bid_suit
                    return

                # 2NT after 2♦ = invitational without a fit (8-9 HCP)
                if bid == '2NT' and opener_stayman_response == '2♦':
                    ranges.narrow_hcp('responder', new_min=8, new_max=9)
                    ranges.invitational = True
                    ranges.responder_limited = True
                    return

                # 3NT after any response = game values without a fit (10+ HCP)
                if bid == '3NT':
                    ranges.narrow_hcp('responder', new_min=10, new_max=15)
                    return

        # Standard responder rebids (non-Stayman)
        if bid in ['2NT']:
            ranges.narrow_hcp('responder', new_min=10, new_max=12)
            ranges.invitational = True
        elif bid == '3NT':
            ranges.narrow_hcp('responder', new_min=13)
            ranges.game_forcing = True
        elif bid.startswith('4') and len(bid) > 1 and bid[1] in '♥♠':
            ranges.narrow_hcp('responder', new_min=13)
            ranges.game_forcing = True

    def _classify_response(self, bid: str, opening: str) -> str:
        """Classify the type of response."""
        if not opening or not bid:
            return 'unknown'

        try:
            open_level = int(opening[0])
            bid_level = int(bid[0])
            open_suit = opening[1:] if len(opening) > 1 else ''
            bid_suit = bid[1:] if len(bid) > 1 else ''
        except (ValueError, IndexError):
            return 'unknown'

        # SPECIAL CASE: Stayman (2♣ over 1NT/2NT)
        # Stayman shows 8+ HCP with a 4-card major (invitational+)
        if opening in ['1NT', '2NT'] and bid == '2♣':
            return 'stayman_2c'

        # SPECIAL CASE: Jacoby Transfers over 1NT
        if opening == '1NT' and bid in ['2♦', '2♥']:
            if bid == '2♦':
                return 'jacoby_2d'  # Transfer to hearts
            else:
                return 'jacoby_2h'  # Transfer to spades

        # Same suit = raise
        if bid_suit == open_suit:
            if bid_level == open_level + 1:
                return 'simple_raise'
            elif bid_level == open_level + 2:
                return 'jump_raise'
            elif bid_level == 4 and open_suit in ['♥', '♠']:
                return 'game_raise'

        # NT responses
        if 'NT' in bid:
            if bid == '1NT':
                return '1NT_response'
            elif bid == '2NT':
                return '2NT_response'
            elif bid == '3NT':
                return '3NT_response'

        # New suit at 1-level
        if bid_level == 1 and bid_suit != open_suit:
            return '1_level_new_suit'

        # New suit at 2-level (after 1-level opening)
        if bid_level == 2 and open_level == 1 and bid_suit != open_suit:
            return '2_level_new_suit'

        return 'unknown'

    def _classify_rebid(self, bid: str, opening: str, prior_auction: List[str]) -> str:
        """Classify opener's rebid."""
        if not opening or not bid:
            return 'unknown'

        try:
            open_level = int(opening[0])
            bid_level = int(bid[0])
            open_suit = opening[1:] if len(opening) > 1 else ''
            bid_suit = bid[1:] if len(bid) > 1 else ''
        except (ValueError, IndexError):
            return 'unknown'

        # SPECIAL CASE: Stayman response (2♦/2♥/2♠ after 1NT-2♣)
        # These are NOT reverses - they just show 4-card majors within 15-17 range
        if opening in ['1NT', '2NT'] and '2♣' in prior_auction:
            if bid in ['2♦', '2♥', '2♠']:
                return 'stayman_response'

        # SPECIAL CASE: Transfer completion (2♥/2♠ after 1NT-2♦/2♥)
        # These are mandatory completions, not showing extra values
        if opening == '1NT':
            if '2♦' in prior_auction and bid == '2♥':
                return 'transfer_completion'
            if '2♥' in prior_auction and bid == '2♠':
                return 'transfer_completion'

        # NT rebid
        if 'NT' in bid:
            if bid == '1NT':
                return '1NT_rebid'
            elif bid == '2NT':
                return '2NT_rebid'
            elif bid == '3NT':
                return 'game_bid'

        # Same suit rebid
        if bid_suit == open_suit:
            if bid_level == open_level + 1:
                return 'minimum_rebid'
            elif bid_level >= open_level + 2:
                return 'jump_rebid'

        # New suit - check for reverse
        if bid_suit != open_suit and bid_level == 2:
            suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
            if suit_rank.get(bid_suit, 0) > suit_rank.get(open_suit, 0):
                return 'reverse'
            return 'minimum_rebid'

        # Game bids
        if bid_level >= 4:
            return 'game_bid'

        return 'minimum_rebid'  # Default conservative


# Singleton analyzer instance
_analyzer = AuctionAnalyzer()


def analyze_auction_context(auction_history: List[str], positions: List[str],
                           my_index: int) -> AuctionContext:
    """
    Convenience function to analyze auction and get context.

    This is the main entry point for other modules to get auction context.
    """
    return _analyzer.analyze_auction(auction_history, positions, my_index)
