from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.ai.feature_extractor import calculate_stoppers
from utils.seats import partner as get_partner_seat
from typing import Optional, Tuple, Dict

SUIT_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
SUIT_NAME = {'♣': 'clubs', '♦': 'diamonds', '♥': 'hearts', '♠': 'spades'}
ALL_SUITS = {'♠', '♥', '♦', '♣'}
FULL_SEAT_NAME = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}


class FourthSuitForcingConvention(ConventionModule):
    """
    Fourth Suit Forcing (FSF) Convention — The Universal Relay

    When three suits have been bid naturally by the partnership, bidding
    the fourth suit is artificial and game-forcing. It does NOT show
    length in that suit. Instead it asks opener to further describe
    their hand.

    Two phases:
    1. Initiation (responder): Bid the 4th suit with 12+ HCP, no fit, no 6+ suit
    2. Response (opener): Priority hierarchy —
       a) 3-card support for responder's major
       b) Stopper in 4th suit → NT
       c) 6+ card rebid of own suit
       d) Min/max signaling
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        auction = features['auction_features']
        opener_rel = auction.get('opener_relationship')

        if opener_rel == 'Partner':
            # I'm the responder — check if I should initiate FSF
            return self._check_fsf_initiation(hand, features)
        elif opener_rel == 'Me':
            # I'm the opener — check if partner bid FSF and I should respond
            return self._check_fsf_response(hand, features)

        return None

    # ------------------------------------------------------------------
    # PHASE 1: Responder initiates FSF
    # ------------------------------------------------------------------

    def _check_fsf_initiation(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Responder bids the 4th suit as an artificial game force.

        Requirements:
        - 3 distinct suits already bid by the partnership
        - 12+ HCP
        - No 4+ fit with partner's last suit
        - No 6+ card suit of our own to rebid
        - This is responder's 2nd bid (exactly 1 prior bid)
        """
        auction_history = features.get('auction_history', [])
        positions = features.get('positions', [])
        my_index = features.get('my_index', 0)
        my_pos = positions[my_index]
        partner_pos = FULL_SEAT_NAME.get(get_partner_seat(my_pos[0]), my_pos)

        # Collect partnership suits and my bids
        suits_bid = set()
        my_bids = []
        partner_suits = []

        for i, bid in enumerate(auction_history):
            bidder = positions[i % 4]
            if bid in ('Pass', 'X', 'XX'):
                continue
            suit = bid[1] if len(bid) >= 2 and bid[1] in ALL_SUITS else None
            if suit and bidder in (my_pos, partner_pos):
                suits_bid.add(suit)
            if suit and bidder == partner_pos:
                partner_suits.append(suit)
            if bidder == my_pos:
                my_bids.append(bid)

        # Must be responder's 2nd turn (exactly 1 prior bid)
        if len(my_bids) != 1:
            return None

        # Need exactly 3 suits bid by partnership
        if len(suits_bid) != 3:
            return None

        # Game-forcing values required
        if hand.hcp < 12:
            return None

        # Identify the fourth suit
        fourth_suit_set = ALL_SUITS - suits_bid
        if len(fourth_suit_set) != 1:
            return None
        fourth_suit = fourth_suit_set.pop()

        # --- Natural alternatives that are better than FSF ---

        # 4+ fit with partner's last suit → raise instead
        if partner_suits:
            if hand.suit_lengths.get(partner_suits[-1], 0) >= 4:
                return None

        # 6+ card suit of our own → rebid instead
        my_first_suit = None
        if my_bids and len(my_bids[0]) >= 2 and my_bids[0][1] in ALL_SUITS:
            my_first_suit = my_bids[0][1]
        if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
            return None

        # --- Calculate FSF bid level ---
        # Find partner's last bid string to determine minimum level
        partner_last_bid_str = None
        for i in range(len(auction_history) - 1, -1, -1):
            bid = auction_history[i]
            if positions[i % 4] == partner_pos and len(bid) >= 2 and bid[1] in ALL_SUITS:
                partner_last_bid_str = bid
                break

        if not partner_last_bid_str:
            return None

        last_level = int(partner_last_bid_str[0])
        last_suit = partner_last_bid_str[1]

        # FSF at cheapest legal level in the 4th suit
        if SUIT_RANK[fourth_suit] > SUIT_RANK[last_suit]:
            fsf_level = last_level
        else:
            fsf_level = last_level + 1

        if fsf_level > 3:
            return None  # Too high

        fsf_bid = f"{fsf_level}{fourth_suit}"
        stoppers = calculate_stoppers(hand)
        stopper_note = "" if stoppers.get(fourth_suit) else " (no stopper)"

        return (
            fsf_bid,
            f"Fourth Suit Forcing - artificial, game-forcing. "
            f"Asks opener to describe hand further. {hand.hcp} HCP{stopper_note}.",
            {'convention': 'fourth_suit_forcing', 'game_forcing': True,
             'bypass_suit_length': True, 'bypass_sanity_check': True}
        )

    # ------------------------------------------------------------------
    # PHASE 2: Opener responds to partner's FSF bid
    # ------------------------------------------------------------------

    def _check_fsf_response(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Opener responds to partner's Fourth Suit Forcing bid.

        Priority hierarchy:
        1. 3-card support for responder's first-bid major → raise
           (min: 3M, max: 4M)
        2. Stopper in 4th suit → NT
           (min: 2NT, max: 3NT)
        3. 6+ card suit → rebid own suit
        4. Min/max signaling (cheapest bid = min, jump = max)
        """
        auction_history = features.get('auction_history', [])
        positions = features.get('positions', [])
        my_index = features.get('my_index', 0)
        my_pos = positions[my_index]
        partner_pos = FULL_SEAT_NAME.get(get_partner_seat(my_pos[0]), my_pos)

        # Collect partnership bid data
        my_bids = []
        partner_bids = []
        my_suits = []
        partner_suits = []

        for i, bid in enumerate(auction_history):
            bidder = positions[i % 4]
            if bid in ('Pass', 'X', 'XX'):
                continue
            suit = bid[1] if len(bid) >= 2 and bid[1] in ALL_SUITS else None

            if bidder == my_pos:
                my_bids.append(bid)
                if suit:
                    my_suits.append(suit)
            elif bidder == partner_pos:
                partner_bids.append(bid)
                if suit:
                    partner_suits.append(suit)

        # Opener must have made exactly 2 bids (open + rebid)
        if len(my_bids) != 2:
            return None

        # Partner must have made exactly 2 bids (response + potential FSF)
        if len(partner_bids) != 2:
            return None

        # Check if partner's last bid is the 4th suit
        last_partner_bid = partner_bids[-1]
        last_partner_suit = (
            last_partner_bid[1]
            if len(last_partner_bid) >= 2 and last_partner_bid[1] in ALL_SUITS
            else None
        )

        if not last_partner_suit:
            return None

        # The 4th suit is a suit not previously bid by the partnership
        # (before partner's last bid, 3 suits should have been bid)
        suits_before_fsf = set()
        for i, bid in enumerate(auction_history):
            bidder = positions[i % 4]
            if bid in ('Pass', 'X', 'XX'):
                continue
            suit = bid[1] if len(bid) >= 2 and bid[1] in ALL_SUITS else None
            if suit and bidder in (my_pos, partner_pos):
                # Stop before partner's last bid
                partner_bid_count = sum(
                    1 for j in range(i + 1)
                    if positions[j % 4] == partner_pos
                    and auction_history[j] not in ('Pass', 'X', 'XX')
                )
                if bidder == partner_pos and partner_bid_count == len(partner_bids):
                    break  # This is the FSF bid itself
                suits_before_fsf.add(suit)

        if len(suits_before_fsf) != 3:
            return None

        fourth_suit = last_partner_suit
        if fourth_suit in suits_before_fsf:
            return None  # Partner rebid an existing suit, not FSF

        # --- Identified FSF. Now respond per priority hierarchy. ---

        # Responder's first-bid suit (the one they want support for)
        responder_first_suit = partner_suits[0] if partner_suits else None
        is_major = responder_first_suit in ('♥', '♠') if responder_first_suit else False

        # Min/max classification
        is_max = hand.hcp >= 14  # 14+ = maximum, 12-13 = minimum

        # PRIORITY 1: 3-card support for responder's first-bid major
        if responder_first_suit and is_major:
            support_len = hand.suit_lengths.get(responder_first_suit, 0)
            if support_len >= 3:
                if is_max:
                    bid = f"4{responder_first_suit}"
                    strength = "maximum"
                else:
                    bid = f"3{responder_first_suit}"
                    strength = "minimum"
                return (
                    bid,
                    f"FSF response: 3-card {SUIT_NAME.get(responder_first_suit, '')} "
                    f"support, {strength} ({hand.hcp} HCP).",
                    {'convention': 'fourth_suit_forcing', 'bypass_sanity_check': True}
                )

        # PRIORITY 2: Stopper in 4th suit → NT
        stoppers = calculate_stoppers(hand)
        if stoppers.get(fourth_suit, False):
            if is_max:
                bid = "3NT"
                strength = "maximum"
            else:
                bid = "2NT"
                strength = "minimum"
            return (
                bid,
                f"FSF response: {SUIT_NAME.get(fourth_suit, '')} stopper, "
                f"{strength} ({hand.hcp} HCP).",
                {'convention': 'fourth_suit_forcing', 'bypass_sanity_check': True}
            )

        # PRIORITY 3: 6+ card suit → rebid own suit
        my_opening_suit = my_suits[0] if my_suits else None
        if my_opening_suit:
            if hand.suit_lengths.get(my_opening_suit, 0) >= 6:
                # Rebid at cheapest level
                rebid_level = 3  # After FSF at 2-level, rebid at 3
                bid = f"{rebid_level}{my_opening_suit}"
                return (
                    bid,
                    f"FSF response: rebid 6-card {SUIT_NAME.get(my_opening_suit, '')} "
                    f"suit ({hand.hcp} HCP).",
                    {'convention': 'fourth_suit_forcing', 'bypass_sanity_check': True}
                )

        # PRIORITY 4: Min/max signaling (no support, no stopper, no long suit)
        # Bid cheapest available bid to show minimum, jump to show maximum
        if responder_first_suit:
            if is_max:
                bid = f"3{responder_first_suit}"
            else:
                bid = f"2{responder_first_suit}"
            strength = "maximum" if is_max else "minimum"
            return (
                bid,
                f"FSF response: {strength}, no 3-card support, no stopper "
                f"({hand.hcp} HCP).",
                {'convention': 'fourth_suit_forcing', 'bypass_sanity_check': True}
            )

        return None

    def get_constraints(self) -> Dict:
        return {
            'description': 'Fourth Suit Forcing (game-forcing, no clear direction)',
            'min_hcp': 12,
            'max_hcp': 20,
            'required_distribution': 'No 8-card fit found, 12+ HCP',
        }


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("fourth_suit_forcing", FourthSuitForcingConvention())
