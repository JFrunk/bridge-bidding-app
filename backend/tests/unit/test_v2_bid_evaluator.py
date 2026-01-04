"""
Unit tests for V2 Schema-Based Bid Evaluator

Tests the V2BidEvaluator class which provides unified evaluation
of user bids using schema rules instead of V1 heuristics.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.hand import Hand, Card
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.v2.feedback.bid_evaluator import (
    V2BidEvaluator,
    V2BiddingFeedback,
    CorrectnessLevel,
    ImpactLevel
)


def make_hand(card_specs):
    """Helper to create Hand from list of (rank, suit) tuples."""
    return Hand([Card(rank, suit) for rank, suit in card_specs])


class TestV2BidEvaluator:
    """Test the V2 bid evaluator."""

    @pytest.fixture
    def engine(self):
        """Create a V2 schema engine for testing."""
        return BiddingEngineV2Schema(use_v1_fallback=False)

    @pytest.fixture
    def evaluator(self, engine):
        """Create evaluator with engine."""
        return V2BidEvaluator(engine)

    def test_optimal_bid_detection(self, evaluator):
        """Test that matching the optimal bid returns OPTIMAL."""
        # Standard 1NT opening hand: 15 HCP, balanced
        hand = make_hand([
            ('A', '♠'), ('K', '♠'), ('5', '♠'), ('3', '♠'),
            ('K', '♥'), ('Q', '♥'), ('7', '♥'),
            ('A', '♦'), ('J', '♦'), ('4', '♦'),
            ('Q', '♣'), ('8', '♣'), ('2', '♣')
        ])

        # Get what the engine recommends
        engine = evaluator.engine
        optimal_bid, _ = engine.get_next_bid(
            hand, [], 'South', 'None', 'detailed', 'North'
        )

        # Evaluate with the same bid
        feedback = evaluator.evaluate_bid(
            hand, optimal_bid, [], 'South', 'None', 'North'
        )

        assert feedback.correctness == CorrectnessLevel.OPTIMAL
        assert feedback.score == 10.0
        assert feedback.user_bid == optimal_bid

    def test_error_detection(self, evaluator):
        """Test that a clearly wrong bid returns ERROR."""
        # Minimum opening hand: 12 HCP, balanced
        hand = make_hand([
            ('A', '♠'), ('Q', '♠'), ('7', '♠'), ('3', '♠'),
            ('K', '♥'), ('J', '♥'), ('5', '♥'),
            ('Q', '♦'), ('9', '♦'), ('4', '♦'),
            ('J', '♣'), ('8', '♣'), ('2', '♣')
        ])

        # Bid 7NT with a minimum hand - clearly wrong
        feedback = evaluator.evaluate_bid(
            hand, '7NT', [], 'South', 'None', 'North'
        )

        # Should be an error
        assert feedback.correctness in [CorrectnessLevel.ERROR, CorrectnessLevel.SUBOPTIMAL]
        assert feedback.score < 7.0
        assert feedback.helpful_hint  # Should have a hint

    def test_feedback_structure(self, evaluator):
        """Test that feedback has all required fields."""
        hand = make_hand([
            ('A', '♠'), ('K', '♠'), ('Q', '♠'), ('J', '♠'), ('5', '♠'),
            ('K', '♥'), ('Q', '♥'), ('7', '♥'),
            ('A', '♦'), ('9', '♦'),
            ('Q', '♣'), ('8', '♣'), ('2', '♣')
        ])

        feedback = evaluator.evaluate_bid(
            hand, '1♠', [], 'South', 'None', 'North'
        )

        # Check all fields are present
        assert hasattr(feedback, 'bid_number')
        assert hasattr(feedback, 'position')
        assert hasattr(feedback, 'user_bid')
        assert hasattr(feedback, 'correctness')
        assert hasattr(feedback, 'score')
        assert hasattr(feedback, 'optimal_bid')
        assert hasattr(feedback, 'optimal_explanation')
        assert hasattr(feedback, 'alternative_bids')
        assert hasattr(feedback, 'matched_candidates')
        assert hasattr(feedback, 'error_category')
        assert hasattr(feedback, 'impact')
        assert hasattr(feedback, 'helpful_hint')
        assert hasattr(feedback, 'key_concept')
        assert hasattr(feedback, 'difficulty')
        assert hasattr(feedback, 'forcing_status')

    def test_to_dict(self, evaluator):
        """Test that feedback can be serialized to dict."""
        hand = make_hand([
            ('A', '♠'), ('K', '♠'), ('Q', '♠'), ('5', '♠'), ('3', '♠'),
            ('A', '♥'), ('Q', '♥'), ('7', '♥'),
            ('K', '♦'), ('9', '♦'),
            ('J', '♣'), ('8', '♣'), ('2', '♣')
        ])

        feedback = evaluator.evaluate_bid(
            hand, '1♠', [], 'South', 'None', 'North'
        )

        d = feedback.to_dict()

        assert isinstance(d, dict)
        assert d['user_bid'] == '1♠'
        assert isinstance(d['correctness'], str)  # Enum value
        assert isinstance(d['score'], float)
        assert isinstance(d['matched_candidates'], list)

    def test_to_user_message(self, evaluator):
        """Test that feedback generates user-friendly messages."""
        hand = make_hand([
            ('A', '♠'), ('K', '♠'), ('Q', '♠'), ('J', '♠'), ('5', '♠'),
            ('K', '♥'), ('Q', '♥'), ('7', '♥'),
            ('A', '♦'), ('9', '♦'),
            ('Q', '♣'), ('8', '♣'), ('2', '♣')
        ])

        # Get optimal bid first
        engine = evaluator.engine
        optimal_bid, _ = engine.get_next_bid(
            hand, [], 'South', 'None', 'detailed', 'North'
        )

        feedback = evaluator.evaluate_bid(
            hand, optimal_bid, [], 'South', 'None', 'North'
        )

        msg = feedback.to_user_message()

        assert isinstance(msg, str)
        assert len(msg) > 0
        # Optimal bids should get positive message
        if feedback.correctness == CorrectnessLevel.OPTIMAL:
            assert '✓' in msg

    def test_matched_candidates_populated(self, evaluator):
        """Test that matched_candidates shows which rules matched."""
        # Strong balanced hand
        hand = make_hand([
            ('A', '♠'), ('K', '♠'), ('Q', '♠'), ('5', '♠'),
            ('A', '♥'), ('K', '♥'), ('7', '♥'),
            ('A', '♦'), ('Q', '♦'), ('9', '♦'),
            ('K', '♣'), ('8', '♣'), ('2', '♣')
        ])

        feedback = evaluator.evaluate_bid(
            hand, '2NT', [], 'South', 'None', 'North'
        )

        # Should have candidates
        assert isinstance(feedback.matched_candidates, list)
        # Each candidate should have required fields
        for candidate in feedback.matched_candidates:
            assert 'bid' in candidate
            assert 'rule_id' in candidate
            assert 'priority' in candidate
            assert 'explanation' in candidate

    def test_engine_evaluate_user_bid_method(self, engine):
        """Test the convenience method on BiddingEngineV2Schema."""
        hand = make_hand([
            ('A', '♠'), ('K', '♠'), ('5', '♠'), ('3', '♠'),
            ('K', '♥'), ('Q', '♥'), ('7', '♥'),
            ('A', '♦'), ('J', '♦'), ('4', '♦'),
            ('Q', '♣'), ('8', '♣'), ('2', '♣')
        ])

        # Use the engine's evaluate_user_bid method directly
        feedback = engine.evaluate_user_bid(
            hand, '1NT', [], 'South', 'None', 'North'
        )

        assert isinstance(feedback, V2BiddingFeedback)
        assert feedback.user_bid == '1NT'


class TestCorrectnessScoring:
    """Test the correctness and scoring logic."""

    @pytest.fixture
    def evaluator(self):
        engine = BiddingEngineV2Schema(use_v1_fallback=False)
        return V2BidEvaluator(engine)

    def test_pass_as_response(self, evaluator):
        """Test evaluating Pass in a response situation."""
        # Weak responding hand
        hand = make_hand([
            ('7', '♠'), ('5', '♠'), ('3', '♠'),
            ('8', '♥'), ('6', '♥'), ('4', '♥'), ('2', '♥'),
            ('9', '♦'), ('7', '♦'), ('5', '♦'),
            ('6', '♣'), ('4', '♣'), ('2', '♣')
        ])

        # Partner opened 1♠
        feedback = evaluator.evaluate_bid(
            hand, 'Pass', ['1♠', 'Pass'], 'South', 'None', 'North'
        )

        # With 0 HCP, Pass should be acceptable
        assert feedback.correctness in [CorrectnessLevel.OPTIMAL, CorrectnessLevel.ACCEPTABLE]


class TestImpactCalculation:
    """Test impact level calculation."""

    @pytest.fixture
    def evaluator(self):
        engine = BiddingEngineV2Schema(use_v1_fallback=False)
        return V2BidEvaluator(engine)

    def test_no_impact_for_optimal(self, evaluator):
        """Optimal bids should have no impact."""
        hand = make_hand([
            ('A', '♠'), ('K', '♠'), ('5', '♠'), ('3', '♠'),
            ('K', '♥'), ('Q', '♥'), ('7', '♥'),
            ('A', '♦'), ('J', '♦'), ('4', '♦'),
            ('Q', '♣'), ('8', '♣'), ('2', '♣')
        ])

        optimal_bid, _ = evaluator.engine.get_next_bid(
            hand, [], 'South', 'None', 'detailed', 'North'
        )

        feedback = evaluator.evaluate_bid(
            hand, optimal_bid, [], 'South', 'None', 'North'
        )

        assert feedback.impact == ImpactLevel.NONE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
