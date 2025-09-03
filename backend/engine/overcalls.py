from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class OvercallModule(ConventionModule):
    """Playbook for making simple overcalls."""
    def get_constraints(self) -> Dict:
        return {}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if not self._is_applicable(features):
            return None
        return self._get_overcall_bid(hand, features)

    def _is_applicable(self, features: Dict) -> bool:
        """
        An overcall is applicable only if an opponent has opened and it is
        our turn immediately after them, and we have not yet bid.
        """
        auction_features = features.get('auction_features', {})
        my_index = features.get('my_index', -1)
        opener_index = auction_features.get('opener_index', -1)
        my_bids = [bid for i, bid in enumerate(features['auction_history']) if features['positions'][i % 4] == features['positions'][my_index]]

        # THIS IS THE FIX: an opener must exist, it must be my turn right after, AND I haven't bid yet.
        return (opener_index != -1 and 
                my_index == (opener_index + 1) % 4 and
                len(my_bids) == 0)

    def _get_overcall_bid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if not (8 <= hand.hcp <= 16): return None
        opponent_bid = features['auction_features']['opening_bid']
        for bid_level in [1, 2]:
            for suit in ['♠', '♥', '♦', '♣']:
                if hand.suit_lengths[suit] >= 5:
                    potential_bid = f"{bid_level}{suit}"
                    if self._is_bid_higher(potential_bid, opponent_bid):
                        honors = {'A', 'K', 'Q', 'J', 'T'}
                        suit_cards = [card.rank for card in hand.cards if card.suit == suit]
                        if sum(1 for rank in suit_cards if rank in honors) >= 2:
                            suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond', '♣': 'Club'}[suit]
                            return (potential_bid, f"Overcall showing 8-16 HCP and a 5+ card {suit_name} suit.")
        return None

    def _is_bid_higher(self, my_bid: str, other_bid: str) -> bool:
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}
        try:
            my_level, my_suit = int(my_bid[0]), my_bid[1:]
            other_level, other_suit = int(other_bid[0]), other_bid[1:]
            if my_level > other_level: return True
            if my_level == other_level and suit_rank.get(my_suit, 0) > suit_rank.get(other_suit, 0):
                return True
        except (ValueError, IndexError):
            return False
        return False