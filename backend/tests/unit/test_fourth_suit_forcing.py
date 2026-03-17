"""
Tests for Fourth Suit Forcing (FSF) Convention.

FSF: When three suits have been bid by the partnership, bidding the
fourth suit is artificial and game-forcing. Does not show length.

Opener responds with priority:
1. 3-card support for responder's major
2. Stopper in 4th suit → NT (2NT min, 3NT max)
3. 6+ card suit → rebid
4. Min/max signaling
"""

import pytest
from engine.hand import Hand, Card
from engine.ai.conventions.fourth_suit_forcing import FourthSuitForcingConvention
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


class TestFSFInitiation:
    """Test responder initiating Fourth Suit Forcing."""

    def test_basic_fsf(self):
        """1♣ - 1♥ - 1♠ → 2♦ (fourth suit forcing)."""
        conv = FourthSuitForcingConvention()
        # North opens 1♣, South responds 1♥, North rebids 1♠
        # Now South (me) bids FSF: 2♦ is the fourth suit
        hand = make_hand("♠Q3 ♥AKJ42 ♦T93 ♣K72")  # 13 HCP, 5♥
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = conv.evaluate(hand, features)
        assert result is not None, "Should initiate FSF"
        assert result[0] == '2♦', f"Expected 2♦ FSF, got {result[0]}"
        assert 'fourth suit' in result[1].lower()

    def test_no_fsf_with_fit(self):
        """If we have 4+ in partner's suit, raise instead of FSF."""
        conv = FourthSuitForcingConvention()
        hand = make_hand("♠KJ93 ♥AKJ4 ♦T93 ♣72")  # 13 HCP, 4♠ fit with partner
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = conv._check_fsf_initiation(hand, features)
        assert result is None, "Should raise partner's spades, not FSF"

    def test_no_fsf_weak(self):
        """Below 12 HCP should not FSF."""
        conv = FourthSuitForcingConvention()
        hand = make_hand("♠Q3 ♥KJ432 ♦T93 ♣872")  # 7 HCP
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = conv._check_fsf_initiation(hand, features)
        assert result is None, "Need 12+ HCP for FSF"

    def test_no_fsf_with_6_card_suit(self):
        """With 6+ card suit, rebid it instead of FSF."""
        conv = FourthSuitForcingConvention()
        hand = make_hand("♠Q3 ♥AKJ432 ♦T9 ♣K72")  # 13 HCP, 6♥
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = conv._check_fsf_initiation(hand, features)
        assert result is None, "Should rebid 6-card hearts, not FSF"

    def test_fsf_level_calculation(self):
        """FSF bid is at cheapest legal level in 4th suit."""
        conv = FourthSuitForcingConvention()
        # 1♦ - 1♠ - 2♣ → 2♥ (fourth suit, same level since ♥ > ♣)
        hand = make_hand("♠AKJ42 ♥T93 ♦Q3 ♣K72")  # 13 HCP
        auction = ['1♦', 'Pass', '1♠', 'Pass', '2♣', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = conv.evaluate(hand, features)
        assert result is not None
        assert result[0] == '2♥', f"Expected 2♥ FSF, got {result[0]}"


class TestFSFOpenerResponse:
    """Test opener responding to partner's FSF bid."""

    def test_3_card_major_support_min(self):
        """Opener shows 3-card major support (minimum)."""
        conv = FourthSuitForcingConvention()
        # North opens 1♣, South 1♥, North rebids 1♠, South bids 2♦ (FSF)
        # North (me) has 3 hearts and minimum
        hand = make_hand("♠AJ42 ♥K93 ♦72 ♣KT84")  # 12 HCP, 3♥
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv.evaluate(hand, features)
        assert result is not None, "Opener should respond to FSF"
        assert result[0] == '3♥', f"Expected 3♥ (3-card support, min), got {result[0]}"

    def test_3_card_major_support_max(self):
        """Opener shows 3-card major support (maximum → 4M)."""
        conv = FourthSuitForcingConvention()
        hand = make_hand("♠AJ42 ♥KQ3 ♦72 ♣AK84")  # 16 HCP, 3♥
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♥', f"Expected 4♥ (3-card support, max), got {result[0]}"

    def test_stopper_min(self):
        """No major support but stopper → 2NT (minimum)."""
        conv = FourthSuitForcingConvention()
        hand = make_hand("♠AJ42 ♥72 ♦KJ3 ♣KT84")  # 12 HCP, ♦ stopper, 2♥
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv.evaluate(hand, features)
        assert result is not None
        assert result[0] == '2NT', f"Expected 2NT (stopper, min), got {result[0]}"

    def test_stopper_max(self):
        """No major support but stopper → 3NT (maximum)."""
        conv = FourthSuitForcingConvention()
        hand = make_hand("♠AJ42 ♥72 ♦AK3 ♣AK84")  # 17 HCP, ♦ stopper, 2♥
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3NT', f"Expected 3NT (stopper, max), got {result[0]}"

    def test_6_card_rebid(self):
        """No support, no stopper, 6+ card suit → rebid."""
        conv = FourthSuitForcingConvention()
        hand = make_hand("♠A94 ♥72 ♦53 ♣AKJ842")  # 12 HCP, 6♣, no ♦ stopper
        auction = ['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv.evaluate(hand, features)
        assert result is not None
        assert '♣' in result[0], f"Expected club rebid, got {result[0]}"

    def test_not_fsf_position(self):
        """If partner didn't bid 4th suit, don't respond as FSF."""
        conv = FourthSuitForcingConvention()
        hand = make_hand("♠AJ42 ♥K93 ♦72 ♣KT84")  # 12 HCP
        # Only 2 suits bid by partnership (♣ and ♥), not FSF situation
        auction = ['1♣', 'Pass', '1♥', 'Pass', '2♣', 'Pass', '2♥', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = conv._check_fsf_response(hand, features)
        assert result is None, "Not an FSF situation (only 2 distinct suits)"
