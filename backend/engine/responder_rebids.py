from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from engine.responder_rebids_stayman import handle_post_stayman, handle_post_stayman_2nt
from engine.responder_rebids_transfers import handle_post_jacoby_transfer
from engine.responder_rebids_strong2c import handle_strong_2c_continuation
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

        # Bid is illegal - try to find next legal bid of same strain (max 1 level jump)
        next_legal = get_next_legal_bid(bid, auction_history, max_level_jump=1)
        if next_legal:
            # SANITY CHECK: If adjustment is more than 1 level, something is wrong
            try:
                original_level = int(bid[0])
                adjusted_level = int(next_legal[0])

                if adjusted_level - original_level > 1:
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

            # Bail out at 4-level+ without game-forcing values (unless in a game-forcing auction)
            if max_level >= 4 and hand.hcp < 13:
                bidding_state = features.get('bidding_state')
                is_game_forcing = False
                if bidding_state is not None:
                    from utils.seats import normalize, partnership_str
                    positions = features.get('positions', [])
                    my_index = features.get('my_index')
                    if positions and my_index is not None:
                        my_seat = normalize(positions[my_index])
                        is_game_forcing = bidding_state.forcing.get(partnership_str(my_seat)) == 'game'
                if not is_game_forcing:
                    return ("Pass", f"Auction at {max_level}-level, insufficient for game ({hand.hcp} HCP).")

            # SAFETY CHECK: If partnership has already reached game (3NT, 4M, 5m),
            # don't keep bidding unless we have slam values (33+ combined).
            # This prevents runaway auctions where modules generate stale bids
            # that get legality-adjusted upward past game.
            if self._partnership_reached_game(auction_history, features):
                combined = self._get_combined_estimate(hand, features)
                if combined < 33:
                    return ("Pass", f"Game already reached, insufficient for slam ({hand.hcp} HCP, combined ~{combined}).")

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

        # SPECIAL CASE: 2♣ Strong Opening
        # 2♣ is GAME FORCING (unless responder shows negative with 2♦ - 2NT sequence)
        # After 2♣ - 2♦ - 2NT, responder MUST continue to 3NT even with 0 points
        # After 2♣ - 2♦ - (suit), responder should continue until game is reached
        if opening_bid == '2♣':
            strong_result = handle_strong_2c_continuation(hand, opener_rebid, my_first_response, features)
            if strong_result:
                return strong_result

        # SPECIAL CASE: Check for Stayman continuation
        # Pattern: 1NT - 2♣ - 2♦/2♥/2♠ - ?
        # After Stayman response, responder must continue based on fit and strength
        if opening_bid == '1NT' and my_first_response == '2♣':
            stayman_result = handle_post_stayman(hand, opener_rebid, features)
            if stayman_result:
                return stayman_result

        # SPECIAL CASE: 2NT Stayman continuation
        # Pattern: 2NT - 3♣ - 3♦/3♥/3♠ - ?
        if opening_bid == '2NT' and my_first_response == '3♣':
            stayman_2nt_result = handle_post_stayman_2nt(hand, opener_rebid)
            if stayman_2nt_result:
                return stayman_2nt_result

        # SPECIAL CASE: Check for Jacoby Transfer completion
        # Pattern: 1NT - 2♦ - 2♥ or 1NT - 2♥ - 2♠
        # After transfer completion, responder must decide based on strength
        if opening_bid == '1NT':
            transfer_result = handle_post_jacoby_transfer(hand, my_first_response, opener_rebid)
            if transfer_result:
                return transfer_result

        # Classify the auction context
        rebid_context = self._analyze_auction_context(
            opening_bid, my_first_response, opener_rebid, hand,
            my_previous_bids=my_bids_after_opening
        )
        # Stash previous bids for downstream FSF fix
        rebid_context['my_bids_after_opening'] = my_bids_after_opening

        # Route to appropriate rebid handler based on strength
        if 6 <= hand.total_points <= 9:
            return self._minimum_rebid(hand, rebid_context, features)
        elif 10 <= hand.total_points <= 12:
            return self._invitational_rebid(hand, rebid_context, features)
        elif hand.total_points >= 13:
            return self._game_forcing_rebid(hand, rebid_context, features)

        return None

    def _analyze_auction_context(self, opening_bid: str, my_first_response: str,
                                 opener_rebid: str, hand: Hand,
                                 my_previous_bids: list = None) -> Dict:
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

        # Track all suits bid (including ALL of responder's previous bids)
        suits_bid = []
        if opener_first_suit:
            suits_bid.append(opener_first_suit)
        if opener_rebid_suit and opener_rebid_suit != opener_first_suit:
            suits_bid.append(opener_rebid_suit)
        if my_first_suit:
            suits_bid.append(my_first_suit)
        # Include suits from all of responder's previous bids (not just first)
        if my_previous_bids:
            for prev_bid in my_previous_bids:
                if len(prev_bid) >= 2 and prev_bid[1] in '♣♦♥♠':
                    prev_suit = prev_bid[1]
                    if prev_suit not in suits_bid:
                        suits_bid.append(prev_suit)

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

    # Combined HCP → max safe bid level (same thresholds as SanityChecker)
    MAX_BID_LEVELS = {
        (0, 19): 2, (20, 23): 3, (24, 32): 4,
        (33, 36): 6, (37, 40): 7, (41, 100): 7
    }

    def _get_max_safe_level(self, hand: Hand, features: Dict) -> int:
        """Compute max safe bid level from actual HCP + partner's estimated range."""
        combined = self._get_combined_estimate(hand, features)
        for (lo, hi), level in self.MAX_BID_LEVELS.items():
            if lo <= combined <= hi:
                return level
        return 2

    def _get_combined_estimate(self, hand: Hand, features: Dict) -> int:
        """
        Estimate combined HCP using actual hand + partner's range midpoint.

        Uses BiddingState per-seat beliefs, falls back to average opener estimate.
        """
        bidding_state = features.get('bidding_state')
        if bidding_state is not None:
            positions = features.get('positions', [])
            my_index = features.get('my_index')
            if positions and my_index is not None:
                from utils.seats import normalize
                my_seat = normalize(positions[my_index])
                partner_belief = bidding_state.partner_of(my_seat)
                spread = partner_belief.hcp[1] - partner_belief.hcp[0]
                if spread <= 25:
                    partner_mid = (partner_belief.hcp[0] + partner_belief.hcp[1]) // 2
                    return hand.hcp + partner_mid

        return hand.hcp + 14  # Fallback: assume average opener

    def _partnership_reached_game(self, auction_history: list, features: Dict) -> bool:
        """Check if any bid by me or partner is at game level (3NT, 4M, 5m+)."""
        positions = features.get('positions', [])
        my_index = features.get('my_index', 0)
        my_pos = positions[my_index] if positions else None
        partner_index = (my_index + 2) % 4
        partner_pos = positions[partner_index] if positions else None

        game_levels = {
            'NT': 3, '♥': 4, '♠': 4, '♦': 5, '♣': 5
        }

        for i, bid in enumerate(auction_history):
            if bid in ['Pass', 'X', 'XX']:
                continue
            bidder = positions[i % 4] if positions else None
            if bidder not in [my_pos, partner_pos]:
                continue
            try:
                level = int(bid[0])
                strain = bid[1:]
                game_threshold = game_levels.get(strain, 5)
                if level >= game_threshold:
                    return True
            except (ValueError, IndexError):
                continue
        return False

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
        max_safe_level = self._get_max_safe_level(hand, features)
        combined_midpoint = self._get_combined_estimate(hand, features)

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
                if 2 > max_safe_level:
                    return ("Pass", f"Minimum hand, cannot safely rebid at 2-level (max safe: {max_safe_level}).")
                return (f"2{my_first_suit}", f"Minimum hand rebidding 6+ card {my_first_suit} suit.")

            # Otherwise pass (no better option)
            return ("Pass", f"Minimum hand, no better option than {context['opener_rebid']}.")

        # Case 2: Opener bid notrump (e.g., 1♣ - 1♥ - 1NT or 1♣ - 1♠ - 2NT)
        if opener_rebid_type == 'notrump':
            opener_rebid = context['opener_rebid']

            # IMPORTANT: 2NT rebid (18-19 HCP) is FORCING TO GAME in SAYC
            # Responder MUST bid even with minimum - bypass HCP validation
            forcing_2nt_metadata = {'bypass_hcp': True, 'forcing_sequence': '2NT_rebid'}
            if opener_rebid == '2NT':
                # With 6+ card major, bid 3M (gives opener choice)
                if my_first_suit in ['♥', '♠'] and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                    return (f"3{my_first_suit}", f"Showing 6+ {my_first_suit} after forcing 2NT rebid. Opener can raise to 4{my_first_suit} or pass.", forcing_2nt_metadata)
                # Otherwise bid 3NT - game is guaranteed with 2NT (18-19) + any response (6+)
                return ("3NT", f"Game in NT after partner's forcing 2NT rebid ({hand.hcp} HCP). Combined 24+ HCP.", forcing_2nt_metadata)

            # 1NT rebid (12-14 HCP) is NOT forcing - can pass with minimum
            # Pass with balanced minimum
            if hand.is_balanced or hand.suit_lengths.get(my_first_suit, 0) < 6:
                return ("Pass", "Minimum hand, accepting notrump contract.")

            # Rebid 6+ card suit (not forcing after 1NT rebid)
            if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                if 2 > max_safe_level:
                    return ("Pass", f"Minimum hand, cannot safely rebid at 2-level (max safe: {max_safe_level}).")
                return (f"2{my_first_suit}", f"Minimum hand with 6+ card {my_first_suit} suit, to play.")

            return ("Pass", "Minimum hand, passing 1NT.")

        # Case 3: Opener showed two suits (e.g., 1♥ - 1♠ - 2♣)
        if opener_rebid_type == 'new_suit' and opener_second_suit:
            # Priority: Rebid own 6+ card suit before giving preference
            # With 6-card suit and minimum, we want to play in our suit rather than opener's
            if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                if 2 > max_safe_level:
                    return ("Pass", f"Minimum hand, cannot safely rebid at 2-level (max safe: {max_safe_level}).")
                return (f"2{my_first_suit}", f"Minimum hand rebidding 6+ card {my_first_suit} suit.")

            # Give preference between opener's suits
            return self._give_preference(hand, opener_first_suit, opener_second_suit, strength='minimum', context=context)

        # Case 4: Opener made jump rebid (invitational, 16-18 HCP)
        if opener_rebid_type == 'jump_rebid':
            # Accept if combined midpoint reaches game (24+) with fit
            if combined_midpoint >= 24 and hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                if opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", f"Accepting game invitation with {opener_first_suit} fit (combined ~{combined_midpoint}).")
                return ("3NT", f"Accepting game invitation (combined ~{combined_midpoint}).")
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

    def _give_preference(self, hand: Hand, suit1: str, suit2: str, strength: str, context: Dict = None) -> Tuple[str, str]:
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
            # With game-forcing values, bid game if major, otherwise 3NT preferred over 5m
            if preferred_suit in ['♥', '♠']:
                level = '4'
                explanation = f"Game in {preferred_suit} with {card_count}+ card fit."
            else:
                # Prefer 3NT over 5m (9 tricks easier than 11)
                level = '3'
                preferred_suit = 'NT'
                explanation = f"Game in NT preferred over 5-minor with game-forcing values."

        bid = f"{level}{preferred_suit}"
        
        # FIX: If our preference is exactly what partner just bid, we should Pass
        # unless we are raising (invitational/game forcing)
        if strength == 'minimum' and context:
             opener_rebid = context.get('opener_rebid')
             if opener_rebid == bid:
                 return ("Pass", f"Minimum hand, preferring {preferred_suit} (already bid by partner).")

        return (bid, explanation)

    def _invitational_rebid(self, hand: Hand, context: Dict, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Handle invitational strength rebids (10-12 points).

        Philosophy: Invite game, let opener decide.
        NEW: Use AuctionContext to check if combined points justify game.

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

        # Use partnership-wide combined HCP from AuctionContext
        combined_midpoint = self._get_combined_estimate(hand, features)
        max_safe_level = self._get_max_safe_level(hand, features)

        # Bid game when combined partnership values reach 25+
        should_bid_game = combined_midpoint >= 25

        # Case 1: Opener rebid same suit - jump raise with fit
        if opener_rebid_type == 'same_suit':
            if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                # With AuctionContext showing game values, bid game directly
                if should_bid_game and max_safe_level >= 4 and opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", f"Game with {opener_first_suit} fit (combined ~{combined_midpoint}).")
                elif should_bid_game and max_safe_level >= 3:
                    return ("3NT", f"Game in NT (combined ~{combined_midpoint}) with {opener_first_suit} fit.")
                if max_safe_level >= 3:
                    return (f"3{opener_first_suit}", f"Invitational raise (10-12 pts) with 3+ {opener_first_suit}.")
                return ("Pass", f"Cannot safely invite at 3-level (combined ~{combined_midpoint}).")

            # Jump rebid own suit with 6+ cards
            if my_first_suit and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                if should_bid_game and max_safe_level >= 4 and my_first_suit in ['♥', '♠']:
                    return (f"4{my_first_suit}", f"Game with 6+ {my_first_suit} (combined ~{combined_midpoint}).")
                if max_safe_level >= 3:
                    return (f"3{my_first_suit}", f"Invitational jump showing 6+ {my_first_suit} and 10-12 pts.")
                return ("Pass", f"Cannot safely invite at 3-level (combined ~{combined_midpoint}).")

            # Bid 2NT or 3NT with balanced hand
            if hand.is_balanced and hand.hcp >= 10:
                if should_bid_game and max_safe_level >= 3:
                    return ("3NT", f"Game in NT (combined ~{combined_midpoint}).")
                return ("2NT", "Invitational with 10-12 HCP, balanced.")

        # Case 2: Opener bid notrump - respond appropriately
        if opener_rebid_type == 'notrump':
            # 2NT rebid is FORCING - must bid game (bypass HCP validation)
            forcing_2nt_metadata = {'bypass_hcp': True, 'forcing_sequence': '2NT_rebid'}
            if opener_rebid == '2NT':
                # With 6+ card major, show it (partner can raise or pass 3NT)
                if my_first_suit in ['♥', '♠'] and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                    return (f"3{my_first_suit}", f"Showing 6+ {my_first_suit} after forcing 2NT. Partner decides between 4{my_first_suit} and 3NT.", forcing_2nt_metadata)
                # With invitational values (10-12), just bid 3NT - combined 28-31 is game
                return ("3NT", f"Game after partner's forcing 2NT rebid ({hand.hcp} HCP). Combined 28-31 HCP.", forcing_2nt_metadata)

            # Check if opener bid 1NT (invite to 2NT or 3NT)
            if opener_rebid == '1NT':
                # With 6+ card major, jump to game if combined values support it
                if my_first_suit in ['♥', '♠'] and hand.suit_lengths.get(my_first_suit, 0) >= 6:
                    if should_bid_game and max_safe_level >= 4:
                        return (f"4{my_first_suit}", f"Game with 6+ {my_first_suit} (combined ~{combined_midpoint}).")
                    if max_safe_level >= 3:
                        return (f"3{my_first_suit}", f"Invitational with 6+ {my_first_suit} and 10-12 pts.")
                    return ("Pass", f"Cannot safely invite at 3-level (combined ~{combined_midpoint}).")

                # With balanced hand, decide between 2NT and 3NT based on combined values
                if hand.is_balanced:
                    if should_bid_game and max_safe_level >= 3:
                        return ("3NT", f"Game in NT (combined ~{combined_midpoint}).")
                    return ("2NT", "Invitational with 10-12 HCP, asking partner to bid 3NT with maximum.")

            # If opener bid 2NT, raise to 3NT with 11+ pts (opener shows extras)
            if opener_rebid == '2NT' and hand.hcp >= 11:
                return ("3NT", f"Accepting partner's 2NT invitation with {hand.hcp} HCP.")

        # Case 3: Opener showed two suits - jump preference (or bid game if combined values support)
        if opener_rebid_type == 'new_suit' and opener_second_suit:
            if should_bid_game and max_safe_level >= 4:
                # Bid game with fit in major
                fit1 = hand.suit_lengths.get(opener_first_suit, 0)
                fit2 = hand.suit_lengths.get(opener_second_suit, 0)
                if fit1 >= 3 and opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", f"Game with {opener_first_suit} fit (combined ~{combined_midpoint}).")
                if fit2 >= 3 and opener_second_suit in ['♥', '♠']:
                    return (f"4{opener_second_suit}", f"Game with {opener_second_suit} fit (combined ~{combined_midpoint}).")
                if hand.is_balanced:
                    return ("3NT", f"Game in NT (combined ~{combined_midpoint}).")
            return self._give_preference(hand, opener_first_suit, opener_second_suit, strength='invitational')

        # Case 4: Opener made jump rebid (already invitational) - accept with 10+ pts
        if opener_rebid_type == 'jump_rebid':
            # Accept invitation with 10+ pts (jump rebid shows extras from opener)
            if hand.total_points >= 10 and max_safe_level >= 4:
                # Accept invitation by bidding game
                if opener_first_suit in ['♥', '♠'] and hand.suit_lengths.get(opener_first_suit, 0) >= 2:
                    return (f"4{opener_first_suit}", f"Accepting game invitation with {hand.total_points} pts (combined ~{combined_midpoint}).")
                return ("3NT", f"Accepting game invitation with {hand.total_points} pts (combined ~{combined_midpoint}).")
            elif hand.total_points >= 10 and max_safe_level >= 3:
                return ("3NT", f"Accepting game invitation with {hand.total_points} pts (combined ~{combined_midpoint}).")
            else:
                # Decline with less than 10 pts or insufficient combined values
                return ("Pass", f"Declining partner's invitation with {hand.total_points} pts.")

        # Case 5: After reverse (forcing) - show invitational values or bid game
        # Reverse shows 17+ from opener, with 10-12 from responder = 27+ combined = GAME
        # Use bypass metadata since reverse is game-forcing with invitational values
        if context['is_forcing']:
            reverse_metadata = {'bypass_hcp': True, 'game_forcing': True, 'forcing_sequence': 'reverse'}

            # Reverse shows 17+ from opener, so combined is 27+ with invitational
            # This is definitely game territory - don't just invite
            if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                # After reverse + invitational, we HAVE game values (27+)
                if opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", f"Game with {opener_first_suit} support after partner's reverse (combined 27+).", reverse_metadata)
                return ("3NT", f"Game in NT with {opener_first_suit} support after reverse (combined 27+).", reverse_metadata)

            # Bid game with balanced hand after reverse (combined values high)
            if hand.is_balanced:
                return ("3NT", "Game in NT after partner's reverse (combined 27+).", reverse_metadata)

        # Default: Bid 2NT or 3NT based on combined values
        if hand.is_balanced:
            if should_bid_game and max_safe_level >= 3:
                return ("3NT", f"Game in NT (combined ~{combined_midpoint}).")
            return ("2NT", "Invitational with 10-12 HCP, balanced.")

        return None

    def _game_forcing_rebid(self, hand: Hand, context: Dict, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Handle game-forcing strength rebids (13+ points).

        Philosophy: Ensure game is reached, explore best strain.
        With 16+ points and fit, consider slam exploration.

        Priorities:
        1. With 16+ points and fit, explore slam (Blackwood will be triggered)
        2. Bid game directly if strain is clear
        3. Use Fourth Suit Forcing to gather more info
        4. Bid new suit (forcing) to show distribution
        5. Jump to 3NT with balanced hand
        """
        opener_rebid_type = context['opener_rebid_type']
        opener_first_suit = context['opener_first_suit']
        opener_second_suit = context['opener_second_suit']
        my_first_suit = context['my_first_suit']
        opener_rebid = context['opener_rebid']
        unbid_suit = context['unbid_suit']
        my_bids_after_opening = context.get('my_bids_after_opening', [])
        max_safe_level = self._get_max_safe_level(hand, features)

        # SLAM AGGREGATION LOGIC (per expert analysis):
        # If Combined_Points >= 33 AND Fit_Found = True THEN Force_Slam_Investigation
        estimated_combined = self._get_combined_estimate(hand, features)
        has_fit = False
        bidding_state = features.get('bidding_state')
        if bidding_state is not None:
            from utils.seats import normalize, partnership_str
            positions = features.get('positions', [])
            my_index = features.get('my_index')
            if positions and my_index is not None:
                my_seat = normalize(positions[my_index])
                has_fit = bidding_state.agreed_suits.get(partnership_str(my_seat)) is not None

        # Expert recommendation: Force slam investigation with 33+ combined and fit
        # With 32+ combined, make a slam try first (3-level)
        # Lowered threshold to 13+ when combined clearly shows slam (partner has extras)
        # The 33+ combined requirement ensures partner's strength compensates
        should_bid_blackwood = estimated_combined >= 33 and has_fit and hand.hcp >= 13
        should_explore_slam = estimated_combined >= 32 and hand.total_points >= 13

        # Case 1: Opener rebid same suit - raise to game with fit (or explore slam)
        if opener_rebid_type == 'same_suit':
            if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                # SLAM AGGREGATION: 33+ combined + fit = Force slam investigation (Blackwood)
                if should_bid_blackwood or (estimated_combined >= 33 and hand.hcp >= 13):
                    return ("4NT", f"Blackwood - slam investigation with {opener_first_suit} fit and {estimated_combined} estimated combined points.")
                # With slam potential but < 16 HCP, make a slam try at 3-level
                if should_explore_slam and opener_first_suit in ['♥', '♠']:
                    # Jump to 3-level shows slam interest with fit (cue-bid/slam try)
                    # This allows partner to ask Blackwood if interested
                    return (f"3{opener_first_suit}", f"Slam try with {opener_first_suit} fit and {hand.total_points} pts (estimated combined: {estimated_combined}).")
                if opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", f"Game with {opener_first_suit} fit (13+ pts).")
                else:
                    # Minor suit - prefer 3NT if balanced, unless slam potential
                    if should_explore_slam:
                        return (f"3{opener_first_suit}", f"Slam try in {opener_first_suit} with {hand.total_points} pts.")
                    if hand.is_balanced:
                        return ("3NT", f"Game in NT with {opener_first_suit} fit but balanced hand.")
                    # 5m needs ~29 combined (11 tricks); prefer 3NT if insufficient
                    if estimated_combined >= 29 and max_safe_level >= 5:
                        return (f"5{opener_first_suit}", f"Game in {opener_first_suit} (combined ~{estimated_combined}).")
                    return ("3NT", f"Game in NT preferred over 5{opener_first_suit} (combined ~{estimated_combined}).")

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
            # Ensure the "unbid" suit wasn't already bid by responder in a previous round
            my_rebid_suits = set()
            for prev_bid in my_bids_after_opening:
                if len(prev_bid) >= 2 and prev_bid[1] in '♣♦♥♠':
                    my_rebid_suits.add(prev_bid[1])
            if unbid_suit and unbid_suit not in my_rebid_suits and hand.hcp >= 12:
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
        # Reverse shows 17+ HCP from opener - with 13+ from responder, combined is 30+
        # MUST bid game - use bypass metadata
        if context['is_forcing']:
            reverse_metadata = {'bypass_hcp': True, 'game_forcing': True, 'forcing_sequence': 'reverse'}

            # Bid game with fit
            if hand.suit_lengths.get(opener_first_suit, 0) >= 3:
                if opener_first_suit in ['♥', '♠']:
                    return (f"4{opener_first_suit}", f"Game with {opener_first_suit} support after partner's reverse (combined 30+).", reverse_metadata)
                return ("3NT", f"Game with {opener_first_suit} support after partner's reverse.", reverse_metadata)

            # Bid 3NT with balanced
            if hand.is_balanced:
                return ("3NT", "Game in NT with 13+ HCP after partner's reverse (combined 30+).", reverse_metadata)

        # Default: Bid 3NT
        if hand.is_balanced and hand.hcp >= 13:
            return ("3NT", "Game in NT with 13+ HCP.")

        return None


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("responder_rebid", ResponderRebidModule())
