from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class NegativeDoubleConvention(ConventionModule):
    """
    Playbook for making a Negative Double.
    This is used by the responder after an opponent's overcall.
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation function for Negative Doubles and Responsive Doubles."""

        # Check for responsive double first (partner doubled, RHO raised)
        responsive_double = self._check_responsive_double(hand, features)
        if responsive_double:
            return responsive_double

        if not self._is_applicable(features):
            return None

        # Get interference information from features
        interference = features['auction_features'].get('interference', {})
        opening_bid = features['auction_features']['opening_bid']
        overcall = interference.get('bid')
        overcall_level = interference.get('level')

        if not overcall or overcall_level is None:
            return None

        # Level-adjusted HCP requirements (SAYC standard)
        if overcall_level <= 2:
            min_hcp = 6  # Through 2♠: 6+ HCP (responding values)
        elif overcall_level == 3:
            min_hcp = 8  # 3-level: 8-10+ HCP (invitational values)
        else:
            min_hcp = 12  # 4-level+: 12+ HCP (game-forcing values)

        if hand.hcp < min_hcp:
            return None

        # Check for unbid hearts
        if '♥' not in opening_bid and '♥' not in overcall and hand.suit_lengths['♥'] >= 4:
            return ("X", f"Negative Double, showing 4+ hearts and {hand.hcp} points.")
        # Check for unbid spades
        if '♠' not in opening_bid and '♠' not in overcall and hand.suit_lengths['♠'] >= 4:
            return ("X", f"Negative Double, showing 4+ spades and {hand.hcp} points.")

        return None

    def _is_applicable(self, features: Dict) -> bool:
        """
        Applicable if partner opened, opponent interfered, and it's our first bid.

        Valid negative double situations:
        - 1♣ - (1♠) - X         (direct position)
        - 1♣ - (1♠) - Pass - (Pass) - X (balancing position)
        """
        auction = features['auction_features']
        my_index = features['my_index']
        positions = features['positions']
        auction_history = features['auction_history']
        interference = auction.get('interference', {})

        # Check my bids
        my_bids = [bid for i, bid in enumerate(auction_history)
                   if positions[i % 4] == positions[my_index] and bid != 'Pass']

        # Must be our first non-pass bid
        if len(my_bids) > 0:
            return False

        # Partner must have opened
        if auction['opener_relationship'] != 'Partner':
            return False

        # There must be interference from an opponent
        if not interference.get('present'):
            return False

        # The interference must be a suit overcall (not X or XX for now)
        if interference.get('type') not in ['suit_overcall', 'nt_overcall']:
            return False

        return True

    def _check_responsive_double(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Check for responsive double: Partner made takeout double, RHO raised, we double.
        Shows competitive values with no clear suit to bid.

        Example: 1♥ - (X) - 2♥ - (X)
        Partner doubled for takeout, RHO raised to 2♥, we double responsively.
        """
        auction_features = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])
        positions = features.get('positions', [])
        my_index = features.get('my_index', 0)
        my_pos_str = positions[my_index]

        # Get partner's position
        partner_pos_str = self._get_partner_position(my_pos_str)

        # Need at least 4 bids in auction
        if len(auction_history) < 4:
            return None

        # Check if partner made a takeout double
        partner_doubled = False
        for i, bid in enumerate(auction_history):
            if positions[i % 4] == partner_pos_str and bid == 'X':
                partner_doubled = True
                break

        if not partner_doubled:
            return None

        # Check if last bid was a raise by opponent
        last_bid = auction_history[-1]
        last_bidder_pos = positions[(len(auction_history) - 1) % 4]

        # Last bidder must be opponent (RHO)
        if last_bidder_pos in [my_pos_str, partner_pos_str]:
            return None

        # Last bid should be a raise (same suit as opener's, higher level)
        opening_bid = auction_features.get('opening_bid', '')
        if not opening_bid or len(opening_bid) < 2 or len(last_bid) < 2:
            return None

        opening_suit = opening_bid[1]
        last_suit = last_bid[1] if last_bid[1] in {'♠', '♥', '♦', '♣'} else None

        # Must be same suit (raise)
        if opening_suit != last_suit:
            return None

        # Need 6-10 HCP for responsive double (competitive values)
        # With more, we'd bid a suit or NT
        if hand.hcp < 6 or hand.hcp > 10:
            return None

        # Should have some values in unbid suits but no clear 5-card suit
        # (Otherwise we'd bid the suit directly)
        max_unbid_length = 0
        for suit in ['♠', '♥', '♦', '♣']:
            if suit != opening_suit:
                max_unbid_length = max(max_unbid_length, hand.suit_lengths.get(suit, 0))

        # If we have 5+ cards in unbid suit, we'd bid it instead of doubling
        if max_unbid_length >= 5:
            return None

        return ("X", f"Responsive double showing {hand.hcp} HCP with no clear suit to bid (asking partner to pick).")

    def _get_partner_position(self, my_pos: str) -> str:
        """Returns partner's position given my position."""
        partners = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E',
                   'North': 'South', 'South': 'North', 'East': 'West', 'West': 'East'}
        return partners.get(my_pos, '')