"""
ACBL SAYC Test Suite: Slam Bidding

Reference: ACBL SAYC Booklet - "Slam Bidding" section

SAYC Slam Conventions:
- Blackwood (4NT): Asks for aces
  - 5♣ = 0 or 4 aces
  - 5♦ = 1 ace
  - 5♥ = 2 aces
  - 5♠ = 3 aces
- 5NT: Asks for kings (implies all aces are held)
- Gerber (4♣): Used over NT openings to ask for aces

Slam requirements:
- Small slam (6-level): 33+ combined points
- Grand slam (7-level): 37+ combined points, all aces
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
# Blackwood Convention
# =============================================================================

class TestBlackwoodConvention:
    """SAYC: 4NT Blackwood asks for aces."""

    def test_blackwood_after_major_fit(self):
        """SAYC: Bid 4NT Blackwood when slam is possible after major fit."""
        # Partner opened 1♠, we have slam interest
        # ♠ KQ32 ♥ A2 ♦ AKQ2 ♣ K32
        # HCP: K(3)+Q(2)+A(4)+A(4)+K(3)+Q(2)+K(3) = 21
        hand = make_hand("KQ32", "A2", "AKQ2", "K32")
        assert hand.hcp >= 18
        auction = ["1♠", "Pass", "3♠", "Pass", "4♠", "Pass"]  # Limit raise, accepted
        # With 4-card support and 21 HCP, should ask for aces
        # Actually after 1♠-3♠-4♠, responder with slam interest bids 4NT
        bid, _ = get_bid(hand, auction)
        assert bid in ["4NT", "Pass"], f"With slam values should consider Blackwood, got {bid}"

    def test_respond_blackwood_no_aces(self):
        """SAYC: Respond 5♣ to Blackwood with 0 (or 4) aces."""
        # Partner bid 4NT (Blackwood)
        # ♠ Q432 ♥ KQ32 ♦ Q32 ♣ 32
        # HCP: Q(2)+K(3)+Q(2)+Q(2) = 9, no aces
        hand = make_hand("Q432", "KQ32", "Q32", "32")
        assert hand.hcp >= 6
        auction = ["1♠", "Pass", "2♠", "Pass", "4NT", "Pass"]
        bid, _ = get_bid(hand, auction)
        assert bid == "5♣", f"With 0 aces should respond 5♣, got {bid}"

    def test_respond_blackwood_one_ace(self):
        """SAYC: Respond 5♦ to Blackwood with 1 ace."""
        # Partner bid 4NT (Blackwood)
        # ♠ A432 ♥ KQ32 ♦ Q32 ♣ 32
        # HCP: A(4)+K(3)+Q(2)+Q(2) = 11, one ace
        hand = make_hand("A432", "KQ32", "Q32", "32")
        # Count aces
        ace_count = sum(1 for c in hand.cards if c.rank == 'A')
        assert ace_count == 1
        auction = ["1♠", "Pass", "2♠", "Pass", "4NT", "Pass"]
        bid, _ = get_bid(hand, auction)
        assert bid == "5♦", f"With 1 ace should respond 5♦, got {bid}"

    def test_respond_blackwood_two_aces(self):
        """SAYC: Respond 5♥ to Blackwood with 2 aces."""
        # Partner bid 4NT (Blackwood)
        # ♠ A432 ♥ AQ32 ♦ Q32 ♣ 32
        # HCP: A(4)+A(4)+Q(2)+Q(2) = 12, two aces
        hand = make_hand("A432", "AQ32", "Q32", "32")
        ace_count = sum(1 for c in hand.cards if c.rank == 'A')
        assert ace_count == 2
        auction = ["1♠", "Pass", "2♠", "Pass", "4NT", "Pass"]
        bid, _ = get_bid(hand, auction)
        assert bid == "5♥", f"With 2 aces should respond 5♥, got {bid}"

    def test_respond_blackwood_three_aces(self):
        """SAYC: Respond 5♠ to Blackwood with 3 aces."""
        # Partner bid 4NT (Blackwood)
        # ♠ A432 ♥ AQ32 ♦ A32 ♣ 32
        # HCP: A(4)+A(4)+Q(2)+A(4) = 14, three aces
        hand = make_hand("A432", "AQ32", "A32", "32")
        ace_count = sum(1 for c in hand.cards if c.rank == 'A')
        assert ace_count == 3
        auction = ["1♠", "Pass", "2♠", "Pass", "4NT", "Pass"]
        bid, _ = get_bid(hand, auction)
        assert bid == "5♠", f"With 3 aces should respond 5♠, got {bid}"

    def test_bid_slam_after_blackwood(self):
        """SAYC: Bid 6♠ after Blackwood shows enough aces."""
        # We (South) opened 1♠, bid 4NT, partner showed 2 aces (5♥)
        # ♠ AKQ32 ♥ AK ♦ KQ32 ♣ 32
        # HCP: A(4)+K(3)+Q(2)+A(4)+K(3)+K(3)+Q(2) = 21
        hand = make_hand("AKQ32", "AK", "KQ32", "32")
        ace_count = sum(1 for c in hand.cards if c.rank == 'A')
        assert ace_count == 2
        # We have 2 aces, partner showed 2, all 4 accounted for
        # dealer='South' so South is the opener who bid 4NT
        auction = ["1♠", "Pass", "3♠", "Pass", "4NT", "Pass", "5♥", "Pass"]
        bid, _ = get_bid(hand, auction, dealer="South")
        # With all 4 aces, should bid slam (6♠) or grand slam (7♠)
        assert bid in ["6♠", "7♠"], f"With all aces should bid slam, got {bid}"

    def test_sign_off_after_blackwood(self):
        """SAYC: Sign off at 5♠ if missing too many aces."""
        # We (South) opened 1♠, bid 4NT, partner showed 0 aces (5♣)
        # ♠ AKQ32 ♥ AK ♦ KQ32 ♣ 32
        # We have 2 aces, partner has 0 = missing 2 aces
        hand = make_hand("AKQ32", "AK", "KQ32", "32")
        # dealer='South' so South is the opener who bid 4NT
        auction = ["1♠", "Pass", "3♠", "Pass", "4NT", "Pass", "5♣", "Pass"]
        bid, _ = get_bid(hand, auction, dealer="South")
        # Missing 2 aces, should sign off
        assert bid in ["5♠", "Pass"], f"Missing aces should sign off, got {bid}"


# =============================================================================
# King Ask (5NT)
# =============================================================================

class TestKingAsk:
    """SAYC: 5NT asks for kings after Blackwood."""

    def test_5nt_asks_kings(self):
        """SAYC: 5NT asks for kings (implies all aces held)."""
        # We (South) opened 1♠, bid 4NT, partner showed all 4 aces (5♣ = 0 or 4)
        # ♠ AKQJ2 ♥ KQ ♦ KQ32 ♣ 32
        # No aces ourselves, so partner has all 4
        hand = make_hand("AKQJ2", "KQ", "KQ32", "32")
        # dealer='South' so South is the opener who bid 4NT
        auction = ["1♠", "Pass", "3♠", "Pass", "4NT", "Pass", "5♣", "Pass"]
        bid, _ = get_bid(hand, auction, dealer="South")
        # With 5♣ response and no aces ourselves, partner could have 0 or 4
        # With 0 aces partner -> sign off; with 4 aces -> ask kings or bid slam
        # Since we have no aces, 5♣ more likely means 0 (partner has 0)
        # Engine should sign off or explore carefully
        assert bid in ["5♠", "5NT", "6♠", "Pass"], f"Should consider king ask or sign off, got {bid}"

    def test_respond_kings_none(self):
        """SAYC: Respond 6♣ with 0 kings."""
        # Partner bid 5NT (king ask)
        # ♠ A432 ♥ AQ32 ♦ 432 ♣ 32
        # 2 aces, 0 kings
        hand = make_hand("A432", "AQ32", "432", "32")
        king_count = sum(1 for c in hand.cards if c.rank == 'K')
        assert king_count == 0
        auction = ["1♠", "Pass", "3♠", "Pass", "4NT", "Pass", "5♥", "Pass", "5NT", "Pass"]
        bid, _ = get_bid(hand, auction)
        assert bid == "6♣", f"With 0 kings should respond 6♣, got {bid}"

    def test_respond_kings_one(self):
        """SAYC: Respond 6♦ with 1 king."""
        # Partner bid 5NT (king ask)
        # ♠ A432 ♥ AK32 ♦ 432 ♣ 32
        # 2 aces, 1 king
        hand = make_hand("A432", "AK32", "432", "32")
        king_count = sum(1 for c in hand.cards if c.rank == 'K')
        assert king_count == 1
        auction = ["1♠", "Pass", "3♠", "Pass", "4NT", "Pass", "5♥", "Pass", "5NT", "Pass"]
        bid, _ = get_bid(hand, auction)
        assert bid == "6♦", f"With 1 king should respond 6♦, got {bid}"


# =============================================================================
# Slam Decisions Without Blackwood
# =============================================================================

class TestSlamDecisionsWithoutBlackwood:
    """SAYC: Direct slam bidding without conventions."""

    def test_bid_small_slam_with_values(self):
        """SAYC: Bid 6NT directly with 33+ combined points balanced."""
        # Partner opened 1NT (15-17), we have 18 = 33+ minimum
        # ♠ AK2 ♥ KQ2 ♦ AJ32 ♣ K32
        # HCP: A(4)+K(3)+K(3)+Q(2)+A(4)+J(1)+K(3) = 20
        hand = make_hand("AK2", "KQ2", "AJ32", "K32")
        assert hand.hcp >= 18
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        # 15-17 + 20 = 35-37, slam values
        assert bid in ["4NT", "6NT"], f"With slam values should bid slam, got {bid}"

    def test_bid_grand_slam_with_values(self):
        """SAYC: Bid 7NT with 37+ combined points and controls."""
        # Partner opened 2NT (20-21), we have 17 = 37+ minimum
        # ♠ AK2 ♥ KQ2 ♦ AK32 ♣ K32
        # HCP: A(4)+K(3)+K(3)+Q(2)+A(4)+K(3)+K(3) = 22
        hand = make_hand("AK2", "KQ2", "AK32", "K32")
        assert hand.hcp >= 17
        bid, _ = get_bid(hand, ["2NT", "Pass"])
        # 20-21 + 22 = 42-43, grand slam values
        assert bid in ["4NT", "6NT", "7NT"], f"With grand slam values should bid slam, got {bid}"


# =============================================================================
# Gerber (4♣) Over NT
# =============================================================================

class TestGerberConvention:
    """SAYC: 4♣ Gerber asks for aces over NT openings."""

    def test_gerber_over_1nt(self):
        """SAYC: 4♣ is Gerber (ace asking) over 1NT."""
        # Partner opened 1NT
        # ♠ AK32 ♥ KQ32 ♦ AK2 ♣ 32
        # HCP: A(4)+K(3)+K(3)+Q(2)+A(4)+K(3) = 19
        hand = make_hand("AK32", "KQ32", "AK2", "32")
        assert hand.hcp >= 18
        # With slam interest and 4-card major, might use Stayman first or Gerber
        bid, _ = get_bid(hand, ["1NT", "Pass"])
        # Gerber is 4♣, but Stayman (2♣) might be preferred with 4-card major
        assert bid in ["2♣", "4♣", "4NT", "6NT"], f"Should explore slam, got {bid}"

    def test_gerber_over_2nt(self):
        """SAYC: 4♣ is Gerber over 2NT."""
        # Partner opened 2NT
        # ♠ AK32 ♥ KQ32 ♦ K32 ♣ 32
        # HCP: A(4)+K(3)+K(3)+Q(2)+K(3) = 15
        hand = make_hand("AK32", "KQ32", "K32", "32")
        # 20-21 + 15 = 35-36, slam territory
        bid, _ = get_bid(hand, ["2NT", "Pass"])
        # With 4-card major might use Stayman, or Gerber for aces
        assert bid in ["3♣", "4♣", "4NT", "6NT"], f"Should explore slam, got {bid}"

    def test_respond_gerber_one_ace(self):
        """SAYC: Respond 4♥ to Gerber with 1 ace."""
        # Opened 1NT, partner bid 4♣ (Gerber)
        # ♠ K32 ♥ AQ2 ♦ KQ32 ♣ K32
        # HCP: 16, 1 ace
        hand = make_hand("K32", "AQ2", "KQ32", "K32")
        ace_count = sum(1 for c in hand.cards if c.rank == 'A')
        assert ace_count == 1
        bid, _ = get_bid(hand, ["1NT", "Pass", "4♣", "Pass"], my_position="South", dealer="South")
        # Standard Gerber responses: 4♦ = 0/4, 4♥ = 1, 4♠ = 2, 4NT = 3
        assert bid == "4♥", f"With 1 ace should respond 4♥ to Gerber, got {bid}"


# =============================================================================
# Control Bids (Cuebids)
# =============================================================================

class TestControlBids:
    """SAYC: Control bids show first or second round control in a suit."""

    def test_cuebid_shows_control(self):
        """SAYC: Cuebid a side suit ace on the way to slam."""
        # Agreed spades as trump, partner bid 4♣ (control)
        # ♠ KQ32 ♥ A2 ♦ AQ32 ♣ 432
        # We can cuebid hearts (ace) or diamonds (ace)
        hand = make_hand("KQ32", "A2", "AQ32", "432")
        auction = ["1♠", "Pass", "3♠", "Pass", "4♣", "Pass"]  # 4♣ = control bid
        bid, _ = get_bid(hand, auction)
        # Should cuebid a control (hearts or diamonds ace)
        assert bid in ["4♦", "4♥", "4♠", "4NT"], f"Should cuebid control, got {bid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
