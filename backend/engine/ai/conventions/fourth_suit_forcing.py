from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict, Set

class FourthSuitForcingConvention(ConventionModule):
    """
    Fourth Suit Forcing (FSF) Convention - Artificial game force

    SAYC Standard:
    - After three suits have been bid naturally, bidding the fourth suit is artificial
    - Game-forcing (or forcing to 3NT)
    - Shows:
      * Game values (12+ HCP typically)
      * No clear direction (no fit found yet, no stopper for NT)
      * Asks opener to further describe their hand
    - Example: 1f - 1e - 1` - 2c (2c is FSF, not showing clubs)

    Responder uses FSF when:
    - Has game-forcing values
    - No fit found in any suit bid so far
    - Uncertain about final contract
    - Wants opener to show:
      * 3-card support for responder's first suit
      * Stopper in 4th suit for NT
      * Extra length in a bid suit
      * Minimum vs. extra values
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Evaluate if Fourth Suit Forcing applies.

        Args:
            hand: The hand to evaluate
            features: Auction features

        Returns:
            (bid, explanation) or None
        """
        auction = features['auction_features']

        # FSF is a responder tool - partner must have opened
        if auction.get('opener_relationship') != 'Partner':
            return None

        # Check if this is a position where responder would use FSF
        result = self._check_fsf_applicable(hand, auction, features)

        if result:
            return result

        # Check if we're opener responding to FSF
        opener_response = self._check_fsf_response(hand, auction, features)
        if opener_response:
            return opener_response

        return None

    def _check_fsf_applicable(self, hand: Hand, auction: Dict,
                              features: Dict) -> Optional[Tuple[str, str]]:
        """
        Check if responder should use Fourth Suit Forcing.

        Requires:
        1. Three suits already bid
        2. Responder has game-forcing values (12+ HCP)
        3. No clear fit found
        4. Fourth suit not yet bid
        """

        # Get auction history
        auction_history = features.get('auction_history', [])
        positions = features.get('positions', [])
        my_index = features.get('my_index', 0)
        my_pos_str = positions[my_index]

        # Get partner's position
        partner_index = (my_index + 2) % 4
        partner_pos = positions[partner_index]

        # Identify all suits bid so far
        suits_bid = set()
        my_bids = []

        for i, bid in enumerate(auction_history):
            if bid in ['Pass', 'XX', 'X']:
                continue

            bidder_pos = positions[i % 4]

            # Extract suit from bid (if applicable)
            if len(bid) >= 2 and bid[1] in ['♥', '♠', '♦', '♣']:
                suit = bid[1]

                # Track suits bid by partnership
                if bidder_pos in [my_pos_str, partner_pos]:
                    suits_bid.add(suit)

            # Track my bids
            if bidder_pos == my_pos_str:
                my_bids.append(bid)

        # Must have exactly 2 bids by our partnership so far
        # (1st: partner opens, 2nd: I respond, 3rd: partner rebids, now it's my 2nd bid)
        if len(my_bids) != 1:
            return None

        # Need exactly 3 suits bid by partnership
        if len(suits_bid) != 3:
            return None

        # Must have game-forcing values
        if hand.hcp < 12:
            return None

        # Find the fourth suit (not yet bid)
        all_suits = {'♥', '♠', '♦', '♣'}
        fourth_suit_set = all_suits - suits_bid

        if len(fourth_suit_set) != 1:
            return None

        fourth_suit = list(fourth_suit_set)[0]

        # Check we don't have a good natural alternative:
        # - Strong fit with partner (4+ cards in their suit)
        # - Stopper in 4th suit for NT bid
        # - Long suit of our own to rebid

        # Get partner's last suit bid
        partner_suits = []
        for i, bid in enumerate(auction_history):
            if positions[i % 4] == partner_pos and len(bid) >= 2 and bid[1] in ['♥', '♠', '♦', '♣']:
                partner_suits.append(bid[1])

        # If we have 4+ cards in partner's suit, we'd raise instead
        if partner_suits:
            partner_last_suit = partner_suits[-1]
            if hand.suit_lengths[partner_last_suit] >= 4:
                return None

        # If we have stopper in 4th suit and balanced, we might bid NT
        # But FSF is still valid if we're unsure about game level
        fourth_suit_stopper = self._has_stopper(hand, fourth_suit)

        # Get my first bid suit
        my_first_suit = None
        if my_bids and len(my_bids[0]) >= 2 and my_bids[0][1] in ['♥', '♠', '♦', '♣']:
            my_first_suit = my_bids[0][1]

        # If we have 6+ cards in our suit, we'd rebid it
        if my_first_suit and hand.suit_lengths[my_first_suit] >= 6:
            return None

        # Determine FSF bid level
        # Must be higher than partner's last bid
        # Get partner's actual last bid (not just last item in auction)
        partner_last_bid = partner_suits[-1] if partner_suits else None
        partner_last_bid_str = None

        # Find the actual bid string for partner's last suit
        for i in range(len(auction_history) - 1, -1, -1):
            bid = auction_history[i]
            if positions[i % 4] == partner_pos and len(bid) >= 2 and bid[1] in ['♥', '♠', '♦', '♣']:
                partner_last_bid_str = bid
                break

        if partner_last_bid_str and len(partner_last_bid_str) >= 2:
            last_level = int(partner_last_bid_str[0]) if partner_last_bid_str[0].isdigit() else 1
            last_suit = partner_last_bid_str[1] if len(partner_last_bid_str) > 1 else ''

            # FSF is at minimum level possible in 4th suit
            suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
            fourth_rank = suit_rank.get(fourth_suit, 0)
            last_rank = suit_rank.get(last_suit, 0)

            if fourth_rank > last_rank:
                fsf_bid = f"{last_level}{fourth_suit}"
            else:
                fsf_bid = f"{last_level + 1}{fourth_suit}"

            # Verify we can make this bid (not too high)
            fsf_level = int(fsf_bid[0])
            if fsf_level > 3:
                return None  # Too high, would be past 3NT

            stopper_info = " (no stopper)" if not fourth_suit_stopper else " (with stopper)"

            return (fsf_bid,
                   f"Fourth Suit Forcing - artificial, game-forcing bid asking partner to describe hand further. "
                   f"Shows {hand.hcp} HCP{stopper_info}.")

        return None

    def _check_fsf_response(self, hand: Hand, auction: Dict,
                           features: Dict) -> Optional[Tuple[str, str]]:
        """
        Respond to partner's Fourth Suit Forcing bid.

        Opener's priorities:
        1. Show 3-card support for responder's first suit
        2. Show stopper in 4th suit and bid NT
        3. Rebid own suit with 6+ cards
        4. Show extra values or minimum
        """

        # Check if partner's last bid was FSF
        # (Would need to track if previous bid was 4th suit - complex logic)
        # For now, simplified: if we opened and partner bid a new suit at 2-level+
        # and we haven't found a fit, might be FSF

        # This is opener's rebid after responder's potential FSF
        my_pos_str = features['positions'][features['my_index']]
        my_bids = [bid for i, bid in enumerate(features['auction_history'])
                   if features['positions'][i % 4] == my_pos_str]

        if len(my_bids) != 2:  # Not opener's 2nd rebid position
            return None

        # Simplified: Return None for now
        # Full FSF response logic would be complex and require tracking
        # whether partner's last bid was actually FSF
        return None

    def _has_stopper(self, hand: Hand, suit: str) -> bool:
        """Check if hand has stopper in suit (A, K, Qx, Jxx)"""
        # Get cards in this suit from the hand
        cards_in_suit = [c for c in hand.cards if c.suit == suit]
        if not cards_in_suit:
            return False

        # Get ranks of cards in suit
        ranks = [c.rank for c in cards_in_suit]

        # Check for stoppers
        if 'A' in ranks or 'K' in ranks:
            return True
        if 'Q' in ranks and len(ranks) >= 2:
            return True
        if 'J' in ranks and len(ranks) >= 3:
            return True

        return False

    def get_constraints(self) -> Dict:
        """Return constraints for generating FSF hands"""
        return {
            'description': 'Fourth Suit Forcing (game-forcing, no clear direction)',
            'min_hcp': 12,
            'max_hcp': 20,
            'required_distribution': 'No 8-card fit found, 12+ HCP'
        }
