"""
Tests for Responsive Double.

Responsive Double: After opponents bid-and-raise and partner doubled/overcalled.

Two variants:
1. Over MINOR raise: Shows 4-4 in both majors, 8+ HCP
   Example: 1♦ - X - 2♦ - X
2. Over MAJOR raise: Shows 10+ HCP with values in unbid suits
   Example: 1♥ - X - 2♥ - X

Level constraint: Only through 3-level.
"""

import pytest
from engine.hand import Hand, Card
from engine.ai.conventions.negative_doubles import NegativeDoubleConvention
from engine.ai.feature_extractor import extract_features


def make_hand(hand_str):
    """Create hand from string like '♠AKT97 ♥JT76 ♦T9 ♣32'."""
    cards = []
    current_suit = None
    for char in hand_str:
        if char in '♠♥♦♣':
            current_suit = char
        elif char in 'AKQJT98765432':
            cards.append(Card(char, current_suit))
    return Hand(cards)


class TestResponsiveDoubleOverMinor:
    """Test responsive double over minor suit raise (requires 4-4 majors)."""

    def test_basic_responsive_over_minor(self):
        """1♦ - X - 2♦ → X showing 4-4 majors, 8+ HCP."""
        conv = NegativeDoubleConvention()
        # East opens 1♦, South(partner) doubles, West raises 2♦, North(me) to act
        hand = make_hand("♠KJ93 ♥QJ42 ♦53 ♣K72")  # 10 HCP, 4♠ 4♥
        auction = ['1♦', 'Pass', 'Pass', 'X', '2♦']
        # Dealer=East, me=North. Positions: E, S, W, N
        # Bid 0 (E): 1♦, Bid 1 (S): Pass, Bid 2 (W): Pass, Bid 3 (N): X → but N is me...
        # Actually: East opens, South passes, West passes, North(partner) doubles, then
        # we need: opener=East, partner doubled, responder raised
        # Let me set up: East opens, South(partner) doubles, West raises
        # Dealer=East: E(open 1♦), S(partner X), W(raise 2♦), N(me to act)
        auction = ['1♦', 'X', '2♦']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is not None, f"Expected responsive double, got None"
        assert result[0] == 'X'
        assert 'major' in result[1].lower()

    def test_no_responsive_minor_without_4_4_majors(self):
        """Over minor raise, need 4-4 in majors — 4-3 not enough."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠KJ93 ♥QT4 ♦532 ♣K72")  # 9 HCP, 4♠ 3♥
        auction = ['1♦', 'X', '2♦']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is None, "Need 4-4 in majors for responsive double over minor"

    def test_no_responsive_minor_weak(self):
        """Over minor raise, need 8+ HCP."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠J932 ♥T432 ♦53 ♣872")  # 1 HCP, 4♠ 4♥
        auction = ['1♦', 'X', '2♦']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is None, "Need 8+ HCP for responsive double"

    def test_no_responsive_with_5_card_suit(self):
        """With a 5-card suit, bid it directly instead of doubling."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠KJ932 ♥QJ42 ♦5 ♣K72")  # 11 HCP, 5♠ 4♥
        auction = ['1♦', 'X', '2♦']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is None, "With 5-card suit, bid it directly"


class TestResponsiveDoubleOverMajor:
    """Test responsive double over major suit raise (requires unbid suit values)."""

    def test_basic_responsive_over_major(self):
        """1♥ - X - 2♥ → X showing unbid suit values, 10+ HCP."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠KJ93 ♥53 ♦AJ42 ♣K72")  # 12 HCP, 4♠ 4♦
        auction = ['1♥', 'X', '2♥']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is not None, f"Expected responsive double over major"
        assert result[0] == 'X'
        assert 'unbid' in result[1].lower()

    def test_no_responsive_major_weak(self):
        """Over major raise, need 10+ HCP (higher than minor)."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠KJ93 ♥53 ♦J432 ♣872")  # 5 HCP
        auction = ['1♥', 'X', '2♥']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is None, "Need 10+ HCP for responsive double over major"

    def test_no_responsive_major_without_unbid_support(self):
        """Over major raise, need 4+ cards in at least 2 unbid suits."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠KJ93 ♥53 ♦QJ2 ♣KT72")  # 12 HCP, but only 2 unbid suits with 4+: ♠(4) and ♣(4), ♦(3)
        auction = ['1♥', 'X', '2♥']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        # ♠=4, ♦=3, ♣=4 → 2 unbid suits with 4+ → should pass
        # Actually ♠(4) and ♣(4) = 2 suits, so this should trigger
        # Let me use a hand that only has 1 unbid suit with 4+
        hand2 = make_hand("♠KJ93 ♥53 ♦QJ2 ♣AT72")  # ♠=4, ♦=3, ♣=4 → 2 suits → triggers
        # Need: only 1 suit with 4+
        hand3 = make_hand("♠KJ932 ♥53 ♦QJ2 ♣AT7")  # ♠=5(bid directly), so use:
        hand4 = make_hand("♠KJ93 ♥532 ♦QJ2 ♣AT7")  # ♠=4, ♦=3, ♣=3 → only 1 suit with 4+
        features4 = extract_features(hand4, ['1♥', 'X', '2♥'], 'North', 'None', 'East')
        result4 = conv._check_responsive_double(hand4, features4)
        assert result4 is None, "Need 4+ in at least 2 unbid suits"


class TestResponsiveDoubleLevelConstraint:
    """Test level constraints for responsive double."""

    def test_responsive_3_level_ok(self):
        """Opponents raise to 3-level → responsive double still OK."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠KJ93 ♥QJ42 ♦53 ♣K72")  # 10 HCP, 4♠ 4♥
        auction = ['1♦', 'X', '3♦']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is not None, "3-level raise is within responsive double range"

    def test_responsive_4_level_too_high(self):
        """Opponents raise to 4-level → too high for responsive double."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠KJ93 ♥QJ42 ♦53 ♣K72")  # 10 HCP, 4♠ 4♥
        auction = ['1♦', 'X', '4♦']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is None, "4-level raise is too high for responsive double"

    def test_not_a_raise(self):
        """If opponents bid different suit, not a responsive double situation."""
        conv = NegativeDoubleConvention()
        hand = make_hand("♠KJ93 ♥QJ42 ♦53 ♣K72")  # 10 HCP
        # RHO bids 2♣ (different suit from opener's 1♦) — not a raise
        auction = ['1♦', 'X', '2♣']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_responsive_double(hand, features)
        assert result is None, "Different suit is not a raise"
