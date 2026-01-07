"""
Regression test for marginal advance coverage gap.

Bug: advancer_bids.py Line 218 was falling through to a generic "No clear action"
Pass for hands with 8-10 HCP that had no fit, no long suit, and no stopper.

Fix: Added "Least Bad Option" heuristic - balanced/semi-balanced hands now bid
1NT to describe values rather than passing and under-representing partnership
resources.

Example hand triggering the gap:
- Partner overcalls 1♠
- You hold: ♠Qx ♥Kxxx ♦Kxxx ♣Qxx (10 HCP)
- Only 2-card spade support, no 5-card suit
- Should bid 1NT (if available) rather than Pass

Date: 2026-01-07
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.hand import Hand, Card
from engine.advancer_bids import AdvancerBidsModule


def create_hand(cards_str: str) -> Hand:
    """Helper to create hand from string like '♠Q2 ♥K765 ♦K764 ♣Q32'"""
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        ranks = part[1:]
        for rank in ranks:
            # Handle 10 as 'T'
            cards.append(Card(rank=rank, suit=suit))
    return Hand(cards)


class TestMarginalAdvanceGap:
    """Tests for the marginal advance coverage gap fix."""

    def setup_method(self):
        """Set up test fixtures."""
        self.advancer = AdvancerBidsModule()

    def _create_features(self, partner_overcall: str, opener_bid: str, my_index: int = 2):
        """Create features dict for advancer scenario."""
        # Auction: 1♣ - 1♠ - Pass - ?
        # Opener bid 1♣, partner overcalled 1♠, RHO passed, we're advancer
        return {
            'auction_history': [opener_bid, partner_overcall, 'Pass'],
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': my_index,
            'auction_features': {
                'partner_last_bid': partner_overcall,
                'opening_bid': opener_bid,
                'opener_relationship': 'LHO'
            }
        }

    def test_marginal_balanced_hand_bids_1nt(self):
        """
        Balanced 10 HCP hand with no fit should bid 1NT, not Pass.

        This is the exact scenario that triggered the gap:
        ♠Qx ♥Kxxx ♦Kxxx ♣Qxx (10 HCP, balanced)
        """
        # ♠Q2 ♥K765 ♦K764 ♣Q32 (10 HCP, 2-4-4-3 shape) - 13 cards
        hand = create_hand("♠Q2 ♥K765 ♦K764 ♣Q32")
        features = self._create_features(partner_overcall='1♠', opener_bid='1♣')

        result = self.advancer.evaluate(hand, features)

        assert result is not None, "Should return a bid, not None"
        bid, explanation = result[0], result[1]

        # Should bid 1NT with balanced 10 HCP, not Pass
        assert bid == "1NT", f"Expected 1NT for balanced 10 HCP without fit, got {bid}"
        assert "balanced" in explanation.lower() or "semi-balanced" in explanation.lower()

    def test_marginal_semi_balanced_hand_bids_1nt(self):
        """
        Semi-balanced 9 HCP hand (no singleton/void) should bid 1NT.

        ♠Jx ♥Kxx ♦QJxx ♣Kxxx (9 HCP, 2-3-4-4 shape)
        """
        hand = create_hand("♠J2 ♥K43 ♦QJ65 ♣K432")
        features = self._create_features(partner_overcall='1♠', opener_bid='1♦')

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid = result[0]

        # Should bid 1NT, not Pass
        assert bid == "1NT", f"Expected 1NT for semi-balanced 9 HCP, got {bid}"

    def test_marginal_hand_with_stopper_still_uses_stopper_path(self):
        """
        Hand with stopper should use the stopper-based 1NT path (priority 5),
        not the fallback marginal path.

        ♠xx ♥Kxx ♦AJxx ♣Qxxx (10 HCP, has diamond stopper)
        """
        hand = create_hand("♠32 ♥K43 ♦AJ65 ♣Q432")
        features = self._create_features(partner_overcall='1♠', opener_bid='1♦')

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid, explanation = result[0], result[1]

        # Should bid 1NT via stopper path, which is higher priority
        assert bid == "1NT", f"Expected 1NT for hand with stopper, got {bid}"

    def test_unbalanced_marginal_hand_with_5card_suit_bids_new_suit(self):
        """
        Unbalanced hand with singleton but 5-card suit should bid new suit (not 1NT).
        This is correct SAYC behavior - new suit shows 8+ points and 5+ cards.

        ♠x ♥Kxxx ♦Kxxxx ♣Qxx (9 HCP, singleton spade, 5-card diamond)
        """
        hand = create_hand("♠2 ♥K765 ♦K7654 ♣Q32")
        features = self._create_features(partner_overcall='1♠', opener_bid='1♣')

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid = result[0]

        # With 5-card suit, should bid the suit (new suit showing constructive values)
        assert bid == "2♦", f"Expected 2♦ new suit bid for hand with 5-card diamond, got {bid}"

    def test_truly_marginal_unbalanced_hand_passes(self):
        """
        Truly marginal unbalanced hand (singleton, no 5-card suit, no fit) should Pass.

        ♠x ♥Kxxx ♦Kxxx ♣Qxxx (9 HCP, singleton spade, no 5-card suit, no fit)
        """
        hand = create_hand("♠2 ♥K765 ♦K764 ♣Q432")
        features = self._create_features(partner_overcall='1♠', opener_bid='1♣')

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid = result[0]

        # Unbalanced with singleton but no 5-card suit - should Pass
        assert bid == "Pass", f"Expected Pass for unbalanced hand with singleton and no 5-card suit, got {bid}"

    def test_marginal_hand_with_fit_at_2_level_raises(self):
        """
        Marginal hand with fit when partner overcalled at 2-level should raise.
        This is correct SAYC - support points make the raise valid.

        ♠Qx ♥Kxxx ♦Kxxx ♣Qxx (10 HCP, 3-card club support) after 1♥ - 2♣ - Pass
        """
        hand = create_hand("♠Q2 ♥K765 ♦K764 ♣Q32")
        features = self._create_features(partner_overcall='2♣', opener_bid='1♥')

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid = result[0]

        # With 3-card club support and 10 support points, should raise
        assert bid == "3♣", f"Expected 3♣ raise with fit, got {bid}"

    def test_marginal_no_fit_at_2_level_passes(self):
        """
        Marginal hand without fit when partner overcalled at 2-level should Pass.
        Can't bid 1NT when auction is at 2-level, and no fit means no raise.

        ♠Q2 ♥K765 ♦K764 ♣Q32 (10 HCP, 3-card club support)
        But partner overcalled 2♦, we have no diamond fit
        """
        hand = create_hand("♠Q32 ♥K765 ♦K7 ♣Q432")  # Only 2 diamonds
        features = self._create_features(partner_overcall='2♦', opener_bid='1♠')

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid = result[0]

        # At 2-level, no fit, no long suit to bid, should Pass
        assert bid == "Pass", f"Expected Pass when overcall was at 2-level with no fit, got {bid}"

    def test_weak_hand_still_passes(self):
        """
        Weak hand (< 8 HCP) should still Pass regardless of shape.

        ♠Qx ♥xxxx ♦Jxxx ♣Qxx (6 HCP)
        """
        # 13 cards: 2 spades + 4 hearts + 4 diamonds + 3 clubs
        hand = create_hand("♠Q2 ♥5432 ♦J764 ♣Q32")
        features = self._create_features(partner_overcall='1♠', opener_bid='1♣')

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid = result[0]

        assert bid == "Pass", f"Expected Pass for weak hand, got {bid}"

    def test_hand_with_fit_uses_raise_not_1nt(self):
        """
        Hand with 3+ card fit should raise partner, not bid 1NT.

        ♠Qxx ♥Kxx ♦Kxxx ♣Qxx (10 HCP, 3-card spade support)
        """
        hand = create_hand("♠Q32 ♥K43 ♦K764 ♣Q32")
        features = self._create_features(partner_overcall='1♠', opener_bid='1♣')

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid = result[0]

        # With 3-card fit and 10 support points, should raise
        assert bid == "2♠", f"Expected 2♠ raise with fit, got {bid}"


class TestMarginalAdvanceIntegration:
    """Integration tests verifying the fix works in full bidding context."""

    def setup_method(self):
        """Set up test fixtures."""
        self.advancer = AdvancerBidsModule()

    def test_no_more_generic_fallback_message(self):
        """
        Verify the old generic "No clear action" message is no longer used
        for balanced marginal hands.
        """
        # Balanced 8 HCP - minimum marginal hand (13 cards: 2+3+4+4)
        hand = create_hand("♠J2 ♥Q65 ♦K764 ♣Q432")
        features = {
            'auction_history': ['1♣', '1♠', 'Pass'],
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 2,
            'auction_features': {
                'partner_last_bid': '1♠',
                'opening_bid': '1♣',
                'opener_relationship': 'LHO'
            }
        }

        result = self.advancer.evaluate(hand, features)

        assert result is not None
        bid, explanation = result[0], result[1]

        # Should NOT get the old generic fallback message
        assert "No clear action to advance partner's overcall." not in explanation
        # Should get descriptive 1NT bid instead
        assert bid == "1NT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
