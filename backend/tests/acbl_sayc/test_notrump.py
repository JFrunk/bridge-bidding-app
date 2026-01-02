"""
ACBL SAYC Test Suite: Notrump Bidding

Reference: ACBL SAYC Booklet - "Notrump Openings and Responses" section

SAYC Notrump ranges:
- 1NT: 15-17 HCP, balanced
- 2NT: 20-21 HCP, balanced
- 3NT: Not a standard opening (use 2♣ then 3NT)
- After 2♣: 22-24 balanced rebids 2NT

Conventions over 1NT:
- Stayman (2♣): Asks for 4-card major
- Jacoby Transfers (2♦/2♥): Shows 5+ hearts/spades
- 2NT: Invitational (8-9)
- 3NT: To play (10-15)
- 4NT: Quantitative slam invite (16-17)
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


def get_bid(hand: Hand, auction: list, my_position: str = "South",
            dealer: str = "North", vulnerability: str = "None") -> tuple:
    """Get the next bid in an auction."""
    engine = BiddingEngine()
    return engine.get_next_bid(
        hand=hand,
        auction_history=auction,
        my_position=my_position,
        vulnerability=vulnerability,
        dealer=dealer
    )


# =============================================================================
# Stayman Convention
# =============================================================================

class TestStaymanConvention:
    """SAYC: 2♣ Stayman asks opener if they have a 4-card major."""

    def test_stayman_with_both_majors(self):
        """SAYC: Responder bids Stayman with 4-4 majors and 8+ points."""
        # Partner opened 1NT
        # ♠ KJ32 ♥ QJ32 ♦ K32 ♣ 32
        # HCP: K(3)+J(1)+Q(2)+J(1)+K(3) = 10
        hand = make_hand("KJ32", "QJ32", "K32", "32")
        assert hand.hcp >= 8
        assert hand.suit_lengths['♠'] >= 4
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        assert bid == "2♣", f"With 4-4 majors and 10 HCP should bid Stayman, got {bid}"

    def test_stayman_with_4_spades(self):
        """SAYC: Responder bids Stayman with 4 spades and 8+ points."""
        # ♠ KQ32 ♥ J32 ♦ K32 ♣ 432
        # HCP: K(3)+Q(2)+J(1)+K(3) = 9
        hand = make_hand("KQ32", "J32", "K32", "432")
        assert hand.hcp >= 8
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        assert bid == "2♣", f"With 4 spades and 9 HCP should bid Stayman, got {bid}"

    def test_stayman_with_4_hearts(self):
        """SAYC: Responder bids Stayman with 4 hearts and 8+ points."""
        # ♠ J32 ♥ KQ32 ♦ K32 ♣ 432
        # HCP: J(1)+K(3)+Q(2)+K(3) = 9
        hand = make_hand("J32", "KQ32", "K32", "432")
        assert hand.hcp >= 8
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        assert bid == "2♣", f"With 4 hearts and 9 HCP should bid Stayman, got {bid}"

    def test_opener_answers_stayman_with_hearts(self):
        """SAYC: Opener bids 2♥ with 4 hearts (or both majors)."""
        # Opened 1NT, partner bid Stayman 2♣
        # ♠ KQ2 ♥ AJ32 ♦ KQ2 ♣ K32
        # HCP: K(3)+Q(2)+A(4)+J(1)+K(3)+Q(2)+K(3) = 18... need 15-17
        # ♠ K32 ♥ AJ32 ♦ KQ2 ♣ K32 = 3+4+1+3+2+3 = 16
        hand = make_hand("K32", "AJ32", "KQ2", "K32")
        assert 15 <= hand.hcp <= 17
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♣", "Pass"], my_position="South", dealer="South")
        assert bid == "2♥", f"With 4 hearts should answer Stayman with 2♥, got {bid}"

    def test_opener_answers_stayman_with_spades(self):
        """SAYC: Opener bids 2♠ with 4 spades (no 4 hearts)."""
        # ♠ AJ32 ♥ K32 ♦ KQ2 ♣ K32
        # HCP: A(4)+J(1)+K(3)+K(3)+Q(2)+K(3) = 16
        hand = make_hand("AJ32", "K32", "KQ2", "K32")
        assert 15 <= hand.hcp <= 17
        assert hand.suit_lengths['♠'] >= 4
        assert hand.suit_lengths['♥'] < 4
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♣", "Pass"], my_position="South", dealer="South")
        assert bid == "2♠", f"With 4 spades, no hearts should answer 2♠, got {bid}"

    def test_opener_answers_stayman_no_major(self):
        """SAYC: Opener bids 2♦ denying 4-card major."""
        # ♠ K32 ♥ AQ2 ♦ KJ32 ♣ K32
        # HCP: K(3)+A(4)+Q(2)+K(3)+J(1)+K(3) = 16
        hand = make_hand("K32", "AQ2", "KJ32", "K32")
        assert 15 <= hand.hcp <= 17
        assert hand.suit_lengths['♠'] < 4
        assert hand.suit_lengths['♥'] < 4
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♣", "Pass"], my_position="South", dealer="South")
        assert bid == "2♦", f"Without 4-card major should deny with 2♦, got {bid}"

    def test_responder_bids_game_after_fit(self):
        """SAYC: Responder bids 4♠ after finding 4-4 spade fit with game values."""
        # Partner opened 1NT, we bid 2♣, partner bid 2♠
        # ♠ KQ32 ♥ J32 ♦ K32 ♣ 432
        # HCP: 9, game values
        hand = make_hand("KQ32", "J32", "K32", "432")
        assert hand.hcp >= 8
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♣", "Pass", "2♠", "Pass"])
        # With 4-card spade fit and 9 HCP (combined 24+), should bid game
        assert bid in ["3♠", "4♠", "3NT"], f"With spade fit should bid game or invite, got {bid}"

    def test_responder_bids_3nt_after_denial(self):
        """SAYC: Responder bids 3NT after Stayman denial with game values."""
        # Partner opened 1NT, we bid 2♣, partner bid 2♦ (no major)
        # ♠ KQ32 ♥ J32 ♦ K32 ♣ 432
        hand = make_hand("KQ32", "J32", "K32", "432")
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♣", "Pass", "2♦", "Pass"])
        # Without major fit but game values, bid 3NT
        assert bid in ["2NT", "3NT"], f"Without fit should bid NT, got {bid}"


# =============================================================================
# Jacoby Transfers
# =============================================================================

class TestJacobyTransfers:
    """SAYC: 2♦ transfers to hearts, 2♥ transfers to spades."""

    def test_transfer_to_hearts(self):
        """SAYC: Bid 2♦ to transfer to hearts with 5+ hearts."""
        # Partner opened 1NT
        # ♠ 32 ♥ KJ432 ♦ K32 ♣ 432
        # HCP: K(3)+J(1)+K(3) = 7
        hand = make_hand("32", "KJ432", "K32", "432")
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        assert bid == "2♦", f"With 5 hearts should transfer with 2♦, got {bid}"

    def test_transfer_to_spades(self):
        """SAYC: Bid 2♥ to transfer to spades with 5+ spades."""
        # Partner opened 1NT
        # ♠ KJ432 ♥ 32 ♦ K32 ♣ 432
        # HCP: K(3)+J(1)+K(3) = 7
        hand = make_hand("KJ432", "32", "K32", "432")
        assert hand.suit_lengths['♠'] >= 5
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        assert bid == "2♥", f"With 5 spades should transfer with 2♥, got {bid}"

    def test_opener_completes_heart_transfer(self):
        """SAYC: Opener bids 2♥ to complete the transfer."""
        # Opened 1NT, partner bid 2♦ (transfer)
        # ♠ K32 ♥ AQ2 ♦ KJ32 ♣ K32
        # HCP: 16
        hand = make_hand("K32", "AQ2", "KJ32", "K32")
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♦", "Pass"], my_position="South", dealer="South")
        assert bid == "2♥", f"Must complete transfer to 2♥, got {bid}"

    def test_opener_completes_spade_transfer(self):
        """SAYC: Opener bids 2♠ to complete the transfer."""
        # Opened 1NT, partner bid 2♥ (transfer)
        # ♠ K32 ♥ AQ2 ♦ KJ32 ♣ K32
        hand = make_hand("K32", "AQ2", "KJ32", "K32")
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♥", "Pass"], my_position="South", dealer="South")
        assert bid == "2♠", f"Must complete transfer to 2♠, got {bid}"

    def test_opener_super_accepts_with_4_card_support(self):
        """SAYC: Opener may jump to 3♥ with maximum and 4-card support."""
        # Opened 1NT, partner bid 2♦ (hearts)
        # ♠ K2 ♥ AQ32 ♦ KJ32 ♣ K32
        # HCP: K(3)+A(4)+Q(2)+K(3)+J(1)+K(3) = 16
        hand = make_hand("K2", "AQ32", "KJ32", "K32")
        assert 15 <= hand.hcp <= 17
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♦", "Pass"], my_position="South", dealer="South")
        # Super-accept is optional - accepting with 2♥ is also correct
        assert bid in ["2♥", "3♥"], f"Should accept transfer, got {bid}"

    def test_transfer_then_bid_game(self):
        """SAYC: After transfer completes, bid game with 10+ HCP.
        Valid options with 5-card major and game values:
        - 3♥: Invitational (some partnerships play as game try)
        - 4♥: Commits to major game (correct with 6+ hearts or unbalanced)
        - 3NT: Game bid, offers partner choice (correct with 5 hearts and balanced)
        """
        # Partner opened 1NT, we transferred, partner completed
        # ♠ 32 ♥ AJ432 ♦ KQ2 ♣ 432
        # HCP: A(4)+J(1)+K(3)+Q(2) = 10, shape 2-5-3-3 (balanced)
        hand = make_hand("32", "AJ432", "KQ2", "432")
        assert hand.hcp >= 10
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♦", "Pass", "2♥", "Pass"])
        # With balanced 10 HCP and 5 hearts, 3NT is also correct (offers partner choice)
        assert bid in ["3♥", "4♥", "3NT"], f"With game values should bid game, got {bid}"

    def test_transfer_then_pass_weak(self):
        """SAYC: After transfer completes, pass with weak hand."""
        # Partner opened 1NT, we transferred, partner completed
        # ♠ 32 ♥ J9432 ♦ Q32 ♣ 432
        # HCP: J(1)+Q(2) = 3
        hand = make_hand("32", "J9432", "Q32", "432")
        assert hand.hcp < 8
        bid, _ = get_bid(hand, ["1NT", "Pass", "2♦", "Pass", "2♥", "Pass"])
        assert bid == "Pass", f"Weak hand should pass after transfer, got {bid}"


# =============================================================================
# Direct Notrump Raises
# =============================================================================

class TestNotrumpRaises:
    """SAYC: Direct raises of 1NT opening."""

    def test_2nt_invitational(self):
        """SAYC: 2NT is invitational with 8-9 HCP balanced."""
        # Partner opened 1NT
        # ♠ K32 ♥ Q32 ♦ J32 ♣ K432
        # HCP: K(3)+Q(2)+J(1)+K(3) = 9
        hand = make_hand("K32", "Q32", "J32", "K432")
        assert 8 <= hand.hcp <= 9
        assert hand.suit_lengths['♠'] < 4  # no 4-card major
        assert hand.suit_lengths['♥'] < 4
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        # Without a 4-card major, 2NT invite is correct
        assert bid == "2NT", f"8-9 HCP balanced should bid 2NT invite, got {bid}"

    def test_3nt_to_play(self):
        """SAYC: 3NT is to play with 10-15 HCP balanced."""
        # Partner opened 1NT
        # ♠ K32 ♥ Q32 ♦ KJ2 ♣ K432
        # HCP: K(3)+Q(2)+K(3)+J(1)+K(3) = 12
        hand = make_hand("K32", "Q32", "KJ2", "K432")
        assert 10 <= hand.hcp <= 15
        assert hand.suit_lengths['♠'] < 4
        assert hand.suit_lengths['♥'] < 4
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        assert bid == "3NT", f"12 HCP balanced without 4-card major should bid 3NT, got {bid}"

    def test_4nt_quantitative(self):
        """SAYC: 4NT is quantitative slam invite with 16-17 HCP."""
        # Partner opened 1NT
        # ♠ AK2 ♥ Q32 ♦ KQ2 ♣ K432
        # HCP: A(4)+K(3)+Q(2)+K(3)+Q(2)+K(3) = 17
        hand = make_hand("AK2", "Q32", "KQ2", "K432")
        assert 16 <= hand.hcp <= 17
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        # 4NT is quantitative (not Blackwood over 1NT)
        assert bid in ["4NT", "6NT"], f"16-17 HCP should invite slam, got {bid}"


# =============================================================================
# 2NT Opening and Responses
# =============================================================================

class Test2NTOpeningAndResponses:
    """SAYC: 2NT shows 20-21 HCP balanced."""

    def test_3c_stayman_over_2nt(self):
        """SAYC: 3♣ is Stayman over 2NT."""
        # Partner opened 2NT
        # ♠ Q432 ♥ Q32 ♦ 432 ♣ 432
        # HCP: Q(2)+Q(2) = 4
        hand = make_hand("Q432", "Q32", "432", "432")
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_bid(hand, ["2NT", "Pass"])
        # With 4-card major, use Stayman (3♣)
        assert bid == "3♣", f"4-card major over 2NT should use Stayman 3♣, got {bid}"

    def test_3d_transfer_to_hearts_over_2nt(self):
        """SAYC: 3♦ transfers to hearts over 2NT."""
        # Partner opened 2NT
        # ♠ 32 ♥ Q9432 ♦ 432 ♣ 432
        # HCP: Q(2) = 2
        hand = make_hand("32", "Q9432", "432", "432")
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_bid(hand, ["2NT", "Pass"])
        assert bid == "3♦", f"5 hearts over 2NT should transfer with 3♦, got {bid}"

    def test_3h_transfer_to_spades_over_2nt(self):
        """SAYC: 3♥ transfers to spades over 2NT."""
        # Partner opened 2NT
        # ♠ Q9432 ♥ 32 ♦ 432 ♣ 432
        # HCP: Q(2) = 2
        hand = make_hand("Q9432", "32", "432", "432")
        assert hand.suit_lengths['♠'] >= 5
        bid, _ = get_bid(hand, ["2NT", "Pass"])
        assert bid == "3♥", f"5 spades over 2NT should transfer with 3♥, got {bid}"

    def test_3nt_over_2nt_to_play(self):
        """SAYC: 3NT over 2NT is to play."""
        # Partner opened 2NT
        # ♠ Q32 ♥ J32 ♦ Q32 ♣ J432
        # HCP: Q(2)+J(1)+Q(2)+J(1) = 6
        hand = make_hand("Q32", "J32", "Q32", "J432")
        assert hand.suit_lengths['♠'] < 4
        assert hand.suit_lengths['♥'] < 4
        assert hand.suit_lengths['♥'] < 5
        assert hand.suit_lengths['♠'] < 5
        bid, _ = get_bid(hand, ["2NT", "Pass"])
        # With balanced hand and no major, bid 3NT
        assert bid == "3NT", f"Balanced without major should bid 3NT, got {bid}"

    def test_pass_2nt_very_weak(self):
        """SAYC: Pass 2NT with very weak hand."""
        # Partner opened 2NT
        # ♠ 432 ♥ 432 ♦ 5432 ♣ 432
        # HCP: 0
        hand = make_hand("432", "432", "5432", "432")
        assert hand.hcp <= 3
        bid, _ = get_bid(hand, ["2NT", "Pass"])
        assert bid == "Pass", f"Very weak hand should pass 2NT, got {bid}"


# =============================================================================
# 1NT Opener's Rebid
# =============================================================================

class Test1NTOpenerRebid:
    """SAYC: 1NT opener's rebid after responder's second bid."""

    def test_pass_2nt_invite_minimum(self):
        """SAYC: Pass 2NT invite with 15 HCP."""
        # Opened 1NT, partner bid 2NT (invite)
        # ♠ K32 ♥ AQ2 ♦ K432 ♣ K32
        # HCP: K(3)+A(4)+Q(2)+K(3)+K(3) = 15
        hand = make_hand("K32", "AQ2", "K432", "K32")
        assert hand.hcp == 15
        bid, _ = get_bid(hand, ["1NT", "Pass", "2NT", "Pass"], my_position="South", dealer="South")
        assert bid == "Pass", f"Minimum 1NT should pass 2NT invite, got {bid}"

    def test_accept_2nt_invite_maximum(self):
        """SAYC: Accept 2NT invite with 17 HCP."""
        # Opened 1NT, partner bid 2NT (invite)
        # ♠ K32 ♥ AQ2 ♦ KQ32 ♣ K32
        # HCP: K(3)+A(4)+Q(2)+K(3)+Q(2)+K(3) = 17
        hand = make_hand("K32", "AQ2", "KQ32", "K32")
        assert hand.hcp == 17
        bid, _ = get_bid(hand, ["1NT", "Pass", "2NT", "Pass"], my_position="South", dealer="South")
        assert bid == "3NT", f"Maximum 1NT should accept 2NT invite, got {bid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
