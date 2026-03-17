from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from utils.seats import partner as get_partner_seat
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
        Responsive double: After opponents bid-and-raise and partner doubled/overcalled.
        Shows competitive values with support for unbid suits.

        Two variants by opponent suit type:
        1. Over MINOR raise (1♦-X-2♦-?): Shows 4-4 in majors, 8+ HCP
        2. Over MAJOR raise (1♥-X-2♥-?): Shows 10+ HCP with unbid suit values

        Level constraint: Only through 3-level (at 4+ level, pass or bid naturally).

        Examples:
        - 1♦ - (X) - 2♦ - X   → 4-4 majors, 8+ HCP
        - 1♥ - (X) - 2♥ - X   → unbid suits, 10+ HCP
        - 1♠ - (2♣) - 2♠ - X  → also works after partner overcalled (not just doubled)
        """
        auction_features = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])
        positions = features.get('positions', [])
        my_index = features.get('my_index', 0)
        my_pos_str = positions[my_index]

        # Get partner's position
        partner_pos_str = self._get_partner_position(my_pos_str)

        # Need at least 3 bids: opponent opens, partner acts, opponent raises
        if len(auction_history) < 3:
            return None

        # Check if partner made a takeout double or overcall
        partner_acted = False
        for i, bid in enumerate(auction_history):
            if positions[i % 4] == partner_pos_str and bid not in ['Pass', 'XX']:
                partner_acted = True
                break

        if not partner_acted:
            return None

        # Check if last bid was a raise by opponent (same suit as opener's, at higher level)
        last_bid = auction_history[-1]
        last_bidder_pos = positions[(len(auction_history) - 1) % 4]

        # Last bidder must be opponent (RHO)
        if last_bidder_pos in [my_pos_str, partner_pos_str]:
            return None

        # Last bid must be a suit bid
        if not last_bid or len(last_bid) < 2 or last_bid in ['Pass', 'X', 'XX']:
            return None
        last_suit = last_bid[1] if last_bid[1] in {'♠', '♥', '♦', '♣'} else None
        if not last_suit:
            return None

        # Opening bid must be a suit bid
        opening_bid = auction_features.get('opening_bid', '')
        if not opening_bid or len(opening_bid) < 2:
            return None
        opening_suit = opening_bid[1] if opening_bid[1] in {'♠', '♥', '♦', '♣'} else None
        if not opening_suit:
            return None

        # Must be a raise (same suit)
        if opening_suit != last_suit:
            return None

        # Level constraint: only through 3-level
        raise_level = int(last_bid[0]) if last_bid[0].isdigit() else 0
        if raise_level > 3:
            return None

        # Determine if opponents' suit is a major or minor
        is_major_raise = opening_suit in {'♥', '♠'}
        is_minor_raise = opening_suit in {'♦', '♣'}

        # If we have a 5+ card unbid suit, bid it directly instead of doubling
        unbid_suits = [s for s in ['♠', '♥', '♦', '♣'] if s != opening_suit]
        max_unbid_length = max(hand.suit_lengths.get(s, 0) for s in unbid_suits)
        if max_unbid_length >= 5:
            return None

        if is_minor_raise:
            # Over minor raise: shows 4-4 in both majors
            h_len = hand.suit_lengths.get('♥', 0)
            s_len = hand.suit_lengths.get('♠', 0)

            if h_len < 4 or s_len < 4:
                return None  # Need 4-4 in majors

            if hand.hcp < 8:
                return None  # 8+ HCP required

            return ("X", f"Responsive double showing 4-4 in both majors ({hand.hcp} HCP). "
                        f"Partner picks the major.",
                    {'bypass_suit_length': True, 'bypass_hcp': True, 'convention': 'responsive_double'})

        elif is_major_raise:
            # Over major raise: shows values in unbid suits
            if hand.hcp < 10:
                return None  # 10+ HCP required (competitive strength)

            # Should have at least 4 cards in 2 of the 3 unbid suits
            unbid_with_support = sum(1 for s in unbid_suits if hand.suit_lengths.get(s, 0) >= 4)
            if unbid_with_support < 2:
                return None

            return ("X", f"Responsive double showing {hand.hcp} HCP with values in unbid suits. "
                        f"Partner picks the best strain.",
                    {'bypass_suit_length': True, 'bypass_hcp': True, 'convention': 'responsive_double'})

        return None

    def _get_partner_position(self, my_pos: str) -> str:
        """Returns partner's position given my position.

        Uses utils.seats.partner() for the mapping, but expands
        single-letter results to full names when the input is a full name,
        since feature_extractor positions use full names.
        """
        short = get_partner_seat(my_pos)
        expand = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
        if len(my_pos) > 1:
            return expand.get(short, short)
        return short
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("negative_doubles", NegativeDoubleConvention())
