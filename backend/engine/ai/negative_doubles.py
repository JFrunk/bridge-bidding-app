from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class NegativeDoubleConvention(ConventionModule):
    """
    Playbook for making a Negative Double.
    This is used by the responder after an opponent's overcall.
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if not self._is_applicable(features):
            return None

        # Standard rule: 6+ points and 4+ cards in an unbid major.
        if hand.hcp >= 6:
            opening_bid = features['auction_features']['opening_bid']
            # The overcall is the last bid in the history
            overcall = features['auction_history'][-1]
            
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
        
        # Must be exactly two bids in the auction (e.g., 1C - 1S)
        return (len(features['auction_history']) == 2 and
                auction['opener_relationship'] == 'Partner' and
                len(my_bids) == 0)