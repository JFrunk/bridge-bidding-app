from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class Unusual2NTConvention(ConventionModule):
    """
    Unusual 2NT Convention - Shows 5-5+ in both minors

    SAYC Standard:
    - Jump to 2NT over opponent's opening (especially majors)
    - Shows 5-5+ in both minors (clubs and diamonds)
    - Strength: Two ranges:
      * Weak: 6-11 HCP (preemptive)
      * Strong: 17+ HCP (very strong distributional hand)
    - Middle range (12-16) should overcall or use Michaels
    - Partner picks better minor or may bid 3NT with stoppers and strength
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Evaluate if Unusual 2NT applies.

        Args:
            hand: The hand to evaluate
            features: Auction features

        Returns:
            (bid, explanation) or None
        """
        auction = features['auction_features']

        # Must be competitive auction (opponent opened)
        if not auction.get('opener') or auction.get('opener_relationship') != 'Opponent':
            return None

        # Must be our first bid
        my_pos_str = features['positions'][features['my_index']]
        my_bids = [bid for i, bid in enumerate(features['auction_history'])
                   if features['positions'][i % 4] == my_pos_str]
        if my_bids:
            # Check if we're responding to partner's Unusual 2NT
            partner_last_bid = auction.get('partner_last_bid', '')
            if partner_last_bid == '2NT' and self._is_unusual_2nt_context(auction):
                return self._respond_to_unusual_2nt(hand, auction)
            return None

        opening_bid = auction['opening_bid']

        # Check for Unusual 2NT opportunity
        result = self._check_unusual_2nt(hand, opening_bid)

        return result

    def _check_unusual_2nt(self, hand: Hand, opponent_bid: str) -> Optional[Tuple[str, str]]:
        """Check if hand qualifies for Unusual 2NT"""

        club_len = hand.suit_lengths['♣']
        diamond_len = hand.suit_lengths['♦']

        # Must have 5-5+ in both minors
        if club_len < 5 or diamond_len < 5:
            return None

        # Strength: Weak (6-11) or Strong (17+), NOT middle range
        if hand.hcp >= 12 and hand.hcp <= 16:
            return None

        # Don't use if we have a strong 4-card major (might have better action)
        if hand.suit_lengths['♥'] >= 4 and hand.hcp >= 10:
            return None
        if hand.suit_lengths['♠'] >= 4 and hand.hcp >= 10:
            return None

        # Extract opponent's bid level
        if len(opponent_bid) < 1:
            return None

        opp_level = int(opponent_bid[0])

        # Most effective over major suit openings
        if len(opponent_bid) >= 2:
            opp_suit = opponent_bid[1]
            if opp_suit in ['♥', '♠']:
                # Especially good over majors
                if hand.hcp <= 11:
                    return ("2NT",
                           f"Unusual 2NT showing 5-5+ in both minors ({club_len} clubs, {diamond_len} diamonds) with {hand.hcp} HCP (preemptive).")
                else:  # 17+ HCP
                    return ("2NT",
                           f"Unusual 2NT showing 5-5+ in both minors ({club_len} clubs, {diamond_len} diamonds) with {hand.hcp} HCP (strong).")

            # Can also use over minor openings (less common)
            elif opp_suit in ['♣', '♦']:
                # Over minors, need better hand or distribution
                if club_len + diamond_len >= 11:  # Very distributional
                    if hand.hcp <= 11:
                        return ("2NT",
                               f"Unusual 2NT showing 5-5+ in both minors ({club_len} clubs, {diamond_len} diamonds) with {hand.hcp} HCP.")
                    elif hand.hcp >= 17:
                        return ("2NT",
                               f"Unusual 2NT showing 5-5+ in both minors ({club_len} clubs, {diamond_len} diamonds) with {hand.hcp} HCP (strong).")

        return None

    def _is_unusual_2nt_context(self, auction: Dict) -> bool:
        """Check if 2NT was likely Unusual (not natural)"""
        # In competitive auctions, 2NT is usually Unusual
        if auction.get('opener_relationship') == 'Opponent':
            # Check if partner's 2NT was a jump
            opening_bid = auction.get('opening_bid', '')
            if opening_bid and opening_bid[0] == '1':
                # 2NT over 1-level opening is unusual
                return True
        return False

    def _respond_to_unusual_2nt(self, hand: Hand, auction: Dict) -> Optional[Tuple[str, str]]:
        """
        Respond to partner's Unusual 2NT.

        Partner showed 5-5 in minors. We need to:
        1. Pick the better minor (usually with 3+ support)
        2. Bid 3NT with stoppers and strength
        3. Jump to 5-level with strong fit and distribution
        """

        club_support = hand.suit_lengths['♣']
        diamond_support = hand.suit_lengths['♦']

        # With strong hand (15+ HCP) and stoppers, consider 3NT
        if hand.hcp >= 15 and hand.is_balanced:
            return ("3NT", f"Bidding 3NT with {hand.hcp} HCP and balanced hand (stoppers in opponent's suit).")

        # With very strong hand (13+ HCP) and good fit, jump to game
        if hand.hcp >= 13:
            if club_support >= diamond_support and club_support >= 3:
                return ("5♣", f"Bidding game in clubs with {club_support}-card fit and {hand.hcp} HCP.")
            elif diamond_support >= 3:
                return ("5♦", f"Bidding game in diamonds with {diamond_support}-card fit and {hand.hcp} HCP.")

        # With invitational hand (10-12 HCP) and fit, bid 4-level
        if hand.hcp >= 10:
            if club_support >= diamond_support and club_support >= 3:
                return ("4♣", f"Inviting game in clubs with {club_support}-card fit and {hand.hcp} HCP.")
            elif diamond_support >= 3:
                return ("4♦", f"Inviting game in diamonds with {diamond_support}-card fit and {hand.hcp} HCP.")

        # Pick the better minor (prefer longer suit, then clubs with equal length)
        if club_support >= diamond_support:
            return ("3♣", f"Picking clubs with {club_support}-card support.")
        else:
            return ("3♦", f"Picking diamonds with {diamond_support}-card support.")

    def get_constraints(self) -> Dict:
        """Return constraints for generating Unusual 2NT hands"""
        return {
            'description': 'Unusual 2NT (5-5 both minors)',
            'min_hcp': 6,
            'max_hcp': 11,  # or 17+ for strong variant
            'required_distribution': '5-5+ in both minors'
        }

# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("unusual_2nt", Unusual2NTConvention())
