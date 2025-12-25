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

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple]:
        """
        Main entry point for responder rebid logic with bid validation.

        Only applies when:
        1. Partner opened
        2. We responded
        3. Partner rebid
        4. It's our turn again

        Returns:
            2-tuple (bid, explanation) or 3-tuple (bid, explanation, metadata)
        """
        auction_history = features['auction_history']

        # Get the raw rebid suggestion
        result = self._evaluate_rebid(hand, features)

        if not result:
            return None

        # Handle 2-tuple or 3-tuple results
        bid = result[0]
        explanation = result[1]
        metadata = result[2] if len(result) > 2 else None

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
            if metadata:
                return (next_legal, adjusted_explanation, metadata)
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

        # SPECIAL CASE: Check for Stayman continuation
        # Pattern: 1NT - 2♣ - 2♦/2♥/2♠ - ?
        # After Stayman response, responder must continue based on fit and strength
        if opening_bid == '1NT' and my_first_response == '2♣':
            stayman_result = self._handle_post_stayman(hand, opener_rebid, features)
            if stayman_result:
                return stayman_result

        # SPECIAL CASE: Check for Jacoby Transfer completion
        # Pattern: 1NT - 2♦ - 2♥ or 1NT - 2♥ - 2♠
        # After transfer completion, responder must decide based on strength
        if opening_bid == '1NT':
            transfer_result = self._handle_post_jacoby_transfer(hand, my_first_response, opener_rebid)
            if transfer_result:
                return transfer_result

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

        # Case 2: Opener bid notrump (e.g., 1♣ - 1♥ - 1NT or 1♣ - 1♠ - 2NT)
        if opener_rebid_type == 'notrump':
            opener_rebid = context['opener_rebid']

            # IMPORTANT: 2NT rebid (18-19 HCP) is FORCING TO GAME in SAYC
            # Responder MUST bid even with minimum
            if opener_rebid == '2NT':
                # With 6+ card major, bid 3M (gives opener choice)
                if my_first_suit in ['♥', '♠'] and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                    return (f"3{my_first_suit}", f"Showing 6+ {my_first_suit} after forcing 2NT rebid. Opener can raise to 4{my_first_suit} or pass.")
                # Otherwise bid 3NT - game is guaranteed with 2NT (18-19) + any response (6+)
                return ("3NT", f"Game in NT after partner's forcing 2NT rebid ({hand.hcp} HCP). Combined 24+ HCP.")

            # 1NT rebid (12-14 HCP) is NOT forcing - can pass with minimum
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

        # Case 2: Opener bid notrump - respond appropriately
        if opener_rebid_type == 'notrump':
            # 2NT rebid is FORCING - must bid game
            if opener_rebid == '2NT':
                # With 6+ card major, show it (partner can raise or pass 3NT)
                if my_first_suit in ['♥', '♠'] and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                    return (f"3{my_first_suit}", f"Showing 6+ {my_first_suit} after forcing 2NT. Partner decides between 4{my_first_suit} and 3NT.")
                # With invitational values (10-12), just bid 3NT - combined 28-31 is game
                return ("3NT", f"Game after partner's forcing 2NT rebid ({hand.hcp} HCP). Combined 28-31 HCP.")

            # Check if opener bid 1NT (invite to 2NT or 3NT)
            if opener_rebid == '1NT':
                # With 6+ card major, jump to 3-level (invitational)
                if my_first_suit in ['♥', '♠'] and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                    return (f"3{my_first_suit}", f"Invitational with 6+ {my_first_suit} and 10-12 pts.")

                # Otherwise invite with 2NT
                if hand.is_balanced:
                    return ("2NT", "Invitational with 10-12 HCP, asking partner to bid 3NT with maximum.")

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

    def _handle_post_stayman(self, hand: Hand, opener_rebid: str,
                              features: Dict) -> Optional[Tuple[str, str]]:
        """
        Handle responder's rebid after Stayman response.

        Sequences handled:
        - 1NT - 2♣ - 2♦ - ? (opener denied 4-card major)
        - 1NT - 2♣ - 2♥ - ? (opener showed 4+ hearts)
        - 1NT - 2♣ - 2♠ - ? (opener showed 4+ spades)

        SAYC Guidelines (partner opened 1NT = 15-17 HCP):
        - 8-9 HCP: Invitational (2NT or 3M if fit found)
        - 10-14 HCP: Game values (3NT, 4M if fit found)
        - 15+ HCP: Slam interest (explored via 4NT/quantitative)

        Key Context:
        - Responder bid Stayman (2♣) with at least one 4-card major
        - Opener's response tells us about THEIR major holdings
        - We need to combine this info to find the best contract

        Returns:
            3-tuple (bid, explanation, metadata) with bypass_hcp=True for convention bids
        """
        hcp = hand.hcp
        spade_length = hand.suit_lengths.get('♠', 0)
        heart_length = hand.suit_lengths.get('♥', 0)

        # Partner has 15-17 HCP
        partner_min = 15
        combined_min = hcp + partner_min

        # Metadata to bypass validation for Stayman convention bids
        # Stayman with 8-9 HCP bidding 3M is valid (invitational raise with fit)
        # Stayman with 10-14 HCP bidding 4M is valid (game with fit)
        # Also bypass suit length - 4 cards is enough when raising partner's shown major
        stayman_metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'stayman_continuation'}

        # Case 1: Opener bid 2♦ (no 4-card major)
        if opener_rebid == '2♦':
            # No major fit possible via Stayman
            # With invitational: 2NT
            # With game values: 3NT
            # With 5-card major: show it

            # Check for 5-card major (we had 4-card to bid Stayman, maybe also have 5 in other)
            if spade_length >= 5:
                # Show 5-card spade suit
                if 8 <= hcp <= 9:
                    return ("2♠", f"Invitational with 5 spades after Stayman denial. Partner raises with 3+ spades or bids 2NT/3NT.", stayman_metadata)
                elif hcp >= 10:
                    return ("3♠", f"Game-forcing with 5+ spades. Partner bids 4♠ with 3+ support or 3NT.", stayman_metadata)

            if heart_length >= 5:
                # Show 5-card heart suit
                if 8 <= hcp <= 9:
                    return ("2♥", f"Invitational with 5 hearts after Stayman denial. Partner raises or bids NT.", stayman_metadata)
                elif hcp >= 10:
                    return ("3♥", f"Game-forcing with 5+ hearts. Partner bids 4♥ with 3+ support or 3NT.", stayman_metadata)

            # No 5-card major - bid NT based on strength
            if 8 <= hcp <= 9:
                return ("2NT", f"Invitational after Stayman ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
            elif 10 <= hcp <= 14:
                return ("3NT", f"Game after Stayman denial ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
            elif hcp >= 15:
                return ("4NT", f"Quantitative slam invite ({hcp} HCP). Partner bids 6NT with 17 HCP.", stayman_metadata)

        # Case 2: Opener bid 2♥ (has 4+ hearts)
        elif opener_rebid == '2♥':
            # We have a heart fit if we have 4+ hearts
            if heart_length >= 4:
                # Heart fit found!
                if 8 <= hcp <= 9:
                    return ("3♥", f"Invitational with 4+ heart fit. Partner bids 4♥ with 16-17 HCP.", stayman_metadata)
                elif 10 <= hcp <= 14:
                    return ("4♥", f"Game with 4+ heart fit ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
                elif hcp >= 15:
                    # Slam interest with fit
                    return ("4NT", f"RKCB for hearts - slam interest with 4+ heart fit and {hcp} HCP.", stayman_metadata)

            else:
                # No heart fit - we must have 4 spades (why we bid Stayman)
                # Opener may also have 4 spades (could have bid up-the-line)
                # Ask about spades or bid NT

                # With 4 spades, bid NT (opener showed hearts first, so prefers hearts)
                if 8 <= hcp <= 9:
                    return ("2NT", f"Invitational, no heart fit ({hcp} HCP). Have 4 spades but partner bid hearts.", stayman_metadata)
                elif hcp >= 10:
                    # With game values, we can bid 3♠ to check for 4-4 spade fit
                    # (opener might have both majors)
                    if spade_length >= 4:
                        return ("3♠", f"Game-forcing, showing 4 spades. Partner bids 4♠ with 4 spades, else 3NT.", stayman_metadata)
                    return ("3NT", f"Game, no heart fit ({hcp} HCP).", stayman_metadata)

        # Case 3: Opener bid 2♠ (has 4+ spades)
        elif opener_rebid == '2♠':
            # We have a spade fit if we have 4+ spades
            if spade_length >= 4:
                # Spade fit found!
                if 8 <= hcp <= 9:
                    return ("3♠", f"Invitational with 4+ spade fit. Partner bids 4♠ with 16-17 HCP.", stayman_metadata)
                elif 10 <= hcp <= 14:
                    return ("4♠", f"Game with 4+ spade fit ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
                elif hcp >= 15:
                    # Slam interest with fit
                    return ("4NT", f"RKCB for spades - slam interest with 4+ spade fit and {hcp} HCP.", stayman_metadata)

            else:
                # No spade fit - we must have 4 hearts (why we bid Stayman)
                # Opener doesn't have 4 hearts (would have bid 2♥ first with both)
                # Bid NT based on strength

                if 8 <= hcp <= 9:
                    return ("2NT", f"Invitational, no spade fit ({hcp} HCP). Have 4 hearts but partner denied.", stayman_metadata)
                elif hcp >= 10:
                    return ("3NT", f"Game, no spade fit ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)

        return None  # Unexpected Stayman response

    def _handle_post_jacoby_transfer(self, hand: Hand, my_first_response: str,
                                     opener_rebid: str) -> Optional[Tuple[str, str]]:
        """
        Handle responder's rebid after Jacoby Transfer completion or super-accept.

        Sequences handled:
        - 1NT - 2♦ - 2♥ - ? (after heart transfer)
        - 1NT - 2♥ - 2♠ - ? (after spade transfer)
        - 1NT - 2♦ - 3♥ - ? (after heart super-accept)
        - 1NT - 2♥ - 3♠ - ? (after spade super-accept)

        SAYC Guidelines (partner opened 1NT = 15-17 HCP):
        - 0-7 HCP: Pass (combined 15-24, not enough for game)
        - 8-9 HCP: Invite (2NT or 3M) - combined 23-26, borderline
        - 10+ HCP: Game (4M or 3NT) - combined 25+, game values

        Super-accept (3M) shows 17 HCP + 4-card support:
        - Any hand: Accept game (4M) - partner has max with fit
        - Slam interest (10+ HCP): Explore slam

        With 5-card major:
        - Minimum: Pass at 2M
        - Invitational: Bid 2NT (5 cards) or 3M (6 cards)
        - Game values: Bid 3NT (5 cards) or 4M (6 cards)

        With 6+ card major:
        - Minimum: Pass at 2M
        - Invitational: Bid 3M (invites game)
        - Game values: Bid 4M
        """
        # Metadata to bypass validation for Jacoby convention bids
        jacoby_metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'jacoby_continuation'}

        # Check for super-accept first (3-level response to transfer)
        # Super-accept: Opener shows max (17 HCP) with 4+ card support
        if my_first_response == '2♦' and opener_rebid == '3♥':
            # Partner super-accepted hearts - bid 4♥ with any hand
            # Partner has 17 HCP + 4 hearts, combined minimum is responder's HCP + 17
            if hand.hcp >= 10:
                # Slam interest - use RKCB
                return ("4NT", f"RKCB for hearts - slam interest after super-accept ({hand.hcp} HCP + partner's 17).", jacoby_metadata)
            else:
                # Accept game
                return ("4♥", f"Accepting super-accept - partner showed max with 4+ hearts ({hand.hcp} HCP + partner's 17).", jacoby_metadata)

        if my_first_response == '2♥' and opener_rebid == '3♠':
            # Partner super-accepted spades - bid 4♠ with any hand
            if hand.hcp >= 10:
                # Slam interest - use RKCB
                return ("4NT", f"RKCB for spades - slam interest after super-accept ({hand.hcp} HCP + partner's 17).", jacoby_metadata)
            else:
                # Accept game
                return ("4♠", f"Accepting super-accept - partner showed max with 4+ spades ({hand.hcp} HCP + partner's 17).", jacoby_metadata)

        # Check if this is a standard Jacoby transfer completion
        # 2♦ transfer completed with 2♥
        if my_first_response == '2♦' and opener_rebid == '2♥':
            major = '♥'
            major_name = 'hearts'
        # 2♥ transfer completed with 2♠
        elif my_first_response == '2♥' and opener_rebid == '2♠':
            major = '♠'
            major_name = 'spades'
        else:
            return None  # Not a transfer completion or super-accept

        major_length = hand.suit_lengths.get(major, 0)
        hcp = hand.hcp
        total_pts = hand.total_points

        # Partner has 15-17 HCP, estimate combined strength
        partner_min = 15
        partner_max = 17
        combined_min = hcp + partner_min
        combined_max = hcp + partner_max

        # MINIMUM (0-7 HCP): Pass - not enough for game
        if hcp <= 7:
            return ("Pass", f"Minimum hand ({hcp} HCP), signing off in 2{major}. Combined {combined_min}-{combined_max} HCP.")

        # INVITATIONAL (8-9 HCP): Combined 23-26 HCP, borderline for game
        if 8 <= hcp <= 9:
            if major_length >= 6:
                # With 6+ card major, invite in the suit
                return (f"3{major}", f"Invitational with {hcp} HCP and 6+ {major_name}. Partner bids 4{major} with max.")
            else:
                # With 5-card major, invite via 2NT (lets partner choose 3NT or 3M)
                return ("2NT", f"Invitational with {hcp} HCP and 5 {major_name}. Partner can pass, bid 3{major}, or 3NT.")

        # GAME VALUES (10+ HCP): Combined 25+ HCP
        if hcp >= 10:
            if major_length >= 6:
                # With 6+ card major, bid game in the major
                return (f"4{major}", f"Game with {hcp} HCP and 6+ {major_name}. Combined {combined_min}+ HCP.")
            else:
                # With 5-card major, offer choice between 3NT and 4M
                # Bid 3NT to show balanced game values, opener can correct to 4M with 3+ support
                if hand.is_balanced:
                    return ("3NT", f"Game with {hcp} HCP and 5 {major_name}. Partner can pass or correct to 4{major}.")
                else:
                    # Unbalanced with only 5-card major - still bid 4M, partner has 2+ for Jacoby
                    return (f"4{major}", f"Game with {hcp} HCP, 5 {major_name}, unbalanced. Partner has 2+ {major_name}.")

        return None  # Should not reach here

# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("responder_rebid", ResponderRebidModule())
