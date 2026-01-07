"""
Regression test for Balancing Module (Borrowed King principle).

The Balancing Module implements the "+3 Virtual HCP Offset" for pass-out seat:
- Balancing 1NT: 11-14 HCP (vs 15-18 direct)
- Balancing Double: 8+ HCP (vs 12+ direct)
- Balancing Suit: 8+ HCP (vs 10+ direct)

The "Borrowed King" principle: When opponents bid and two passes follow,
partner has ~8-10 HCP trapped behind the opener. We "borrow" from partner.

Date: 2026-01-07
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.balancing import BalancingModule


def create_hand(cards_str: str) -> Hand:
    """Helper to create hand from string like '♠AKQ32 ♥AK ♦KQ32 ♣32'"""
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        ranks = part[1:]
        for rank in ranks:
            cards.append(Card(rank=rank, suit=suit))
    return Hand(cards)


class TestBalancing1NT:
    """Tests for Balancing 1NT (11-14 HCP, balanced, stopper)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_balance_1nt_with_12_hcp(self):
        """
        12 HCP balanced with stopper should bid 1NT in balancing seat.
        Direct seat would need 15-18 HCP for 1NT overcall.
        """
        # 12 HCP balanced: K(3) + Q(2) + A(4) + K(3) = 12
        hand = create_hand("♠KQ76 ♥A54 ♦K98 ♣765")

        # Opponent opened 1♥, partner passed, RHO passed
        auction = ["1♥", "Pass", "Pass"]
        bid, explanation = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        assert bid == "1NT", f"12 HCP balanced with stopper should balance 1NT, got {bid}"
        assert "Balancing" in explanation.get('primary_reason', '') or "balancing" in explanation.get('primary_reason', '').lower()

    def test_balance_1nt_with_14_hcp(self):
        """
        14 HCP balanced with stopper should bid 1NT in balancing seat.
        At the top of the range but still balancing 1NT.
        """
        # 14 HCP balanced: A(4) + Q(2) + A(4) + Q(2) + J(1) + J(1) = 14
        hand = create_hand("♠AQ76 ♥A54 ♦QJ8 ♣J76")

        auction = ["1♦", "Pass", "Pass"]
        bid, explanation = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        assert bid == "1NT", f"14 HCP balanced with stopper should balance 1NT, got {bid}"

    def test_no_balance_1nt_with_10_hcp(self):
        """
        10 HCP is below the 11 HCP minimum for balancing 1NT.
        Should double or bid a suit instead.
        """
        # 10 HCP: K(3) + Q(2) + Q(2) + K(3) = 10
        hand = create_hand("♠KQ76 ♥Q54 ♦K98 ♣765")

        auction = ["1♥", "Pass", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # Should not be 1NT (below minimum), expect double or Pass
        assert bid != "1NT", f"10 HCP should not balance 1NT, got {bid}"

    def test_no_balance_1nt_without_stopper(self):
        """
        12 HCP balanced but NO stopper in opponent's suit.
        Should not bid 1NT, should double or bid suit.
        """
        # 12 HCP but no heart stopper (opponent opened 1♥)
        hand = create_hand("♠KQ76 ♥543 ♦AK8 ♣765")

        auction = ["1♥", "Pass", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # Without stopper, should double (has support for unbid) or Pass
        assert bid != "1NT", f"Should not balance 1NT without stopper, got {bid}"


class TestBalancingDouble:
    """Tests for Balancing Takeout Double (8+ HCP with shape)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_balance_double_with_9_hcp(self):
        """
        9 HCP with classic takeout shape should double in balancing seat.
        Direct seat would need 12+ HCP.
        """
        # 9 HCP: K(3) + Q(2) + Q(2) + J(1) + J(1) = 9
        # Shape: 4-4-3-2 with shortness in hearts (opponent's suit)
        hand = create_hand("♠KQ76 ♥54 ♦QJ98 ♣J76")

        auction = ["1♥", "Pass", "Pass"]
        bid, explanation = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        assert bid == "X", f"9 HCP with takeout shape should balance double, got {bid}"

    def test_balance_double_with_8_hcp(self):
        """
        8 HCP minimum for balancing double (vs 12+ direct).
        """
        # 8 HCP: K(3) + Q(2) + Q(2) + J(1) = 8
        hand = create_hand("♠KQ76 ♥54 ♦Q987 ♣J76")

        auction = ["1♥", "Pass", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # With 8 HCP and good shape, should double
        assert bid == "X", f"8 HCP with takeout shape should balance double, got {bid}"

    def test_no_balance_double_with_7_hcp(self):
        """
        7 HCP is below the minimum for balancing double.
        """
        # 7 HCP: K(3) + Q(2) + J(1) + J(1) = 7
        hand = create_hand("♠KJ76 ♥54 ♦Q987 ♣J76")

        auction = ["1♥", "Pass", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # With only 7 HCP, should pass (or bid suit if strong suit)
        assert bid != "X", f"7 HCP should not balance double, got {bid}"

    def test_no_balance_double_with_length_in_opponent_suit(self):
        """
        Even with 10 HCP, 4+ cards in opponent's suit means no takeout double.
        This is a "trap" hand - pass and defend.
        """
        # 10 HCP but 4 hearts (opponent opened 1♥) - trap pass
        hand = create_hand("♠K76 ♥QJ54 ♦K98 ♣765")

        auction = ["1♥", "Pass", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # With length in opponent's suit, should pass or bid NT, not double
        assert bid != "X", f"Should not double with 4 cards in opponent's suit, got {bid}"


class TestBalancingSuitBid:
    """Tests for Balancing Suit Bids (8+ HCP with 5+ card suit)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_balance_suit_with_8_hcp_5_card_major(self):
        """
        8 HCP with 5-card major should bid suit in balancing seat.
        """
        # 8 HCP: K(3) + Q(2) + Q(2) + J(1) = 8 with 5 spades
        hand = create_hand("♠KQJ76 ♥54 ♦Q98 ♣765")

        auction = ["1♥", "Pass", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # With 5-card major and 8 HCP, should bid 1♠
        assert bid == "1♠", f"8 HCP with 5-card spade should balance 1♠, got {bid}"

    def test_balance_suit_at_2_level_needs_quality(self):
        """
        At 2-level, need better suit quality (more HCP in suit).
        """
        # 10 HCP with 5-card club (opponent opened 1♠)
        # Need to bid at 2-level, so suit should be good
        hand = create_hand("♠54 ♥Q98 ♦K76 ♣AQ765")

        auction = ["1♠", "Pass", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # With AQ in clubs (good suit), should bid 2♣
        # Or might double if shape supports it
        assert bid in ["2♣", "X"], f"Expected 2♣ or X with good club suit, got {bid}"


class TestBalancingEdgeCases:
    """Edge cases and special scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_not_balancing_seat_after_responder_bid(self):
        """
        If responder made a bid, this is not balancing seat.
        """
        # 10 HCP - would balance if in passout seat
        hand = create_hand("♠KQ76 ♥54 ♦QJ98 ♣J76")

        # Responder bid 2♥, so not passout seat
        auction = ["1♥", "Pass", "2♥", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # This is NOT balancing seat - responder bid
        # With 10 HCP, might pass or make a competitive action
        # Just verify we don't crash and get a legal response
        assert bid in ["Pass", "X", "2♠", "2NT", "3♣", "3♦"], f"Got unexpected bid {bid}"

    def test_trap_pass_with_strong_holding_in_opponent_suit(self):
        """
        With KQJx in opponent's suit, should trap pass.
        """
        # 10 HCP with KQJ in hearts (opponent opened 1♥)
        hand = create_hand("♠876 ♥KQJ5 ♦K98 ♣765")

        auction = ["1♥", "Pass", "Pass"]
        bid, explanation = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        # Should trap pass with strong heart holding
        assert bid == "Pass", f"Should trap pass with KQJ in opponent's suit, got {bid}"

    def test_weak_hand_passes(self):
        """
        Very weak hand (< 8 HCP) should pass even in balancing seat.
        """
        # 5 HCP: Q(2) + J(1) + J(1) + J(1) = 5
        hand = create_hand("♠Q765 ♥J54 ♦J98 ♣J76")

        auction = ["1♥", "Pass", "Pass"]
        bid, _ = self.engine.get_next_bid_structured(hand, auction, "West", "None")

        assert bid == "Pass", f"5 HCP should pass in balancing seat, got {bid}"


class TestBalancingModuleDirectly:
    """Direct unit tests for BalancingModule class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.module = BalancingModule()

    def test_virtual_offset_constant(self):
        """Verify the Borrowed King offset is +3."""
        assert self.module.VIRTUAL_OFFSET == 3

    def test_stopper_detection(self):
        """Test stopper detection logic."""
        # Hand with Ace stopper (4+3+3+3=13 cards)
        hand = create_hand("♠A765 ♥654 ♦K98 ♣J76")
        assert self.module._has_stopper(hand, '♠') is True

        # Hand with Kx stopper (2+4+3+4=13 cards)
        hand = create_hand("♠K7 ♥6543 ♦K98 ♣J765")
        assert self.module._has_stopper(hand, '♠') is True

        # Hand with no stopper (small cards) (3+4+3+3=13 cards)
        hand = create_hand("♠765 ♥6543 ♦K98 ♣J76")
        assert self.module._has_stopper(hand, '♠') is False

    def test_trap_hand_detection(self):
        """Test trap hand detection (strong holdings in opponent's suit)."""
        # KQJx is a trap hand
        hand = create_hand("♠876 ♥KQJ5 ♦K98 ♣765")
        assert self.module._has_trap_hand(hand, '♥') is True

        # Small cards are not a trap
        hand = create_hand("♠876 ♥6543 ♦K98 ♣A76")
        assert self.module._has_trap_hand(hand, '♥') is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
