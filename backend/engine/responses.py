from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.ai.bid_explanation import BidExplanation
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict, Union

class ResponseModule(ConventionModule):
    """
    Playbook for all of the responder's natural bids, based on the user's flowcharts.
    """
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main entry point for response actions with bid validation."""
        auction_history = features['auction_history']

        # Get the raw response suggestion
        result = self._evaluate_response(hand, features)

        if not result:
            return None

        bid, explanation = result

        # Always pass Pass bids through
        if bid == "Pass":
            return result

        # Validate the bid is legal
        if BidValidator.is_legal_bid(bid, auction_history):
            return result

        # Bid is illegal - try to find next legal bid of same strain
        next_legal = get_next_legal_bid(bid, auction_history)
        if next_legal:
            adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
            return (next_legal, adjusted_explanation)

        # No legal bid possible - pass
        return None

    def _evaluate_response(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates response without validation."""
        auction = features['auction_features']
        opening_bid = auction.get('opening_bid')
        opener_index = auction.get('opener_index', -1)
        if not opening_bid or auction.get('opener_relationship') != 'Partner' or opener_index == -1:
            return None # Not a response situation

        # Count my bids AFTER partner's opening
        my_bids_after_opening = [bid for i, bid in enumerate(features['auction_history'])
                                if (i % 4) == features['my_index'] and i > opener_index]

        if len(my_bids_after_opening) == 0:
            return self._get_first_response(hand, opening_bid, features)
        else:
            return self._get_responder_rebid(hand, features, my_bids_after_opening)

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

        Natural responses (no interference):
        - 0-7 HCP: Pass
        - 8-9 HCP: 2NT (invitational)
        - 10-14 HCP: 3NT (game)
        - 15-17 HCP: 4NT (quantitative, slam invite)
        - 18+ HCP: 6NT or explore slam
        """
        if not interference['present'] or interference['type'] == 'double':
            # No interference OR double (systems ON)
            # Check if Stayman/Jacoby conventions will handle this
            # If not, provide natural response based on HCP

            # Conventions will handle if:
            # - 4+ card major(s) AND 8+ HCP (Stayman)
            # - 5+ card major AND 8+ HCP (Jacoby Transfer)
            # Otherwise, we need to provide natural response here

            # Natural responses when no special convention applies:
            if hand.hcp < 8:
                return ("Pass", "Partner opened 1NT (15-17 HCP), we have insufficient strength for game (< 8 HCP).")

            # Note: 8-9 HCP hands with 4-card majors will be handled by Stayman
            # Note: 8+ HCP hands with 5-card majors will be handled by Jacoby
            # So these natural bids are mainly for balanced hands without major interest

            if hand.hcp >= 18:
                # Slam interest - quantitative 4NT or direct 6NT
                if hand.hcp >= 20:
                    return ("6NT", "Slam bid with 20+ HCP opposite partner's 15-17 HCP (combined 35+).")
                else:
                    return ("4NT", "Quantitative slam invitation with 18-19 HCP (non-Blackwood).")

            if hand.hcp >= 15:
                # Quantitative slam invitation
                return ("4NT", "Quantitative slam invitation with 15-17 HCP (non-Blackwood).")

            if hand.hcp >= 10:
                # Game values - bid 3NT directly
                # Note: Stayman/Jacoby will intercept if there's a major suit fit
                return ("3NT", "Game bid with 10-14 HCP opposite partner's 15-17 HCP (combined 25+).")

            if hand.hcp >= 8:
                # Invitational range
                # Note: Stayman will intercept if we have 4-card major
                return ("2NT", "Invitational with 8-9 HCP, asking partner to bid 3NT with maximum (17).")

            # Below 8 HCP - pass
            return ("Pass", "Insufficient strength to invite game (< 8 HCP).")

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
                bid = f"4{opening_suit}" if opening_suit in '♥♠' else "3NT"
                explanation = BidExplanation(bid)
                explanation.set_primary_reason(f"Game-forcing raise with excellent fit for partner's {opening_suit}")
                explanation.add_requirement("Support Points", "13+")
                explanation.add_requirement(f"{opening_suit} Support", "3+")
                explanation.add_actual_value("Support Points", str(support_points))
                explanation.add_actual_value("HCP", str(hand.hcp))
                explanation.add_actual_value(f"{opening_suit} Length", f"{hand.suit_lengths[opening_suit]} cards")
                explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
                explanation.set_forcing_status("Game-forcing")

                # Show shortness bonuses if applicable
                for suit, length in hand.suit_lengths.items():
                    if suit != opening_suit:
                        if length == 0:
                            explanation.add_actual_value(f"Void in {suit}", "+3 support points")
                        elif length == 1:
                            explanation.add_actual_value(f"Singleton {suit}", "+2 support points")

                return (bid, explanation)

            if 10 <= support_points <= 12:
                explanation = BidExplanation(f"3{opening_suit}")
                explanation.set_primary_reason(f"Invitational raise with good fit for partner's {opening_suit}")
                explanation.add_requirement("Support Points", "10-12")
                explanation.add_requirement(f"{opening_suit} Support", "3+")
                explanation.add_actual_value("Support Points", str(support_points))
                explanation.add_actual_value("HCP", str(hand.hcp))
                explanation.add_actual_value(f"{opening_suit} Length", f"{hand.suit_lengths[opening_suit]} cards")
                explanation.set_forcing_status("Invitational")
                explanation.add_alternative(f"2{opening_suit}", f"Too strong (have {support_points} support points, need 10+)")
                explanation.add_alternative(f"4{opening_suit}", f"Not quite enough (have {support_points} support points, need 13+)")
                return (f"3{opening_suit}", explanation)

            if 6 <= support_points <= 9:
                explanation = BidExplanation(f"2{opening_suit}")
                explanation.set_primary_reason(f"Simple raise showing minimum support for partner's {opening_suit}")
                explanation.add_requirement("Support Points", "6-9")
                explanation.add_requirement(f"{opening_suit} Support", "3+")
                explanation.add_actual_value("Support Points", str(support_points))
                explanation.add_actual_value("HCP", str(hand.hcp))
                explanation.add_actual_value(f"{opening_suit} Length", f"{hand.suit_lengths[opening_suit]} cards")
                explanation.set_forcing_status("Sign-off (partner may pass)")
                return (f"2{opening_suit}", explanation)

        # Without fit, bid new suits up-the-line (if no interference or low interference)
        if not interference['present'] or interference['level'] <= 1:
            # JUMP SHIFT responses (17+ HCP, game-forcing)
            # Jump shift shows a strong hand with a good suit and slam interest
            if hand.hcp >= 17:
                # After 1♣ opening, can jump to 2♥/2♠ (or 3♦)
                if opening_bid == '1♣':
                    if hand.suit_lengths.get('♥', 0) >= 5:
                        return ("2♥", "Jump shift showing 17+ HCP and 5+ hearts (game-forcing).")
                    if hand.suit_lengths.get('♠', 0) >= 5:
                        return ("2♠", "Jump shift showing 17+ HCP and 5+ spades (game-forcing).")
                    if hand.suit_lengths.get('♦', 0) >= 5:
                        return ("3♦", "Jump shift showing 17+ HCP and 5+ diamonds (game-forcing).")

                # After 1♦ opening, can jump to 2♥/2♠ (or 3♣)
                if opening_bid == '1♦':
                    if hand.suit_lengths.get('♥', 0) >= 5:
                        return ("2♥", "Jump shift showing 17+ HCP and 5+ hearts (game-forcing).")
                    if hand.suit_lengths.get('♠', 0) >= 5:
                        return ("2♠", "Jump shift showing 17+ HCP and 5+ spades (game-forcing).")
                    if hand.suit_lengths.get('♣', 0) >= 5:
                        return ("3♣", "Jump shift showing 17+ HCP and 5+ clubs (game-forcing).")

                # After 1♥ opening, can jump to 2♠ (or 3♣/3♦)
                if opening_bid == '1♥':
                    if hand.suit_lengths.get('♠', 0) >= 5:
                        return ("2♠", "Jump shift showing 17+ HCP and 5+ spades (game-forcing).")
                    if hand.suit_lengths.get('♣', 0) >= 5:
                        return ("3♣", "Jump shift showing 17+ HCP and 5+ clubs (game-forcing).")
                    if hand.suit_lengths.get('♦', 0) >= 5:
                        return ("3♦", "Jump shift showing 17+ HCP and 5+ diamonds (game-forcing).")

                # After 1♠ opening, can jump to 3♣/3♦/3♥
                if opening_bid == '1♠':
                    if hand.suit_lengths.get('♥', 0) >= 5:
                        return ("3♥", "Jump shift showing 17+ HCP and 5+ hearts (game-forcing).")
                    if hand.suit_lengths.get('♣', 0) >= 5:
                        return ("3♣", "Jump shift showing 17+ HCP and 5+ clubs (game-forcing).")
                    if hand.suit_lengths.get('♦', 0) >= 5:
                        return ("3♦", "Jump shift showing 17+ HCP and 5+ diamonds (game-forcing).")

            # Can still bid new suits at 1-level
            if opening_bid in ['1♣', '1♦'] and hand.suit_lengths.get('♥', 0) >= 4:
                return ("1♥", "Showing a 4+ card heart suit.")
            if opening_bid in ['1♣', '1♦', '1♥'] and hand.suit_lengths.get('♠', 0) >= 4:
                return ("1♠", "Showing a 4+ card spade suit.")

            # 2-level new suit responses (require 10+ HCP in SAYC)
            # Bid a new suit at the 2-level with 10+ HCP and 5+ card suit
            if hand.hcp >= 10:
                # After 1♣ or 1♦ opening, can bid 2♦ or 2♣ or a major
                if opening_bid == '1♣':
                    if hand.suit_lengths.get('♦', 0) >= 5:
                        return ("2♦", "New suit at 2-level showing 10+ HCP and 5+ diamonds.")
                if opening_bid == '1♦':
                    if hand.suit_lengths.get('♣', 0) >= 5:
                        return ("2♣", "New suit at 2-level showing 10+ HCP and 5+ clubs.")

                # After 1♥ or 1♠ opening, can bid a lower-ranking suit at 2-level
                if opening_bid in ['1♥', '1♠']:
                    # Bid longest unbid suit (5+ cards) at 2-level
                    for suit in ['♦', '♣']:  # Check minors
                        if hand.suit_lengths.get(suit, 0) >= 5:
                            return (f"2{suit}", f"New suit at 2-level showing 10+ HCP and 5+ {suit}.")

                # After 1♥ opening, can bid 2♠ with 5+ spades and 10+ HCP
                if opening_bid == '1♥' and hand.suit_lengths.get('♠', 0) >= 5:
                    return ("2♠", "New suit showing 10+ HCP and 5+ spades (forcing).")

            # 2NT invitational response (11-12 HCP, balanced, no fit)
            if hand.is_balanced and 11 <= hand.hcp <= 12:
                return ("2NT", "Invitational showing 11-12 HCP, balanced, and no fit.")

            # 1NT response (6-10 HCP, balanced, no fit)
            # Note: Upper range adjusted from 9 to 10 since 11-12 now bids 2NT
            if hand.is_balanced and 6 <= hand.hcp <= 10:
                return ("1NT", "Shows 6-10 HCP, balanced, and no fit.")

        # With interference at 2-level or higher, need more to bid a new suit
        # Pass without a clear action
        return ("Pass", "No clear response available.")

    def _get_responder_rebid(self, hand: Hand, features: Dict, my_bids_after_opening: list):
        auction_features = features['auction_features']
        opening_bid = auction_features.get('opening_bid', '')

        # Special case: After 2♣ opening and 2♦ waiting response, auction is FORCING TO GAME
        # Responder cannot pass until game is reached
        if opening_bid == "2♣" and len(my_bids_after_opening) >= 1 and my_bids_after_opening[0] == "2♦":
            # We must bid until game is reached
            # Get partner's most recent bid to determine what they showed
            partner_last_bid = auction_features.get('partner_last_bid')

            if partner_last_bid and partner_last_bid != "Pass":
                # If partner showed a suit, we need to respond appropriately
                if len(partner_last_bid) >= 2 and partner_last_bid[1] in ['♣', '♦', '♥', '♠']:
                    partner_suit = partner_last_bid[1]

                    # With 2+ card support for a major, raise to game
                    if partner_suit in ['♥', '♠'] and hand.suit_lengths.get(partner_suit, 0) >= 2:
                        return (f"4{partner_suit}", f"Game bid showing support for partner's {partner_suit} in 2♣ auction.")

                    # With 3+ card support for any suit, raise
                    if hand.suit_lengths.get(partner_suit, 0) >= 3:
                        # Raise to game level
                        if partner_suit in ['♥', '♠']:
                            return (f"4{partner_suit}", f"Game bid showing support for partner's {partner_suit} in 2♣ auction.")
                        else:
                            # Minor suit - prefer 3NT if balanced, else 5-level
                            if hand.is_balanced or hand.hcp >= 8:
                                return ("3NT", "Game in NT with minor suit fit (2♣ auction).")
                            else:
                                return (f"5{partner_suit}", f"Game in {partner_suit} (2♣ auction).")

                    # Without support for partner's suit, bid 3NT with any balanced hand
                    # or show own 5+ card suit
                    for suit in ['♠', '♥', '♦', '♣']:
                        if hand.suit_lengths.get(suit, 0) >= 5:
                            return (f"3{suit}", f"Natural bid showing 5+ {suit} in game-forcing 2♣ auction.")

                    # No 5-card suit - bid 3NT (must reach game)
                    return ("3NT", "Game in NT (2♣ auction, no fit found).")

                # Partner bid 2NT - respond based on hand
                if 'NT' in partner_last_bid:
                    # With a 5+ card major, show it
                    for suit in ['♠', '♥']:
                        if hand.suit_lengths.get(suit, 0) >= 5:
                            return (f"3{suit}", f"Showing 5+ {suit} after partner's NT rebid.")
                    # Otherwise bid 3NT
                    return ("3NT", "Game in NT (2♣ auction).")

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