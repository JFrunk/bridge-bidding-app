from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class BlackwoodConvention(ConventionModule):
    """
    Playbook for Blackwood, including 4NT (aces) and 5NT (kings).
    """
    def get_constraints(self) -> Dict:
        """Defines requirements for a hand that might ask for aces."""
        return {'hcp_range': (18, 40)}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation function. Checks for asking or answering."""
        if self._is_ace_answering_applicable(features):
            return self._get_ace_answer_bid(hand)
        if self._is_ace_asking_applicable(hand, features):
            return self._get_ace_ask_bid()
        # King-asking and slam bidding logic can be added here later
        return None

    def _is_ace_asking_applicable(self, hand: Hand, features: Dict) -> bool:
        """Determines if this hand should ask for aces."""
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if not partner_last_bid: return False
        
        # A simplified trigger: if partner has made an invitational or game-forcing raise.
        is_strong_raise = len(partner_last_bid) == 2 and partner_last_bid[0] in ['3', '4']
        
        # Condition: Do I have a very strong hand (18+ pts) after partner showed a good hand?
        if is_strong_raise and hand.total_points >= 18:
            return True
            
        return False

    def _get_ace_ask_bid(self) -> Tuple[str, str]:
        """Returns the 4NT ace-asking bid."""
        return ("4NT", "Blackwood convention, asking for aces.")

    def _is_ace_answering_applicable(self, features: Dict) -> bool:
        """Determines if we are responding to a 4NT bid."""
        return features['auction_features'].get('partner_last_bid') == '4NT'

    def _get_ace_answer_bid(self, hand: Hand) -> Tuple[str, str]:
        """Counts aces and returns the correct conventional response."""
        num_aces = sum(1 for card in hand.cards if card.rank == 'A')

        if num_aces == 0 or num_aces == 4:
            return ("5♣", "Response to Blackwood: 0 or 4 aces.")
        if num_aces == 1:
            return ("5♦", "Response to Blackwood: 1 ace.")
        if num_aces == 2:
            return ("5♥", "Response to Blackwood: 2 aces.")
        if num_aces == 3:
            return ("5♠", "Response to Blackwood: 3 aces.")
        
        return ("Pass", "Error: Could not count aces.") # Should not be reached