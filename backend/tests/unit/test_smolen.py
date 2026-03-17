"""
Tests for Smolen Convention.

Smolen: After 1NT → 2♣ → 2♦ (Stayman denial), responder with 5-4 in
majors and 10+ HCP jumps to 3-level in their 4-CARD major (inverted):
  - 3♥ = 4 hearts, 5 spades
  - 3♠ = 4 spades, 5 hearts

Opener responds:
  - 4M (partner's 5-card suit) with 3+ support
  - 3NT without support
"""

import pytest
from engine.hand import Hand, Card
from engine.ai.conventions.smolen import SmolenConvention
from engine.ai.conventions.stayman import StaymanConvention
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


class TestSmolenInitiation:
    """Test responder's Smolen jump."""

    def test_smolen_5_spades_4_hearts(self):
        """5 spades + 4 hearts + 10+ HCP → 3♥ (bid 4-card suit)."""
        smolen = SmolenConvention()
        hand = make_hand("♠AKJ97 ♥QJ43 ♦T9 ♣32")  # 11 HCP, 5♠ 4♥
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♥', f"Expected 3♥ Smolen (4 hearts), got {result[0]}"

    def test_smolen_5_hearts_4_spades(self):
        """5 hearts + 4 spades + 10+ HCP → 3♠ (bid 4-card suit)."""
        smolen = SmolenConvention()
        hand = make_hand("♠KQ43 ♥AQT97 ♦T9 ♣32")  # 12 HCP, 4♠ 5♥
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♠', f"Expected 3♠ Smolen (4 spades), got {result[0]}"

    def test_no_smolen_weak_hand(self):
        """<10 HCP should not trigger Smolen."""
        smolen = SmolenConvention()
        hand = make_hand("♠QJ976 ♥J432 ♦T9 ♣32")  # 5 HCP, 5♠ 4♥
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is None, "Weak hand should not use Smolen"

    def test_no_smolen_4_4_shape(self):
        """4-4 in majors (not 5-4) should not trigger Smolen."""
        smolen = SmolenConvention()
        hand = make_hand("♠KQ43 ♥AQT9 ♦T92 ♣32")  # 12 HCP, 4♠ 4♥
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is None, "4-4 shape should use regular Stayman, not Smolen"

    def test_no_smolen_after_2nt(self):
        """Smolen only applies after 1NT, not 2NT."""
        smolen = SmolenConvention()
        hand = make_hand("♠AKJ97 ♥QJ43 ♦T9 ♣32")  # 11 HCP, 5♠ 4♥
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♦', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is None, "Smolen should not apply over 2NT (use Puppet instead)"

    def test_no_smolen_when_fit_found(self):
        """If opener showed a major and we have fit, no Smolen needed."""
        smolen = SmolenConvention()
        hand = make_hand("♠AKJ97 ♥QJ43 ♦T9 ♣32")  # 11 HCP, 5♠ 4♥
        # Opener showed hearts - we have 4♥ fit, Stayman handles this
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♥', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is None, "Should not use Smolen when fit found"


class TestSmolenOpenerResponse:
    """Test opener's response to partner's Smolen jump."""

    def test_opener_accepts_with_3_spades(self):
        """Partner bid 3♥ (= 5 spades), opener has 3+ spades → 4♠."""
        smolen = SmolenConvention()
        hand = make_hand("♠AQ5 ♥KJ3 ♦AJ42 ♣Q73")  # 16 HCP, 3♠
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass', '3♥', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♠', f"Expected 4♠ (accepting Smolen), got {result[0]}"

    def test_opener_declines_without_spade_support(self):
        """Partner bid 3♥ (= 5 spades), opener has <3 spades → 3NT."""
        smolen = SmolenConvention()
        hand = make_hand("♠Q5 ♥KJ32 ♦AJ42 ♣Q73")  # 15 HCP, 2♠
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass', '3♥', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3NT', f"Expected 3NT (declining Smolen), got {result[0]}"

    def test_opener_accepts_with_3_hearts(self):
        """Partner bid 3♠ (= 5 hearts), opener has 3+ hearts → 4♥."""
        smolen = SmolenConvention()
        hand = make_hand("♠KJ3 ♥AQ5 ♦AJ42 ♣Q73")  # 16 HCP, 3♥
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass', '3♠', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♥', f"Expected 4♥ (accepting Smolen), got {result[0]}"

    def test_opener_declines_without_heart_support(self):
        """Partner bid 3♠ (= 5 hearts), opener has <3 hearts → 3NT."""
        smolen = SmolenConvention()
        hand = make_hand("♠KJ32 ♥Q5 ♦AJ42 ♣Q73")  # 15 HCP, 2♥
        auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass', '3♠', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = smolen.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3NT', f"Expected 3NT (declining Smolen), got {result[0]}"


class TestStaymanAllowsSmolenShape:
    """Test that Stayman now accepts 5-4 major hands for Smolen."""

    def test_stayman_accepts_5_4_with_game_values(self):
        """5-4 major hand with 10+ HCP should be allowed into Stayman."""
        stayman = StaymanConvention()
        hand = make_hand("♠AKJ97 ♥QJ43 ♦T9 ♣32")  # 11 HCP, 5♠ 4♥
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = stayman.evaluate(hand, features)
        assert result is not None
        assert result[0] == '2♣', f"Expected 2♣ Stayman for Smolen-eligible hand, got {result[0]}"

    def test_stayman_rejects_5_4_weak(self):
        """5-4 major hand with <10 HCP should use Jacoby, not Stayman."""
        stayman = StaymanConvention()
        hand = make_hand("♠QJ976 ♥J432 ♦T9 ♣32")  # 5 HCP, 5♠ 4♥
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = stayman.evaluate(hand, features)
        assert result is None, "Weak 5-4 hand should use Jacoby, not Stayman"

    def test_stayman_rejects_5_3_shape(self):
        """5-3 in majors should still use Jacoby (only 5-4 gets Smolen)."""
        stayman = StaymanConvention()
        hand = make_hand("♠AKJ97 ♥QJ4 ♦T92 ♣32")  # 11 HCP, 5♠ 3♥
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = stayman.evaluate(hand, features)
        assert result is None, "5-3 shape should use Jacoby, not Stayman"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
