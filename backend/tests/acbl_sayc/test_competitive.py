"""
ACBL SAYC Test Suite: Competitive Bidding

Reference: ACBL SAYC Booklet - "Competitive Bidding" section

SAYC Competitive Conventions:
- Overcalls: 8-16 points, good 5+ card suit
- 1NT Overcall: 15-18 HCP, balanced, stopper in opponent's suit
- Takeout Doubles: Opening values, support for unbid suits
- Negative Doubles: Over partner's opening, shows unbid major(s)
- Michaels Cuebid: 5-5 in two suits (majors or major + minor)
- Unusual 2NT: 5-5 in two lowest unbid suits

Advancing partner's overcall:
- Simple raise: 8-10 points, 3+ support
- Jump raise: 11-12 points, 4+ support
- Cuebid: Game-forcing with support
- New suit: Non-forcing, good suit
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
            dealer: str = "East", vulnerability: str = "None") -> tuple:
    """Get the next bid in an auction (default: opponent opened)."""
    engine = BiddingEngine()
    return engine.get_next_bid(
        hand=hand,
        auction_history=auction,
        my_position=my_position,
        vulnerability=vulnerability,
        dealer=dealer
    )


# =============================================================================
# Simple Overcalls
# =============================================================================

class TestSimpleOvercalls:
    """SAYC: Simple overcalls show 8-16 points and a good 5+ card suit."""

    def test_1s_overcall(self):
        """SAYC: Overcall 1♠ with 5+ spades and 8-16 points."""
        # Opponent opened 1♥
        # ♠ AQJ32 ♥ 32 ♦ K32 ♣ 432
        # HCP: A(4)+Q(2)+J(1)+K(3) = 10
        hand = make_hand("AQJ32", "32", "K32", "432")
        assert 8 <= hand.hcp <= 16
        assert hand.suit_lengths['♠'] >= 5
        bid, _ = get_bid(hand, ["1♥"])  # East opened 1♥
        assert bid == "1♠", f"With 5 spades and 10 HCP should overcall 1♠, got {bid}"

    def test_2c_overcall(self):
        """SAYC: Overcall 2♣ with 5+ clubs and 10+ points."""
        # Opponent opened 1♠
        # ♠ 32 ♥ K32 ♦ 432 ♣ AKJ32
        # HCP: K(3)+A(4)+K(3)+J(1) = 11
        hand = make_hand("32", "K32", "432", "AKJ32")
        assert hand.hcp >= 10
        assert hand.suit_lengths['♣'] >= 5
        bid, _ = get_bid(hand, ["1♠"])
        assert bid == "2♣", f"With 5 clubs and 11 HCP should overcall 2♣, got {bid}"

    def test_2h_overcall(self):
        """SAYC: Overcall 2♥ over 1♠ with good heart suit."""
        # Opponent opened 1♠
        # ♠ 32 ♥ AKQ32 ♦ K32 ♣ 432
        # HCP: A(4)+K(3)+Q(2)+K(3) = 12
        hand = make_hand("32", "AKQ32", "K32", "432")
        assert hand.hcp >= 10
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_bid(hand, ["1♠"])
        assert bid == "2♥", f"With 5 hearts and 12 HCP should overcall 2♥, got {bid}"

    def test_pass_weak_no_suit(self):
        """SAYC: Pass with less than 8 points or poor suit."""
        # Opponent opened 1♥
        # ♠ Q432 ♥ 32 ♦ K32 ♣ J432
        # HCP: Q(2)+K(3)+J(1) = 6
        hand = make_hand("Q432", "32", "K32", "J432")
        assert hand.hcp < 8
        bid, _ = get_bid(hand, ["1♥"])
        assert bid == "Pass", f"With weak hand should pass, got {bid}"


# =============================================================================
# 1NT Overcall
# =============================================================================

class Test1NTOvercall:
    """SAYC: 1NT overcall shows 15-18 HCP, balanced, with stopper."""

    def test_1nt_overcall_with_stopper(self):
        """SAYC: Overcall 1NT with 15-18 balanced and stopper in opener's suit."""
        # Opponent opened 1♥
        # ♠ K32 ♥ AQ2 ♦ KJ32 ♣ K32
        # HCP: K(3)+A(4)+Q(2)+K(3)+J(1)+K(3) = 16
        hand = make_hand("K32", "AQ2", "KJ32", "K32")
        assert 15 <= hand.hcp <= 18
        assert hand.is_balanced
        # Has heart stopper (AQ)
        bid, _ = get_bid(hand, ["1♥"])
        assert bid == "1NT", f"With 16 HCP balanced and heart stopper should bid 1NT, got {bid}"

    def test_1nt_overcall_various_stoppers(self):
        """SAYC: 1NT with KJx stopper."""
        # Opponent opened 1♦
        # ♠ K32 ♥ AQ2 ♦ KJ2 ♣ K432
        # HCP: K(3)+A(4)+Q(2)+K(3)+J(1)+K(3) = 16
        hand = make_hand("K32", "AQ2", "KJ2", "K432")
        assert 15 <= hand.hcp <= 18
        # Has diamond stopper (KJ)
        bid, _ = get_bid(hand, ["1♦"])
        assert bid == "1NT", f"With 16 HCP balanced and diamond stopper should bid 1NT, got {bid}"

    def test_no_1nt_without_stopper(self):
        """SAYC: Don't overcall 1NT without stopper in opponent's suit."""
        # Opponent opened 1♠
        # ♠ 32 ♥ AQ32 ♦ KQ32 ♣ K32
        # HCP: A(4)+Q(2)+K(3)+Q(2)+K(3) = 14... need more
        # ♠ 32 ♥ AQ32 ♦ KQ32 ♣ KJ2 = 4+2+3+2+3+1 = 15
        hand = make_hand("32", "AQ32", "KQ32", "KJ2")
        assert hand.hcp >= 15
        # No spade stopper
        bid, _ = get_bid(hand, ["1♠"])
        # Should not bid 1NT without stopper - might double or pass
        assert bid != "1NT", f"Without spade stopper should not bid 1NT, got {bid}"


# =============================================================================
# Takeout Doubles
# =============================================================================

class TestTakeoutDoubles:
    """SAYC: Takeout double shows opening values and support for unbid suits."""

    def test_takeout_double_classic_shape(self):
        """SAYC: Double with opening values and 4+ in each unbid suit."""
        # Opponent opened 1♥
        # ♠ KJ32 ♥ 2 ♦ AQ32 ♣ K432
        # HCP: K(3)+J(1)+A(4)+Q(2)+K(3) = 13
        hand = make_hand("KJ32", "2", "AQ32", "K432")
        assert hand.hcp >= 12
        assert hand.suit_lengths['♠'] >= 3
        assert hand.suit_lengths['♦'] >= 3
        assert hand.suit_lengths['♣'] >= 3
        bid, _ = get_bid(hand, ["1♥"])
        assert bid == "X", f"Classic takeout shape should double, got {bid}"

    def test_takeout_double_over_1c(self):
        """SAYC: Double 1♣ with support for all three other suits."""
        # Opponent opened 1♣
        # ♠ KJ32 ♥ AQ32 ♦ K432 ♣ 2
        # HCP: K(3)+J(1)+A(4)+Q(2)+K(3) = 13
        hand = make_hand("KJ32", "AQ32", "K432", "2")
        assert hand.hcp >= 12
        bid, _ = get_bid(hand, ["1♣"])
        assert bid == "X", f"With support for majors and diamonds should double, got {bid}"

    def test_takeout_double_strong_hand(self):
        """SAYC: Double with 17+ even without perfect shape, plan to bid again."""
        # Opponent opened 1♦
        # ♠ AKQ32 ♥ AQ32 ♦ 2 ♣ K32
        # HCP: A(4)+K(3)+Q(2)+A(4)+Q(2)+K(3) = 18
        hand = make_hand("AKQ32", "AQ32", "2", "K32")
        assert hand.hcp >= 17
        bid, _ = get_bid(hand, ["1♦"])
        # With 18 HCP might double (plan to bid spades) or overcall 1♠
        assert bid in ["X", "1♠"], f"Strong hand should double or overcall, got {bid}"


# =============================================================================
# Responding to Takeout Double
# =============================================================================

class TestRespondingToDouble:
    """SAYC: Responding to partner's takeout double."""

    def test_minimum_response_to_double(self):
        """SAYC: Bid cheapest 4-card major with 0-8 points."""
        # Partner (North) doubled opponent's (East) 1♥
        # Auction: East opens 1♥, South passes, West passes, North doubles, East passes, South responds
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # ♠ Q432 ♥ 432 ♦ K32 ♣ 432
        # HCP: Q(2)+K(3) = 5
        hand = make_hand("Q432", "432", "K32", "432")
        assert hand.hcp <= 8
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass", "X", "Pass"])
        assert bid == "1♠", f"With 4 spades should respond 1♠, got {bid}"

    def test_jump_response_to_double(self):
        """SAYC: Jump bid with 9-11 points (invitational)."""
        # Partner (North) doubled opponent's (East) 1♥
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # ♠ KQ32 ♥ 432 ♦ KJ2 ♣ 432
        # HCP: K(3)+Q(2)+K(3)+J(1) = 9
        hand = make_hand("KQ32", "432", "KJ2", "432")
        assert 9 <= hand.hcp <= 11
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass", "X", "Pass"])
        assert bid == "2♠", f"With 9 HCP and 4 spades should jump to 2♠, got {bid}"

    def test_game_response_to_double(self):
        """SAYC: Bid game with 12+ points."""
        # Partner (North) doubled opponent's (East) 1♥
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # ♠ AQ32 ♥ 432 ♦ KQ2 ♣ K32
        # HCP: A(4)+Q(2)+K(3)+Q(2)+K(3) = 14
        hand = make_hand("AQ32", "432", "KQ2", "K32")
        assert hand.hcp >= 12
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass", "X", "Pass"])
        # Game values, bid 4♠ or cuebid 2♥
        assert bid in ["4♠", "2♥"], f"With game values should bid game or cuebid, got {bid}"

    def test_1nt_response_to_double(self):
        """SAYC: Bid 1NT with stopper in opponent's suit and 6-10 HCP."""
        # Partner (North) doubled opponent's (East) 1♥
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # ♠ K32 ♥ AJ2 ♦ Q432 ♣ 432
        # HCP: K(3)+A(4)+J(1)+Q(2) = 10
        hand = make_hand("K32", "AJ2", "Q432", "432")
        assert 6 <= hand.hcp <= 10
        # Heart stopper (AJ)
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass", "X", "Pass"])
        assert bid == "1NT", f"With heart stopper and 10 HCP should bid 1NT, got {bid}"


# =============================================================================
# Negative Doubles
# =============================================================================

class TestNegativeDoubles:
    """SAYC: Negative double shows unbid major(s) when opponent overcalls."""

    def test_negative_double_shows_hearts(self):
        """SAYC: Negative double of 1♠ overcall shows 4+ hearts."""
        # Partner opened 1♦, opponent overcalled 1♠
        # ♠ 32 ♥ KQ32 ♦ Q32 ♣ K432
        # HCP: K(3)+Q(2)+Q(2)+K(3) = 10
        hand = make_hand("32", "KQ32", "Q32", "K432")
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_bid(hand, ["1♦", "1♠"], dealer="North")  # Partner opened
        assert bid == "X", f"With 4 hearts should make negative double, got {bid}"

    def test_negative_double_shows_spades(self):
        """SAYC: Negative double of 2♣ overcall shows 4+ spades."""
        # Partner opened 1♥, opponent overcalled 2♣
        # ♠ KQ32 ♥ 32 ♦ Q432 ♣ 432
        # HCP: K(3)+Q(2)+Q(2) = 7
        hand = make_hand("KQ32", "32", "Q432", "432")
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_bid(hand, ["1♥", "2♣"], dealer="North")
        assert bid == "X", f"With 4 spades should make negative double, got {bid}"

    def test_negative_double_both_majors(self):
        """SAYC: Negative double of 1♦ shows both 4-card majors."""
        # Partner opened 1♣, opponent overcalled 1♦
        # ♠ KJ32 ♥ Q432 ♦ 32 ♣ K32
        # HCP: K(3)+J(1)+Q(2)+K(3) = 9
        hand = make_hand("KJ32", "Q432", "32", "K32")
        assert hand.suit_lengths['♠'] >= 4
        assert hand.suit_lengths['♥'] >= 4
        bid, _ = get_bid(hand, ["1♣", "1♦"], dealer="North")
        assert bid == "X", f"With both majors should make negative double, got {bid}"


# =============================================================================
# Michaels Cuebid
# =============================================================================

class TestMichaelsCuebid:
    """SAYC: Cuebid of opponent's suit shows 5-5 two-suiter."""

    def test_michaels_over_minor(self):
        """SAYC: 2♣ over 1♣ shows both majors (5-5)."""
        # Opponent opened 1♣
        # ♠ KQ432 ♥ AJ432 ♦ 2 ♣ 32
        # HCP: K(3)+Q(2)+A(4)+J(1) = 10
        hand = make_hand("KQ432", "AJ432", "2", "32")
        assert hand.suit_lengths['♠'] >= 5
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_bid(hand, ["1♣"])
        assert bid == "2♣", f"With 5-5 majors should cuebid 2♣, got {bid}"

    def test_michaels_over_1h(self):
        """SAYC: 2♥ over 1♥ shows spades + minor."""
        # Opponent opened 1♥
        # ♠ KQ432 ♥ 2 ♦ AJ432 ♣ 32
        # 5-5 spades and diamonds
        hand = make_hand("KQ432", "2", "AJ432", "32")
        assert hand.suit_lengths['♠'] >= 5
        assert hand.suit_lengths['♦'] >= 5
        bid, _ = get_bid(hand, ["1♥"])
        assert bid == "2♥", f"With 5-5 spades/diamonds should cuebid 2♥, got {bid}"

    def test_michaels_over_1s(self):
        """SAYC: 2♠ over 1♠ shows hearts + minor."""
        # Opponent opened 1♠
        # ♠ 2 ♥ KQ432 ♦ AJ432 ♣ 32
        # 5-5 hearts and diamonds
        hand = make_hand("2", "KQ432", "AJ432", "32")
        assert hand.suit_lengths['♥'] >= 5
        assert hand.suit_lengths['♦'] >= 5
        bid, _ = get_bid(hand, ["1♠"])
        assert bid == "2♠", f"With 5-5 hearts/diamonds should cuebid 2♠, got {bid}"


# =============================================================================
# Unusual 2NT
# =============================================================================

class TestUnusual2NT:
    """SAYC: 2NT overcall shows 5-5 in the two lowest unbid suits."""

    def test_unusual_2nt_over_1s(self):
        """SAYC: 2NT over 1♠ shows clubs and diamonds."""
        # Opponent opened 1♠
        # ♠ 2 ♥ 32 ♦ KQ432 ♣ AJ432
        # 5-5 minors
        hand = make_hand("2", "32", "KQ432", "AJ432")
        assert hand.suit_lengths['♦'] >= 5
        assert hand.suit_lengths['♣'] >= 5
        bid, _ = get_bid(hand, ["1♠"])
        assert bid == "2NT", f"With 5-5 minors should bid unusual 2NT, got {bid}"

    def test_unusual_2nt_over_1h(self):
        """SAYC: 2NT over 1♥ shows clubs and diamonds."""
        # Opponent opened 1♥
        # ♠ 32 ♥ 2 ♦ KQ432 ♣ AJ432
        hand = make_hand("32", "2", "KQ432", "AJ432")
        assert hand.suit_lengths['♦'] >= 5
        assert hand.suit_lengths['♣'] >= 5
        bid, _ = get_bid(hand, ["1♥"])
        assert bid == "2NT", f"With 5-5 minors should bid unusual 2NT, got {bid}"


# =============================================================================
# Advancing Partner's Overcall
# =============================================================================

class TestAdvancingOvercall:
    """SAYC: Advancing (responding to) partner's overcall."""

    def test_simple_raise_of_overcall(self):
        """SAYC: Raise overcall with 8-10 points and 3+ support."""
        # Opponent (East) opened 1♥, South passes, West passes, partner (North) overcalled 1♠
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # ♠ Q32 ♥ 432 ♦ KJ32 ♣ K32
        # HCP: Q(2)+K(3)+J(1)+K(3) = 9
        hand = make_hand("Q32", "432", "KJ32", "K32")
        assert 8 <= hand.hcp <= 10
        assert hand.suit_lengths['♠'] >= 3
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass", "1♠", "Pass"], dealer="East")
        assert bid == "2♠", f"With 3-card support and 9 HCP should raise to 2♠, got {bid}"

    def test_jump_raise_of_overcall(self):
        """SAYC: Jump raise overcall with 11-12 points and 4+ support."""
        # Opponent (East) opened 1♥, South passes, West passes, partner (North) overcalled 1♠
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # ♠ Q432 ♥ 32 ♦ AQ32 ♣ K32 = 2+4+2+3 = 11
        hand = make_hand("Q432", "32", "AQ32", "K32")
        assert 11 <= hand.hcp <= 12
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass", "1♠", "Pass"], dealer="East")
        assert bid == "3♠", f"With 4-card support and 11 HCP should jump to 3♠, got {bid}"

    def test_cuebid_game_force(self):
        """SAYC: Cuebid opponent's suit to show game-forcing raise."""
        # Opponent (East) opened 1♥, South passes, West passes, partner (North) overcalled 1♠
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # ♠ AQ32 ♥ 32 ♦ AQ32 ♣ K32
        # HCP: A(4)+Q(2)+A(4)+Q(2)+K(3) = 15
        hand = make_hand("AQ32", "32", "AQ32", "K32")
        assert hand.hcp >= 13
        assert hand.suit_lengths['♠'] >= 4
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass", "1♠", "Pass"], dealer="East")
        # Cuebid 2♥ shows game-forcing spade support
        assert bid in ["2♥", "4♠"], f"Game-forcing raise should cuebid or bid game, got {bid}"

    def test_new_suit_non_forcing(self):
        """SAYC: New suit by advancer is non-forcing."""
        # Opponent (East) opened 1♣, South passes, West passes, partner (North) overcalled 1♠
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # ♠ 32 ♥ AQJ32 ♦ K32 ♣ 432
        # HCP: A(4)+Q(2)+J(1)+K(3) = 10
        hand = make_hand("32", "AQJ32", "K32", "432")
        assert hand.hcp >= 8
        assert hand.suit_lengths['♥'] >= 5
        bid, _ = get_bid(hand, ["1♣", "Pass", "Pass", "1♠", "Pass"], dealer="East")
        # With good heart suit, bid 2♥ (non-forcing)
        assert bid == "2♥", f"With 5-card heart suit should bid 2♥, got {bid}"

    def test_2nt_advance(self):
        """SAYC: 2NT shows 11-12 with stopper in opponent's suit (invitational)."""
        # Opponent (East) opened 1♦, South passes, West passes, partner (North) overcalled 1♠
        # Position: East(0), South(1), West(2), North(3) - South's partner is North
        # Note: 1NT would be illegal after partner's 1♠, so 2NT is the invitational bid
        # ♠ J2 ♥ K32 ♦ AJ32 ♣ K432 = 1+3+4+1+3 = 12
        hand = make_hand("J2", "K32", "AJ32", "K432")
        assert 11 <= hand.hcp <= 12
        # Diamond stopper (AJ)
        bid, _ = get_bid(hand, ["1♦", "Pass", "Pass", "1♠", "Pass"], dealer="East")
        assert bid == "2NT", f"With stopper and 12 HCP should bid 2NT (invitational), got {bid}"


# =============================================================================
# Balancing
# =============================================================================

class TestBalancing:
    """SAYC: Balancing in passout seat."""

    def test_balancing_double(self):
        """SAYC: Balance with double on lighter values."""
        # 1♥ - Pass - Pass - ? (South in balancing/pass-out seat)
        # Position: West(0), North(1), East(2), South(3) - with dealer=West
        # West opens, North passes, East passes, South balances
        # ♠ KJ32 ♥ 32 ♦ Q432 ♣ K32
        # HCP: K(3)+J(1)+Q(2)+K(3) = 9
        hand = make_hand("KJ32", "32", "Q432", "K32")
        assert hand.hcp >= 8  # Lighter in balancing seat
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass"], dealer="West")
        # Balance with double on 9 HCP and shape
        assert bid == "X", f"Should balance with double, got {bid}"

    def test_balancing_1nt(self):
        """SAYC: Balance with 1NT on 11-14 (not 15-18)."""
        # 1♦ - Pass - Pass - ? (South in balancing/pass-out seat)
        # Position: West(0), North(1), East(2), South(3) - with dealer=West
        # ♠ K32 ♥ QJ2 ♦ KJ2 ♣ Q432
        # HCP: K(3)+Q(2)+J(1)+K(3)+J(1)+Q(2) = 12
        hand = make_hand("K32", "QJ2", "KJ2", "Q432")
        assert 11 <= hand.hcp <= 14
        # Diamond stopper
        bid, _ = get_bid(hand, ["1♦", "Pass", "Pass"], dealer="West")
        assert bid == "1NT", f"Should balance with 1NT, got {bid}"

    def test_balancing_overcall(self):
        """SAYC: Balance with suit bid on lighter values."""
        # 1♥ - Pass - Pass - ? (South in balancing/pass-out seat)
        # Position: West(0), North(1), East(2), South(3) - with dealer=West
        # ♠ KQJ32 ♥ 32 ♦ Q32 ♣ 432
        # HCP: K(3)+Q(2)+J(1)+Q(2) = 8
        hand = make_hand("KQJ32", "32", "Q32", "432")
        assert hand.hcp >= 6  # Very light balancing
        assert hand.suit_lengths['♠'] >= 5
        bid, _ = get_bid(hand, ["1♥", "Pass", "Pass"], dealer="West")
        assert bid == "1♠", f"Should balance with 1♠, got {bid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
