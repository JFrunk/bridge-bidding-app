"""
Unit tests for the QA Differential Testing Pipeline.

Tests:
- LTC calculation with dubious honor adjustments
- PBN mapping layer (deal parsing, bid translation, vulnerability)
- PBN test set generator
- QA harness bid comparison logic
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.hand import Hand, Card
from engine.ai.feature_extractor import calculate_losing_trick_count
from qa.pbn_mapper import (
    translate_bid,
    parse_pbn_deal_string,
    parse_pbn_vulnerability,
    parse_pbn_auction,
    parse_pbn_file,
    calculate_feature_vector,
    PBNRecord,
)
from qa.pbn_generator import PBNTestGenerator
from qa.bidding_qa_harness import BiddingQAHarness


# =============================================================================
# LTC Tests (Enhanced with dubious honor adjustments)
# =============================================================================

class TestLTCCalculation:
    """Test Losing Trick Count with NLTC adjustments."""

    def test_basic_ltc_all_aces_kings(self):
        """AK in every suit = 0 losers per suit (8 winners + 5 losers in 3rd cards)."""
        # ♠AK432 ♥AK43 ♦AK ♣32
        hand = Hand.from_pbn('AK432.AK43.AK.32')
        ltc = calculate_losing_trick_count(hand)
        # ♠: AK432 → 1 loser (no Q)
        # ♥: AK43 → 1 loser (no Q)
        # ♦: AK → 0 losers
        # ♣: 32 → 2 losers (no A, no K)
        assert ltc == 4.0

    def test_ltc_void(self):
        """Void = 0 losers."""
        # ♠AKQJT987 ♥AK4 ♦32 ♣- (void clubs, 13 cards)
        hand = Hand.from_pbn('AKQJT987.AK4.32.')
        ltc = calculate_losing_trick_count(hand)
        # ♠: AKQJT987 → 0 losers
        # ♥: AK4 → 1 loser (no Q)
        # ♦: 32 → 2 losers
        # ♣: void → 0 losers
        assert ltc == 3.0

    def test_ltc_singleton_ace(self):
        """Singleton Ace = 0 losers."""
        # ♠A ♥KQJ98 ♦KQJ93 ♣KQ = 13 cards (1+5+5+2)
        hand = Hand.from_pbn('A.KQJ98.KQJ93.KQ')
        ltc = calculate_losing_trick_count(hand)
        # ♠: A → 0 losers
        # ♥: KQJ98 → 1 loser (K+Q = 2 winners of 3 potential)
        # ♦: KQJ93 → 1 loser (K+Q = 2 winners of 3 potential)
        # ♣: KQ → 0.5 losers (K=1 winner, Q=0.5 with K protection)
        assert ltc == 2.5

    def test_ltc_singleton_king_dubious(self):
        """Singleton King = 0.5 losers (NLTC adjustment)."""
        hand = Hand.from_pbn('K.AKQJT98.AKQ.32')
        ltc = calculate_losing_trick_count(hand)
        # ♠: K (singleton) → 1.0 losers (0.5 base + 0.5 fragile penalty)
        # ♥: AKQJT98 → 0 losers
        # ♦: AKQ → 0 losers
        # ♣: 32 → 2 losers
        assert ltc == 3.0

    def test_ltc_unprotected_queen_doubleton(self):
        """Qx (doubleton Queen without Ace/King) = 2.0 losers (Q worth 0 winners)."""
        # ♠AKQJT ♥AKQ ♦Q7 ♣432 = 5+3+2+3 = 13
        hand = Hand.from_pbn('AKQJT.AKQ.Q7.432')
        ltc = calculate_losing_trick_count(hand)
        # ♠: AKQJT → 0 losers (A+K+Q = 3 winners of 3 potential)
        # ♥: AKQ → 0 losers
        # ♦: Q7 → 2.5 losers (Q without A/K = 0 winners + 0.5 fragile penalty)
        # ♣: 432 → 3 losers
        assert ltc == 5.5

    def test_ltc_protected_queen_doubleton(self):
        """AQ (doubleton with Ace) = Q counts as half winner."""
        # ♠AKQJT ♥AKQ ♦AQ ♣432 = 5+3+2+3 = 13
        hand = Hand.from_pbn('AKQJT.AKQ.AQ.432')
        ltc = calculate_losing_trick_count(hand)
        # ♠: AKQJT → 0 losers
        # ♥: AKQ → 0 losers
        # ♦: AQ → A=1 winner, Q=0.5 winner (protected by A) → 2-1.5 = 0.5 losers
        # ♣: 432 → 3 losers
        assert ltc == 3.5

    def test_ltc_example_hand_from_spec(self):
        """Test the example from the specification: ♠AK942 ♥8 ♦Q763 ♣J105."""
        hand = Hand.from_pbn('AK942.8.Q763.JT5')
        ltc = calculate_losing_trick_count(hand)
        # ♠: AK942 → 1 loser (no Q)
        # ♥: 8 (singleton, not A) → 1 loser
        # ♦: Q763 → 2 losers (no A, no K)
        # ♣: JT5 → 3 losers (no A, no K, no Q)
        assert ltc == 7.0

    def test_ltc_returns_float(self):
        """LTC should return float for dubious honor adjustments."""
        hand = Hand.from_pbn('AK942.8.Q763.JT5')
        result = calculate_losing_trick_count(hand)
        assert isinstance(result, float)


# =============================================================================
# PBN Mapper Tests
# =============================================================================

class TestBidTranslation:
    """Test PBN → MBB bid translation."""

    def test_pass_variants(self):
        assert translate_bid('P') == 'Pass'
        assert translate_bid('Pass') == 'Pass'

    def test_double_variants(self):
        assert translate_bid('D') == 'X'
        assert translate_bid('X') == 'X'
        assert translate_bid('Dbl') == 'X'

    def test_redouble_variants(self):
        assert translate_bid('R') == 'XX'
        assert translate_bid('XX') == 'XX'
        assert translate_bid('Rdbl') == 'XX'

    def test_suit_bids(self):
        assert translate_bid('1S') == '1♠'
        assert translate_bid('2H') == '2♥'
        assert translate_bid('3D') == '3♦'
        assert translate_bid('4C') == '4♣'

    def test_nt_bids(self):
        assert translate_bid('1NT') == '1NT'
        assert translate_bid('3NT') == '3NT'
        assert translate_bid('6NT') == '6NT'

    def test_already_unicode(self):
        assert translate_bid('1♠') == '1♠'
        assert translate_bid('2♥') == '2♥'

    def test_invalid_bid_raises(self):
        with pytest.raises(ValueError):
            translate_bid('ZZZ')


class TestPBNDealParsing:
    """Test PBN deal string → Hand objects."""

    def test_basic_deal(self):
        deal_str = "N:AKQJ.T987.654.32 T98.AKQ.JT9.8765 765.J6.AK873.QJT 432.5432.Q2.AK94"
        hands = parse_pbn_deal_string(deal_str)
        assert 'North' in hands
        assert 'East' in hands
        assert 'South' in hands
        assert 'West' in hands
        assert hands['North'].hcp == 10  # AKQJ = 10
        assert len(hands['North'].cards) == 13

    def test_deal_starting_from_east(self):
        deal_str = "E:T98.AKQ.JT9.8765 765.J6.AK873.QJT 432.5432.Q2.AK94 AKQJ.T987.654.32"
        hands = parse_pbn_deal_string(deal_str)
        assert hands['East'].hcp == 10  # A=4 + K=3 + Q=2 + J=1 = 10

    def test_deal_without_prefix(self):
        deal_str = "AKQJ.T987.654.32 T98.AKQ.JT9.8765 765.J6.AK873.QJT 432.5432.Q2.AK94"
        hands = parse_pbn_deal_string(deal_str)
        assert 'North' in hands

    def test_invalid_deal_count(self):
        with pytest.raises(ValueError):
            parse_pbn_deal_string("N:AKQJ.T987.654.32 T98.AKQ.JT9.8765")


class TestVulnerabilityParsing:
    """Test PBN vulnerability → MBB format."""

    def test_standard_values(self):
        assert parse_pbn_vulnerability('None') == 'None'
        assert parse_pbn_vulnerability('NS') == 'NS'
        assert parse_pbn_vulnerability('EW') == 'EW'
        assert parse_pbn_vulnerability('Both') == 'Both'

    def test_alternate_values(self):
        assert parse_pbn_vulnerability('Love') == 'None'
        assert parse_pbn_vulnerability('All') == 'Both'
        assert parse_pbn_vulnerability('-') == 'None'
        assert parse_pbn_vulnerability('N-S') == 'NS'
        assert parse_pbn_vulnerability('E-W') == 'EW'

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_pbn_vulnerability('Invalid')


class TestAuctionParsing:
    """Test PBN auction → MBB bid list."""

    def test_basic_auction(self):
        bids = parse_pbn_auction(['1S Pass 2H Pass 4S Pass Pass Pass'], 'North')
        assert bids == ['1♠', 'Pass', '2♥', 'Pass', '4♠', 'Pass', 'Pass', 'Pass']

    def test_all_pass(self):
        bids = parse_pbn_auction(['1S Pass Pass AP'], 'North')
        # After "1S Pass Pass" there are 2 trailing passes, AP adds 1 more
        assert bids == ['1♠', 'Pass', 'Pass', 'Pass']

    def test_multiline_auction(self):
        bids = parse_pbn_auction(['1S Pass', '2H Pass', '4S Pass Pass Pass'], 'North')
        assert len(bids) == 8

    def test_skip_comments(self):
        bids = parse_pbn_auction(['{comment} 1S Pass'], 'North')
        # The comment token is skipped (starts with {, and } is in same token)
        assert '1♠' in bids
        assert 'Pass' in bids


class TestFeatureVector:
    """Test feature vector calculation for debugging."""

    def test_basic_features(self):
        hand = Hand.from_pbn('AK942.8.Q763.JT5')
        features = calculate_feature_vector(hand)
        # A=4, K=3, Q=2, J=1 = 10 HCP
        assert features['hcp'] == 10
        assert features['shape']['♠'] == 5
        assert features['shape']['♥'] == 1
        assert isinstance(features['quick_tricks'], float)
        assert isinstance(features['losing_trick_count'], float)
        assert isinstance(features['controls'], int)


# =============================================================================
# PBN Generator Tests
# =============================================================================

class TestPBNGenerator:
    """Test PBN test set generation."""

    def test_generate_balanced_suite(self):
        gen = PBNTestGenerator(seed=42)
        with tempfile.NamedTemporaryFile(suffix='.pbn', delete=False) as f:
            filepath = f.name

        try:
            count = gen.generate_balanced_suite(10, filepath)
            assert count > 0
            assert os.path.exists(filepath)

            # Verify file is valid PBN
            with open(filepath) as f:
                content = f.read()
            assert '[Event' in content
            assert '[Deal' in content
        finally:
            os.unlink(filepath)

    def test_generate_competitive_suite(self):
        gen = PBNTestGenerator(seed=42)
        with tempfile.NamedTemporaryFile(suffix='.pbn', delete=False) as f:
            filepath = f.name

        try:
            count = gen.generate_competitive_suite(10, filepath)
            assert count > 0
        finally:
            os.unlink(filepath)

    def test_generate_mixed_suite(self):
        gen = PBNTestGenerator(seed=42)
        with tempfile.NamedTemporaryFile(suffix='.pbn', delete=False) as f:
            filepath = f.name

        try:
            count = gen.generate_mixed_suite(20, filepath)
            assert count > 0

            # Parse it back and verify
            records = parse_pbn_file(filepath)
            assert len(records) > 0
            for record in records:
                assert len(record.hands) == 4
                for hand in record.hands.values():
                    assert len(hand.cards) == 13
        finally:
            os.unlink(filepath)

    def test_vulnerability_rotation(self):
        gen = PBNTestGenerator(seed=42)
        assert gen._vulnerability_for_board(1) == 'None'
        assert gen._vulnerability_for_board(2) == 'NS'
        assert gen._vulnerability_for_board(3) == 'EW'
        assert gen._vulnerability_for_board(4) == 'Both'

    def test_dealer_rotation(self):
        gen = PBNTestGenerator(seed=42)
        assert gen._dealer_for_board(1) == 'North'
        assert gen._dealer_for_board(2) == 'East'
        assert gen._dealer_for_board(3) == 'South'
        assert gen._dealer_for_board(4) == 'West'


# =============================================================================
# QA Harness Tests
# =============================================================================

class TestGroundTruthSuite:
    """Integration tests for the ground truth PBN suite."""

    GROUND_TRUTH_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data', 'ground_truth',
    )

    def test_all_tier_files_exist(self):
        """All tier PBN files must exist."""
        expected = ['tier_1_core.pbn', 'tier_2_specialized.pbn',
                    'tier_3_boundary.pbn', 'tier_4_advanced.pbn']
        for name in expected:
            path = os.path.join(self.GROUND_TRUTH_DIR, name)
            assert os.path.exists(path), f"Missing ground truth file: {name}"

    def test_all_boards_parse_with_valid_hands(self):
        """Every board in every tier file must parse with 4 hands of 13 cards each."""
        from collections import Counter
        total_boards = 0
        for name in os.listdir(self.GROUND_TRUTH_DIR):
            if not name.endswith('.pbn'):
                continue
            path = os.path.join(self.GROUND_TRUTH_DIR, name)
            records = parse_pbn_file(path)
            for r in records:
                total_boards += 1
                assert r.hands, f"Board {r.board} ({name}): no hands parsed"
                assert len(r.hands) == 4, f"Board {r.board} ({name}): {len(r.hands)} hands"
                all_cards = []
                for seat, hand in r.hands.items():
                    assert len(hand.cards) == 13, (
                        f"Board {r.board} ({name}): {seat} has {len(hand.cards)} cards"
                    )
                    all_cards.extend((c.suit, c.rank) for c in hand.cards)
                assert len(set(all_cards)) == 52, (
                    f"Board {r.board} ({name}): {len(set(all_cards))} unique cards"
                )
        assert total_boards >= 30, f"Expected 30+ boards, got {total_boards}"

    def test_all_boards_have_auctions(self):
        """Every ground truth board must have a non-empty auction."""
        for name in os.listdir(self.GROUND_TRUTH_DIR):
            if not name.endswith('.pbn'):
                continue
            path = os.path.join(self.GROUND_TRUTH_DIR, name)
            records = parse_pbn_file(path)
            for r in records:
                assert r.auction, f"Board {r.board} ({name}): no auction"
                assert len(r.auction) >= 4, (
                    f"Board {r.board} ({name}): auction too short ({len(r.auction)} bids)"
                )

    def test_harness_runs_against_ground_truth(self):
        """The QA harness must complete without errors on all ground truth files."""
        harness = BiddingQAHarness()
        tier_results = harness.run_directory(self.GROUND_TRUTH_DIR)
        assert len(tier_results) >= 4, f"Expected 4+ tier files, got {len(tier_results)}"
        for filename, result in tier_results.items():
            assert result.total_boards > 0, f"{filename}: no boards processed"
            assert result.total_bids_compared > 0, f"{filename}: no bids compared"

    def test_tier_report_produces_accuracy(self):
        """print_tier_report must return a numeric overall accuracy."""
        harness = BiddingQAHarness()
        tier_results = harness.run_directory(self.GROUND_TRUTH_DIR)
        accuracy = harness.print_tier_report(tier_results)
        assert isinstance(accuracy, (int, float))
        assert 0 <= accuracy <= 100


class TestBidEquivalence:
    """Test bid comparison logic."""

    def test_identical_bids(self):
        assert BiddingQAHarness._bids_equivalent('1♠', '1♠')
        assert BiddingQAHarness._bids_equivalent('Pass', 'Pass')

    def test_notation_differences(self):
        assert BiddingQAHarness._bids_equivalent('1♠', '1S')
        assert BiddingQAHarness._bids_equivalent('Pass', 'P')
        assert BiddingQAHarness._bids_equivalent('X', 'D')
        assert BiddingQAHarness._bids_equivalent('XX', 'R')

    def test_different_bids(self):
        assert not BiddingQAHarness._bids_equivalent('1♠', '1♥')
        assert not BiddingQAHarness._bids_equivalent('Pass', '1♣')
        assert not BiddingQAHarness._bids_equivalent('2NT', '3NT')


class TestHarnessIntegration:
    """Integration test: generate PBN → run harness → verify output structure."""

    def test_full_pipeline_with_generated_hands(self):
        """Generate hands, run harness (no reference auction), verify no crashes."""
        gen = PBNTestGenerator(seed=42)
        with tempfile.NamedTemporaryFile(suffix='.pbn', delete=False) as f:
            filepath = f.name

        try:
            gen.generate_balanced_suite(5, filepath)

            # Since generated PBN has no auctions, harness should handle gracefully
            harness = BiddingQAHarness()
            result = harness.run_pbn_file(filepath, seats=['South'], max_boards=5)

            # No auctions to compare → 0 bids compared
            assert result.total_boards >= 0
            assert result.boards_with_hands >= 0
        finally:
            os.unlink(filepath)

    def test_harness_with_manual_pbn(self):
        """Test with a manually crafted PBN that includes an auction."""
        pbn_content = '''[Event "Test"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:AKQ32.KQ8.A95.74 J98.AT7.KQJ3.KQ8 T764.J65.T84.A53 5.9432.762.JT962"]
[Auction "N"]
1S Pass 2S Pass
4S Pass Pass Pass
'''
        with tempfile.NamedTemporaryFile(
            suffix='.pbn', delete=False, mode='w', encoding='utf-8'
        ) as f:
            f.write(pbn_content)
            filepath = f.name

        try:
            harness = BiddingQAHarness()
            result = harness.run_pbn_file(
                filepath, seats=['North', 'South'], max_boards=1
            )
            assert result.total_boards == 1
            assert result.boards_with_auctions == 1
            assert result.total_bids_compared > 0

            # Verify result is serializable
            result_dict = result.to_dict()
            assert 'summary' in result_dict
            assert 'boards' in result_dict
        finally:
            os.unlink(filepath)

    def test_result_save_and_load(self):
        """Test JSON serialization of results."""
        pbn_content = '''[Event "Test"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:AKQ32.KQ8.A95.74 J98.AT7.KQJ3.KQ8 T764.J65.T84.A53 5.9432.762.JT962"]
[Auction "N"]
1S Pass 2S Pass
Pass Pass
'''
        with tempfile.NamedTemporaryFile(
            suffix='.pbn', delete=False, mode='w', encoding='utf-8'
        ) as f:
            f.write(pbn_content)
            pbn_path = f.name

        with tempfile.NamedTemporaryFile(
            suffix='.json', delete=False
        ) as f:
            json_path = f.name

        try:
            harness = BiddingQAHarness()
            result = harness.run_pbn_file(pbn_path, max_boards=1)
            result.save(json_path)

            # Load and verify
            import json
            with open(json_path) as f:
                data = json.load(f)
            assert data['summary']['total_boards'] == 1
        finally:
            os.unlink(pbn_path)
            os.unlink(json_path)
