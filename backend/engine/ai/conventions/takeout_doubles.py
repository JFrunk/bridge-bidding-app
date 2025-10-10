from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class TakeoutDoubleConvention(ConventionModule):
    """
    Playbook for making a Takeout Double, based on the provided flowchart.
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Main evaluation function. Checks if a takeout double is the correct action.
        """
        if not self._is_applicable(features):
            return None

        if self._hand_qualifies(hand, features):
            return ("X", "Takeout Double. Shows 12+ points and support for unbid suits.")
            
        return None

    def _is_applicable(self, features: Dict) -> bool:
        """
        A takeout double is applicable if an opponent has opened (but not in NT)
        and our side has not yet bid.
        """
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid', '')
        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != "Pass"]
        
        # Rule: Is this the first bid after an opponent's opening?
        is_correct_position = (auction_features.get('opener_relationship') == 'Opponent' and
                               len(non_pass_bids) == 1)
        
        # Rule: Is the opening bid No-Trump? If so, double is not for takeout.
        is_not_nt_opening = opening_bid and 'NT' not in opening_bid
        
        return is_correct_position and is_not_nt_opening

    def _hand_qualifies(self, hand: Hand, features: Dict) -> bool:
        """
        Checks for 12+ points (SAYC standard), shortness in opponent's suit, and support for unbid suits.
        """
        # Rule 1: Must have opening strength (SAYC standard is 12+ HCP).
        if hand.hcp < 12:
            return False

        # Rule 2: Must be short in the opponent's suit (0, 1, or 2 cards).
        opponent_suit = features['auction_features']['opening_bid'][1]
        if hand.suit_lengths.get(opponent_suit, 0) > 2:
            return False
            
        # Rule 3: Must have at least 3-card support for all unbid suits.
        all_suits = {'♠', '♥', '♦', '♣'}
        unbid_suits = all_suits - {opponent_suit}
        
        for suit in unbid_suits:
            if hand.suit_lengths.get(suit, 0) < 3:
                return False
                
        return True