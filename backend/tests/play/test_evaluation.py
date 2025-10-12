"""
Unit tests for Position Evaluation

Tests the evaluation function used by minimax AI:
- Tricks won component
- Sure winners component
- Overall evaluation scoring
- Perspective-based evaluation
"""

import pytest
from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.evaluation import PositionEvaluator
from tests.play_test_helpers import create_test_deal, create_play_scenario


class TestTricksWonComponent:
    """Test tricks won evaluation component"""

    def test_no_tricks_won(self):
        """Test evaluation at start of hand (no tricks won)"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        evaluator = PositionEvaluator()
        score = evaluator._tricks_won_component(state, 'N')

        # No tricks won yet
        assert score == 0.0

    def test_declarer_wins_tricks(self):
        """Test evaluation when declarer has won tricks"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # Simulate North and South winning tricks
        state.tricks_won['N'] = 5
        state.tricks_won['S'] = 4

        evaluator = PositionEvaluator()
        score = evaluator._tricks_won_component(state, 'N')

        # North is declarer (N-S partnership)
        # N+S = 9 tricks, E+W = 0 tricks
        # Score = 9 - 0 = +9.0
        assert score == 9.0

    def test_defenders_win_tricks(self):
        """Test evaluation when defenders are winning"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # Simulate defenders winning tricks
        state.tricks_won['E'] = 6
        state.tricks_won['W'] = 3

        evaluator = PositionEvaluator()
        score = evaluator._tricks_won_component(state, 'E')

        # East is defender (E-W partnership)
        # E+W = 9 tricks, N+S = 0 tricks (declarer)
        # From defender's perspective: 9 - 0 = +9.0
        assert score == 9.0

    def test_perspective_matters(self):
        """Test that perspective affects evaluation"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # N-S have 7 tricks, E-W have 2 tricks
        state.tricks_won['N'] = 4
        state.tricks_won['S'] = 3
        state.tricks_won['E'] = 1
        state.tricks_won['W'] = 1

        evaluator = PositionEvaluator()

        # From North's perspective (declarer)
        score_north = evaluator._tricks_won_component(state, 'N')
        assert score_north == 5.0  # (7 - 2)

        # From East's perspective (defender)
        score_east = evaluator._tricks_won_component(state, 'E')
        assert score_east == -5.0  # (2 - 7)


class TestSureWinnersComponent:
    """Test sure winners evaluation component"""

    def test_ace_is_sure_winner(self):
        """Test that lone aces count as sure winners"""
        deal = create_test_deal(
            north="♠A432 ♥A432 ♦A3 ♣A32",
            east="♠KQJ5 ♥KQJ5 ♦KQJ ♣KQ",
            south="♠876 ♥876 ♦8765 ♣876",
            west="♠T9 ♥T9 ♦T942 ♣JT985"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        evaluator = PositionEvaluator()
        score = evaluator._sure_winners_component(state, 'N')

        # North has 4 aces (all top cards in their suits)
        # Each counts as 0.5, so score should be positive
        assert score > 0

    def test_ace_king_sequence(self):
        """Test that AK sequence counts as sure winners"""
        deal = create_test_deal(
            north="♠AK32 ♥AK32 ♦AK3 ♣A2",
            east="♠QJ54 ♥QJ54 ♦QJ5 ♣KQ",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠T9 ♥T9 ♦T94 ♣JT9543"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        evaluator = PositionEvaluator()
        score = evaluator._sure_winners_component(state, 'N')

        # North has AK in spades, hearts, diamonds
        # Plus A in clubs
        # Should have more sure winners than just aces
        assert score > 0

    def test_no_sure_winners(self):
        """Test position with no top cards"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",  # No top cards
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        evaluator = PositionEvaluator()

        # From South's perspective (partner of declarer)
        score = evaluator._sure_winners_component(state, 'S')

        # South has no top sequential cards
        # But North (partner) has many
        # Score will depend on partnership counting
        # Might be 0 for just South's hand
        assert score >= 0


class TestOverallEvaluation:
    """Test complete evaluation function"""

    def test_initial_position_evaluation(self):
        """Test evaluation at start of hand"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        evaluator = PositionEvaluator()

        # From declarer's perspective
        score_north = evaluator.evaluate(state, 'N')

        # North has strong hand, should evaluate positively
        assert score_north > 0

        # From defender's perspective
        score_east = evaluator.evaluate(state, 'E')

        # East has weak hand against strong declarer
        # At start of hand (no tricks won), defenders might have 0 or negative score
        # depending on sure winners component
        assert score_east <= 0

    def test_mid_hand_evaluation(self):
        """Test evaluation in middle of hand"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # Simulate some tricks played
        state.tricks_won['N'] = 3
        state.tricks_won['E'] = 1

        evaluator = PositionEvaluator()
        score = evaluator.evaluate(state, 'N')

        # Declarer winning, should be positive
        assert score > 0

    def test_evaluation_range(self):
        """Test that evaluation stays in reasonable range"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        evaluator = PositionEvaluator()
        score = evaluator.evaluate(state, 'N')

        # Should be in range roughly [-13, +13] (tricks)
        assert -15 < score < 15


class TestEvaluationWithTrump:
    """Test evaluation with trump suits"""

    def test_trump_suit_in_hearts(self):
        """Test evaluation in hearts contract"""
        deal = create_test_deal(
            north="♠AK32 ♥AK32 ♦AK3 ♣A2",
            east="♠QJ54 ♥QJ54 ♦QJ5 ♣54",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠T9 ♥T9 ♦T94 ♣KQJT93"
        )

        state = create_play_scenario("4♥ by N", deal, "None")

        evaluator = PositionEvaluator()
        score = evaluator.evaluate(state, 'N')

        # Should evaluate (trump component disabled for MVP)
        # But evaluation should still work
        assert isinstance(score, (int, float))

    def test_notrump_evaluation(self):
        """Test evaluation in notrump contract"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        evaluator = PositionEvaluator()
        score = evaluator.evaluate(state, 'N')

        # Notrump evaluation should work
        assert isinstance(score, (int, float))
        assert score > 0  # Strong hand


class TestEvaluationWeights:
    """Test evaluation weight system"""

    def test_custom_weights(self):
        """Test evaluation with custom weights"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # Default weights
        evaluator_default = PositionEvaluator()
        score_default = evaluator_default.evaluate(state, 'N')

        # Custom weights (only tricks won)
        evaluator_custom = PositionEvaluator()
        evaluator_custom.weights['sure_winners'] = 0.0  # Disable
        score_custom = evaluator_custom.evaluate(state, 'N')

        # With no tricks won yet, custom should be 0
        assert score_custom == 0.0

        # Default should be positive (sure winners component)
        assert score_default > 0

    def test_weight_values(self):
        """Test that weight values are reasonable"""
        evaluator = PositionEvaluator()

        # Check default weights
        assert evaluator.weights['tricks_won'] == 1.0
        assert evaluator.weights['sure_winners'] == 0.6
        assert evaluator.weights['trump_control'] == 0.0  # Disabled
        assert evaluator.weights['communication'] == 0.0  # Disabled
        assert evaluator.weights['defensive'] == 0.0  # Disabled


class TestEvaluationConsistency:
    """Test that evaluation is consistent and makes sense"""

    def test_symmetry(self):
        """Test that evaluation is symmetric for opposing sides"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # Set tricks won
        state.tricks_won['N'] = 7
        state.tricks_won['S'] = 0
        state.tricks_won['E'] = 3
        state.tricks_won['W'] = 0

        evaluator = PositionEvaluator()

        score_north = evaluator.evaluate(state, 'N')
        score_east = evaluator.evaluate(state, 'E')

        # Tricks component should be opposite
        # (Sure winners might not be symmetric)
        # But the tricks component should be exactly opposite
        tricks_n = evaluator._tricks_won_component(state, 'N')
        tricks_e = evaluator._tricks_won_component(state, 'E')
        assert abs(tricks_n + tricks_e) < 0.001  # Should be exactly opposite

    def test_monotonicity_tricks(self):
        """Test that more tricks = better evaluation"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")
        evaluator = PositionEvaluator()

        # Declarer has 5 tricks
        state.tricks_won['N'] = 5
        score_5 = evaluator.evaluate(state, 'N')

        # Declarer has 7 tricks
        state.tricks_won['N'] = 7
        score_7 = evaluator.evaluate(state, 'N')

        # More tricks should be better
        assert score_7 > score_5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
