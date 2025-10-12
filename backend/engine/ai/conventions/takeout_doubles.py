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
        """
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
        """
        # Rule 1: Must have opening strength (SAYC standard is 12+ HCP).
        if hand.hcp < 12:
            return False

        # Determine which suit we're doubling
        # In competitive auctions, we double the LAST suit bid by opponents, not necessarily the opening
        opponent_suit = self._get_doubled_suit(features)
        if not opponent_suit:
            return False

        # SPECIAL CASE: Very strong balanced hand (19+ HCP)
        # These hands are too strong for 1NT overcall (15-18) but too balanced for suit overcall
        # Solution: Double now, bid NT later to show 19-21 HCP
        if hand.hcp >= 19 and hand.is_balanced:
            # Just need a stopper in opponent's suit (not shortness)
            return True  # Will double and bid NT next round

        # NORMAL TAKEOUT DOUBLE RULES:
        # Rule 2: Must be short in the opponent's suit (0, 1, or 2 cards).
        if hand.suit_lengths.get(opponent_suit, 0) > 2:
            return False

        # Rule 3: Must have at least 3-card support for all unbid suits.
        all_suits = {'♠', '♥', '♦', '♣'}
        unbid_suits = all_suits - {opponent_suit}

        for suit in unbid_suits:
            if hand.suit_lengths.get(suit, 0) < 3:
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