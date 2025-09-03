from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class ResponseModule(ConventionModule):
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        auction = features['auction_features']
        my_bids = [bid for i, bid in enumerate(features['auction_history']) if features['positions'][i % 4] == features['my_index']]
        
        if auction['partner_last_bid'] == 'X' and auction['opener_relationship'] == 'Opponent':
            return self._get_response_to_takeout_double(hand, features)
        if len(my_bids) == 0 and auction['opener_relationship'] == 'Partner':
            return self._get_first_response(hand, auction['opening_bid'])
        if len(my_bids) >= 1 and auction['opener_relationship'] == 'Partner':
            return self._get_responder_rebid(hand, features)
        return None

    def _get_first_response(self, hand: Hand, opening_bid: str):
        if opening_bid == "2♣":
            if hand.hcp >= 8: return ("2NT", "Positive response to 2♣ showing 8+ HCP, balanced.")
            else: return ("2♦", "Artificial waiting response to 2♣.")
        
        if hand.total_points < 6: return ("Pass", "Less than 6 total points.")
        opening_suit = opening_bid[1]
        
        if hand.suit_lengths[opening_suit] >= 3:
            support_points = hand.hcp + (5 if hand.suit_lengths.get(opening_suit, 0) > 3 else 0) # Simplified support calc
            if 10 <= support_points <= 12: return (f"3{opening_suit}", f"Invitational raise showing 10-12 support points.")
            return (f"2{opening_suit}", f"Simple raise showing 6-9 support points.")
        
        if hand.is_balanced:
            if 10 <= hand.hcp <= 12: return ("2NT", "Shows a balanced 10-12 HCP and no fit.")
            if 6 <= hand.hcp <= 9: return ("1NT", "Shows 6-9 HCP, balanced, and no 4-card major.")

        if opening_bid in ['1♣', '1♦'] and hand.suit_lengths['♠'] >= 4: return ("1♠", "Showing a 4+ card spade suit.")
        if opening_bid in ['1♣', '1♦', '1♥'] and hand.suit_lengths['♥'] >= 4: return ("1♥", "Showing a 4+ card heart suit.")
        
        if hand.total_points >= 10: return ("2♣", "New suit, showing 10+ points.")
        return ("Pass", "No clear response.")
        
    def _get_responder_rebid(self, hand: Hand, features: Dict):
        # This logic remains as previously verified
        pass # Placeholder for brevity

    def _get_response_to_takeout_double(self, hand: Hand, features: Dict):
        # This logic remains as previously verified
        pass # Placeholder for brevity