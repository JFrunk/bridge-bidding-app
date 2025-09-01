from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class PreemptConvention(ConventionModule):
    def get_constraints(self) -> Dict:
        """Defines the requirements for a hand to make a preemptive bid."""
        return {
            'hcp_range': (6, 10),
            'suit_length_req': (['♦', '♥', '♠'], 6, 'any_of') 
        }

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if self._is_opening_preempt_applicable(features):
            return self._get_opening_preempt(hand)
        if self._is_response_applicable(features):
            return self._get_response_to_preempt(hand, features)
        return None
        
    def _is_opening_preempt_applicable(self, features: Dict) -> bool:
        return not features.get('auction_features', {}).get('opener')
        
    def _get_opening_preempt(self, hand: Hand) -> Optional[Tuple[str, str]]:
        constraints = self.get_constraints()
        hcp_range = constraints['hcp_range']
        if not (hcp_range[0] <= hand.hcp <= hcp_range[1]): return None
        
        suits, min_length, _ = constraints['suit_length_req']
        for suit in suits:
            if hand.suit_lengths[suit] >= min_length:
                honors = {'A', 'K', 'Q', 'J', 'T'}
                suit_cards = [card.rank for card in hand.cards if card.suit == suit]
                if sum(1 for rank in suit_cards if rank in honors) >= 2:
                    suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond'}[suit]
                    return (f"2{suit}", f"Weak Two bid. Shows 6-10 HCP and a 6-card {suit_name} suit.")
        return None
        
    def _is_response_applicable(self, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')
        return (auction_features.get('opener_relationship') == 'Partner' and opening_bid in ['2♦', '2♥', '2♠'])
        
    def _get_response_to_preempt(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        opening_bid = features['auction_features']['opening_bid']
        preempt_suit = opening_bid[1]
        if hand.total_points >= 15: return ("2NT", "Ogust Convention.")
        if hand.suit_lengths[preempt_suit] >= 3:
            if hand.total_points >= 17: return (f"4{preempt_suit}", "Raising to game.")
            if hand.total_points >= 11: return (f"3{preempt_suit}", "Constructive raise.")
        return ("Pass", "Not enough strength or fit to respond to the preempt.")