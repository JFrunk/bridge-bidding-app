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

        IMPORTANT SAYC RESTRICTIONS for Weak Twos (2-level):
        - NO void or singleton ace (hand too shapely/strong)
        - NO 4-card side major (may belong in that suit)
        - Typically 2 of top 3 honors (A/K/Q) or 3 of top 5
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
                    # Check for sufficient suit quality
                    suit_cards = [card.rank for card in hand.cards if card.suit == suit]

                    # For Weak Twos (6-card): STRICT requirement of 2 of top 3 honors (A/K/Q)
                    # For 3-level+ preempts (7-8 card): More lenient - 2+ honors including J/T
                    if suit_length == 6:
                        # SAYC: Weak Two requires 2 of top 3 honors (A, K, Q)
                        top_three_honors = {'A', 'K', 'Q'}
                        top_honor_count = sum(1 for rank in suit_cards if rank in top_three_honors)
                        has_quality_suit = top_honor_count >= 2
                    else:
                        # 7-8 card preempts: 2+ honors (can include J, T)
                        honors = {'A', 'K', 'Q', 'J', 'T'}
                        honor_count = sum(1 for rank in suit_cards if rank in honors)
                        has_quality_suit = honor_count >= 2

                    if has_quality_suit:
                        suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond'}[suit]

                        # Determine level based on suit length
                        if suit_length == 8:
                            # 4-level preempt (8-card suit)
                            return (f"4{suit}", f"4-level preempt showing 8-card {suit_name} suit with 6-10 HCP.")
                        elif suit_length == 7:
                            # 3-level preempt (7-card suit)
                            return (f"3{suit}", f"3-level preempt showing 7-card {suit_name} suit with 6-10 HCP.")
                        elif suit_length == 6:
                            # 2-level preempt (weak two) - apply SAYC restrictions
                            if not self._is_valid_weak_two(hand, suit):
                                continue  # Skip this suit, try next one
                            return (f"2{suit}", f"Weak Two bid showing 6-card {suit_name} suit with 6-10 HCP.")

        return None

    def _is_valid_weak_two(self, hand: Hand, preempt_suit: str) -> bool:
        """
        Check if hand meets SAYC requirements for a weak two bid.

        SAYC Restrictions:
        - NO void (0-card suit)
        - NO singleton ace (too strong/shapely)
        - NO 4-card side MAJOR (might belong in that major)

        Returns: True if hand is valid for weak two, False otherwise
        """
        # Check for voids
        for suit in ['♠', '♥', '♦', '♣']:
            if hand.suit_lengths[suit] == 0:
                return False  # Void - reject weak two

        # Check for singleton aces
        for suit in ['♠', '♥', '♦', '♣']:
            if hand.suit_lengths[suit] == 1:
                # Check if it's an ace
                suit_cards = [card for card in hand.cards if card.suit == suit]
                if suit_cards and suit_cards[0].rank == 'A':
                    return False  # Singleton ace - reject weak two

        # Check for 4-card side major
        for major in ['♠', '♥']:
            if major != preempt_suit and hand.suit_lengths[major] >= 4:
                return False  # 4-card side major - reject weak two

        return True
        
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