from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict, List

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
        # Add other stayman-related evaluation steps here if necessary
        return None

    def _should_bid_stayman(self, hand: Hand, features: Dict) -> bool:
        """Check if responder should bid 2♣ Stayman."""
        auction_features = features.get('auction_features', {})
        # Condition: Partner must have opened 1NT
        if auction_features.get('opening_bid') != '1NT' or auction_features.get('opener_relationship') != 'Partner':
            return False
        
        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != 'Pass']
        if len(non_pass_bids) != 1: return False
        
        # Condition: Hand must meet Stayman point and suit requirements
        if hand.hcp < 8: return False
        if hand.suit_lengths['♥'] >= 5 or hand.suit_lengths['♠'] >= 5: return False # Use Jacoby for 5-card majors
        if hand.suit_lengths['♥'] < 4 and hand.suit_lengths['♠'] < 4: return False
        
        return True

    def _initiate_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        """Bid 2♣ Stayman."""
        return ("2♣", f"Stayman. Asks partner for a 4-card major. Shows {hand.hcp} HCP.")

    def _is_stayman_response_position(self, features: Dict) -> bool:
        """Check if we're opener responding to Stayman 2♣."""
        auction_features = features.get('auction_features', {})
        # THIS IS THE FIX: Added check for opening_bid == '1NT'
        return (auction_features.get('opening_bid') == '1NT' and
                auction_features.get('opener_relationship') == 'Me' and
                auction_features.get('partner_last_bid') == '2♣')

    def _respond_to_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        """Opener's response to 2♣ Stayman."""
        if hand.suit_lengths['♥'] >= 4: return ("2♥", "Stayman response showing 4+ hearts.")
        if hand.suit_lengths['♠'] >= 4: return ("2♠", "Stayman response showing 4+ spades.")
        return ("2♦", "Stayman response denying 4-card majors.")