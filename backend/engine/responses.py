from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class ResponseModule(ConventionModule):
    """
    Playbook for all of the responder's natural bids, based on the user's flowcharts.
    """
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        auction = features['auction_features']
        opening_bid = auction.get('opening_bid')
        if not opening_bid or auction.get('opener_relationship') != 'Partner':
            return None # Not a response situation

        my_bids = [bid for i, bid in enumerate(features['auction_history']) if features['positions'][i % 4] == features['my_index']]
        
        if len(my_bids) == 0:
            return self._get_first_response(hand, opening_bid)
        else:
            return self._get_responder_rebid(hand, features)

    def _calculate_support_points(self, hand: Hand, trump_suit: str) -> int:
        points = hand.hcp
        for suit, length in hand.suit_lengths.items():
            if suit != trump_suit:
                if length == 1: points += 2
                if length == 0: points += 3
        return points

    def _get_first_response(self, hand: Hand, opening_bid: str):
        if opening_bid == "2♣":
            if hand.hcp >= 8: return ("2NT", "Positive response to 2♣ (8+ HCP, balanced).")
            else: return ("2♦", "Artificial waiting response to 2♣.")
        
        if hand.total_points < 6: return ("Pass", "Less than 6 total points.")
        
        opening_suit = opening_bid[1]
        if hand.suit_lengths[opening_suit] >= 3:
            support_points = self._calculate_support_points(hand, opening_suit)
            if support_points >= 13:
                return (f"4{opening_suit}" if opening_suit in '♥♠' else "3NT", "Game-forcing raise.")
            if 10 <= support_points <= 12:
                return (f"3{opening_suit}", f"Invitational raise showing 10-12 support points.")
            return (f"2{opening_suit}", f"Simple raise showing 6-9 support points.")

        if opening_bid in ['1♣', '1♦'] and hand.suit_lengths['♥'] >= 4: return ("1♥", "Showing a 4+ card heart suit.")
        if opening_bid in ['1♣', '1♦', '1♥'] and hand.suit_lengths['♠'] >= 4: return ("1♠", "Showing a 4+ card spade suit.")

        if hand.is_balanced and 6 <= hand.hcp <= 9:
            return ("1NT", "Shows 6-9 HCP, balanced, and no fit.")
        
        return ("Pass", "No clear natural response.")

    def _get_responder_rebid(self, hand: Hand, features: Dict):
        auction_features = features['auction_features']
        if 6 <= hand.total_points <= 9:
            return ("Pass", "Minimum hand (6-9 pts), no reason to bid further.")
        elif 10 <= hand.total_points <= 12:
            opener_first_suit = auction_features.get('opening_bid')[1]
            if hand.suit_lengths[opener_first_suit] >= 3:
                return (f"3{opener_first_suit}", "Invitational raise (10-12 pts) with trump support.")
            return ("2NT", "Invitational (10-12 pts), suggesting a 3NT contract.")
        elif hand.total_points >= 13:
            opener_first_suit = auction_features.get('opening_bid')[1]
            if hand.suit_lengths[opener_first_suit] >= 3:
                return (f"4{opener_first_suit}", "Game-forcing (13+ pts) with a fit.")
            return ("3NT", "Game-forcing (13+ pts), bidding game in No-Trump.")
        return ("Pass", "No clear rebid for responder.")