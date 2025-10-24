from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict

class MichaelsCuebidConvention(ConventionModule):
    """
    Michaels Cuebid Convention - Shows 5-5+ in two suits

    SAYC Standard:
    - After 1c/1f: Cuebid (2c/2f) shows both majors (5-5+)
    - After 1e: 2e shows spades + minor (5-5+), partner asks with 2NT
    - After 1`: 2` shows hearts + minor (5-5+), partner asks with 2NT
    - Strength: 8-16 HCP (weak to intermediate)
    - Partner bids suit or 2NT to ask for minor
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation function with bid validation."""
        auction_history = features.get('auction_history', [])

        # Get the raw michaels bid
        result = self._evaluate_michaels(hand, features)

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
            # Prevents Michaels responses from escalating to unreasonable levels
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

    def _evaluate_michaels(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates michaels bid without validation."""
        auction = features['auction_features']

        # Must be competitive auction (opponent opened)
        if not auction.get('opener') or auction.get('opener_relationship') != 'Opponent':
            return None

        # Must be our first bid
        my_pos_str = features['positions'][features['my_index']]
        my_bids = [bid for i, bid in enumerate(features['auction_history'])
                   if features['positions'][i % 4] == my_pos_str]
        if my_bids:
            return None

        opening_bid = auction['opening_bid']

        # Check for Michaels cuebid opportunities
        result = self._check_michaels_cuebid(hand, opening_bid)

        # If Michaels applies, return it
        if result:
            return result

        # Check if we're responding to partner's Michaels
        partner_last_bid = auction.get('partner_last_bid', '')
        if partner_last_bid and self._is_michaels_cuebid(partner_last_bid, opening_bid):
            return self._respond_to_michaels(hand, partner_last_bid, opening_bid, auction)

        return None

    def _check_michaels_cuebid(self, hand: Hand, opponent_bid: str) -> Optional[Tuple[str, str]]:
        """Check if hand qualifies for Michaels cuebid"""

        # Strength: 8-16 HCP (don't want to be too strong)
        if hand.hcp < 8 or hand.hcp > 16:
            return None

        # Extract opponent's suit
        if len(opponent_bid) < 2:
            return None
        opp_suit = opponent_bid[1]

        # After minor opening (1♣ or 1♦): Cuebid shows both majors
        if opp_suit in ['♣', '♦']:
            if hand.suit_lengths['♥'] >= 5 and hand.suit_lengths['♠'] >= 5:
                cuebid_level = int(opponent_bid[0]) + 1
                cuebid = f"{cuebid_level}{opp_suit}"
                return (cuebid,
                       f"Michaels Cuebid showing 5-5+ in both majors ({hand.hcp} HCP).")

        # After 1♥: Cuebid shows spades + minor (5-5+)
        elif opp_suit == '♥':
            spade_len = hand.suit_lengths['♠']
            club_len = hand.suit_lengths['♣']
            diamond_len = hand.suit_lengths['♦']

            if spade_len >= 5:
                # Find which minor is 5+ cards
                if club_len >= 5 or diamond_len >= 5:
                    return ("2♥",
                           f"Michaels Cuebid showing 5+ spades and 5+ in a minor ({hand.hcp} HCP). Partner can ask with 2NT.")

        # After 1♠: Cuebid shows hearts + minor (5-5+)
        elif opp_suit == '♠':
            heart_len = hand.suit_lengths['♥']
            club_len = hand.suit_lengths['♣']
            diamond_len = hand.suit_lengths['♦']

            if heart_len >= 5:
                # Find which minor is 5+ cards
                if club_len >= 5 or diamond_len >= 5:
                    return ("2♠",
                           f"Michaels Cuebid showing 5+ hearts and 5+ in a minor ({hand.hcp} HCP). Partner can ask with 2NT.")

        return None

    def _is_michaels_cuebid(self, bid: str, opponent_bid: str) -> bool:
        """Check if partner's bid was a Michaels cuebid"""
        if len(bid) < 2 or len(opponent_bid) < 2:
            return False

        # Michaels is a cuebid of opponent's suit at the 2-level
        return (bid[0] == '2' and bid[1:] == opponent_bid[1:])

    def _respond_to_michaels(self, hand: Hand, michaels_bid: str,
                            opening_bid: str, auction: Dict) -> Optional[Tuple[str, str]]:
        """
        Respond to partner's Michaels cuebid.

        Partner showed 5-5 in two suits. We need to:
        1. Pick one of partner's suits (usually with 3+ support)
        2. Bid 2NT to ask for the minor (if partner showed major + minor)
        3. Jump to game with strong hand
        """

        opp_suit = opening_bid[1] if len(opening_bid) >= 2 else ''

        # After minor opening, partner showed both majors
        if opp_suit in ['c', 'f']:
            heart_support = hand.suit_lengths['e']
            spade_support = hand.suit_lengths['`']

            # With strong hand (11+ HCP) and fit, jump to game
            if hand.hcp >= 11:
                if spade_support >= 3:
                    return ("4`", f"Game in spades with {spade_support}-card fit and {hand.hcp} HCP.")
                if heart_support >= 3:
                    return ("4e", f"Game in hearts with {heart_support}-card fit and {hand.hcp} HCP.")

            # Pick the major with better fit (prefer spades with equal length)
            if spade_support >= heart_support and spade_support >= 3:
                level = 3 if hand.hcp >= 9 else 2
                return (f"{level}`", f"Supporting partner's spades with {spade_support}-card fit.")
            elif heart_support >= 3:
                level = 3 if hand.hcp >= 9 else 2
                return (f"{level}e", f"Supporting partner's hearts with {heart_support}-card fit.")

            # With weak hand and no clear fit, pick spades (higher)
            return ("2`", "Picking spades (partner's higher major).")

        # After major opening, partner showed other major + minor
        # Determine which major partner has
        if opp_suit == 'e':
            # Partner has spades + minor
            spade_support = hand.suit_lengths['`']

            # With 3+ spades, support them
            if spade_support >= 3:
                if hand.hcp >= 11:
                    return ("4`", f"Game in spades with {spade_support}-card fit and {hand.hcp} HCP.")
                level = 3 if hand.hcp >= 9 else 2
                return (f"{level}`", f"Supporting partner's spades with {spade_support}-card fit.")

            # With weak spades, ask for minor with 2NT or pass 2`
            if hand.hcp >= 9:
                return ("2NT", "Asking partner to show their minor suit.")

            return ("2`", "Passing partner's spade suit.")

        elif opp_suit == '`':
            # Partner has hearts + minor
            heart_support = hand.suit_lengths['e']

            # With 3+ hearts, support them
            if heart_support >= 3:
                if hand.hcp >= 11:
                    return ("4e", f"Game in hearts with {heart_support}-card fit and {hand.hcp} HCP.")
                level = 3 if hand.hcp >= 9 else 2
                return (f"{level}e", f"Supporting partner's hearts with {heart_support}-card fit.")

            # With weak hearts, ask for minor with 2NT
            if hand.hcp >= 9:
                return ("2NT", "Asking partner to show their minor suit.")

            return None  # Can't support the major, no good bid

        return None

    def get_constraints(self) -> Dict:
        """Return constraints for generating Michaels hands"""
        return {
            'description': 'Michaels Cuebid (5-5 two suits)',
            'min_hcp': 8,
            'max_hcp': 16,
            'required_distribution': '5-5+ in two specific suits'
        }
