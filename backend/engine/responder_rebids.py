from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict, List

class ResponderRebidModule(ConventionModule):
    """
    Comprehensive logic for responder's second (and subsequent) bids.

    Handles auctions like:
    - 1♣ - 1♥ - 1♠ - ? (responder's second bid)
    - 1♦ - 1♠ - 2♣ - ? (responder shows preference)
    - 1♥ - 1♠ - 1NT - ? (responder rebids after opener's 1NT)

    SAYC Rules:
    - 6-9 points: Sign off (pass, simple preference, simple rebid)
    - 10-12 points: Invite (jump preference, 2NT, jump in own suit)
    - 13+ points: Force to game (3NT, 4M, new suit forcing, FSF)
    """

    # Suit ranking for various calculations
    SUIT_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Main entry point for responder rebid logic with bid validation.

        Only applies when:
        1. Partner opened
        2. We responded
        3. Partner rebid
        4. It's our turn again
        """
        auction_history = features['auction_history']

        # Get the raw rebid suggestion
        result = self._evaluate_rebid(hand, features)

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
            # SANITY CHECK: If adjustment is more than 2 levels, something is wrong
            # This prevents runaway bid escalation (e.g., 2NT→7NT)
            try:
                original_level = int(bid[0])
                adjusted_level = int(next_legal[0])

                if adjusted_level - original_level > 2:
                    # The suggested bid is way off - pass instead of making unreasonable bid
                    return ("Pass", f"Cannot make reasonable rebid at current auction level (suggested {bid}, would need {next_legal}).")
            except (ValueError, IndexError):
                # Not a level bid (e.g., Pass, X, XX) - allow adjustment
                pass

            adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
            return (next_legal, adjusted_explanation)

        # No legal bid possible - pass
        return None

    def _evaluate_rebid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates rebid without validation."""
        auction_features = features['auction_features']
        auction_history = features['auction_history']

        # SAFETY CHECK: If auction is already at slam level and we don't have slam values, pass
        # This prevents responders with 10-12 HCP from bidding slam
        if auction_history:
            # Find highest bid level in auction
            max_level = 0
            for bid in auction_history:
                if bid not in ['Pass', 'X', 'XX'] and len(bid) >= 1 and bid[0].isdigit():
                    level = int(bid[0])
                    max_level = max(max_level, level)

            # If auction is at 5-level or higher and we have < 18 HCP, pass
            # (Need ~33+ combined for slam, so if partner has 15-20 and we have < 18, not enough)
            if max_level >= 5 and hand.hcp < 18:
                return ("Pass", f"Auction already at {max_level}-level, insufficient values for slam (have {hand.hcp} HCP).")

        # Check if partner is the opener
        if auction_features.get('opener_relationship') != 'Partner':
            return None

        opening_bid = auction_features.get('opening_bid')
        opener_index = auction_features.get('opener_index', -1)
        my_index = features['my_index']

        if not opening_bid or opener_index == -1:
            return None

        # Count my bids AFTER partner's opening
        my_bids_after_opening = [
            bid for i, bid in enumerate(auction_history)
            if (i % 4) == my_index and i > opener_index and bid not in ['Pass', 'X', 'XX']
        ]

        # Only apply if I've already made at least one bid (this is my second+ bid)
        if len(my_bids_after_opening) < 1:
            return None  # First response handled by ResponseModule

        # Get my first response
        my_first_response = my_bids_after_opening[0]

        # Get opener's rebid (their second bid)
        opener_bids = [
            bid for i, bid in enumerate(auction_history)
            if (i % 4) == opener_index and bid not in ['Pass', 'X', 'XX']
        ]

        if len(opener_bids) < 2:
            return None  # Opener hasn't rebid yet

        opener_rebid = opener_bids[1]

        # Classify the auction context
        auction_context = self._analyze_auction_context(
            opening_bid, my_first_response, opener_rebid, hand
        )

        # Route to appropriate rebid handler based on strength
        if 6 <= hand.total_points <= 9:
            return self._minimum_rebid(hand, auction_context, features)
        elif 10 <= hand.total_points <= 12:
            return self._invitational_rebid(hand, auction_context, features)
        elif hand.total_points >= 13:
            return self._game_forcing_rebid(hand, auction_context, features)

        return None

    def _analyze_auction_context(self, opening_bid: str, my_first_response: str,
                                 opener_rebid: str, hand: Hand) -> Dict:
        """
        Analyze the auction to understand what's happening.

        Returns context dictionary with:
        - opener_rebid_type: 'same_suit', 'new_suit', 'notrump', 'reverse', 'jump'
        - opener_first_suit: First suit shown by opener
        - opener_second_suit: Second suit shown by opener (if applicable)
        - my_first_suit: Suit I showed in first response
        - suits_bid: List of all suits bid so far
        - unbid_suit: The fourth suit (for FSF detection)
        - is_forcing: Whether current auction is forcing
        """
        context = {}

        # Extract suits from bids
        opener_first_suit = opening_bid[1] if len(opening_bid) >= 2 and opening_bid[1] in '♣♦♥♠' else None
        opener_rebid_suit = opener_rebid[1] if len(opener_rebid) >= 2 and opener_rebid[1] in '♣♦♥♠' else None
        my_first_suit = my_first_response[1] if len(my_first_response) >= 2 and my_first_response[1] in '♣♦♥♠' else None

        context['opener_first_suit'] = opener_first_suit
        context['opener_second_suit'] = opener_rebid_suit if opener_rebid_suit != opener_first_suit else None
        context['my_first_suit'] = my_first_suit
        context['opening_bid'] = opening_bid
        context['opener_rebid'] = opener_rebid
        context['my_first_response'] = my_first_response

        # Determine opener's rebid type
        if 'NT' in opener_rebid:
            context['opener_rebid_type'] = 'notrump'
        elif opener_rebid_suit == opener_first_suit:
            # Check for jump rebid
            opener_level = int(opening_bid[0])
            rebid_level = int(opener_rebid[0])
            if rebid_level > opener_level + 1:
                context['opener_rebid_type'] = 'jump_rebid'
            else:
                context['opener_rebid_type'] = 'same_suit'
        elif opener_rebid_suit and opener_rebid_suit != opener_first_suit:
            # New suit - check if it's a reverse
            if self._is_reverse(opening_bid, opener_rebid):
                context['opener_rebid_type'] = 'reverse'
            else:
                context['opener_rebid_type'] = 'new_suit'
        else:
            context['opener_rebid_type'] = 'unknown'

        # Track all suits bid
        suits_bid = []
        if opener_first_suit:
            suits_bid.append(opener_first_suit)
        if opener_rebid_suit and opener_rebid_suit != opener_first_suit:
            suits_bid.append(opener_rebid_suit)
        if my_first_suit:
            suits_bid.append(my_first_suit)

        context['suits_bid'] = suits_bid

        # Find unbid suit (for Fourth Suit Forcing)
        all_suits = ['♣', '♦', '♥', '♠']
        unbid_suits = [s for s in all_suits if s not in suits_bid]
        context['unbid_suit'] = unbid_suits[0] if len(unbid_suits) == 1 else None

        # Determine if auction is forcing
        # Reverses are forcing, jump rebids are invitational+
        context['is_forcing'] = (context['opener_rebid_type'] in ['reverse', 'jump_rebid'])

        return context

    def _is_reverse(self, opening_bid: str, rebid: str) -> bool:
        """
        Determine if opener's rebid is a reverse.

        A reverse occurs when:
        1. Opener bids a new suit at the 2-level
        2. The new suit ranks HIGHER than the opening suit
        3. Shows 17+ HCP, forcing one round

        Examples:
        - 1♦ - 1♠ - 2♥ = REVERSE (hearts > diamonds)
        - 1♣ - 1♥ - 2♦ = NOT reverse (diamonds < hearts, but > clubs)
        - 1♥ - 1♠ - 2♦ = NOT reverse (diamonds < hearts)
        """
        if not opening_bid or not rebid or len(opening_bid) < 2 or len(rebid) < 2:
            return False

        opening_suit = opening_bid[1]
        rebid_suit = rebid[1]

        # Must be at 2-level
        if rebid[0] != '2':
            return False

        # Must be different suits
        if opening_suit == rebid_suit:
            return False

        # New suit must rank higher than opening suit
        return self.SUIT_RANK.get(rebid_suit, 0) > self.SUIT_RANK.get(opening_suit, 0)

    def _minimum_rebid(self, hand: Hand, context: Dict, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Handle minimum strength rebids (6-9 points).

        Philosophy: Sign off, don't encourage game.

        Priorities:
        1. Pass if comfortable with current contract
        2. Give simple preference between opener's suits
        3. Rebid own 6+ card suit at 2-level
        4. Bid 2NT as last resort (rare with minimum)
        """
        opener_rebid_type = context['opener_rebid_type']
        opener_first_suit = context['opener_first_suit']
        opener_second_suit = context['opener_second_suit']
        my_first_suit = context['my_first_suit']

        # Special case: Forced to bid after reverse (reverse is forcing)
        if context['is_forcing']:
            return self._minimum_forced_bid(hand, context)

        # Case 1: Opener rebid same suit (e.g., 1♥ - 1♠ - 2♥)
        if opener_rebid_type == 'same_suit':
            # Pass with 2+ card support (we're happy with the fit)
            if hand.suit_lengths.get(opener_first_suit, 0) >= 2:
                return ("Pass", f"Minimum hand (6-9 pts), satisfied with {opener_first_suit} contract.")

            # Rebid own 6+ card suit if available
            if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                return (f"2{my_first_suit}", f"Minimum hand rebidding 6+ card {my_first_suit} suit.")

            # Otherwise pass (no better option)
            return ("Pass", f"Minimum hand, no better option than {context['opener_rebid']}.")

        # Case 2: Opener bid notrump (e.g., 1♣ - 1♥ - 1NT)
        if opener_rebid_type == 'notrump':
            # Pass with balanced minimum
            if hand.is_balanced or hand.suit_lengths.get(my_first_suit, 0) < 6:
                return ("Pass", "Minimum hand, accepting notrump contract.")

            # Rebid 6+ card suit (not forcing after 1NT rebid)
            if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                return (f"2{my_first_suit}", f"Minimum hand with 6+ card {my_first_suit} suit, to play.")

            return ("Pass", "Minimum hand, passing 1NT.")

        # Case 3: Opener showed two suits (e.g., 1♣ - 1♥ - 1♠)
        if opener_rebid_type == 'new_suit' and opener_second_suit:
            return self._give_preference(hand, opener_first_suit, opener_second_suit, strength='minimum')

        # Case 4: Opener made jump rebid (invitational)
        if opener_rebid_type == 'jump_rebid':
            # Decline invitation with minimum
            return ("Pass", "Minimum hand, declining partner's game invitation.")

        # Default: Pass
        return ("Pass", "Minimum hand, no clear rebid available.")

    def _minimum_forced_bid(self, hand: Hand, context: Dict) -> Tuple[str, str]:
        """
        Handle minimum rebids when forced to bid (after reverse or other forcing situation).

        With minimum values after a forcing bid:
        - Bid 2NT as "no fit" signal
        - Rebid own suit cheaply
        - Give preference to opener's first suit
        """
        opener_first_suit = context['opener_first_suit']
        my_first_suit = context['my_first_suit']

        # Prefer to rebid own 6+ card suit
        if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
            return (f"3{my_first_suit}", f"Forced to bid, showing 6+ {my_first_suit} with minimum.")

        # Give preference to opener's first suit with 3+ cards
        if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
            return (f"3{opener_first_suit}", f"Forced to bid, preference to {opener_first_suit} with minimum.")

        # Bid 2NT as weakness signal
        return ("2NT", "Forced to bid after partner's reverse, showing minimum values.")

    def _give_preference(self, hand: Hand, suit1: str, suit2: str, strength: str) -> Tuple[str, str]:
        """
        Give preference between two suits shown by opener.

        Logic:
        1. Choose suit based on length (prefer longer)
        2. If equal length, prefer first suit
        3. Level depends on strength (minimum=2-level, invitational=3-level)
        """
        len1 = hand.suit_lengths.get(suit1, 0)
        len2 = hand.suit_lengths.get(suit2, 0)

        # Determine preferred suit
        if len1 > len2:
            preferred_suit = suit1
            card_count = len1
        elif len2 > len1:
            preferred_suit = suit2
            card_count = len2
        else:
            # Equal length - prefer first suit (standard practice)
            preferred_suit = suit1
            card_count = len1

        # Determine level based on strength
        if strength == 'minimum':
            level = '2'
            explanation = f"Simple preference to {preferred_suit} with {card_count}+ cards (minimum hand)."
        elif strength == 'invitational':
            level = '3'
            explanation = f"Jump preference to {preferred_suit} with {card_count}+ cards (invitational, 10-12 pts)."
        else:  # game-forcing
            # With game-forcing values, bid game if major, otherwise 3-level
            if preferred_suit in ['♥', '♠']:
                level = '4'
                explanation = f"Game in {preferred_suit} with {card_count}+ card fit."
            else:
                level = '5' if card_count >= 4 else '3'
                explanation = f"Preference to {preferred_suit} with game-forcing values."

        return (f"{level}{preferred_suit}", explanation)

    def _invitational_rebid(self, hand: Hand, context: Dict, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Handle invitational strength rebids (10-12 points).

        Philosophy: Invite game, let opener decide.

        Priorities:
        1. Jump raise opener's suit (3-level)
        2. Bid 2NT with balanced hand and stoppers
        3. Jump in own suit (3-level) with 6+ cards
        4. Jump preference between opener's suits
        """
        opener_rebid_type = context['opener_rebid_type']
        opener_first_suit = context['opener_first_suit']
        opener_second_suit = context['opener_second_suit']
        my_first_suit = context['my_first_suit']
        opener_rebid = context['opener_rebid']

        # Case 1: Opener rebid same suit - jump raise with fit
        if opener_rebid_type == 'same_suit':
            if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                return (f"3{opener_first_suit}", f"Invitational raise (10-12 pts) with 3+ {opener_first_suit}.")

            # Jump rebid own suit with 6+ cards
            if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                return (f"3{my_first_suit}", f"Invitational jump showing 6+ {my_first_suit} and 10-12 pts.")

            # Bid 2NT with balanced hand
            if hand.is_balanced and hand.hcp >= 10:
                return ("2NT", "Invitational with 10-12 HCP, balanced.")

        # Case 2: Opener bid notrump - invite to 3NT
        if opener_rebid_type == 'notrump':
            # Check if opener bid 1NT (invite to 2NT or 3NT)
            if opener_rebid == '1NT':
                # With 6+ card major, jump to 3-level (invitational)
                if my_first_suit in ['♥', '♠'] and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                    return (f"3{my_first_suit}", f"Invitational with 6+ {my_first_suit} and 10-12 pts.")

                # Otherwise invite with 2NT
                if hand.is_balanced:
                    return ("2NT", "Invitational with 10-12 HCP, asking partner to bid 3NT with maximum.")

            # If opener bid 2NT, raise to 3NT with maximum (12 pts)
            if opener_rebid == '2NT' and hand.hcp >= 12:
                return ("3NT", "Accepting partner's 2NT invitation with 12 HCP.")

        # Case 3: Opener showed two suits - jump preference
        if opener_rebid_type == 'new_suit' and opener_second_suit:
            return self._give_preference(hand, opener_first_suit, opener_second_suit, strength='invitational')

        # Case 4: Opener made jump rebid (already invitational) - accept with maximum
        if opener_rebid_type == 'jump_rebid':
            if hand.total_points >= 11:
                # Accept invitation by bidding game
                if opener_first_suit in ['♥', '♠'] and hand.suit_lengths.get(opener_first_suit, 0) >= 2:
                    return (f"4{opener_first_suit}", f"Accepting game invitation with {hand.total_points} pts.")
                return ("3NT", f"Accepting game invitation with {hand.total_points} pts.")
            else:
                # Decline with 10 pts
                return ("Pass", "Declining partner's invitation with 10 pts.")

        # Case 5: After reverse (forcing) - show invitational values
        if context['is_forcing']:
            # With invitational values after reverse, bid game if good fit
            if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                return (f"3{opener_first_suit}", f"Showing support for {opener_first_suit} with invitational values.")

            # Bid 2NT showing invitational balanced
            if hand.is_balanced:
                return ("2NT", "Showing invitational values (10-12 pts) after partner's reverse.")

        # Default: Bid 2NT invitational
        if hand.is_balanced:
            return ("2NT", "Invitational with 10-12 HCP, balanced.")

        return None

    def _game_forcing_rebid(self, hand: Hand, context: Dict, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Handle game-forcing strength rebids (13+ points).

        Philosophy: Ensure game is reached, explore best strain.

        Priorities:
        1. Bid game directly if strain is clear
        2. Use Fourth Suit Forcing to gather more info
        3. Bid new suit (forcing) to show distribution
        4. Jump to 3NT with balanced hand
        """
        opener_rebid_type = context['opener_rebid_type']
        opener_first_suit = context['opener_first_suit']
        opener_second_suit = context['opener_second_suit']
        my_first_suit = context['my_first_suit']
        opener_rebid = context['opener_rebid']
        unbid_suit = context['unbid_suit']

        # Case 1: Opener rebid same suit - raise to game with fit
        if opener_rebid_type == 'same_suit':
            if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                if opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", f"Game with {opener_first_suit} fit (13+ pts).")
                else:
                    # Minor suit - prefer 3NT if balanced
                    if hand.is_balanced:
                        return ("3NT", f"Game in NT with {opener_first_suit} fit but balanced hand.")
                    return (f"5{opener_first_suit}", f"Game in {opener_first_suit} (13+ pts).")

            # No fit - bid 3NT if balanced
            if hand.is_balanced and hand.hcp >= 13:
                return ("3NT", "Game in NT with 13+ HCP, balanced, no fit.")

            # Jump in own suit to show 6+ cards game-forcing
            if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                if my_first_suit in ['♥', '♠']:
                    return (f"4{my_first_suit}", f"Game in {my_first_suit} with 6+ card suit.")
                else:
                    return (f"3{my_first_suit}", f"Game-forcing jump in {my_first_suit}.")

        # Case 2: Opener bid notrump - raise to game or show suit
        if opener_rebid_type == 'notrump':
            if opener_rebid == '1NT':
                # With 6+ card major, bid game
                if my_first_suit in ['♥', '♠'] and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                    return (f"4{my_first_suit}", f"Game with 6+ {my_first_suit} and 13+ pts.")

                # Otherwise bid 3NT
                return ("3NT", "Game in NT with 13+ HCP.")

            if opener_rebid == '2NT':
                # Raise to 3NT
                return ("3NT", "Game in NT accepting partner's 2NT rebid.")

        # Case 3: Opener showed two suits - decide on best game
        if opener_rebid_type == 'new_suit' and opener_second_suit:
            # Check for fit in either suit
            fit1 = hand.suit_lengths.get(opener_first_suit, 0)
            fit2 = hand.suit_lengths.get(opener_second_suit, 0)

            # Bid game with fit in major
            if fit1 >= 3 and opener_first_suit in ['♥', '♠']:
                return (f"4{opener_first_suit}", f"Game with {opener_first_suit} fit.")
            if fit2 >= 3 and opener_second_suit in ['♥', '♠']:
                return (f"4{opener_second_suit}", f"Game with {opener_second_suit} fit.")

            # No major fit - check for Fourth Suit Forcing
            if unbid_suit and hand.hcp >= 12:
                # Fourth Suit Forcing - ask for more info
                return (f"2{unbid_suit}", f"Fourth Suit Forcing, asking for more information (game-forcing).")

            # Bid 3NT with balanced and stoppers
            if hand.is_balanced:
                return ("3NT", "Game in NT with balanced hand, no major fit.")

            # Give preference at game level
            return self._give_preference(hand, opener_first_suit, opener_second_suit, strength='game-forcing')

        # Case 4: After jump rebid - bid game
        if opener_rebid_type == 'jump_rebid':
            if hand.suit_lengths.get(opener_first_suit, 0) >= 2:
                if opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", "Game accepting partner's strong jump rebid.")
                return ("3NT", "Game accepting partner's jump rebid.")
            return ("3NT", "Game in NT with 13+ HCP.")

        # Case 5: After reverse (already forcing) - continue to game
        if context['is_forcing']:
            # Bid game with fit
            if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                if opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", f"Game with {opener_first_suit} support.")
                return ("3NT", f"Game with {opener_first_suit} support.")

            # Bid 3NT with balanced
            if hand.is_balanced:
                return ("3NT", "Game in NT with 13+ HCP after partner's reverse.")

        # Default: Bid 3NT
        if hand.is_balanced and hand.hcp >= 13:
            return ("3NT", "Game in NT with 13+ HCP.")

        return None
