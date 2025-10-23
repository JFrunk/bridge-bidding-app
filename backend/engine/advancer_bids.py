from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict

class AdvancerBidsModule(ConventionModule):
    """
    Playbook for the partner of an overcaller (the Advancer).

    SAYC Guidelines for Advancer:
    - Simple raise: 8-10 points, 3+ card support
    - Jump raise: 11-12 points, 3+ card support (invitational) OR preemptive with 4+ support and weak hand
    - Cuebid: 12+ points, game-forcing, usually fit for partner's suit
    - New suit: 8+ points, 5+ card suit, non-forcing but constructive
    - NT bids: Stopper in opener's suit, balanced
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main entry point for advancer actions with bid validation."""
        auction_history = features['auction_history']

        # Get the raw advancer suggestion
        result = self._evaluate_advance(hand, features)

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

    def _evaluate_advance(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates advance bid without validation."""
        partner_overcall = features['auction_features']['partner_last_bid']
        opener_bid = features['auction_features']['opening_bid']

        # Validate that partner actually made an overcall (not Pass, not opening)
        if not partner_overcall or partner_overcall == 'Pass':
            return None  # Not an advancing situation

        # Partner doubled for takeout - handle separately (could add logic later)
        if partner_overcall in ['X', 'XX']:
            return None  # Responding to doubles needs different logic

        # Partner bid NT - different logic needed
        if 'NT' in partner_overcall:
            return self._advance_nt_overcall(hand, partner_overcall, opener_bid)

        # Partner overcalled a suit - now we can advance
        if len(partner_overcall) < 2:
            return None  # Invalid bid format

        # Check if this is our first advance or a subsequent competitive bid
        my_previous_bids = self._get_my_bids(features)

        if len(my_previous_bids) > 0:
            # This is a subsequent bid - handle competition
            return self._subsequent_advance(hand, partner_overcall, opener_bid, my_previous_bids[0], features)

        # First time advancing
        return self._advance_suit_overcall(hand, partner_overcall, opener_bid, features)

    def _advance_suit_overcall(self, hand: Hand, partner_overcall: str, opener_bid: str, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Advance partner's suit overcall.

        Priority:
        1. Game bid with 12+ points and fit (SIMPLIFIED - cuebid logic disabled)
        2. Jump raise with 11-12 points (invitational) or 4+ support weak (preemptive)
        3. Simple raise with 8-10 points and 3+ support
        4. New suit with 8+ points and 5+ card suit (constructive)
        5. NT with stopper and balanced
        6. Pass with weak hand
        """
        overcall_suit = partner_overcall[1]
        overcall_level = int(partner_overcall[0])
        support = hand.suit_lengths.get(overcall_suit, 0)

        # Calculate support points if we have fit
        support_points = self._calculate_support_points(hand, overcall_suit) if support >= 3 else hand.total_points

        # DISABLED: Cuebid logic (has critical bug - bids opponent's suit as trump)
        # TODO: Re-enable after implementing proper cuebid sequence tracking
        # The bug: Returns opponent's suit as bid, which engine treats as establishing new trump
        # Example bug: 1♦-1♠-Pass-3♦ (bidding opener's diamonds instead of supporting spades!)
        #
        # if hand.total_points >= 12:
        #     # Cuebid shows game-forcing values
        #     # Use cuebid when we have fit or very strong hand
        #     if support >= 3 or hand.total_points >= 14:
        #         cuebid_suit = opener_bid[1] if len(opener_bid) >= 2 else None
        #         if cuebid_suit and cuebid_suit in ['♣', '♦', '♥', '♠']:
        #             cuebid_level = overcall_level + 1  # One level above partner's bid
        #             return (f"{cuebid_level}{cuebid_suit}", f"Cuebid showing game-forcing values ({hand.total_points} pts) with fit for partner's {overcall_suit}.")
        #
        # To fix this properly, we need:
        # 1. A bidding state engine to track that cuebid was made
        # 2. Logic to continue bidding partner's ORIGINAL suit after cuebid
        # 3. Understanding that cuebid is forcing, not trump establishment

        # 1. Game bid with strong hand (12+ points and fit) - DIRECT APPROACH
        if hand.total_points >= 12 and support >= 3:
            # With major suit fit, bid game directly
            if overcall_suit in ['♥', '♠']:
                return (f"4{overcall_suit}", f"Game bid with {support_points} support points and {support}-card support.")
            # With minor suit fit and very strong hand (14+), bid game
            elif hand.total_points >= 14:
                if hand.is_balanced and self._has_stopper(hand, opener_bid):
                    return ("3NT", f"Game bid with {hand.hcp} HCP, balanced, with stopper.")
                else:
                    # Bid game in minor (5-level)
                    return (f"5{overcall_suit}", f"Game bid in minor with {support_points} support points and {support}-card support.")

        # 2. Jump raise (invitational with 11-12 OR preemptive with weak hand and 4+ support)
        if support >= 3:
            # Invitational jump raise: 11-12 support points, 3+ card support
            if 11 <= support_points <= 12:
                jump_level = overcall_level + 2
                if jump_level <= 5:  # Don't jump past game
                    if overcall_suit in ['♥', '♠'] and jump_level >= 4:
                        # Just bid game
                        return (f"4{overcall_suit}", f"Game bid with {support_points} support points and {support}-card support.")
                    else:
                        return (f"{jump_level}{overcall_suit}", f"Invitational jump raise with {support_points} support points and {support}-card support.")

            # Preemptive jump raise: 4+ card support, weak hand (5-8 points), long trumps
            # This is done to make it harder for opponents
            if support >= 4 and 5 <= hand.total_points <= 8:
                jump_level = overcall_level + 2
                if jump_level <= 4:  # Reasonable preemptive level
                    return (f"{jump_level}{overcall_suit}", f"Preemptive jump raise with {support}-card support (competitive bid).")

        # 3. Simple raise with 8-10 points and 3+ support
        if support >= 3 and 8 <= support_points <= 10:
            simple_raise_level = overcall_level + 1
            return (f"{simple_raise_level}{overcall_suit}", f"Simple raise showing {support_points} support points and {support}-card support.")

        # 4. New suit bid (8+ points, 5+ card suit, constructive but non-forcing)
        # Bid a good suit to show values and suggest alternative contract
        if hand.total_points >= 8:
            # Try to bid a new suit at cheapest level
            for suit in ['♠', '♥', '♦', '♣']:
                if suit == overcall_suit:
                    continue  # Skip partner's suit
                if hand.suit_lengths.get(suit, 0) >= 5:
                    # Find cheapest level to bid this suit
                    suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
                    if suit_rank.get(suit, 0) > suit_rank.get(overcall_suit, 0):
                        # Can bid at same level
                        new_suit_level = overcall_level
                    else:
                        # Need to bid at next level
                        new_suit_level = overcall_level + 1

                    # Don't bid new suit too high (keep it at 2-level or 3-level max)
                    if new_suit_level <= 3:
                        suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond', '♣': 'Club'}[suit]
                        return (f"{new_suit_level}{suit}", f"New suit showing {hand.total_points} points and 5+ {suit_name} suit (constructive).")

        # 5. NT bid with balanced hand and stopper
        if hand.is_balanced and self._has_stopper(hand, opener_bid):
            # 2NT: 11-12 HCP, invitational
            if 11 <= hand.hcp <= 12:
                return ("2NT", f"Invitational 2NT showing {hand.hcp} HCP, balanced, with stopper.")
            # 1NT: 8-10 HCP
            elif 8 <= hand.hcp <= 10 and overcall_level == 1:
                return ("1NT", f"1NT showing {hand.hcp} HCP, balanced, with stopper.")
            # 3NT: 13+ HCP, game bid
            elif hand.hcp >= 13:
                return ("3NT", f"3NT showing {hand.hcp} HCP, balanced, with stopper (game bid).")

        # 6. Pass with weak hand (< 8 points) or no clear action
        if hand.total_points < 8:
            return ("Pass", f"Weak hand ({hand.total_points} pts), passing partner's overcall.")

        # No clear action - pass
        return ("Pass", "No clear action to advance partner's overcall.")

    def _advance_nt_overcall(self, hand: Hand, partner_nt_bid: str, opener_bid: str) -> Optional[Tuple[str, str]]:
        """
        Advance partner's NT overcall (1NT or 2NT).

        After 1NT overcall (15-18 HCP):
        - 0-7 HCP: Pass
        - 8-9 HCP: 2NT invitational
        - 10+ HCP: 3NT or explore major fit
        """
        nt_level = int(partner_nt_bid[0])

        if nt_level == 1:
            # Partner showed 15-18 HCP
            if hand.hcp < 8:
                return ("Pass", "Weak hand, passing partner's 1NT overcall.")
            elif 8 <= hand.hcp <= 9:
                # Invitational - or transfer if have 5-card major
                if hand.suit_lengths.get('♥', 0) >= 5 or hand.suit_lengths.get('♠', 0) >= 5:
                    # Could use Stayman/Jacoby if available, but keep it simple
                    return ("2NT", f"Invitational with {hand.hcp} HCP.")
                return ("2NT", f"Invitational with {hand.hcp} HCP, asking partner to bid 3NT with maximum.")
            else:
                # Game values (10+ HCP)
                return ("3NT", f"Game bid with {hand.hcp} HCP opposite partner's 15-18 HCP.")

        elif nt_level == 2:
            # Partner showed 19-20 HCP (strong NT overcall)
            if hand.hcp < 5:
                return ("Pass", "Very weak hand, passing partner's 2NT overcall.")
            else:
                # With any values, bid game (partner has 19-20)
                return ("3NT", f"Game bid with {hand.hcp} HCP opposite partner's 19-20 HCP.")

        return None

    def _calculate_support_points(self, hand: Hand, trump_suit: str) -> int:
        """Calculate support points (HCP + shortness bonuses)."""
        points = hand.hcp
        for suit, length in hand.suit_lengths.items():
            if suit != trump_suit:
                if length == 1:
                    points += 2  # Singleton
                elif length == 0:
                    points += 3  # Void
        return points

    def _has_stopper(self, hand: Hand, opener_bid: str) -> bool:
        """Check if hand has stopper in opener's suit."""
        if len(opener_bid) < 2:
            return False

        suit = opener_bid[1]
        if suit not in ['♣', '♦', '♥', '♠']:
            return False

        suit_cards = [card for card in hand.cards if card.suit == suit]
        if not suit_cards:
            return False  # Void is not a stopper for NT

        ranks = [card.rank for card in suit_cards]
        length = len(ranks)

        # Stopper: A, Kx+, Qxx+, or Jxxx+
        if 'A' in ranks:
            return True
        if 'K' in ranks and length >= 2:
            return True
        if 'Q' in ranks and length >= 3:
            return True
        if 'J' in ranks and length >= 4:
            return True

        return False

    def _get_my_bids(self, features: Dict) -> list:
        """
        Get list of my non-Pass bids in this auction.

        Returns:
            List of bids I've made (excluding Pass, X, XX)
        """
        my_pos_str = features['positions'][features['my_index']]
        my_bids = [
            bid for i, bid in enumerate(features['auction_history'])
            if features['positions'][i % 4] == my_pos_str and bid not in ['Pass', 'X', 'XX']
        ]
        return my_bids

    def _subsequent_advance(self, hand: Hand, partner_overcall: str, opener_bid: str,
                           my_first_bid: str, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Handle subsequent bids after initial advance.

        After advancing once, we need to decide:
        1. Should we compete higher if opponents bid over us?
        2. Should we accept partner's invitation?
        3. Should we pass (already described our hand)?

        Args:
            hand: Current hand
            partner_overcall: Partner's original overcall
            opener_bid: Opener's bid
            my_first_bid: Our first advancing bid
            features: Auction features

        Returns:
            (bid, explanation) or None
        """
        overcall_suit = partner_overcall[1]
        support = hand.suit_lengths.get(overcall_suit, 0)
        support_points = self._calculate_support_points(hand, overcall_suit) if support >= 3 else hand.total_points

        # Get partner's last bid to see if they're inviting or competing
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        # If we already showed support, only compete with maximum values
        if my_first_bid.endswith(overcall_suit):
            # We already supported partner's suit

            # If partner invited (jumped), accept with maximum
            if partner_last_bid and len(partner_last_bid) >= 2:
                try:
                    partner_level = int(partner_last_bid[0])
                    my_first_level = int(my_first_bid[0])

                    # Partner jumped - they're inviting
                    if partner_level > my_first_level + 1:
                        # Accept invitation with maximum (10 pts for simple raise)
                        if support_points >= 10:
                            if overcall_suit in ['♥', '♠'] and partner_level == 3:
                                return (f"4{overcall_suit}", f"Accepting invitation with maximum ({support_points} pts).")
                            elif partner_level < 5:
                                return (f"{partner_level + 1}{overcall_suit}",
                                       f"Accepting invitation with maximum ({support_points} pts).")
                except (ValueError, IndexError):
                    pass

            # Check if opponents are competing
            last_opp_bid = self._get_last_opponent_bid(features)
            if last_opp_bid and last_opp_bid not in ['Pass', 'X', 'XX']:
                # Opponents are competing - only compete with extras
                if support >= 4 and support_points >= 10:
                    # We have maximum values and excellent fit
                    try:
                        my_first_level = int(my_first_bid[0])
                        compete_level = my_first_level + 1
                        if compete_level <= 4:  # Don't compete too high
                            return (f"{compete_level}{overcall_suit}",
                                   f"Competing with maximum support ({support_points} pts, {support}-card fit).")
                    except (ValueError, IndexError):
                        pass

            # Default: Pass (already described our hand)
            return ("Pass", "Already showed support, no extras to bid again.")

        # If we bid a different suit or NT initially, we may have different logic
        # For now, pass (we've described our hand)
        return ("Pass", "Already described hand, nothing more to say.")

    def _get_last_opponent_bid(self, features: Dict) -> Optional[str]:
        """
        Get the last non-Pass bid by opponents.

        Returns:
            Last opponent bid or None
        """
        auction_history = features['auction_history']
        positions = features['positions']
        my_pos_str = positions[features['my_index']]

        # Determine partner's position (opposite of me)
        partner_index = (features['my_index'] + 2) % 4
        partner_pos_str = positions[partner_index]

        # Find last opponent bid (not me, not partner, not Pass)
        for i in range(len(auction_history) - 1, -1, -1):
            bid = auction_history[i]
            pos = positions[i % 4]
            if pos not in [my_pos_str, partner_pos_str] and bid not in ['Pass', 'X', 'XX']:
                return bid

        return None
