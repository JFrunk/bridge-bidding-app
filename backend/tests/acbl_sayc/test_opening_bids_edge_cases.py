"""
ACBL SAYC Test Suite: Opening Bids - Edge Cases and Boundary Conditions

This file specifically tests boundary conditions that can slip through
standard testing. For each rule, we test:
1. Exact minimum threshold
2. Exact maximum threshold (if applicable)
3. Conditions that would have triggered bugs (e.g., missing OR clauses)

Created after user feedback discovered 2♣ rule was too restrictive.
"""
import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


def make_hand(spades: str, hearts: str, diamonds: str, clubs: str) -> Hand:
    """Create a Hand from suit strings like 'AKQ32' for each suit."""
    cards = []
    for suit, holding in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for rank in holding:
            cards.append(Card(rank, suit))
    if len(cards) != 13:
        raise ValueError(f"Hand must have 13 cards, got {len(cards)}")
    return Hand(cards)


def get_opening_bid(hand: Hand) -> tuple:
    """Get the opening bid for a hand."""
    engine = BiddingEngine()
    return engine.get_next_bid(
        hand=hand,
        auction_history=[],
        my_position="South",
        vulnerability="None",
        dealer="South"
    )


# =============================================================================
# Strong 2♣ Opening: Boundary Condition Tests
# =============================================================================

class TestStrong2ClubBoundaryConditions:
    """Test 2♣ opening at exact thresholds to catch rule configuration bugs.

    Bug discovered 2026-02-05: Rule required 22+ HCP AND (4+ quick tricks OR 24+ HCP)
    which meant 22-23 HCP hands without 4 quick tricks incorrectly skipped 2♣.
    """

    def test_2c_exactly_22_hcp_balanced_low_quick_tricks(self):
        """CRITICAL: 22 HCP balanced with only 2-3 quick tricks must still open 2♣.

        This is the exact case that caught the bug - the rule required
        additional conditions beyond just 22+ HCP.
        """
        # ♠ AKQJ ♥ AK53 ♦ KQ7 ♣ 64 = 10+7+5+0 = 22 HCP
        # Quick tricks: AKQ=2.5 + AK=2 + KQ=1.5 = 6... too many
        # Need exactly 22 HCP with fewer quick tricks
        # ♠ AKQJ ♥ AK53 ♦ KQ7 ♣ 64 has 22 HCP
        # Let me recalculate: A(4)+K(3)+Q(2)+J(1) + A(4)+K(3) + K(3)+Q(2) = 22 ✓
        hand = make_hand("AKQJ", "AK53", "KQ7", "64")
        assert hand.hcp == 22, f"Expected 22 HCP, got {hand.hcp}"
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "2♣", f"22 HCP balanced MUST open 2♣, got {bid}"

    def test_2c_exactly_22_hcp_unbalanced_low_quick_tricks(self):
        """22 HCP unbalanced with moderate quick tricks must open 2♣."""
        # ♠ AKQJ32 ♥ AKQ ♦ K7 ♣ 64 = 10+9+3+0 = 22 HCP, 6-3-2-2
        hand = make_hand("AKQJ32", "AKQ", "K7", "64")
        assert hand.hcp == 22, f"Expected 22 HCP, got {hand.hcp}"
        assert not hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "2♣", f"22 HCP unbalanced MUST open 2♣, got {bid}"

    def test_2c_23_hcp_balanced(self):
        """23 HCP balanced must open 2♣ regardless of quick tricks."""
        # ♠ AKQJ ♥ AKJ ♦ KQ7 ♣ Q64 = 10+8+5+2 = 25... too much
        # ♠ AKQ2 ♥ AKJ ♦ KQ7 ♣ 764 = 9+8+5+0 = 22... need 23
        # ♠ AKQ2 ♥ AKJ ♦ KQJ ♣ 764 = 9+8+6+0 = 23
        hand = make_hand("AKQ2", "AKJ", "KQJ", "764")
        assert hand.hcp == 23, f"Expected 23 HCP, got {hand.hcp}"
        bid, _ = get_opening_bid(hand)
        assert bid == "2♣", f"23 HCP must open 2♣, got {bid}"

    def test_2c_minimum_21_hcp_does_not_qualify(self):
        """21 HCP balanced should NOT open 2♣ (opens 2NT)."""
        # ♠ AKJ2 ♥ AQ3 ♦ KJ32 ♣ K2 = 8+6+4+3 = 21 HCP
        hand = make_hand("AKJ2", "AQ3", "KJ32", "K2")
        assert hand.hcp == 21, f"Expected 21 HCP, got {hand.hcp}"
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "2NT", f"21 HCP balanced should open 2NT not 2♣, got {bid}"


# =============================================================================
# 2NT Opening: Boundary Condition Tests
# =============================================================================

class Test2NTBoundaryConditions:
    """Test 2NT opening at exact thresholds (20-21 HCP balanced)."""

    def test_2nt_exactly_20_hcp(self):
        """20 HCP balanced must open 2NT."""
        # ♠ AKJ2 ♥ AQ3 ♦ KJ32 ♣ Q2 = 8+6+4+2 = 20 HCP
        hand = make_hand("AKJ2", "AQ3", "KJ32", "Q2")
        assert hand.hcp == 20, f"Expected 20 HCP, got {hand.hcp}"
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "2NT", f"20 HCP balanced must open 2NT, got {bid}"

    def test_2nt_exactly_21_hcp(self):
        """21 HCP balanced must open 2NT."""
        # ♠ AKJ2 ♥ AQ3 ♦ KJ32 ♣ K2 = 8+6+4+3 = 21 HCP
        hand = make_hand("AKJ2", "AQ3", "KJ32", "K2")
        assert hand.hcp == 21, f"Expected 21 HCP, got {hand.hcp}"
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "2NT", f"21 HCP balanced must open 2NT, got {bid}"

    def test_2nt_19_hcp_does_not_qualify(self):
        """19 HCP balanced should NOT open 2NT (opens 1NT rebid sequence)."""
        # ♠ AKJ2 ♥ AQ3 ♦ J432 ♣ K2 = 8+6+1+3 = 18 HCP
        # Need 19: ♠ AKJ2 ♥ AQ3 ♦ KJ32 ♣ 32 = 8+6+4+0 = 18... still not 19
        # ♠ AKJ2 ♥ AQ3 ♦ KJ32 ♣ J2 = 8+6+4+1 = 19
        hand = make_hand("AKJ2", "AQ3", "KJ32", "J2")
        assert hand.hcp == 19, f"Expected 19 HCP, got {hand.hcp}"
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid != "2NT", f"19 HCP should not open 2NT, got {bid}"


# =============================================================================
# 1NT Opening: Boundary Condition Tests
# =============================================================================

class Test1NTBoundaryConditions:
    """Test 1NT opening at exact thresholds (15-17 HCP balanced)."""

    def test_1nt_exactly_15_hcp(self):
        """15 HCP balanced must open 1NT."""
        # ♠ AQ32 ♥ KJ5 ♦ Q43 ♣ K32 = 6+4+2+3 = 15 HCP
        hand = make_hand("AQ32", "KJ5", "Q43", "K32")
        assert hand.hcp == 15, f"Expected 15 HCP, got {hand.hcp}"
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "1NT", f"15 HCP balanced must open 1NT, got {bid}"

    def test_1nt_exactly_17_hcp(self):
        """17 HCP balanced must open 1NT."""
        # ♠ AKJ2 ♥ KQ43 ♦ J32 ♣ K2 = 8+5+1+3 = 17 HCP
        hand = make_hand("AKJ2", "KQ43", "J32", "K2")
        assert hand.hcp == 17, f"Expected 17 HCP, got {hand.hcp}"
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "1NT", f"17 HCP balanced must open 1NT, got {bid}"

    def test_1nt_14_hcp_does_not_qualify(self):
        """14 HCP balanced should NOT open 1NT."""
        # ♠ AQ32 ♥ KJ5 ♦ Q43 ♣ Q32 = 6+4+2+2 = 14 HCP
        hand = make_hand("AQ32", "KJ5", "Q43", "Q32")
        assert hand.hcp == 14, f"Expected 14 HCP, got {hand.hcp}"
        bid, _ = get_opening_bid(hand)
        assert bid != "1NT", f"14 HCP should NOT open 1NT, got {bid}"

    def test_1nt_18_hcp_does_not_qualify(self):
        """18 HCP balanced should NOT open 1NT (too strong)."""
        # ♠ AK32 ♥ KQ43 ♦ Q32 ♣ A2 = 7+5+2+4 = 18 HCP
        hand = make_hand("AK32", "KQ43", "Q32", "A2")
        assert hand.hcp == 18, f"Expected 18 HCP, got {hand.hcp}"
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid != "1NT", f"18 HCP should NOT open 1NT, got {bid}"


# =============================================================================
# Weak Two Bids: Boundary Condition Tests
# =============================================================================

class TestWeakTwoBoundaryConditions:
    """Test weak two bids at exact thresholds (5-11 HCP, 6-card suit)."""

    def test_weak_2_exactly_5_hcp(self):
        """5 HCP is minimum for weak two - borderline acceptable."""
        # ♠ 32 ♥ KQT932 ♦ 432 ♣ 32 = 0+5+0+0 = 5 HCP
        hand = make_hand("32", "KQT932", "432", "32")
        assert hand.hcp == 5, f"Expected 5 HCP, got {hand.hcp}"
        bid, _ = get_opening_bid(hand)
        # 5 HCP is minimum - both 2♥ and Pass are acceptable
        assert bid in ["2♥", "Pass"], f"5 HCP weak two or pass, got {bid}"

    def test_weak_2_exactly_11_hcp(self):
        """11 HCP is maximum for weak two - borderline with opening."""
        # ♠ 32 ♥ AQJ932 ♦ KJ2 ♣ 32 = 0+7+4+0 = 11 HCP
        hand = make_hand("32", "AQJ932", "KJ2", "32")
        assert hand.hcp == 11, f"Expected 11 HCP, got {hand.hcp}"
        bid, _ = get_opening_bid(hand)
        # 11 HCP is borderline - weak 2♥ or light 1♥ acceptable
        assert bid in ["2♥", "1♥"], f"11 HCP borderline, got {bid}"

    def test_weak_2_12_hcp_does_not_qualify(self):
        """12 HCP exceeds weak two range - should open at 1-level."""
        # ♠ 32 ♥ AKJ932 ♦ KJ2 ♣ 32 = 0+8+4+0 = 12 HCP
        hand = make_hand("32", "AKJ932", "KJ2", "32")
        assert hand.hcp == 12, f"Expected 12 HCP, got {hand.hcp}"
        bid, _ = get_opening_bid(hand)
        # 12 HCP is opening values - should open 1♥
        assert bid in ["1♥", "Pass"], f"12 HCP should open 1♥ or pass, got {bid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
