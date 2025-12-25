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
            # This prevents runaway bid escalation (e.g., 2♣→7♣)
            try:
                original_level = int(bid[0])
                adjusted_level = int(next_legal[0])

                if adjusted_level - original_level > 2:
                    # The suggested bid is way off - pass instead of making unreasonable bid
                    return ("Pass", f"Cannot make reasonable bid at current auction level (suggested {bid}, would need {next_legal}).")
            except (ValueError, IndexError):
                # Not a level bid (e.g., Pass, X, XX) - allow adjustment
                pass

            adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
            return (next_legal, adjusted_explanation)

        # No legal bid possible - pass
        return None

    def _evaluate_rebid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates rebid without validation."""
        auction_history = features['auction_history']
        partner_response = features['auction_features']['partner_last_bid']
        my_opening_bid = features['auction_features']['opening_bid']

        if not partner_response or not my_opening_bid:
            return ("Pass", "Cannot determine auction context for rebid.")

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
                if hand.hcp >= 13:  # Maximum of 12-14 range
                    return ("3NT", f"Accepting invitation with maximum ({hand.hcp} HCP) after 1NT rebid.")
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
                if hand.hcp >= 13:
                    # Bid game with maximum
                    if partner_suit in ['♥', '♠']:
                        return (f"4{partner_suit}", f"Accepting 3-level invitation with maximum ({hand.hcp} HCP).")
                    else:
                        return ("3NT", f"Accepting 3-level invitation with maximum ({hand.hcp} HCP).")
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

        # Special handling for Negative Double (X) - FORCING, opener must rebid
        if partner_response == 'X':
            # Partner's negative double shows unbid major(s) and competitive values
            # Opener must bid, prioritizing support for partner's suit(s)

            # Prefer spades at 1-level if we have 3+ cards (economical)
            # Check spades first since it can be bid at 1-level
            if hand.suit_lengths.get('♠', 0) >= 3:
                if hand.total_points <= 15:
                    return ("1♠", "Supporting partner's negative double with 3+ spades.")
                elif hand.total_points <= 18:
                    return ("2♠", "Jump supporting partner's negative double with 16-18 pts and 3+ spades.")
                else:
                    return ("3♠", "Strong jump supporting partner's negative double with 19+ pts and 3+ spades.")

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
                    # Use AuctionContext to make smarter game decision
                    # Simple raise shows 6-10 pts, combined range is 19-25
                    # With maximum minimum (15) and good shape, consider game
                    auction_context = features.get('auction_context')
                    my_suit = my_opening_bid[1:]

                    # Calculate if game is reasonable based on combined strength
                    should_bid_game = False
                    should_invite = False

                    if auction_context is not None:
                        # Use expert-level range tracking
                        combined_mid = auction_context.ranges.combined_midpoint
                        combined_min = auction_context.ranges.combined_minimum

                        # Major suit game needs ~25 combined points
                        # With fit already established, be aggressive
                        if combined_mid >= 25:
                            should_bid_game = True
                        elif combined_mid >= 23 and hand.total_points >= 14:
                            # Close to game, invite with extras
                            should_invite = True
                    else:
                        # Fallback: Use traditional logic with more aggressive thresholds
                        # Partner shows 6-10, we have 13-15
                        # Combined: 19-25 (midpoint ~22)
                        if hand.total_points >= 15:
                            # Maximum minimum + simple raise = consider game with shape
                            has_long_suit = hand.suit_lengths.get(my_suit, 0) >= 6
                            has_good_suit = hand.suit_hcp.get(my_suit, 0) >= 6  # 2+ honors
                            if has_long_suit or has_good_suit:
                                should_invite = True

                    if should_bid_game and my_suit in ['♥', '♠']:
                        return (f"4{my_suit}", f"Bidding game with maximum minimum ({hand.total_points} pts) and good combined values.")
                    elif should_invite and my_suit in ['♥', '♠']:
                        return (f"3{my_suit}", f"Inviting game with {hand.total_points} pts and good shape (partner can pass or bid 4).")
                    else:
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

        elif 16 <= hand.total_points <= 18: # Medium Hand
            if partner_response.endswith(my_opening_bid[1]):
                return (f"3{my_opening_bid[1]}", "Invitational (16-18 pts), raising partner's simple raise.")
            if partner_response[0] == '1' and len(partner_response) == 2:
                partner_suit = partner_response[1]
                if hand.suit_lengths.get(partner_suit, 0) >= 4:
                    return (f"3{partner_suit}", f"Invitational (16-18 pts) jump raise showing 4+ card support.")

                # Check for 2NT rebid with 18-19 HCP balanced hand (SAYC standard)
                # This shows too strong for 1NT opening but balanced
                if hand.is_balanced and 18 <= hand.hcp <= 19:
                    return ("2NT", f"Balanced rebid showing 18-19 HCP (too strong for 1NT opening).")

                # Check for reverse bid with 17+ HCP and 4+ card second suit
                # Reverse shows a strong hand (17+ HCP) and is forcing
                if hand.hcp >= 17:
                    for suit in ['♠', '♥', '♦', '♣']:  # Check in rank order
                        if suit != my_opening_bid[1] and hand.suit_lengths.get(suit, 0) >= 4:
                            if self._is_reverse_bid(my_opening_bid, suit):
                                return (f"2{suit}", f"Reverse bid showing 17+ HCP and 4+ {suit} (forcing).")

            if hand.suit_lengths.get(my_opening_bid[1], 0) >= 6:
                return (f"3{my_opening_bid[1]}", f"Invitational (16-18 pts) jump rebid of a 6+ card suit.")

            # Fallback 2NT rebid for medium hands without fit
            if hand.is_balanced:
                return ("2NT", "Shows a balanced medium hand (16-17 HCP) with no obvious fit.")
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

                # Check for 3NT rebid with 19-20 HCP balanced hand (SAYC standard)
                # This shows a very strong balanced hand that's too strong for 2NT rebid
                if hand.is_balanced and 19 <= hand.hcp <= 20:
                    return ("3NT", f"Balanced rebid showing 19-20 HCP, bidding game in No-Trump.")

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

            # 3NT rebid only if balanced (otherwise prefer showing suits)
            if hand.is_balanced:
                return ("3NT", f"Strong balanced hand ({hand.hcp} HCP), bidding game in No-Trump.")

            # Unbalanced strong hand - prefer showing suit distribution
            return (f"3{my_opening_bid[1]}", f"Strong hand ({hand.total_points} pts) with unbalanced distribution.")

        return ("Pass", "No clear rebid available.")
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("openers_rebid", RebidModule())
