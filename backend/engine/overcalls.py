from engine.hand import Hand
from typing import Optional, Tuple, Dict

class OvercallModule:
    """Playbook for making overcalls, now including 2-level overcalls."""

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if not self._is_applicable(features):
            return None

        # This module does not handle weak jump overcalls, that is in preempts.
        
        # Check for a standard overcall
        overcall_bid = self._get_overcall_bid(hand, features)
        if overcall_bid:
            return overcall_bill
            
        return None

    def _is_applicable(self, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != "Pass"]
        return (auction_features.get('opener_relationship') == 'Opponent' and
                len(non_pass_bids) == 1)

    def _get_overcall_bid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if not (8 <= hand.hcp <= 16):
            return None # Points not in range for a simple overcall

        opponent_bid = features['auction_features']['opening_bid']
        
        # Find the best 5+ card suit to bid
        for bid_level in [1, 2]: # Check for 1-level then 2-level overcalls
            for suit in ['♠', '♥', '♦', '♣']:
                if hand.suit_lengths[suit] >= 5:
                    potential_bid = f"{bid_level}{suit}"
                    # Simple legality check (is my bid higher than opponent's?)
                    if self._is_bid_higher(potential_bid, opponent_bid):
                        suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond', '♣': 'Club'}[suit]
                        return (potential_bid, f"Overcall showing 8-16 HCP and a 5+ card {suit_name} suit.")
        
        return None

    def _is_bid_higher(self, my_bid: str, other_bid: str) -> bool:
        """Helper to check if my_bid is higher than other_bid."""
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}
        my_level, my_suit = int(my_bid[0]), my_bid[1:]
        other_level, other_suit = int(other_bid[0]), other_bid[1:]
        
        if my_level > other_level: return True
        if my_level == other_level and suit_rank.get(my_suit, 0) > suit_rank.get(other_suit, 0):
            return True
        return False