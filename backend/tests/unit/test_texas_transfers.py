"""
Tests for Texas Transfers and Stayman→Gerber transition.

Texas Transfers:
- 4♦ over 1NT/2NT = transfer to 4♥ (6+ hearts, game values)
- 4♥ over 1NT/2NT = transfer to 4♠ (6+ spades, game values)
- Opener MUST complete the transfer
- 4NT after Texas completion = strictly RKCB (not quantitative)

Stayman→Gerber:
- After 1NT→2♣→2♥/2♠, responder's 4♣ = Gerber (ace-asking)
- Opener must respond with ace count
"""

import pytest
from engine.hand import Hand, Card
from engine.ai.conventions.texas_transfers import TexasTransferConvention, is_texas_transfer_sequence
from engine.ai.conventions.gerber import GerberConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.ai.feature_extractor import extract_features


def make_hand(hand_str):
    """Create hand from string like '♠AKT972 ♥JT76 ♦T9 ♣2'."""
    cards = []
    current_suit = None
    for char in hand_str:
        if char in '♠♥♦♣':
            current_suit = char
        elif char in 'AKQJT98765432':
            cards.append(Card(char, current_suit))
    return Hand(cards)


class TestTexasTransferInitiation:
    """Test responder initiating Texas Transfer."""

    def test_texas_hearts_over_1nt(self):
        """6+ hearts with 10-14 HCP over 1NT → 4♦ Texas."""
        texas = TexasTransferConvention()
        hand = make_hand("♠K5 ♥AQT987 ♦J42 ♣Q3")  # 12 HCP, 6 hearts
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♦', f"Expected 4♦ Texas Transfer, got {result[0]}"

    def test_texas_spades_over_1nt(self):
        """6+ spades with 10-14 HCP over 1NT → 4♥ Texas."""
        texas = TexasTransferConvention()
        hand = make_hand("♠AKJ976 ♥J5 ♦Q42 ♣T3")  # 12 HCP, 6 spades
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♥', f"Expected 4♥ Texas Transfer, got {result[0]}"

    def test_texas_over_2nt(self):
        """6+ hearts with 4-9 HCP over 2NT → 4♦ Texas."""
        texas = TexasTransferConvention()
        hand = make_hand("♠85 ♥KJT976 ♦T42 ♣63")  # 5 HCP, 6 hearts
        auction = ['2NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♦', f"Expected 4♦ Texas Transfer over 2NT, got {result[0]}"

    def test_no_texas_with_5_card_suit(self):
        """5-card major should use Jacoby, not Texas."""
        texas = TexasTransferConvention()
        hand = make_hand("♠K5 ♥AQT98 ♦J42 ♣Q32")  # 12 HCP, 5 hearts
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is None, "5-card major should not trigger Texas Transfer"

    def test_no_texas_with_slam_values(self):
        """15+ HCP should use Jacoby + Blackwood, not Texas."""
        texas = TexasTransferConvention()
        hand = make_hand("♠K5 ♥AKQ987 ♦AJ4 ♣Q3")  # 18 HCP, 6 hearts
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is None, "Slam-strength hand should not use Texas (use Jacoby + Blackwood)"

    def test_no_texas_with_weak_hand(self):
        """<10 HCP over 1NT should not use Texas."""
        texas = TexasTransferConvention()
        hand = make_hand("♠85 ♥QJT976 ♦T42 ♣63")  # 5 HCP, 6 hearts
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is None, "Weak hand should not use Texas over 1NT"

    def test_texas_prefers_spades(self):
        """With both 6+ majors, prefer spades."""
        texas = TexasTransferConvention()
        # 6-6-1-0 shape, exactly 13 cards, 10 HCP
        hand = make_hand("♠AKJ976 ♥QJT976 ♦4")  # 10 HCP, 6-6-1-0
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♥', f"Expected 4♥ (Texas for spades preferred), got {result[0]}"


class TestTexasTransferCompletion:
    """Test opener completing Texas Transfer."""

    def test_opener_completes_hearts(self):
        """Opener must complete 4♦→4♥ Texas Transfer."""
        texas = TexasTransferConvention()
        hand = make_hand("♠AQ5 ♥KJ3 ♦AJ42 ♣Q73")  # 16 HCP, 1NT opener
        auction = ['1NT', 'Pass', '4♦', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♥', f"Expected 4♥ (completing Texas), got {result[0]}"

    def test_opener_completes_spades(self):
        """Opener must complete 4♥→4♠ Texas Transfer."""
        texas = TexasTransferConvention()
        hand = make_hand("♠AQ5 ♥KJ3 ♦AJ42 ♣Q73")  # 16 HCP
        auction = ['1NT', 'Pass', '4♥', 'Pass']
        features = extract_features(hand, auction, 'North', 'None', 'North')
        result = texas.evaluate(hand, features)
        assert result is not None
        assert result[0] == '4♠', f"Expected 4♠ (completing Texas), got {result[0]}"


class TestTexasToRKCBPipeline:
    """Test that 4NT after Texas Transfer is always RKCB."""

    def test_4nt_after_texas_is_rkcb(self):
        """After Texas Transfer completion, 4NT = RKCB, not quantitative."""
        blackwood = BlackwoodConvention()
        # North opened 1NT, South bid 4♦ (Texas hearts), North completed 4♥
        # South now bids 4NT → must be RKCB for hearts
        north_hand = make_hand("♠AQ5 ♥KJ3 ♦AJ42 ♣Q73")  # 16 HCP, 1NT opener
        auction = [
            '1NT',  # North
            'Pass',
            '4♦',   # South (Texas transfer to hearts)
            'Pass',
            '4♥',   # North (completes)
            'Pass',
            '4NT',  # South (RKCB, not quantitative!)
            'Pass',
            # North must respond with keycards
        ]
        features = extract_features(north_hand, auction, 'North', 'None', 'North')
        result = blackwood.evaluate(north_hand, features)

        assert result is not None, "4NT after Texas should be RKCB, not quantitative"
        bid = result[0]
        # North has: ♠A + ♦A = 2 aces, ♥K = trump king → 3 keycards
        # No ♥Q → no trump queen
        # RKCB 1430: 3 keycards → 5♦ (0 or 3)
        assert bid == '5♦', f"Expected 5♦ (3 keycards via RKCB 1430), got {bid}"

    def test_texas_transfer_sequence_detection(self):
        """Test the is_texas_transfer_sequence utility function."""
        positions = ['North', 'East', 'South', 'West']

        # Pattern: North opens 1NT, South bids 4♦, North completes 4♥
        auction = ['1NT', 'Pass', '4♦', 'Pass', '4♥', 'Pass']
        # From South's perspective (index 2)
        assert is_texas_transfer_sequence(auction, positions, 2)
        # From North's perspective (index 0)
        assert is_texas_transfer_sequence(auction, positions, 0)

    def test_non_texas_not_detected(self):
        """Normal auction without Texas should not be detected."""
        positions = ['North', 'East', 'South', 'West']
        auction = ['1NT', 'Pass', '2♦', 'Pass', '2♥', 'Pass']  # Jacoby, not Texas
        assert not is_texas_transfer_sequence(auction, positions, 2)


class TestStaymanToGerber:
    """Test Stayman→Gerber transition."""

    def test_responder_bids_gerber_after_stayman_heart_fit(self):
        """After 1NT→2♣→2♥, responder with slam values bids 4♣ Gerber."""
        gerber = GerberConvention()
        # Responder has 4 hearts + slam values
        hand = make_hand("♠AK5 ♥AQJ4 ♦KQ42 ♣73")  # 18 HCP, 4 hearts
        auction = [
            '1NT',  # North opens
            'Pass',
            '2♣',   # South (Stayman)
            'Pass',
            '2♥',   # North shows 4 hearts
            'Pass',
            # South's turn — should bid 4♣ Gerber
        ]
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = gerber.evaluate(hand, features)
        assert result is not None, "Should be able to bid Gerber after Stayman"
        assert result[0] == '4♣', f"Expected 4♣ Gerber, got {result[0]}"

    def test_responder_bids_gerber_after_stayman_denial(self):
        """After 1NT→2♣→2♦ (denial), responder can still bid 4♣ Gerber."""
        gerber = GerberConvention()
        hand = make_hand("♠AK54 ♥AQJ4 ♦KQ4 ♣73")  # 19 HCP
        auction = [
            '1NT',  # North opens
            'Pass',
            '2♣',   # South (Stayman)
            'Pass',
            '2♦',   # North denies 4-card major
            'Pass',
        ]
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = gerber.evaluate(hand, features)
        assert result is not None, "Should be able to bid Gerber after Stayman denial"
        assert result[0] == '4♣', f"Expected 4♣ Gerber, got {result[0]}"

    def test_opener_responds_to_gerber_after_stayman(self):
        """Opener recognizes 4♣ as Gerber after responding to Stayman."""
        gerber = GerberConvention()
        # North opened 1NT, responded 2♥ to Stayman, South now bids 4♣
        north_hand = make_hand("♠AQ5 ♥KJ43 ♦AJ4 ♣Q73")  # 16 HCP, 4 hearts
        auction = [
            '1NT',  # North opens
            'Pass',
            '2♣',   # South (Stayman)
            'Pass',
            '2♥',   # North shows hearts
            'Pass',
            '4♣',   # South (Gerber!)
            'Pass',
            # North must respond with ace count
        ]
        features = extract_features(north_hand, auction, 'North', 'None', 'North')
        result = gerber.evaluate(north_hand, features)
        assert result is not None, "Should recognize 4♣ as Gerber after Stayman response"
        bid = result[0]
        # North has 2 aces (♠A, ♦A) → 4♠
        assert bid == '4♠', f"Expected 4♠ (2 aces), got {bid}"

    def test_no_gerber_after_stayman_without_slam_values(self):
        """Responder with <15 HCP over 1NT should not bid Gerber after Stayman."""
        gerber = GerberConvention()
        hand = make_hand("♠K54 ♥QJ43 ♦Q42 ♣J73")  # 10 HCP
        auction = [
            '1NT', 'Pass', '2♣', 'Pass', '2♥', 'Pass',
        ]
        features = extract_features(hand, auction, 'South', 'None', 'North')
        result = gerber.evaluate(hand, features)
        assert result is None, "10 HCP should not bid Gerber after Stayman"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
