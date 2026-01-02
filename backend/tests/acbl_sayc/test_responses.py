"""
ACBL SAYC Test Suite: Responses to Opening Bids

Reference: ACBL SAYC Booklet - "Responding to Opening Bids" section

Response requirements from SAYC:
- Raises of major: 3+ card support
  - Single raise (1♥→2♥): 6-10 points
  - Limit raise (1♥→3♥): 10-12 points
  - Jump to game (1♥→4♥): 5+ support, weak hand (preemptive)
- New suit at 1-level: 6+ points, 4+ cards
- New suit at 2-level: 10+ points, 4+ cards (some exceptions)
- 1NT response: 6-10 points, no major fit, no 4-card major to bid
- 2NT response: 13-15 points, balanced, game forcing
- 3NT response: 16-18 points, balanced
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
            cards.append(Card(rank, suit))

    if len(cards) != 13:
        raise ValueError(f"Hand must have 13 cards, got {len(cards)}: ♠{spades} ♥{hearts} ♦{diamonds} ♣{clubs}")

    return Hand(cards)


def get_response(hand: Hand, opening_bid: str, vulnerability: str = "None") -> tuple:
    """Get the response to partner's opening bid."""
    engine = BiddingEngine()
    # Partner (North) opened, opponent (East) passed, we (South) respond
    return engine.get_next_bid(
        hand=hand,
        auction_history=[opening_bid, "Pass"],
        my_position="South",
        vulnerability=vulnerability,
        dealer="North"
    )


# =============================================================================
# Responses to 1♥ Opening
# =============================================================================

class TestResponsesToOneHeart:
    """SAYC: Responses to partner's 1♥ opening."""

    def test_2h_simple_raise_minimum(self):
        """SAYC: Raise to 2♥ with 3+ support and 6-10 points."""
        # ♠ 432 ♥ K32 ♦ Q432 ♣ 432
        # HCP: K(3)+Q(2) = 5 + 1 for doubleton = 6 pts
        # Actually we need at least 6 HCP for this to be clear
        # ♠ 432 ♥ KJ2 ♦ Q432 ♣ 432 = 3+1+2 = 6
        hand = make_hand("432", "KJ2", "Q432", "432")
        assert hand.hcp == 6
        assert hand.suit_lengths['♥'] >= 3
        bid, _ = get_response(hand, "1♥")
        assert bid == "2♥", f"6 HCP with 3-card support should raise to 2♥, got {bid}"

    def test_2h_simple_raise_maximum(self):
        """SAYC: Raise to 2♥ with 3+ support and up to 10 points."""
        # ♠ K32 ♥ Q32 ♦ KJ32 ♣ 432
        # HCP: K(3)+Q(2)+K(3)+J(1) = 9
        hand = make_hand("K32", "Q32", "KJ32", "432")
        assert hand.hcp == 9
        assert hand.suit_lengths['♥'] >= 3
        bid, _ = get_response(hand, "1♥")
        assert bid == "2♥", f"9 HCP with 3-card support should raise to 2♥, got {bid}"

    def test_3h_limit_raise(self):
        """SAYC: Raise to 3♥ (limit raise) with 4+ support and 10-12 points."""
        # ♠ K2 ♥ KJ32 ♦ Q432 ♣ 432
        # HCP: K(3)+K(3)+J(1)+Q(2) = 9... need 10+
        # ♠ K32 ♥ KJ32 ♦ Q432 ♣ 42 = 3+3+1+2 = 9... + 1 for doubleton = 10
        # Let's use: ♠ K2 ♥ KQ32 ♦ Q432 ♣ 432 = 3+3+2+2 = 10
        hand = make_hand("K2", "KQ32", "Q432", "432")
        assert hand.hcp == 10
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_response(hand, "1♥")
        assert bid == "3♥", f"10 HCP with 4-card support should limit raise to 3♥, got {bid}"

    def test_1s_new_suit_at_one_level(self):
        """SAYC: Bid 1♠ with 4+ spades and 6+ points (new suit at 1-level)."""
        # ♠ KJ32 ♥ 32 ♦ Q432 ♣ 432
        # HCP: K(3)+J(1)+Q(2) = 6
        hand = make_hand("KJ32", "32", "Q432", "432")
        assert hand.hcp == 6
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_response(hand, "1♥")
        assert bid == "1♠", f"6 HCP with 4 spades should respond 1♠, got {bid}"

    def test_1nt_no_major_fit_no_spades(self):
        """SAYC: Bid 1NT with 6-10 points, no heart support, no 4-card spade suit."""
        # ♠ K32 ♥ 32 ♦ Q432 ♣ K432
        # HCP: K(3)+Q(2)+K(3) = 8
        hand = make_hand("K32", "32", "Q432", "K432")
        assert hand.hcp == 8
        assert hand.suit_lengths['♥'] < 3
        assert hand.suit_lengths['♠'] < 4
        bid, _ = get_response(hand, "1♥")
        assert bid == "1NT", f"8 HCP without major fit should respond 1NT, got {bid}"

    def test_2c_new_suit_at_two_level(self):
        """SAYC: Bid 2♣ with 10+ points and 4+ clubs."""
        # ♠ K32 ♥ 32 ♦ Q32 ♣ AJ432
        # HCP: K(3)+Q(2)+A(4)+J(1) = 10
        hand = make_hand("K32", "32", "Q32", "AJ432")
        assert hand.hcp == 10
        assert hand.suit_lengths['♣'] >= 4
        bid, _ = get_response(hand, "1♥")
        assert bid == "2♣", f"10 HCP with 5 clubs should respond 2♣, got {bid}"

    def test_2d_new_suit_at_two_level(self):
        """SAYC: Bid 2♦ with 10+ points and 4+ diamonds."""
        # ♠ K32 ♥ 32 ♦ AJ432 ♣ Q32
        # HCP: K(3)+A(4)+J(1)+Q(2) = 10
        hand = make_hand("K32", "32", "AJ432", "Q32")
        assert hand.hcp == 10
        assert hand.suit_lengths['♦'] >= 4
        bid, _ = get_response(hand, "1♥")
        assert bid == "2♦", f"10 HCP with 5 diamonds should respond 2♦, got {bid}"


# =============================================================================
# Responses to 1♠ Opening
# =============================================================================

class TestResponsesToOneSpade:
    """SAYC: Responses to partner's 1♠ opening."""

    def test_2s_simple_raise(self):
        """SAYC: Raise to 2♠ with 3+ support and 6-10 points."""
        # ♠ Q32 ♥ K432 ♦ J32 ♣ 432
        # HCP: Q(2)+K(3)+J(1) = 6
        hand = make_hand("Q32", "K432", "J32", "432")
        assert hand.hcp == 6
        assert hand.suit_lengths['♠'] >= 3
        bid, _ = get_response(hand, "1♠")
        assert bid == "2♠", f"6 HCP with 3-card support should raise to 2♠, got {bid}"

    def test_3s_limit_raise(self):
        """SAYC: Limit raise to 3♠ with 4+ support and 10-12 points."""
        # ♠ KQ32 ♥ K32 ♦ J432 ♣ 32
        # HCP: K(3)+Q(2)+K(3)+J(1) = 9... + 1 for doubleton = 10
        hand = make_hand("KQ32", "K32", "J432", "32")
        assert hand.hcp == 9
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_response(hand, "1♠")
        assert bid == "3♠", f"9 HCP + distribution with 4-card support should limit raise, got {bid}"

    def test_1nt_no_spade_fit(self):
        """SAYC: Bid 1NT with 6-10 points and no spade support."""
        # ♠ 32 ♥ K432 ♦ Q432 ♣ K32
        # HCP: K(3)+Q(2)+K(3) = 8
        hand = make_hand("32", "K432", "Q432", "K32")
        assert hand.hcp == 8
        assert hand.suit_lengths['♠'] < 3
        bid, _ = get_response(hand, "1♠")
        assert bid == "1NT", f"8 HCP without spade fit should respond 1NT, got {bid}"

    def test_2h_new_suit_shows_5_plus(self):
        """SAYC: 2♥ over 1♠ typically shows 5+ hearts (new suit at 2-level)."""
        # ♠ 32 ♥ AJ432 ♦ K32 ♣ Q32
        # HCP: A(4)+J(1)+K(3)+Q(2) = 10
        hand = make_hand("32", "AJ432", "K32", "Q32")
        assert hand.hcp == 10
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_response(hand, "1♠")
        assert bid == "2♥", f"10 HCP with 5 hearts should respond 2♥, got {bid}"


# =============================================================================
# Responses to 1♣ Opening
# =============================================================================

class TestResponsesToOneClub:
    """SAYC: Responses to partner's 1♣ opening."""

    def test_1d_new_suit_at_one_level(self):
        """SAYC: Bid 1♦ with 4+ diamonds and 6+ points."""
        # ♠ K32 ♥ 432 ♦ QJ32 ♣ 432
        # HCP: K(3)+Q(2)+J(1) = 6
        hand = make_hand("K32", "432", "QJ32", "432")
        assert hand.hcp == 6
        assert hand.suit_lengths['♦'] >= 4
        bid, _ = get_response(hand, "1♣")
        assert bid == "1♦", f"6 HCP with 4 diamonds should respond 1♦, got {bid}"

    def test_1h_4_card_major(self):
        """SAYC: Bid 1♥ with 4+ hearts and 6+ points (up the line)."""
        # ♠ 432 ♥ KJ32 ♦ Q32 ♣ 432
        # HCP: K(3)+J(1)+Q(2) = 6
        hand = make_hand("432", "KJ32", "Q32", "432")
        assert hand.hcp == 6
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_response(hand, "1♣")
        assert bid == "1♥", f"6 HCP with 4 hearts should respond 1♥, got {bid}"

    def test_1s_4_card_major(self):
        """SAYC: Bid 1♠ with 4+ spades and 6+ points."""
        # ♠ KJ32 ♥ 432 ♦ Q32 ♣ 432
        # HCP: K(3)+J(1)+Q(2) = 6
        hand = make_hand("KJ32", "432", "Q32", "432")
        assert hand.hcp == 6
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_response(hand, "1♣")
        assert bid == "1♠", f"6 HCP with 4 spades should respond 1♠, got {bid}"

    def test_1h_over_1s_both_majors_up_line(self):
        """SAYC: With both 4-card majors, bid 1♥ first (up the line)."""
        # ♠ KJ32 ♥ QJ32 ♦ 32 ♣ 432
        # HCP: K(3)+J(1)+Q(2)+J(1) = 7
        hand = make_hand("KJ32", "QJ32", "32", "432")
        assert hand.hcp == 7
        assert hand.suit_lengths['♥'] >= 4
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_response(hand, "1♣")
        assert bid == "1♥", f"With 4-4 majors should bid 1♥ first (up the line), got {bid}"

    def test_2c_raise_with_support(self):
        """SAYC: Raise to 2♣ with 5+ support and 6-10 points."""
        # ♠ K32 ♥ 32 ♦ 432 ♣ QJ432
        # HCP: K(3)+Q(2)+J(1) = 6
        hand = make_hand("K32", "32", "432", "QJ432")
        assert hand.hcp == 6
        assert hand.suit_lengths['♣'] >= 5
        bid, _ = get_response(hand, "1♣")
        # With 5-card club support and no 4-card major, raising is appropriate
        # But we should check for majors first - no 4-card major here
        assert bid in ["2♣", "1NT"], f"6 HCP with 5 clubs, no major should raise clubs or bid 1NT, got {bid}"


# =============================================================================
# Responses to 1♦ Opening
# =============================================================================

class TestResponsesToOneDiamond:
    """SAYC: Responses to partner's 1♦ opening."""

    def test_1h_4_card_major(self):
        """SAYC: Bid 1♥ with 4+ hearts and 6+ points."""
        # ♠ 432 ♥ KJ32 ♦ Q32 ♣ 432
        hand = make_hand("432", "KJ32", "Q32", "432")
        assert hand.hcp == 6
        bid, _ = get_response(hand, "1♦")
        assert bid == "1♥", f"6 HCP with 4 hearts should respond 1♥, got {bid}"

    def test_1s_4_card_major(self):
        """SAYC: Bid 1♠ with 4+ spades and 6+ points."""
        # ♠ KJ32 ♥ 432 ♦ Q32 ♣ 432
        hand = make_hand("KJ32", "432", "Q32", "432")
        assert hand.hcp == 6
        bid, _ = get_response(hand, "1♦")
        assert bid == "1♠", f"6 HCP with 4 spades should respond 1♠, got {bid}"

    def test_2d_raise_with_support(self):
        """SAYC: Raise to 2♦ with 4+ support and 6-10 points when no major."""
        # ♠ 432 ♥ 32 ♦ KJ432 ♣ K32
        # HCP: K(3)+J(1)+K(3) = 7
        hand = make_hand("432", "32", "KJ432", "K32")
        assert hand.hcp == 7
        assert hand.suit_lengths['♦'] >= 4
        bid, _ = get_response(hand, "1♦")
        # Without a 4-card major, raising diamonds is appropriate
        assert bid in ["2♦", "1NT"], f"7 HCP with 5 diamonds, no major should raise or bid 1NT, got {bid}"


# =============================================================================
# Responses to 1NT Opening
# =============================================================================

class TestResponsesToOneNotrump:
    """SAYC: Responses to partner's 1NT (15-17 HCP) opening."""

    def test_pass_weak_balanced(self):
        """SAYC: Pass with 0-7 points and no 5+ card major."""
        # ♠ 432 ♥ 432 ♦ J432 ♣ 432
        # HCP: J(1) = 1
        hand = make_hand("432", "432", "J432", "432")
        assert hand.hcp <= 7
        bid, _ = get_response(hand, "1NT")
        assert bid == "Pass", f"Weak balanced hand should pass 1NT, got {bid}"

    def test_2c_stayman(self):
        """SAYC: Bid 2♣ (Stayman) with 8+ points and a 4-card major."""
        # ♠ KJ32 ♥ Q32 ♦ K32 ♣ 432
        # HCP: K(3)+J(1)+Q(2)+K(3) = 9
        hand = make_hand("KJ32", "Q32", "K32", "432")
        assert hand.hcp >= 8
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_response(hand, "1NT")
        assert bid == "2♣", f"9 HCP with 4 spades should bid Stayman 2♣, got {bid}"

    def test_2d_jacoby_transfer_hearts(self):
        """SAYC: Bid 2♦ (Jacoby transfer) with 5+ hearts."""
        # ♠ 432 ♥ KJ432 ♦ K32 ♣ 32
        # HCP: K(3)+J(1)+K(3) = 7
        hand = make_hand("432", "KJ432", "K32", "32")
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_response(hand, "1NT")
        assert bid == "2♦", f"5-card heart suit should transfer with 2♦, got {bid}"

    def test_2h_jacoby_transfer_spades(self):
        """SAYC: Bid 2♥ (Jacoby transfer) with 5+ spades."""
        # ♠ KJ432 ♥ 432 ♦ K32 ♣ 32
        # HCP: K(3)+J(1)+K(3) = 7
        hand = make_hand("KJ432", "432", "K32", "32")
        assert hand.suit_lengths['♠'] >= 5
        bid, _ = get_response(hand, "1NT")
        assert bid == "2♥", f"5-card spade suit should transfer with 2♥, got {bid}"

    def test_3nt_game_values(self):
        """SAYC: Bid 3NT directly with 10-15 HCP balanced, no 4-card major."""
        # ♠ K32 ♥ Q32 ♦ AJ32 ♣ K32
        # HCP: K(3)+Q(2)+A(4)+J(1)+K(3) = 13
        hand = make_hand("K32", "Q32", "AJ32", "K32")
        assert 10 <= hand.hcp <= 15
        assert hand.suit_lengths['♠'] < 4
        assert hand.suit_lengths['♥'] < 4
        bid, _ = get_response(hand, "1NT")
        assert bid == "3NT", f"13 HCP balanced without 4-card major should bid 3NT, got {bid}"

    def test_2nt_invitational(self):
        """SAYC: Bid 2NT with 8-9 HCP balanced, inviting game."""
        # ♠ K32 ♥ Q32 ♦ J32 ♣ K432
        # HCP: K(3)+Q(2)+J(1)+K(3) = 9
        hand = make_hand("K32", "Q32", "J32", "K432")
        assert 8 <= hand.hcp <= 9
        bid, _ = get_response(hand, "1NT")
        # Could be 2NT invite or Stayman if 4-card major
        assert bid in ["2NT", "2♣"], f"8-9 HCP balanced should invite with 2NT or use Stayman, got {bid}"


# =============================================================================
# Responses to 2♣ Opening (Strong, Artificial)
# =============================================================================

class TestResponsesToTwoClubs:
    """SAYC: Responses to partner's strong 2♣ opening."""

    def test_2d_waiting_weak(self):
        """SAYC: 2♦ is waiting/negative with 0-7 HCP."""
        # ♠ 432 ♥ 432 ♦ J432 ♣ 432
        # HCP: J(1) = 1
        hand = make_hand("432", "432", "J432", "432")
        assert hand.hcp < 8
        bid, _ = get_response(hand, "2♣")
        assert bid == "2♦", f"Weak hand should bid 2♦ waiting, got {bid}"

    def test_2h_positive_response(self):
        """SAYC: 2♥/2♠ is positive with 8+ HCP and good 5+ card suit."""
        # ♠ 32 ♥ AKJ32 ♦ 432 ♣ 432
        # HCP: A(4)+K(3)+J(1) = 8
        hand = make_hand("32", "AKJ32", "432", "432")
        assert hand.hcp >= 8
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_response(hand, "2♣")
        assert bid == "2♥", f"8+ HCP with good 5-card heart suit should bid 2♥, got {bid}"

    def test_2nt_positive_balanced(self):
        """SAYC: 2NT shows 8+ HCP balanced without a good 5-card suit."""
        # ♠ KQ32 ♥ Q32 ♦ K32 ♣ 432
        # HCP: K(3)+Q(2)+Q(2)+K(3) = 10
        hand = make_hand("KQ32", "Q32", "K32", "432")
        assert hand.hcp >= 8
        assert hand.is_balanced
        bid, _ = get_response(hand, "2♣")
        assert bid == "2NT", f"10 HCP balanced should bid 2NT positive, got {bid}"


# =============================================================================
# Responses to Weak Two Bids
# =============================================================================

class TestResponsesToWeakTwo:
    """SAYC: Responses to partner's weak two bid."""

    def test_pass_weak_no_fit(self):
        """SAYC: Pass with weak hand and no fit."""
        # Partner opens 2♥
        # ♠ K432 ♥ 2 ♦ Q432 ♣ J432
        # HCP: K(3)+Q(2)+J(1) = 6
        hand = make_hand("K432", "2", "Q432", "J432")
        assert hand.hcp < 10
        assert hand.suit_lengths['♥'] < 3
        bid, _ = get_response(hand, "2♥")
        assert bid == "Pass", f"Weak hand without fit should pass weak two, got {bid}"

    def test_raise_with_fit(self):
        """SAYC: Raise to 3♥ with 3+ card support (preemptive)."""
        # ♠ K432 ♥ 432 ♦ Q432 ♣ 32
        # HCP: K(3)+Q(2) = 5, but we have a fit
        hand = make_hand("K432", "432", "Q432", "32")
        assert hand.suit_lengths['♥'] >= 3
        bid, _ = get_response(hand, "2♥")
        # With 3-card support, raising is appropriate (preemptive)
        assert bid in ["3♥", "Pass"], f"With 3-card support, should raise or pass, got {bid}"

    def test_raise_to_game_with_values(self):
        """SAYC: Raise to 4♥ with good support and values."""
        # ♠ A2 ♥ KJ32 ♦ A432 ♣ 432
        # HCP: A(4)+K(3)+J(1)+A(4) = 12
        hand = make_hand("A2", "KJ32", "A432", "432")
        assert hand.hcp >= 12
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_response(hand, "2♥")
        assert bid == "4♥", f"12 HCP with 4-card support should raise to game, got {bid}"

    def test_2nt_asking(self):
        """SAYC: 2NT is a feature ask (artificial) with game interest."""
        # ♠ AK32 ♥ K2 ♦ AQ32 ♣ 432
        # HCP: A(4)+K(3)+K(3)+A(4)+Q(2) = 16
        hand = make_hand("AK32", "K2", "AQ32", "432")
        assert hand.hcp >= 15
        bid, _ = get_response(hand, "2♥")
        # With 16 HCP and game interest, 2NT ask is appropriate
        # or direct 4♥ with support
        assert bid in ["2NT", "4♥"], f"Strong hand should ask or bid game, got {bid}"


# =============================================================================
# Pass with Insufficient Values
# =============================================================================

class TestPassOnResponses:
    """SAYC: Pass with insufficient values to respond."""

    def test_pass_under_6_hcp(self):
        """SAYC: Pass with fewer than 6 HCP."""
        # ♠ J32 ♥ 432 ♦ J432 ♣ 432
        # HCP: J(1)+J(1) = 2
        hand = make_hand("J32", "432", "J432", "432")
        assert hand.hcp < 6
        bid, _ = get_response(hand, "1♥")
        assert bid == "Pass", f"Under 6 HCP should pass, got {bid}"

    def test_pass_5_hcp_no_fit(self):
        """SAYC: Pass with 5 HCP and no fit."""
        # ♠ K32 ♥ 32 ♦ Q432 ♣ 5432
        # HCP: K(3)+Q(2) = 5
        hand = make_hand("K32", "32", "Q432", "5432")
        assert hand.hcp == 5
        bid, _ = get_response(hand, "1♥")
        assert bid == "Pass", f"5 HCP should pass, got {bid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
