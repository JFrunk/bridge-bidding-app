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
        
    def _get_opening_preempt(self, hand: Hand, vulnerability: str = 'None') -> Optional[Tuple[str, str]]:
        """
        Generate opening preemptive bid.

        SAYC Standard:
        - 2-level: 6-card suit, 6-10 HCP, 2+ honors
        - 3-level: 7-card suit, 6-10 HCP, 2+ honors
        - 4-level: 8-card suit, 6-10 HCP (or 7-card with favorable vulnerability)
        """
        constraints = self.get_constraints()
        hcp_range = constraints['hcp_range']
        if not (hcp_range[0] <= hand.hcp <= hcp_range[1]):
            return None

        suits, _, _ = constraints['suit_length_req']

        # Check each suit for preempt possibility (prioritize longer suits)
        for suit_length in [8, 7, 6]:
            for suit in suits:
                if hand.suit_lengths[suit] == suit_length:
                    # Check for sufficient honors (2+ honors)
                    honors = {'A', 'K', 'Q', 'J', 'T'}
                    suit_cards = [card.rank for card in hand.cards if card.suit == suit]
                    honor_count = sum(1 for rank in suit_cards if rank in honors)

                    if honor_count >= 2:
                        suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond'}[suit]

                        # Determine level based on suit length
                        if suit_length == 8:
                            # 4-level preempt (8-card suit)
                            return (f"4{suit}", f"4-level preempt showing 8-card {suit_name} suit with 6-10 HCP.")
                        elif suit_length == 7:
                            # 3-level preempt (7-card suit)
                            return (f"3{suit}", f"3-level preempt showing 7-card {suit_name} suit with 6-10 HCP.")
                        elif suit_length == 6:
                            # 2-level preempt (weak two)
                            return (f"2{suit}", f"Weak Two bid showing 6-card {suit_name} suit with 6-10 HCP.")

        return None
        
    def _is_response_applicable(self, features: Dict) -> bool:
        """Check if we're responding to partner's preempt."""
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')

        # Partner must have opened with a preempt (2/3/4-level suit bid)
        if not opening_bid or auction_features.get('opener_relationship') != 'Partner':
            return False

        # Check if it's a preemptive opening (2/3/4-level in a suit)
        try:
            level = int(opening_bid[0])
            suit = opening_bid[1]
            return level in [2, 3, 4] and suit in ['♦', '♥', '♠']
        except (ValueError, IndexError):
            return False

    def _get_response_to_preempt(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        """
        Respond to partner's preemptive opening.

        General guidelines:
        - With 15+ HCP and 2-level preempt: 2NT (Ogust asking)
        - With 3-card support: Raise based on strength
        - With very strong hand: Bid game or explore slam
        """
        opening_bid = features['auction_features']['opening_bid']
        preempt_level = int(opening_bid[0])
        preempt_suit = opening_bid[1]

        # For 2-level preempts: Ogust convention with 15+ HCP
        if preempt_level == 2 and hand.total_points >= 15:
            return ("2NT", "Ogust Convention asking about preempt quality.")

        # With fit (3+ card support), raise based on strength
        if hand.suit_lengths[preempt_suit] >= 3:
            if preempt_level == 2:
                # Responding to 2-level preempt
                if hand.total_points >= 17:
                    return (f"4{preempt_suit}", f"Raising to game with {hand.total_points} points and fit.")
                if hand.total_points >= 11:
                    return (f"3{preempt_suit}", f"Constructive raise with {hand.total_points} points.")
            elif preempt_level == 3:
                # Responding to 3-level preempt (need more strength)
                if hand.total_points >= 15:
                    return (f"4{preempt_suit}", f"Raising to game with {hand.total_points} points.")
            # For 4-level preempts, usually pass unless exploring slam

        # Without fit, need very strong hand to bid
        if hand.hcp >= 16 and hand.is_balanced:
            return ("3NT", f"Bidding 3NT with {hand.hcp} HCP, no fit for preempt.")

        return ("Pass", f"Passing partner's preempt with {hand.total_points} points.")