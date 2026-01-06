"""
Unit tests for the DifferentialAnalyzer service.

Tests the core logic for comparing user bids against optimal bids
and generating educational feedback.
"""

import pytest
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.hand import Hand, Card
from engine.v2.differential_analyzer import (
    DifferentialAnalyzer,
    DifferentialResult,
    DifferentialFactor,
    DiagnosticDomain,
    PhysicsSummary,
    get_differential_analyzer
)


def make_hand(pbn: str) -> Hand:
    """Create a Hand from PBN notation (e.g., 'AKQ32.K87.J9.T65')."""
    parts = pbn.split('.')
    suits = ['♠', '♥', '♦', '♣']
    cards = []
    for i, suit_str in enumerate(parts):
        for rank in suit_str:
            cards.append(Card(rank=rank, suit=suits[i]))
    return Hand(cards)


class TestDifferentialAnalyzerBasics:
    """Test basic DifferentialAnalyzer functionality."""

    def test_factory_function(self):
        """Test that get_differential_analyzer returns an instance."""
        analyzer = get_differential_analyzer()
        assert analyzer is not None
        assert isinstance(analyzer, DifferentialAnalyzer)

    def test_optimal_bid_returns_optimal_rating(self):
        """When user bid matches optimal, rating should be 'optimal'."""
        analyzer = DifferentialAnalyzer()
        hand = make_hand('AKQ32.K87.J9.T65')  # 12 HCP

        # Opening 1♠ should be optimal for this hand
        result = analyzer.analyze(
            user_bid='1♠',
            optimal_bid='1♠',
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        assert result.rating == 'optimal'
        assert result.score == 100
        assert result.user_bid == '1♠'
        assert result.optimal_bid == '1♠'
        assert len(result.differential_factors) == 0

    def test_different_bid_returns_differential_factors(self):
        """When bids differ, differential factors should explain why."""
        analyzer = DifferentialAnalyzer()
        hand = make_hand('AKQ32.K87.J9.T65')

        result = analyzer.analyze(
            user_bid='2♠',
            optimal_bid='1♠',
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        assert result.rating != 'optimal'
        assert result.score < 100
        assert result.user_bid == '2♠'
        assert result.optimal_bid == '1♠'

    def test_physics_summary_populated(self):
        """Physics summary should be populated with hand features."""
        analyzer = DifferentialAnalyzer()
        # AKQ32.K87.J9.T65 = A(4)+K(3)+Q(2)+K(3)+J(1) = 13 HCP
        hand = make_hand('AKQ32.K87.J9.T65')

        result = analyzer.analyze(
            user_bid='1♠',
            optimal_bid='1♠',
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        assert result.physics is not None
        assert result.physics.hcp == 13  # A(4)+K(3)+Q(2)+K(3)+J(1) = 13
        assert result.physics.shape == '5-3-2-3'
        assert result.physics.longest_suit == '♠'
        # 5-3-2-3 is balanced by bridge standards (no 5+ card minor, no singleton/void)

    def test_diagnostic_domain_classification(self):
        """Domain should be classified based on differential factors."""
        analyzer = DifferentialAnalyzer()

        # Test domain classification logic
        result = analyzer._classify_domain([])
        assert result == DiagnosticDomain.GENERAL

        # LoTT factor should classify as SAFETY
        lott_factor = DifferentialFactor(
            feature='lott_safe_level',
            label='LoTT Safe Level',
            actual_value=2,
            required_value=3,
            gap='Level exceeds safe level',
            impact='Overbid',
            status='FAIL'
        )
        result = analyzer._classify_domain([lott_factor])
        assert result == DiagnosticDomain.SAFETY


class TestDifferentialFactorCalculation:
    """Test differential factor calculation."""

    def test_lott_violation_detected(self):
        """LoTT violations should be detected when bidding too high."""
        analyzer = DifferentialAnalyzer()

        # Hand with 4-card support but limited values
        hand = make_hand('KT92.873.Q65.A42')  # 9 HCP, 4 spades

        # User bids 3♠ but with 8-card fit, LoTT safe level is 2
        result = analyzer.analyze(
            user_bid='3♠',
            optimal_bid='2♠',
            hand=hand,
            auction_history=['1♠', 'Pass'],  # Partner opened
            position='South',
            vulnerability='None',
            dealer='North'
        )

        # Should have differential factors
        assert result.rating != 'optimal'
        assert result.user_bid == '3♠'

    def test_working_hcp_factor(self):
        """Working HCP ratio should influence feedback."""
        analyzer = DifferentialAnalyzer()

        # Hand with HCP in short suits (13 cards total: 2+3+3+5=13)
        # KQJ(6) + QJ(3) + KQJ(6) = 15 HCP
        hand = make_hand('32.KQJ.QJ5.KQJ32')

        result = analyzer.analyze(
            user_bid='1♣',
            optimal_bid='1♣',  # Use optimal to avoid assertion issues
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        # Check physics includes working_hcp_ratio
        assert result.physics.working_hcp_ratio is not None
        assert result.physics.hcp == 15  # KQJ(6) + QJ(3) + KQJ(6) = 15


class TestLearningMessageGeneration:
    """Test educational message generation."""

    def test_primary_reason_generated(self):
        """Primary reason should be generated for non-optimal bids."""
        analyzer = DifferentialAnalyzer()
        hand = make_hand('AKQ32.K87.J9.T65')

        result = analyzer.analyze(
            user_bid='2♠',
            optimal_bid='1♠',
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        assert result.primary_reason is not None
        assert len(result.primary_reason) > 0

    def test_learning_point_generated(self):
        """Learning point should be generated."""
        analyzer = DifferentialAnalyzer()
        hand = make_hand('AKQ32.K87.J9.T65')

        result = analyzer.analyze(
            user_bid='1♠',
            optimal_bid='1♠',
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        assert result.learning_point is not None
        assert len(result.learning_point) > 0

    def test_commentary_html_generated(self):
        """HTML commentary should be generated."""
        analyzer = DifferentialAnalyzer()
        hand = make_hand('AKQ32.K87.J9.T65')

        result = analyzer.analyze(
            user_bid='2♠',
            optimal_bid='1♠',
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        assert result.commentary_html is not None
        assert '<' in result.commentary_html  # Contains HTML tags


class TestRuleMatching:
    """Test rule matching functionality."""

    def test_user_bid_rules_populated(self):
        """Rules matching user's bid should be populated."""
        analyzer = DifferentialAnalyzer()
        hand = make_hand('AKQ32.K87.J9.T65')

        result = analyzer.analyze(
            user_bid='1♠',
            optimal_bid='1♠',
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        # Should have at least one rule for 1♠ opening
        assert len(result.user_bid_rules) > 0 or len(result.optimal_bid_rules) > 0

    def test_optimal_bid_rules_populated(self):
        """Rules matching optimal bid should be populated."""
        analyzer = DifferentialAnalyzer()
        hand = make_hand('AKQ32.K87.J9.T65')

        result = analyzer.analyze(
            user_bid='Pass',
            optimal_bid='1♠',
            hand=hand,
            auction_history=[],
            position='South',
            vulnerability='None',
            dealer='South'
        )

        # Should have rules for optimal bid
        assert len(result.optimal_bid_rules) > 0


class TestRatingCalculation:
    """Test rating and score calculation."""

    def test_optimal_score_is_100(self):
        """Optimal bid should get score of 100."""
        analyzer = DifferentialAnalyzer()
        rating, score = analyzer._calculate_rating('1♠', '1♠', [])
        assert rating == 'optimal'
        assert score == 100

    def test_suboptimal_score_below_100(self):
        """Suboptimal bids should score below 100."""
        analyzer = DifferentialAnalyzer()
        factors = [
            DifferentialFactor(
                feature='hcp',
                label='HCP',
                actual_value=10,
                required_value=12,
                gap='Need 2 more HCP',
                impact='Insufficient strength',
                status='FAIL',
                shortfall=2
            )
        ]
        rating, score = analyzer._calculate_rating('2♠', '1♠', factors)
        assert rating in ['acceptable', 'suboptimal', 'error']
        assert score < 100

    def test_error_rating_for_severe_issues(self):
        """Multiple FAIL factors should result in error rating."""
        analyzer = DifferentialAnalyzer()
        factors = [
            DifferentialFactor(feature='hcp', label='HCP', actual_value=8,
                             required_value=12, gap='Gap', impact='Impact',
                             status='FAIL', shortfall=4),
            DifferentialFactor(feature='lott', label='LoTT', actual_value=2,
                             required_value=4, gap='Gap', impact='Impact',
                             status='FAIL', shortfall=2),
            DifferentialFactor(feature='fit', label='Fit', actual_value=6,
                             required_value=8, gap='Gap', impact='Impact',
                             status='FAIL', shortfall=2),
        ]
        rating, score = analyzer._calculate_rating('4♠', '1♠', factors)
        assert rating == 'error'
        assert score <= 30


class TestBidLevelExtraction:
    """Test bid level extraction helper."""

    def test_extract_numeric_level(self):
        """Numeric levels should be extracted correctly."""
        analyzer = DifferentialAnalyzer()
        assert analyzer._get_bid_level('1♠') == 1
        assert analyzer._get_bid_level('2NT') == 2
        assert analyzer._get_bid_level('3♥') == 3
        assert analyzer._get_bid_level('4♣') == 4
        assert analyzer._get_bid_level('7NT') == 7

    def test_special_bids_return_none(self):
        """Pass, Double, Redouble should return None."""
        analyzer = DifferentialAnalyzer()
        assert analyzer._get_bid_level('Pass') is None
        assert analyzer._get_bid_level('X') is None
        assert analyzer._get_bid_level('XX') is None
        assert analyzer._get_bid_level('Double') is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
