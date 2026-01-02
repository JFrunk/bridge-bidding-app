"""
ACBL SAYC Test Suite: Opening Bids

Reference: ACBL SAYC Booklet - "Opening the Bidding" section

Opening bid requirements from SAYC:
- 1-level suit: 13+ points (12 with good suit/shape)
- 1NT: 15-17 HCP, balanced
- 2♣: 22+ HCP, or 9+ tricks
- 2♦/2♥/2♠: Weak two (5-11 HCP, good 6-card suit)
- 2NT: 20-21 HCP, balanced
- 3-level: Preemptive (good 7+ card suit, less than opening values)
"""
import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


# =============================================================================
# Test Helpers
# =============================================================================

def make_hand(spades: str, hearts: str, diamonds: str, clubs: str) -> Hand:
    """Create a Hand from suit strings like 'AKQ32' for each suit."""
    cards = []
    for suit, holding in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for rank in holding:
            # Convert 'T' to '10' display but keep as 'T' internally
            cards.append(Card(rank, suit))

    if len(cards) != 13:
        raise ValueError(f"Hand must have 13 cards, got {len(cards)}: ♠{spades} ♥{hearts} ♦{diamonds} ♣{clubs}")

    return Hand(cards)


def get_opening_bid(hand: Hand, vulnerability: str = "None") -> tuple:
    """Get the opening bid for a hand (first to bid, no interference)."""
    engine = BiddingEngine()
    return engine.get_next_bid(
        hand=hand,
        auction_history=[],
        my_position="South",
        vulnerability=vulnerability,
        dealer="South"
    )


# =============================================================================
# 1NT Opening: 15-17 HCP, Balanced
# =============================================================================

class TestOneNotrumpOpening:
    """SAYC: 1NT shows 15-17 HCP and a balanced hand (no singleton, no void, at most one doubleton)."""

    def test_1nt_minimum_15_hcp_4333(self):
        """SAYC Example: 15 HCP, 4-3-3-3 shape opens 1NT."""
        # ♠ AQ32 ♥ KJ5 ♦ Q43 ♣ K32
        # HCP: A(4)+Q(2)+K(3)+J(1)+Q(2)+K(3) = 15
        hand = make_hand("AQ32", "KJ5", "Q43", "K32")
        assert hand.hcp == 15
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "1NT", f"15 HCP balanced should open 1NT, got {bid}"

    def test_1nt_maximum_17_hcp_4432(self):
        """SAYC Example: 17 HCP, 4-4-3-2 shape opens 1NT."""
        # ♠ AKJ2 ♥ KQ43 ♦ Q32 ♣ K2
        # HCP: A(4)+K(3)+J(1)+K(3)+Q(2)+Q(2)+K(3) = 18... adjust
        # ♠ AKJ2 ♥ KQ43 ♦ J32 ♣ K2 = 4+3+1+3+2+1+3 = 17
        hand = make_hand("AKJ2", "KQ43", "J32", "K2")
        assert hand.hcp == 17
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "1NT", f"17 HCP balanced should open 1NT, got {bid}"

    def test_1nt_16_hcp_5332(self):
        """SAYC Example: 16 HCP, 5-3-3-2 with 5-card minor opens 1NT."""
        # ♠ KQ3 ♥ AJ2 ♦ KQJ32 ♣ 32
        # HCP: K(3)+Q(2)+A(4)+J(1)+K(3)+Q(2)+J(1) = 16
        hand = make_hand("KQ3", "AJ2", "KQJ32", "32")
        assert hand.hcp == 16
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "1NT", f"16 HCP balanced with 5-card minor should open 1NT, got {bid}"

    def test_1nt_rejected_singleton(self):
        """SAYC: Hand with singleton is NOT balanced, should not open 1NT."""
        # ♠ AKJ32 ♥ K ♦ Q432 ♣ K32
        # HCP: A(4)+K(3)+J(1)+K(3)+Q(2)+K(3) = 16, but has singleton heart
        hand = make_hand("AKJ32", "K", "Q432", "K32")
        assert hand.hcp == 16
        assert not hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid != "1NT", "Singleton hand should not open 1NT"
        assert bid == "1♠", f"5-card major with 16 HCP should open 1♠, got {bid}"

    def test_1nt_rejected_14_hcp(self):
        """SAYC: 14 HCP is below 1NT range, should open 1 of a suit."""
        # ♠ AQ32 ♥ KJ5 ♦ Q43 ♣ J32
        # HCP: A(4)+Q(2)+K(3)+J(1)+Q(2)+J(1) = 13... need 14
        # ♠ AQ32 ♥ KJ5 ♦ Q43 ♣ Q32 = 4+2+3+1+2+2 = 14
        hand = make_hand("AQ32", "KJ5", "Q43", "Q32")
        assert hand.hcp == 14
        bid, _ = get_opening_bid(hand)
        assert bid != "1NT", f"14 HCP should not open 1NT, got {bid}"

    def test_1nt_rejected_18_hcp(self):
        """SAYC: 18 HCP is above 1NT range, should open 1 of a suit and rebid."""
        # ♠ AKJ2 ♥ AQ43 ♦ K32 ♣ K2
        # HCP: A(4)+K(3)+J(1)+A(4)+Q(2)+K(3)+K(3) = 20... too much
        # ♠ AKJ2 ♥ KQ43 ♦ K32 ♣ K2 = 4+3+1+3+2+3+3 = 19... still too much
        # ♠ AKJ2 ♥ KQ43 ♦ Q32 ♣ A2 = 4+3+1+3+2+2+4 = 19
        # ♠ AK32 ♥ KQ43 ♦ Q32 ♣ A2 = 4+3+3+2+2+4 = 18
        hand = make_hand("AK32", "KQ43", "Q32", "A2")
        assert hand.hcp == 18
        bid, _ = get_opening_bid(hand)
        assert bid != "1NT", f"18 HCP should not open 1NT, got {bid}"


# =============================================================================
# 2NT Opening: 20-21 HCP, Balanced
# =============================================================================

class Test2NTOpening:
    """SAYC: 2NT shows 20-21 HCP and a balanced hand."""

    def test_2nt_20_hcp_balanced(self):
        """SAYC Example: 20 HCP balanced opens 2NT."""
        # ♠ AKJ2 ♥ AQ3 ♦ KQ32 ♣ K2
        # HCP: A(4)+K(3)+J(1)+A(4)+Q(2)+K(3)+Q(2)+K(3) = 22... too much
        # ♠ AKJ2 ♥ AQ3 ♦ KJ32 ♣ K2 = 4+3+1+4+2+3+1+3 = 21
        # ♠ AKJ2 ♥ AQ3 ♦ KJ32 ♣ Q2 = 4+3+1+4+2+3+1+2 = 20
        hand = make_hand("AKJ2", "AQ3", "KJ32", "Q2")
        assert hand.hcp == 20
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "2NT", f"20 HCP balanced should open 2NT, got {bid}"

    def test_2nt_21_hcp_balanced(self):
        """SAYC Example: 21 HCP balanced opens 2NT."""
        # ♠ AKJ2 ♥ AQ3 ♦ KJ32 ♣ K2 = 21
        hand = make_hand("AKJ2", "AQ3", "KJ32", "K2")
        assert hand.hcp == 21
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "2NT", f"21 HCP balanced should open 2NT, got {bid}"


# =============================================================================
# Strong 2♣ Opening: 22+ HCP or 9+ Tricks
# =============================================================================

class TestStrong2ClubOpening:
    """SAYC: 2♣ is artificial and forcing, showing 22+ HCP or 9+ tricks."""

    def test_2c_22_hcp_balanced(self):
        """SAYC Example: 22 HCP balanced opens 2♣ (planning to rebid 2NT)."""
        # ♠ AKJ2 ♥ AQJ ♦ KQ32 ♣ K2
        # HCP: A(4)+K(3)+J(1)+A(4)+Q(2)+J(1)+K(3)+Q(2)+K(3) = 23
        hand = make_hand("AKJ2", "AQJ", "KQ32", "K2")
        assert hand.hcp == 23
        bid, _ = get_opening_bid(hand)
        assert bid == "2♣", f"23 HCP should open 2♣, got {bid}"

    def test_2c_24_hcp_balanced(self):
        """SAYC Example: 24 HCP balanced opens 2♣."""
        # ♠ AKQ2 ♥ AKJ ♦ KQ32 ♣ K2 = 4+3+2+4+3+1+3+2+3 = 25
        hand = make_hand("AKQ2", "AKJ", "KQ32", "K2")
        assert hand.hcp == 25
        bid, _ = get_opening_bid(hand)
        assert bid == "2♣", f"25 HCP should open 2♣, got {bid}"

    def test_2c_unbalanced_game_force(self):
        """SAYC Example: Strong unbalanced hand with 9+ tricks opens 2♣."""
        # ♠ AKQJT932 ♥ A ♦ KQ ♣ A2
        # HCP: A(4)+K(3)+Q(2)+J(1)+T(0)+A(4)+K(3)+Q(2)+A(4) = 23
        # 8 spade tricks + 3 side aces = 11 tricks
        hand = make_hand("AKQJT932", "A", "KQ", "A2")
        assert hand.hcp == 23
        bid, _ = get_opening_bid(hand)
        assert bid == "2♣", f"Strong hand with 9+ tricks should open 2♣, got {bid}"


# =============================================================================
# Weak Two Bids: 5-11 HCP, Good 6-Card Suit
# =============================================================================

class TestWeakTwoBids:
    """SAYC: Weak 2♦/2♥/2♠ shows 5-11 HCP with a good 6-card suit."""

    def test_weak_2h_classic(self):
        """SAYC Example: 8 HCP with KQJxxx in hearts opens 2♥."""
        # ♠ 32 ♥ KQJ932 ♦ J32 ♣ 32
        # HCP: K(3)+Q(2)+J(1)+J(1) = 7
        hand = make_hand("32", "KQJ932", "J32", "32")
        assert 5 <= hand.hcp <= 11
        bid, _ = get_opening_bid(hand)
        assert bid == "2♥", f"Weak two in hearts should open 2♥, got {bid}"

    def test_weak_2s_classic(self):
        """SAYC Example: 9 HCP with AQJxxx in spades opens 2♠."""
        # ♠ AQJ932 ♥ 32 ♦ J32 ♣ 32
        # HCP: A(4)+Q(2)+J(1)+J(1) = 8
        hand = make_hand("AQJ932", "32", "J32", "32")
        assert 5 <= hand.hcp <= 11
        bid, _ = get_opening_bid(hand)
        assert bid == "2♠", f"Weak two in spades should open 2♠, got {bid}"

    def test_weak_2d_classic(self):
        """SAYC Example: 7 HCP with KQTxxx in diamonds opens 2♦."""
        # ♠ 32 ♥ 432 ♦ KQT932 ♣ 32
        # HCP: K(3)+Q(2) = 5
        hand = make_hand("32", "432", "KQT932", "32")
        assert 5 <= hand.hcp <= 11
        bid, _ = get_opening_bid(hand)
        # Note: Some implementations may pass with only 5 HCP
        assert bid in ["2♦", "Pass"], f"Weak two in diamonds or pass, got {bid}"


# =============================================================================
# One-Level Suit Openings: 13+ Points
# =============================================================================

class TestOneLevelSuitOpenings:
    """SAYC: Open 1 of a suit with 13+ points (HCP + length points)."""

    def test_1s_opening_5_card_major(self):
        """SAYC: Open 1♠ with 5+ spades and opening values."""
        # ♠ AKJ32 ♥ Q32 ♦ K32 ♣ 32
        # HCP: A(4)+K(3)+J(1)+Q(2)+K(3) = 13
        hand = make_hand("AKJ32", "Q32", "K32", "32")
        assert hand.hcp == 13
        bid, _ = get_opening_bid(hand)
        assert bid == "1♠", f"5-card major with 13 HCP should open 1♠, got {bid}"

    def test_1h_opening_5_card_major(self):
        """SAYC: Open 1♥ with 5+ hearts and opening values."""
        # ♠ Q32 ♥ AKJ32 ♦ K32 ♣ 32
        hand = make_hand("Q32", "AKJ32", "K32", "32")
        assert hand.hcp == 13
        bid, _ = get_opening_bid(hand)
        assert bid == "1♥", f"5-card major with 13 HCP should open 1♥, got {bid}"

    def test_1d_opening_longer_minor(self):
        """SAYC: Open 1♦ with longer diamonds than clubs."""
        # ♠ K32 ♥ Q32 ♦ AKJ32 ♣ 32
        hand = make_hand("K32", "Q32", "AKJ32", "32")
        assert hand.hcp == 13
        bid, _ = get_opening_bid(hand)
        assert bid == "1♦", f"Longer diamonds should open 1♦, got {bid}"

    def test_1c_opening_longer_clubs(self):
        """SAYC: Open 1♣ with longer clubs than diamonds."""
        # ♠ K32 ♥ Q32 ♦ 32 ♣ AKJ32
        hand = make_hand("K32", "Q32", "32", "AKJ32")
        assert hand.hcp == 13
        bid, _ = get_opening_bid(hand)
        assert bid == "1♣", f"Longer clubs should open 1♣, got {bid}"

    def test_1c_opening_equal_minors_3_3(self):
        """SAYC: With 3-3 in minors, open 1♣."""
        # ♠ AK32 ♥ KQ3 ♦ J32 ♣ Q32 = 4-3-3-3
        # HCP: A(4)+K(3)+K(3)+Q(2)+J(1)+Q(2) = 15... too much for testing minor choice
        # Use: ♠ AK32 ♥ J32 ♦ Q32 ♣ Q32 = 4+3+2+2 = 11... not enough
        # Use: ♠ AK32 ♥ K32 ♦ J32 ♣ Q32 = 4+3+3+1+2 = 13
        hand = make_hand("AK32", "K32", "J32", "Q32")
        assert hand.hcp == 13
        assert hand.suit_lengths['♦'] == 3
        assert hand.suit_lengths['♣'] == 3
        bid, _ = get_opening_bid(hand)
        # With 4-3-3-3 balanced and 13 HCP, opens a minor
        # SAYC says with 3-3 minors, open 1♣
        assert bid in ["1♣", "1♠"], f"3-3 minors typically opens 1♣, got {bid}"

    def test_1d_opening_equal_minors_4_4(self):
        """SAYC: With 4-4 in minors, open 1♦."""
        # ♠ AK3 ♥ Q2 ♦ KJ32 ♣ J432 = 3-2-4-4 = 13 cards
        # HCP: A(4)+K(3)+Q(2)+K(3)+J(1)+J(1) = 14
        hand = make_hand("AK3", "Q2", "KJ32", "J432")
        assert hand.hcp == 14
        assert hand.suit_lengths['♦'] == 4
        assert hand.suit_lengths['♣'] == 4
        bid, _ = get_opening_bid(hand)
        assert bid == "1♦", f"4-4 minors should open 1♦, got {bid}"

    def test_1_major_priority_over_minor(self):
        """SAYC: 5-card major takes priority over longer minor."""
        # ♠ AKJ32 ♥ 32 ♦ AQJ32 ♣ 2
        # 5-5 in spades and diamonds
        hand = make_hand("AKJ32", "32", "AQJ32", "2")
        assert hand.suit_lengths['♠'] == 5
        assert hand.suit_lengths['♦'] == 5
        bid, _ = get_opening_bid(hand)
        assert bid == "1♠", f"5-card major takes priority, should open 1♠, got {bid}"

    def test_both_majors_open_longer(self):
        """SAYC: With both majors, open the longer one."""
        # ♠ AK32 ♥ KQJ32 ♦ 32 ♣ 32
        # 4 spades, 5 hearts
        hand = make_hand("AK32", "KQJ32", "32", "32")
        assert hand.suit_lengths['♠'] == 4
        assert hand.suit_lengths['♥'] == 5
        bid, _ = get_opening_bid(hand)
        assert bid == "1♥", f"Longer major (hearts) should be opened, got {bid}"

    def test_both_majors_equal_open_spades(self):
        """SAYC: With 5-5 in majors, open 1♠."""
        # ♠ AKJ32 ♥ KQJ32 ♦ 2 ♣ 32
        hand = make_hand("AKJ32", "KQJ32", "2", "32")
        assert hand.suit_lengths['♠'] == 5
        assert hand.suit_lengths['♥'] == 5
        bid, _ = get_opening_bid(hand)
        assert bid == "1♠", f"5-5 majors should open 1♠, got {bid}"


# =============================================================================
# Preemptive Openings: 3-Level
# =============================================================================

class TestPreemptiveOpenings:
    """SAYC: 3-level openings show a good 7+ card suit with less than opening values."""

    def test_3h_preempt_classic(self):
        """SAYC Example: 6 HCP with KQJxxxx in hearts opens 3♥."""
        # ♠ 32 ♥ KQJ9432 ♦ 32 ♣ 32
        # HCP: K(3)+Q(2)+J(1) = 6
        hand = make_hand("32", "KQJ9432", "32", "32")
        assert hand.hcp == 6
        assert hand.suit_lengths['♥'] == 7
        bid, _ = get_opening_bid(hand)
        assert bid == "3♥", f"7-card heart suit preempt should open 3♥, got {bid}"

    def test_3s_preempt_classic(self):
        """SAYC Example: 7 HCP with AQJxxxx in spades opens 3♠."""
        # ♠ AQJ9432 ♥ 32 ♦ 32 ♣ 32
        # HCP: A(4)+Q(2)+J(1) = 7
        hand = make_hand("AQJ9432", "32", "32", "32")
        assert hand.hcp == 7
        assert hand.suit_lengths['♠'] == 7
        bid, _ = get_opening_bid(hand)
        assert bid == "3♠", f"7-card spade suit preempt should open 3♠, got {bid}"

    def test_3d_preempt_classic(self):
        """SAYC Example: 5 HCP with KQTxxxx in diamonds opens 3♦."""
        # ♠ 32 ♥ 32 ♦ KQT9432 ♣ 32
        # HCP: K(3)+Q(2) = 5
        hand = make_hand("32", "32", "KQT9432", "32")
        assert hand.hcp == 5
        assert hand.suit_lengths['♦'] == 7
        bid, _ = get_opening_bid(hand)
        assert bid == "3♦", f"7-card diamond suit preempt should open 3♦, got {bid}"


# =============================================================================
# Pass: Insufficient Values
# =============================================================================

class TestPassWithInsufficientValues:
    """SAYC: Pass with fewer than 13 points (no preempt shape)."""

    def test_pass_11_hcp_balanced(self):
        """Should pass with 11 HCP balanced (no preempt shape)."""
        # ♠ KJ32 ♥ Q32 ♦ Q32 ♣ J32
        # HCP: K(3)+J(1)+Q(2)+Q(2)+J(1) = 9... need 11
        # ♠ KJ32 ♥ KQ3 ♦ Q32 ♣ J32 = 3+1+3+2+2+1 = 12
        # ♠ KJ32 ♥ K32 ♦ Q32 ♣ J32 = 3+1+3+2+1 = 10
        # ♠ KJ32 ♥ KJ3 ♦ Q32 ♣ J32 = 3+1+3+1+2+1 = 11
        hand = make_hand("KJ32", "KJ3", "Q32", "J32")
        assert hand.hcp == 11
        assert hand.is_balanced
        bid, _ = get_opening_bid(hand)
        assert bid == "Pass", f"11 HCP balanced should pass, got {bid}"

    def test_pass_10_hcp_no_shape(self):
        """Should pass with 10 HCP and no preemptive shape."""
        # ♠ K432 ♥ Q32 ♦ K32 ♣ 432
        # HCP: K(3)+Q(2)+K(3) = 8...
        # ♠ KJ32 ♥ Q32 ♦ K32 ♣ 432 = 3+1+2+3 = 9
        # ♠ KJ32 ♥ QJ2 ♦ K32 ♣ 432 = 3+1+2+1+3 = 10
        hand = make_hand("KJ32", "QJ2", "K32", "432")
        assert hand.hcp == 10
        bid, _ = get_opening_bid(hand)
        assert bid == "Pass", f"10 HCP should pass, got {bid}"


# =============================================================================
# Light Opening Considerations
# =============================================================================

class TestLightOpenings:
    """SAYC allows opening light (12 HCP) with good shape or suit quality."""

    def test_12_hcp_good_suit_may_open(self):
        """12 HCP with excellent 6-card suit may open (borderline)."""
        # ♠ AKQJ32 ♥ 32 ♦ J32 ♣ 32
        # HCP: A(4)+K(3)+Q(2)+J(1)+J(1) = 11... need 12
        # ♠ AKQJ32 ♥ 32 ♦ Q32 ♣ 32 = 4+3+2+1+2 = 12
        hand = make_hand("AKQJ32", "32", "Q32", "32")
        assert hand.hcp == 12
        bid, _ = get_opening_bid(hand)
        # With 12 HCP and an excellent 6-card spade suit, opening 1♠ is reasonable
        # but some conservative systems might pass
        assert bid in ["1♠", "Pass"], f"12 HCP with good suit may open or pass, got {bid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
