from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class TakeoutDoubleConvention(ConventionModule):
    """
    Playbook for making a Takeout Double, based on the provided flowchart.
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Main evaluation function. Checks if a takeout double is the correct action.
        Also handles support doubles.
        """
        # Check for support double first (opener showing 3-card support)
        support_double = self._check_support_double(hand, features)
        if support_double:
            return support_double

        if not self._is_applicable(features):
            return None

        if self._hand_qualifies(hand, features):
            # Provide appropriate explanation based on hand strength
            if hand.hcp >= 19 and hand.is_balanced:
                return ("X", f"Takeout Double with {hand.hcp} HCP (too strong for 1NT overcall). Planning to bid NT next to show 19+ HCP.")
            else:
                return ("X", f"Takeout Double showing {hand.hcp}+ points and support for unbid suits.")

        return None

    def _is_applicable(self, features: Dict) -> bool:
        """
        A takeout double is applicable if an opponent has opened (but not in NT)
        and our side has not yet bid.
        Works in direct seat (immediately after opening) or later in competitive auctions.
        """
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid', '')

        # Must be a competitive auction (opponent opened)
        if auction_features.get('opener_relationship') != 'Opponent':
            return False

        # Rule: Opening bid must not be No-Trump (double of NT is penalty, not takeout)
        if not opening_bid or 'NT' in opening_bid:
            return False

        # Rule: Our side (me and partner) must not have made any non-pass bids yet
        # Check my bids
        my_pos_str = features['positions'][features['my_index']]
        my_bids = [bid for i, bid in enumerate(features['auction_history'])
                   if features['positions'][i % 4] == my_pos_str]
        my_non_pass_bids = [bid for bid in my_bids if bid != 'Pass']

        if len(my_non_pass_bids) > 0:
            return False  # I've already bid

        # Check partner's bids
        partner_last_bid = auction_features.get('partner_last_bid')
        if partner_last_bid and partner_last_bid not in ['Pass', None]:
            return False  # Partner already bid

        return True

    def _hand_qualifies(self, hand: Hand, features: Dict) -> bool:
        """
        Checks for 12+ points (SAYC standard), shortness in opponent's suit, and support for unbid suits.

        Also handles STRONG balanced hands (17+ HCP) that are too strong for 1NT overcall.
        These hands double first and bid NT later to show 19-21 HCP.

        In BALANCING SEAT (passout seat), HCP requirements are reduced to 8+ HCP
        because partner has already passed showing some values.
        """
        # Determine if we're in balancing seat (opponent opened, partner passed, opponent passed)
        is_balancing = self._is_balancing_seat(features)

        # Rule 1: Must have opening strength (SAYC standard is 12+ HCP).
        # In balancing seat, only 8+ HCP is needed (partner has passed showing values)
        min_hcp = 8 if is_balancing else 12
        if hand.hcp < min_hcp:
            return False

        # Determine which suit we're doubling
        # In competitive auctions, we double the LAST suit bid by opponents, not necessarily the opening
        opponent_suit = self._get_doubled_suit(features)
        if not opponent_suit:
            return False

        # SPECIAL CASE 1: Very strong balanced hand (19+ HCP)
        # These hands are too strong for 1NT overcall (15-18) but too balanced for suit overcall
        # Solution: Double now, bid NT later to show 19-21 HCP
        if hand.hcp >= 19 and hand.is_balanced:
            return True  # Will double and bid NT next round

        # SPECIAL CASE 2: Strong hand in balancing seat (15+ HCP)
        # In balancing seat, partner may be trapped with length in opponent's suit
        # With 15+ HCP, we double even with length in their suit to protect partner
        if is_balancing and hand.hcp >= 15:
            return True

        # NORMAL TAKEOUT DOUBLE RULES:
        opponent_length = hand.suit_lengths.get(opponent_suit, 0)

        # Rule 2: Must be short in the opponent's suit (0, 1, or 2 cards).
        # Exception: In balancing seat with 12+ HCP, can have 3 cards in their suit
        if opponent_length > 2:
            if not (is_balancing and hand.hcp >= 12 and opponent_length == 3):
                return False

        # Rule 3: Support for unbid suits
        # Classic shape: 3+ cards in all 3 unbid suits
        # Relaxed: 3+ cards in at least 2 unbid suits (must include a major if possible)
        all_suits = {'♠', '♥', '♦', '♣'}
        unbid_suits = all_suits - {opponent_suit}

        suits_with_support = sum(1 for suit in unbid_suits if hand.suit_lengths.get(suit, 0) >= 3)

        # Need at least 2 suits with 3+ card support
        if suits_with_support < 2:
            return False

        return True

    def _get_doubled_suit(self, features: Dict) -> Optional[str]:
        """
        Determines which suit we would be doubling.
        In a takeout double, we're asking partner to bid, so we need to be short
        in the LAST suit bid by opponents (not necessarily the opening bid).

        For example: 1♦ - Pass - 1♥ - X
        We're doubling hearts (the last bid), not diamonds (the opening).
        """
        auction_history = features.get('auction_history', [])
        positions = features.get('positions', [])
        my_index = features.get('my_index', 0)
        my_pos_str = positions[my_index]

        # Determine partner position
        partner_pos_str = self._get_partner_position(my_pos_str)

        # Walk backwards through the auction to find the last suit bid by an opponent
        for i in range(len(auction_history) - 1, -1, -1):
            bid = auction_history[i]
            bidder_pos = positions[i % 4]

            # Skip our bids (me and partner)
            if bidder_pos in [my_pos_str, partner_pos_str]:
                continue

            # Check if this is a suit bid (not Pass, X, XX, or NT)
            if bid and bid != 'Pass' and 'X' not in bid and 'NT' not in bid:
                # Extract suit from bid (e.g., "1♥" -> "♥", "4♠" -> "♠")
                if len(bid) >= 2:
                    suit = bid[1]
                    if suit in {'♠', '♥', '♦', '♣'}:
                        return suit

        # Fallback to opening bid suit if we can't find a recent suit bid
        opening_bid = features.get('auction_features', {}).get('opening_bid', '')
        if opening_bid and len(opening_bid) >= 2:
            return opening_bid[1]

        return None

    def _get_partner_position(self, my_pos: str) -> str:
        """Returns partner's position given my position."""
        partners = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
        return partners.get(my_pos, '')

    def _is_balancing_seat(self, features: Dict) -> bool:
        """
        Check if we're in balancing (passout) seat.

        Balancing seat is when:
        - Opponent opened
        - Partner passed
        - RHO passed
        - If we pass, the auction is over

        Example: 1♥ - Pass - Pass - ?
        We're in balancing seat - the auction will die if we pass.
        """
        auction_history = features.get('auction_history', [])

        if len(auction_history) < 3:
            return False

        # Check if the last two bids before us were passes
        if auction_history[-1] != 'Pass' or auction_history[-2] != 'Pass':
            return False

        # Check if there was only one substantive bid before the passes
        non_pass_bids = [b for b in auction_history if b != 'Pass']
        if len(non_pass_bids) != 1:
            return False  # More than one bid = not simple balancing

        # The one bid should be from an opponent (opening bid)
        return True

    def _check_support_double(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Check for support double: Opener doubles after partner responds and RHO overcalls.
        Shows exactly 3-card support for partner's suit.

        Example: 1♣ - (P) - 1♥ - (1♠) - X
        Opener doubles to show 3-card heart support (with 4+, would raise).
        """
        auction_features = features.get('auction_features', {})

        # Must be opener (I opened the bidding)
        if auction_features.get('opener_relationship') != 'Me':
            return None

        # Get auction history
        auction_history = features.get('auction_history', [])
        positions = features.get('positions', [])
        my_index = features.get('my_index', 0)
        my_pos_str = positions[my_index]
        partner_pos_str = self._get_partner_position(my_pos_str)

        # Need at least 4 bids: 1) I open, 2) opponent passes/bids, 3) partner responds, 4) RHO overcalls
        if len(auction_history) < 4:
            return None

        # Find partner's last bid (should be a suit response)
        partner_suit = None
        for i, bid in enumerate(auction_history):
            if positions[i % 4] == partner_pos_str and bid != 'Pass':
                # Check if it's a suit bid
                if len(bid) >= 2 and bid[1] in {'♠', '♥', '♦', '♣'} and 'NT' not in bid:
                    partner_suit = bid[1]

        if not partner_suit:
            return None  # Partner didn't bid a suit

        # Check last bid was an opponent's overcall
        last_bid = auction_history[-1]
        last_bidder_pos = positions[(len(auction_history) - 1) % 4]

        # Last bidder must be an opponent
        if last_bidder_pos in [my_pos_str, partner_pos_str]:
            return None

        # Last bid must be a suit overcall (not Pass, X, NT)
        if last_bid == 'Pass' or 'X' in last_bid or 'NT' in last_bid:
            return None

        # Check support: exactly 3 cards in partner's suit
        partner_support = hand.suit_lengths.get(partner_suit, 0)

        if partner_support == 3:
            suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}[partner_suit]
            return ("X", f"Support double showing exactly 3-card {suit_name} support (would raise with 4+).")

        return None
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("takeout_doubles", TakeoutDoubleConvention())
