from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class OpeningBidsModule(ConventionModule):
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        # This module does not need features, but conforms to the interface
        
        # Rule for very strong balanced hands (22+ HCP)
        if hand.is_balanced:
            if 25 <= hand.hcp <= 27: return ("3NT", "Shows a balanced hand with 25-27 HCP.")
            if 22 <= hand.hcp <= 24: return ("2NT", "Shows a balanced hand with 22-24 HCP.")
        
        # Rule for very strong hands (22+ total points)
        if hand.total_points >= 22:
            return ("2♣", "Strong and artificial. Shows 22+ total points.")

        # Rule for standard balanced 1NT opening
        if 15 <= hand.hcp <= 17 and hand.is_balanced:
            return ("1NT", "Shows 15-17 HCP and a balanced hand.")
        
        # Rule for standard 1-level openings (13-21 points)
        if hand.total_points >= 13:
            if max(hand.suit_lengths.values()) >= 5: # Has a 5+ card suit
                # Prioritize majors
                if hand.suit_lengths['♥'] >= 5 and hand.suit_lengths['♥'] >= hand.suit_lengths['♠']:
                    return ("1♥", "Shows 13+ total points and a 5+ card heart suit.")
                if hand.suit_lengths['♠'] >= 5:
                    return ("1♠", "Shows 13+ total points and a 5+ card spade suit.")
                # Then minors
                if hand.suit_lengths['♦'] >= 5 and hand.suit_lengths['♦'] >= hand.suit_lengths['♣']:
                     return ("1♦", "Shows 13+ total points and a 5+ card diamond suit.")
                if hand.suit_lengths['♣'] >= 5:
                     return ("1♣", "Shows 13+ total points and a 5+ card club suit.")
            # No 5-card suit, open longer minor
            if hand.suit_lengths['♦'] > hand.suit_lengths['♣']:
                return ("1♦", "Shows 13+ points, no 5-card suit. Diamonds is the longer minor.")
            else:
                return ("1♣", "Shows 13+ points, no 5-card suit. Clubs is the longer or equal minor.")

        return ("Pass", "Less than 13 total points.")