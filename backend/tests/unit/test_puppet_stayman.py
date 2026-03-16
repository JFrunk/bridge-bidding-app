"""
Tests for Puppet Stayman Convention.

Puppet Stayman: 3♣ over 2NT to discover both 4-card and 5-card majors.

Opener's response to 3♣:
  - 3♦ = has at least one 4-card major
  - 3♥ = has 5 hearts
  - 3♠ = has 5 spades
  - 3NT = no 4+ card major

After 3♦ (opener has 4-card major), responder uses INVERSION:
  - 3♥ = I have 4 spades (bid suit I don't have)
  - 3♠ = I have 4 hearts (bid suit I don't have)
  - 4♦ = I have both 4-card majors

Opener then places the final contract.
"""

import pytest
from engine.hand import Hand, Card
from engine.ai.conventions.puppet_stayman import PuppetStaymanConvention
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


class TestPuppetInitiation:
    """Test responder initiating Puppet Stayman (3♣ over 2NT)."""

    def test_puppet_with_4_card_major(self):
        """4-card major + game values over 2NT → 3♣ Puppet."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠KQ43 ♥J53 ♦Q42 ♣T73")  # 8 HCP, 4♠
        auction = ['2NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♣', f"Expected 3♣ Puppet Stayman, got {result[0]}"

    def test_puppet_with_both_majors(self):
        """Both 4-card majors over 2NT → 3♣ Puppet."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠KQ43 ♥QJ42 ♦T92 ♣73")  # 9 HCP, 4♠ 4♥
        auction = ['2NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♣', f"Expected 3♣ Puppet Stayman, got {result[0]}"

    def test_no_puppet_without_major(self):
        """No 4+ card major → no Puppet."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠K53 ♥J53 ♦Q942 ♣T73")  # 6 HCP, no 4-card major
        auction = ['2NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is None, "No 4-card major should not trigger Puppet"

    def test_no_puppet_over_1nt(self):
        """Puppet Stayman only applies over 2NT, not 1NT."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠KQ43 ♥J53 ♦Q42 ♣T73")  # 8 HCP, 4♠
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is None, "Puppet should not apply over 1NT"

    def test_stayman_no_longer_handles_2nt(self):
        """Regular Stayman should not claim 2NT auctions anymore."""
        stayman = StaymanConvention()
        hand = make_hand("♠KQ43 ♥QJ42 ♦T92 ♣73")  # 9 HCP, 4♠ 4♥
        auction = ['2NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = stayman.evaluate(hand, features)
        assert result is None, "Regular Stayman should not handle 2NT (Puppet takes over)"


class TestPuppetOpenerResponse:
    """Test opener's response to 3♣ Puppet Stayman."""

    def test_opener_shows_5_hearts(self):
        """Opener with 5 hearts → 3♥."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠AQ5 ♥KQJ43 ♦AJ4 ♣Q7")  # 20 HCP, 5♥
        auction = ['2NT', 'Pass', '3♣', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♥', f"Expected 3♥ (5 hearts), got {result[0]}"

    def test_opener_shows_5_spades(self):
        """Opener with 5 spades → 3♠."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠AKJ43 ♥AQ5 ♦AJ4 ♣Q7")  # 21 HCP, 5♠
        auction = ['2NT', 'Pass', '3♣', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♠', f"Expected 3♠ (5 spades), got {result[0]}"

    def test_opener_relays_with_4_card_major(self):
        """Opener with 4-card major (no 5) → 3♦ relay."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠AQ53 ♥KJ3 ♦AJ4 ♣Q73")  # 17 HCP, 4♠
        auction = ['2NT', 'Pass', '3♣', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♦', f"Expected 3♦ (4-card major relay), got {result[0]}"

    def test_opener_denies_with_3nt(self):
        """Opener with no 4+ card major → 3NT."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠AQ5 ♥KJ3 ♦AJ42 ♣Q73")  # 17 HCP, 3-3-4-3
        auction = ['2NT', 'Pass', '3♣', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3NT', f"Expected 3NT (no major), got {result[0]}"


class TestPuppetInversion:
    """Test responder's inversion bids after opener's 3♦."""

    def test_inversion_has_spades(self):
        """Responder with 4♠ only bids 3♥ (suit they DON'T have)."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠KQ43 ♥J53 ♦Q42 ♣T73")  # 8 HCP, 4♠
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♦', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♥', f"Expected 3♥ inversion (has 4♠), got {result[0]}"

    def test_inversion_has_hearts(self):
        """Responder with 4♥ only bids 3♠ (suit they DON'T have)."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠J53 ♥KQ43 ♦Q42 ♣T73")  # 8 HCP, 4♥
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♦', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3♠', f"Expected 3♠ inversion (has 4♥), got {result[0]}"

    def test_inversion_has_both(self):
        """Responder with both 4-card majors bids 4♦."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠KQ43 ♥QJ42 ♦T92 ♣73")  # 9 HCP, 4♠ 4♥
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♦', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♦', f"Expected 4♦ (both majors), got {result[0]}"


class TestPuppetOpenerPlacement:
    """Test opener's final contract placement after responder's inversion."""

    def test_opener_places_4_spades_after_3h_inversion(self):
        """After 3♥ inversion (responder has 4♠), opener with 4♠ → 4♠."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠AQ53 ♥KJ3 ♦AJ4 ♣Q73")  # 17 HCP, 4♠
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♦', 'Pass', '3♥', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♠', f"Expected 4♠ (fit found), got {result[0]}"

    def test_opener_places_3nt_no_spade_fit(self):
        """After 3♥ inversion (responder has 4♠), opener without 4♠ → 3NT."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠AQ5 ♥KJ43 ♦AJ4 ♣Q73")  # 17 HCP, 4♥ only
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♦', 'Pass', '3♥', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3NT', f"Expected 3NT (no spade fit), got {result[0]}"

    def test_opener_places_4_hearts_after_3s_inversion(self):
        """After 3♠ inversion (responder has 4♥), opener with 4♥ → 4♥."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠AQ5 ♥KJ43 ♦AJ4 ♣Q73")  # 17 HCP, 4♥
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♦', 'Pass', '3♠', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♥', f"Expected 4♥ (fit found), got {result[0]}"

    def test_opener_places_after_4d_both_majors(self):
        """After 4♦ (responder has both), opener bids their 4-card major."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠AQ53 ♥KJ3 ♦AJ4 ♣Q73")  # 17 HCP, 4♠
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♦', 'Pass', '4♦', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♠', f"Expected 4♠ (opener's major), got {result[0]}"


class TestPuppetAfterDirectMajor:
    """Test responder's continuation after opener shows 5-card major."""

    def test_raise_5_hearts_with_support(self):
        """Opener bid 3♥ (5 hearts), responder with 3+ hearts → 4♥."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠KQ43 ♥J53 ♦Q42 ♣T73")  # 8 HCP, 3♥
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♥', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♥', f"Expected 4♥ (raising 5-card suit), got {result[0]}"

    def test_3nt_without_heart_support(self):
        """Opener bid 3♥ (5 hearts), responder without support → 3NT."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠KQ43 ♥J5 ♦Q742 ♣T73")  # 7 HCP, 2♥
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3♥', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == '3NT', f"Expected 3NT (no heart support), got {result[0]}"

    def test_pass_after_3nt_denial(self):
        """Opener bid 3NT (no major), responder passes."""
        puppet = PuppetStaymanConvention()
        hand = make_hand("♠KQ43 ♥J53 ♦Q42 ♣T73")  # 8 HCP
        auction = ['2NT', 'Pass', '3♣', 'Pass', '3NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = puppet.evaluate(hand, features)
        assert result is not None
        assert result[0] == 'Pass', f"Expected Pass after 3NT denial, got {result[0]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
