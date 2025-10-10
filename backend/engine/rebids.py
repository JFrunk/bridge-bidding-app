from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class RebidModule(ConventionModule):
    """
    Playbook for the opener's second bid (rebid).
    """

    # Suit ranking for reverse bid detection (higher number = higher ranking)
    SUIT_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}

    def _is_reverse_bid(self, opening_bid: str, rebid_suit: str) -> bool:
        """
        Check if rebidding a new suit would be a reverse (forcing, showing 17+ HCP).

        A reverse occurs when:
        1. Opener bids a new suit at the 2-level
        2. The new suit ranks HIGHER than the opening suit

        Examples:
        - 1♦ - 1♠ - 2♥: REVERSE (hearts > diamonds)
        - 1♥ - 1♠ - 2♦: NOT reverse (diamonds < hearts)
        - 1♣ - 1♥ - 2♦: NOT reverse (diamonds > clubs but not forcing in standard)
        """
        if not opening_bid or len(opening_bid) < 2:
            return False

        opening_suit = opening_bid[1]

        # Only applies to 1-level openings
        if opening_bid[0] != '1':
            return False

        # Rebid suit must rank higher than opening suit
        return self.SUIT_RANK.get(rebid_suit, 0) > self.SUIT_RANK.get(opening_suit, 0)

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

                # Check for reverse bid with 17+ HCP and 4+ card second suit
                # Reverse shows a strong hand (17+ HCP) and is forcing
                if hand.hcp >= 17:
                    for suit in ['♠', '♥', '♦', '♣']:  # Check in rank order
                        if suit != my_opening_bid[1] and hand.suit_lengths.get(suit, 0) >= 4:
                            if self._is_reverse_bid(my_opening_bid, suit):
                                return (f"2{suit}", f"Reverse bid showing 17+ HCP and 4+ {suit} (forcing).")

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

                # Check for reverse bid with 4+ card second suit
                # With 19+ HCP, reverse shows slam interest
                for suit in ['♠', '♥', '♦', '♣']:  # Check in rank order
                    if suit != my_opening_bid[1] and hand.suit_lengths.get(suit, 0) >= 4:
                        if self._is_reverse_bid(my_opening_bid, suit):
                            return (f"2{suit}", f"Reverse bid showing 19+ HCP and 4+ {suit} (forcing, slam interest).")

            # Before jumping to 3NT, check if we have a 6-card suit to show
            my_suit = my_opening_bid[1]
            if hand.suit_lengths.get(my_suit, 0) >= 6:
                # Rebid the 6-card suit at the 3-level to show extras and length
                return (f"3{my_suit}", f"Strong hand ({hand.total_points} pts) with a 6+ card {my_suit} suit.")

            return ("3NT", f"Strong hand ({hand.total_points} pts), bidding game in No-Trump.")

        return ("Pass", "No clear rebid available.")