from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class RebidModule(ConventionModule):
    """
    Playbook for the opener's second bid (rebid).
    """
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main entry point for all opener rebid actions."""
        auction_history = features['auction_history']
        partner_response = features['auction_features']['partner_last_bid']
        my_opening_bid = features['auction_features']['opening_bid']

        if not partner_response or not my_opening_bid:
            return ("Pass", "Cannot determine auction context for rebid.")
        
        # Logic for rebids after a 2 Club opening
        if my_opening_bid == '2♣':
            if partner_response == '2♦':
                if 22 <= hand.hcp <= 24 and hand.is_balanced:
                    return ("2NT", "Shows a balanced hand with 22-24 HCP.")
                best_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
                if hand.suit_lengths[best_suit] >= 5:
                    bid_level = '3' if best_suit in ['♣', '♦'] else '2'
                    return (f"{bid_level}{best_suit}", f"Shows a strong hand with a long {best_suit} suit.")
            if partner_response == '2NT':
                best_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
                if hand.suit_lengths[best_suit] >= 5:
                    return (f"3{best_suit}", f"Showing my long {best_suit} suit.")

        # Logic for rebids after a 1-level opening
        if 13 <= hand.total_points <= 15: # Minimum Hand
            # Check if partner raised our suit
            if partner_response.endswith(my_opening_bid[1:]):
                # Distinguish between simple raise (2-level) and invitational raise (3-level)
                partner_level = int(partner_response[0])
                my_opening_level = int(my_opening_bid[0])

                if partner_level == my_opening_level + 1:  # Simple raise (e.g., 1♠-2♠)
                    return ("Pass", "Minimum hand (13-15 pts), passing partner's simple raise.")

                elif partner_level == my_opening_level + 2:  # Invitational raise (e.g., 1♠-3♠)
                    # Partner is inviting game (10-12 points). Accept with maximum or good shape
                    my_suit = my_opening_bid[1:]

                    # Accept invitation if:
                    # 1. Maximum minimum (15 points), OR
                    # 2. Good 6+ card suit, OR
                    # 3. 14+ points with quality suit (2+ honors)
                    has_long_suit = hand.suit_lengths.get(my_suit, 0) >= 6
                    has_quality_suit = hand.suit_hcp.get(my_suit, 0) >= 6  # 2+ honors

                    if hand.total_points >= 15 or has_long_suit or (hand.total_points >= 14 and has_quality_suit):
                        if my_suit in ['♥', '♠']:
                            return (f"4{my_suit}", f"Accepting invitation to game with {hand.total_points} points and good shape/suit quality.")
                        else:
                            return ("3NT", f"Accepting invitation to game with {hand.total_points} points.")
                    else:
                        return ("Pass", "Declining invitation with minimum (13 points) and no extra shape.")
            if partner_response == "1NT":
                second_suits = [s for s, l in hand.suit_lengths.items() if l >= 4 and s != my_opening_bid[1]]
                if second_suits:
                    return (f"2{second_suits[0]}", f"Minimum hand (13-15 pts) showing a second suit.")
                if hand.suit_lengths.get(my_opening_bid[1], 0) >= 6:
                    return (f"2{my_opening_bid[1]}", f"Minimum hand (13-15 pts) rebidding a 6+ card suit.")
                return (f"2{my_opening_bid[1]}", f"Minimum hand (13-15 pts) rebidding a 5-card suit.")
            if partner_response[0] == '1' and len(partner_response) == 2:
                partner_suit = partner_response[1]
                if hand.suit_lengths.get(partner_suit, 0) >= 4:
                    return (f"2{partner_suit}", f"Minimum hand (13-15 pts) showing 4+ card support.")
                if hand.is_balanced:
                    return ("1NT", "Minimum hand (12-14 HCP), balanced, no fit for partner's suit.")

        elif 16 <= hand.total_points <= 18: # Medium Hand
            if partner_response.endswith(my_opening_bid[1]):
                return (f"3{my_opening_bid[1]}", "Invitational (16-18 pts), raising partner's simple raise.")
            if partner_response[0] == '1' and len(partner_response) == 2:
                partner_suit = partner_response[1]
                if hand.suit_lengths.get(partner_suit, 0) >= 4:
                    return (f"3{partner_suit}", f"Invitational (16-18 pts) jump raise showing 4+ card support.")
            if hand.suit_lengths.get(my_opening_bid[1], 0) >= 6:
                return (f"3{my_opening_bid[1]}", f"Invitational (16-18 pts) jump rebid of a 6+ card suit.")
            return ("2NT", "Shows a strong hand (16-18 pts) with no obvious fit.")

        elif hand.total_points >= 19: # Strong Hand
            if partner_response.endswith(my_opening_bid[1]):
                partner_suit = my_opening_bid[1]
                if partner_suit in ['♥', '♠']:
                    return (f"4{partner_suit}", f"Strong hand ({hand.total_points} pts), bidding game after partner's raise.")
            if len(partner_response) == 2:
                partner_suit = partner_response[1]
                if partner_suit in ['♥', '♠'] and hand.suit_lengths.get(partner_suit, 0) >= 4:
                     return (f"4{partner_suit}", f"Strong hand ({hand.total_points} pts), bidding game with a fit.")
            return ("3NT", f"Strong hand ({hand.total_points} pts), bidding game in No-Trump.")

        return ("Pass", "No clear rebid available.")