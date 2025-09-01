from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule # CORRECTED IMPORT
from typing import Optional, Tuple, Dict

class BlackwoodConvention(ConventionModule):
    """
    Playbook for Blackwood, including 4NT (aces) and 5NT (kings).
    """
    def get_constraints(self) -> Dict:
        return {'hcp_range': (18, 40)}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if self._is_final_slam_bid_applicable(features):
            return self._get_final_slam_bid(hand, features)
        if self._is_king_answering_applicable(features):
            return self._get_king_answer_bid(hand)
        if self._is_king_asking_applicable(hand, features):
            return self._get_king_ask_bid()
        if self._is_ace_answering_applicable(features):
            return self._get_ace_answer_bid(hand)
        if self._is_ace_asking_applicable(hand, features):
            return self._get_ace_ask_bid()
        return None

    # ... The rest of the BlackwoodConvention class is the same ...
    def _is_ace_asking_applicable(self, hand: Hand, features: Dict) -> bool:
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if not partner_last_bid: return False
        is_strong_raise = len(partner_last_bid) == 2 and partner_last_bid[0] in ['3', '4']
        return is_strong_raise and hand.total_points >= 18
    def _get_ace_ask_bid(self) -> Tuple[str, str]:
        return ("4NT", "Blackwood convention, asking for aces.")
    def _is_ace_answering_applicable(self, features: Dict) -> bool:
        return features['auction_features'].get('partner_last_bid') == '4NT'
    def _get_ace_answer_bid(self, hand: Hand) -> Tuple[str, str]:
        num_aces = sum(1 for card in hand.cards if card.rank == 'A')
        if num_aces in [0, 4]: return ("5♣", "Response to Blackwood: 0 or 4 aces.")
        if num_aces == 1: return ("5♦", "Response to Blackwood: 1 ace.")
        if num_aces == 2: return ("5♥", "Response to Blackwood: 2 aces.")
        if num_aces == 3: return ("5♠", "Response to Blackwood: 3 aces.")
        return ("Pass", "Error: Could not count aces.")
    def _is_king_asking_applicable(self, hand: Hand, features: Dict) -> bool:
        partner_ace_response = features['auction_features'].get('partner_last_bid')
        if not partner_ace_response or partner_ace_response[0] != '5': return False
        my_aces = sum(1 for card in hand.cards if card.rank == 'A')
        partner_aces = -1
        if partner_ace_response == '5♦': partner_aces = 1
        if partner_ace_response == '5♥': partner_aces = 2
        if partner_ace_response == '5♠': partner_aces = 3
        return my_aces + partner_aces == 4 if partner_aces != -1 else False
    def _get_king_ask_bid(self) -> Tuple[str, str]:
        return ("5NT", "Blackwood convention, asking for kings.")
    def _is_king_answering_applicable(self, features: Dict) -> bool:
        return features['auction_features'].get('partner_last_bid') == '5NT'
    def _get_king_answer_bid(self, hand: Hand) -> Tuple[str, str]:
        num_kings = sum(1 for card in hand.cards if card.rank == 'K')
        if num_kings == 0: return ("6♣", "Response to King-ask: 0 kings.")
        if num_kings == 1: return ("6♦", "Response to King-ask: 1 king.")
        if num_kings == 2: return ("6♥", "Response to King-ask: 2 kings.")
        if num_kings == 3: return ("6♠", "Response to King-ask: 3 kings.")
        if num_kings == 4: return ("6NT", "Response to King-ask: 4 kings.")
        return ("Pass", "Error: Could not count kings.")
    def _is_final_slam_bid_applicable(self, features: Dict) -> bool:
        my_bids = [bid for i, bid in enumerate(features['auction_history']) if i % 2 == features['my_index'] % 2]
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        return ('4NT' in my_bids and partner_last_bid and partner_last_bid[0] in ['5', '6'])
    def _get_final_slam_bid(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        agreed_suit = '♠' # Simplified for now
        return (f"6{agreed_suit}", f"Bidding the small slam in {agreed_suit}.")