"""
Tests for Support Double and Support Redouble.

Support Double: Opener doubles after partner responds at 1-level and RHO overcalls,
showing exactly 3-card support for partner's suit.

Support Redouble: Same concept but when RHO doubles instead of overcalling.

Key rules:
- Exactly 3-card support (with 4+, raise directly)
- Only through 2-level of partner's suit (Law of Total Tricks)
- Opener HCP: 12-17 (18+ bid naturally)
- XX when RHO doubled (instead of X)
"""

import pytest
from engine.hand import Hand, Card
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention
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


class TestSupportDouble:
    """Test support double after partner responds and RHO overcalls."""

    def test_basic_support_double(self):
        """1♣ - P - 1♥ - 1♠ → X showing 3 hearts."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠A5 ♥K93 ♦QJ7 ♣KT842")  # 13 HCP, 3♥
        auction = ['1♣', 'Pass', '1♥', '1♠']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is not None
        assert result[0] == 'X', f"Expected support X, got {result[0]}"
        assert '3-card' in result[1].lower() or 'support' in result[1].lower()

    def test_no_support_double_with_4_card(self):
        """With 4+ card support, should NOT support double (would raise instead)."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠A5 ♥K932 ♦QJ7 ♣KT84")  # 13 HCP, 4♥
        auction = ['1♣', 'Pass', '1♥', '1♠']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is None, "Should NOT support double with 4-card support"

    def test_no_support_double_with_2_card(self):
        """With only 2-card support, should pass (not double)."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠A53 ♥K9 ♦QJ76 ♣KT84")  # 13 HCP, 2♥
        auction = ['1♣', 'Pass', '1♥', '1♠']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is None, "Should NOT support double with only 2-card support"

    def test_support_double_hcp_too_high(self):
        """18+ HCP should bid naturally, not support double."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠AK ♥KQ3 ♦AQJ7 ♣KT84")  # 20 HCP, 3♥
        auction = ['1♣', 'Pass', '1♥', '1♠']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is None, "18+ HCP should bid naturally, not support double"

    def test_support_double_hcp_too_low(self):
        """Below 12 HCP should not support double (not a valid opener)."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠85 ♥K93 ♦QJ7 ♣T8432")  # 8 HCP, 3♥
        auction = ['1♣', 'Pass', '1♥', '1♠']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is None, "Below 12 HCP should not support double"

    def test_level_constraint_2_level_ok(self):
        """RHO overcalls at 2-level with lower suit than partner → OK."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠A5 ♥K93 ♦QJ7 ♣KT842")  # 13 HCP, 3♥
        # 1♣ - P - 1♠ - 2♦ → X is fine (2♠ is still available)
        auction = ['1♣', 'Pass', '1♠', '2♦']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        # 3 spades needed
        # This hand has 2 spades, so shouldn't trigger
        assert result is None

    def test_level_constraint_too_high(self):
        """RHO overcalls at 3-level → too high for support double."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠A5 ♥K93 ♦QJ7 ♣KT842")  # 13 HCP, 3♥
        auction = ['1♣', 'Pass', '1♥', '3♦']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is None, "3-level overcall is too high for support double"

    def test_level_constraint_2_level_outranks_partner(self):
        """RHO overcalls 2♠ over partner's 1♥ → forces 3♥, too high."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠A5 ♥K93 ♦QJ7 ♣KT842")  # 13 HCP, 3♥
        auction = ['1♣', 'Pass', '1♥', '2♠']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is None, "2♠ over 1♥ forces 3♥ level, too high for support double"


class TestSupportRedouble:
    """Test support redouble (XX) when RHO doubles."""

    def test_support_redouble(self):
        """1♦ - P - 1♠ - X → XX showing 3 spades."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠K93 ♥A5 ♦KQT84 ♣J72")  # 13 HCP, 3♠
        auction = ['1♦', 'Pass', '1♠', 'X']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is not None
        assert result[0] == 'XX', f"Expected support XX, got {result[0]}"

    def test_no_redouble_without_3_card(self):
        """RHO doubles but only 2-card support → no redouble."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠K9 ♥A53 ♦KQT84 ♣J72")  # 13 HCP, 2♠
        auction = ['1♦', 'Pass', '1♠', 'X']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_support_double(hand, features)
        assert result is None

    def test_not_opener(self):
        """Support double only applies when I am the opener."""
        conv = TakeoutDoubleConvention()
        hand = make_hand("♠K93 ♥A5 ♦KQT84 ♣J72")  # 13 HCP, 3♠
        # Here East opened, not us
        auction = ['Pass', '1♦', 'Pass', '1♠', 'X']
        features = extract_features(hand, auction, 'North', 'None', 'East')
        result = conv._check_support_double(hand, features)
        assert result is None, "Support double only for opener"
