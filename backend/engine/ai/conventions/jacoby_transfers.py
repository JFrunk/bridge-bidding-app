from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class JacobyConvention(ConventionModule):
    """Complete playbook for the Jacoby Transfer convention."""
    
    def get_constraints(self) -> Dict:
        return {'suit_length_req': (['♥', '♠'], 5, 'any_of')}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if self._is_completion_applicable(features):
            return self._get_completion_bid(hand, features)
        if self._is_initiation_applicable(hand, features):
            return self._get_transfer_bid(hand)
        return None

    def _is_completion_applicable(self, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        partner_last_bid = auction_features.get('partner_last_bid')
        return (auction_features.get('opener_relationship') == 'Me' and
                auction_features.get('opening_bid') == '1NT' and
                partner_last_bid in ['2♦', '2♥'])

    def _get_completion_bid(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        partner_last_bid = features['auction_features']['partner_last_bid']
        if partner_last_bid == "2♦":
            if hand.hcp >= 17 and hand.suit_lengths['♥'] == 2:
                return ("2NT", "Maximum 1NT opening (17-18 HCP) with no fit for Hearts.")
            return ("2♥", "Completing the transfer to Hearts.")
        if partner_last_bid == "2♥":
            if hand.hcp >= 17 and hand.suit_lengths['♠'] == 2:
                return ("2NT", "Maximum 1NT opening (17-18 HCP) with no fit for Spades.")
            return ("2♠", "Completing the transfer to Spades.")
        return ("Pass", "Error: Fall-through in transfer completion.")

    def _is_initiation_applicable(self, hand: Hand, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != 'Pass']
        return (auction_features.get('opening_bid') == '1NT' and
                auction_features.get('opener_relationship') == 'Partner' and
                len(non_pass_bids) == 1 and
                (hand.suit_lengths['♥'] >= 5 or hand.suit_lengths['♠'] >= 5))
    
    def _get_transfer_bid(self, hand: Hand) -> Optional[Tuple[str, str]]:
        if hand.suit_lengths['♥'] >= 5:
            return ("2♦", "Jacoby Transfer showing 5+ Hearts.")
        if hand.suit_lengths['♠'] >= 5:
            return ("2♥", "Jacoby Transfer showing 5+ Spades.")
        return None