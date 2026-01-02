from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class SplinterBidsConvention(ConventionModule):
    """
    Splinter Bids Convention - Shows slam interest with shortness

    SAYC Standard:
    - Unusual jump in new suit (double jump or jump to 4-level)
    - Shows:
      * 4+ card support for partner's suit
      * Game-forcing values (12-15+ support points)
      * Singleton or void in the bid suit
    - Example: 1e - 4c (shows club shortness, heart support, slam interest)
    - Example: 1` - 4f (shows diamond shortness, spade support, slam interest)

    Splinter helps partner evaluate:
    - If their honors in splinter suit are wasted
    - Whether slam is feasible based on fitting honors
    """

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Evaluate if Splinter Bid applies.

        Args:
            hand: The hand to evaluate
            features: Auction features

        Returns:
            (bid, explanation) or None
        """
        auction = features['auction_features']

        # Splinters are responding hands - partner must have opened
        if auction.get('opener_relationship') != 'Partner':
            return None

        opening_bid = auction.get('opening_bid', '')

        # Only splinter after partner's suit opening (not 1NT or 2NT)
        if not opening_bid or len(opening_bid) < 2:
            return None

        opening_suit = opening_bid[1]
        if opening_suit not in ['♥', '♠', '♦', '♣']:
            return None

        # Must be our first bid (no interference or direct splinter)
        my_pos_str = features['positions'][features['my_index']]
        my_bids = [bid for i, bid in enumerate(features['auction_history'])
                   if features['positions'][i % 4] == my_pos_str]
        if my_bids:
            return None

        # Check for splinter opportunity
        result = self._check_splinter(hand, opening_bid, opening_suit, auction)

        return result

    def _check_splinter(self, hand: Hand, opening_bid: str,
                       opening_suit: str, auction: Dict) -> Optional[Tuple[str, str]]:
        """Check if hand qualifies for splinter bid"""

        # Must have 4+ card support for partner's suit
        support = hand.suit_lengths[opening_suit]
        if support < 4:
            return None

        # Calculate support points (HCP + distribution)
        support_points = hand.hcp
        for suit in ['♥', '♠', '♦', '♣']:
            if suit != opening_suit:
                length = hand.suit_lengths[suit]
                if length <= 1:
                    # Add points for shortness when we have a fit
                    if length == 1:
                        support_points += 2  # Singleton
                    else:
                        support_points += 3  # Void (but be conservative)

        # Need game-forcing values (12-15+ support points)
        if support_points < 12:
            return None

        # Don't splinter with 16+ HCP (too strong, might miss slam - use other methods)
        if hand.hcp > 15:
            return None

        # Find singleton or void suits
        shortness_suits = []
        for suit in ['♥', '♠', '♦', '♣']:
            if suit != opening_suit and hand.suit_lengths[suit] <= 1:
                shortness_suits.append((suit, hand.suit_lengths[suit]))

        if not shortness_suits:
            return None

        # Prefer splinter in the highest-ranking short suit (more descriptive)
        # Rank order: ♠ > ♥ > ♦ > ♣
        suit_rank = {'♠': 4, '♥': 3, '♦': 2, '♣': 1}
        shortness_suits.sort(key=lambda x: suit_rank[x[0]], reverse=True)

        splinter_suit, short_length = shortness_suits[0]

        # Determine splinter level
        # Splinters are unusual jumps (usually to 4-level, or 3-level if partner opened minor)
        opening_level = int(opening_bid[0])

        # Over major opening (1♥ or 1♠), splinter at 4-level
        if opening_suit in ['♥', '♠']:
            splinter_bid = f"4{splinter_suit}"
        # Over minor opening (1♣ or 1♦), splinter at 3-level or 4-level
        else:
            # Use 3-level for lower shortage suits, 4-level for spades
            if splinter_suit == '♠':
                splinter_bid = f"3{splinter_suit}"
            else:
                # Determine if this is a jump
                # Normal bid would be 1-level or 2-level
                # 3-level or 4-level is a jump splinter
                if splinter_suit in ['♥']:
                    splinter_bid = f"3{splinter_suit}"
                else:
                    splinter_bid = f"4{splinter_suit}"

        # Verify this is actually an unusual jump
        # (e.g., 1e-4c is unusual, 1e-2c is not)
        splinter_level = int(splinter_bid[0])

        # Must be at least 3-level (for minors) or 4-level (for majors over majors)
        if opening_suit in ['♥', '♠'] and splinter_level < 4:
            return None
        if opening_suit in ['♦', '♣'] and splinter_level < 3:
            return None

        shortness_desc = "singleton" if short_length == 1 else "void"

        # Metadata to bypass suit length validation - splinter bids are ARTIFICIAL
        # The bid shows shortness in the suit, NOT length
        # Also bypass HCP validation since this uses support points
        splinter_metadata = {
            'bypass_suit_length': True,
            'bypass_hcp': True,
            'convention': 'splinter',
            'game_forcing': True  # Splinters are game-forcing
        }

        return (splinter_bid,
               f"Splinter bid showing {support}-card {self._suit_name(opening_suit)} support, "
               f"{shortness_desc} in {self._suit_name(splinter_suit)}, and slam interest "
               f"({hand.hcp} HCP, {support_points} support points).",
               splinter_metadata)

    def _suit_name(self, suit: str) -> str:
        """Convert suit symbol to name"""
        names = {'♥': 'hearts', '♠': 'spades', '♦': 'diamonds', '♣': 'clubs'}
        return names.get(suit, suit)

    def get_constraints(self) -> Dict:
        """Return constraints for generating Splinter hands"""
        return {
            'description': 'Splinter Bid (shortness + support + slam interest)',
            'min_hcp': 12,
            'max_hcp': 15,
            'required_distribution': '4+ support, singleton or void in side suit'
        }

# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("splinter_bids", SplinterBidsConvention())
