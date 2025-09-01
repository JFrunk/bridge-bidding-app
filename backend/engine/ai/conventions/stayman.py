from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class StaymanConvention(ConventionModule):
    """
    Complete Stayman convention implementation.
    """
    def get_constraints(self) -> Dict:
        return {'hcp_range': (8, 40), 'suit_length_req': (['♥', '♠'], 4, 'any_of')}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if self._should_bid_stayman(hand, features):
            return self._initiate_stayman(hand, features)
        if self._is_stayman_response_position(features):
            return self._respond_to_stayman(hand, features)
        if self._is_opener_rebid_position(features):
            return self._handle_opener_rebid(hand, features)
        if self._is_stayman_followup_position(features):
            return self._handle_stayman_followup(hand, features)
        return None

    def _should_bid_stayman(self, hand: Hand, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])
        if (auction_features.get('opening_bid') != '1NT' or auction_features.get('opener_relationship') != 'Partner'): return False
        non_pass_bids = [bid for bid in auction_history if bid != 'Pass']
        if len(non_pass_bids) != 1: return False
        return self._validate_stayman_requirements(hand)

    def _validate_stayman_requirements(self, hand: Hand) -> bool:
        """
        Validates hand meets Stayman requirements with corrected logic.
        """
        # Rule 1: Must have 8+ HCP
        if hand.hcp < 8: 
            return False
        
        # Rule 2: Must NOT have a 5+ card major (those hands should transfer)
        if hand.suit_lengths['♥'] >= 5 or hand.suit_lengths['♠'] >= 5:
            return False
            
        # Rule 3: Must have at least one 4-card major
        if hand.suit_lengths['♥'] >= 4 or hand.suit_lengths['♠'] >= 4:
            return True
            
        return False

    def _initiate_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        return ("2♣", f"Stayman. Asks partner for a 4-card major. Shows {hand.hcp} HCP.")

    def _is_stayman_response_position(self, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        return (auction_features.get('opener_relationship') == 'Me' and
                auction_features.get('partner_last_bid') == '2♣')

    def _respond_to_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        if hand.suit_lengths['♥'] >= 4: return ("2♥", "Stayman response showing 4+ hearts.")
        if hand.suit_lengths['♠'] >= 4: return ("2♠", "Stayman response showing 4+ spades.")
        return ("2♦", "Stayman response denying 4-card majors.")

    # ... The rest of the class remains the same ...
    def _is_opener_rebid_position(self, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        partner_bid = auction_features.get('partner_last_bid')
        return (auction_features.get('opener_relationship') == 'Me' and
                auction_features.get('opening_bid') == '1NT' and
                partner_bid and partner_bid.startswith('2') and partner_bid != '2♣')

    def _handle_opener_rebid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        partner_response = features['auction_features']['partner_last_bid']
        if partner_response == '2♠':
            if hand.suit_lengths['♠'] >= 4:
                return ("3♠", "Invitational raise in spades.") if hand.hcp < 17 else ("4♠", "Bidding game in spades.")
            else:
                return ("2NT", "Minimum 1NT hand with no spade fit.") if hand.hcp < 17 else ("3NT", "Maximum 1NT hand with no spade fit.")
        return None

    def _is_stayman_followup_position(self, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        if auction_features.get('opener_relationship') != 'Partner' or not auction_features.get('opener_last_bid'): return False
        return (auction_features.get('opening_bid') == '1NT' and 
                '2♣' in auction_features.get('partner_bids', []))

    def _handle_stayman_followup(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        opener_response = features['auction_features']['opener_last_bid']
        if opener_response == "2♦": return self._handle_no_major_response(hand)
        elif opener_response in ["2♥", "2♠"]: return self._handle_major_shown(hand, opener_response)
        return None

    def _handle_no_major_response(self, hand: Hand) -> Tuple[str, str]:
        if 8 <= hand.hcp <= 9: return ("2NT", "Invitational with 8-9 HCP. No major suit fit found.")
        if hand.hcp >= 10: return ("3NT", "Game bid with 10+ HCP. No major suit fit found.")
        return ("Pass", "Minimum hand, no major fit.")

    def _handle_major_shown(self, hand: Hand, opener_response: str) -> Tuple[str, str]:
        shown_major = opener_response[1]
        suit_name = "hearts" if shown_major == '♥' else "spades"
        if hand.suit_lengths[shown_major] >= 4:
            if 8 <= hand.hcp <= 9: return (f"3{shown_major}", f"Invitational raise in {suit_name}.")
            if hand.hcp >= 10: return (f"4{shown_major}", f"Game bid in {suit_name}.")
        else:
            other_major = '♠' if shown_major == '♥' else '♥'
            if hand.suit_lengths[other_major] >= 4:
                return (f"2{other_major}", f"Showing my 4-card {other_major} suit.")
        return ("Pass", "Minimum hand, no fit found.")