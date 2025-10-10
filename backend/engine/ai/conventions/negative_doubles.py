from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class NegativeDoubleConvention(ConventionModule):
    """
    Playbook for making a Negative Double.
    This is used by the responder after an opponent's overcall.
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation function for Negative Doubles."""
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