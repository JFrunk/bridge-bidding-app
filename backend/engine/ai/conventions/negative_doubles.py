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

        opening_bid = features['auction_features']['opening_bid']
        # The overcall is the last non-pass bid in the history (excluding opening)
        auction_history = features['auction_history']
        overcall = None
        for bid in reversed(auction_history):
            if bid != 'Pass' and bid != opening_bid:
                overcall = bid
                break

        if not overcall:
            return None

        # Determine overcall level for HCP requirements
        try:
            overcall_level = int(overcall[0])
        except (ValueError, IndexError):
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
        Applicable if partner opened, RHO overcalled, and it's our first bid.

        Valid negative double situations:
        - 1♣ - (1♠) - X         (direct position)
        - 1♣ - (1♠) - Pass - (Pass) - X (balancing position)
        """
        auction = features['auction_features']
        my_index = features['my_index']
        positions = features['positions']
        auction_history = features['auction_history']

        # Check my bids
        my_bids = [bid for i, bid in enumerate(auction_history)
                   if positions[i % 4] == positions[my_index] and bid != 'Pass']

        # Must be our first non-pass bid
        if len(my_bids) > 0:
            return False

        # Partner must have opened
        if auction['opener_relationship'] != 'Partner':
            return False

        # There must be at least 2 non-pass bids (partner's opening + opponent's overcall)
        non_pass_bids = [b for b in auction_history if b != 'Pass']
        if len(non_pass_bids) < 2:
            return False

        # The most recent non-pass bid (excluding ours) must be an opponent's overcall
        # This ensures we're responding to interference, not just to partner's opening
        opening_bid = auction['opening_bid']
        for bid in reversed(auction_history):
            if bid != 'Pass' and bid != opening_bid:
                # Found the overcall - this is valid
                return True

        return False