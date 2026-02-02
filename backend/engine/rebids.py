from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict

class RebidModule(ConventionModule):
    """
    Playbook for the opener's second bid (rebid).
    """

    # Suit ranking for reverse bid detection (higher number = higher ranking)
    SUIT_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}

    def _estimate_combined_with_partner(self, hand, features):
        """Use BiddingState for combined HCP, fall back to None."""
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
        return None

    def _is_jump_shift_response(self, opening_bid: str, response: str) -> bool:
        """
        Check if responder's bid is a jump shift (GAME FORCING).

        A jump shift is a new suit bid one level higher than necessary.
        Examples:
        - 1♣ - 2♥ (jump shift - hearts could have been bid at 1-level)
        - 1♣ - 2♠ (jump shift - spades could have been bid at 1-level)
        - 1♦ - 2♥ (jump shift - hearts could have been bid at 1-level)
        - 1♦ - 2♠ (jump shift - spades could have been bid at 1-level)
        - 1♥ - 2♠ (NOT a jump shift - spades at 1-level would be normal)
        - 1♥ - 3♣ (jump shift - clubs could have been bid at 2-level)
        - 1♥ - 3♦ (jump shift - diamonds could have been bid at 2-level)
        - 1♠ - 3♣ (jump shift - clubs could have been bid at 2-level)
        - 1♠ - 3♦ (jump shift - diamonds could have been bid at 2-level)
        - 1♠ - 3♥ (jump shift - hearts could have been bid at 2-level)

        Jump shifts show 16+ points and are GAME FORCING.
        """
        if not opening_bid or not response:
            return False

        # Must be 1-level opening
        if opening_bid[0] != '1' or len(opening_bid) < 2:
            return False

        # Response must be a suit bid at 2 or 3 level
        if not response[0].isdigit() or len(response) < 2:
            return False

        response_level = int(response[0])
        response_suit = response[1]
        opening_suit = opening_bid[1]

        # NT openings cannot have jump shifts — only suit openings
        if opening_suit not in '♣♦♥♠':
            return False

        # Response must be in a different suit (it's a shift)
        if response_suit == opening_suit:
            return False

        # Response must be at 2 or 3 level
        if response_level not in [2, 3]:
            return False

        opening_rank = self.SUIT_RANK.get(opening_suit, 0)
        response_rank = self.SUIT_RANK.get(response_suit, 0)

        # For 2-level response: it's a jump shift if the suit could have been bid at 1-level
        # A suit can be bid at 1-level if it ranks higher than the opening suit
        if response_level == 2:
            # If response suit ranks HIGHER than opening, it's a jump (could have been bid at 1-level)
            return response_rank > opening_rank

        # For 3-level response: it's a jump shift if the suit could have been bid at 2-level
        # A suit is bid at 2-level after 1-major when it ranks LOWER than opening suit
        if response_level == 3:
            # At 3-level, it's a jump if the suit could have been bid at 2-level
            # 2-level new suits are those ranking lower than opening OR...
            # Actually for 3-level: it's always a jump because cheapest new suit after 1M is at 2-level
            # So 3♣ after 1♥ is a jump (could bid 2♣), 3♦ after 1♥ is a jump (could bid 2♦)
            return response_rank < opening_rank

        return False

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
        """Main entry point for all opener rebid actions with bid validation."""
        auction_history = features['auction_history']

        # Get the raw rebid suggestion
        result = self._evaluate_rebid(hand, features)

        if not result:
            return ("Pass", "No rebid found.")

        # Handle both 2-tuple (bid, explanation) and 3-tuple (bid, explanation, metadata)
        if len(result) == 3:
            bid, explanation, metadata = result
        else:
            bid, explanation = result
            metadata = None

        # Always pass Pass bids through
        if bid == "Pass":
            return result

        # Validate the bid is legal
        if BidValidator.is_legal_bid(bid, auction_history):
            return result

        # Bid is illegal - try to find next legal bid of same strain
        next_legal = get_next_legal_bid(bid, auction_history, max_level_jump=1)
        if next_legal:
            # SANITY CHECK: If adjustment is more than 1 level, something is wrong
            # This prevents runaway bid escalation (e.g., 2♣→7♣)
            try:
                original_level = int(bid[0])
                adjusted_level = int(next_legal[0])

                if adjusted_level - original_level > 1:
                    # The suggested bid is way off - pass instead of making unreasonable bid
                    return ("Pass", f"Cannot make reasonable bid at current auction level (suggested {bid}, would need {next_legal}).")
            except (ValueError, IndexError):
                # Not a level bid (e.g., Pass, X, XX) - allow adjustment
                pass

            adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
            if metadata:
                return (next_legal, adjusted_explanation, metadata)
            return (next_legal, adjusted_explanation)

        # No legal bid possible - pass
        return None

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

    def _evaluate_rebid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates rebid without validation."""
        auction_history = features['auction_history']
        partner_response = features['auction_features']['partner_last_bid']
        my_opening_bid = features['auction_features']['opening_bid']

        if not partner_response or not my_opening_bid:
            return ("Pass", "Cannot determine auction context for rebid.")

        # SAFETY CHECK: If partnership has already reached game (3NT, 4M, 5m),
        # don't keep bidding unless we have slam values.
        # This prevents runaway auctions past game.
        if self._partnership_reached_game(auction_history, features):
            combined = self._estimate_combined_with_partner(hand, features)
            if combined is None:
                combined = hand.hcp + 14  # fallback estimate
            if combined < 33:
                return ("Pass", f"Game already reached, insufficient for slam ({hand.hcp} HCP, combined ~{combined}).")

        # Check if I previously bid 1NT and partner is now inviting
        # Extract my previous bids (excluding Pass, X, XX)
        my_position = features['positions'][features['my_index']]
        my_previous_bids = [bid for i, bid in enumerate(auction_history)
                            if features['positions'][i % 4] == my_position
                            and bid not in ['Pass', 'X', 'XX']]

        # If I already rebid 1NT, handle partner's follow-up bid
        if '1NT' in my_previous_bids and len(my_previous_bids) >= 2:
            # I already rebid 1NT (showing 12-14 HCP), now partner has bid again
            # Partner's new bid is likely invitational or forcing

            # If partner bid 2NT, they're inviting game with 11-12 HCP
            if partner_response == '2NT':
                # Use AuctionContext for smarter game decision
                auction_context = features.get('auction_context')
                should_accept = False

                if auction_context is not None:
                    combined_mid = auction_context.ranges.combined_midpoint
                    # 2NT invitation shows 11-12, opener rebid 1NT shows 12-14
                    # Combined should be ~24-25, need 25 for 3NT
                    if combined_mid >= 24:
                        should_accept = True
                    elif combined_mid >= 23 and hand.hcp >= 13:
                        should_accept = True
                else:
                    # Fallback: accept with maximum
                    if hand.hcp >= 13:
                        should_accept = True

                if should_accept:
                    return ("3NT", f"Accepting invitation with {hand.hcp} HCP after 1NT rebid.")
                else:
                    return ("Pass", f"Declining invitation with minimum ({hand.hcp} HCP).")

            # If partner bid a new suit at the 2-level, it's invitational
            # In SAYC after 1NT rebid, 2-level suit bids show 5+ card suit and invitational values
            if partner_response and partner_response[0] == '2' and len(partner_response) == 2:
                partner_suit = partner_response[1]

                # Accept invitation with maximum (13-14 HCP)
                if hand.hcp >= 13:
                    # After 1NT rebid, prefer 3NT over raising partner's suit
                    # Only raise if we have 4-card support (very strong fit)
                    if hand.suit_lengths.get(partner_suit, 0) >= 4 and partner_suit in ['♥', '♠']:
                        return (f"4{partner_suit}", f"Accepting invitation with {hand.hcp} HCP and 4-card major support.")
                    else:
                        return ("3NT", f"Accepting invitation with maximum ({hand.hcp} HCP).")
                else:
                    # Decline with minimum (12 HCP) - pass (accepting sign-off)
                    return ("Pass", f"Accepting sign-off with minimum ({hand.hcp} HCP).")

            # If partner bid 3NT, pass (partner took control)
            if partner_response == '3NT':
                return ("Pass", "Partner bid game.")

            # If partner raised to 3-level in my original suit or their suit, accept or decline
            if partner_response and partner_response[0] == '3' and len(partner_response) == 2:
                partner_suit = partner_response[1]

                # Partner is inviting game at 3-level
                # Use AuctionContext for smarter game decision
                auction_context = features.get('auction_context')
                should_accept = False

                if auction_context is not None:
                    combined_mid = auction_context.ranges.combined_midpoint
                    # 3-level invitation shows invitational values (10-12)
                    # With fit, be aggressive - need ~25 combined for major game
                    if combined_mid >= 24:
                        should_accept = True
                    elif combined_mid >= 23 and hand.hcp >= 13:
                        should_accept = True
                else:
                    # Fallback: accept with maximum
                    if hand.hcp >= 13:
                        should_accept = True

                if should_accept:
                    if partner_suit in ['♥', '♠']:
                        return (f"4{partner_suit}", f"Accepting 3-level invitation with {hand.hcp} HCP.")
                    else:
                        return ("3NT", f"Accepting 3-level invitation with {hand.hcp} HCP.")
                else:
                    return ("Pass", f"Declining 3-level invitation with minimum ({hand.hcp} HCP).")

        # Check if I previously bid 2NT and partner is now inviting
        # 2NT rebid shows 18-19 HCP (after 1-level opening)
        if '2NT' in my_previous_bids and len(my_previous_bids) >= 2:
            # I already rebid 2NT (showing 18-19 HCP), now partner has bid again
            # Partner's new bid is likely invitational or forcing

            # If partner bid 3NT, pass (partner accepted)
            if partner_response == '3NT':
                return ("Pass", "Partner bid game.")

            # If partner bid a suit at 3-level, they're showing preference or mild slam interest
            if partner_response and partner_response[0] == '3' and len(partner_response) == 2:
                partner_suit = partner_response[1]

                # With maximum 2NT rebid (19 HCP) and fit, accept invitation
                if hand.hcp >= 19:
                    # Bid game with maximum and 3+ card support
                    if hand.suit_lengths.get(partner_suit, 0) >= 3:
                        if partner_suit in ['♥', '♠']:
                            return (f"4{partner_suit}", f"Accepting invitation with maximum ({hand.hcp} HCP) and 3-card support.")
                        else:
                            # Minor suit - prefer 3NT over 5-level
                            return ("3NT", f"Accepting invitation with maximum ({hand.hcp} HCP), preferring 3NT.")
                    else:
                        return ("3NT", f"Accepting invitation with maximum ({hand.hcp} HCP).")
                else:
                    # With minimum 2NT rebid (18 HCP), pass (already showed strength)
                    return ("Pass", f"Partner's preference bid - staying in 3{partner_suit} with minimum ({hand.hcp} HCP).")

            # If partner bid 4NT (quantitative), they're inviting slam
            if partner_response == '4NT':
                if hand.hcp >= 19:
                    return ("6NT", f"Accepting slam invitation with maximum ({hand.hcp} HCP).")
                else:
                    return ("Pass", f"Declining slam invitation with minimum ({hand.hcp} HCP).")

            # If partner bid at 4-level (major suit game or cuebid)
            if partner_response and partner_response[0] == '4' and len(partner_response) == 2:
                partner_suit = partner_response[1]
                if partner_suit in ['♥', '♠']:
                    # Partner bid game in major, pass
                    return ("Pass", "Partner bid game in major.")
                else:
                    # 4♣/4♦ might be cuebid or natural - pass for now
                    return ("Pass", "Accepting partner's 4-level bid.")

        # Check if partner raised our suit at 3-level (invitational)
        # Example: 1♥ - 1♠ - 2♥ - 3♥ (partner invites with 3-card support)
        if len(my_previous_bids) >= 2 and partner_response and partner_response[0] == '3':
            # Check if partner raised our original suit
            my_first_bid = my_previous_bids[0]
            if len(my_first_bid) >= 2 and len(partner_response) >= 2:
                my_suit = my_first_bid[1]
                partner_suit = partner_response[1]

                # Partner raised our suit at 3-level
                if my_suit == partner_suit and my_suit in '♣♦♥♠':
                    # This is invitational (10-12 pts from responder)
                    # Accept with 15+ total points (good shape/extras)
                    if hand.total_points >= 15:
                        if my_suit in ['♥', '♠']:
                            return (f"4{my_suit}", f"Accepting 3-level invitation with extras ({hand.total_points} pts).")
                        else:
                            # Minor suit - consider 3NT
                            if hand.is_balanced and hand.hcp >= 15:
                                return ("3NT", f"Accepting invitation with {hand.hcp} HCP, preferring 3NT.")
                            else:
                                return (f"5{my_suit}", f"Accepting invitation in minor with {hand.total_points} pts.")
                    else:
                        # Decline with minimum (13-14 pts)
                        return ("Pass", f"Declining invitation with minimum ({hand.total_points} pts).")

        # Special handling: Partner jumped to 3NT (showing 13-15 HCP balanced)
        # This typically comes after a 1-level suit opening
        # Combined HCP is opener's hand + 13-15, so explore slam if combined >= 31
        if partner_response == '3NT':
            combined_min = hand.hcp + 13
            combined_max = hand.hcp + 15
            # With 18+ HCP, combined is 31-33+ - explore slam with Gerber
            if hand.hcp >= 18:
                gerber_metadata = {'bypass_suit_length': True, 'convention': 'gerber'}
                return ("4♣", f"Gerber convention asking for aces - combined HCP is {combined_min}-{combined_max}, exploring slam.", gerber_metadata)
            # With 15-17 HCP, combined is 28-32 - marginal for slam, pass and play 3NT
            else:
                return ("Pass", f"Accepting 3NT game - combined HCP is {combined_min}-{combined_max}.")

        # Special handling for Negative Double (X) - FORCING, opener must rebid
        if partner_response == 'X':
            # Partner's negative double shows unbid major(s) and competitive values
            # Opener must bid, prioritizing support for partner's suit(s)

            # Prefer spades at 1-level if we have 3+ cards (economical)
            # Check spades first since it can be bid at 1-level
            # After negative double, 3-card support is sufficient - bypass suit length validation
            if hand.suit_lengths.get('♠', 0) >= 3:
                if hand.total_points <= 15:
                    return ("1♠", "Supporting partner's negative double with 3+ spades.", {'bypass_suit_length': True})
                elif hand.total_points <= 18:
                    return ("2♠", "Jump supporting partner's negative double with 16-18 pts and 3+ spades.", {'bypass_suit_length': True})
                else:
                    return ("3♠", "Strong jump supporting partner's negative double with 19+ pts and 3+ spades.", {'bypass_suit_length': True})

            # Then check hearts (requires 2-level bid)
            if hand.suit_lengths.get('♥', 0) >= 4:
                if hand.total_points <= 15:
                    return ("2♥", "Supporting partner's negative double with 4+ hearts.")
                elif hand.total_points <= 18:
                    return ("3♥", "Jump supporting partner's negative double with 16-18 pts and 4+ hearts.")
                else:
                    return ("4♥", "Strong jump supporting partner's negative double with 19+ pts and 4+ hearts.")

            # No major fit - rebid our suit or bid notrump
            my_suit = my_opening_bid[1:]
            if hand.suit_lengths.get(my_suit, 0) >= 6:
                return (f"2{my_suit}", f"Rebidding 6+ card {my_suit} suit after partner's negative double.")

            if hand.is_balanced and hand.hcp >= 15:
                return ("1NT", "Balanced hand with 15+ HCP after partner's negative double.")

            # Default: rebid our suit at minimum level
            return (f"2{my_suit}", f"Minimum rebid of {my_suit} after partner's negative double.")

        # Logic for rebids after a 2 Club opening
        # 2♣ is GAME FORCING - opener must continue the auction!
        if my_opening_bid == '2♣':
            # Metadata to bypass HCP validation - 2♣ is game forcing
            strong_2c_metadata = {'bypass_hcp': True, 'forcing_sequence': '2c_game_forcing'}

            if partner_response == '2♦':
                # 2♦ is the negative/waiting response
                if 22 <= hand.hcp <= 24 and hand.is_balanced:
                    return ("2NT", "Shows a balanced hand with 22-24 HCP.", strong_2c_metadata)
                if 25 <= hand.hcp <= 27 and hand.is_balanced:
                    return ("3NT", "Shows a balanced hand with 25-27 HCP.", strong_2c_metadata)
                best_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
                if hand.suit_lengths[best_suit] >= 5:
                    bid_level = '3' if best_suit in ['♣', '♦'] else '2'
                    return (f"{bid_level}{best_suit}", f"Shows a strong hand with a long {best_suit} suit.", strong_2c_metadata)
                # No clear rebid - bid 2NT to show balanced
                return ("2NT", "Balanced hand after 2♣ opening.", strong_2c_metadata)

            if partner_response == '2NT':
                # Partner showed positive values, balanced
                best_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
                if hand.suit_lengths[best_suit] >= 5:
                    return (f"3{best_suit}", f"Showing my long {best_suit} suit.", strong_2c_metadata)
                # Balanced with no 5-card suit - bid 3NT or explore slam
                if hand.hcp >= 25:
                    return ("4NT", "Quantitative slam invite after partner's positive 2NT.", strong_2c_metadata)
                return ("3NT", "Game in NT after partner's positive response.", strong_2c_metadata)

            # POSITIVE RESPONSES: 2♥, 2♠, 3♣, 3♦ show 8+ HCP with 5+ card suit
            # Opener must continue to game
            if partner_response in ['2♥', '2♠']:
                partner_suit = partner_response[1]
                support = hand.suit_lengths.get(partner_suit, 0)

                # With 3+ card support, raise to game
                if support >= 3:
                    return (f"4{partner_suit}", f"Game in {partner_suit} with support for partner's positive response.", strong_2c_metadata)

                # With 2-card support, raise to 3-level
                if support == 2:
                    return (f"3{partner_suit}", f"Preference to partner's suit with doubleton.", strong_2c_metadata)

                # No support - show our own suit or bid NT
                best_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
                if hand.suit_lengths[best_suit] >= 5:
                    if best_suit in ['♠'] and partner_response == '2♥':
                        return ("2♠", f"Showing our own {best_suit} suit.", strong_2c_metadata)
                    else:
                        return (f"3{best_suit}", f"Showing our own {best_suit} suit.", strong_2c_metadata)

                # No fit, no suit - bid 2NT/3NT
                if partner_response == '2♥':
                    return ("2NT", "No heart support, suggesting NT game.", strong_2c_metadata)
                return ("3NT", "No spade support, game in NT.", strong_2c_metadata)

            # Positive response in a minor (3♣ or 3♦)
            if partner_response in ['3♣', '3♦']:
                partner_minor = partner_response[1]
                support = hand.suit_lengths.get(partner_minor, 0)

                # Probably best to bid 3NT unless we have good fit
                if support >= 4:
                    return (f"4{partner_minor}", f"Supporting partner's minor.", strong_2c_metadata)
                # Check for major suit
                for major in ['♠', '♥']:
                    if hand.suit_lengths.get(major, 0) >= 5:
                        return (f"3{major}", f"Showing major suit, partner chooses 3NT or suit game.", strong_2c_metadata)
                return ("3NT", "Game in NT after partner's minor suit positive.", strong_2c_metadata)

        # CRITICAL: Handle JUMP SHIFT by responder (GAME FORCING)
        # A jump shift (e.g., 1♠ - 3♥, 1♦ - 2♠, 1♣ - 2♥) shows 16+ points and is GAME FORCING
        # Opener MUST continue bidding to game - never pass!
        if self._is_jump_shift_response(my_opening_bid, partner_response):
            # Game forcing metadata - bypass HCP validation
            jump_shift_metadata = {'bypass_hcp': True, 'game_forcing': True, 'forcing_sequence': 'jump_shift'}

            # Partner has 16+ HCP, combined is at least 29+ (game forcing to slam consideration)
            partner_suit = partner_response[1] if len(partner_response) >= 2 and partner_response[1] in '♠♥♦♣' else None
            my_suit = my_opening_bid[1] if len(my_opening_bid) >= 2 and my_opening_bid[1] in '♠♥♦♣' else None

            if partner_suit:
                # With 3+ card support for partner's suit, raise to game
                support = hand.suit_lengths.get(partner_suit, 0)
                if support >= 3:
                    if partner_suit in ['♥', '♠']:
                        return (f"4{partner_suit}", f"Game in {partner_suit} with support after partner's jump shift (game forcing).", jump_shift_metadata)
                    else:
                        return ("3NT", f"Game in NT with minor suit support after jump shift.", jump_shift_metadata)

            # With 6+ card suit, rebid it
            if my_suit and hand.suit_lengths.get(my_suit, 0) >= 6:
                level = '3' if int(partner_response[0]) <= 2 else '4'
                return (f"{level}{my_suit}", f"Rebidding 6+ card suit in game forcing sequence.", jump_shift_metadata)

            # With balanced hand, bid 3NT
            if hand.is_balanced:
                return ("3NT", f"Game in NT after partner's jump shift.", jump_shift_metadata)

            # With good second suit, show it
            for suit in ['♠', '♥', '♦', '♣']:
                if suit != my_suit and suit != partner_suit and hand.suit_lengths.get(suit, 0) >= 4:
                    level = '3' if suit in ['♣', '♦'] or int(partner_response[0]) >= 3 else '2'
                    return (f"{level}{suit}", f"Showing second suit in game forcing sequence.", jump_shift_metadata)

            # Default: bid 3NT
            return ("3NT", f"Game in NT after partner's jump shift (game forcing).", jump_shift_metadata)

        # Logic for rebids after a 1-level opening
        # Adjusted thresholds to account for total_points including distribution
        if 13 <= hand.total_points <= 16: # Minimum Hand
            # Check if partner raised our suit
            if partner_response.endswith(my_opening_bid[1:]):
                # Distinguish between simple raise (2-level) and invitational raise (3-level)
                partner_level = int(partner_response[0])
                my_opening_level = int(my_opening_bid[0])

                if partner_level == my_opening_level + 1:  # Simple raise (e.g., 1♠-2♠)
                    # Simple raise shows 6-10 pts - use partner's MIDPOINT (8 pts)
                    # With minimum opening (13-15 pts), combined is only 21-23
                    # Game needs 25 pts - DO NOT bid game with minimum opener after simple raise
                    #
                    # CRITICAL FIX: Use ACTUAL hand points, not AuctionContext midpoint
                    # AuctionContext uses opener range (13-21) midpoint (17), which inflates estimate
                    my_suit = my_opening_bid[1:]

                    # Calculate realistic combined points
                    # Use BiddingState when available, fall back to hardcoded midpoint
                    combined_bs = self._estimate_combined_with_partner(hand, features)
                    if combined_bs is not None:
                        realistic_combined = combined_bs
                    else:
                        # Partner's simple raise shows 6-10 support points (midpoint 8)
                        partner_midpoint = 8  # (6+10)/2 = 8 support points
                        realistic_combined = hand.total_points + partner_midpoint

                    should_bid_game = False
                    should_invite = False

                    # Game in major needs ~25 combined points with fit
                    # With 13-15 opener + 8 (partner midpoint) = 21-23 combined
                    # This is NOT enough for game - only invite with maximum (15 pts)
                    if realistic_combined >= 25:
                        # This requires opener to have 17+ pts, which is medium/strong hand
                        # But we're in 13-15 range, so this shouldn't trigger
                        should_bid_game = True
                    elif realistic_combined >= 23 and hand.total_points >= 15:
                        # Maximum minimum (15 pts) + partner's 8 = 23 combined
                        # Close to game, invite with good shape
                        has_long_suit = hand.suit_lengths.get(my_suit, 0) >= 6
                        has_good_suit = hand.suit_hcp.get(my_suit, 0) >= 6  # 2+ honors
                        if has_long_suit or has_good_suit:
                            should_invite = True

                    if should_bid_game and my_suit in ['♥', '♠']:
                        return (f"4{my_suit}", f"Bidding game with {hand.total_points} pts + partner's ~8 = {realistic_combined} combined.")
                    elif should_invite and my_suit in ['♥', '♠']:
                        return (f"3{my_suit}", f"Inviting game with {hand.total_points} pts and good shape (partner can pass or bid 4).")
                    else:
                        return ("Pass", f"Minimum hand ({hand.total_points} pts), passing partner's simple raise (combined ~{realistic_combined}).")

                elif partner_level == my_opening_level + 2:  # Invitational raise (e.g., 1♠-3♠)
                    # Partner is inviting game (10-12 support points).
                    # SAYC: With minimum opening (13 HCP), PASS. Accept with 14+ HCP or good extras.
                    #
                    # CRITICAL FIX: Use ACTUAL hand HCP, not AuctionContext midpoint
                    # Also be conservative - use HCP (not total points) for threshold calculation
                    my_suit = my_opening_bid[1:]

                    # Calculate realistic combined using BiddingState or fallback
                    combined_bs = self._estimate_combined_with_partner(hand, features)
                    if combined_bs is not None:
                        realistic_combined_hcp = combined_bs
                    else:
                        # Partner's invitational raise shows 10-12 support points (midpoint 11)
                        # But support points include distribution, so use midpoint 10 HCP for conservative estimate
                        partner_hcp_midpoint = 10  # Conservative HCP estimate (they have 10-12 support pts)
                        realistic_combined_hcp = hand.hcp + partner_hcp_midpoint

                    should_bid_game = False

                    # Game in major needs ~25 combined HCP with fit
                    # With 13 HCP opener + 10 (partner midpoint) = 23 combined - decline
                    # With 14 HCP opener + 10 = 24 combined - borderline, accept with good shape
                    # With 15 HCP opener + 10 = 25 combined - accept
                    if realistic_combined_hcp >= 25:
                        # 15+ HCP + 10 = 25+ combined - clearly accept
                        should_bid_game = True
                    elif realistic_combined_hcp >= 24:
                        # 14 HCP + 10 = 24 combined - borderline, accept with good shape
                        has_long_suit = hand.suit_lengths.get(my_suit, 0) >= 6
                        has_quality_suit = hand.suit_hcp.get(my_suit, 0) >= 6  # 2+ honors
                        if has_long_suit or has_quality_suit:
                            should_bid_game = True
                    elif hand.hcp == 13:
                        # Pure minimum - only accept with EXCEPTIONAL shape
                        has_long_suit = hand.suit_lengths.get(my_suit, 0) >= 6
                        has_quality_suit = hand.suit_hcp.get(my_suit, 0) >= 8  # Strong honors (AKQ or similar)
                        if has_long_suit and has_quality_suit:
                            should_bid_game = True

                    if should_bid_game:
                        if my_suit in ['♥', '♠']:
                            return (f"4{my_suit}", f"Accepting invitation with {hand.hcp} HCP + partner's ~10 = {realistic_combined_hcp} combined.")
                        else:
                            return ("3NT", f"Accepting invitation with {hand.hcp} HCP + partner's ~10 = {realistic_combined_hcp} combined.")
                    else:
                        return ("Pass", f"Declining invitation with {hand.hcp} HCP (combined ~{realistic_combined_hcp}, need 24+ with shape or 25+).")
            if partner_response == "1NT":
                # CRITICAL FIX: 1NT is a SEMI-FORCING response showing 6-10 HCP
                # With minimum opening (12-14 HCP), opener should PASS unless:
                # 1. Hand has 15+ HCP (extras), OR
                # 2. Hand has a strong 6+ card suit worth rebidding
                #
                # SAYC Standard: After 1M - 1NT, opener passes with 12-14 balanced or semi-balanced
                # Only bid with extras or a very strong suit

                # Check if we have a 6+ card suit worth rebidding
                my_suit = my_opening_bid[1:]
                if hand.suit_lengths.get(my_suit, 0) >= 6:
                    # With 6+ card suit, rebid it to show extras or escape 1NT
                    return (f"2{my_suit}", f"Minimum hand (13-15 pts) rebidding a 6+ card suit.")

                # With only 5-card suit and minimum (12-14 HCP), we should PASS
                # 1NT is likely the best contract
                # DO NOT bid a second suit with minimum - this overstates our strength
                return ("Pass", f"Minimum hand ({hand.total_points} pts), accepting 1NT as final contract.")

            # Handle 2-level new suit response (e.g., 1♥-2♣, 1♦-2♣)
            # Partner's 2-level new suit response shows 10+ HCP and is forcing
            # Opener must rebid - cannot pass!
            if partner_response[0] == '2' and len(partner_response) == 2:
                partner_suit = partner_response[1]
                my_suit = my_opening_bid[1:]

                # Priority 1: Raise partner's suit with 4+ card support
                if hand.suit_lengths.get(partner_suit, 0) >= 4:
                    return (f"3{partner_suit}", f"Raising partner's {partner_suit} with 4+ card support (13-15 pts).")

                # Priority 2: Rebid 6+ card suit
                if hand.suit_lengths.get(my_suit, 0) >= 6:
                    return (f"2{my_suit}", f"Rebidding 6+ card {my_suit} suit (13-15 pts).")

                # Priority 3: Bid 2NT with balanced hand (13-14 HCP)
                if hand.is_balanced:
                    return ("2NT", f"Balanced rebid showing 13-14 HCP after partner's 2-level response.")

                # Priority 4: Show a new 4+ card suit (if lower ranking, not a reverse)
                for suit in ['♣', '♦', '♥', '♠']:
                    if suit != my_suit and suit != partner_suit and hand.suit_lengths.get(suit, 0) >= 4:
                        if not self._is_reverse_bid(my_opening_bid, suit):
                            return (f"2{suit}", f"Showing second 4+ card {suit} suit (13-15 pts).")

                # Priority 5: Rebid 5-card suit as last resort
                return (f"2{my_suit}", f"Rebidding 5-card {my_suit} suit (13-15 pts).")
            if partner_response[0] == '1' and len(partner_response) == 2:
                partner_suit = partner_response[1]
                if hand.suit_lengths.get(partner_suit, 0) >= 4:
                    return (f"2{partner_suit}", f"Minimum hand (13-15 pts) showing 4+ card support.")

                # Check for a second 4+ card suit to bid (non-reverse)
                # Bid lower-ranking suits first to avoid reverses with minimum hands
                my_suit = my_opening_bid[1]
                for suit in ['♣', '♦', '♥', '♠']:
                    if suit != my_suit and suit != partner_suit and hand.suit_lengths.get(suit, 0) >= 4:
                        # Avoid reverse bids (higher-ranking suit at 2-level) with minimum
                        if not self._is_reverse_bid(my_opening_bid, suit):
                            return (f"2{suit}", f"Minimum hand (13-15 pts) showing a second 4+ card {suit} suit.")

                if hand.is_balanced:
                    return ("1NT", "Minimum hand (12-14 HCP), balanced, no fit for partner's suit.")

                # No second suit available without reversing - rebid original suit
                if hand.suit_lengths.get(my_suit, 0) >= 6:
                    return (f"2{my_suit}", f"Minimum hand (13-15 pts) rebidding a 6+ card {my_suit} suit.")

                # With only a 5-card suit and no second suit, rebid it anyway
                return (f"2{my_suit}", f"Minimum hand (13-15 pts) rebidding a 5-card {my_suit} suit.")

        elif 17 <= hand.total_points <= 19: # Medium Hand
            if partner_response.endswith(my_opening_bid[1]):
                # Upgrade to Game if HCP is strong (18+)
                if hand.hcp >= 18:
                    return (f"4{my_opening_bid[1]}", f"Bidding game with strong hand ({hand.hcp} HCP) after partner's raise.")
                return (f"3{my_opening_bid[1]}", "Invitational (16-18 pts), raising partner's simple raise.")
            if partner_response[0] == '1' and len(partner_response) == 2:
                partner_suit = partner_response[1]
                if hand.suit_lengths.get(partner_suit, 0) >= 4:
                    return (f"3{partner_suit}", f"Invitational (16-18 pts) jump raise showing 4+ card support.")

                # Check for reverse bid with 17+ HCP and 4+ card second suit
                # Reverse shows a strong hand (17+ HCP) and is forcing
                # This takes priority over 2NT rebid when we have a good second suit
                # Note: Reverse bids show 4+ cards in second suit (first suit is 5+)
                # Bypass suit length validation since 4-card suits are standard for reverses
                if hand.hcp >= 17:
                    reverse_metadata = {'bypass_suit_length': True, 'convention': 'reverse_bid'}
                    for suit in ['♠', '♥', '♦', '♣']:  # Check in rank order
                        if suit != my_opening_bid[1] and hand.suit_lengths.get(suit, 0) >= 4:
                            if self._is_reverse_bid(my_opening_bid, suit):
                                return (f"2{suit}", f"Reverse bid showing 17+ HCP and 4+ {suit} (forcing).", reverse_metadata)

                # Check for 2NT rebid with 18-19 HCP balanced hand (SAYC standard)
                # This shows too strong for 1NT opening but balanced
                # NOTE: Only use 2NT if we don't have a good second suit to show via reverse
                if hand.is_balanced and 18 <= hand.hcp <= 19:
                    return ("2NT", f"Balanced rebid showing 18-19 HCP (too strong for 1NT opening).")

            # After 1NT response from partner (semi-forcing)
            # With medium hand (16-18 pts), we should NOT pass
            # Show distribution or jump rebid
            if partner_response == "1NT":
                my_suit = my_opening_bid[1:]
                # With 6+ card suit and medium hand, jump rebid to show extras
                if hand.suit_lengths.get(my_suit, 0) >= 6:
                    return (f"3{my_suit}", f"Medium hand (16-18 pts) jump rebidding 6+ card {my_suit} suit.")

                # With 5-4 shape, show second 4-card suit (doesn't require 17+ for non-reverse)
                reverse_metadata = {'bypass_suit_length': True, 'convention': 'reverse_bid'}
                for suit in ['♥', '♦', '♣']:  # Check lower suits first
                    if suit != my_suit and hand.suit_lengths.get(suit, 0) >= 4:
                        if not self._is_reverse_bid(my_opening_bid, suit):
                            return (f"2{suit}", f"Medium hand (16-18 pts) showing second 4+ card {suit} suit.")
                        elif hand.hcp >= 17:  # Reverse requires 17+ HCP
                            return (f"2{suit}", f"Reverse bid showing 17+ HCP and 4+ {suit} (forcing).", reverse_metadata)

                # Check for reverse bid with 17+ HCP and 4+ card second suit
                # Reverse shows a strong hand (17+ HCP) and is forcing
                if hand.hcp >= 17:
                    for suit in ['♠', '♥', '♦', '♣']:  # Check in rank order
                        if suit != my_opening_bid[1] and hand.suit_lengths.get(suit, 0) >= 4:
                            if self._is_reverse_bid(my_opening_bid, suit):
                                return (f"2{suit}", f"Reverse bid showing 17+ HCP and 4+ {suit} (forcing).", reverse_metadata)

            if hand.suit_lengths.get(my_opening_bid[1], 0) >= 6:
                return (f"3{my_opening_bid[1]}", f"Invitational (16-18 pts) jump rebid of a 6+ card suit.")

            # Fallback 2NT rebid for medium hands without fit
            if hand.is_balanced:
                return ("2NT", "Shows a balanced medium hand (16-17 HCP) with no obvious fit.")
            return ("2NT", "Shows a strong hand (16-18 pts) with no obvious fit.")

        elif hand.total_points >= 20: # Strong Hand
            # Check for slam potential using AuctionContext
            # Expert recommendation: Combined_Points >= 33 AND Fit_Found = slam investigation
            auction_context = features.get('auction_context')
            estimated_combined = 0
            has_fit = False

            if auction_context is not None:
                estimated_combined = auction_context.ranges.combined_midpoint
                has_fit = auction_context.has_fit
            else:
                # Fallback: partner's response shows 6-10 (new suit/raise), 10-12 (jump)
                partner_level = int(partner_response[0]) if partner_response[0].isdigit() else 1
                partner_estimated = 11 if partner_level >= 3 else 8
                estimated_combined = hand.total_points + partner_estimated

            # SLAM AGGREGATION LOGIC (per expert analysis):
            # If Combined_Points >= 33 AND Fit_Found = True THEN Force_Slam_Investigation
            # With 33+ combined and established fit, ask Blackwood directly
            # IMPORTANT: Only consider slam exploration with 21+ HCP opener AND 32+ combined
            # With 19-20 HCP after 1-level response (6-10), combined is only 25-30 - just bid game
            should_bid_blackwood = estimated_combined >= 33 and has_fit and hand.hcp >= 21
            should_explore_slam = estimated_combined >= 32 and hand.hcp >= 21

            if partner_response.endswith(my_opening_bid[1]):
                partner_suit = my_opening_bid[1]
                if partner_suit in ['♥', '♠']:
                    # Partner raised our suit - fit is established
                    if should_bid_blackwood or (estimated_combined >= 33 and hand.hcp >= 20):
                        # Force slam investigation with Blackwood
                        return ("4NT", f"Blackwood - slam investigation with fit and {estimated_combined} estimated combined points.")
                    elif should_explore_slam:
                        return (f"3{partner_suit}", f"Slam try with {hand.total_points} pts after partner's raise (estimated combined: {estimated_combined}).")
                    return (f"4{partner_suit}", f"Strong hand ({hand.total_points} pts), bidding game after partner's raise.")
            if len(partner_response) == 2:
                partner_suit = partner_response[1]
                if partner_suit in ['♥', '♠'] and hand.suit_lengths.get(partner_suit, 0) >= 4:
                    # We have 4-card support for partner's major - fit is established
                    # With 19 HCP and 4-card support, bid game (4♠/4♥) - not Blackwood
                    # Blackwood only with 20+ HCP and 33+ combined
                    if should_bid_blackwood or (estimated_combined >= 33 and hand.hcp >= 20):
                        # Force slam investigation with Blackwood
                        return ("4NT", f"Blackwood - slam investigation with {partner_suit} fit and {estimated_combined} estimated combined points.")
                    elif should_explore_slam:
                        return (f"3{partner_suit}", f"Slam try with {partner_suit} fit and {hand.total_points} pts.")
                    # Standard case: bid game with 19 HCP and 4-card support
                    return (f"4{partner_suit}", f"Strong hand ({hand.total_points} pts), bidding game with 4+ {partner_suit}.")

                # Check for 2NT rebid with 19 HCP balanced hand (SAYC standard)
                # 19 HCP is on the boundary - SAYC says 18-19 rebids 2NT
                if hand.is_balanced and hand.hcp == 19:
                    return ("2NT", f"Balanced rebid showing 18-19 HCP (too strong for 1NT opening).")
                # 20+ HCP balanced bids 3NT
                if hand.is_balanced and hand.hcp >= 20:
                    return ("3NT", f"Balanced rebid showing 20+ HCP, bidding game in No-Trump.")

                # Check for reverse bid with 4+ card second suit
                # With 19+ HCP, reverse shows slam interest
                # Bypass suit length validation - reverse shows 4+ in second suit
                reverse_metadata = {'bypass_suit_length': True, 'convention': 'reverse_bid'}
                for suit in ['♠', '♥', '♦', '♣']:  # Check in rank order
                    if suit != my_opening_bid[1] and hand.suit_lengths.get(suit, 0) >= 4:
                        if self._is_reverse_bid(my_opening_bid, suit):
                            return (f"2{suit}", f"Reverse bid showing 19+ HCP and 4+ {suit} (forcing, slam interest).", reverse_metadata)

            # Check if partner's bid is at the 3-level (showing preference, not a raise)
            # This happens after opener's jump rebid when partner returns to their suit
            # With game values (19+ pts) and combined ~25-27 HCP, bid 3NT for game
            if partner_response and len(partner_response) == 2 and partner_response[0] == '3':
                partner_suit = partner_response[1]
                # Partner is showing preference at 3-level (e.g., 3♠ after 1♦-1♠-3♦)
                # This shows 6-9 HCP typically, combined is ~25-28 - game values
                if partner_suit in ['♥', '♠'] and hand.suit_lengths.get(partner_suit, 0) >= 4:
                    # 4-card support for partner's major (8+ total trumps) - bid 4 of the major
                    return (f"4{partner_suit}", f"Game in partner's major with 4+ support and {hand.total_points} pts.")
                else:
                    # Only 3-card support (7 total trumps) or minor - prefer 3NT
                    return ("3NT", f"Game in NT with {hand.hcp} HCP after partner's preference.")

            # Before jumping to 3NT, check if we have a 6-card suit to show
            my_suit = my_opening_bid[1]
            if hand.suit_lengths.get(my_suit, 0) >= 6:
                # Rebid the 6-card suit at the 3-level to show extras and length
                return (f"3{my_suit}", f"Strong hand ({hand.total_points} pts) with a 6+ card {my_suit} suit.")

            # 3NT rebid only if balanced (otherwise prefer showing suits)
            if hand.is_balanced:
                return ("3NT", f"Strong balanced hand ({hand.hcp} HCP), bidding game in No-Trump.")

            # Unbalanced strong hand - prefer showing suit distribution
            return (f"3{my_opening_bid[1]}", f"Strong hand ({hand.total_points} pts) with unbalanced distribution.")

        return ("Pass", "No clear rebid available.")
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("openers_rebid", RebidModule())
