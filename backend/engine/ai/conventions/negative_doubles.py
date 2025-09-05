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

        # Standard rule: 6+ points and typically 4 cards in any unbid major.
        if hand.hcp >= 6:
            opening_bid = features['auction_features']['opening_bid']
            # The overcall is the last non-pass bid in the history
            overcall = next((b for b in reversed(features['auction_history']) if b != 'Pass'), None)

            if not overcall:
                return None
            
            # Check for unbid hearts
            if '♥' not in opening_bid and '♥' not in overcall and hand.suit_lengths['♥'] >= 4:
                return ("X", "Negative Double, showing 4+ hearts and 6+ points.")
            # Check for unbid spades
            if '♠' not in opening_bid and '♠' not in overcall and hand.suit_lengths['♠'] >= 4:
                return ("X", "Negative Double, showing 4+ spades and 6+ points.")

        return None

    def _is_applicable(self, features: Dict) -> bool:
        """Applicable if partner opened, RHO overcalled, and it's our first bid."""
        auction = features['auction_features']
        my_bids = [bid for i, bid in enumerate(features['auction_history']) if features['positions'][i % 4] == features['my_index']]
        
        # Must be exactly two non-pass bids in the auction (e.g., 1C - 1S)
        non_pass_bids = [b for b in features['auction_history'] if b != 'Pass']
        return (len(non_pass_bids) == 2 and
                auction['opener_relationship'] == 'Partner' and
                len(my_bids) == 0)