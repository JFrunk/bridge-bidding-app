"""
ACBL SAYC Test Suite: Rebids

Reference: ACBL SAYC Booklet - "Opener's Rebid" and "Responder's Rebid" sections

Opener's Rebid ranges:
- Minimum (13-16): Simple rebid of suit, raise partner's suit, 1NT
- Medium (17-18): Jump in own suit, jump raise of partner
- Maximum (19-21): Jump to game, jump shift, 2NT

Responder's Rebid:
- Sign-off: Minimum hand, made minimum response
- Invitational: 11-12 points
- Game-forcing: 13+ points
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


def get_opener_rebid(hand: Hand, auction: list, vulnerability: str = "None") -> tuple:
    """Get opener's rebid after partner responds."""
    engine = BiddingEngine()
    return engine.get_next_bid(
        hand=hand,
        auction_history=auction,
        my_position="South",
        vulnerability=vulnerability,
        dealer="South"
    )


def get_responder_rebid(hand: Hand, auction: list, vulnerability: str = "None") -> tuple:
    """Get responder's rebid after opener rebids."""
    engine = BiddingEngine()
    return engine.get_next_bid(
        hand=hand,
        auction_history=auction,
        my_position="South",
        vulnerability=vulnerability,
        dealer="North"
    )


# =============================================================================
# Opener's Rebid After 1-Level Response
# =============================================================================

class TestOpenerRebidAfterOneLevelResponse:
    """SAYC: Opener's rebid after partner responds at the 1-level."""

    def test_raise_partners_major_minimum(self):
        """SAYC: Raise partner's major with 4-card support, minimum hand (13-15)."""
        # Opened 1♦, partner bid 1♠, we have 4 spades
        # Need a hand with 13-15 HCP (minimum) to expect simple raise
        # ♠ KJ32 ♥ K2 ♦ AQJ32 ♣ 32
        # HCP: K(3)+J(1)+K(3)+A(4)+Q(2)+J(1) = 14
        hand = make_hand("KJ32", "K2", "AQJ32", "32")
        assert 13 <= hand.hcp <= 15, f"Expected 13-15 HCP, got {hand.hcp}"
        assert hand.suit_lengths['♠'] >= 4
        auction = ["1♦", "Pass", "1♠", "Pass"]  # We opened, partner responded 1♠
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "2♠", f"With 4-card spade support and minimum hand, should raise to 2♠, got {bid}"

    def test_rebid_1nt_balanced_minimum(self):
        """SAYC: Rebid 1NT with balanced minimum (13-14) after 1-level response."""
        # Opened 1♦, partner bid 1♠
        # ♠ K2 ♥ Q32 ♦ AJ432 ♣ K32
        # HCP: K(3)+Q(2)+A(4)+J(1)+K(3) = 13
        hand = make_hand("K2", "Q32", "AJ432", "K32")
        assert hand.hcp == 13
        assert hand.is_balanced
        auction = ["1♦", "Pass", "1♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "1NT", f"Balanced minimum should rebid 1NT, got {bid}"

    def test_rebid_own_suit_minimum(self):
        """SAYC: Rebid own suit with 6+ cards, minimum hand."""
        # Opened 1♥, partner bid 1♠
        # ♠ 32 ♥ AKJ432 ♦ K32 ♣ 32
        # HCP: A(4)+K(3)+J(1)+K(3) = 11... need 13
        # ♠ 32 ♥ AKJ432 ♦ KQ2 ♣ 32 = 4+3+1+3+2 = 13
        hand = make_hand("32", "AKJ432", "KQ2", "32")
        assert hand.hcp == 13
        assert hand.suit_lengths['♥'] >= 6
        auction = ["1♥", "Pass", "1♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "2♥", f"With 6-card suit minimum should rebid suit, got {bid}"

    def test_new_suit_lower_ranking(self):
        """SAYC: Bid new suit (lower ranking) with two-suited hand.
        Note: With minimum (13 HCP) after 1NT response, both Pass (accept 1NT)
        and 2♦ (show second suit) are valid SAYC options.
        """
        # Opened 1♠, partner bid 1NT
        # ♠ AKJ32 ♥ 32 ♦ KQ32 ♣ 32
        # HCP: A(4)+K(3)+J(1)+K(3)+Q(2) = 13
        hand = make_hand("AKJ32", "32", "KQ32", "32")
        assert hand.hcp == 13
        auction = ["1♠", "Pass", "1NT", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        # Both Pass (accept 1NT) and 2♦ (show second suit) are acceptable with minimum
        assert bid in ["2♦", "Pass"], f"Should show second suit 2♦ or pass, got {bid}"

    def test_jump_rebid_medium_hand(self):
        """SAYC: Jump rebid own suit with 17-18 and 6+ cards."""
        # Opened 1♥, partner bid 1♠
        # ♠ K2 ♥ AKQ432 ♦ KQ2 ♣ 32
        # HCP: K(3)+A(4)+K(3)+Q(2)+K(3)+Q(2) = 17
        hand = make_hand("K2", "AKQ432", "KQ2", "32")
        assert hand.hcp == 17
        assert hand.suit_lengths['♥'] >= 6
        auction = ["1♥", "Pass", "1♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "3♥", f"17 HCP with 6-card suit should jump rebid to 3♥, got {bid}"

    def test_jump_raise_partners_major(self):
        """SAYC: Jump raise partner's major with 4-card support, 17-18."""
        # Opened 1♦, partner bid 1♠
        # ♠ AQ32 ♥ K2 ♦ AKJ32 ♣ 32
        # HCP: A(4)+Q(2)+K(3)+A(4)+K(3)+J(1) = 17
        hand = make_hand("AQ32", "K2", "AKJ32", "32")
        assert hand.hcp == 17
        assert hand.suit_lengths['♠'] >= 4
        auction = ["1♦", "Pass", "1♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "3♠", f"17 HCP with 4-card support should jump raise to 3♠, got {bid}"

    def test_rebid_2nt_18_19_balanced(self):
        """SAYC: Rebid 2NT with 18-19 balanced."""
        # Opened 1♦, partner bid 1♠
        # ♠ KQ2 ♥ AQ2 ♦ AKJ32 ♣ 32
        # HCP: K(3)+Q(2)+A(4)+Q(2)+A(4)+K(3)+J(1) = 19
        hand = make_hand("KQ2", "AQ2", "AKJ32", "32")
        assert hand.hcp == 19
        auction = ["1♦", "Pass", "1♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "2NT", f"19 HCP balanced should rebid 2NT, got {bid}"

    def test_jump_to_game_in_major(self):
        """SAYC: Jump to 4♠ with 19+ and 4-card support."""
        # Opened 1♦, partner bid 1♠
        # ♠ AK32 ♥ A2 ♦ AKJ32 ♣ 32
        # HCP: A(4)+K(3)+A(4)+A(4)+K(3)+J(1) = 19
        hand = make_hand("AK32", "A2", "AKJ32", "32")
        assert hand.hcp == 19
        assert hand.suit_lengths['♠'] >= 4
        auction = ["1♦", "Pass", "1♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "4♠", f"19 HCP with 4-card support should jump to 4♠, got {bid}"


# =============================================================================
# Opener's Rebid After 2-Level Response
# =============================================================================

class TestOpenerRebidAfterTwoLevelResponse:
    """SAYC: Opener's rebid after partner responds at the 2-level (10+ points)."""

    def test_raise_partners_minor(self):
        """SAYC: Raise partner's minor with 4+ support."""
        # Opened 1♥, partner bid 2♣
        # ♠ 32 ♥ AKJ32 ♦ K2 ♣ Q432
        # HCP: A(4)+K(3)+J(1)+K(3)+Q(2) = 13
        hand = make_hand("32", "AKJ32", "K2", "Q432")
        assert hand.hcp == 13
        assert hand.suit_lengths['♣'] >= 4
        auction = ["1♥", "Pass", "2♣", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "3♣", f"With 4-card club support should raise to 3♣, got {bid}"

    def test_rebid_own_suit(self):
        """SAYC: Rebid 6-card suit."""
        # Opened 1♥, partner bid 2♦
        # ♠ K2 ♥ AQJ432 ♦ 32 ♣ K32
        # HCP: K(3)+A(4)+Q(2)+J(1)+K(3) = 13
        hand = make_hand("K2", "AQJ432", "32", "K32")
        assert hand.hcp == 13
        assert hand.suit_lengths['♥'] >= 6
        auction = ["1♥", "Pass", "2♦", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "2♥", f"With 6-card heart suit should rebid 2♥, got {bid}"

    def test_rebid_2nt_balanced(self):
        """SAYC: Rebid 2NT with balanced 13-14."""
        # Opened 1♦, partner bid 2♣
        # ♠ KQ2 ♥ Q32 ♦ AJ32 ♣ K32
        # HCP: K(3)+Q(2)+Q(2)+A(4)+J(1)+K(3) = 15... too high
        # ♠ KQ2 ♥ J32 ♦ AJ32 ♣ K32 = 3+2+1+4+1+3 = 14
        hand = make_hand("KQ2", "J32", "AJ32", "K32")
        assert hand.hcp == 14
        assert hand.is_balanced
        auction = ["1♦", "Pass", "2♣", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "2NT", f"Balanced 14 should rebid 2NT, got {bid}"


# =============================================================================
# Opener's Rebid After Raise
# =============================================================================

class TestOpenerRebidAfterRaise:
    """SAYC: Opener's rebid after partner raises."""

    def test_pass_after_single_raise_minimum(self):
        """SAYC: Pass after single raise with minimum opening."""
        # Opened 1♠, partner raised to 2♠
        # ♠ AKJ32 ♥ Q32 ♦ K32 ♣ 32
        # HCP: A(4)+K(3)+J(1)+Q(2)+K(3) = 13
        hand = make_hand("AKJ32", "Q32", "K32", "32")
        assert hand.hcp == 13
        auction = ["1♠", "Pass", "2♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "Pass", f"Minimum opener should pass single raise, got {bid}"

    def test_invite_game_after_raise(self):
        """SAYC: Invite game (3♠) after raise with 16-17."""
        # Opened 1♠, partner raised to 2♠
        # ♠ AKJ32 ♥ AQ2 ♦ K32 ♣ 32
        # HCP: A(4)+K(3)+J(1)+A(4)+Q(2)+K(3) = 17
        hand = make_hand("AKJ32", "AQ2", "K32", "32")
        assert hand.hcp == 17
        auction = ["1♠", "Pass", "2♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "3♠", f"17 HCP should invite game with 3♠, got {bid}"

    def test_bid_game_after_raise(self):
        """SAYC: Bid game (4♠) after raise with 18+."""
        # Opened 1♠, partner raised to 2♠
        # ♠ AKJ32 ♥ AK2 ♦ K32 ♣ 32
        # HCP: A(4)+K(3)+J(1)+A(4)+K(3)+K(3) = 18
        hand = make_hand("AKJ32", "AK2", "K32", "32")
        assert hand.hcp == 18
        auction = ["1♠", "Pass", "2♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "4♠", f"18 HCP should bid game 4♠, got {bid}"

    def test_accept_limit_raise_minimum_with_quality_suit(self):
        """SAYC: Accept limit raise with minimum but quality trumps (AKJ32).

        Limit raise shows 10-12 HCP. With 13 HCP and AKJ32 (7 HCP in suit),
        combined ~24 with excellent trumps is a reasonable accept.
        """
        # ♠ AKJ32 ♥ Q32 ♦ K32 ♣ 32 = 13 HCP
        hand = make_hand("AKJ32", "Q32", "K32", "32")
        assert hand.hcp == 13
        auction = ["1♠", "Pass", "3♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "4♠", f"13 HCP with quality AKJ32 trumps should accept limit raise, got {bid}"

    def test_decline_limit_raise_weak_minimum(self):
        """SAYC: Decline limit raise with weak minimum (12 HCP, poor suit)."""
        # ♠ Q9832 ♥ KJ2 ♦ AQ4 ♣ 32 = 2+4+6+0 = 12 HCP, poor trumps
        hand = make_hand("Q9832", "KJ2", "AQ4", "32")
        assert hand.hcp == 12
        auction = ["1♠", "Pass", "3♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "Pass", f"12 HCP with poor trumps should decline limit raise, got {bid}"

    def test_accept_limit_raise_maximum(self):
        """SAYC: Accept limit raise (bid 4♠) with 15+."""
        # Opened 1♠, partner limit raised to 3♠
        # ♠ AKJ32 ♥ AQ2 ♦ K32 ♣ 32
        # HCP: 17
        hand = make_hand("AKJ32", "AQ2", "K32", "32")
        assert hand.hcp >= 15
        auction = ["1♠", "Pass", "3♠", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "4♠", f"Strong opener should accept limit raise, got {bid}"


# =============================================================================
# Responder's Rebid
# =============================================================================

class TestResponderRebid:
    """SAYC: Responder's rebid after opener rebids."""

    def test_pass_with_minimum_after_1nt_rebid(self):
        """SAYC: Pass opener's 1NT rebid with minimum response."""
        # Partner opened 1♦, we bid 1♠, partner rebid 1NT
        # ♠ KJ32 ♥ 432 ♦ 32 ♣ Q432
        # HCP: K(3)+J(1)+Q(2) = 6
        hand = make_hand("KJ32", "432", "32", "Q432")
        assert hand.hcp == 6
        auction = ["1♦", "Pass", "1♠", "Pass", "1NT", "Pass"]
        bid, _ = get_responder_rebid(hand, auction)
        assert bid == "Pass", f"Minimum responder should pass 1NT, got {bid}"

    def test_raise_1nt_to_2nt_invitational(self):
        """SAYC: Raise 1NT to 2NT with 11-12 points."""
        # Partner opened 1♦, we bid 1♠, partner rebid 1NT
        # ♠ KJ32 ♥ K32 ♦ 32 ♣ Q432
        # HCP: K(3)+J(1)+K(3)+Q(2) = 9... need 11
        # ♠ KQ32 ♥ KJ2 ♦ 32 ♣ Q432 = 3+2+3+1+2 = 11
        hand = make_hand("KQ32", "KJ2", "32", "Q432")
        assert hand.hcp == 11
        auction = ["1♦", "Pass", "1♠", "Pass", "1NT", "Pass"]
        bid, _ = get_responder_rebid(hand, auction)
        assert bid == "2NT", f"11 HCP should invite with 2NT, got {bid}"

    def test_raise_1nt_to_3nt_game_values(self):
        """SAYC: Raise 1NT to 3NT with 13+ points."""
        # Partner opened 1♦, we bid 1♠, partner rebid 1NT
        # ♠ KQ32 ♥ AJ2 ♦ 32 ♣ Q432
        # HCP: K(3)+Q(2)+A(4)+J(1)+Q(2) = 12... need 13
        # ♠ KQ32 ♥ AJ2 ♦ 32 ♣ K432 = 3+2+4+1+3 = 13
        hand = make_hand("KQ32", "AJ2", "32", "K432")
        assert hand.hcp == 13
        auction = ["1♦", "Pass", "1♠", "Pass", "1NT", "Pass"]
        bid, _ = get_responder_rebid(hand, auction)
        assert bid == "3NT", f"13 HCP should bid 3NT, got {bid}"

    def test_preference_back_to_openers_suit(self):
        """SAYC: Give preference to opener's first suit with doubleton."""
        # Partner opened 1♥, we bid 1♠, partner rebid 2♦
        # ♠ KJ432 ♥ 32 ♦ Q32 ♣ Q32
        # HCP: K(3)+J(1)+Q(2)+Q(2) = 8
        hand = make_hand("KJ432", "32", "Q32", "Q32")
        assert hand.hcp == 8
        auction = ["1♥", "Pass", "1♠", "Pass", "2♦", "Pass"]
        bid, _ = get_responder_rebid(hand, auction)
        # With 2-2 in opener's suits, should prefer hearts (first suit)
        # or pass with equal length
        assert bid in ["2♥", "Pass"], f"Should give preference to hearts or pass, got {bid}"

    def test_rebid_own_suit_with_6_cards(self):
        """SAYC: Rebid own suit with 6+ cards."""
        # Partner opened 1♥, we bid 1♠, partner rebid 2♣
        # ♠ QJ9432 ♥ 32 ♦ K32 ♣ 32
        # HCP: Q(2)+J(1)+K(3) = 6
        hand = make_hand("QJ9432", "32", "K32", "32")
        assert hand.hcp == 6
        assert hand.suit_lengths['♠'] == 6
        auction = ["1♥", "Pass", "1♠", "Pass", "2♣", "Pass"]
        bid, _ = get_responder_rebid(hand, auction)
        assert bid == "2♠", f"With 6-card spade suit should rebid 2♠, got {bid}"


# =============================================================================
# Opener's Rebid After 1NT Response
# =============================================================================

class TestOpenerRebidAfter1NTResponse:
    """SAYC: Opener's rebid after partner responds 1NT (6-10)."""

    def test_pass_1nt_with_balanced_minimum(self):
        """SAYC: Pass 1NT with balanced minimum."""
        # Opened 1♠, partner bid 1NT
        # ♠ AKJ32 ♥ Q32 ♦ K32 ♣ 32
        # HCP: 13, balanced
        hand = make_hand("AKJ32", "Q32", "K32", "32")
        assert hand.hcp == 13
        auction = ["1♠", "Pass", "1NT", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        # With 5-3-3-2 and minimum, passing 1NT is often right
        # but rebidding 2♠ with 5-card suit is also acceptable
        assert bid in ["Pass", "2♠"], f"Minimum balanced should pass or rebid suit, got {bid}"

    def test_rebid_6_card_suit(self):
        """SAYC: Rebid 6-card suit after 1NT response."""
        # Opened 1♠, partner bid 1NT
        # ♠ AKJ432 ♥ Q2 ♦ K32 ♣ 32
        # HCP: A(4)+K(3)+J(1)+Q(2)+K(3) = 13
        hand = make_hand("AKJ432", "Q2", "K32", "32")
        assert hand.hcp == 13
        assert hand.suit_lengths['♠'] == 6
        auction = ["1♠", "Pass", "1NT", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "2♠", f"With 6-card spade suit should rebid 2♠, got {bid}"

    def test_show_second_suit(self):
        """SAYC: Show second suit after 1NT response.
        Note: With minimum (13 HCP) after 1NT response, both Pass (accept 1NT)
        and 2♥ (show second suit) are valid SAYC options.
        """
        # Opened 1♠, partner bid 1NT
        # ♠ AKJ32 ♥ KQ32 ♦ 32 ♣ 32
        # HCP: A(4)+K(3)+J(1)+K(3)+Q(2) = 13
        hand = make_hand("AKJ32", "KQ32", "32", "32")
        assert hand.hcp == 13
        auction = ["1♠", "Pass", "1NT", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        # Both Pass and 2♥ are acceptable with minimum 5-4 after 1NT
        assert bid in ["2♥", "Pass"], f"With 5-4 should show second suit 2♥ or pass, got {bid}"

    def test_jump_rebid_with_extras(self):
        """SAYC: Jump rebid with 17+ and 6-card suit."""
        # Opened 1♠, partner bid 1NT
        # ♠ AKQ432 ♥ AQ ♦ K32 ♣ 32
        # HCP: A(4)+K(3)+Q(2)+A(4)+Q(2)+K(3) = 18
        hand = make_hand("AKQ432", "AQ", "K32", "32")
        assert hand.hcp == 18
        assert hand.suit_lengths['♠'] == 6
        auction = ["1♠", "Pass", "1NT", "Pass"]
        bid, _ = get_opener_rebid(hand, auction)
        assert bid == "3♠", f"18 HCP with 6-card suit should jump rebid 3♠, got {bid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
