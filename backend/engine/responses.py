from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class ResponseModule(ConventionModule):
    """
    Playbook for all of the responder's natural bids, based on the user's flowcharts.
    """
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        auction = features['auction_features']
        opening_bid = auction.get('opening_bid')
        if not opening_bid or auction.get('opener_relationship') != 'Partner':
            return None # Not a response situation

        my_bids = [bid for i, bid in enumerate(features['auction_history']) if features['positions'][i % 4] == features['my_index']]

        if len(my_bids) == 0:
            return self._get_first_response(hand, opening_bid, features)
        else:
            return self._get_responder_rebid(hand, features)

    def _calculate_support_points(self, hand: Hand, trump_suit: str) -> int:
        points = hand.hcp
        for suit, length in hand.suit_lengths.items():
            if suit != trump_suit:
                if length == 1: points += 2
                if length == 0: points += 3
        return points

    def _get_first_response(self, hand: Hand, opening_bid: str, features: Dict):
        """
        Determine responder's first bid after partner's opening.
        Handles both uncontested and contested auctions.
        """
        # Special case: 2♣ opening (strong artificial)
        if opening_bid == "2♣":
            if hand.hcp >= 8: return ("2NT", "Positive response to 2♣ (8+ HCP, balanced).")
            else: return ("2♦", "Artificial waiting response to 2♣.")

        if hand.total_points < 6: return ("Pass", "Less than 6 total points.")

        # Get interference information
        interference = features['auction_features'].get('interference', {'present': False})

        # Route to appropriate handler based on opening bid type
        if 'NT' in opening_bid:
            return self._respond_to_1nt(hand, opening_bid, interference)
        else:
            return self._respond_to_suit_opening(hand, opening_bid, interference)

    def _respond_to_1nt(self, hand: Hand, opening_bid: str, interference: Dict):
        """
        Respond to 1NT opening, handling interference per SAYC rules.

        SAYC Rules:
        - After (X): Systems ON (Stayman/Jacoby still work)
        - After suit overcall: Systems OFF (all bids natural)
        """
        if not interference['present'] or interference['type'] == 'double':
            # No interference OR double (systems ON)
            # Let Stayman/Jacoby conventions handle this
            return None

        # Interference present - systems are OFF
        # Use natural competitive bidding
        return self._competitive_1nt_response(hand, interference)

    def _competitive_1nt_response(self, hand: Hand, interference: Dict):
        """
        Natural competitive responses after 1NT - (overcall) - ?

        Strategy:
        - Bid a good 5-card major with 5+ HCP (competitive, not forcing)
        - Pass with weak balanced hands
        - Advanced: Cuebid with game-forcing hands
        """
        # With a good 5-card major, compete at the 2-level
        for suit in ['♥', '♠']:  # Check majors first
            if hand.suit_lengths.get(suit, 0) >= 5 and hand.hcp >= 5:
                # Bid at cheapest legal level (usually 2-level)
                return (f"2{suit}", f"Natural competitive bid showing 5+ {suit} and 5+ HCP.")

        # With a good 6-card minor, can compete
        for suit in ['♣', '♦']:
            if hand.suit_lengths.get(suit, 0) >= 6 and hand.hcp >= 5:
                return (f"3{suit}", f"Natural competitive bid showing 6+ {suit}.")

        # Otherwise, pass
        return ("Pass", "No suitable competitive action after interference.")

    def _respond_to_suit_opening(self, hand: Hand, opening_bid: str, interference: Dict):
        """
        Respond to suit opening (1♣/1♦/1♥/1♠), handling interference.

        SAYC Rules with interference:
        - Direct raises show same ranges (6-9, 10-12, 13+)
        - New suits still forcing
        - Competitive environment but basic structure maintained
        """
        opening_suit = opening_bid[1]

        # Raise partner's suit with 3+ card support
        if opening_suit in hand.suit_lengths and hand.suit_lengths[opening_suit] >= 3:
            support_points = self._calculate_support_points(hand, opening_suit)

            if support_points >= 13:
                return (f"4{opening_suit}" if opening_suit in '♥♠' else "3NT", "Game-forcing raise.")
            if 10 <= support_points <= 12:
                return (f"3{opening_suit}", f"Invitational raise showing 10-12 support points.")
            if 6 <= support_points <= 9:
                return (f"2{opening_suit}", f"Simple raise showing 6-9 support points.")

        # Without fit, bid new suits up-the-line (if no interference or low interference)
        if not interference['present'] or interference['level'] <= 1:
            # Can still bid new suits at 1-level
            if opening_bid in ['1♣', '1♦'] and hand.suit_lengths.get('♥', 0) >= 4:
                return ("1♥", "Showing a 4+ card heart suit.")
            if opening_bid in ['1♣', '1♦', '1♥'] and hand.suit_lengths.get('♠', 0) >= 4:
                return ("1♠", "Showing a 4+ card spade suit.")

            # 1NT response (6-9 HCP, balanced, no fit)
            if hand.is_balanced and 6 <= hand.hcp <= 9:
                return ("1NT", "Shows 6-9 HCP, balanced, and no fit.")

        # With interference at 2-level or higher, need more to bid a new suit
        # Pass without a clear action
        return ("Pass", "No clear response available.")

    def _get_responder_rebid(self, hand: Hand, features: Dict):
        auction_features = features['auction_features']
        opening_bid = auction_features.get('opening_bid', '')

        if 6 <= hand.total_points <= 9:
            return ("Pass", "Minimum hand (6-9 pts), no reason to bid further.")
        elif 10 <= hand.total_points <= 12:
            # Check if opening was NT
            if 'NT' in opening_bid:
                return ("2NT", "Invitational (10-12 pts), suggesting a 3NT contract.")

            opener_first_suit = opening_bid[1]
            if opener_first_suit in hand.suit_lengths and hand.suit_lengths[opener_first_suit] >= 3:
                return (f"3{opener_first_suit}", "Invitational raise (10-12 pts) with trump support.")
            return ("2NT", "Invitational (10-12 pts), suggesting a 3NT contract.")
        elif hand.total_points >= 13:
            # Check if opening was NT
            if 'NT' in opening_bid:
                return ("3NT", "Game-forcing (13+ pts), bidding game in No-Trump.")

            opener_first_suit = opening_bid[1]
            if opener_first_suit in hand.suit_lengths and hand.suit_lengths[opener_first_suit] >= 3:
                return (f"4{opener_first_suit}", "Game-forcing (13+ pts) with a fit.")
            return ("3NT", "Game-forcing (13+ pts), bidding game in No-Trump.")
        return ("Pass", "No clear rebid for responder.")