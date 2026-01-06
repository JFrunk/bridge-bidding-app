from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict


class GrandSlamForceConvention(ConventionModule):
    """
    Grand Slam Force (5NT) Convention.

    SAYC Standard:
    - A jump to 5NT (when not part of Blackwood sequence) is Grand Slam Force
    - Asks partner to bid 7 of the agreed suit with 2 of the top 3 honors (A, K, Q)
    - With fewer than 2 top honors, bid 6 of the agreed suit

    Responses:
    - 6 of agreed suit = fewer than 2 top honors
    - 7 of agreed suit = 2 of the 3 top honors (A, K, or Q)
    """

    def get_constraints(self) -> Dict:
        """Defines requirements for GSF."""
        return {'hcp_range': (16, 40)}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation for Grand Slam Force."""
        # Check for responding to GSF
        if self._is_gsf_response_applicable(features):
            return self._get_gsf_response(hand, features)

        # Check for initiating GSF
        if self._should_bid_gsf(hand, features):
            return self._initiate_gsf(hand, features)

        return None

    def _should_bid_gsf(self, hand: Hand, features: Dict) -> bool:
        """
        Check if we should bid 5NT Grand Slam Force.

        Requirements:
        - Very strong hand (16+ HCP)
        - Clear suit agreement with partner
        - Partner has shown game-forcing or slam-invitational values
        - Interested in grand slam if partner has trump honors
        - Not in a Blackwood sequence (didn't bid 4NT)
        """
        auction_features = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)

        # Need very strong hand for grand slam interest
        if hand.hcp < 16:
            return False

        # Check we haven't bid 4NT (would be Blackwood sequence)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]
        if '4NT' in my_bids:
            return False  # This would be Blackwood 5NT king-ask, not GSF

        # Need a clear trump suit agreement
        trump_suit = self._get_agreed_trump_suit(features)
        if not trump_suit:
            return False

        # Must have strong trump support (at least one top honor ourselves)
        trump_cards = [card for card in hand.cards if card.suit == trump_suit]
        my_top_honors = sum(1 for card in trump_cards if card.rank in ['A', 'K', 'Q'])
        if my_top_honors == 0:
            return False  # Need at least one top honor to ask for grand

        # GSF should only be bid when slam has been established or partner has shown
        # game-forcing/slam-invitational values. Don't bid GSF after a simple raise.
        partner_bids = auction_features.get('partner_bids', [])
        partner_nonpass = [b for b in partner_bids if b not in ['Pass', 'X', 'XX']]

        if len(partner_nonpass) == 1:
            # Partner has only made one bid - check if it shows slam interest
            partner_bid = partner_nonpass[0]

            # Simple raises (2-level of opener's suit) show only 6-10 pts - not enough for GSF
            if partner_bid.startswith('2') and len(partner_bid) == 2:
                partner_suit = partner_bid[1]
                # Check if this is a simple raise of our suit
                opening_bid = auction_features.get('opening_bid', '')
                if len(opening_bid) >= 2 and partner_suit == opening_bid[1]:
                    return False  # Simple raise - let rebids module handle this

            # Jump raises (3-level) are invitational (10-12 pts) - borderline for GSF
            # Jacoby 2NT over major shows 13+ with support - OK for GSF
            # Game bids (4M) show values - OK for GSF

        # Check total points suggest grand slam possibility (37+ for 7-level)
        # Estimate partner's points based on their bidding
        # Use HCP only (not total_points) for more conservative estimate
        partner_min_points = self._estimate_partner_points(partner_nonpass, auction_features)
        combined_estimate = hand.hcp + partner_min_points

        # GSF should only be bid when grand slam is highly likely
        # Require 35+ combined HCP to even consider GSF (conservative)
        if combined_estimate < 35:
            return False

        # Also require at least 18 HCP ourselves to initiate GSF
        if hand.hcp < 18:
            return False

        return True

    def _estimate_partner_points(self, partner_bids: list, auction_features: Dict) -> int:
        """Estimate partner's minimum points from their bids."""
        if not partner_bids:
            return 0

        opening_bid = auction_features.get('opening_bid', '')
        opener_rel = auction_features.get('opener_relationship', '')

        # If partner opened
        if opener_rel == 'Partner':
            return 13  # Opening strength

        # If I opened and partner responded
        if opener_rel == 'Me' and partner_bids:
            last_bid = partner_bids[-1]

            # Jacoby 2NT over major = 13+ with support
            if last_bid == '2NT' and opening_bid and opening_bid[1] in ['♥', '♠']:
                return 13

            # 3NT response = 13-15 balanced
            if last_bid == '3NT':
                return 13

            # Jump raise (3-level of opener's suit) = 10-12
            if last_bid.startswith('3') and len(last_bid) == 2:
                if len(opening_bid) >= 2 and last_bid[1] == opening_bid[1]:
                    return 10

            # Simple raise (2-level of opener's suit) = 6-10
            if last_bid.startswith('2') and len(last_bid) == 2:
                if len(opening_bid) >= 2 and last_bid[1] == opening_bid[1]:
                    return 6

            # New suit at 2-level = 10+ (or game forcing in 2/1)
            if last_bid.startswith('2'):
                return 10

            # 1-level response = 6+
            if last_bid.startswith('1'):
                return 6

        return 6  # Default minimum

    def _get_agreed_trump_suit(self, features: Dict) -> Optional[str]:
        """
        Determine the agreed trump suit from the auction.

        Returns the suit if there's clear agreement, None otherwise.
        """
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)

        if my_index < 0 or len(auction_history) == 0:
            return None

        # Get my bids and partner's bids
        my_bids = []
        partner_bids = []
        for i, bid in enumerate(auction_history):
            if bid in ['Pass', 'X', 'XX']:
                continue
            pos = i % 4
            if pos == my_index:
                my_bids.append(bid)
            elif pos == (my_index + 2) % 4:  # Partner
                partner_bids.append(bid)

        # Look for a suit that both of us have bid (explicit agreement)
        my_suits = [bid[1] for bid in my_bids if len(bid) >= 2 and bid[1] in '♣♦♥♠']
        partner_suits = [bid[1] for bid in partner_bids if len(bid) >= 2 and bid[1] in '♣♦♥♠']

        common_suits = set(my_suits) & set(partner_suits)
        if common_suits:
            # Prefer majors
            for suit in ['♠', '♥', '♦', '♣']:
                if suit in common_suits:
                    return suit

        # If I raised partner's suit, that's the trump suit
        for partner_suit in partner_suits:
            if partner_suit in my_suits:
                return partner_suit

        # If partner raised my suit, that's the trump suit
        for my_suit in my_suits:
            if my_suit in partner_suits:
                return my_suit

        # If only one suit mentioned by either, check for specific agreement patterns
        all_suits = set(my_suits) | set(partner_suits)
        if len(all_suits) == 1:
            the_suit = list(all_suits)[0]

            # Jacoby 2NT: Partner bid 2NT over our major opening = suit agreement
            # This is a convention showing 4+ card support for opener's major
            if the_suit in ['♥', '♠'] and '2NT' in partner_bids:
                return the_suit  # Jacoby shows agreement

            # Otherwise, one suit mentioned doesn't mean agreement
            # e.g., 1♣ - 3NT means partner denied clubs (showed balanced, no major)
            # e.g., 1♥ - 3NT means partner denied heart fit (showed stoppers, 2-3 hearts)
            return None

        return None

    def _initiate_gsf(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        """Bid 5NT Grand Slam Force."""
        trump_suit = self._get_agreed_trump_suit(features)
        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}.get(trump_suit, 'trump')
        return ("5NT", f"Grand Slam Force asking partner to bid 7{trump_suit} with 2 of top 3 honors (A/K/Q) in {suit_name}.")

    def _is_gsf_response_applicable(self, features: Dict) -> bool:
        """
        Check if we should respond to partner's 5NT Grand Slam Force.

        5NT is GSF if:
        - Partner bid 5NT
        - Partner did NOT bid 4NT earlier (would be Blackwood king-ask)
        - There's an agreed trump suit
        """
        auction_features = features.get('auction_features', {})
        partner_last_bid = auction_features.get('partner_last_bid', '')

        if partner_last_bid != '5NT':
            return False

        # Check partner didn't bid 4NT (would be Blackwood sequence)
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)
        partner_index = (my_index + 2) % 4

        partner_bids = [auction_history[i] for i in range(len(auction_history))
                        if i % 4 == partner_index]
        if '4NT' in partner_bids:
            return False  # This is Blackwood king-ask, not GSF

        # Need an agreed trump suit
        trump_suit = self._get_agreed_trump_suit(features)
        return trump_suit is not None

    def _get_gsf_response(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        """
        Respond to partner's 5NT Grand Slam Force.

        - Bid 7 of trump suit with 2 of top 3 honors (A, K, Q)
        - Bid 6 of trump suit with fewer than 2 top honors
        """
        trump_suit = self._get_agreed_trump_suit(features)
        if not trump_suit:
            # Shouldn't happen, but default to 6NT
            return ("6NT", "Cannot determine trump suit, signing off in 6NT.")

        # Count top honors in trump suit
        trump_cards = [card for card in hand.cards if card.suit == trump_suit]
        top_honors = sum(1 for card in trump_cards if card.rank in ['A', 'K', 'Q'])

        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}[trump_suit]

        if top_honors >= 2:
            return (f"7{trump_suit}", f"Grand slam! Have {top_honors} of top 3 honors (A/K/Q) in {suit_name}.")
        else:
            return (f"6{trump_suit}", f"Small slam only - have {top_honors} of top 3 honors in {suit_name}.")


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("grand_slam_force", GrandSlamForceConvention())
